# Agent-Run Experiment Eval & Replay Guide v1

> **版本**: v1.0 — 驗收、Replay 與失敗分析指南  
> **票號**: W6-T7 · experiment-eval-and-replay-guide-v1  
> **適用**: W6-T3/T4/T5/T6 Agent-run 標準案實驗線  
> **日期**: 2026-06-10  
> **上游依據**: 
> - `docs/agent-run-standard-case-experiment-v1.md` (W6-T3)
> - `docs/agent-run-standard-case-orchestrator-v1.md` (W6-T4)
> - `docs/checkpoint-a-integration-v1.md` (W6-T5)
> - `docs/checkpoint-b-integration-v1.md` (W6-T6)
> - `docs/multi-agent-replay-guide-v1.md`
> - `docs/ninety-five-percent-automation-blueprint-v1.md`
> - `docs/tabular-mvp-release-checklist.md`

---

## §1 目的

本指南為 **Agent-run 標準案實驗線**（W6-T3 至 W6-T6）提供：

1. **成功定義**：何時可標記一條實驗 run 為「成功」
2. **最小驗證命令**：驗收時必跑的 CLI / unittest 清單
3. **Replay 方法論**：如何從任意檢查點重新執行或除錯
4. **失敗分析框架**：常見失敗類型的排查順序與診斷命令
5. **升級條件**：何時可視為「可進入下一輪自動化」

---

## §2 Agent-Run 標準案的成功定義

### 2.1 實驗線架構回顧

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    AGENT-RUN STANDARD CASE EXPERIMENT — 15 STEPS                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [S1]      [S2]        [S3]         [S4]        [S5]        [S6]        [S7]        │
│ INTAKE → INDEX → DECISION_EVAL → CP-A → ROUTE_PLAN → TOOL_SELECT → GATE_VALID      │
│  Upload  Refresh   (W5-T1)       (HITL)   (W4-T1)   (W3-TL-T2)  (auto)           │
│                                                                                      │
│                                     ↓                                                │
│  [S8]        [S9]        [S10]       [S11]       [S12]       [S13]       [S14]    │
│ CLEAN → OUTBOX → BUNDLE_BUILD → OUTPUT_GUARD → CP-B → DELIVERY → LEDGER → NOTIFY  │
│ (auto)  (W3-TL-T3)  (auto)      (auto)       (HITL)   (HITL)    (auto)   (auto)    │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 成功定義（三級）

#### Level 1: Preview Success（預演成功）

| 檢查項 | 標準 | 驗證命令 |
|--------|------|----------|
| Decision 輸出 | `ok: true`，`decision` 欄位存在 | orchestrator `--mode preview` |
| Route Plan | `planned_tools[]` 非空 | `--mode preview` JSON |
| Checkpoint A 觸發判斷 | `checkpoint_a_status` 正確 | 見 §3.1 |
| 無 crash / exception | exit code 0 | CLI exit code |

**適用情境**：W6-T4 orchestrator preview mode，驗證「決策 → 路由規劃」鏈路完整。

#### Level 2: Auto-Chain Success（自動鏈成功）

| 檢查項 | 標準 | 驗證方法 |
|--------|------|----------|
| S1-S15 無阻塞 | 無 `blocked` / `error` 狀態 | 檢查 `final_status` |
| Checkpoint 正確觸發 | CP-A/CP-B 依條件觸發/跳過 | 檢查 `checkpoint_*_status` |
| Output artifacts | `cleaned/*.csv`, `reports/*.json` 存在 | `ls` 檢查 |
| Outbox entries | 每步有對應 `outbox/*.json` | `inspect_tabular_outbox.py` |
| Bundle 生成 | `delivery_signoff.md` 存在 | 檔案檢查 |

**適用情境**：`--auto-approve-intake` 模式，驗證完整 auto-chain 無人干涉。

#### Level 3: Full HITL Success（完整 HITL 成功）

