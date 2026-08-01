#!/usr/bin/env python3
"""P7 staging env bootstrap (WH-P7-PROD-staging-env-bootstrap-v1).

Provisions staging slot resources without flipping TIER=staging for S1 POST.
Creates DLQ staging path, env slot manifest, rollback bundle, and optional receiver secret slot.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

DEFAULT_SLOT_ROOT = _REPO_ROOT / "05_Temp_Cache" / "staging" / "p7_notification"
DEFAULT_DLQ_DIR = _REPO_ROOT / "outbox" / "notification_dlq" / "staging"
DEFAULT_DLQ_PATH = DEFAULT_DLQ_DIR / "events.jsonl"
DEFAULT_RECEIVER_HOST = "localhost"
DEFAULT_RECEIVER_PORT = 8765
DEFAULT_RECEIVER_PATH = "/webhooks/gov/staging"

ROLLBACK_ENV = {
    "GOV_NOTIFICATION_WEBHOOK_TIER": "sandbox",
    "GOV_NOTIFICATION_WEBHOOK_ENABLED": "0",
    "GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED": "0",
    "GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED": "0",
    "GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS": "0",
    "GOV_NOTIFICATION_WEBHOOK_URL": "",
    "GOV_NOTIFICATION_WEBHOOK_DLQ_PATH": "outbox/notification_dlq/events.jsonl",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_staging_secret() -> str:
    return f"p7-staging-{secrets.token_hex(16)}"


def _openssl_executable() -> str:
    candidates = [
        "openssl",
        str(_REPO_ROOT / ".." / ".." / "Program Files" / "Git" / "usr" / "bin" / "openssl.exe"),
        r"C:\Program Files\Git\usr\bin\openssl.exe",
    ]
    for candidate in candidates:
        if candidate == "openssl":
            return candidate
        if Path(candidate).is_file():
            return candidate
    return "openssl"


def _ensure_tls_material(slot_root: Path, host: str = DEFAULT_RECEIVER_HOST) -> Dict[str, str]:
    cert_path = slot_root / "staging_receiver.crt"
    key_path = slot_root / "staging_receiver.key"
    if cert_path.is_file() and key_path.is_file():
        return {"cert": str(cert_path), "key": str(key_path)}

    bundled_cert = _REPO_ROOT / "tests" / "fixtures" / "staging_tls" / "localhost.crt"
    bundled_key = _REPO_ROOT / "tests" / "fixtures" / "staging_tls" / "localhost.key"
    if bundled_cert.is_file() and bundled_key.is_file():
        cert_path.write_bytes(bundled_cert.read_bytes())
        key_path.write_bytes(bundled_key.read_bytes())
        return {"cert": str(cert_path), "key": str(key_path)}

    cmd = [
        _openssl_executable(),
        "req",
        "-x509",
        "-newkey",
        "rsa:2048",
        "-keyout",
        str(key_path),
        "-out",
        str(cert_path),
        "-days",
        "30",
        "-nodes",
        "-subj",
        f"/CN={host}",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "TLS material missing: bundle tests/fixtures/staging_tls or install openssl. "
            f"detail={proc.stderr.strip() or proc.stdout.strip()}"
        )
    return {"cert": str(cert_path), "key": str(key_path)}


def provision_staging_slot(
    *,
    slot_root: Path = DEFAULT_SLOT_ROOT,
    dlq_dir: Path = DEFAULT_DLQ_DIR,
    receiver_host: str = DEFAULT_RECEIVER_HOST,
    receiver_port: int = DEFAULT_RECEIVER_PORT,
    receiver_path: str = DEFAULT_RECEIVER_PATH,
    regenerate_secret: bool = False,
) -> Dict[str, Any]:
    slot_root.mkdir(parents=True, exist_ok=True)
    dlq_dir.mkdir(parents=True, exist_ok=True)

    secret_path = slot_root / "hmac_secret.slot"
    if secret_path.is_file() and not regenerate_secret:
        hmac_secret = secret_path.read_text(encoding="utf-8").strip()
    else:
        hmac_secret = _generate_staging_secret()
        secret_path.write_text(hmac_secret + "\n", encoding="utf-8")

    tls_material = _ensure_tls_material(slot_root, host=receiver_host)
    receiver_url = f"https://{receiver_host}:{receiver_port}{receiver_path}"
    allowlist = f"{receiver_host}:{receiver_port}{receiver_path}"

    env_template = {
        "GOV_NOTIFICATION_WEBHOOK_ENABLED": "1",
        "GOV_NOTIFICATION_WEBHOOK_TIER": "sandbox",
        "GOV_NOTIFICATION_WEBHOOK_URL": receiver_url,
        "GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST": allowlist,
        "GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST": "demo_*",
        "GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED": "1",
        "GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET": "<from hmac_secret.slot>",
        "GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED": "1",
        "GOV_NOTIFICATION_WEBHOOK_DLQ_PATH": str(
            Path("outbox/notification_dlq/staging/events.jsonl")
        ),
        "GOV_NOTIFICATION_WEBHOOK_DLQ_TIER": "staging",
        "GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS": "3",
        "GOV_NOTIFICATION_WEBHOOK_RETRY_BASE_DELAY_MS": "50",
        "GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_DELAY_MS": "200",
    }

    manifest = {
        "schema_id": "p7_staging_env_slot_v1",
        "provisioned_at": _utc_now_iso(),
        "slot_root": str(slot_root.relative_to(_REPO_ROOT)).replace("\\", "/"),
        "dlq_path": str(DEFAULT_DLQ_PATH.relative_to(_REPO_ROOT)).replace("\\", "/"),
        "receiver_url": receiver_url,
        "url_allowlist": allowlist,
        "hmac_secret_slot": str(secret_path.relative_to(_REPO_ROOT)).replace("\\", "/"),
        "tls_cert": str(Path(tls_material["cert"]).relative_to(_REPO_ROOT)).replace("\\", "/"),
        "tls_key": str(Path(tls_material["key"]).relative_to(_REPO_ROOT)).replace("\\", "/"),
        "tier_at_provision": "sandbox",
        "governance_dual": "simulated_local_execute_2026-06-24",
        "rollback_bundle": "rollback_env.json",
        "env_template": env_template,
    }

    manifest_path = slot_root / "env_slot.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    rollback_path = slot_root / "rollback_env.json"
    rollback_path.write_text(json.dumps(ROLLBACK_ENV, indent=2) + "\n", encoding="utf-8")

    runtime_env_path = slot_root / "runtime_env.json"
    runtime_env = dict(env_template)
    runtime_env["GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET"] = hmac_secret
    runtime_env_path.write_text(json.dumps(runtime_env, indent=2) + "\n", encoding="utf-8")

    return {
        "ok": True,
        "message": "staging slot provisioned",
        "manifest_path": str(manifest_path),
        "runtime_env_path": str(runtime_env_path),
        "rollback_path": str(rollback_path),
        "dlq_path": str(DEFAULT_DLQ_PATH.relative_to(_REPO_ROOT)).replace("\\", "/"),
        "receiver_url": receiver_url,
        "provisioned_at": manifest["provisioned_at"],
        "tls_cert": tls_material["cert"],
        "tls_key": tls_material["key"],
    }


def apply_runtime_env(runtime_env_path: Path) -> Dict[str, Optional[str]]:
    saved: Dict[str, Optional[str]] = {}
    data = json.loads(runtime_env_path.read_text(encoding="utf-8"))
    for key, value in data.items():
        saved[key] = os.environ.get(key)
        if value is None or value == "":
            os.environ.pop(key, None)
        else:
            os.environ[str(key)] = str(value)
    return saved


def restore_env(saved: Dict[str, Optional[str]]) -> None:
    for key, value in saved.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def rollback_staging_post(*, slot_root: Path = DEFAULT_SLOT_ROOT) -> Dict[str, Any]:
    rollback_path = slot_root / "rollback_env.json"
    if not rollback_path.is_file():
        return {"ok": False, "message": f"rollback bundle missing: {rollback_path}"}

    data = json.loads(rollback_path.read_text(encoding="utf-8"))
    for key in list(os.environ.keys()):
        if key.startswith("GOV_NOTIFICATION_WEBHOOK"):
            os.environ.pop(key, None)
    for key, value in data.items():
        if value is None or value == "":
            os.environ.pop(key, None)
        else:
            os.environ[str(key)] = str(value)

    return {
        "ok": True,
        "message": "rollback applied",
        "rollback_at": _utc_now_iso(),
        "tier": os.environ.get("GOV_NOTIFICATION_WEBHOOK_TIER", "(unset)"),
        "enabled": os.environ.get("GOV_NOTIFICATION_WEBHOOK_ENABLED", "(unset)"),
    }


def dry_run_rollback_timing(*, slot_root: Path = DEFAULT_SLOT_ROOT) -> Dict[str, Any]:
    start = time.perf_counter()
    result = rollback_staging_post(slot_root=slot_root)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    result["elapsed_ms"] = elapsed_ms
    result["within_1_minute"] = elapsed_ms <= 60_000
    return result


def load_runtime_env(slot_root: Path = DEFAULT_SLOT_ROOT) -> Dict[str, str]:
    runtime_env_path = slot_root / "runtime_env.json"
    if not runtime_env_path.is_file():
        raise FileNotFoundError(f"runtime env missing: {runtime_env_path}")
    data = json.loads(runtime_env_path.read_text(encoding="utf-8"))
    return {str(k): str(v) for k, v in data.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description="P7 staging env bootstrap")
    parser.add_argument("--slot-root", default=str(DEFAULT_SLOT_ROOT))
    parser.add_argument("--regenerate-secret", action="store_true")
    parser.add_argument("--rollback-dry-run", action="store_true")
    args = parser.parse_args()

    slot_root = Path(args.slot_root)

    if args.rollback_dry_run:
        provision_staging_slot(slot_root=slot_root)
        result = dry_run_rollback_timing(slot_root=slot_root)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("ok") else 1

    result = provision_staging_slot(
        slot_root=slot_root,
        regenerate_secret=args.regenerate_secret,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
