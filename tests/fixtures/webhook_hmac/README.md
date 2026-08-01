# Webhook HMAC receiver fixtures (P7 · §4.6.5.2)

Test-only signed samples for contract tests and staging receiver verification.

## Secret (fixture-only · non-prod)

All fixtures use the shared test secret:

`p7-staging-fixture-hmac-secret-v1`

**Do not reuse** for prod or customer staging slots.

## Files

| Fixture | Scenario |
|---------|----------|
| `signed_delivery_bundle_ready.json` + `.headers.json` | Valid signed POST |
| `invalid_signature.json` + `.headers.json` | Wrong `sha256=` digest |
| `expired_timestamp.json` + `.headers.json` | Timestamp outside ±300s window |
| `event_id_mismatch.json` + `.headers.json` | Header `event_id` ≠ body |
| `replay_same_event_id.json` + `.headers.json` | Second delivery of same `event_id` (stateful replay test uses cache) |

## Regenerate headers

```bash
python tools/generate_webhook_hmac_fixtures_v1.py
```

## Contract tests

```bash
python -m unittest tests.test_webhook_hmac_receiver_v1 -v
```