| 檢查項 | 標準 | 驗證方法 |
|--------|------|----------|
| CP-A 正確暫停 | `status: awaiting_human` | checkpoint JSON |
| Human decision 應用 | `resume_context` 正確生成 | checkpoint JSON |
| Resume plan 可執行 | `resume_from` 指向有效步驟 | §4 replay 命令 |
| CP-B 品質把關 | `output_guard.status` 觸發邏輯正確 | 檢查 guard 條件 |
| Final delivery | `cases/index.json` status 更新 | index 檢查 |

**適用情境**：完整 HITL 流程，含 checkpoint 暫停、人工決策、resume。

### 2.3 Success Criteria Matrix

| Fixture | Level 1 (Preview) | Level 2 (Auto) | Level 3 (Full HITL) |
|---------|-------------------|----------------|---------------------|
| `demo_phase` | ✅ `--mode preview` | ✅ `--auto-approve-intake` | ⚠️ CP-A 預期觸發 |
| `sampleco` | ✅ `--mode preview` | ✅ `--auto-approve-intake` | ⚠️ CP-B 預期觸發 |
| `additional_demo` | ✅ `--mode preview` | ✅ **W8-T1** run → CP-B（experimental） | ⚠️ CP-A 預期觸發 |
| `sandbox_client` | ✅ `--mode preview` | ✅ **W8-T1** run → cleaning_preview（experimental） | ⚠️ CP-A 預期觸發 |

### 2.4 擴大 Run 覆蓋（W7-T2 · 錨點案型）

| 檢查項 | `demo_phase` | `sampleco/2026-0001` |
|--------|--------------|----------------------|
| run_path_profile.stop_at | `bundle` | `checkpoint_b` |
| 執行工具 | eligibility → cleaning → bundle | eligibility → cleaning |
| delivery 前停止 | 否 | 是（`stop_before_delivery`） |
| outbox 記錄 | `run_execution.outbox_entries` 非空 | 同左 |
| 預期 final_status | `waiting_for_human` 或 `run_complete` | `stopped_at_checkpoint_b` |
| Checkpoint B | 依 live output_guard 觸發 | `stopped_before_delivery` 或 `written` |

### 2.5 實驗 Fixture Run 覆蓋（W8-T1 · experimental only）

| 檢查項 | `additional_demo` | `sandbox_client` |
|--------|-------------------|------------------|
| run_path_profile.stop_at | `checkpoint_b` | `cleaning_preview` |
| 執行工具 | gate → cleaning（`force_cleaning`） | gate only |
| delivery 前停止 | 是 | 是（cleaning 未執行） |
| outbox 記錄 | cleaning 步 outbox 非空 | gate outbox 可空 |
| 預期 final_status | `stopped_at_checkpoint_b` | `stopped_at_cleaning_preview` |
| Checkpoint B | live output_guard + safeguard | `stopped_at_cleaning_preview`（不評估 B） |
| Safeguard | CP-A + output_guard + 止步 delivery | CP-A + mock S11 + 止步 S8 |

**成功條件（W7-T2 / W8-T1）**：
- `ok: true`
- `path_kind: "run"`
- `run_path_profile` 與上表一致
- `run_execution.ok: true` 且 `tools_executed` 符合 profile
- 非 allowlist case：`final_status: blocked`（run 模式亦拒絕）

---

## §3 最小驗證命令清單

### 3.1 核心 Orchestrator 驗證

```bash
# === Level 1: Preview Success ===
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode preview \
  --format json

# 預期檢查:
# - "ok": true
# - "decision.decision": "needs_review" (demo_phase) 或 "auto_accept" (sampleco)
# - "checkpoint_a_status.would_trigger": true (demo_phase) / false (sampleco)
# - "planned_route.planned_tools": 非空 array
# - "final_status": "preview_ready"
```

```bash
# === W7-T1 Extended fixtures (experiment line only) ===
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/additional_demo \
  --mode preview \
  --format json

python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/sandbox_client \
  --mode preview \
  --format json

# 預期: ok=true, decision=needs_review, final_status=waiting_for_human
```

