# FP-G3-p75-trace-ssot — P7.5 Gate Trace SSOT State

> **Lane A · Group G3** · **Sub-block**: P75 gate trace SSOT（Phase 3 upstream trace schema）  
> **Authority doc**: `docs/p75-intake-gate-control-plane-trace-v1.md`（§A–F canonical · **不重定义字段**）  
> **Phase% SSOT**: `docs/WAVE_PROGRESS_DASHBOARD.md` · **2026-06-26**（本票 **不改** Phase%）  
> **Closure**: **none** — skeleton **ready** for downstream Wave 2/3/5 consumers

---

## META

| 欄位 | 值 |
|------|-----|
| **group_id** | G3 |
| **wave_id** | null（Foundation · 消费 W1-P75-TRACE 成果） |
| **phase_targets** | P3 · P7.5 |
| **ticket_class** | doc/spec + minimal build（join key 对齐） |
| **evidence_tier** | L-local |
| **lifecycle_phase** | C（Implementer 本轮回） |
| **sub_block_status** | **`ready`** — canonical schema · join keys · consumers · Non-Goals 已冻结 |
| **last_updated** | 2026-06-26 |

---

## Objective

将 **P7.5 上游 gate trace** 收敛为单一 SSOT，使 gate CLI · MP-SMOKE/MC-SMOKE · matrix §7.4.1 · ticket STATE · observer CLI **只引用** `docs/p75-intake-gate-control-plane-trace-v1.md` §Canonical trace schema — **禁止** ad-hoc 字段发明。

**成功判准（本子区块）**：canonical 表与代码/CLI/matrix 字段名一致；join key 在 smoke step detail 可 join；Non-Goals 书面化；B/C/D/O 可追溯。

---

## Canonical 字段表（索引 · 权威正文见 SSOT doc）

> 完整 §A–F 见 `docs/p75-intake-gate-control-plane-trace-v1.md`。下表为 **STATE 速查 + join 用法**。

### §A — Intake request identification

| Name | Join role | Producer |
|------|-----------|----------|
| `intake_decision_id` | **Primary** gate→notify→outbox join | `routing/intake_gate_layer_v1.evaluate_intake_gate` |
| `case_ref` | **Universal** P7.5→P8→P8.9→P9 join | gate layer · smoke summary · metrics |
| `case_dir` | Gate CLI input path（repo-relative） | gate layer |
| `task_type` | Routing key | gate layer |
| `schema_version` | `intake_gate_result_v1` | gate layer |
| `mode` | `preview` \| `run` | gate CLI / MP-SMOKE steps 1–2 |
| `created_at` | Gate evaluation timestamp | gate layer |

**Deprecated alias**: `intake_id` → **must use** `intake_decision_id`.

### §B — Gate decision fields

| Name | Alias | Semantics |
|------|-------|-----------|
| `decision` | `gate_decision` · `gate_status`（summary only） | `accept` \| `review_needed` \| `reject` |
| `reason_codes` | — | Ordered deduped policy + v2 codes |
| `p75_policy_decision` | — | `policy_deny` \| `policy_review` \| `policy_pass` |
| `deny_reason` | — | PM-D3 `reason_code` when deny |
| `gate_checks` | — | Rule rows |
| `ok` | — | Evaluation succeeded（≠ accept） |

### §C — Run / observability identification

| Name | Scope |
|------|-------|
| `run_at` | MP-SMOKE summary id（v1 **无** top-level `run_id`） |
| `step_id` | `gate_preview` \| `gate_run_notify` |
| `steps[].ok` | Per-step pass/fail |
| `outbox_record_path` | Durable gate JSON（run mode） |
| `notification_ok` | Notify emit result |
| `event_type` | Upstream: `intake.gate_decision` |

### §D — Cross-phase correlation（minimal）

| Name | Phases |
|------|--------|
| `case_ref` | P7.5 · P8 · P8.9 · P9 |
| `intake_decision_id` | P7.5 → P8.9 notify/consumer |
| `tracking_status` | P8.9 ack read model |
| `notifications_*_ack_count` | P8 · P8.9 metrics |
| `backlog_status` | P8 operator |

### §E — Deny-path（cross-ref deny MVP）

`multi_case_smoke_run.cases[].failed_steps` · `gate_decision`（MC 摘要 · **非** `gate_status`）

### §F — G-1–G-5 upstream observability only

`resume_eligibility` · `resume_blocked_reason` · `checkpoint_load_error` · `case_allowlist_block` — **Wave 2 runtime owner** · **不得**作为 gate upstream 完成证明。

---

## Join key 用法

```text
intake_decision_id  ──► outbox gate record
                    ──► notify envelope checkpoint_id slot
                    ──► notification artifacts.intake_decision_id
                    ──► MP-SMOKE steps[gate_*].detail.intake_decision_id

case_ref            ──► MP-SMOKE / MC-SMOKE summary
                    ──► export_std_case_metrics_v1
                    ──► operator backlog
                    ──► verification bundle paths

run_at + case_ref    ──► multi_phase_smoke_run.json observability id（无 run_id 键时）
```

