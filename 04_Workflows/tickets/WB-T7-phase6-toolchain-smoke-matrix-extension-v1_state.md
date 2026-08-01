# TICKET STATE · WB-T7 · phase6-toolchain-smoke-matrix-extension-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- Goal: 在 WA-T6 P6 contract 之上增補 tool-chain smoke matrix（YAML SSOT），與 WB-T4 dashboard 命令表對齊；Wave C Agent 可讀 tier / gate_class / blocks_mainline。
- Scope:
  - `routing/toolchain_smoke_matrix_v1.yaml`（新增 ≥10 列）
  - `tests/test_phase6_toolchain_smoke_matrix_v1.py`（schema + 命令存在性；不 subprocess smoke）
  - `docs/phase6-int-regression-gate-contract-v1.md` 附录 A 引用 YAML
  - `tests/test_phase6_int_regression_gate_contract_v1.py` 增補斷言
  - `docs/WAVE_PROGRESS_DASHBOARD.md` P6 84%→88%
- NonScope:
  - 不改 `.github/workflows/*`
  - 不改 `core/wave7_regression_gate.py` Tier-A/B
  - 不新增 CI workflow step / smoke runner
  - 不把 tool-chain smoke 升格 PR mandatory
  - 不改 MVP mainline regression 行為
- AllowedPaths:
  - `docs/phase6-int-regression-gate-contract-v1.md`（§ 附錄增補）
  - `routing/toolchain_smoke_matrix_v1.yaml`
  - `tests/test_phase6_toolchain_smoke_matrix_v1.py`
  - `tests/test_phase6_int_regression_gate_contract_v1.py`
  - `04_Workflows/tickets/WB-T7-phase6-toolchain-smoke-matrix-extension-v1_state.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
- BlockedPaths:
  - `.github/workflows/*`
  - `core/wave7_regression_gate.py`
  - `scripts/run_mvp_mainline_regression.py`（行為）
  - INT gate / CI runtime 模組
- Dependencies: WA-T6 · WA-T3 P3.5 · WB-T4 · W3-TL · W4-T2/T4 · W10-T1
- AcceptanceCriteria: AC-1–AC-10（doc+test only；無 runtime 行為變更）

---

## STATE

- overall_status: done
- current_owner: orchestrator
- next_action: 無（票面已收口；Toolchain Wave B closure complete）
- last_updated: 2026-06-11 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files:
  - `routing/toolchain_smoke_matrix_v1.yaml`（新增 · 12 entries）
  - `tests/test_phase6_toolchain_smoke_matrix_v1.py`（新增）
  - `docs/phase6-int-regression-gate-contract-v1.md`（附录 A → YAML SSOT）
  - `tests/test_phase6_int_regression_gate_contract_v1.py`（YAML 引用斷言）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（P6 84%→88% · WB-T7 驗證命令）
  - `04_Workflows/tickets/WB-T7-phase6-toolchain-smoke-matrix-extension-v1_state.md`
- artifacts:
  - `routing/toolchain_smoke_matrix_v1.yaml`（machine-readable SSOT）
- verification:
  - `python -m unittest tests.test_phase6_toolchain_smoke_matrix_v1 -v` → OK
  - `python -m unittest tests.test_phase6_int_regression_gate_contract_v1 -v` → OK
- behavior_notes:
  - doc+test only；無 CI / INT gate / runner 行為變更
  - agent lines CI 明示 `gate_class=optional`（TS-AGENT-LINES-CI*）
  - MVP mainline 標 `tier=release_only` · `blocks_mainline=true`
  - YAML 覆蓋 WB-T4 dashboard 六條驗證命令（單向同步）
- deferred_items:
  - 無 runtime smoke runner；執行仍用既有 scripts

---

## C_REPORT

- conclusion: **accepted**
- blocking_issues: **无**
- checks_summary:
  - **FRAME**：未被 Implementer 改动；doc+test only、ForbiddenChanges（不改 CI/workflow/gate runtime）遵守。
  - **B_REPORT 证据**：`tests.test_phase6_toolchain_smoke_matrix_v1` + gate contract 含于汇总 **108/108 OK**；`routing/toolchain_smoke_matrix_v1.yaml` **12 entries**（≥10）；含 tier / `gate_class` / `blocks_mainline`；agent lines CI 明示 optional；MVP mainline `release_only` + `blocks_mainline=true`。
  - **AC 对照**：P6 附录 A 引用 YAML SSOT；与 WB-T4 dashboard 六条验证命令单向同步；Dashboard P6 84%→88%；无 CI workflow 变更。
  - **Rule 3/5**：变更均在 AllowedPaths。
- risk_level: **low**
- suggestions:
  - **缺但可接受**：无 runtime smoke runner（执行仍用既有 scripts/unittest；符合 NonScope）。
  - FRAME 未逐条枚举 AC-1–AC-10 文字，但 B_REPORT + 交付物覆盖完整 → 可接受。
  - 无 blocking；可交 Scribe。

---

## D_REPORT

- docs_updates:
  - P6 附录 A 与 `routing/toolchain_smoke_matrix_v1.yaml` 交叉引用已交付；Dashboard Toolchain 分栏状态列已对齐（WC-PRE-01）
- progress_entry: WB-T7 交付 P6 toolchain smoke matrix YAML SSOT（Reviewer **`accepted`**）；`tests.test_phase6_toolchain_smoke_matrix_v1` 含于 Wave B 汇总 108/108 OK；无 CI workflow 变更。
- followup_suggestions:
  - **WC-PRE-05**：runtime smoke runner 消费 `toolchain_smoke_matrix_v1.yaml`
  - **WC-PRE-07**：mandatory CI runner（**需尚書省批文**；无批文不得改 PR required）
