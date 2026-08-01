# TICKET STATE · W4-T4 · Routing CI Hooks（dry-run + release checklist）

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 4-COORD · Tabular MVP · Routing CI Hooks

---

## FRAME

- Title: W4-T4 · Routing CI Hooks（dry-run + release checklist）
- Goal: 在 PR CI 中加上 routing eval dry-run 檢查（`tests.test_routing_eval_runner` + `run_routing_eval.py --dry-run`），並在 docs 中定義 Tabular MVP release checklist；不在 PR CI 跑 mainline regression 或 execute 模式。
- Scope:
  - 修改 `.github/workflows/eval-gate-ci.yml` — 在 PR/push job 新增 routing eval unittest + dry-run CLI 步驟
  - 新增 `docs/tabular-mvp-release-checklist.md` — 發版前人工 checklist
  - 更新 `04_Workflows/WORKFLOW_INDEX.md` · `docs/WAVE_PROGRESS_DASHBOARD.md`
- NonScope:
  - **不**改 routing engine、router、Gov policy、主鏈腳本
  - **不**接 Langfuse、不加 secrets 或外部依賴
  - **不**在 PR CI 跑 `--execute` 或 `run_mvp_mainline_regression.py`
  - **不**讓本步驟成為唯一 CI 守門（與既有 eval-gate / core-agent-smoke 並存）
  - **不**改任何 `*.py` / `tests/*` 或治理母本（憲法 / ENGINEERING_CONTRACT / AGENTS / `.cursor/rules/*`）
- Minimal Read Set:
  - `.github/workflows/eval-gate-ci.yml`
  - `.github/workflows/core-agent-smoke.yml`（對照 PR tier 風格）
  - `docs/routing-eval-runner-v1.md`（W4-T2 runner spec）
  - `docs/mvp-mainline-regression.md`（主鏈回歸；release 手動項）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
