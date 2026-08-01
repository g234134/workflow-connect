# HITL Checkpoints v1 — Human-In-The-Loop Minimal Gates

> **Ticket**: W5-T2 · HITL Checkpoints Design v1  
> **Date**: 2026-06-10  
> **Status**: Design spec — implementation deferred to future tickets  
> **Scope**: Design only; no code changes in this ticket

---

## 1. Design Goal

為 Tabular MVP workflow（intake → gate → cleaning → bundle → delivery）設計 **極簡人工確認點** — 僅在關鍵決策節點保留 HITL，而非每一步都暫停。

**核心原則**:
- **Agent 主導**: 大部分流程自動推進
- **極少人工**: 僅 2 個 checkpoints（接案確認、交付確認）
- **可審計**: 所有決策與人工介入都留下 trace
- **可恢復**: 支援 resume，不從頭重跑

---

## 2. Checkpoint Overview

| Checkpoint | 時機 | 決策者 | 選項 | 預設行為 |
|------------|------|--------|------|----------|
| **A: Intake Confirmation** | Agent 完成 intake decision / suggested_route 後 | Human operator | `approve` / `reject` / `revise_plan` | `approve`（timeout auto-approve） |
| **B: Delivery Confirmation** | Agent 完成 cleaning 與 delivery draft 後 | Human operator | `approve_delivery` / `request_changes` / `hold` | `hold`（timeout → `hold`） |

---

## 3. Checkpoint A: Intake Confirmation

### 3.1 觸發條件

Agent 完成以下任一情況時觸發:

1. `routing/intake_decision_rules_v1.py::evaluate_intake_decision()` 返回 `decision=needs_review`
2. 即使 `decision=auto_accept`，但 `risk_level=medium` 且配置 `HITL_FORCE_CHECKPOINT_A=1`
3. 未知 fixture profile（非 allowlist: `demo_phase`, `sampleco`）

**不觸發的情況**:
- `decision=reject`（直接終止，進入拒絕流程）
- `decision=auto_accept` + `risk_level=low` + known allowlist fixture（自動推進）

### 3.2 Agent 輸出資料（Checkpoint 前必須準備）

```json
{
  "checkpoint": {
    "id": "A-intake-confirmation",
    "version": "v1",
    "triggered_at": "2026-06-10T08:30:00Z",
    "case_ref": "demo_phase",
    "task_type": "tabular.cleaning.mvp"
  },
  "agent_output": {
    "intake_decision": {
      "decision": "needs_review",
      "risk_level": "medium",
      "rationale": ["task_type=tabular.cleaning.mvp", "manual_review_required"],
      "suggested_route": {
        "selector_task_type": "e2e",
        "planned_tools": ["validate.eligibility", "clean.phase_demo", "export.delivery_bundle"],
        "orchestration_tool_id": "orchestrate.e2e"
      }
    },
    "case_summary": {
      "client_ref": "internal-demo",
      "case_id": "demo_phase",
      "input_file": "raw/Phase.csv",
      "estimated_rows": 7,
      "estimated_duration_seconds": 45
    },
    "gate_preview": {
      "eligibility": "review_needed",
      "exit_code": 2,
      "reason_code": "rows<100"
    }
  },
  "human_decision": null,
  "state": {
    "status": "awaiting_human",
    "expires_at": "2026-06-10T08:35:00Z"
  }
}
```

### 3.3 Human 決策選項

| 選項 | 行為 | 後續流程 |
|------|------|----------|
| `approve` | 同意 Agent 建議的 route | 進入 Wave 3-TL Selector → Executor pipeline |
| `reject` | 否決此案 | 寫入 `outbox/<case_ref>/rejected_<timestamp>.json`，終止流程 |
| `revise_plan` | 修改 planned_tools 或換 route | 進入 revise 子流程，Agent 重新生成 plan |

### 3.4 決策後流程

```
Human Decision: approve
  └─> 更新 state.checkpoint.human_decision = { "action": "approve", "by": "operator_001", "at": "..." }
  └─> resume_from: "selector"
  └─> 呼叫 tools/tabular_tool_selector.py::select_tabular_tools()

Human Decision: reject
  └─> 寫入 rejection record
  └─> 更新 cases/index.json → status=rejected
  └─> 流程終止，返回 { "ok": false, "checkpoint": "A-rejected", ... }

Human Decision: revise_plan
  └─> 進入 revise 子流程
  └─> Agent 接收修訂指令，重新生成 glue_plan
  └─> 回到 Checkpoint A（再次 await_human）
```

