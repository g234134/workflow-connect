# FP-G3-G1G5-resume-mvp — P7 Resume-Loop G-1–G-5 Minimal Runtime MVP



> **Lane A · Group G3** · Groundwork Technical Closer · **MVP runtime only**  

> **Spec SSOT**: `docs/p7-resume-loop-g1-g5-spec-v1.md` · `04_Workflows/testing/p7-resume-loop-g1-g5-matrix-v1.yaml`  

> **Gate trace SSOT**（分轨）: `docs/p75-intake-gate-control-plane-trace-v1.md` §F upstream-only  

> **Phase%**: 不改 · **non-claim**: 非 full fleet · 非 prod gate · 非 GA-remote



---



## FRAME



- **Goal**: 基于既有 matrix/spec，提供 **单 scenario resume runtime CLI**，证明 G-1 路径在 orchestrator 地基上可跑一次并产出 trace 字段；G-2–G-5 有 spot CLI 或明确 Non-Goals。

- **Scope**:

  - `scripts/run_p7_resume_loop_mvp_v1.py` — `--scenario G-1`…`G-5` · isolated temp outbox · structured `dict` 输出

  - `tests/test_p7_resume_loop_mvp_v1.py` — G-1 primary + G-4 spot unittest

  - 本 STATE · matrix `gate_trace_status=active` cross-ref W1-P75-TRACE

- **NonScope**:

  - 全 G-* fleet dedicated orchestrator unittest · staging · required CI · MP-SMOKE 七步扩展

  - 不宣稱 G-1–G-5 closed · 不修改 orchestrator core 逻辑 · 不改 Dashboard Phase%

- **AcceptanceCriteria**:

  - AC-1：**G-1 MVP 必须跑通** — CLI `--scenario G-1` → `ok=true` · `trace_fields.resume_eligibility=stale_checkpoint` · `final_status=stale_checkpoint`

  - AC-2：**输入/输出契约清晰** — CLI 接受 `--scenario` · 返回 `{ ok, scenario, trace_fields, resume_result, spec_ref, matrix_ref }`

  - AC-3：**至少一条运行证据** — L-local CLI run + unittest `tests/test_p7_resume_loop_mvp_v1.py` green

  - AC-4：**G-2–G-5 范围诚实** — CLI 支持全部五 scenario；MVP 关票范围 = G-1 full + G-4 spot unittest；G-2/G-3/G-5 = spot CLI only（无 dedicated unittest · 非 blocking）

  - AC-5：**Non-claims** — 非 prod gate · 非 full fleet · 非 Phase closure · gate trace SSOT 分轨（§F upstream-only）



---



## STATE



- overall_status: implementer_done_pending_review

- implementation_status: mvp_complete · verify_evidence_landed

- lifecycle_phase: D

- current_owner: reviewer

- next_action: Reviewer 纸面 AC-1–AC-5 勾选；C_REPORT accepted 后 Scribe 收口

- last_updated: 2026-06-27 · Groundwork Technical Closer

- phase_percent_modified: false

- closure_claimed: false

- status_by_role:

  - orchestrator: planned

  - implementer: done

  - reviewer: pending

  - scribe: pending



---



## B_REPORT



- **changed_files**:

  - `scripts/run_p7_resume_loop_mvp_v1.py`（新建 · MVP CLI）

  - `tests/test_p7_resume_loop_mvp_v1.py`（新建 · G-1 + G-4 unittest）

  - `04_Workflows/tickets/FP-G3-G1G5-resume-mvp_state.md`（本文件 · AC + D/O 补全）

  - `04_Workflows/testing/p7-resume-loop-g1-g5-matrix-v1.yaml`（`gate_trace_status: active`）

  - `scripts/verify_g_matrix.py`（accept `active` gate trace status）

- **MVP 形状**:

  - **输入**: `--scenario G-1`（默认）· optional `--outbox-root` · `--format json|text`

  - **输出**: `{ ok, scenario, trace_fields, resume_result, spec_ref, matrix_ref, isolated_outbox, outbox_root }`

  - **G-1（primary）**: synthetic expired CP-A → `validate_resume_eligibility` → `stale_checkpoint`

  - **G-2/G-3（spot CLI）**: on-disk status `revise_needed` / `on_hold` → blocked + `resume_blocked_reason`

  - **G-4（spot unittest）**: missing checkpoint path → `checkpoint_load_error`

  - **G-5（spot CLI）**: non-allowlisted `case_ref` → `case_allowlist_block` early block

- **scenario coverage（MVP 关票范围）**:



| Scenario | MVP tier | Evidence |

|----------|----------|----------|

| G-1 stale_checkpoint | **required full** | CLI + unittest |

| G-2 revise_needed | spot CLI only | Finisher L-local run · no dedicated unittest |

| G-3 on_hold | spot CLI only | Finisher L-local run · no dedicated unittest |

| G-4 checkpoint_load_error | **spot unittest** | CLI + unittest |

| G-5 case_allowlist_block | spot CLI only | Finisher L-local run · no dedicated unittest |



