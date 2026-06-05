# Retention Policy

## Default
- Normal successful runs: keep `workflow_summary.json` and `final_report.md`
- Failed or abnormal runs: keep full `execution_trace.json`
- `artifacts/` only keep important outputs
- Sensitive content must not be committed into git

## Review Window
- Review raw traces after 30 to 90 days
- Archive or delete low-value large traces