### 3.5 Resume 策略

```json
{
  "resume_context": {
    "checkpoint_id": "A-intake-confirmation",
    "case_ref": "demo_phase",
    "original_decision": { "decision": "needs_review", "risk_level": "medium" },
    "human_decision": { "action": "approve", "by": "operator_001", "at": "..." },
    "resume_from": "selector",
    "selector_task_type": "e2e",
    "planned_tools": ["validate.eligibility", "clean.phase_demo", "export.delivery_bundle"]
  }
}
```

**Resume 行為**:
- 若 `resume_from=selector`: 直接使用 checkpoint 中的 `planned_tools`，跳過 intake_decision_rules 重算
- 若 `resume_from=gate`: 從 eligibility validation 重新開始（人為 revise 選擇不同 path 時）

---

## 4. Checkpoint B: Delivery Confirmation

### 4.1 觸發條件

Agent 完成以下所有步驟後觸發:

1. Cleaning 完成（`clean.phase_demo` 或其他 cleaning tool）
2. Bundle 已生成（`reports/report.json`, `cleaned/*_cleaned.csv`, `delivery_signoff.md`）
3. `output_guard.status` 為 `ok` 或 `warning`

**特殊觸發條件**:
- `output_guard.status=warning`（建議人工檢視）
- 清洗後 row count 下降超過 90%（`input_rows * 0.1 > output_rows`）
- 任何 cleaning step 使用了 `--force`

**不觸發的情況**:
- E2E 失敗（`overall_ok=false`）— 直接進入 error handling，不經 Checkpoint B
- `output_guard.status=error`（自動終止）

### 4.2 Agent 輸出資料（Checkpoint 前必須準備）

```json
{
  "checkpoint": {
    "id": "B-delivery-confirmation",
    "version": "v1",
    "triggered_at": "2026-06-10T08:31:30Z",
    "case_ref": "demo_phase",
    "task_type": "tabular.cleaning.mvp"
  },
  "agent_output": {
    "execution_summary": {
      "tools_executed": [
        { "tool_id": "validate.eligibility", "ok": true, "exit_code": 2 },
        { "tool_id": "clean.phase_demo", "ok": true, "forced": true },
        { "tool_id": "export.delivery_bundle", "ok": true }
      ],
      "outbox_runs": [
        "2026-06-10T08-30-15Z_eligibility",
        "2026-06-10T08-30-45Z_phase_demo",
        "2026-06-10T08-31-15Z_delivery_bundle"
      ]
    },
    "cleaning_results": {
      "input_rows": 7,
      "output_rows": 5,
      "removed_rows": 2,
      "removal_ratio": 0.286,
      "qa_status": "pass_with_warnings"
    },
    "artifacts": {
      "eligibility_report": "reports/eligibility_result.json",
      "cleaned_csv": "cleaned/Phase_cleaned.csv",
      "delivery_bundle": "reports/delivery_bundle.zip",
      "signoff": "delivery_signoff.md"
    },
    "output_guard": {
      "status": "ok",
      "checks": {
        "ratio_check": "ok",
        "schema_check": "ok",
        "completeness_check": "ok"
      }
    },
    "delivery_draft": {
      "summary_text": "已清洗 7→5 rows，移除 2 行（duplicate/null）。輸出符合 Phase 表四欄格式。",
      "confidence_score": 0.92
    }
  },
  "human_decision": null,
  "state": {
    "status": "awaiting_human",
    "expires_at": "2026-06-10T08:36:30Z"
  }
}
```

### 4.3 Human 決策選項

| 選項 | 行為 | 後續流程 |
|------|------|----------|
| `approve_delivery` | 確認交付 | 更新 case status → `delivered`，notify client，流程結束 |
| `request_changes` | 要求修改 | 進入 revise 子流程，Agent 重新執行特定 step（如 re-clean with different params） |
| `hold` | 暫停 | case status → `on_hold`，保留所有 artifacts，等待進一步指示 |

### 4.4 決策後流程

