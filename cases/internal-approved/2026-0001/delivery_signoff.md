# Delivery Signoff · `2026-0001`

> **Template (Wave 2 P4)** — Stage D signoff #4 per `docs/C2-P2_RUNBOOK.md` §19.  
> **Maintainer**: Scribe / Product PM (update checklist wording; do not change bundle paths without Orchestrator).

| Field | Value |
|-------|-------|
| case_id | `2026-0001` |
| client_ref | `internal-approved` |
| product_sku | `CLEAN-BASIC` |
| job_id | `case-2026-0001` |
| lead_approval | `approved by user-authorized-lead` |
| delivered_at | `2026-07-22T13:15:35Z` |

## Stage D checklist (C2-P2 §19.1)

- [ ] Deliverables match bundle (`cleaned/` + `reports/` + `delivery_signoff.md`)
- [ ] PII redacted per agreement
- [ ] Customer informed: non-SLA, manual review required
- [ ] No absolute paths or secrets in deliverables
- [ ] Known limits documented in **Exceptions / notes** below

## Cleaning summary

<!-- Auto-filled by `scripts/build_case_delivery_bundle.py` when signoff is created; edit freely. -->

| Metric | Value |
|--------|-------|
| intake rows | 7 |
| accepted rows | 6 |
| rejected rows | 1 |
| qa_status | `pass_with_warnings` |

### Rules applied

<!-- Manual or auto-filled from report.json cleaning_rules_applied -->

- `trim_text_fields`: trim text fields
- `dedup_by_primary_key`: dedup by primary key
- `drop_missing_primary_key`: drop missing primary key
- `parse_numeric`: parse numeric
- `flag_out_of_range`: flag out of range

## Eligibility summary

| Field | Value |
|-------|-------|
| status | `review_needed` |
| checked_at | `2026-07-22T13:08:00.130407+00:00` |
| reasons | rows<100; size<1024 |

## Signoff

| Field | Value |
|-------|-------|
| reviewer | `user-authorized-lead` |
| signer (Lead) | `user-authorized-lead` |
| signed_at | `2026-07-22T13:15:35Z` |
| bundle_built_at | `2026-07-22T13:15:35Z` |

## Exceptions / notes

<!-- Manual: waivers, customer caveats, risk remarks (C2-P2 §19). -->

- Non-SLA manual pipeline; external delivery requires Lead approval.