```bash
# === W7-T1 Extended regression (optional flag) ===
python scripts/run_agent_standard_case_regression.py --format json
python scripts/run_agent_standard_case_regression.py --include-extended-fixtures --format json
# 預設 2 cases (demo_phase + sampleco); --include-extended-fixtures 追加 2 cases
```

```bash
# === Level 2: Auto-Chain (skip HITL) — demo_phase full run path (W7-T2) ===
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode run \
  --auto-approve-intake \
  --format json

# 預期檢查:
# - "run_path_profile.stop_at": "bundle"
# - "run_execution.tools_executed" 含 export.delivery_bundle
# - "final_status": "waiting_for_human" 或 "run_complete"
```

```bash
# === W7-T2: sampleco controlled run (cleaning only, stop before delivery) ===
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/sampleco/2026-0001 \
  --mode run \
  --auto-approve-intake \
  --format json

# 預期檢查:
# - "run_path_profile.stop_at": "checkpoint_b"
# - "run_execution.tools_executed" 不含 export.delivery_bundle
# - "final_status": "stopped_at_checkpoint_b"
```

```bash
# === W7-T2: Regression — all allowlist fixtures in run mode ===
python scripts/run_agent_standard_case_regression.py \
  --run-mode run-all-allowed \
  --auto-approve-intake \
  --format json

# 預期: ok=true, passed=2/2; sampleco final_status=stopped_at_checkpoint_b
```

```bash
# === W8-T1: additional_demo controlled run (experimental) ===
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/additional_demo \
  --mode run \
  --auto-approve-intake \
  --format json

# 預期檢查:
# - "run_path_profile.stop_at": "checkpoint_b"
# - "run_path_profile.experimental": true
# - "run_execution.tools_executed" 含 clean.phase_demo、不含 export.delivery_bundle
# - "final_status": "stopped_at_checkpoint_b"
```

```bash
# === W8-T1: sandbox_client conservative run (experimental) ===
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/sandbox_client \
  --mode run \
  --auto-approve-intake \
  --format json

# 預期檢查:
# - "run_path_profile.stop_at": "cleaning_preview"
# - "run_execution.tools_executed": ["validate.eligibility"] only
# - "final_status": "stopped_at_cleaning_preview"
# - "checkpoint_b_status.status": "stopped_at_cleaning_preview"
```

```bash
# === W8-T1: Regression — all fixtures including experimental run ===
python scripts/run_agent_standard_case_regression.py \
  --run-mode run-all-allowed \
  --include-extended-fixtures \
  --auto-approve-intake \
  --format json

# 預期: ok=true, passed=4/4
# additional_demo / sandbox_client: experimental_run=true in case summaries
```

### 3.2 整合層單元測試

```bash
# === Checkpoint A Integration ===
python -m unittest tests.test_checkpoint_a_integration_v1 -v
# 預期: 測試 approve/revise/reject 三種決策路徑

# === Checkpoint B Integration ===
python -m unittest tests.test_checkpoint_b_integration_v1 -v
# 預期: 測試 approve_delivery/request_changes/hold 三種決策

# === Delivery Approval One-Click CLI (W8-T3) ===
python -m unittest tests.test_delivery_approval_cli_v1 -v
# 預期: preview/confirm、三種 action、notify 跳過/呼叫

# === Orchestrator ===
python -m unittest tests.test_agent_standard_case_experiment -v
# 預期: preview/run 模式、auto-approve 邏輯
```

### 3.3 上游依賴驗證（Regression Guard）

```bash
# === W5-T1 Decision Rules ===
python routing/intake_decision_rules_v1.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --json
# 預期: "decision": "needs_review", "risk_level": "medium"

# === W4-T1 Glue ===
python -m unittest tests.test_routing_tabular_glue -v
# 預期: 9/9 OK

# === W5-T1B Agent Entry ===
python scripts/run_agent_intake_decision_demo.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --format json
# 預期: decision + checkpoint 預覽
```