- **verification**:

  ```bash

  python scripts/run_p7_resume_loop_mvp_v1.py --scenario G-1 --format json

  python scripts/run_p7_resume_loop_mvp_v1.py --scenario G-4 --format json

  python scripts/verify_g_matrix.py

  python -m unittest tests.test_p7_resume_loop_mvp_v1 tests.test_p7_resume_loop_g_matrix_v1 -v

  ```

- **evidence_tier**: L-local · MVP only



---



## C_REPORT



- conclusion: pending

- reviewer_date: —

- verdict: pending

- blocking_issues: —

- checks_summary: Implementer 自檢 AC-1 G-1 full · AC-2 I/O · AC-3 unittest · AC-4 G-2–G-5 spot/non-goals · AC-5 non-claims；待 Reviewer 独立确认

- risk_level: —

- suggestions: —



---



## D_REPORT



- scribe_date: —

- finisher_verify_date: 2026-06-27 · Groundwork Technical Closer

- verdict_echo: pending Reviewer

- test_results:

  - G-1 CLI `ok=true` · `resume_eligibility=stale_checkpoint` · `final_status=stale_checkpoint`

  - G-4 CLI `ok=true` · `checkpoint_load_error` present · `final_status=blocked`

  - G-2 spot: `resume_blocked_reason=revise_needed` · `final_status=blocked`

  - G-3 spot: `resume_blocked_reason=on_hold` · `final_status=blocked`

  - G-5 spot: `case_allowlist_block=true` · `final_status=blocked`

  - `verify_g_matrix.py` → 5 entries OK · matrix unittest 3/3 OK · MVP unittest 2/2 OK

- verify_commands:

  ```bash

  python scripts/run_p7_resume_loop_mvp_v1.py --scenario G-1 --format json

  python scripts/run_p7_resume_loop_mvp_v1.py --scenario G-4 --format json

  python scripts/verify_g_matrix.py

  python -m unittest tests.test_p7_resume_loop_mvp_v1 tests.test_p7_resume_loop_g_matrix_v1 -v

  ```

- evidence_tier: L-local

- known_boundaries:

  - G-2/G-3/G-5 无 dedicated orchestrator unittest（Wave 2 `W2-P7-matrix-G1-G5-resume-loop-v1`）

  - isolated temp outbox — 不污染 repo `outbox/`

  - gate upstream trace（W1-P75-TRACE）与 resume runtime 分轨

- docs_updates: none（spec/matrix 已存在）

- non_claims_echo: **MVP G-1 primary closure only** · **G-2–G-5 spot CLI ≠ fleet closed** · **非 prod gate** · **非 Phase%** · **非 GA-remote CI**

- progress_entry: Groundwork Finisher A 2026-06-26 · Technical Closer 2026-06-27 evidence + unittest

- followup_suggestions: Wave 2 dedicated orchestrator resume unittests per G-* row



---



## O_OBSERVE



| 观测点 | 命令 / 路径 | 期望 trace 字段 | 2026-06-27 实测 |

|--------|-------------|-----------------|-----------------|

| G-1 primary | `run_p7_resume_loop_mvp_v1.py --scenario G-1` | `resume_eligibility=stale_checkpoint` | `ok=true` · `final_status=stale_checkpoint` · message含 `expired` |

| G-4 spot | `--scenario G-4` | `checkpoint_load_error` | `ok=true` · `final_status=blocked` · load error message present |

| G-2 spot | `--scenario G-2` | `resume_blocked_reason=revise_needed` | `ok=true` · `final_status=blocked` |

| G-3 spot | `--scenario G-3` | `resume_blocked_reason=on_hold` | `ok=true` · `final_status=blocked` |

| G-5 spot | `--scenario G-5` | `case_allowlist_block` | `ok=true` · `case_allowlist_block=true` |

| Matrix schema | `verify_g_matrix.py` | 5 gap rows · `gate_trace_status=active` | `entries_checked=5` · gap_ids G-1…G-5 |

| Spec cross-ref | output `spec_ref` / `matrix_ref` | SSOT paths | `docs/p7-resume-loop-g1-g5-spec-v1.md` · matrix YAML |

| Gate trace 分轨 | `p75-intake-gate-control-plane-trace-v1.md` §F | upstream-only names | resume fields **not** gate proof |



### Reviewer AC checklist (paper audit)



| AC | Evidence location | Finisher status |

|----|-------------------|-----------------|

| AC-1 G-1 full | D_REPORT G-1 run · `tests/test_p7_resume_loop_mvp_v1.py` | **ready** |

| AC-2 I/O | `scripts/run_p7_resume_loop_mvp_v1.py` argparse + return dict | **ready** |

| AC-3 evidence | verify_commands · unittest 2/2 + matrix 3/3 | **ready** |

| AC-4 G-2–G-5 | B_REPORT scenario table · O_OBSERVE spot rows | **ready** — honest non-goals for unittest fleet |

| AC-5 non-claims | FRAME NonScope · D_REPORT non_claims_echo | **ready** |



---



*FP-G3-G1G5-resume-mvp · Groundwork Technical Closer · 2026-06-27*

