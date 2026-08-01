# Skill Map v2 — Tabular MVP · Wave 7 模組映射

> **Ticket**: W7-T4 · update-ninety-five-percent-blueprint-and-skills-wave7-v1  
> **Date**: 2026-06-10  
> **Purpose**: 更新步驟／模組映射與成熟度（done / experimental / planned）

**上游**：`docs/skill-map-v1.md` · W7-T1/T2/T3 交付物

---

## 流程步驟總覽（v2）

```
┌─────────┐   ┌──────────┐   ┌───────┐   ┌─────────┐   ┌──────────────┐   ┌────────┐   ┌─────────────┐   ┌────────────┐   ┌─────────────┐
│ intake  │──▶│ decision │──▶│ glue  │──▶│selector │──▶│ run_path /   │──▶│ outbox │──▶│ checkpoint  │──▶│ notify     │──▶│release/reg │
│         │   │          │   │       │   │         │   │ executor     │   │        │   │ A / B       │   │ (controlled)│   │            │
└─────────┘   └──────────┘   └───────┘   └─────────┘   └──────────────┘   └────────┘   └─────────────┘   └─────────────┘   └────────────┘
                                                              ▲ W7-T2 new                              ▲ W7-T3 new
```

---

## 步驟映射表

### 1. Intake（接案）

| 欄位 | v2 內容 |
|------|---------|
| **Module** | `scripts/new_cleaning_case.py` |
| **Fixtures** | demo_phase · sampleco · **additional_demo** · **sandbox_client** |
| **Maturity** | **done** |
| **Notes** | 無 intake API；Wave 8 G8-7 |

---

### 2. Decision（決策）

| 欄位 | v2 內容 |
|------|---------|
| **Module** | `routing/intake_decision_rules_v1.py` |
| **Maturity** | **done**（demo/sampleco）· **controlled_experimental**（+2 fixture profile · W11-T1） |
| **Allowlist** | `_ALLOWLIST_PROFILES = {demo_phase, sampleco}` |
| **W7 行為** | additional_demo / sandbox_client → `needs_review` + `unknown_fixture_profile` |

---

### 3. Glue（路由膠合）

| 欄位 | v2 內容 |
|------|---------|
| **Module** | `routing/intake_to_tabular_glue.py` |
| **Maturity** | **done** |
| **W7** | 四 fixture 皆可 `plan_tabular_route` |

---

### 4. Selector（工具選擇）

| 欄位 | v2 內容 |
|------|---------|
| **Module** | `tools/tabular_tool_selector.py` · `run_tabular_intake_tool_path.py` |
| **Maturity** | **done**（preview） |

---

### 5. Run Path / Executor（W7-T2 · 新增映射）

| 欄位 | 內容 |
|------|------|
| **Step** | run_path / executor |
| **Module** | `scripts/run_agent_standard_case_experiment.py` → `_execute_run_path_tools` → `tools/tabular_tool_executor.py` |
| **Profiles** | `_RUN_PATH_PROFILES` in orchestrator |
| **Input** | `mode=run` · cleared Checkpoint A · `run_path_profile` for case_ref |
| **Output** | `run_execution` dict · live outbox entries · `output_guard` from `cleaning_stats.json` |
| **Maturity** | **done**（demo_phase · sampleco）· **controlled_experimental**（additional_demo · sandbox_client · W11-T1） |

**Run Path Profile 表**

| case_ref | stop_at | tools_to_run | force | stop_before_delivery | maturity |
|----------|---------|--------------|-------|----------------------|----------|
| `demo_phase` | bundle | gate · clean · bundle | yes | no | stable |
| `sampleco/2026-0001` | checkpoint_b | gate · clean | no | yes | stable |
| `additional_demo` | checkpoint_b | gate · clean | yes | yes | **controlled_experimental** |
| `sandbox_client` | cleaning_preview | gate · clean | no | yes | **controlled_experimental** |

---

### 6. Checkpoint A / B（HITL）

| 欄位 | v2 內容 |
|------|---------|
| **Checkpoint A** | `hitl/checkpoint_a_integration_v1.py` + orchestrator inline · **done**（run write） |
| **Checkpoint B** | `hitl/checkpoint_b_integration_v1.py` · **done**（W7-T2 `_resolve_checkpoint_b_after_run`） |
| **CLI** | `scripts/run_hitl_checkpoint_cli.py` |
| **Maturity** | **done**（integration + run path）· replay resume **planned** |

---

### 7. Outbox（出箱）

| 欄位 | v2 內容 |
|------|---------|
| **Module** | `tools/tabular_outbox_writer.py` · consumer |
| **Maturity** | **done**（run path 寫入）· experiment regression artifacts **done** |
| **W7 paths** | `outbox/agent_experiment_regression/` · `notify_experiment_*.json` |

---

### 8. Controlled Notify（W7-T3 · 新增）

