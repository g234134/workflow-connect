# Agent Standard Line v1 — Summary

> **收口票**: W6-T4/5/6-REVIEW · agent-standard-line-integration-review-and-handoff  
> **整合範圍**: W6-T3（設計）+ W6-T4（orchestrator CLI）+ W6-T5（Checkpoint A 整合層）+ W6-T6（Checkpoint B 整合層）  
> **日期**: 2026-06-10  
> **狀態**: v1 實驗線可 preview / partial-run；S8–S15 主鏈執行仍 deferred

---

## 1. Purpose（這條線的目的）

**Agent Standard Line v1** 是一條限定於 Tabular MVP 案型的 **Agent 主導 + 兩個 HITL checkpoint** 實驗線：

- **設計母本**（W6-T3）：定義 S1–S15 完整流程、驅動者分布、Checkpoint A/B 觸發與 resume 語意  
- **Orchestrator CLI**（W6-T4）：單一入口串接 decision → route → tool path preview → checkpoint 預覽  
- **Checkpoint A 整合層**（W6-T5）：W5-T1 decision → W5-T2B outbox state → resume_plan  
- **Checkpoint B 整合層**（W6-T6）：output_guard → W5-T2B outbox state → delivery_plan  

**核心約束**：不改 production 主鏈預設行為；不碰 Local UI、Gov routing glue、executor 主路徑；僅 allowlist 案型可跑。

---

## 2. Supported Cases（支援案型）

| case_ref | case_dir | Checkpoint A（cleaning.mvp） | Checkpoint B（mock S11） |
|----------|----------|------------------------------|---------------------------|
| `demo_phase` | `cases/demo_phase` | `needs_review` / medium → 觸發 | mock `status=ok`；orchestrator 因 `forced_cleaning=true` 標 `would_trigger=true`（見 §4 備註） |
| `sampleco/2026-0001` | `cases/sampleco/2026-0001` | `needs_review` → 觸發 | mock `status=warning` → `would_trigger=true` |
| `additional_demo` | `cases/additional_demo` | `needs_review`（`unknown_fixture_profile`）→ 觸發 | mock `status=ok`；**實驗線 only** |
| `sandbox_client` | `cases/sandbox_client` | `needs_review`（`unknown_fixture_profile`）→ 觸發 | mock `status=ok`；**實驗線 only** |

**錨點案型**（`demo_phase` / `sampleco`）為 production-adjacent 穩定錨點；**擴展案型**（`additional_demo` / `sandbox_client`）標記為實驗線範圍，不進 production contract。

### 2.1 Run Path Coverage（W7-T2 / W8-T1）

| case_ref | run 模式 | stop_at | tools 執行 | experimental |
|----------|----------|---------|------------|--------------|
| `demo_phase` | ✅ | `bundle` | gate → clean → bundle | no |
| `sampleco/2026-0001` | ✅ | `checkpoint_b` | gate → clean | no |
| `additional_demo` | ✅ | `checkpoint_b` | gate → clean + outbox（force） | **controlled_experimental** |
| `sandbox_client` | ✅ | `cleaning_preview` | gate → clean（live guard） | **controlled_experimental** |

非 allowlist 或非 tabular task_type → `final_status=blocked`。

---

## 3. S1–S15 Implementation Matrix

