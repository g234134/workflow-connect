# TICKET STATE · W2-P7-matrix-G1-G5-resume-loop-v1

> G-1–G-5 resume-loop **spec + trace contract** (spec-only · non-prod-gate).  
> Wave：Wave 2 · Chat 2 · P7

---

## FRAME

- **Title**: P7 matrix · G-1–G-5 resume-loop MVP spec + test matrix + trace contract
- **Goal**: 將 `standard-case-hitl-resume-notify-matrix.md` §9 G-1–G-5 缺口對齊 outbox/runner/trace 觀測契約；Reviewer 可不跑 staging 即審計 resume-loop 行為與觀測點。
- **Scope**:
  - 新建 `docs/p7-resume-loop-g1-g5-spec-v1.md`
  - 新建 `04_Workflows/testing/p7-resume-loop-g1-g5-matrix-v1.yaml`
  - 更新 `standard-case-hitl-resume-notify-matrix.md` §9 G-1–G-5 Observability 列
  - 新建 `scripts/verify_g_matrix.py` + `tests/test_p7_resume_loop_g_matrix_v1.py`
  - MAY：`WORKFLOW_INDEX.md` §1.45 一句索引
- **NonScope**:
  - 不新增 orchestrator/resume runtime code
  - 不做 full prod gate · 不跑 staging POST · 不升格 CI required
  - 不宣稱 G-1–G-5 closed · 不覆蓋 G-6–G-13
  - 不改 Dashboard Phase% · 不改 W-ORCH
- **AllowedPaths**:
  - `docs/p7-resume-loop-g1-g5-spec-v1.md`
  - `04_Workflows/testing/p7-resume-loop-g1-g5-matrix-v1.yaml`
  - `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md`（§9 增量）
  - `scripts/verify_g_matrix.py`
  - `tests/test_p7_resume_loop_g_matrix_v1.py`
  - `04_Workflows/WORKFLOW_INDEX.md`（§1.45 一句 · MAY）
  - 本票 `_state.md`
- **BlockedPaths**:
  - `scripts/run_agent_standard_case_experiment.py`（runtime 路徑）
  - `core/**` · `.github/workflows/**` · Dashboard Phase% · W-ORCH 程式
- **AcceptanceCriteria**:
  - AC-1–AC-5：G-1–G-5 各列觸發 · 預期 resume · trace_field · matrix R-11–R-15 cross-ref
  - AC-6：trace contract 分表 · W1-P75-TRACE / `p75-intake-gate-control-plane-trace-v1.md` **active**（原 W1-T5 占位已解除）
  - AC-7：test matrix ≥5 行 · 每行 verify_command
  - AC-8：non-claims 含 spec ≠ runtime impl ≠ prod gate
- **Observability**:
  - verify_commands:
    - `rg "G-1|G-2|G-3|G-4|G-5|stale_checkpoint|resume_eligibility|resume_blocked_reason" docs/p7-resume-loop-g1-g5-spec-v1.md 04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md`
    - `rg "W1-P75-TRACE|p75-intake-gate-control-plane-trace" docs/p7-resume-loop-g1-g5-spec-v1.md`
    - `python scripts/verify_g_matrix.py`
    - `python -m unittest tests.test_p7_resume_loop_g_matrix_v1 -v`

### Wave Master 擴展

- wave_id: W2
- group_id: G7
- lifecycle_phase: O
- phase_targets: [P7, P7.5]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- non_claims:
  - G-1–G-5 unittest/runtime 已落地
  - P7 Round-2 execute 已完成
  - resume-loop prod gate / required CI
  - MP-SMOKE 七步已覆蓋 resume-loop
  - 此票不等於 runtime prod gate

---

## STATE

- overall_status: done
- implementation_status: closed · C_accepted · AC6_trace_active · orch_closed
- lifecycle_phase: closed
- current_owner: orchestrator
- next_action: 无（本票收口）· Downstream = G-* resume-loop **runtime impl** 另票（非本票）
- last_updated: 2026-07-09 · Orchestrator（gap closure · TRACE active → done）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  2026-06-26 原 `done_with_gaps` 唯一可關缺口 = `pending_w1_t5`。
  W1-P75-TRACE-UPSTREAM-v1 已 done · spec §3.2 / YAML `gate_trace_status: active`。
  2026-07-09 重跑 verify_g_matrix + 3 unittest OK · INDEX §1.45 一句 ·
  升 `overall_status: done`。G-* runtime unittest 仍 planned impl（AC-8 · 非本票 gap）。

---

## B_REPORT

### Matrix spec 完成情況（Build · 2026-06-26）

