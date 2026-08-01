# TICKET STATE · WF-P6-INT-UPLIFT · Phase 6 INT Gate Uplift to 90%+ (Technical + Governance Prep)

> **Orchestrator line ticket** · P6 专项目 · 子 agent 隔离施工  
> **Upstream SSOT**: `docs/phase6-int-regression-gate-contract-v1.md` · `WF-P6-INT-GATE` (verification line complete)  
> **handoff 摘要檔**；跨 Task 子 agent 以本檔 FRAME 為準

---

## FRAME

- **Goal**: 在治理安全前提下，补齐 P6 INT regression gate **uplift 到 90%+** 所需的技术证据与 CI 设计文档；使尚書省可在治理线单独裁决 Phase% 调整，**本票不直接改 Phase%**。
- **Scope**:
  - 新建 `docs/ci-design-p6-int-gate-v1.md`（CI 接入设计 · 技术落地 vs 治理解锁两步）
  - 补充 `routing/toolchain_smoke_matrix_v1.yaml` P6 INT gate 相关条目（mandatory / optional / CI 建议语义）
  - 补充 `docs/phase6-int-regression-verification-report-v1.md`「CI readiness」节
  - 补充 `docs/testing.md` pointer（CI design doc cross-ref）
  - 在 `04_Workflows/workflow_line_status_2026-06-27.yaml` P6 行新增 `uplift_ready: true`（**不改** `complete` / 全局 Phase%）
  - 本票 FRAME 即 uplift 治理票草稿载体（技术证据 + uplift 边界）
- **NonScope**:
  - **不**修改 `.github/workflows/*`（须尚書省批准 CI 设计后另票落地）
  - **不**改 Batch 1 治理 YAML
  - **不**改 `docs/WAVE_PROGRESS_DASHBOARD.md` Phase% 数字
  - **不**改 `_wave7_regression_gate.py` / `core/wave7_regression_gate.py` 逻辑
  - **不**宣称 nightly INT CI 已上线或 PR mandatory 已接入
- **AllowedPaths**:
  - `docs/phase6-int-regression-gate-contract-v1.md`（**仅** §8 / appendix cross-ref 补充，不改核心 §1–§7 条款）
  - `docs/phase6-int-regression-verification-report-v1.md`
  - `docs/ci-design-p6-int-gate-v1.md`（**新建**）
  - `docs/testing.md`（最小 pointer diff）
  - `routing/toolchain_smoke_matrix_v1.yaml`
  - `04_Workflows/workflow_line_status_2026-06-27.yaml`（仅 `uplift_ready` 等预备字段）
  - `04_Workflows/tickets/WF-P6-INT-UPLIFT_state.md`（B/C/D_REPORT only · FRAME by Orchestrator）
  - `tests/test_phase6_int_regression_gate_contract_v1.py`（若需验证新 cross-ref）
  - `tests/test_phase6_toolchain_smoke_matrix_v1.py`（若改 matrix）
- **BlockedPaths**:
  - `.github/workflows/*`
  - Batch 1 治理 YAML（`*governance*.yaml` 于 `routing/` 或 `docs/governance/` 已定稿档）
  - `docs/WAVE_PROGRESS_DASHBOARD.md` Phase% 表
  - `04_Workflows/_wave7_regression_gate.py`
  - `01_Environments/python_venvs/gov_core_system/core/wave7_regression_gate.py`
  - `04_Workflows/00_Agent_Work_Progress.md` 历史段落（Scribe 仅末尾追加）
- **Dependencies**:
  - `WF-P6-INT-GATE` verification line complete（2026-06-27）
  - `docs/phase6-int-regression-gate-contract-v1.md` v1 landed
  - `04_Workflows/_wave7_regression_gate.py` CLI 可用
  - gov_core_system venv（Tier-A live run）