| Step | 名稱 | v1 狀態 | 實作 / 備註 |
|------|------|---------|-------------|
| S1 | Intake Upload | **human-only** | `scripts/new_cleaning_case.py`（既有；實驗線不執行） |
| S2 | Index Refresh | **stub** | `scripts/build_cases_index.py`（既有；orchestrator 不呼叫） |
| S3 | Decision Evaluate | **live** | `evaluate_intake_decision`；W6-T4 orchestrator + W6-T5 整合層 |
| S4 | Checkpoint A | **live（整合層）** | W6-T5 `hitl/checkpoint_a_integration_v1.py`；W6-T4 inline preview/write |
| S5 | Route Planning | **live** | `plan_tabular_route`（W4-T1 glue） |
| S6 | Tool Path Preview | **live（dry-run）** | `run_tabular_intake_tool_path`（W4-T3-A；無 subprocess） |
| S7 | Gate Validation | **stub** | 僅在 tool path preview 的 planned_command 中出現；orchestrator 不執行 |
| S8 | Cleaning Execution | **stub** | 僅 preview planned_command；不執行 |
| S9 | Outbox Write | **stub** | executor 路徑未接；checkpoint 檔案寫入除外（A only, run mode） |
| S10 | Bundle Build | **stub** | 僅 preview planned_command |
| S11 | Output Guard | **mock** | W6-T4 profile mock；非 bundle 讀取 |
| S12 | Checkpoint B | **planned / 整合層** | W6-T6 整合層可獨立使用；W6-T4 僅 `planned` + `would_trigger` |
| S13 | Delivery Approval | **stub** | 無 CLI；delivery_plan 僅 dict |
| S14 | Ledger Update | **stub** | consumer 未接 |
| S15 | Client Notify | **stub** | `notify_client` 恆 `false` |

**圖例**：live = 可呼叫且 unittest 覆蓋；mock = 固定 profile；stub/planned = 設計或 preview 佔位，無實際 side effect。

---

## 4. HITL Checkpoints（現有 HITL 點）

### Checkpoint A — Intake Confirmation（S4）

| 項目 | 內容 |
|------|------|
| **模組** | `hitl/checkpoint_a_integration_v1.py` |
| **觸發** | `decision=needs_review` 或 `risk_level=medium/high` |
| **Human 動作** | `approve` / `revise_plan` / `reject` |
| **持久化** | `outbox/<case_ref>/checkpoint_A-intake-confirmation_*.json` |
| **Orchestrator** | preview → `would_pause`；run → write（除非 `--auto-approve-intake`） |

### Checkpoint B — Delivery Confirmation（S12）

| 項目 | 內容 |
|------|------|
| **模組** | `hitl/checkpoint_b_integration_v1.py` |
| **觸發（整合層）** | `output_guard.status=warning/blocked`；`ok`+`auto_approve` 跳過 |
| **Human 動作** | `approve_delivery` / `request_changes` / `hold` |
| **持久化** | `outbox/<case_ref>/checkpoint_B-delivery-confirmation_*.json` |
| **Orchestrator** | v1 僅 `planned` preview；**未**呼叫 W6-T6 模組 |

### 已知 v1 差異（deferred，非 blocker）

1. **Orchestrator 未接 W6-T5/W6-T6 整合模組**：T4 使用 inline checkpoint 邏輯 + `checkpoints_v1.write_checkpoint`；對稱接線留待後續票。  
2. **Checkpoint B 觸發規則不一致**：T4 orchestrator 額外以 `forced_cleaning` / `removal_ratio>0.5` 標 `would_trigger`；T6 整合層僅 `warning/blocked`。demo_phase mock 因此標 `would_trigger=true`，與 W6-T3 設計文「demo 不觸發 B」文字略有出入。  
3. **Checkpoint B 檔案寫入**：僅 W6-T6 整合層 + unittest；orchestrator 不寫 B 檔。

---

## 5. Runbook — 從 0 跑一次實驗線

### 5.1 前置（fixtures 已存在時可略）

```bash
# 確認 fixture 存在
# cases/demo_phase/intake.json, raw/Phase.csv
# cases/sampleco/2026-0001/intake.json, raw/sampleco_milestone_export.csv
# cases/additional_demo/intake.json, raw/Phase_extended.csv  (W7-T1 實驗線)
# cases/sandbox_client/intake.json, raw/sandbox_milestone_export.csv  (W7-T1 實驗線)
```

### 5.2 Preview（推薦起點 — 無 side effect）

```bash
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode preview \
  --format json
```

### 5.3 Partial run — auto-approve intake + resume plan

```bash
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode run \
  --auto-approve-intake \
  --format json
```

### 5.4 Partial run — 寫入 Checkpoint A（needs_review 停等）

```bash
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode run \
  --format json
# → outbox/demo_phase/checkpoint_A-intake-confirmation_*.json
```

### 5.5 Checkpoint A 整合層（獨立呼叫）

