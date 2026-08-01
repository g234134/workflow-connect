# TICKET STATE · WF-P6-INT-GATE · Phase 6 INT Regression Gate Verification Line

> **Orchestrator line ticket** · 總調度批 WF-2026-06-27 · 子 agent 隔離施工  
> **Upstream SSOT**: `docs/phase6-int-regression-gate-contract-v1.md` · WA-T6  
> **handoff 摘要檔**；跨 Task 子 agent 以本檔 FRAME 為準

---

## FRAME

- **Goal**: 補齊 Phase 6 INT regression gate 的 **consolidated verification report** 與 **machine-readable mandatory 邊界標記**（Tier-A local mandatory · NOT in PR CI），使 operator 有單一 artifact 可查 gate 通過證據；不改 CI gate。
- **Scope**:
  - 新增 `docs/phase6-int-regression-verification-report-v1.md`（executed report · 含 Tier-A CLI JSON 摘要）
  - 在 `routing/toolchain_smoke_matrix_v1.yaml` 新增 `TS-INT-TIER-A` 條目（`tier: local_mandatory` · `gate_class: mandatory` · `blocks_pr_ci: false`）
  - 更新 contract / bundle SSOT cross-ref（`docs/phase6-int-regression-gate-contract-v1.md` §8 · `docs/testing.md` 一行 pointer）
  - 可選：擴展 `tests/test_phase6_toolchain_smoke_matrix_v1.py` 或 contract unittest 驗證新 YAML 條目
- **NonScope**:
  - 不改 `_wave7_regression_gate.py` / `core/wave7_regression_gate.py` 邏輯
  - 不改 `.github/workflows/*` · 不把 INT Tier-A 硬塞 PR CI
  - 不改 Batch 1 治理 YAML · 不改全局 Phase% 數字
  - 不新增 nightly INT GHA workflow · 不擴 Tier-B 場景
- **AllowedPaths**:
  - `docs/phase6-int-regression-verification-report-v1.md`（新建）
  - `docs/phase6-int-regression-gate-contract-v1.md`（§8 cross-ref only）
  - `docs/testing.md`（INT report pointer · 最小 diff）
  - `routing/toolchain_smoke_matrix_v1.yaml`（新增 TS-INT-TIER-A 條目）
  - `tests/test_phase6_int_regression_gate_contract_v1.py`
  - `tests/test_phase6_toolchain_smoke_matrix_v1.py`
  - `04_Workflows/tickets/WF-P6-INT-GATE_state.md`（B/C/D_REPORT only · FRAME/STATE by Orchestrator）
- **BlockedPaths**:
  - `.github/workflows/*`
  - `04_Workflows/_wave7_regression_gate.py`
  - `01_Environments/python_venvs/gov_core_system/core/wave7_regression_gate.py`
  - Batch 1 治理 YAML（`*governance*.yaml` 於 `routing/` 或 `docs/governance/` 已定稿檔）
  - `docs/WAVE_PROGRESS_DASHBOARD.md` Phase% 表
  - `04_Workflows/00_Agent_Work_Progress.md` 歷史段落（Scribe 僅末尾追加）
- **Dependencies**:
  - WA-T6 contract v1（已 landed）
  - `04_Workflows/_wave7_regression_gate.py` CLI（已存在）
  - gov_core_system venv（Tier-A live run · 缺 venv 則 report 標 `blocked`）
- **boot_text**: `WF-P6-INT-GATE: Phase 6 INT Tier-A verification report + toolchain matrix mandatory entry; doc/YAML only; no CI change`
- **AcceptanceCriteria**:
  - **AC-1**: `docs/phase6-int-regression-verification-report-v1.md` 存在，含 executive summary · Tier-A 命令 · JSON 關鍵欄位 · verdict
  - **AC-2**: `routing/toolchain_smoke_matrix_v1.yaml` 含 `TS-INT-TIER-A`，語意為 **local mandatory · not in PR CI**
  - **AC-3**: `python -m unittest tests.test_phase6_int_regression_gate_contract_v1 -v` → exit 0
  - **AC-4**: `python -m unittest tests.test_phase6_toolchain_smoke_matrix_v1 -v` → exit 0（若改 matrix）
  - **AC-5**: `python 04_Workflows/_wave7_regression_gate.py --tier A --pretty` → `ok: true` · exit 0（venv 可用時；否則 report 標 blocked + contract unittest 仍绿）
  - **AC-6**: 無 `.github/workflows/*` diff

### Wave Master 擴展

- wave_id: null
- group_id: G6
- lifecycle_phase: B
- phase_targets: P6
- ticket_class: doc/spec + verification
- evidence_tier: L-local
- parallel_ok: true
- non_claims:
  - no_ci_gate_change
  - no_nightly_int_in_ci
  - no_global_phase_pct_uplift

