# W6-T4 · Agent-run Standard Case Orchestrator v1

> **角色**: Orchestrator + Implementer  
> **類型**: Implementation  
> **Wave**: Wave 6 — 95% Automation Blueprint 延伸  
> **建立日期**: 2026-06-10  
> **狀態**: reviewer accepted · scribe done

---

## FRAME

### Goal
實作 Agent-run 標準案實驗線 CLI，串接 W5-T1B decision、W4-T1 glue、W4-T3 tool path preview、W5-T2B checkpoint 工具；限定 demo_phase / sampleco；不改 production 主鏈預設行為。

### Scope
- [x] `scripts/run_agent_standard_case_experiment.py`
- [x] `docs/agent-run-standard-case-orchestrator-v1.md`
- [x] `tests/test_agent_standard_case_experiment.py`
- [x] preview 模式：S3 / S4 / S5 / S6 / S11 mock / S12 planned
- [x] run 模式最小版：allowlist + auto-approve-intake + resume plan
- [x] WORKFLOW_INDEX / WAVE_PROGRESS_DASHBOARD 索引更新

### NonScope
- 不修改禁改檔（new_cleaning_case、local_ui、mainline regression、glue、selector、executor、Gov routing）
- 不執行 S8 cleaning / S9 outbox / S10 bundle / S13 delivery
- S11 使用 mock/placeholder（非 bundle 讀取）

### BlockedPaths（未修改）
- `scripts/new_cleaning_case.py`
- `app/local_ui.py`
- `scripts/run_mvp_mainline_regression.py`
- `routing/intake_to_tabular_glue.py`
- `tools/tabular_tool_selector.py`
- `tools/tabular_tool_executor.py`

---

## STATE

```yaml
overall_status: reviewer_accepted
current_owner: scribe
last_updated: 2026-06-10

status_by_role:
  orchestrator: done
  implementer: done
  reviewer: done
  scribe: done

deliverables:
  cli: scripts/run_agent_standard_case_experiment.py
  docs: docs/agent-run-standard-case-orchestrator-v1.md
  tests: tests/test_agent_standard_case_experiment.py
  state: 04_Workflows/tickets/W6-T4-agent-run-standard-case-orchestrator-v1_state.md
```

---

## B_REPORT（Implementer）

### changed_files
- `scripts/run_agent_standard_case_experiment.py`（新建）
- `docs/agent-run-standard-case-orchestrator-v1.md`（新建）
- `tests/test_agent_standard_case_experiment.py`（新建）
- `04_Workflows/tickets/W6-T4-agent-run-standard-case-orchestrator-v1_state.md`（新建）
- `04_Workflows/WORKFLOW_INDEX.md`（Wave 6 條目追加）
- `docs/WAVE_PROGRESS_DASHBOARD.md`（W6-T4 狀態追加）

### verification
```bash
python -m unittest tests.test_agent_standard_case_experiment -v
```

### behavior_notes
- preview：Checkpoint A 僅 `would_pause`，不寫 outbox
- run + needs_review：寫入 `outbox/<case_ref>/checkpoint_A-intake-confirmation_*.json`
- run + `--auto-approve-intake`：跳過 Checkpoint A，輸出 `resume_plan`
- S11 output_guard 為 profile mock（demo_phase=ok，sampleco=warning）

### deferred_items
- S8–S10 實際執行（另開 W6-T5+）
- S11 從 bundle 讀取 live output_guard
- Checkpoint B 檔案寫入與 resume CLI

---

## Acceptance Criteria（Reviewer 檢查）

| AC | 描述 | Reviewer |
|----|------|----------|
| AC-1 | `scripts/run_agent_standard_case_experiment.py` 存在且 allowlist 僅 demo_phase / sampleco | ✅ |
| AC-2 | preview 串接 S3 / S4 / S5 / S6 / S11 mock / S12 planned | ✅ |
| AC-3 | run 模式：`--auto-approve-intake` → resume_plan；needs_review → outbox 寫 A | ✅ |
| AC-4 | 未 import 禁改模組（unittest AST 檢查） | ✅ |
| AC-5 | `tests.test_agent_standard_case_experiment` 全綠（8/8） | ✅ |
| AC-6 | docs + WORKFLOW_INDEX + WAVE_PROGRESS 索引 | ✅ |

**例外 / deferred（不阻擋收口）**：
- 未 import W6-T5/W6-T6 整合模組（inline checkpoint 邏輯）；對稱接線另票。
- S11 mock 的 `forced_cleaning` 使 demo_phase `checkpoint_b.would_trigger=true`，與 W6-T3 文字略有出入；見 `docs/agent-standard-line-v1-summary.md` §4。

---

## C_REPORT（Reviewer）

- **conclusion**: `accepted_with_gaps`
- **blocking_issues**: 無
- **checks_summary**:
  - unittest 8/8 OK（2026-06-10）
  - demo_phase preview CLI 乾跑 exit 0
  - forbidden import AST 檢查通過
  - BlockedPaths 未修改
- **risk_level**: low
- **suggestions**:
  - 後續票：orchestrator 改呼叫 `evaluate_and_maybe_checkpoint_a` / `maybe_create_checkpoint_b`
  - 對齊 Checkpoint B 觸發規則與 W6-T6 整合層

---

## D_REPORT（Scribe）

- **docs_updates**:
  - 新增 `docs/agent-standard-line-v1-summary.md`（收口總結）
  - 更新 `docs/agent-run-standard-case-orchestrator-v1.md` §8 cross-ref
  - 更新 `docs/agent-run-standard-case-experiment-v1.md` §10 產物索引
- **progress_append**: 待尚書省封存時追加 Progress 末尾（本收口票）
- **handoff**: Agent Standard Line v1 最小可跑路徑見 summary §5

---

*W6-T4 · Agent-run Standard Case Orchestrator v1 · 2026-06-10*