```bash
python -m unittest tests.test_checkpoint_a_integration_v1 -v
# 或程式內：
# from hitl.checkpoint_a_integration_v1 import evaluate_and_maybe_checkpoint_a
```

### 5.6 Checkpoint B 整合層（獨立呼叫）

```bash
python -m unittest tests.test_checkpoint_b_integration_v1 -v
# 消費端見 docs/checkpoint-b-integration-v1.md §6
```

### 5.7 驗收 unittest 三套件

```bash
python -m unittest tests.test_agent_standard_case_experiment -v
python -m unittest tests.test_checkpoint_a_integration_v1 -v
python -m unittest tests.test_checkpoint_b_integration_v1 -v
```

---

## 6. Example — demo_phase preview JSON

以下為 2026-06-10 Reviewer 乾跑 `--mode preview --format json` 的實際輸出（`planned_command` 內 python 路徑因本機而異，語意不變）：

```json
{
  "ok": true,
  "experiment_id": "7c73be10-9fc4-4cb0-8cef-058a3259e6ce",
  "case_ref": "demo_phase",
  "case_dir": "cases/demo_phase",
  "task_type": "tabular.cleaning.mvp",
  "mode": "preview",
  "steps_run": [
    "S3_decision_evaluate",
    "S5_route_planning",
    "S6_tool_path_preview",
    "S4_checkpoint_a",
    "S11_output_guard_mock",
    "S12_checkpoint_b_planned"
  ],
  "decision": {
    "ok": true,
    "decision": "needs_review",
    "risk_level": "medium",
    "suggested_route": {
      "selector_task_type": "e2e",
      "planned_tools": [
        "validate.eligibility",
        "clean.phase_demo",
        "export.delivery_bundle"
      ]
    }
  },
  "checkpoint_a_status": {
    "checkpoint_id": "A-intake-confirmation",
    "would_trigger": true,
    "status": "would_pause",
    "message": "needs human review at Checkpoint A (preview; no state written)"
  },
  "planned_route": {
    "ok": true,
    "selector_task_type": "e2e",
    "planned_tools": ["validate.eligibility", "clean.phase_demo", "export.delivery_bundle"]
  },
  "tool_path_preview": {
    "ok": true,
    "mode": "dry_run_preview",
    "selector_view": { "ok": true, "selector_rule_id": "phase_demo.clean.force" }
  },
  "output_guard": {
    "status": "ok",
    "removal_ratio": 0.286,
    "forced_cleaning": true,
    "source": "mock_profile_demo_phase",
    "note": "S11 mock/placeholder — not read from bundle build in v1 experiment line"
  },
  "checkpoint_b_status": {
    "checkpoint_id": "B-delivery-confirmation",
    "status": "planned",
    "would_trigger": true
  },
  "final_status": "waiting_for_human",
  "message": "experiment preview complete; final_status=waiting_for_human"
}
```

---

## 7. Document Index

| 文件 | 票號 | 角色 |
|------|------|------|
| `docs/agent-run-standard-case-experiment-v1.md` | W6-T3 | 15 步設計母本 |
| `docs/agent-run-standard-case-orchestrator-v1.md` | W6-T4 | Orchestrator CLI 規格 |
| `docs/checkpoint-a-integration-v1.md` | W6-T5 | Checkpoint A 整合層 |
| `docs/checkpoint-b-integration-v1.md` | W6-T6 | Checkpoint B 整合層 |
| **本檔** | REVIEW | 收口總結 |

---

## 8. Verification Record（Reviewer）

| 命令 | 結果 | 日期 |
|------|------|------|
| `python -m unittest tests.test_agent_standard_case_experiment -v` | 8/8 OK | 2026-06-10 |
| `python -m unittest tests.test_checkpoint_a_integration_v1 -v` | 6/6 OK | 2026-06-10 |
| `python -m unittest tests.test_checkpoint_b_integration_v1 -v` | 10/10 OK | 2026-06-10 |
| demo_phase preview CLI 乾跑 | exit 0, JSON 見 §6 | 2026-06-10 |

---

*Agent-Standard-Line-v1-Summary · W6-T4/5/6-REVIEW · 2026-06-10*