```
Human Decision: approve_delivery
  └─> 更新 cases/index.json → status=delivered, delivered_at=...
  └─> 寫入 delivery_confirmation record
  └─> 通知 client（if configured）
  └─> 流程結束，返回 { "ok": true, "checkpoint": "B-approved", ... }

Human Decision: request_changes
  └─> 進入 revise 子流程
  └─> 顯示 revise 選項（re-clean, re-validate, re-bundle）
  └─> Agent 執行選定 step，回到 Checkpoint B（再次 await_human）

Human Decision: hold
  └─> 更新 cases/index.json → status=on_hold
  └─> 寫入 hold record
  └─> 流程暫停，等待 manual resume
```

### 4.5 Resume 策略

```json
{
  "resume_context": {
    "checkpoint_id": "B-delivery-confirmation",
    "case_ref": "demo_phase",
    "original_decision": { "action": "request_changes", "change_request": "re-clean with stricter null handling" },
    "human_decision": { "action": "approve_delivery", "by": "operator_002", "at": "..." },
    "resume_from": "delivery",
    "artifacts": { "eligibility_report": "...", "cleaned_csv": "..." }
  }
}
```

**Resume 行為**:
- 若 `resume_from=cleaning`: 重新執行 cleaning step，保留 gate/bundle 結果
- 若 `resume_from=bundle`: 重新執行 bundle step，保留 cleaning 結果
- 若 `resume_from=delivery`: 僅更新 status / notify，不重新執行任何 tool

---

## 5. State / Outbox / Trace 記錄

### 5.1 Checkpoint State Schema

```json
{
  "schema_version": "hitl_checkpoint_v1",
  "checkpoint_id": "A-intake-confirmation",
  "case_ref": "demo_phase",
  "run_id": "2026-06-10T08-30-00Z_intake_confirm",
  "status": "awaiting_human | approved | rejected | revised | timed_out",
  "created_at": "2026-06-10T08:30:00Z",
  "expires_at": "2026-06-10T08:35:00Z",
  "resolved_at": "2026-06-10T08:32:15Z",
  "agent_input": { ... },
  "agent_output": { ... },
  "human_decision": {
    "action": "approve",
    "operator_id": "operator_001",
    "comment": "",
    "timestamp": "2026-06-10T08:32:15Z"
  },
  "resume_context": { ... }
}
```

### 5.2 儲存位置

| 類型 | 路徑 | 說明 |
|------|------|------|
| Checkpoint state | `outbox/<case_ref>/checkpoint_<checkpoint_id>_<timestamp>.json` | 每個 checkpoint 獨立檔案 |
| Checkpoint events | `outbox/checkpoint_events.jsonl` | Append-only log |
| Case status | `cases/index.json` | 欄位 `hitl_status`, `checkpoint_pending` |

### 5.3 Trace 欄位

**L1 Business Trace** (MVP CLI stdout / JSON):
```json
{
  "step": "hitl.checkpoint",
  "checkpoint_id": "A-intake-confirmation",
  "status": "awaiting_human",
  "expires_at": "...",
  "resume_token": "<base64_encoded_resume_context>"
}
```

**Outbox integration**:
- Checkpoint state 參考相關的 outbox runs（`outbox/<case_ref>/<run_id>.json`）
- `checkpoint_events.jsonl` 與 `events.jsonl` 並存，但分離（checkpoint ≠ tool execution）

---

## 6. 為什麼只保留 1–2 個 Checkpoints？

### 6.1 效率考量

| 方案 | 每 case 平均暫停次數 | 人工時間/ case | 吞吐量預估 |
|------|---------------------|----------------|------------|
| **全自動**（無 HITL） | 0 | 0 min | 100% |
| **v1 設計（2 checkpoints）** | 0.3–0.5 | 1–2 min | 85–90% |
| **每步 HITL**（5+ checkpoints） | 3–5 | 10–15 min | 20–30% |
| **傳統人工審批** | 10+ | 30+ min | 5–10% |

**關鍵洞察**:
- Wave 1–4 實證：MVP 主鏈 6/6 regression 已能自動跑通 `demo_phase` 與 `sampleco`
- `needs_review` 僅占預估 20–30% cases（allowlist fixtures 多為 `auto_accept`）
- Checkpoint B 僅在 `warning` 或 `forced` cleaning 時觸發

