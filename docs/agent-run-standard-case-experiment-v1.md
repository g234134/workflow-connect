# Agent-Run Standard Case Experiment v1 — Tabular MVP 標準實驗線

> **版本**: v1.0 設計稿（Design Only · 本票不寫程式碼）
> **票號**: W6-T3 · Agent-run Standard Case Experiment
> **適用**: demo_phase / sampleco Tabular MVP 案型
> **日期**: 2026-06-10
> **上游依據**: `docs/ninety-five-percent-automation-blueprint-v1.md` · `docs/skill-cards-v1.md` · `docs/hitl-checkpoints-v1.md`

---

## §1 設計目標

定義一條「**Agent 主導 + 兩個 HITL checkpoint**」的標準實驗線，從 S1 Intake Upload 到 S15 Client Notify，讓未來可以用一張實作票（如 W6-T5/W6-T8）把它變成可重跑的實驗流程。

**核心約束**:
- 限定在 **demo_phase** / **sampleco** 兩個 Tabular MVP 案型
- 只做 **設計與文檔**，本票不寫程式碼
- 明確標示每個步驟的驅動者（Agent / Script / Human）
- 預留兩個 HITL checkpoint（A: Intake Confirmation, B: Delivery Confirmation）

---

## §2 15 步標準實驗線

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                    AGENT-RUN STANDARD CASE EXPERIMENT — 15 STEPS                         │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  [S1]      [S2]        [S3]         [S4]        [S5]        [S6]        [S7]            │
│ INTAKE → INDEX → DECISION_EVAL → CP-A → ROUTE_PLAN → TOOL_SELECT → GATE_VALID          │
│  Upload  Refresh   (W5-T1)       (HITL)   (W4-T1)   (W3-TL-T2)  (auto)                 │
│                                                                                          │
│                                     ↓                                                    │
│  [S8]        [S9]        [S10]       [S11]       [S12]       [S13]       [S14]   [S15]  │
│ CLEAN → OUTBOX → BUNDLE_BUILD → OUTPUT_GUARD → CP-B → DELIVERY → LEDGER → NOTIFY    │
│ (auto)  (W3-TL-T3)  (auto)      (auto)       (HITL)   (HITL)    (auto)   (auto)      │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## §3 步驟詳細規格

### S1: Intake Upload（接案上傳）

| 屬性 | 內容 |
|------|------|
| **現狀** | human-only |
| **目標** | **HITL**（Agent 輔助 + Human 確認） |
| **驅動者** | Human operator（未來: Agent + Human confirm） |
| **CLI/Module** | `scripts/new_cleaning_case.py` |
| **輸入** | `--client-ref`, `--case-id`, `--data-file`, `--product-sku` |
| **輸出** | `cases/{client}/{case_id}/intake.json` + `raw/` 目錄 |

**Agent 整合設計（未來實作）**:
```bash
# 未來實作: Agent 接收上傳請求，自動建議 case_id
python scripts/run_agent_intake_decision_demo.py \
  --task-type tabular.intake.new_case \
  --case-dir cases/demo_phase \
  --format json
# → 輸出 decision=auto_accept，觸發 S2
```

**與 W5-T1 關係**: 使用 `evaluate_intake_decision("tabular.intake.new_case", case_dir)` 做 intake 決策

---

### S2: Index Refresh（索引刷新）

| 屬性 | 內容 |
|------|------|
| **現狀** | auto |
| **目標** | **auto**（維持） |
| **驅動者** | Script |
| **CLI/Module** | `scripts/build_cases_index.py` |
| **輸入** | —（掃描 `cases/` 目錄） |
| **輸出** | `cases/index.json` 更新 |

**驗證信號**: `ok=true`, `cases_written≥2`

---

### S3: Decision Evaluate（決策評估）

| 屬性 | 內容 |
|------|------|
| **現狀** | partial auto |
| **目標** | **auto** |
| **驅動者** | Agent（呼叫 W5-T1 decision helper） |
| **CLI/Module** | `scripts/run_agent_intake_decision_demo.py` |
| **核心函數** | `routing/intake_decision_rules_v1.py::evaluate_intake_decision()` |
| **輸入** | `task_type=tabular.cleaning.mvp`, `case_dir` |
| **輸出** | `decision: auto_accept / needs_review / reject` + `risk_level` + `suggested_route` |