### 3.4 Outbox 與產物驗證

```bash
# === 檢查 outbox 內容 ===
python tools/inspect_tabular_outbox.py --case-ref demo_phase --list

# === 檢查產物完整性 ===
ls -la cases/demo_phase/cleaned/
ls -la cases/demo_phase/reports/
cat cases/demo_phase/delivery_signoff.md
```

### 3.5 完整回歸（Release Grade）

```bash
# === Tabular MVP Release Checklist ===
# 參見 docs/tabular-mvp-release-checklist.md §2

python scripts/run_mvp_mainline_regression.py -v
# 預期: 6/6 OK
```

---

## §4 如何 Replay 一次 Run

### 4.1 Replay 方法論總覽

| 階段 | Replay 起點 | 命令模式 | 狀態來源 |
|------|-------------|----------|----------|
| **Decision** | S3 輸出 | `--mode preview` + 手動改 decision | orchestrator output |
| **Checkpoint A** | S4 暫停後 | `--resume-from-checkpoint` (未來) | `outbox/checkpoint_A-*.json` |
| **Route/Tool Path** | S5-S6 | `run_tabular_intake_tool_path.py` | checkpoint `resume_context` |
| **Checkpoint B** | S12 暫停後 | W5-T2B CLI + integration resume | `outbox/checkpoint_B-*.json` |
| **Delivery Approval** | S13 | manual `index.json` edit (v1) | checkpoint B resume plan |

### 4.2 Decision 階段 Replay

**情境**：驗證不同 decision 結果的分支行為。

```bash
# Step 1: 取得 baseline decision
python scripts/run_agent_intake_decision_demo.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --format json > /tmp/decision_baseline.json

# Step 2: 手動修改 decision（模擬 auto_accept 場景）
# 編輯 /tmp/decision_modified.json:
#   "decision": "auto_accept",
#   "risk_level": "low"

# Step 3: 用 orchestrator 測試修改後的路徑
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode preview \
  --format json 2>&1 | jq '.checkpoint_a_status'
# 預期: auto_accept + low risk → "would_trigger": false
```

### 4.3 Checkpoint A Replay

**情境**：人工決策後 resume 流程。

```bash
# Step 1: 確認 checkpoint 存在
ls outbox/demo_phase/checkpoint_A-intake-confirmation_*.json

# Step 2: 讀取 checkpoint 內容
cat outbox/demo_phase/checkpoint_A-intake-confirmation_*.json | jq '.'

# Step 3: 模擬 human decision（使用 W5-T2B CLI）
python scripts/run_hitl_checkpoint_cli.py \
  --checkpoint outbox/demo_phase/checkpoint_A-intake-confirmation_*.json \
  --action approve \
  --notes "Replay test approval"

# Step 4: 取得 resume_context
cat outbox/demo_phase/checkpoint_A-intake-confirmation_*.json | jq '.resume_context'

# Step 5: 使用 resume_context 繼續（v1: 手動提取 planned_tools）
# 從 resume_context 提取 selector_task_type 與 planned_tools
# 手動呼叫 downstream steps
```

**v1 限制**：W6-T4 orchestrator 尚不支援 `--resume-from-checkpoint`（見 W6-T12 gap）。

### 4.4 Route / Tool Path Replay

**情境**：驗證 S5-S6 路由規劃與工具選擇。

```bash
# Step 1: 獨立執行 route planning
python scripts/run_tabular_intake_tool_path.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --json

# Step 2: 檢查 glue_plan + selector_view + executor_plan
# 輸出包含:
# - glue_plan.selector_task_type
# - glue_plan.planned_tools[]
# - selector_view.candidate_tools[]
# - executor_plan.dry_run: true (W4-T3-A 不寫 outbox)

# Step 3: 若要實際執行（非 replay 用途），使用 W3-TL executor
python tools/tabular_tool_executor.py \
  --case-dir cases/demo_phase \
  --tool clean.phase_demo \
  --force  # 若 needed
```

### 4.5 Checkpoint B Replay

