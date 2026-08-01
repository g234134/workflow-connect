# Standard-Case HITL / Resume / Notify — 新工程師入門指南

> **版本**: v1.0 (W6 v2)  
> **對象**: 新加入的工程師  
> **前提**: 已熟悉 agent standard-case experiment line 基本流程（S3→S5→S6→...）

---

## 1. High-level Picture：整條 pipeline 一眼看懂

這一節用 bullet 流程圖呈現從 S3 到 S13 + Checkpoint A/B + Resume + Notify 的完整路徑。

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Agent Standard-Case Pipeline v2                         │
└─────────────────────────────────────────────────────────────────────────────────┘

【S3-S6: 前置流程 — Intake Phase】
• S3 Decision → S5 Route → S6 Tool preview
  ↓
  ├─ 需要人工確認？──────────────────────────────→ 【Checkpoint A: Intake Gate】
  │                                                (S4 寫入 checkpoint A 檔案)
  │
  └─ 自動通過（auto_approved）→ 繼續 S7+ 執行路徑

【Checkpoint A: Intake Confirmation】
• 觸發條件：S6 判定 needs_review 且未帶 --auto-approve-intake
• 行為：
  - preview mode: 計算 would_pause（不寫檔）
  - run mode: 寫入 outbox/<case_ref>/checkpoint_A_*.json，status=awaiting_human
• 人類決策選項（透過 run_hitl_checkpoint_cli --apply-decision）：
  - approve → 可 resume 進入 S7
  - revise_plan → 需要人工改 plan，v1 不支援 resume
  - reject → 終止，v1 不支援 resume

【Resume from A → S7+】
• 命令：--resume-checkpoint <checkpoint_A_path> --mode run
• 驗證：validate_resume_eligibility() 檢查
  - status 必須是 approved
  - case_ref / task_type 必須與 CLI 一致
  - 不能是 preview mode
  - 不能是 awaiting_human / rejected / revise_needed / on_hold
• 成功後：跳過 S3-S6，直接進入 S7+ 執行

【S7-S12: 執行階段 — Tool Execution + Output Guard】
• S7+ 執行 planned tools → S12 產出 output_guard 評估
  ↓
  ├─ output_guard = warning / blocked ─────────→ 【Checkpoint B: Delivery Gate】
  │                                               (寫入 checkpoint B 檔案)
  │
  ├─ output_guard = ok + --auto-approve-delivery → 跳過 B，直接進 S13
  │
  └─ output_guard = error ─────────────────────→ 終止，不寫 checkpoint B

【Checkpoint B: Delivery Confirmation】
• 觸發條件：output_guard 判定需要人工確認 delivery
• 行為：
  - preview: 計算 would_trigger（不寫檔）
  - run: 寫入 checkpoint_B_*.json，status=awaiting_human 或 stopped_before_delivery
• 人類決策選項：
  - approve_delivery → 可 resume 進入 S13 執行 delivery
  - request_changes → 需要修改，v1 不支援 resume
  - hold → 暫停處理，v1 不支援 resume

【Resume from B → S13】
• 命令：--resume-checkpoint <checkpoint_B_path> --mode run
• 驗證：與 A 類似，額外檢查
  - artifacts 存在性（eligibility_report, cleaned_csv）
  - 不能重複 delivery（outbox marker 防重複）
• 成功後：跳過 S3-S12，直接執行 S13 Delivery export

【S13: Delivery Export】
• 產生 delivery bundle
• Sandbox e2e 路徑可能走到 S10 Sandbox bundle

【Notification Gateway: 選配的通知層】
• 預設：關閉（零副作用）
• 啟用：--enable-notifications 或 env GOV_NOTIFICATION_GATEWAY_ENABLED=1
• 只在 mode=run 時發送事件
• 事件類型：
  - checkpoint.awaiting_human (A 或 B 等待人工)
  - checkpoint.approved (A 自動/人工通過 或 B 通過)
  - delivery.bundle_ready (bundle 產生完成)
  - run.completed (run 正常結束)
  - run.blocked (run 被阻擋/失敗)
  - intake.gate_decision (Intake Gate run 模式 + notifications 啟用；P75-G4)
• 輸出：
  - 個別事件檔案: outbox/notifications/<case_ref>/<event_id>.json
  - 彙整 log: outbox/notification_events.jsonl
