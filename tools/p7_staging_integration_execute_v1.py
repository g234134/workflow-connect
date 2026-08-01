#!/usr/bin/env python3
"""P7 staging integration execute — S1–S4 smoke (WH-P7-NOTIF-staging-integration-execute-v1).

Runs first real-env (local staging slot) smoke per smoke-runbook-v1 B_REPORT §2–§5.
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery import notification_gateway_v1 as gw
from delivery import notification_webhook_adapter_v1 as webhook
from tools.p7_staging_env_bootstrap_v1 import (
    DEFAULT_SLOT_ROOT,
    load_runtime_env,
    provision_staging_slot,
    rollback_staging_post,
)
from tools.staging_webhook_receiver_v1 import StagingWebhookReceiver

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

# Local staging slot uses self-signed TLS; disable verification for this runner only.
ssl._create_default_https_context = ssl._create_unverified_context  # type: ignore[attr-defined]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _count_dlq_lines(dlq_path: Path) -> int:
    if not dlq_path.is_file():
        return 0
    return sum(1 for line in dlq_path.read_text(encoding="utf-8").splitlines() if line.strip())


def _run_inspect(subcommand: str, *, dlq_path: Path, tier: str = "staging") -> Dict[str, Any]:
    cmd = [
        sys.executable,
        str(_REPO_ROOT / "tools" / "inspect_notification_dlq_v1.py"),
        subcommand,
        "--tier",
        tier,
        "--dlq-path",
        str(dlq_path),
        "--json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(_REPO_ROOT))
    if proc.returncode != 0:
        return {"ok": False, "stderr": proc.stderr.strip(), "stdout": proc.stdout.strip()}
    try:
        return {"ok": True, "data": json.loads(proc.stdout)}
    except json.JSONDecodeError:
        return {"ok": True, "raw": proc.stdout.strip()}


def _apply_env(env: Dict[str, str]) -> None:
    for key, value in env.items():
        if value == "":
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def _emit_notification(suffix: str) -> tuple[Dict[str, Any], str]:
    event_id = f"evt-staging-{suffix}-{uuid.uuid4().hex[:8]}"
    event = gw.build_notification_event(
        "run.completed",
        case_ref="demo_phase",
    )
    event["event_id"] = event_id
    result = webhook.send_webhook_notification(event, case_ref="demo_phase")
    return result, event_id


def _base_staging_env(*, receiver: StagingWebhookReceiver, dlq_path: Path) -> Dict[str, str]:
    env = load_runtime_env()
    env["GOV_NOTIFICATION_WEBHOOK_TIER"] = "staging"
    env["GOV_NOTIFICATION_WEBHOOK_URL"] = receiver.base_url
    env["GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST"] = receiver.allowlist_entry
    env["GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED"] = "1"
    env["GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED"] = "1"
    env["GOV_NOTIFICATION_WEBHOOK_DLQ_PATH"] = str(dlq_path.relative_to(_REPO_ROOT)).replace("\\", "/")
    env["GOV_NOTIFICATION_WEBHOOK_DLQ_TIER"] = "staging"
    env["GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS"] = "1"
    env["GOV_NOTIFICATION_WEBHOOK_RETRY_BASE_DELAY_MS"] = "10"
    env["GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_DELAY_MS"] = "20"
    return env


def run_s1(*, receiver: StagingWebhookReceiver, dlq_path: Path) -> Dict[str, Any]:
    env = _base_staging_env(receiver=receiver, dlq_path=dlq_path)
    _apply_env(env)
    receiver.set_mode("ok")

    result_match, event_id_match = _emit_notification("s1-match")
    wr_match = result_match["webhook_result"]

    env_miss = dict(env)
    env_miss["GOV_NOTIFICATION_WEBHOOK_URL"] = "https://evil-not-in-allowlist.example/webhook"
    _apply_env(env_miss)
    result_miss, event_id_miss = _emit_notification("s1-miss")
    wr_miss = result_miss["webhook_result"]

    passed = (
        wr_match.get("dispatched") is True
        and wr_match.get("http_status") == 200
        and wr_miss.get("dispatched") is False
        and wr_miss.get("blocked_reason") == "blocked_by_url_tier_policy"
    )
    return {
        "phase": "S1",
        "go": passed,
        "event_ids": {"match": event_id_match, "miss": event_id_miss},
        "match": {
            "dispatched": wr_match.get("dispatched"),
            "http_status": wr_match.get("http_status"),
        },
        "miss": {
            "dispatched": wr_miss.get("dispatched"),
            "blocked_reason": wr_miss.get("blocked_reason"),
            "blocked_rule": wr_miss.get("blocked_rule"),
        },
        "receiver_calls": len(receiver.get_received()),
    }


def run_s2(*, receiver: StagingWebhookReceiver, dlq_path: Path) -> Dict[str, Any]:
    env = _base_staging_env(receiver=receiver, dlq_path=dlq_path)
    _apply_env(env)

    dlq_before = _count_dlq_lines(dlq_path)
    receiver.set_mode("ok")
    result_ok, event_id_ok = _emit_notification("s2-ok")
    dlq_after_ok = _count_dlq_lines(dlq_path)

    receiver.set_mode("always_503")
    result_fail, event_id_fail = _emit_notification("s2-503")
    wr_fail = result_fail["webhook_result"]
    dlq_after_fail = _count_dlq_lines(dlq_path)
    inspect_list = _run_inspect("list", dlq_path=dlq_path)
    inspect_stats = _run_inspect("stats", dlq_path=dlq_path)

    passed = (
        result_ok["webhook_result"].get("dispatched") is True
        and dlq_after_ok == dlq_before
        and wr_fail.get("retry_exhausted") is True
        and dlq_after_fail == dlq_before + 1
    )
    return {
        "phase": "S2",
        "go": passed,
        "event_ids": {"happy": event_id_ok, "fail_503": event_id_fail},
        "happy_path": {
            "dispatched": result_ok["webhook_result"].get("dispatched"),
            "dlq_delta": dlq_after_ok - dlq_before,
        },
        "fail_path": {
            "retry_exhausted": wr_fail.get("retry_exhausted"),
            "attempt_count": wr_fail.get("attempt_count"),
            "dlq_delta": dlq_after_fail - dlq_before,
        },
        "inspect_list": inspect_list,
        "inspect_stats": inspect_stats,
    }


def run_s3(*, receiver: StagingWebhookReceiver, dlq_path: Path) -> Dict[str, Any]:
    env = _base_staging_env(receiver=receiver, dlq_path=dlq_path)
    _apply_env(env)
    receiver.set_mode("ok")

    result_signed, event_id_signed = _emit_notification("s3-signed")
    wr_signed = result_signed["webhook_result"]
    received = receiver.get_received()
    last_verify = received[-1]["verify"] if received else {}

    env_blocked = dict(env)
    env_blocked["GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED"] = "0"
    _apply_env(env_blocked)
    result_blocked, event_id_blocked = _emit_notification("s3-no-hmac")
    wr_blocked = result_blocked["webhook_result"]

    env_restore = dict(env)
    _apply_env(env_restore)
    result_restore, event_id_restore = _emit_notification("s3-restore")
    wr_restore = result_restore["webhook_result"]

    passed = (
        wr_signed.get("dispatched") is True
        and last_verify.get("ok") is True
        and wr_blocked.get("dispatched") is False
        and wr_blocked.get("blocked_reason") == "blocked_by_hmac_tier_policy"
        and wr_restore.get("dispatched") is True
    )
    return {
        "phase": "S3",
        "go": passed,
        "event_ids": {
            "signed": event_id_signed,
            "blocked": event_id_blocked,
            "restore": event_id_restore,
        },
        "signed": {"dispatched": wr_signed.get("dispatched"), "receiver_verify": last_verify},
        "blocked": {
            "dispatched": wr_blocked.get("dispatched"),
            "blocked_reason": wr_blocked.get("blocked_reason"),
            "blocked_rule": wr_blocked.get("blocked_rule"),
        },
        "restore": {"dispatched": wr_restore.get("dispatched")},
    }


def run_s4(*, receiver: StagingWebhookReceiver, dlq_path: Path) -> Dict[str, Any]:
    env = _base_staging_env(receiver=receiver, dlq_path=dlq_path)
    env["GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS"] = "3"
    _apply_env(env)

    dlq_before = _count_dlq_lines(dlq_path)
    receiver.set_mode("sequential_503_then_200")
    result_retry_ok, event_id_retry_ok = _emit_notification("s4-retry-ok")
    wr_retry_ok = result_retry_ok["webhook_result"]
    dlq_after_retry_ok = _count_dlq_lines(dlq_path)

    receiver.set_mode("always_503")
    result_exhaust, event_id_exhaust = _emit_notification("s4-exhaust")
    wr_exhaust = result_exhaust["webhook_result"]
    dlq_after_exhaust = _count_dlq_lines(dlq_path)
    inspect_stats = _run_inspect("stats", dlq_path=dlq_path)

    passed = (
        wr_retry_ok.get("dispatched") is True
        and wr_retry_ok.get("retry_exhausted") is False
        and dlq_after_retry_ok == dlq_before
        and wr_exhaust.get("retry_exhausted") is True
        and dlq_after_exhaust == dlq_before + 1
    )
    return {
        "phase": "S4",
        "go": passed,
        "event_ids": {"retry_ok": event_id_retry_ok, "exhaust": event_id_exhaust},
        "retry_ok": {
            "dispatched": wr_retry_ok.get("dispatched"),
            "attempt_count": wr_retry_ok.get("attempt_count"),
            "retry_exhausted": wr_retry_ok.get("retry_exhausted"),
            "dlq_delta": dlq_after_retry_ok - dlq_before,
        },
        "exhaust": {
            "retry_exhausted": wr_exhaust.get("retry_exhausted"),
            "attempt_count": wr_exhaust.get("attempt_count"),
            "dlq_delta": dlq_after_exhaust - dlq_before,
        },
        "inspect_stats": inspect_stats,
    }


def run_all(*, output_path: Optional[Path] = None) -> Dict[str, Any]:
    bootstrap = provision_staging_slot()
    runtime_env = load_runtime_env()
    hmac_secret = runtime_env["GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET"]
    os.environ["GOV_STAGING_RECEIVER_HMAC_SECRET"] = hmac_secret

    dlq_path = _REPO_ROOT / bootstrap["dlq_path"].replace("/", os.sep)
    dlq_path.parent.mkdir(parents=True, exist_ok=True)
    if dlq_path.is_file():
        dlq_path.unlink()

    receiver = StagingWebhookReceiver(
        secret=hmac_secret,
        mode="ok",
        tls_cert=bootstrap.get("tls_cert"),
        tls_key=bootstrap.get("tls_key"),
    )
    receiver.start()
    time.sleep(0.2)

    report: Dict[str, Any] = {
        "run_id": RUN_ID,
        "run_url": receiver.base_url,
        "started_at": _utc_now_iso(),
        "bootstrap": {
            "provisioned_at": bootstrap.get("provisioned_at"),
            "manifest_path": bootstrap.get("manifest_path"),
        },
        "phases": [],
    }

    try:
        for runner in (run_s1, run_s2, run_s3, run_s4):
            phase_report = runner(receiver=receiver, dlq_path=dlq_path)
            report["phases"].append(phase_report)
            print(f"[{phase_report['phase']}] go={phase_report['go']}")
    finally:
        receiver.stop()
        rollback = rollback_staging_post()
        report["rollback"] = rollback
        report["finished_at"] = _utc_now_iso()
        report["go_no_go"] = all(p.get("go") for p in report["phases"]) and rollback.get("ok")

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="P7 staging integration execute S1–S4")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_SLOT_ROOT / f"execute_report_{RUN_ID}.json"),
    )
    args = parser.parse_args()

    report = run_all(output_path=Path(args.output))
    print(json.dumps({"run_id": report["run_id"], "go_no_go": report["go_no_go"]}, indent=2))
    return 0 if report.get("go_no_go") else 1


if __name__ == "__main__":
    raise SystemExit(main())