**情境**：delivery 品質確認後的放行或修改。

```bash
# Step 1: 確認 checkpoint B 觸發條件
# 條件: output_guard.status=warning OR removal_ratio>0.5 OR forced_cleaning=true

# Step 2: 檢查 output_guard 輸出
cat cases/demo_phase/reports/report.json | jq '.output_guard'

# Step 3: 計算 removal_ratio
# 從 cleaning_stats.json 或 report.json output_guard

# Step 4a: 一鍵 approval CLI（W8-T3 · 推薦）
# 預覽（不寫入）
python scripts/run_delivery_approval_cli.py \
  --case-dir cases/demo_phase \
  --checkpoint-id B-delivery-confirmation \
  --action approve \
  --notes "Reviewing before confirm"

# 確認寫入決策
python scripts/run_delivery_approval_cli.py \
  --case-dir cases/demo_phase \
  --action approve \
  --notes "Quality approved" \
  --confirm \
  --format json

# Step 4b: 低階 checkpoint CLI（仍可用）
python scripts/run_hitl_checkpoint_cli.py \
  --review \
  --checkpoint-id B-delivery-confirmation

python scripts/run_hitl_checkpoint_cli.py \
  --apply-decision approve_delivery \
  --checkpoint-id B-delivery-confirmation \
  --notes "Quality approved in replay"

# Step 5: 檢查 resume plan
cat outbox/demo_phase/checkpoint_B-delivery-confirmation_*.json | jq '.resume_context'
```

### 4.6 Delivery Approval Replay

**情境**：驗證 delivery 後的 index 更新與通知。

```bash
# Step 1: 確認 delivery_signoff.md 存在
cat cases/demo_phase/delivery_signoff.md

# Step 2: W8-T3 一鍵 approve（含 optional notify experiment）
python scripts/run_delivery_approval_cli.py \
  --case-dir cases/demo_phase \
  --action approve \
  --confirm \
  --with-notify-experiment

# Step 3: 手動更新 index (v1 無自動化)
python -c "
import json
with open('cases/index.json') as f:
    idx = json.load(f)
idx['demo_phase']['status'] = 'delivered'
idx['demo_phase']['delivered_at'] = '2026-06-10T12:00:00Z'
with open('cases/index.json', 'w') as f:
    json.dump(idx, f, indent=2)
"

# Step 3: 驗證更新
python scripts/build_cases_index.py --verify
```

### 4.7 Full Run Replay 腳本（模板）

```bash
#!/bin/bash
# replay_experiment.sh — Full replay template

CASE_REF="demo_phase"
CASE_DIR="cases/${CASE_REF}"
TASK_TYPE="tabular.cleaning.mvp"

echo "=== S1-S3: Intake + Decision ==="
python scripts/run_agent_standard_case_experiment.py \
  --task-type ${TASK_TYPE} \
  --case-dir ${CASE_DIR} \
  --mode run \
  --format json > /tmp/s1_s3_result.json

echo "=== S4: Checkpoint A (if triggered) ==="
if jq -e '.checkpoint_a_status.would_trigger' /tmp/s1_s3_result.json > /dev/null; then
  echo "Checkpoint A would trigger — manual approval needed"
  # 手動執行: scripts/run_hitl_checkpoint_cli.py --action approve
fi

echo "=== S5-S11: Route → Execution → Guard ==="
# 使用 checkpoint resume_context 或從 decision 重跑
# 注意: v1 需手動提取 planned_tools 並逐 step 執行

echo "=== S12: Checkpoint B (if triggered) ==="
# 檢查 output_guard.status

echo "=== S13-S15: Delivery → Ledger → Notify ==="
# 手動或 auto-approve-delivery 模式
```

---

## §5 常見失敗類型與排查順序

### 5.1 失敗分類總覽