### 6.2 風險分層

| 風險層級 | 對應機制 | HITL 角色 |
|----------|----------|-----------|
| **高風險** | `decision=reject`, `output_guard.status=error` | **自動阻斷**，無需人工 |
| **中風險** | `decision=needs_review`, `output_guard.status=warning` | **Checkpoint A/B** — 人工確認後放行 |
| **低風險** | `decision=auto_accept`, `risk_level=low` | **全自動**，無 HITL |
| **事後審計** | Outbox / L1 Trace / L2 observability | **Read-only**，不阻斷流程 |

- 高風險自動阻斷：避免人工疲勞導致的誤放行
- 中風險人工確認：保留品質閘門，但僅限必要時
- 低風險全自動：最大化吞吐量

### 6.3 可審計性

即使僅有 2 個 checkpoints，仍可完整追溯：

```
Case Lifecycle Audit Trail:
├── intake.json（原始輸入）
├── checkpoint_A-intake-confirmation.json（人工決策記錄）
├── outbox/<run_id>.json（每個 tool 執行記錄）
├── reports/*.json（業務產出）
├── checkpoint_B-delivery-confirmation.json（人工決策記錄）
└── delivery_signoff.md（最終交付）
```

- **無 checkpoint 觸發**: 仍有完整 outbox tool execution trace
- **Checkpoint 觸發**: 額外記錄人工決策 context
- **拒絕/暫停**: 明確記錄原因與時間戳

---

## 7. v1 不做什麼（NonScope）

### 7.1 外部通知整合

| 項目 | v1 狀態 | 未來可能 |
|------|---------|----------|
| Slack approval | ❌ 不做 | W5-T3+ |
| Email approval | ❌ 不做 | W5-T3+ |
| Telegram bot 互動 | ❌ 不做 | W5-T3+ |
| Web UI dashboard | ❌ 不做（Local UI 僅 read-only） | W5+ |

**原因**: 
- 外部通知需要額外的 async / webhook 基礎建設
- 會增加測試與維運複雜度
- v1 先建立 state / resume 基礎，通知層可後續擴展

### 7.2 長效 Workflow Engine

| 項目 | v1 狀態 | 說明 |
|------|---------|------|
| Durable workflow (Temporal / Cadence) | ❌ 不做 | v1 使用檔案-based state + resume CLI |
| Checkpoint 超過 24hr 自動清理 | ❌ 不做 | 僅記錄 `expires_at`，由 operator 決定 |
| 分散式 checkpoint 儲存 | ❌ 不做 | 僅本地 `outbox/` |

**v1 替代方案**:
- Checkpoint state 寫入 `outbox/` JSON 檔
- Resume 透過 CLI flag `--resume-from-checkpoint <path>`
- Timeout 僅為提示，不自動清理

### 7.3 任意步驟暫停

| 項目 | v1 狀態 | 說明 |
|------|---------|------|
| 任意 step 可設 checkpoint | ❌ 不做 | 僅固定 2 個 checkpoints |
| Dynamic checkpoint 配置 | ❌ 不做 | 不支援 `checkpoint_after=cleaning` 等自定義 |
| Pause/resume API | ❌ 不做 | Resume 透過 CLI 或 future Local UI |

**原因**: 
- 固定 2 個 checkpoints 簡化設計與測試
- 減少 resume 路徑的組合爆炸

### 7.4 多人簽核

| 項目 | v1 狀態 | 說明 |
|------|---------|------|
| 多級審批（初審/複審） | ❌ 不做 | 僅單一 operator decision |
| 簽核人角色區分 | ❌ 不做 | 無 `approver` / `reviewer` 角色區分 |
| 簽核流配置 | ❌ 不做 | 無 YAML / JSON 配置簽核流程 |

**v1 替代方案**:
- 單一 `operator_id` 欄位記錄決策者
- 若需多人，可在 `comment` 欄位記錄共識過程

### 7.5 其他 NonScope

- ❌ 不修改既有 `scripts/new_cleaning_case.py`, `app/local_ui.py`, E2E drivers
- ❌ 不寫入 Langfuse / PG `task_runs`（L2 observability 保持 adjacent）
- ❌ 不支援非 Tabular 家族（Gov / ask routes）
- ❌ 不做 checkpoint 統計分析（未來可從 `checkpoint_events.jsonl` 离线分析）

