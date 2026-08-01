# WC-PRE-06/07 · Non-blocking governance snapshot (L0)

> **Status**: L0 observability only — does **not** change PR gate pass/fail or branch protection.

## Purpose

This snapshot is the first governance landing step after WC-PRE-05 (smoke matrix runner) and WB-T4 (toolchain health dashboard). It aggregates:

- Smoke matrix metadata and simple coverage counts (`routing/toolchain_smoke_matrix_v1.yaml`)
- Per-component last smoke observation (CI-observed passes, external JSON, or `not_observed`)
- Toolchain health dashboard embed (`toolchain_health_v1`, dry-run read-only)
- Recent error summaries (failed smokes + degraded health sections)

It is **advisory**. Failures in the snapshot must not block merge.

## Generate locally

```bash
python scripts/generate_toolchain_governance_snapshot.py --write
# → output/toolchain/governance_snapshot.json
# → output/toolchain/governance_snapshot.md
```

Optional CI context (marks smokes known to have run in that workflow when the job succeeded):

```bash
python scripts/generate_toolchain_governance_snapshot.py --ci-context eval-gate-pr --write
python scripts/generate_toolchain_governance_snapshot.py \
  --ci-context core-agent-smoke-pr \
  --smoke-results-json smoke_ci_summary.json \
  --write
```

## CI usage

| Workflow | Step | Context | Gate impact |
|----------|------|---------|-------------|
| `eval-gate-ci.yml` | After eval gate checks, before artifact upload | `eval-gate-pr` | `continue-on-error: true` · `--non-blocking` |
| `core-agent-smoke.yml` | After smoke summary upload prep | `core-agent-smoke-pr` | same |

Artifacts:

- `output/toolchain/governance_snapshot.json`
- `output/toolchain/governance_snapshot.md`

CI logs print a short trailer:

```text
=== Toolchain governance snapshot (non-blocking · WC-PRE-06/07 L0) ===
...
=== end governance snapshot ===
```

## Schema

Top-level keys (`toolchain_governance_snapshot_v1`):

| Key | Description |
|-----|-------------|
| `ok` | Snapshot assembly succeeded (matrix loaded) |
| `non_blocking` | Always `true` for this deliverable |
| `coverage` | Tier / gate_class counts from smoke matrix |
| `components` | One row per matrix `smoke_id` with `last_result` |
| `toolchain_health_embed` | WB-T4 summary (`sections_populated`, score, degraded sections) |
| `recent_errors` | Truncated list for human triage |

## What this is not

- Not `OG-TOOLCHAIN-HEALTH` required check (WC-PRE-06 design approval still pending)
- Not mandatory smoke matrix execution in CI (WC-PRE-07)
- Not a replacement for `run_toolchain_health_dashboard.py` or `run_toolchain_smoke_matrix.py`

## References

- Design proposal: `docs/toolchain-observability-governance-upgrade-v1.md`
- Smoke matrix SSOT: `routing/toolchain_smoke_matrix_v1.yaml`
- Health dashboard: `docs/toolchain-health-dashboard-v1.md`
- Implementation: `scripts/generate_toolchain_governance_snapshot.py`