| 類型代碼 | 名稱 | 發生階段 | 頻率 |
|----------|------|----------|------|
| **F1** | Decision Mismatch | S3 | 高 |
| **F2** | Checkpoint State Lost | S4, S12 | 中 |
| **F3** | Tool Execution Fail | S6-S8 | 中 |
| **F4** | Guard Trigger Unexpected | S11 | 中 |
| **F5** | Resume Context Invalid | S4, S12 resume | 低 |
| **F6** | Fixture Data Drift | S1, S7 | 低 |

### 5.2 F1: Decision Mismatch（最常見）

**症狀**：
- `demo_phase` 預期 `needs_review` 但得到 `auto_accept`
- `sampleco` 預期 `needs_review` 但得到 `reject`

**診斷順序**：

```bash
# Step 1: 檢查 decision rules 版本
python routing/intake_decision_rules_v1.py --version 2>/dev/null || echo "v1 無 --version"

# Step 2: 直接跑 decision rules（繞過 orchestrator）
python routing/intake_decision_rules_v1.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --json | jq '.decision, .risk_level, .rationale'

# Step 3: 檢查 allowlist
# intake_decision_rules_v1.py 內建 demo_phase / sampleco allowlist
# 若 case_ref 不在 allowlist → 可能 fallback 至 unexpected decision

# Step 4: 檢查 glue 輸出（W4-T1 為 decision 提供輸入）
python -c "
from routing.intake_to_tabular_glue import plan_tabular_route
import json
result = plan_tabular_route('tabular.cleaning.mvp', 'cases/demo_phase')
print(json.dumps(result, indent=2))
"
```

**修復方向**：
- 若 allowlist 問題：檢查 `case_dir` 路徑是否正確
- 若 glue 問題：檢查 `intake.json` 格式是否正確
- 若規則問題：檢查 W5-T1 `evaluate_intake_decision` 邏輯

### 5.3 F2: Checkpoint State Lost

**症狀**：
- Checkpoint A/B 觸發後 crash，狀態未寫入
- `outbox/` 無對應 checkpoint JSON
- Resume 時找不到 `resume_context`

**診斷順序**：

```bash
# Step 1: 檢查 outbox 目錄結構
ls -la outbox/${CASE_REF}/

# Step 2: 檢查 checkpoint 命名模式
ls outbox/${CASE_REF}/checkpoint_*_*.json 2>/dev/null || echo "No checkpoints found"

# Step 3: 檢查 W5-T2B 核心功能
python -c "
from hitl.checkpoints_v1 import list_checkpoints
import json
checkpoints = list_checkpoints('demo_phase')
print(json.dumps(checkpoints, indent=2))
"

# Step 4: 手動重建 checkpoint（若因 crash 遺失）
# 從 orchestrator 輸出提取 agent_output，手動建立 checkpoint JSON
```

**修復方向**：
- 檢查 `outbox/` 目錄權限
- 檢查 orchestrator 是否在 write checkpoint 前 crash
- 使用 W5-T2B `scripts/run_hitl_checkpoint_cli.py --list` 確認狀態

### 5.4 F3: Tool Execution Fail

**症狀**：
- `clean.phase_demo` exit 1
- `requires_force=true` 但未加 `--force`
- `outbox/` 無 tool execution entry

**診斷順序**：

```bash
# Step 1: 檢查 gate status
cat cases/demo_phase/reports/eligibility_result.json | jq '.status, .exit_code, .reason_code'

# Step 2: 確認是否需要 force
# demo_phase: exit_code=2 → needs --force
# sampleco: exit_code=0 → no force needed

# Step 3: 直接執行 cleaning（繞過 orchestrator）
python notebooks/csv_cleaning/clean_phase_demo.py \
  --case-dir cases/demo_phase \
  --skip-eligibility \
  --force 2>&1 | tail -20

# Step 4: 檢查 raw data 完整性
wc -l cases/demo_phase/raw/Phase.csv
head -5 cases/demo_phase/raw/Phase.csv
```

**修復方向**：
- 若 row count 不符預期：重建 fixture data
- 若 schema 變更：更新 cleaning script
- 若 force flag 遺漏：檢查 orchestrator `--auto-approve-intake` 邏輯