- AllowedPaths:
  - `.github/workflows/eval-gate-ci.yml`
  - `docs/tabular-mvp-release-checklist.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `04_Workflows/tickets/W4-T4-routing-ci-hooks_state.md`
- BlockedPaths:
  - `scripts/*.py` · `tests/*` · `routing/*` · `tools/*` · `core/*`
  - `HARNESS_CONSTITUTION.md` · `ENGINEERING_CONTRACT.md` · `AGENTS.md` · `.cursor/rules/*`
  - `config/routing_policy.yaml`
- Dependencies:
  - **W4-T2** · `scripts/run_routing_eval.py` + `tests/test_routing_eval_runner.py`
  - **W2-T2** · `routing/routing_eval_cases_v1.yaml`
- Risks:
  - CI 時間略增（~1 min 以內）→ 可接受
  - cases/catalog 漂移 → dry-run 失敗即 PR 紅，符合設計
- Observability:
  - logs: GitHub Actions step stdout（unittest + JSON dry-run）
  - metrics: N/A
  - traces: N/A
- OutputArtifacts:
  - `.github/workflows/eval-gate-ci.yml`（routing eval steps）
  - `docs/tabular-mvp-release-checklist.md`
- AcceptanceCriteria:
  - **AC-1**：PR workflow 中包含跑 `tests.test_routing_eval_runner` 的 step
  - **AC-2**：PR workflow 中包含跑 `scripts/run_routing_eval.py --dry-run --format json` 的 step，並在所有 case 對齊時成功退出
  - **AC-3**：這些步驟不跑任何 `--execute` 模式，不拉起 `run_mvp_mainline_regression.py`
  - **AC-4**：release checklist 文檔列出至少：主鏈 6/6、routing eval dry-run、W3-TL 四件套 unittest
  - **AC-5**：本票修改的 CI 步驟經本地命令驗證通過；對現有 workflow 影響有限（僅 eval-gate job 追加兩條命令）
- VerificationCommands:
  - `python -m unittest tests.test_routing_eval_runner -v`
    - 預期：**12/12 OK**，exit 0
  - `python scripts/run_routing_eval.py --dry-run --format json`
    - 預期：**4/4 aligned**，`ok: true`，exit 0
  - 提醒：mainline regression **不在** PR CI；release checklist §2 要求發版前人工跑 `run_mvp_mainline_regression.py -v`

---

## STATE

- overall_status: in_progress
- current_owner: implementer
- next_action: Reviewer 對照 AC-1–AC-5 審查 CI diff 與 release checklist
- last_updated: 2026-06-10 · orchestrator + implementer
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

- changed_files:
  - `.github/workflows/eval-gate-ci.yml`
  - `docs/tabular-mvp-release-checklist.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `04_Workflows/tickets/W4-T4-routing-ci-hooks_state.md`
- artifacts: `docs/tabular-mvp-release-checklist.md`
- verification:
  - `python -m unittest tests.test_routing_eval_runner -v` → **12/12 OK**
  - `python scripts/run_routing_eval.py --dry-run --format json` → **4/4 aligned**, exit 0
- behavior_notes: routing eval 掛在 `eval-gate-ci.yml` 的 `eval-gate` job（PR/push），緊接 P+ eval unit tests 之後；dry-run only，無 `--execute`
- deferred_items: mainline regression 接入 nightly CI（未來票）；W3-TL / glue / intake path unittest 接入 PR CI（未來票，現僅 release checklist）

---

## C_REPORT

- conclusion: accepted_with_gaps
- blocking_issues: None
- checks_summary:
  - **FRAME / B_REPORT 对照**：已读 FRAME AC-1–AC-5、NonScope、VerificationCommands 与 B_REPORT；B_REPORT 所列 5 个 changed_files 均在 AllowedPaths 内；B_REPORT 宣称的 step 名称、命令与 verification 结果与 repo 现状一致。
  - **AC-1（CI unittest step）**：`.github/workflows/eval-gate-ci.yml` → job `eval-gate`（PR/push，`if: github.event_name != 'schedule'`）→ step `Routing eval dry-run (W4-T4)` 含 `python -m unittest tests.test_routing_eval_runner -v`。**通过**。
  - **AC-2（CI dry-run CLI）**：同 step 含 `python scripts/run_routing_eval.py --dry-run --format json`；`set -euo pipefail` 保证任一命令非零退出即失败 step。**通过**（AC 要求「step」；两命令合于单 step，符合任务卡与 B_REPORT 描述）。
  - **AC-3（无 execute / 无 mainline regression in CI）**：全 repo `.github/workflows/` grep `--execute` 与 `run_mvp_mainline_regression` → **0 命中**；`eval-shadow-nightly` 亦无 routing eval / mainline 调用；dry-run CLI 输出 `"execute": false`（catalog case 仅 plan 对齐 mainline entrypoint，未拉起脚本）。**通过**。
  - **AC-4（release checklist）**：`docs/tabular-mvp-release-checklist.md` §2.1 主链 6/6、§2.3 W3-TL 四件套 unittest、§2.4 routing eval dry-run；§4 表格明确 PR CI 仅自动覆盖 routing eval dry-run，主链/W3-TL 为 release 人工项。**通过**。
  - **AC-5（本地验证 · Reviewer 独立复跑 2026-06-15）**：
    - `python -m unittest tests.test_routing_eval_runner -v` → **Ran 12 tests in 0.480s — OK**（12/12），exit 0。
    - `python scripts/run_routing_eval.py --dry-run --format json` → `"ok": true`, `"message": "4/4 case(s) aligned"`, `"execute": false`, exit 0。
    - 与 B_REPORT / CI step 命令一致。**通过**。
  - **Diff hygiene（非阻塞 gap）**：`eval-gate-ci.yml` 同文件另含 W1-T3 observability、P+ unittest 扩充、toolchain governance snapshot 等非 W4-T4 变更；`WORKFLOW_INDEX.md` diff 范围亦大于本票。**功能性满足 AC；合并审计粒度不足**。
- risk_level: low
- suggestions:
  - **diff 拆分**：合并前将 `eval-gate-ci.yml` 中 W1-T3 / WC-IMPL / P+ 扩充与 W4-T4 `Routing eval dry-run` step 分 commit 或分 PR，便于 bisect 与 AC-5「影响有限」审计。
  - **deferred — mainline regression nightly CI**：维持 B_REPORT deferred；另开 follow-up 票在 nightly（非 PR）job 挂 `run_mvp_mainline_regression.py -v`，与 checklist §2.1 对齐；PR CI 仍禁止。
  - **deferred — W3-TL / glue / intake path PR CI**：维持 release checklist 人工项；后续票评估是否接入 `core-agent-smoke` 或独立 lightweight job，避免 eval-gate job 持续膨胀。
  - **Scribe 收尾**：确认 `docs/WAVE_PROGRESS_DASHBOARD.md` 与 C_REPORT `accepted_with_gaps` 结论同步；本票 STATE `reviewer: pending` → `done` 由 Orchestrator/Scribe 更新。

---

## D_REPORT

- docs_updates: <!-- Scribe 填 -->
- progress_entry: <!-- Scribe 填 -->
- followup_suggestions: <!-- Scribe 填 -->

---

## O_NOTES

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-10 | orchestrator | 開票 FRAME + AC | 本檔 |
| 2026-06-10 | implementer | CI dry-run steps + release checklist + index | 本檔 B_REPORT |