| 欄位 | 內容 |
|------|------|
| **Step** | notify / controlled_delivery |
| **Module** | `delivery/controlled_notify_experiment_v1.py` |
| **CLI** | `scripts/run_controlled_delivery_notify_experiment.py` |
| **Input** | `case_dir` · `dry_run`（default true） |
| **Output** | `client_summary_text` · optional `outbox/.../notify_experiment_*.json` |
| **Maturity** | **experimental** |
| **Allowlist** | demo_phase · sampleco only |
| **Safeguard** | `external_dispatch=false` · internal sensitivity only |

---

### 9. Inspect / Replay

| 欄位 | v2 內容 |
|------|---------|
| **Module** | `tools/inspect_tabular_outbox.py` · `docs/agent-run-experiment-eval-guide-v1.md` |
| **Maturity** | **done**（inspect）· **planned**（`--resume-from-checkpoint`） |

---

### 10. Release / Regression

| 欄位 | v2 內容 |
|------|---------|
| **MVP Mainline** | `scripts/run_mvp_mainline_regression.py` · **done** · 6/6 |
| **Experiment Regression** | `scripts/run_agent_standard_case_regression.py` · **done** |
| **W7 flags** | `--run-mode run-all-allowed` · `--include-extended-fixtures` |
| **Maturity** | **done**（2 fixture default）· **controlled_experimental**（4 fixture run-all-allowed · W11-T1） |

**Regression 覆蓋矩陣**

| Case | Default preview | `--include-extended-fixtures` | `--run-mode run-all-allowed` |
|------|-----------------|------------------------------|------------------------------|
| demo_phase | ✅ | ✅ | ✅ run → bundle |
| sampleco | ✅ | ✅ | ✅ run → stop CP-B |
| additional_demo | ❌ | ✅ preview / run | ✅ run → stop CP-B · `regression_bundle_probe` |
| sandbox_client | ❌ | ✅ preview / run | ✅ run → cleaning_preview + live guard |

---

## 成熟度總表（v2）

| Step | Module | v1 | v2 |
|------|--------|----|----|
| intake | `new_cleaning_case.py` | done | done |
| decision | `intake_decision_rules_v1.py` | done | done + **experimental** profiles |
| glue | `intake_to_tabular_glue.py` | done | done |
| selector | `tabular_tool_selector.py` | done | done |
| **run_path** | orchestrator + executor | — | **done**（2 stable）/ **controlled_experimental**（+2 · W11-T1） |
| executor | `tabular_tool_executor.py` | done | done（接 run path） |
| outbox | outbox writer/consumer | done | done |
| **checkpoint A/B** | hitl integration | planned | **done**（run） |
| **notify** | controlled_notify_experiment | — | **experimental** |
| inspect | outbox consumer | done / planned replay | done / planned replay |
| release | mainline + experiment regression | done / W6-T8 | done + **W7 flags** |

---

## 模組依賴圖（v2 增量）

```
run_agent_standard_case_experiment.py (W6-T4 / W7-T2)
    │
    ├── evaluate_intake_decision (W5-T1)
    ├── plan_tabular_route (W4-T1)
    ├── run_tabular_intake_tool_path (W4-T3)
    ├── write_checkpoint / CP-A (W5-T2B / W6-T5)
    │
    ├── _execute_run_path_tools ──→ execute_tabular_tool (W3-TL-T3)  [W7-T2]
    │         │
    │         └── outbox/{case_ref}/*.json
    │
    └── maybe_create_checkpoint_b (W6-T6)  [W7-T2 run]

run_controlled_delivery_notify_experiment.py (W7-T3)
    │
    └── load_delivery_context ──→ signoff + report.json
              │
              └── outbox/{case_ref}/notify_experiment_*.json (dry_run=false)
```

---

## 檔案路徑速查（v2 新增）

| 類別 | 路徑 |
|------|------|
| **W7 fixtures** | `cases/additional_demo/` · `cases/sandbox_client/` |
| **Run path config** | `scripts/run_agent_standard_case_experiment.py` → `_RUN_PATH_PROFILES` |
| **Controlled notify** | `delivery/controlled_notify_experiment_v1.py` |
| **Notify CLI** | `scripts/run_controlled_delivery_notify_experiment.py` |
| **Regression** | `scripts/run_agent_standard_case_regression.py` |
| **Tests** | `tests/test_agent_standard_case_experiment.py` · `tests/test_controlled_delivery_notify_experiment_v1.py` |

---

## 版本記錄

| 版本 | 日期 | 變更 |
|------|------|------|
| v1.0 | 2026-06-10 | W6-T1 · 8 步驟 |
| v2.0 | 2026-06-10 | W7-T4 · run_path + notify + 4 fixture + 成熟度更新 |
| v2.1 | 2026-06-10 | W11-T1 · C/D `controlled_experimental` · sandbox live cleaning guard · regression bundle probe |

---

*SKILL-MAP-v2 · W7-T4 · 2026-06-10*