### MP-SMOKE step 1–2 detail（C-phase 对齐后）

| Step | Required detail keys |
|------|---------------------|
| `gate_preview` | `case_ref` · `intake_decision_id` · `decision` · `gate_decision` · `mode=preview` · `reason_codes` |
| `gate_run_notify` | 同上 + `mode=run` · `outbox_record_path`（artifact_paths）· `event_type=intake.gate_decision` · `notification_ok` |

### MC-SMOKE per-case summary

| Key | Source |
|-----|--------|
| `case_ref` | case entry |
| `gate_decision` | `steps[gate_run_notify].detail.decision`（canonical alias） |
| `failed_steps` | failed step_id list |

---

## 必须只引用本 SSOT 的消费者

| Consumer | 引用方式 | 禁止 |
|----------|----------|------|
| `scripts/run_intake_gate_cli.py` | stdout JSON = gate layer shape | 发明 `intake_id` 主键 |
| `scripts/run_multi_phase_smoke_v1.py` | step detail 字段名 §C | 新 top-level `run_id` |
| `scripts/run_multi_case_smoke_v1.py` | `gate_decision` 摘要 | top-level `gate_status`（v1 deferred） |
| `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` §7.4.1 | CP-T1–T4 rows | G-1–G-5 runtime 证明 |
| Ticket STATE `observability.trace_fields` | 子集自 §A–D | 自造字段 |
| `W5-T3` evidence observer | read-only rollup | 重写 deny enum |
| Wave 2 `W2-P7-matrix-G1-G5-resume-loop-v1` | §F names only | gate step 1–2 扩展 |
| Matrix / MP-METRICS / inspector | join on `case_ref` · ack counts | prod SLA keys |

---

## Non-Goals（本子区块不支援）

| Item | Reason |
|------|--------|
| Top-level `run_id` in v1 runners | SSOT §Non-goals · use `run_at` + `case_ref` |
| `intake_id` as canonical | Deprecated · use `intake_decision_id` |
| MC-SMOKE `gate_status` top-level key | Deferred · use `gate_decision` |
| G-1–G-5 resume-loop **runtime** proof | Wave 2 · §F observability names only |
| Staging POST / prod notify SLA | Out of P7.5 upstream scope |
| P8.5 browser session ids | Correlate by `case_ref` only |
| P9 payment fields in gate SSOT | Separate P9 contracts |
| Phase% 上调 · closure 宣稱 | Governance 独占 |

---

## B / C / D / O 方案

| Phase | 产出 | 本轮回 |
|-------|------|--------|
| **B** Spec | `docs/p75-intake-gate-control-plane-trace-v1.md` §A–F（W1-P75-TRACE · **已 landed**） | ✅ 消费 · 不重写 schema |
| **B** Spec | 本 STATE · join key 表 · consumer 表 | ✅ 本文件 |
| **C** Code | `run_multi_phase_smoke_v1.py` — gate step detail join keys | ✅ 本轮回 |
| **C** Code | `run_multi_case_smoke_v1.py` — per-case `gate_decision` | ✅ 本轮回 |
| **D** Verify | `python -m unittest tests.test_multi_phase_smoke_v1 tests.test_multi_case_smoke_v1 -v` | ✅ 本轮回 |
| **D** Verify | `rg "intake_decision_id\|gate_decision" scripts/run_multi_phase_smoke_v1.py` | ✅ spot-check |
| **O** Observe | Progress append · matrix §7.4.1 cross-ref 已存在 | Scribe 可选 append |

---

## B_REPORT（Implementer · 2026-06-26）

- **changed_files**:
  - `04_Workflows/tickets/FP-G3-p75-trace-ssot_state.md`（新建）
  - `scripts/run_multi_phase_smoke_v1.py`（gate step detail join keys）
  - `scripts/run_multi_case_smoke_v1.py`（per-case `gate_decision`）
- **verification**:
  - `python -m unittest tests.test_multi_phase_smoke_v1 tests.test_multi_case_smoke_v1 -v`
- **behavior_notes**: MP-SMOKE step detail 现含 `intake_decision_id` · `case_ref` · `decision`/`gate_decision` · `event_type`；MC-SMOKE 用 `gate_decision` 非 deferred `gate_status`。
- **deferred_items**: G-1–G-5 runtime（Wave 2）· Langfuse/PG（FP-G3-T3）

---

## STATE

```yaml
overall_status: implementer_done_pending_review
lifecycle_phase: C
current_owner: implementer
sub_block_readiness:
  p75_gate_trace_ssot: ready  # ~98% — schema + join keys + consumers; runtime G-1–G-5 deferred
next_action: Reviewer 对照 SSOT doc + unittest；Scribe 可选 Progress append
last_updated: 2026-06-26
phase_percent_modified: false
closure_claimed: false
```

---

*FP-G3-p75-trace-ssot · Lane A Implementer · 2026-06-26 · 不改 Dashboard Phase%*