• 特性：best-effort（失敗不影響 orchestrator ok 狀態）

【完整流程摘要】
S3 → S5 → S6 ──┬─[needs_review]→ Checkpoint A ──[human approve]──┐
               │    (awaiting_human)            (resume)         │
               │                                    ↓              │
               └──[auto_approved]────────────────→ S7+ ────────────┘
                                                    ↓
                                                  S12 ──┬─[warning/blocked]→ Checkpoint B
                                                        │   (awaiting_human)
                                                        │
                                                        └──[ok+auto_approve]→ S13/S10
                                                               ↓
                                                    [human approve_delivery]
                                                               ↓
                                                           (resume)
                                                               ↓
                                                            S13 Export
                                                               ↓
                                                      [notification events]
```

---

## 2. Key Concepts：新手必懂的三個核心概念

### 2.1 Checkpoint A vs Checkpoint B

| 層級 | 時機 | 目的 | 寫入時機 |
|------|------|------|----------|
| **Checkpoint A** | Intake 階段 (S6 之後) | 確認 intake decision / tool plan 是否正確 | needs_review 且未 auto-approve |
| **Checkpoint B** | Delivery 階段 (S12 之後) | 確認 output guard 結果，是否可交付 | warning/blocked 且未 auto-approve |

**簡單記法**：
- A = Approval（進來時要人類點頭）
- B = Before delivery（出去前要人類確認）

**檔案位置**：
```
outbox/
  <case_ref>/
    checkpoint_A_<timestamp>_<id>.json   # Intake gate
    checkpoint_B_<timestamp>_<id>.json     # Delivery gate
  notifications/
    <case_ref>/
      <event_id>.json                      # 個別通知事件
  notification_events.jsonl                  # 彙整 JSONL
```

### 2.2 Human Gate / Resume / Fail-Close

這三個詞是整個 HITL 系統的設計哲學：

**Human Gate（人工閘門）**
- 機器跑到某個點，發現需要人類判斷，就停下來寫一個 checkpoint 檔案
- 狀態標為 `awaiting_human`
- 人類用 CLI 工具看內容、做決定：approve / revise / reject（A）或 approve_delivery / request_changes / hold（B）

**Resume（恢復執行）**
- 人類決定「繼續」後，用 `--resume-checkpoint <path>` 告訴 orchestrator 從哪裡接續
- Resume 會**跳過前面所有步驟**，直接從斷點後繼續
  - A resume → 直接進 S7+（跳過 S3-S6）
  - B resume → 直接進 S13（跳過 S3-S12）
- Resume **必須**用 `--mode run`，preview 不允許 resume

**Fail-Close（故障時關閉）**
- Resume 有嚴格的驗證，任何可疑狀況都會 `blocked` 不給過
- 這是安全設計：寧可擋掉合法的 resume，也不要讓錯誤的 resume 跑過去
- 常見被擋的情況：
  - checkpoint 狀態不是 approved（還在等待人類、被拒絕、需要修改）
  - case_ref 或 task_type 對不上（換了 case 或 task type）
  - artifacts 不見了（檔案被刪或過期）
  - 重複 delivery（同一個 B 被 resume 兩次）

### 2.3 Notification Event / Best-Effort

**Notification Event（通知事件）**
- 當 `--enable-notifications` 開啟時，orchestrator 會在關鍵節點發送事件
- 這是給下游系統看的「工作流狀態廣播」，不是核心邏輯
- 事件帶有 `idempotency_key`，下游可用來去重

**Best-Effort（盡力而為）**
- 通知系統失敗**不會**讓整個 run 失敗
- 寫入失敗、exception、lock 搶不到 → 都只是記錄 error dict，不 raise
- Orchestrator 的 `ok` 和 `final_status` 完全不受通知影響
- 為什麼這樣設計？通知是「觀測性」功能，不是「可靠性」功能

### 2.4 Intake Gate 上游入口（P75-G4）

Gate 決策與 orchestrator S3 共用 `routing/intake_gate_layer_v1.evaluate_intake_gate()`，但 **獨立 CLI** 適合 PM / 整合測試：

```bash
# Preview — 不寫 outbox、不發 notify
python scripts/run_intake_gate_cli.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode preview --format json

# Run — 寫 outbox record；加 --enable-notifications 發 intake.gate_decision
python scripts/run_intake_gate_cli.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode run --enable-notifications --format json