| AC | 狀態 | 證據 |
|----|------|------|
| AC-1 G-1 stale_checkpoint | done | `docs/p7-resume-loop-g1-g5-spec-v1.md` §2 G-1 · matrix R-11 · YAML `G-1` entry |
| AC-2 G-2 revise_needed blocked | done | spec §2 G-2 · R-12 · `resume_blocked_reason=revise_needed` |
| AC-3 G-3 on_hold blocked | done | spec §2 G-3 · R-13 · CLI/integration 邊界明示 |
| AC-4 G-4 missing checkpoint | done | spec §2 G-4 · R-14 · `checkpoint_load_error` |
| AC-5 G-5 allowlist block | done | spec §2 G-5 · R-15 · `case_allowlist_block` |
| AC-6 W1-T5 / TRACE cross-ref | **done（2026-07-09）** | spec §3.2 **active** · YAML `gate_trace_ssot` · 雙向 xref TRACE doc |
| AC-7 test matrix ≥5 rows | done | spec §4 M-G1–M-G5 · YAML 5 entries |
| AC-8 non-claims | done | spec 首段 · YAML `non_claims` · STATE |

**changed_files**（2026-06-26）:
- `docs/p7-resume-loop-g1-g5-spec-v1.md`（新建）
- `04_Workflows/testing/p7-resume-loop-g1-g5-matrix-v1.yaml`（新建）
- `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md`（§9 Observability 列）
- `scripts/verify_g_matrix.py`（新建）
- `tests/test_p7_resume_loop_g_matrix_v1.py`（新建）

**changed_files**（2026-07-09 gap closure）:
- `docs/p7-resume-loop-g1-g5-spec-v1.md`（Changelog + References TRACE active）
- `04_Workflows/WORKFLOW_INDEX.md`（§1.45 一句）
- 本 state 檔

**skeleton / placeholder**: G-* dedicated orchestrator unittest 仍 `planned impl`（刻意 · AC-8）。**已解除**：`pending_w1_t5`。

---

## C_REPORT

| 項目 | 值 |
|------|-----|
| **Config / schema 路徑** | `04_Workflows/testing/p7-resume-loop-g1-g5-matrix-v1.yaml` |
| **型別** | YAML mapping · `schema_version: p7_resume_loop_g_matrix_v1` |
| **Spec 路徑** | `docs/p7-resume-loop-g1-g5-spec-v1.md` |
| **Runtime 影響** | 無（spec-only；未改 orchestrator） |

- **Scribe 收口摘要**（2026-06-26 · verdict: **accepted_with_gaps**）:
  - **spec-only** matrix 已完成；Known gap：`pending_w1_t5` · G-* runtime unittest planned。

- **Gap-closure Reviewer**（2026-07-09 · verdict: **accepted**）:
  - AC-1–AC-8 紙面 + L-local：`verify_g_matrix.py` → `ok=true` · `entries_checked=5`；unittest **3/3 OK**
  - AC-6：spec/YAML 無 `pending_w1_t5`；`gate_trace_status: active`；TRACE doc 雙向 xref 本票
  - INDEX §1.45 一句存在；AllowedPaths 內
  - **blocking 無** · risk=low
  - 殘餘非阻塞：G-* runtime impl 另票（AC-8 明示 · 不挡本票 done）

---

## D_REPORT

### verify_commands（2026-06-26 · implementer）

| 命令 | 結果 |
|------|------|
| `python scripts/verify_g_matrix.py` | **OK** — `ok=true`, `entries_checked=5` |
| `python -m unittest tests.test_p7_resume_loop_g_matrix_v1 -v` | **OK** — 3 tests passed |

### Gap-closure verify（2026-07-09）

| 命令 | 結果 |
|------|------|
| `python scripts/verify_g_matrix.py` | **OK** — `ok=true`, gap_ids G-1–G-5 |
| `python -m unittest tests.test_p7_resume_loop_g_matrix_v1 -v` | **OK** — 3/3 |
| `rg pending_w1_t5` on spec/YAML | **無命中**（僅歷史 STATE 敘事已改寫） |
| `rg W1-P75-TRACE\|p75-intake-gate-control-plane-trace` on spec | **命中** · status active |

**docs_updates**: INDEX §1.45 一句 · spec Changelog 2026-07-09  
**progress_entry**: 已 append Progress「W2-P7-matrix · gap closure · done」  
**followup_suggestions**: 開 G-1–G-5 **runtime unittest / resume-loop impl** 另票；W5-T3 observer 可消費 resume trace 欄位名

---

## O_REPORT

- **Scribe 收口**（2026-06-26）：`done_with_gaps` · pending W1-P75-TRACE
- **Orchestrator 關票**（2026-07-09）：TRACE active · AC-6 關 · `overall_status: done` · runtime impl **未開**（誠實）
