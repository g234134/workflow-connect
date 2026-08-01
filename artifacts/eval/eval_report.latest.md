# Eval gate report (Wave B bootstrap)

> Generated: `2026-06-07T07:49:23Z`

## Executive summary

- **Samples (N)**: 3
- **Source files**: `eval_export_sample.jsonl`
- **needs_review**: 2 (66.7%)
- **Confidence**: high
- **Suggested max-needs-review-ratio range**: 0.72–0.87
- **Suggested fail-on-tags**: infra_risk

### Index context

> Observability only — not eval_gate rules and not prod selector hook.

| kb_index_status | Samples | needs_review | Ratio |
|-----------------|---------|--------------|-------|
| `ready` | 1 | 1 | 100.0% |
| `not_set` | 2 | 1 | 50.0% |

## Tag histogram (top)

| Tag | Count |
|-----|-------|
| `high_retry` | 1 |
| `infra_risk` | 1 |

## Reproduce

```bash
python -m observability.eval_report "tests\fixtures\eval\eval_export_sample.jsonl" --out-dir artifacts/eval
```

## Full text stats

```text
ok: True
message: analyzed 3 sample(s); needs_review 66.67%

=== Overall ===
N=3  needs_review=2  ratio=66.67%
pass=1  rows_with_tags=2

=== Tags (row-level appearances) ===
  high_retry: 1 (33.33% of N)
  infra_risk: 1 (33.33% of N)

=== CI: max-needs-review-ratio ===
  suggested range: 0.72 – 0.87
  observed: 66.67%
  note: Observed needs_review ratio: 66.67% (2/3).
  note: Suggest --max-needs-review-ratio in [0.72, 0.87]: ceiling above typical batch with room for small regressions; tighten toward the low end once staging baseline stabilizes.
  note: Observed infra_risk in 1/3 rows (33.33%) — any occurrence should fail CI.

=== CI: fail-on-tags ===
  infra_risk: fail — Infrastructure failures (timeout, context_overflow) should block CI even when overall needs_review ratio is within range.
  observability_gap: optional_fail — Low frequency in current sample; enable --fail-on-tags observability_gap on nightly/production paths when baseline is near zero.

=== CI: monitor / warn ===
  high_retry: monitor — high_retry seen 1 time(s) (33.33%); ratio gate usually sufficient — fail-on-tags only if policy requires.

=== Suggested CLI (provisional) ===
  --max-needs-review-ratio 0.87 --fail-on-tags infra_risk
```