# 稽核：合併 workflow 通知流
python scripts/inspect_workflow_events.py --case-ref demo_phase --format json
```

**範例 `intake.gate_decision` payload（節錄）**：

```json
{
  "schema_version": "notification_event_v1",
  "event_type": "intake.gate_decision",
  "case_ref": "demo_phase",
  "checkpoint_id": "igd_2026-06-19T10-00-00Z_demo_phase_tabular.cleaning.mvp",
  "artifacts": {
    "intake_decision_id": "igd_2026-06-19T10-00-00Z_demo_phase_tabular.cleaning.mvp",
    "decision": "review_needed",
    "reason_codes": ["manual_review_required", "allowlist_fixture"],
    "policy_version": "intake_gate_policy_v1",
    "outbox_record_path": "outbox/demo_phase/intake_gate_decision_....json"
  },
  "status_summary": {
    "decision": "review_needed",
    "reason_codes": ["manual_review_required", "allowlist_fixture"],
    "policy_version": "intake_gate_policy_v1",
    "intake_decision_id": "igd_...",
    "outbox_record_path": "outbox/demo_phase/intake_gate_decision_....json"
  }
}
```

Notify 失敗 **不會** 讓 gate `ok=false`（best-effort，與 W6 gateway 一致）。Orchestrator S3 已呼叫同一 gate layer；`intake.gate_decision` 目前由 **gate CLI** 在 run + `--enable-notifications` 時 emit。

---

## 3. How to Debug：遇到問題先看哪裡

### 3.1 出現 "blocked" 時

**Step 1: 看 orchestrator 輸出的 `final_status`**
```bash
python scripts/run_agent_standard_case_experiment.py ... --format json
# 看 "final_status" 欄位
```

**Step 2: 對照 final_status 查原因**

| final_status | 可能原因 | 查看位置 |
|--------------|----------|----------|
| `blocked` | 一般性阻擋 | 看 `message` 欄位說明 |
| `checkpoint_mismatch` | case_ref 或 task_type 對不上 | 檢查 `--case-dir` 和 `--task-type` 是否與 checkpoint 一致 |
| `duplicate_delivery` | 同一個 checkpoint B 被 resume 兩次 | 看 outbox 是否有 `.delivery_marker` 檔案 |
| `stale_checkpoint` | checkpoint 過期（expires_at 已過）且還在 awaiting_human | 檢查 checkpoint JSON 的 `expires_at` |
| `waiting_for_human` | 正常暫停，等待人工決定 | 看 checkpoint 檔案的 `status` 是否 awaiting_human |

**Step 3: 看 resume 子物件的詳細錯誤**
```json
{
  "ok": false,
  "final_status": "blocked",
  "resume": {
    "checkpoint_loaded": true,
    "eligible": false,
    "message": "checkpoint status is awaiting_human, not approved"
  }
}
```

### 3.2 出現 "duplicate" 時

**檢查點**：outbox marker 檔案
```bash
# marker 檔案位置（檔名包含 checkpoint id）
ls outbox/<case_ref>/.*.delivery_marker*

# 如果存在 marker，表示這個 checkpoint B 已經 delivery 過了
# 需要手動刪除 marker 才能再次 resume（v1 設計：刪除即允許重送）
```

### 3.3 出現 "stale" 時

**Stale 有兩種情境**：

| 類型 | 檢查位置 | 處理方式 |
|------|----------|----------|
| **Stale checkpoint** | `expires_at` < now 且 status=awaiting_human | 需要重新從 S3 開始跑，checkpoint 已無效 |
| **Stale artifacts** | B resume 時找不到 eligibility_report / cleaned_csv | 檔案被刪或路徑錯誤，檢查 `resume_context.artifacts` |

**常用 debug 指令**：
```bash
# 1. 檢查 checkpoint 內容
cat outbox/<case_ref>/checkpoint_A_*.json | python -m json.tool

# 2. 檢查 artifacts 是否存在
ls outbox/<case_ref>/eligibility_report_*.json
ls outbox/<case_ref>/cleaned_*.csv