**Agent 呼叫方式**:
```python
# Agent 內部呼叫
from routing.intake_decision_rules_v1 import evaluate_intake_decision

result = evaluate_intake_decision(
    task_type="tabular.cleaning.mvp",
    case_dir="cases/demo_phase"
)
# result → {
#   "ok": True,
#   "decision": "needs_review",  # demo_phase 預期結果
#   "risk_level": "medium",
#   "suggested_route": { ... }
# }
```

**決策後分支**:
- `auto_accept` + `low` risk → 跳過 S4 (Checkpoint A)，直接進 S5
- `needs_review` + `medium` risk → **觸發 S4 (Checkpoint A)**
- `reject` → 流程終止，寫入 rejection record

---

### S4: Checkpoint A — Intake Confirmation（接案確認）

| 屬性 | 內容 |
|------|------|
| **現狀** | planned（W5-T2 設計） |
| **目標** | **HITL** |
| **驅動者** | **Human**（決策者）+ Agent（準備資料） |
| **觸發條件** | `decision=needs_review` OR `risk_level=medium` |
| **CLI/Module** | `scripts/run_agent_intake_decision_demo.py`（產生 checkpoint 資料） |
| **設計參考** | `docs/hitl-checkpoints-v1.md` §3 |

**Agent 準備資料（checkpoint state）**:
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
    "intake_decision": { ... },
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
    },
    "suggested_route": {
      "selector_task_type": "e2e",
      "planned_tools": [
        "validate.eligibility",
        "clean.phase_demo",
        "export.delivery_bundle"
      ]
    }
  },
  "human_decision": null,
  "state": {
    "status": "awaiting_human",
    "expires_at": "2026-06-10T08:35:00Z"
  }
}
```

**Human 決策選項**:
| 選項 | 行為 | 後續流程 |
|------|------|----------|
| `approve` | 同意 Agent 建議的 route | 進入 S5 (Route Planning) |
| `reject` | 否決此案 | 寫入 rejection record，流程終止 |
| `revise_plan` | 修改 planned_tools | 進入 revise 子流程，Agent 重新生成 plan |

**預設行為**: `approve`（timeout 5 分鐘後自動放行）

**Resume Context**（供 S5 消費）:
```json
{
  "resume_context": {
    "checkpoint_id": "A-intake-confirmation",
    "case_ref": "demo_phase",
    "human_decision": { "action": "approve", "by": "operator_001", "at": "..." },
    "resume_from": "selector",
    "selector_task_type": "e2e",
    "planned_tools": ["validate.eligibility", "clean.phase_demo", "export.delivery_bundle"]
  }
}
```

---

### S5: Route Planning（路由規劃）

| 屬性 | 內容 |
|------|------|
| **現狀** | auto |
| **目標** | **auto**（維持） |
| **驅動者** | Script（呼叫 W4-T1 glue） |
| **CLI/Module** | `routing/intake_to_tabular_glue.py::plan_tabular_route()` |
| **輸入** | `task_type`, `case_dir` |
| **輸出** | `glue_plan`: `selector_task_type`, `planned_tools[]`, `case_profile` |

**與 S4 關係**: 若 S4 checkpoint 決定 `approve`，直接使用 checkpoint 中的 `planned_tools` 與 `selector_task_type`，跳過重算

---

### S6: Tool Selection（工具選擇）

| 屬性 | 內容 |
|------|------|
| **現狀** | auto |
| **目標** | **auto**（維持） |
| **驅動者** | Agent（呼叫 W3-TL-T2 selector） |
| **CLI/Module** | `tools/tabular_tool_selector.py::select_tabular_tools()` |
| **輸入** | `case_dir`, `task_type`, `intake`, `gate_notes` |
| **輸出** | `candidate_tools[]` with `tool_id`, `reason`, `requires_force`, `human_review_required` |

**關鍵呼叫**:
```python
# Agent 內部呼叫
candidates = select_tabular_tools(
    case_dir="cases/demo_phase",
    task_type="tabular.cleaning.mvp",
    intake=intake_data,
    gate_notes=["phase_like", "phase_demo"]
)
# → [{"tool_id": "clean.phase_demo", "requires_force": true, ...}]
```

---

### S7: Gate Validation（資格驗證）

| 屬性 | 內容 |
|------|------|
| **現狀** | auto |
| **目標** | **auto**（維持） |
| **驅動者** | Script |
| **CLI/Module** | `scripts/check_case_eligibility.py` |
| **輸入** | `--case-dir cases/demo_phase --json` |
| **輸出** | `eligibility_result.json` → `status: review_needed/accepted/rejected` |

**demo_phase 預期**: `status=review_needed`, `exit_code=2`, `reason_code=rows<100`

**sampleco 預期**: `status=accepted`, `exit_code=0`

---

### S8: Cleaning Execution（清洗執行）

| 屬性 | 內容 |
|------|------|
| **現狀** | auto |
| **目標** | **auto**（維持） |
| **驅動者** | Script |
| **CLI/Module** | `notebooks/csv_cleaning/clean_phase_demo.py` |
| **輸入** | `--case-dir cases/demo_phase --skip-eligibility [--force]` |
| **輸出** | `cleaned/Phase_cleaned.csv` + `reports/report.json` |

**demo_phase**: 需要 `--force`（因 S7 exit 2）
**sampleco**: 不需 `--force`（因 S7 exit 0）

**預期結果**:
| Case | Input Rows | Output Rows | Removal Ratio |
|------|-----------|-------------|---------------|
| demo_phase | 7 | 5 | 28.6% |
| sampleco | 115 | 8 | 93.0% |

---

### S9: Outbox Write（出箱寫入）

| 屬性 | 內容 |
|------|------|
| **現狀** | auto |
| **目標** | **auto**（維持） |
| **驅動者** | Script（W3-TL-T3 executor） |
| **CLI/Module** | `tools/tabular_tool_executor.py` + `tools/tabular_outbox_writer.py` |
| **輸出** | `outbox/{case_ref}/{run_id}.json` |

**每個 tool 執行後都寫入 outbox**:
- `outbox/demo_phase/2026-06-10T08-30-00Z_eligibility.json`
- `outbox/demo_phase/2026-06-10T08-30-30Z_phase_demo.json`
- `outbox/demo_phase/2026-06-10T08-31-00Z_delivery_bundle.json`

---

### S10: Bundle Build（交付包建置）

| 屬性 | 內容 |
|------|------|
| **現狀** | auto |
| **目標** | **auto**（維持） |
| **驅動者** | Script |
| **CLI/Module** | `scripts/build_case_delivery_bundle.py` |
| **輸入** | `--case-dir cases/demo_phase --json` |
| **輸出** | `delivery_signoff.md` + bundle artifacts |

---

### S11: Output Guard（輸出守衛）

| 屬性 | 內容 |
|------|------|
| **現狀** | auto |
| **目標** | **auto**（維持） |
| **驅動者** | Script（內嵌於 bundle build） |
| **輸出** | `output_guard.status: ok / warning / error` |

**觸發 S12 Checkpoint B 的條件**:
- `output_guard.status=warning`
- `removal_ratio > 0.5`（如 sampleco 93% 刪減）
- `forced_cleaning=true`

**demo_phase**: `status=ok`（不觸發 Checkpoint B）
**sampleco**: `status=warning`（觸發 Checkpoint B）

---

### S12: Checkpoint B — Delivery Confirmation（交付確認）

| 屬性 | 內容 |
|------|------|
| **現狀** | planned（W5-T2 設計） |
| **目標** | **HITL** |
| **驅動者** | **Human**（決策者）+ Agent（準備資料） |
| **觸發條件** | `output_guard.status=warning` OR `removal_ratio>0.5` OR `forced_cleaning=true` |
| **設計參考** | `docs/hitl-checkpoints-v1.md` §4 |

**Agent 準備資料**:
```json
{
  "checkpoint": {
    "id": "B-delivery-confirmation",
    "version": "v1",
    "triggered_at": "2026-06-10T08:31:30Z",
    "case_ref": "demo_phase"
  },
  "agent_output": {
    "execution_summary": {
      "tools_executed": [
        { "tool_id": "validate.eligibility", "ok": true, "exit_code": 2 },
        { "tool_id": "clean.phase_demo", "ok": true, "forced": true },
        { "tool_id": "export.delivery_bundle", "ok": true }
      ]
    },
    "cleaning_results": {
      "input_rows": 7,
      "output_rows": 5,
      "removed_rows": 2,
      "removal_ratio": 0.286
    },
    "output_guard": {
      "status": "ok",
      "checks": { "ratio_check": "ok", "schema_check": "ok" }
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

**Human 決策選項**:
| 選項 | 行為 | 後續流程 |
|------|------|----------|
| `approve_delivery` | 確認交付 | 進入 S13 (Delivery Approval) |
| `request_changes` | 要求修改 | 進入 revise 子流程，重新執行特定 step |
| `hold` | 暫停 | case status → `on_hold`，等待進一步指示 |

**預設行為**: `hold`（timeout 不自動放行，品質把關）

---

### S13: Delivery Approval（交付批准）

| 屬性 | 內容 |
|------|------|
| **現狀** | human-only |
| **目標** | **HITL**（輕量確認） |
| **驅動者** | **Human**（一鍵確認） |
| **觸發條件** | Checkpoint B `approve_delivery` 或自動通過（no warning） |
| **CLI/Module** | 未來: `scripts/approve_delivery.py` |
| **輸出** | `cases/index.json` → `status=delivered` |

**v1 設計**: 人工閱讀 `delivery_signoff.md` 後，一鍵確認（或透過 Telegram/Slack bot）

---

### S14: Ledger Update（帳本更新）

| 屬性 | 內容 |
|------|------|
| **現狀** | auto |
| **目標** | **auto**（維持） |
| **驅動者** | Script（W3-TL-T4 consumer） |
| **CLI/Module** | `tools/tabular_outbox_consumer.py` |
| **輸出** | `outbox/events.jsonl` + `cases/index.json` sync |

---

### S15: Client Notify（客戶通知）

| 屬性 | 內容 |
|------|------|
| **現狀** | human-only |
| **目標** | **auto**（未來實作） |
| **驅動者** | Script（未來: `app/notification_gateway.py`） |
| **v1 設計** | 預留介面，實作另開 W6-T10 |

**未來設計**:
```bash
python app/notification_gateway.py \
  --case-ref demo_phase \
  --channel telegram \
  --message "Case demo_phase delivered. Bundle: cases/demo_phase/reports/"
```

---

## §4 驅動者分布摘要

| 分類 | 步驟 | 數量 | 說明 |
|------|------|------|------|
| **Auto (Agent/Script)** | S2, S3, S5, S6, S7, S8, S9, S10, S11, S14 | 10 | Agent 自主執行，無需人工介入 |
| **HITL (Human 決策)** | S4 (Checkpoint A), S12 (Checkpoint B), S13 (Delivery Approval) | 3 | Agent 準備資料，Human 做決策 |
| **Human-only (v1)** | S1 (Intake Upload), S15 (Client Notify) | 2 | 純人工，未來轉 HITL/auto |

**自動化率計算**:
```
現在: (10 + 0×0.5) / 15 = 67%  # HITL 未實作，算 manual
目標: (11 + 3×0.5) / 15 = 87%  # S1/S15 轉 HITL + Checkpoint 半自動
95% 藍圖: (12 + 2×0.5) / 15 = 93%  # S13 也轉 auto
```

---

## §5 Agent 呼叫點明細

### 呼叫點 1: S3 Decision Evaluate

```python
# 模組: routing/intake_decision_rules_v1.py
# CLI: scripts/run_agent_intake_decision_demo.py

result = evaluate_intake_decision(
    task_type="tabular.cleaning.mvp",
    case_dir="cases/demo_phase"
)

# 預期輸出 (demo_phase):
{
    "ok": True,
    "decision": "needs_review",
    "risk_level": "medium",
    "rationale": ["task_type=tabular.cleaning.mvp", "manual_review_required"],
    "suggested_route": {
        "selector_task_type": "e2e",
        "planned_tools": [
            "validate.eligibility",
            "clean.phase_demo",
            "export.delivery_bundle"
        ],
        "orchestration_tool_id": "orchestrate.e2e"
    }
}
```

### 呼叫點 2: S5-S6 Route + Select

```python
# 模組: routing/intake_to_tabular_glue.py (W4-T1)
# 模組: tools/tabular_tool_selector.py (W3-TL-T2)

# Agent 內部呼叫鏈:
glue_plan = plan_tabular_route("tabular.cleaning.mvp", "cases/demo_phase")
candidates = select_tabular_tools(
    case_dir="cases/demo_phase",
    task_type="tabular.cleaning.mvp",
    intake=intake_data,
    gate_notes=glue_plan["inferred_gate_notes"]
)
```

**等價 CLI（預演）**:
```bash
python scripts/run_tabular_intake_tool_path.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --json
# → 輸出 glue_plan + selector_view + executor_plan（dry-run only）
```

---

## §6 Checkpoint 狀態機

### Checkpoint A 狀態流

```
[S3 decision=needs_review]
       ↓
[Agent 準備 checkpoint 資料]
       ↓
[狀態: awaiting_human] ←──┐
       ↓                  │
   [Human 決策]            │
   ├─ approve ─→ [resume_from=selector] ─→ S5
   ├─ reject ─→ [流程終止]
   └─ revise_plan ─→ [Agent 重算 plan] ─→ 回到 awaiting_human
```

### Checkpoint B 狀態流

```
[S11 output_guard.status=warning]
       ↓
[Agent 準備 checkpoint 資料]
       ↓
[狀態: awaiting_human] ←──┐
       ↓                  │
   [Human 決策]            │
   ├─ approve_delivery ─→ S13
   ├─ request_changes ─→ [revise 子流程] ─→ 回到 awaiting_human
   └─ hold ─→ [狀態: on_hold] ─→ 等待 manual resume
```

---

## §7 前置條件與 Fixtures

### 必要 Fixtures

| Fixture | 路徑 | 用途 |
|---------|------|------|
| demo_phase | `cases/demo_phase/` | Gate exit 2 + `--force` 路徑測試 |
| sampleco | `cases/sampleco/2026-0001/` | Gate exit 0 + warning ratio 測試 |

### 前置檔案檢查清單

```bash
# S1 前必須存在
cases/demo_phase/intake.json
cases/demo_phase/raw/Phase.csv
cases/sampleco/2026-0001/intake.json
cases/sampleco/2026-0001/raw/sampleco_milestone_export.csv

# S7 前必須可呼叫
scripts/check_case_eligibility.py

# S8 前必須可呼叫
notebooks/csv_cleaning/clean_phase_demo.py

# S10 前必須可呼叫
scripts/build_case_delivery_bundle.py
```

---

## §8 常見卡住點與 Fallback

### 卡住點 1: Gate 誤判（S7）

**症狀**: `demo_phase` 本應 `review_needed` (exit 2)，卻得到 `accepted` (exit 0)

**可能原因**:
- `cases/index.json` 中 `gate_status` 被手動改過
- `raw/Phase.csv` 行數被修改（非 7 行）

**Fallback**:
```bash
# 1. 檢查 raw 檔案
wc -l cases/demo_phase/raw/Phase.csv
# 預期: 8 (含 header + 7 data rows)

# 2. 重建 index
python scripts/build_cases_index.py

# 3. 重跑 gate
python scripts/check_case_eligibility.py --case-dir cases/demo_phase --json
```

### 卡住點 2: Cleaning 失敗（S8）

**症狀**: `clean.phase_demo` exit 1，`requires_force=true` 但未加 `--force`

**Fallback**:
```bash
# 確認需要 force
cat cases/demo_phase/reports/eligibility_result.json | grep status
# → "review_needed"

# 重跑 cleaning 加 --force
python notebooks/csv_cleaning/clean_phase_demo.py \
  --case-dir cases/demo_phase \
  --skip-eligibility \
  --force
```

### 卡住點 3: Checkpoint 狀態遺失

**症狀**: Checkpoint A/B 準備好資料後，程序 crash，狀態未寫入

**Fallback**:
```bash
# 檢查 outbox 是否有 checkpoint 檔案
ls -la outbox/demo_phase/checkpoint_*.json

# 若無，從頭重跑（本設計不支援 mid-checkpoint resume v1）
python scripts/run_agent_intake_decision_demo.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --format json
```

---

## §9 NonScope（本設計不做）

| 項目 | v1 狀態 | 說明 |
|------|---------|------|
| Retry / DLQ 機制 | ❌ 不做 | 見 `docs/ninety-five-percent-automation-blueprint-v1.md` §6.1 G6；另開 W6-T7 |
| 真實金流整合 | ❌ 不做 | 本設計限 Tabular MVP，不含 payment gateway |
| 真實 Email/Slack 通知 | ❌ 不做 | S15 為設計預留，實作另開 W6-T10 |
| 多級審批流程 | ❌ 不做 | Checkpoint 僅單一 operator decision |
| 24hr+ 長效 checkpoint | ❌ 不做 | Timeout 僅為提示，不自動清理 |
| 任意步驟可設 checkpoint | ❌ 不做 | 僅固定 2 個 checkpoints |
| Langfuse / PG trace 接線 | ❌ 不做 | L2 observability 為 adjacent，未接線 |
| Non-tabular 案型 | ❌ 不做 | 僅限 `demo_phase`, `sampleco` |

---

## §10 與現有產物的對照索引

| 本設計引用 | 現有產物位置 | 狀態 |
|-----------|-------------|------|
| W5-T1 Decision Rules | `routing/intake_decision_rules_v1.py` | ✅ done |
| W5-T1B Agent Entry | `scripts/run_agent_intake_decision_demo.py` | ✅ done |
| W5-T2 HITL Design | `docs/hitl-checkpoints-v1.md` | ✅ 設計 done |
| W4-T1 Glue | `routing/intake_to_tabular_glue.py` | ✅ done |
| W4-T3-A Intake Path | `scripts/run_tabular_intake_tool_path.py` | ✅ done |
| W3-TL-T2 Selector | `tools/tabular_tool_selector.py` | ✅ done |
| W3-TL-T3 Executor | `tools/tabular_tool_executor.py` | ✅ done |
| W3-TL-T4 Consumer | `tools/tabular_outbox_consumer.py` | ✅ done |
| W6-T1 Skill Cards | `docs/skill-cards-v1.md` | ✅ done |
| W6-T2 95% Blueprint | `docs/ninety-five-percent-automation-blueprint-v1.md` | ✅ done |
| W6-T4 Orchestrator CLI | `scripts/run_agent_standard_case_experiment.py` | ✅ v1 preview/run |
| W6-T5 Checkpoint A 整合 | `hitl/checkpoint_a_integration_v1.py` | ✅ 整合層 done |
| W6-T6 Checkpoint B 整合 | `hitl/checkpoint_b_integration_v1.py` | ✅ 整合層 done |
| **收口總結** | `docs/agent-standard-line-v1-summary.md` | ✅ Reviewer handoff |

---

## §11 驗證設計（Future Implementation）

### 未來實作票（W6-T5, W6-T8）驗收標準

| AC | 驗收方式 | 對應本設計 |
|----|----------|-----------|
| AC-1 | 15 個步驟都有「模組 / 驅動者 / HITL 分類」 | §3 各步驟表格 |
| AC-2 | demo_phase 完整走一次「理想 happy path」 | §3 S1–S15 流程 |
| AC-3 | 標出 2–3 個「最可能卡住的點」與 fallback | §8 卡住點 |
| AC-4 | NonScope 明確寫出 v1 不處理哪些情形 | §9 NonScope |

### Happy Path 驗證命令（設計預覽）

```bash
# 未來實作完成後，可用以下命令驗證

# 1. 完整實驗線（dry-run mode）
python scripts/run_standard_case_experiment.py \
  --case-ref demo_phase \
  --mode dry-run \
  --checkpoints enabled

# 2. 僅執行 auto 步驟（skip HITL）
python scripts/run_standard_case_experiment.py \
  --case-ref demo_phase \
  --skip-checkpoints

# 3. 從 Checkpoint A resume
python scripts/resume_from_checkpoint.py \
  --checkpoint outbox/demo_phase/checkpoint_A-intake-confirmation_*.json \
  --action approve
```

---

## §12 版本記錄

| 版本 | 日期 | 變更 |
|------|------|------|
| v1.0 | 2026-06-10 | W6-T3 初始設計；15 步流程定義；Checkpoint A/B 整合 |

---

*AGENT-RUN-STANDARD-CASE-EXPERIMENT-v1 · W6-T3 · Design Only · 2026-06-10*
