# Toolchain Health Dashboard

> Schema: `toolchain_health_v1` · Generated: `2026-06-11T01:04:32Z` · Score: **95**/100 (heuristic, not SLA)

- **Overall ok**: `True`
- **Gate class**: `optional` · **blocks_mainline**: `False`
- **Sections populated**: 5/5
- **Mode**: `dry-run (read-only)`

## agent_ci

- status: `ok` · ok: `True`
- scope: `all` · tabular_ok: `True`
- source: `outbox/agent_ci/20260610T010418Z_ci_summary.json`

## metrics_summary

- status: `ok` · runs: `15`
- error_rate: `0.0` · cp_a: `0.8`

## monthly_report_head

- Generated from `metrics_summary.json` · source snapshot: `2026-06-10T01:44:10Z`
- Schema: `agent_lines_monthly_report_v1` · **offline only** — no external monitoring
- | Metric | All lines | Tabular | Non-tabular preview |
- | Total runs | 13 | 13 | 0 |
- | Successful | 13 | 13 | 0 |
- | Failed | 0 | 0 | 0 |
- | Error rate | 0.0% | 0.0% | 0.0% |
- | CP-A trigger rate | 92.3% | 92.3% | — |
- | CP-B trigger rate | 76.9% | 76.9% | — |
- | Non-tabular previews | 0 | — | 0 |
- | Tier | Runs | Error rate | CP-A rate | CP-B rate |
- | `stable` | 8 | 0.0% | 100.0% | 100.0% |

## fixture_maturity_tiers

| tier | metrics_runs | ci_passed/ci_total |
|------|--------------|-------------------|
| stable | 8 | 0/0 |
| controlled_experimental | 4 | 0/0 |
| unknown | 1 | 0/0 |

## catalog_health

- tabular tools: `11` · non-tabular: `4`
- revisions: tabular=`2026-06-10` · nt=`2026-06-10`
- stale_revision: `False`

## wf_status_summary (optional)

- status: `missing` · samples: `None` · needs_review_ratio: `None`