- **boot_text**: `WF-P6-INT-UPLIFT: 設計並補齊 P6 INT gate 的 CI 接入方案 + smoke matrix + uplift-ready 標記`
- **AcceptanceCriteria**:
  - **AC-1**: 本地 Tier-A gate smoke 命令明确且 exit 0（`python 04_Workflows/_wave7_regression_gate.py --tier A --pretty`）
  - **AC-2**: `routing/toolchain_smoke_matrix_v1.yaml` 含清楚 `TS-INT-TIER-A` 条目，标示 mandatory / CI 建议 / `blocks_pr_ci: false`
  - **AC-3**: `docs/ci-design-p6-int-gate-v1.md` 存在，描述 PR optional / nightly scheduled / release mandatory 三轨 CI 接入设计（含 pseudo-config · 技术落地 vs 治理解锁两步）
  - **AC-4**: 本票 FRAME + verification report 含 uplift 治理证据（72%→90%+ 理由 · 前提条件 · functional_gaps 清单）
  - **AC-5**: `workflow_line_status_2026-06-27.yaml` P6 行新增 `uplift_ready: true`，**不改** `complete` / Phase%
  - **AC-6**: contract + matrix unittest 仍 exit 0；无 `.github/workflows/*` diff

### Uplift 治理摘要（尚書省裁决用）

| 项 | 现状 (72%) | Uplift 目标 (90%+) | 本票交付 | 仍须治理批准 |
|----|------------|-------------------|----------|--------------|
| Contract SSOT | ✅ v1 §1–§8 | 维持 | cross-ref only | — |
| Tier-A CLI + unittest | ✅ 24/24 + live 112 passed | 维持 | verification report | — |
| Toolchain matrix | ✅ TS-INT-TIER-A | 语义加固 | matrix notes + optional Tier-B entry | — |
| CI design doc | ❌ | ✅ design-only | `ci-design-p6-int-gate-v1.md` | 尚書省批准后才能改 workflows |
| Nightly INT CI | gap | design-only | pseudo-config in ci-design | workflow 落地票 |
| PR Tier-A optional job | gap | design-only | eval-gate 或独立 job 方案 | workflow 落地票 |
| Phase% uplift | 72% | 90%+ | **不修改** | 治理 chat 单独裁决 |

**Uplift 理由（技术就绪）**:
- INT Tier-A gate 有 contract SSOT、executable CLI、21–24 contract tests、112-test live pass、consolidated verification report
- Smoke matrix 有 machine-readable mandatory 边界（local_mandatory · not PR CI）
- CI 接入路径已文档化，operator 可重复验证

**Uplift 前提（治理）**:
- 尚書省批准 `docs/ci-design-p6-int-gate-v1.md` 中 CI 方案（至少 nightly scheduled 或 PR optional 择一）
- CI 落地票（`.github/workflows/*`）单独开 FRAME 施工
- Phase% 重算仅在治理 chat 由授权方执行

### Wave Master 扩展

- wave_id: null
- group_id: G6
- lifecycle_phase: D
- phase_targets: P6
- ticket_class: doc/spec + governance prep
- evidence_tier: L-local
- parallel_ok: false
- non_claims:
  - no_ci_workflow_change
  - no_global_phase_pct_uplift
  - no_nightly_int_ci_live
  - no_pr_mandatory_tier_a

---

## STATE

- overall_status: done_with_gaps
- lifecycle_phase: D
- current_owner: orchestrator
- next_action: 尚書省 governance chat — CI design approval + Phase% 72%→90%+ uplift
- last_updated: 2026-06-27 · scribe
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

**Implementer**: implementation-worker · 2026-06-27  
**Status**: 施工完成 · 待 checker-reviewer

### Changed files

| Path | Summary |
|------|---------|
| `docs/ci-design-p6-int-gate-v1.md` | **Created** — three-track CI design (A PR optional / B nightly / C release); two-step governance; pseudo YAML; explicit non-claims |
| `docs/phase6-int-regression-verification-report-v1.md` | Added **CI readiness** section with gaps + verification commands |
| `docs/phase6-int-regression-gate-contract-v1.md` | §8.4 cross-ref to ci-design doc only |
| `docs/testing.md` | One-line ci-design pointer in header |
| `routing/toolchain_smoke_matrix_v1.yaml` | TS-INT-TIER-A notes reinforced; **TS-INT-TIER-B** added (`local_recommended` · optional) |

