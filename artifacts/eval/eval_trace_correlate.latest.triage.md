# eval flagged triage

- **ok**: True
- **message**: correlated 2 eval row(s); trace_found=1
- **eval**: `tests/fixtures/eval/eval_export_sample.jsonl`
- **trace**: `tests/fixtures/trace/sample_traces.jsonl`
- **only_needs_review**: True
- **join priority**: trace_id > task_id > session_id

## eval line 1 · t-infra

- **gate_result**: `needs_review`
- **tags**: infra_risk
- **reasons**: error_type=timeout
- **kb_index_status**: `ready`
- **join**: `trace_id=tr-3`
- **trace events**: 2
- **event types**: trace_end×1, trace_start×1
- **trace_completeness**: 0.6
- **span**: 2026-05-23T10:01:30Z → 2026-05-23T10:02:00Z
- **why_flagged**: error_type=timeout

## eval line 2 · t-retry

- **gate_result**: `needs_review`
- **tags**: high_retry
- **reasons**: retry_count=2 >= 2
- **kb_index_status**: `unknown`
- **join**: —
- **trace**: not found (no trace events for join keys (trace_id=tr-2, task_id=t-retry))
- **why_flagged**: retry_count=2 >= 2