# 3. 檢查通知事件與 downstream ack 狀態
python scripts/inspect_workflow_events.py --case-ref <case_ref> --format json
python scripts/inspect_workflow_events.py --case-ref <case_ref> --format text
python scripts/run_feedback_ingest.py --case-ref <case_ref> --dry-run --format json
python scripts/run_agent_audit_quickview.py --case-ref <case_ref> --view investigation --format json
# 原始檔案（進階）
ls outbox/notifications/<case_ref>/
ls outbox/feedback/<case_ref>/acks/
tail outbox/notification_events.jsonl
```

### 3.4 Debug Checklist

遇到問題時依序檢查：

- [ ] **Orchestrator 輸出**：`ok`, `final_status`, `message` 欄位
- [ ] **Checkpoint 檔案**：存在？status？expires_at？case_ref/task_type 對嗎？
- [ ] **Human decision**：有沒有跑過 `run_hitl_checkpoint_cli --apply-decision`？
- [ ] **Resume 參數**：`--mode run`？checkpoint path 正確？
- [ ] **Artifacts**：B resume 時需要的檔案都存在？
- [ ] **Notification**：開啟了嗎？事件有寫出去嗎？pending ack 可在 investigation view 的 `missing_downstream_ack` gap 看到

---

## 4. How to Run Tests Locally

### 4.1 最常用測試組合

**完整驗證 W6 HITL/Resume/Notify 功能**：
```bash
# 1. Checkpoint A 整合測試（9 tests）
python -m unittest tests.test_checkpoint_a_integration_v1 -v

# 2. Checkpoint B 整合測試（11 tests）
python -m unittest tests.test_checkpoint_b_integration_v1 -v

# 3. Notification Gateway 測試（23 tests）
python -m unittest tests.test_notification_gateway_v1 -v

# 4. Orchestrator 全路徑測試（43 tests，包含 resume matrix）
python -m unittest tests.test_agent_standard_case_experiment -v
```

### 4.2 依場景選擇測試

| 場景 | 測試指令 |
|------|----------|
| **Resume 邊界測試** | `python -m unittest tests.test_agent_standard_case_experiment -v -k resume` |
| **Notification gateway** | `python -m unittest tests.test_notification_gateway_v1 -v` |
| **Checkpoint A 整合** | `python -m unittest tests.test_checkpoint_a_integration_v1 -v` |
| **Checkpoint B 整合** | `python -m unittest tests.test_checkpoint_b_integration_v1 -v` |
| **Human decision CLI** | `python -m unittest tests.test_hitl_checkpoints_v1 -v` |
| **Delivery approval CLI** | `python -m unittest tests.test_delivery_approval_cli_v1 -v` |

### 4.3 快速驗證關鍵路徑

```bash
# 一次跑完所有 W6 相關測試（約 86 tests）
python -m unittest \
  tests.test_checkpoint_a_integration_v1 \
  tests.test_checkpoint_b_integration_v1 \
  tests.test_notification_gateway_v1 \
  tests.test_agent_standard_case_experiment \
  -v 2>&1 | tail -20
```

### 4.4 測試分類速查

**Resume 相關測試（10個）** — 在 `test_agent_standard_case_experiment` 中：
- `test_approved_checkpoint_a_resume_runs_s7_path`
- `test_approved_checkpoint_b_resume_runs_s13_delivery`
- `test_resume_checkpoint_case_ref_mismatch_blocked`
- `test_resume_checkpoint_task_type_mismatch_blocked`
- `test_resume_checkpoint_awaiting_human_blocked`
- `test_resume_checkpoint_preview_mode_blocked`
- `test_resume_checkpoint_duplicate_delivery_blocked`
- `test_resume_checkpoint_b_stale_artifacts_blocked`
- `test_resume_checkpoint_rejected_status_blocked`
- `test_resume_checkpoint_wrong_human_action_blocked`

**Notification 關鍵測試**：
- `test_enable_notifications_produces_notification_files` — 開啟後產生檔案
- `test_disabled_returns_skipped` — 關閉時無副作用
- `test_dry_run_returns_no_write` — dry-run 不寫檔
- `test_preview_mode_does_not_emit_notifications` — preview 不發通知
- `test_concurrent_appends_produce_valid_jsonl` — 並發寫入正確性

---

## 5. 快速參考卡

### CLI 命令速查

```bash
# Preview（不寫檔，看會發生什麼）
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode preview

# Run（正式執行，會寫 checkpoint）
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode run \
  --outbox-root ./outbox

# Run + auto approve（跳過 checkpoint A）
python scripts/run_agent_standard_case_experiment.py \
  ... --mode run --auto-approve-intake