### 5.5 F4: Guard Trigger Unexpected

**症狀**：
- `demo_phase` 預期 `output_guard.status=ok` 但得到 `warning`
- `sampleco` 預期 `warning` 但未觸發 Checkpoint B

**診斷順序**：

```bash
# Step 1: 檢查 cleaning 結果
python tools/inspect_tabular_outbox.py --case-ref demo_phase --run-id latest

# Step 2: 計算實際 removal_ratio
python -c "
import json
with open('cases/demo_phase/reports/cleaning_stats.json') as f:
    stats = json.load(f)
input_rows = stats.get('input_rows', 0)
output_rows = stats.get('output_rows', 0)
if input_rows > 0:
    ratio = (input_rows - output_rows) / input_rows
    print(f'Removal ratio: {ratio:.2%}')
    print(f'Trigger warning: {ratio > 0.5}')
"

# Step 3: 檢查 output_guard 邏輯
# 見 checkpoint_b_integration_v1.py::should_create_checkpoint_b
```

**修復方向**：
- 若 ratio 計算錯誤：檢查 `cleaning_stats.json` 欄位
- 若 guard 條件不符：檢查 W6-T6 `should_create_checkpoint_b` 實作

### 5.6 F5: Resume Context Invalid

**症狀**：
- Checkpoint 決策後 `resume_context` 為 null
- `resume_from` 指向不存在的 step
- `planned_tools` 為空或格式錯誤

**診斷順序**：

```bash
# Step 1: 檢查 checkpoint JSON 結構
cat outbox/demo_phase/checkpoint_A-intake-confirmation_*.json | jq 'keys'

# Step 2: 驗證 resume_context 欄位
cat outbox/demo_phase/checkpoint_A-intake-confirmation_*.json | jq '.resume_context' | jq 'keys'

# Step 3: 檢查必要欄位
# - resume_from: "selector" | "gate" | "cleaning" | "bundle" | "delivery"
# - selector_task_type: string
# - planned_tools: string[]
```

**修復方向**：
- 若 W5-T2B `record_human_decision` 未生成 context：檢查 CLI 參數
- 若 integration layer 未正確轉換：檢查 W6-T5/W6-T6 resume plan 函數

### 5.7 F6: Fixture Data Drift

**症狀**：
- `demo_phase` row count 非 7
- `sampleco` eligibility status 非預期

**診斷順序**：

```bash
# Step 1: 驗證 fixture 完整性
python scripts/run_mvp_mainline_regression.py -v 2>&1 | grep -A5 "FAIL"

# Step 2: 檢查 raw data
wc -l cases/demo_phase/raw/Phase.csv      # 預期: 8 (header + 7)
wc -l cases/sampleco/2026-0001/raw/sampleco_milestone_export.csv

# Step 3: 重建 index
python scripts/build_cases_index.py --force

# Step 4: 重跑 gate
python scripts/check_case_eligibility.py \
  --case-dir cases/demo_phase \
  --json | jq '.status, .exit_code'
```

**修復方向**：
- 若 fixture 被修改：從 git restore
- 若 index 過期：重建 `cases/index.json`

### 5.8 排查速查表

| 問題現象 | 先查 | 再查 | 最後 |
|----------|------|------|------|
| Decision 不對 | W5-T1 rules | W4-T1 glue | intake.json |
| Checkpoint 沒存 | outbox 權限 | W5-T2B write | orchestrator log |
| Tool 跑不動 | eligibility exit | force flag | raw data |
| Guard 誤觸發 | cleaning stats | removal_ratio | threshold config |
| Resume 失敗 | checkpoint JSON | resume_context | integration layer |
| Data 不對 | row count | index.json | fixture git status |

---

## §6 何時視為「可升級到下一輪自動化」

### 6.1 升級條件（Gate Criteria）