### Verification (implementer run)

| Command | Result |
|---------|--------|
| `python -m unittest tests.test_phase6_int_regression_gate_contract_v1 -v` | **24/24 OK** · exit 0 |
| `python -m unittest tests.test_phase6_toolchain_smoke_matrix_v1 -v` | **13/13 OK** · exit 0 (20 matrix entries incl. TS-INT-TIER-B) |
| `python 04_Workflows/_wave7_regression_gate.py --tier A --pretty` | **ok: true** · 14 modules · 112 passed · exit 0 |

### Skeleton / placeholder

- None — all deliverables are documentation / matrix entries.

### Blocked / deferred

- `.github/workflows/*` — Step 2 · governance approval required
- `workflow_line_status_2026-06-27.yaml` `uplift_ready` — Scribe scope (implementer did NOT touch)
- Phase% uplift — governance chat only

### Non-claims

- No live CI · no nightly INT scheduled · no PR mandatory Tier-A · no Phase% change

---

## C_REPORT

**Reviewer**: checker-reviewer · 2026-06-27  
**Verdict**: `accepted_with_gaps`

### AC summary

| AC | Criterion | Verdict | Evidence |
|----|-----------|---------|----------|
| AC-1 | Tier-A gate smoke exit 0 | **PASS** | Reviewer rerun: `ok: true` · 14 modules · 112 passed · exit 0 |
| AC-2 | Matrix TS-INT-TIER-A (+ Tier-B) | **PASS** | `TS-INT-TIER-A` mandatory/local semantics; `TS-INT-TIER-B` optional entry added |
| AC-3 | `docs/ci-design-p6-int-gate-v1.md` | **PASS** | Three-track design (PR optional / nightly / release); two-step governance; pseudo-config |
| AC-4 | Uplift governance evidence in FRAME + verification report | **PASS** | CI readiness section · 72%→90%+ rationale · functional_gaps table |
| AC-5 | `workflow_line_status` `uplift_ready: true` | **PENDING → Scribe** | Implementer correctly deferred YAML uplift fields to Scribe scope |
| AC-6 | Contract + matrix unittest green; no workflows diff | **PASS** | 24/24 + 13/13 OK; no `.github/workflows/*` diff |

### Gaps (non-blocking for technical prep)

- Nightly INT gate CI not scheduled (design-only)
- Tier-B heavier integration optional, not mandatory
- Governance CI design approval pending
- CI workflow landing pending (Step 2 ticket)
- Phase% uplift awaits separate governance chat

### Reviewer rerun

| Command | Result |
|---------|--------|
| `python -m unittest tests.test_phase6_int_regression_gate_contract_v1 -v` | 24/24 OK · exit 0 |
| `python -m unittest tests.test_phase6_toolchain_smoke_matrix_v1 -v` | 13/13 OK · exit 0 |
| `python 04_Workflows/_wave7_regression_gate.py --tier A --pretty` | ok: true · 112 passed · exit 0 |

---

## D_REPORT

**Scribe**: 2026-06-27

### docs_updates

| Path | Action |
|------|--------|
| `04_Workflows/workflow_line_status_2026-06-27.yaml` | P6 line: `uplift_ready: true` · `uplift_ticket` · `ci_design` artifact · expanded `functional_gaps` |
| `04_Workflows/tickets/WF-P6-INT-UPLIFT_state.md` | C_REPORT · D_REPORT · STATE → `done_with_gaps` / lifecycle D |
| `04_Workflows/00_Agent_Work_Progress.md` | Appended §2026-06-27 · WF-P6-INT-UPLIFT |

### progress_entry

- Section: `## 2026-06-27 · WF-P6-INT-UPLIFT · P6 INT gate uplift technical prep`
- Role chain: Orchestrator batch · Implementer → Reviewer → Scribe
- Conclusion: technical uplift prep complete; Phase% and CI workflow landing await governance

### Non-claims (scribe boundary)

- No `.github/workflows/*` change
- No `docs/WAVE_PROGRESS_DASHBOARD.md` Phase% change
- No Batch 1 governance YAML change