# Run + 啟用通知
python scripts/run_agent_standard_case_experiment.py \
  ... --mode run --enable-notifications

# Resume from checkpoint A
python scripts/run_agent_standard_case_experiment.py \
  ... --mode run --resume-checkpoint outbox/demo_phase/checkpoint_A_xxx.json

# Resume from checkpoint B
python scripts/run_agent_standard_case_experiment.py \
  ... --mode run --resume-checkpoint outbox/demo_phase/checkpoint_B_xxx.json

# Human decision CLI（決定 checkpoint A）
python scripts/run_hitl_checkpoint_cli.py \
  --checkpoint outbox/demo_phase/checkpoint_A_xxx.json \
  --apply-decision approve

# Human decision CLI（決定 checkpoint B）
python scripts/run_hitl_checkpoint_cli.py \
  --checkpoint outbox/demo_phase/checkpoint_B_xxx.json \
  --apply-decision approve_delivery

# Delivery approval CLI（另一個 B 的決策入口）
python delivery/delivery_approval_cli_v1.py approve \
  --checkpoint outbox/demo_phase/checkpoint_B_xxx.json

# Workflow event read model（notify + checkpoint + ack merge，唯讀）
python scripts/inspect_workflow_events.py --case-ref demo_phase --format json
python scripts/inspect_workflow_events.py --case-ref demo_phase --event-type run.completed --format text
python scripts/inspect_workflow_events.py --case-ref demo_phase --since 2026-06-01T00:00:00Z --format json

# Pending downstream ack scan（dry-run，不寫 ack）
python scripts/run_feedback_ingest.py --case-ref demo_phase --dry-run --format json
```

### Checkpoint JSON 結構速查

**Checkpoint A 關鍵欄位**：
```json
{
  "schema_version": "hitl_checkpoint_v1",
  "checkpoint_type": "A",
  "case_ref": "demo_phase",
  "task_type": "tabular.cleaning.mvp",
  "status": "approved",
  "expires_at": "2026-06-20T10:00:00Z",
  "resume_context": {
    "planned_tools": [...],
    "resume_from": "selector"
  }
}
```

**Checkpoint B 關鍵欄位**：
```json
{
  "schema_version": "hitl_checkpoint_v1",
  "checkpoint_type": "B",
  "case_ref": "demo_phase",
  "status": "approved",
  "resume_context": {
    "artifacts": {
      "eligibility_report": "...",
      "cleaned_csv": "..."
    },
    "resume_from": "delivery"
  }
}
```

---

## 6. 常見新手問題 FAQ

**Q: Preview 和 Run 到底差在哪？**
A: Preview 計算「會發生什麼」但不寫任何檔案到 outbox；Run 會真的寫 checkpoint、發通知、產 bundle。Resume 只能用 Run mode。

**Q: 為什麼我的 resume 被 blocked？**
A: 最常見原因：(1) checkpoint 還在 awaiting_human 沒有人類決定 (2) case/task 對不上 (3) 用 preview mode resume。先看 `final_status` 和 `resume.message`。

**Q: Notification 開了但沒看到檔案？**
A: 檢查三點：(1) 真的用 `--enable-notifications` 或 env (2) 是 run mode 不是 preview (3) 檢查 `outbox/notifications/<case_ref>/` 目錄存在且有權限。

**Q: Checkpoint B 可以 resume 幾次？**
A: 只能一次。成功 delivery 後會寫 marker 檔案，第二次 resume 會被擋（`duplicate_delivery`）。刪除 marker 可重設（但要想清楚為什麼要重送）。

**Q: 過期的 checkpoint 還能 resume 嗎？**
A: 如果已經 approved，v1 **不會**再檢查 expires_at（設計決定）。但如果還在 awaiting_human 就過期，會被標為 stale 不能 resume。

---

## 7. 延伸閱讀

| 文件 | 位置 | 內容 |
|------|------|------|
| Test Matrix | `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` | 63+ 個測試情境對照表 |
| Closure Report | `04_Workflows/reports/W6-standard-case-v2-closure-report.md` | W6 技術結案報告，含詳細設計決定 |
| HITL Design | `docs/hitl-checkpoints-v1.md` | Checkpoint 系統設計文件 |
| Orchestrator Guide | `docs/agent-run-standard-case-orchestrator-v1.md` | Orchestrator 完整文件（§9 Resume）|
