# TICKET STATE · W10-T1 · agent-lines-ci-workflow-hook-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- **Goal**: 將既有 `scripts/run_agent_lines_ci_suite.py` 掛入 GitHub Actions，使 Agent Lines v1 regression 可在 CI 自動執行（PR path-filtered + nightly），不再僅依賴本地 unittest。

- **Scope**:
  1. 新增 `.github/workflows/agent-lines-ci.yml`
  2. PR（path-filtered）執行 `--scope all`（tabular run-all-allowed + NT preview）
  3. Nightly cron 執行 `--scope all --include-extended-fixtures`
  4. `workflow_dispatch` 支援 scope / extended / stub 參數
  5. 上傳 `outbox/agent_ci/` 等 artifacts

- **NonScope**:
  - ❌ 不改 `scripts/run_agent_lines_ci_suite.py` 核心邏輯
  - ❌ 不改 mainline regression / Gov Core smoke / eval gate workflows
  - ❌ 不升格為 required PR check（optional job）
  - ❌ 不改 `hitl/*` 或其他 tickets state

- **AllowedPaths**:
  - `.github/workflows/agent-lines-ci.yml`
  - `04_Workflows/tickets/W10-T1-agent-lines-ci-workflow-hook-v1_state.md`
  - `docs/ci/README.md`（選擇性）

- **AcceptanceCriteria**:
  - [AC-1] CI workflow 存在且命名清晰（`agent-lines-ci.yml`）
  - [AC-2] 至少 nightly 或 PR 之一觸發 `--scope all`
  - [AC-3] 覆蓋 tabular run-all-allowed + NT preview
  - [AC-4] 重用 Python 3.12 / checkout / setup-python 既有 pattern
  - [AC-5] 獨立 job，不阻塞 mainline CI
  - [AC-6] B_REPORT / O_NOTES 留痕

- **Dependencies**: W10-T1 `integrate-agent-lines-into-ci-v1`（suite script 已交付）

---

## STATE

- **overall_status**: implementer_done
- **current_owner**: implementer
- **next_action**: Reviewer 審查 workflow 觸發條件與 artifact 上傳
- **last_updated**: 2026-06-16 · Implementer
- **status_by_role**:
  - orchestrator: pending
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

- **changed_files**:
  - `.github/workflows/agent-lines-ci.yml`（新增）
  - `04_Workflows/tickets/W10-T1-agent-lines-ci-workflow-hook-v1_state.md`（本檔）

- **verification**:
  - `python -m unittest tests.test_agent_lines_ci_suite_v1 -v` → **10/10 OK**
  - `python scripts/run_agent_lines_ci_suite.py --scope all --format json` → `ok: true`（tabular + non_tabular real fixtures）

- **workflow_behavior**:
  | Job | Trigger | Command |
  |-----|---------|---------|
  | `agent-lines-ci-pr` | `pull_request`（path-filtered：agent-line scripts / cases / 相關 tests） | `python scripts/run_agent_lines_ci_suite.py --scope all --format json` |
  | `agent-lines-ci-nightly` | `schedule` cron `30 5 * * *` UTC | `python scripts/run_agent_lines_ci_suite.py --scope all --include-extended-fixtures --format json` |
  | `agent-lines-ci-manual` | `workflow_dispatch` | `--scope` / `--include-extended-fixtures` / `AGENT_LINES_CI_USE_STUB_FIXTURES` 依 inputs |

- **behavior_notes**:
  - Python **3.12** · `actions/checkout@v4` · `actions/setup-python@v5`（對齊 `core-agent-smoke.yml` / `eval-gate-ci.yml`）
  - PR job 先跑 `tests.test_agent_lines_ci_suite_v1`，再跑 full suite
  - Nightly 額外 `--include-extended-fixtures`（Wave 7 C/D profiles）
  - Artifacts：`outbox/agent_ci/` · tabular / NT outbox JSON + CI summary wrapper
  - **Optional check**：未加入 branch protection required checks
  - suite 僅用 stdlib + repo scripts，無額外 pip install

---

## C_REPORT

- **conclusion**: pending
- **blocking_issues**: —
- **checks_summary**: —
- **risk_level**: —
- **suggestions**: —

---

## D_REPORT

- **docs_updates**: none（`docs/agent-lines-ci-suite-v1.md` 已描述 CLI；workflow hook 留本票 B_REPORT）

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-06-16 | implementer | Agent Lines suite 已掛入 CI：`.github/workflows/agent-lines-ci.yml` — PR path-filtered `--scope all` + nightly cron UTC 05:30 `--include-extended-fixtures` + manual dispatch |
