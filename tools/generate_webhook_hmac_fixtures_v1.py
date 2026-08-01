#!/usr/bin/env python3
"""Generate webhook_hmac fixture bodies + header sidecars (non-prod test secret only)."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery.webhook_hmac_receiver_v1 import sign_gov_webhook_headers

FIXTURE_SECRET = "p7-staging-fixture-hmac-secret-v1"
FIXTURE_DIR = _REPO_ROOT / "tests" / "fixtures" / "webhook_hmac"


def _write_pair(name: str, body: dict, headers: dict) -> None:
    body_path = FIXTURE_DIR / f"{name}.json"
    headers_path = FIXTURE_DIR / f"{name}.headers.json"
    body_bytes = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    body_path.write_bytes(body_bytes)
    headers_path.write_text(json.dumps(headers, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    signed_body = {
        "schema_version": "notification_event_v1",
        "event_id": "evt-fixture-signed-001",
        "event_type": "delivery.bundle_ready",
        "case_ref": "demo_phase",
        "timestamp": "2026-06-24T00:00:00Z",
    }
    signed_bytes = json.dumps(signed_body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    signed_headers = sign_gov_webhook_headers(
        signed_bytes,
        shared_secret=FIXTURE_SECRET,
        event_id=signed_body["event_id"],
        timestamp=1750000000,
    )
    _write_pair("signed_delivery_bundle_ready", signed_body, signed_headers)

    invalid_body = dict(signed_body)
    invalid_body["event_id"] = "evt-fixture-invalid-sig-001"
    invalid_bytes = json.dumps(invalid_body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    invalid_headers = sign_gov_webhook_headers(
        invalid_bytes,
        shared_secret=FIXTURE_SECRET,
        event_id=invalid_body["event_id"],
        timestamp=1750000000,
    )
    invalid_headers["X-Gov-Signature-256"] = "sha256=deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
    _write_pair("invalid_signature", invalid_body, invalid_headers)

    expired_body = {
        "schema_version": "notification_event_v1",
        "event_id": "evt-fixture-expired-001",
        "event_type": "run.completed",
        "case_ref": "demo_phase",
        "timestamp": "2026-06-24T00:00:00Z",
    }
    expired_bytes = json.dumps(expired_body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    expired_headers = sign_gov_webhook_headers(
        expired_bytes,
        shared_secret=FIXTURE_SECRET,
        event_id=expired_body["event_id"],
        timestamp=1,
    )
    _write_pair("expired_timestamp", expired_body, expired_headers)

    mismatch_body = {
        "schema_version": "notification_event_v1",
        "event_id": "evt-fixture-body-id-001",
        "event_type": "run.completed",
        "case_ref": "demo_phase",
        "timestamp": "2026-06-24T00:00:00Z",
    }
    mismatch_bytes = json.dumps(mismatch_body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    mismatch_headers = sign_gov_webhook_headers(
        mismatch_bytes,
        shared_secret=FIXTURE_SECRET,
        event_id="evt-fixture-header-id-001",
        timestamp=int(time.time()),
    )
    _write_pair("event_id_mismatch", mismatch_body, mismatch_headers)

    replay_body = {
        "schema_version": "notification_event_v1",
        "event_id": "evt-fixture-replay-001",
        "event_type": "delivery.bundle_ready",
        "case_ref": "demo_phase",
        "timestamp": "2026-06-24T00:00:00Z",
    }
    replay_bytes = json.dumps(replay_body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    replay_headers = sign_gov_webhook_headers(
        replay_bytes,
        shared_secret=FIXTURE_SECRET,
        event_id=replay_body["event_id"],
        timestamp=int(time.time()),
    )
    _write_pair("replay_same_event_id", replay_body, replay_headers)

    print(f"[OK] wrote fixtures under {FIXTURE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
