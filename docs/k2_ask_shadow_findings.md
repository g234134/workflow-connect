# K-2 ↔ ask shadow findings (Wave 3 / Chat D)

> Dev/test artifact from `tests/test_k2_ask_shadow.py`. K-2 is **not** enabled on `/api/ask`.  
> **Extended baseline (Chat A)**: see [`k2_behavior_profile.md`](k2_behavior_profile.md) for scenario matrix, `compare_shadow_profiles`, and governance boundaries.

## Shadow scheme

| Piece | Location |
|-------|----------|
| Runner | `core/k2_ask_shadow.run_shadow_pair` |
| Compare fields | `SHADOW_COMPARE_FIELDS` in `core/k2_ask_shadow.py` |
| Tests | `tests/test_k2_ask_shadow.py` (mocks health/RAG; no API) |
| Merge hook draft | `k2_result_to_ask_response_envelope`, `ask_response_envelope` |

Flow: same `task_input` → `run_ask_flow` (legacy, `ibridge_v0=False`) + `run_k2_flow` → normalized summaries → field diff report.

## Observed differences (mocked e2e, 2026-05-23)

Both pipelines complete without crash (`ask_raw_ok=True`, `k2_raw_ok=True`). Compared fields rarely all match (`match_ok=False`).

| Field | ask (legacy) | K-2 |
|-------|----------------|-----|
| `ok` | `True` | `True` |
| `message_preview` | `ask pipeline completed` | `agent succeeded` |
| `answer_preview` | `shadow-mock-answer` (RAG mock) | `agent succeeded` (agent stub) |
| `context_entry_mode` | `None` | `k2_pipeline` |
| `has_eval_metadata` | `False` | `True` |
| `executed_node_count` | `3` (health/retrieve/answer) | `0` (agent graph, not LG node list) |
| `handoff_count` | `0` in simple case; `2` in longer run | `2` when M-line record populated |
| `retry_count` | `0` legacy; K-2 skill-retry via `skill_results.retrieve.retry_count` | `≥1` on simulated skill failure |

Notes:

1. **Context mode** — K-2 uses `k2_pipeline`; legacy ask does not set `context_entry_mode` at entry (H-line bypass).
2. **Eval metadata** — K-2 always has `eval_metadata` / `eval_gate` after `finalize_eval`.
3. **Answer source** — Different producers (RAG mock vs agent `final_result`); merge hook must not assume identical answer strings.
4. **Observability shape** — Ask reports `executed_nodes`; K-2 reports handoff/retry on M-line + `eval_metadata` (not the same field names).
5. **Skill retry** — `simulate_skill_failure=True` still yields `k2_raw_ok=True` with retrieve `retry_count≥1` while ask path unchanged.

## Merge hook (draft)

```python
k2_result_to_ask_response_envelope(k2_result, query=..., top_k=..., include_eval=True) -> dict
ask_response_envelope(ask_result, eval_metadata=...) -> dict
```

Target: top-level ask keys (`mode`, `ok`, `message`, `answer`, `errors`, `executed_nodes`) plus optional `k2_eval_metadata` / `k2_metrics_record` overlay — not wired to production.

## P3 fixture representative set (2026-05-25)

> **Ticket**: `HQ-GOV-K2-P1-SHADOW-20260525` gate P3 · **not** prod decision samples.

| Check | Result |
|-------|--------|
| `python -m unittest tests.test_k2_ask_shadow -v` | **13 tests OK** |

| Scenario | `merge_safe` | `unacceptable_diffs` |
|----------|--------------|----------------------|
| `retrieve_timeout` | False | `['error_type']` |
| `simple_happy` | True | `[]` |
| `summary_probe` | True | `[]` |

During Phase 1 prod shadow, P3 reporting should switch to **real shadow export weekly** (`compare_shadow_profiles` + `eval_ci_check`), not this mocked matrix alone.

## Next steps

1. Extend shadow cases with `ibridge_v0=True` for apples-to-apples H-line on ask side.
2. Define merge policy: when to prefer K-2 eval vs ask node outputs.
3. Add governance sign-off on `k2_pipeline` → `ask_pipeline` context mode switch.
4. Gate production merge on shadow diff thresholds per field (not byte-identical answers).