| 條件 ID | 描述 | 驗證方法 | 達標標準 |
|---------|------|----------|----------|
| **G1** | Stable Preview | 連續 10 次 `--mode preview` | 100% success rate |
| **G2** | Stable Auto-Chain | 連續 10 次 `--auto-approve-intake` | 100% Level 2 success |
| **G3** | HITL Resume Works | Checkpoint A/B 各 5 次 resume | 100% resume success |
| **G4** | Regression Pass | `run_mvp_mainline_regression.py` | 6/6 OK |
| **G5** | Decision Accuracy | Decision 與預期對照 | 100% match (allowlist cases) |
| **G6** | No State Loss | Checkpoint crash 測試 | 0% state loss (simulated) |
| **G7** | Documentation | 本指南 + spec 完整 | Reviewer `accepted` |

### 6.2 升級決策矩陣

```
當前狀態: W6-T3/T4/T5/T6 (實驗線 v1)
                ↓
    ┌───────────────────────────┐
    │ 滿足 G1-G7?                │
    └───────────────────────────┘
           │           │
          YES         NO
           │           │
           ▼           ▼
    ┌──────────┐  ┌──────────────┐
    │ 可升級至  │  │ 修復後重測   │
    │ Wave 6/7  │  │ (見 §5)      │
    │ 實作票   │  │              │
    └──────────┘  └──────────────┘
           │
           ▼
    W6-T5: Checkpoint A 實作
    W6-T8: Checkpoint B 實作
    W6-T9: Delivery Automation
    W6-T10: Notification Gateway
```

### 6.3 下一輪自動化定義

| 升級目標 | 當前 (W6-T3~T6) | 下一輪 (W6-T5/T8/T9/T10) |
|----------|-----------------|--------------------------|
| CP-A 狀態 | `would_pause` / planned | `awaiting_human` + resume API |
| CP-B 狀態 | `planned` / mock | `awaiting_human` + delivery plan |
| S13 Delivery | human-only edit | `scripts/run_delivery_approval_cli.py` (W8-T3) |
| S15 Notify | manual Telegram | `app/notification_gateway.py` auto |
| Resume | 手動提取 context | `--resume-from-checkpoint` CLI |

### 6.4 測量方法

```bash
# === 批次驗證腳本（測量 G1-G3）===
#!/bin/bash
# measure_readiness.sh

CASES=("demo_phase" "sampleco")
ITERATIONS=10
PASS_COUNT=0

for case in "${CASES[@]}"; do
  for i in $(seq 1 $ITERATIONS); do
    result=$(python scripts/run_agent_standard_case_experiment.py \
      --task-type tabular.cleaning.mvp \
      --case-dir cases/$case \
      --mode preview \
      --format json 2>/dev/null | jq -r '.ok')
    
    if [ "$result" = "true" ]; then
      ((PASS_COUNT++))
    fi
  done
done

TOTAL=$((ITERATIONS * ${#CASES[@]}))
echo "Pass rate: $PASS_COUNT / $TOTAL ($((PASS_COUNT * 100 / TOTAL))%)"
# 升級門檻: 100%
```

---

## §7 交叉引用

| 文件 | 用途 |
|------|------|
| `docs/agent-run-standard-case-experiment-v1.md` | W6-T3 完整 15 步設計 |
| `docs/agent-run-standard-case-orchestrator-v1.md` | W6-T4 orchestrator CLI |
| `docs/checkpoint-a-integration-v1.md` | W6-T5 CP-A integration API |
| `docs/checkpoint-b-integration-v1.md` | W6-T6 CP-B integration API |
| `docs/hitl-checkpoints-v1.md` | W5-T2 checkpoint 設計母本 |
| `docs/ninety-five-percent-automation-blueprint-v1.md` | 95% 自動化藍圖（含 gap list）|
| `docs/tabular-mvp-release-checklist.md` | 發版前驗證清單 |
| `docs/multi-agent-replay-guide-v1.md` | Multi-Chat 票 replay 方法論 |

---

*AGENT-RUN-EXPERIMENT-EVAL-GUIDE-v1 · W6-T7 · 2026-06-10*