---

## STATE

- overall_status: done_with_gaps
- lifecycle_phase: D
- current_owner: orchestrator
- next_action: orchestrator 歸檔 batch WF-2026-06-27；INT Tier-A PR CI 納入須另開票
- last_updated: 2026-06-27 · scribe
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

<!-- Implementer 填 -->

- changed_files:
  - docs/phase6-int-regression-verification-report-v1.md (NEW)
  - docs/phase6-int-regression-gate-contract-v1.md (§8 cross-ref + appendix A.2 TS-INT-TIER-A row)
  - docs/testing.md (INT verification report pointer)
  - routing/toolchain_smoke_matrix_v1.yaml (TS-INT-TIER-A + local_mandatory tier)
  - tests/test_phase6_int_regression_gate_contract_v1.py (verification report tests)
  - tests/test_phase6_toolchain_smoke_matrix_v1.py (TS-INT-TIER-A semantics + 04_Workflows path resolve)
- artifacts:
  - report: docs/phase6-int-regression-verification-report-v1.md
  - matrix_entry_id: TS-INT-TIER-A
- verification:
  - `python -m unittest tests.test_phase6_int_regression_gate_contract_v1 -v` → **ok** (24 tests, exit 0)
  - `python -m unittest tests.test_phase6_toolchain_smoke_matrix_v1 -v` → **ok** (13 tests, exit 0)
  - `python 04_Workflows/_wave7_regression_gate.py --tier A --pretty` → **ok** (`ok: true`, 14 modules, 112 passed, exit 0)
- behavior_notes:
  - TS-INT-TIER-A uses new tier `local_mandatory` + `gate_class: mandatory` + `blocks_pr_ci: false`; does not block PR merge
  - Matrix test allows only TS-INT-TIER-A as mandatory gate_class; all other entries remain optional/shadow
  - gov_core_system venv available; live Tier-A run captured in verification report
- deferred_items:
  - nightly INT GHA workflow (explicit NonScope)
  - wiring INT Tier-A into eval-gate-ci / core-agent-smoke as required check
  - Tier-B scenario expansion

---

## C_REPORT

<!-- Reviewer 填 -->

- ok: true
- conclusion: accepted
- failed_steps: 无
- notes: 独立重跑 AC-3/4/5 全绿；AC-1/2 文档与 YAML 语义对齐 B_REPORT；scope 仅 AllowedPaths；repo 内另有无关 workflow dirty 状态，本票未触 AC-6 边界。
- blocking_issues: 无
- checks_summary:
  - AC-1: PASS — verification report 含 executive summary · Tier-A 命令 · JSON 关键栏 · verdict PASS
  - AC-2: PASS — TS-INT-TIER-A · tier local_mandatory · gate_class mandatory · blocks_pr_ci false
  - AC-3: PASS — contract unittest 24/24 exit 0（checker 独立重跑）
  - AC-4: PASS — matrix unittest 13/13 exit 0（checker 独立重跑）
  - AC-5: PASS — tier A live ok true · 112 passed · exit 0（checker 独立重跑）
  - AC-6: PASS — B_REPORT changed_files 无 .github/workflows/*；BlockedPaths 未修改
  - scope: PASS — changed_files ⊆ AllowedPaths
- risk_level: low
- suggestions:
  - Scribe 末尾追加 Progress 时引用 verification report 路径即可
  - 后续若需 PR CI 纳入 INT Tier-A 须另开 ticket（本票 NonScope）

---

## D_REPORT

<!-- Scribe 填 -->

- docs_updates:
  - `04_Workflows/workflow_line_status_2026-06-27.yaml` — `p6_int_regression_gate.complete: true` · lifecycle `done_with_gaps` · artifacts filled
  - `04_Workflows/00_Agent_Work_Progress.md` — 末尾追加 batch WF-2026-06-27 P6 段落
- progress_entry:
  - `04_Workflows/00_Agent_Work_Progress.md` §2026-06-27 · WF batch P6+P8.9 verification
  - verification report: `docs/phase6-int-regression-verification-report-v1.md`
  - matrix entry: `routing/toolchain_smoke_matrix_v1.yaml` · `TS-INT-TIER-A`
- followup_suggestions:
  - 若需 nightly INT GHA 或 PR CI 硬納 Tier-A → 另開 ticket（本線 NonScope）
  - Tier-B heavier integration 維持 optional；擴場景須 WA-T6 修訂 + 新 matrix 條目
  - Scribe SSOT: `workflow_line_status_2026-06-27.yaml` · functional_gaps 保留 nightly CI + tier B optional
