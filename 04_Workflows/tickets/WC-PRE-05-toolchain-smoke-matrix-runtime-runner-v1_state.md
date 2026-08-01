# TICKET STATE · WC-PRE-05 · toolchain-smoke-matrix-runtime-runner-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

<!-- Orchestrator 填 -->

---

## STATE

- overall_status: accepted_with_gaps
- current_owner: orchestrator
- next_action: 無（本地 optional runner 已交付；CI 接入留 WC-PRE-07）
- last_updated: 2026-06-12 · reviewer
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: pending

---

## B_REPORT

- changed_files:
  - `scripts/run_toolchain_smoke_matrix.py`（新建 · 讀 YAML、tier/smoke-id 篩選、dry-run / execute）
  - `tests/test_run_toolchain_smoke_matrix_v1.py`（新建 · schema / dry-run / mocked execute）
  - `docs/phase6-int-regression-gate-contract-v1.md`（附录 A **一行** runner 指針）
  - `04_Workflows/tickets/WC-PRE-05-toolchain-smoke-matrix-runtime-runner-v1_state.md`（本檔 B_REPORT）
- artifacts:
  - `scripts/run_toolchain_smoke_matrix.py`
- verification:
  - `python -m unittest tests.test_run_toolchain_smoke_matrix_v1 tests.test_phase6_toolchain_smoke_matrix_v1 -v` → **19/19 OK**
  - `python scripts/run_toolchain_smoke_matrix.py --list --format json` → exit 0；`entries_requested=12`；`dry_run=true`
- behavior_notes:
  - 本地 optional runner；預設 `--tier local_recommended`；`--dry-run` / `--list` 僅列計畫不執行。
  - 未改 `routing/toolchain_smoke_matrix_v1.yaml` 內容、`.github/workflows/*`、`core/wave7_regression_gate.py` 或 MVP mainline regression 行為。
  - 不接 PR mandatory gate；`blocks_mainline` 僅報告語義，runner 不自動升格 release gate。
- deferred_items:
  - 未將 runner 接入 CI workflow step（符合 NonScope）

---

## C_REPORT

- conclusion: **accepted_with_gaps**
- blocking_issues: none
- checks_summary:
  - 抽检 `scripts/run_toolchain_smoke_matrix.py` 存在；支持 `--list` · `--dry-run` · tier/smoke-id 筛选；默认 `--tier local_recommended`。
  - B_REPORT 验证 **19/19 OK** + `--list --format json` CLI 抽检（`entries_requested=12` · `dry_run=true`）。
  - 未改 `routing/toolchain_smoke_matrix_v1.yaml` 内容、`.github/workflows/*`、`core/wave7_regression_gate.py`；`blocks_mainline` 仅报告语义。
  - gap（非阻塞，by design）：runner 未接入 CI workflow；P6 contract 附录 A 仅增一行 runner 指针（非语义正文改写）。
- risk_level: **low**（本地 runner）；**medium**（若 Wave C 误当 PR mandatory gate）
- suggestions:
  - Wave C 可本地调用 `run_toolchain_smoke_matrix.py` 消费 WB-T7 YAML；C1 盘点时引用 dry-run / list 能力。
  - **不得**假设 smoke matrix 已是 PR required 或 `blocks_mainline=true` 的 prod gate（见 WC-PRE-07 · 需批文）。
  - WC-PRE-06 治理升格与 WC-PRE-07 mandatory CI 须尚書省批文后另票实装。

---

## D_REPORT

<!-- Scribe 填 -->