---

## 8. Resume CLI（Tabular unified driver · v1.1）

Tabular 主鏈 resume 已落地於 `scripts/run_hitl_checkpoint_cli.py`（子命令）與 `scripts/tabular_hitl_resume_lib.py`。

```bash
# CP-A approve + resume（demo_phase 範例）
python scripts/run_hitl_checkpoint_cli.py approve-a --case-id demo_phase --json
python scripts/run_hitl_checkpoint_cli.py resume-after-checkpoint --case-id demo_phase --json

# CP-B approve → approved_for_delivery
python scripts/run_hitl_checkpoint_cli.py approve-b --case-id demo_phase --json
python scripts/run_hitl_checkpoint_cli.py resume-after-checkpoint --case-id demo_phase --json

# Reject
python scripts/run_hitl_checkpoint_cli.py reject-a --case-id demo_phase --json
python scripts/run_hitl_checkpoint_cli.py reject-b --case-id demo_phase --json
```

**Resume step 對照**（詳見 `docs/tabular-hitl-resume-flow-v1.md`）：

| Checkpoint | Approve 後 | Reject 後 |
|------------|------------|-----------|
| CP-A | `checkpoint_resume_step=cleaning` | `stopped` |
| CP-B | `current_step=approved_for_delivery` · `completed` | `paused`（hold） |

Legacy outbox-only（實驗線／手動 path）仍可用：

```bash
python scripts/run_hitl_checkpoint_cli.py --apply-decision approve \
  --checkpoint-id A-intake-confirmation --notes "LGTM"
```

**仍屬 NonScope**：`revise_plan` 自動 replan、`request_changes` CLI 別名、過期 checkpoint 清理 CLI。

---

## 9. 與現有系統的關係

```
Existing System (Wave 1–5):
├── intake_decision_rules_v1 (W5-T1) ──┐
│                                      │
├── plan_tabular_route (W4-T1) ────────┼─► Checkpoint A (本設計)
│                                      │    [awaiting_human / approved / rejected]
├── select_tabular_tools (W3-TL-T2) ◄──┘
│                                      
├── execute_tabular_tool (W3-TL-T3) ───► outbox/<case_ref>/<run_id>.json
│                                      
├── tabular_outbox_consumer (W3-TL-T4) ┐
│                                      │
└── case bundle / delivery ◄───────────┴─► Checkpoint B (本設計)
                                             [awaiting_human / approved / changes_requested / hold]
```

**銜接點**:
1. Checkpoint A: 在 `intake_decision_rules_v1.py` 輸出 `needs_review` 時插入
2. Checkpoint B: 在 `tabular_outbox_consumer` 偵測到所有 planned_tools 完成後插入
3. Resume: 透過 CLI 讀取 checkpoint JSON，繼續後續流程

---

## 10. 驗收標準（本設計票）

| 項 | 驗收方式 |
|----|----------|
| 設計文件完成 | 本文件 `docs/hitl-checkpoints-v1.md` 存在且完整 |
| State schema 定義 | §5.1 JSON schema 明確 |
| Checkpoint A 流程 | §3 觸發條件、輸出、決策、resume 完整 |
| Checkpoint B 流程 | §4 觸發條件、輸出、決策、resume 完整 |
| NonScope 明確 | §7 列出 v1 不做項目 |
| 與現有系統關係 | §9 圖示與說明正確 |

**注意**: 本票僅設計，無程式碼、無 runner、無 test。實作票另開。

---

## 11. Cross References

| 文件 | 用途 |
|------|------|
| `docs/intake-decision-rules-v1.md` | Checkpoint A 前置 decision helper |
| `docs/routing-tool-layer-glue-v1.md` | `suggested_route` 結構來源 |
| `docs/tabular-tool-outbox-spec.md` | Checkpoint B 的 execution summary 來源 |
| `docs/tabular-outbox-consumer-spec.md` | Checkpoint B 觸發條件偵測 |
| `docs/mvp-standard-trace-path.md` | L1 trace 分層參考 |
| `04_Workflows/tickets/W5-T2-hitl-checkpoints-v1_state.md` | 本票施工狀態 |

---

*HITL-CHECKPOINTS-v1 · W5-T2 · Design Only · 2026-06-10*
