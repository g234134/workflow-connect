"""Unit tests for sandbox end-to-end delivery bundle v1 (W12-T1)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from delivery.sandbox_delivery_bundle_v1 import (
    can_proceed_sandbox_bundle,
    find_latest_sandbox_bundle,
    is_sandbox_e2e_allowed,
    write_sandbox_delivery_bundle,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ADDITIONAL_DEMO = _REPO_ROOT / "cases" / "additional_demo"


class TestSandboxDeliveryBundleV1(unittest.TestCase):
    def test_allowlist_only_additional_demo(self) -> None:
        allowed, _ = is_sandbox_e2e_allowed("additional_demo")
        self.assertTrue(allowed)
        allowed, reason = is_sandbox_e2e_allowed("demo_phase")
        self.assertFalse(allowed)
        self.assertIn("demo_phase", reason)
        allowed, _ = is_sandbox_e2e_allowed("sandbox_client")
        self.assertFalse(allowed)

    def test_can_proceed_guard_ok(self) -> None:
        ok, reason = can_proceed_sandbox_bundle({"status": "ok", "removal_ratio": 0.2})
        self.assertTrue(ok)
        self.assertEqual(reason, "output_guard_ok")

    def test_can_proceed_blocked_without_approve(self) -> None:
        ok, reason = can_proceed_sandbox_bundle(
            {"status": "warning", "removal_ratio": 0.9}
        )
        self.assertFalse(ok)
        self.assertIn("blocked", reason)

    def test_can_proceed_auto_approve_delivery(self) -> None:
        ok, reason = can_proceed_sandbox_bundle(
            {"status": "warning", "removal_ratio": 0.9},
            auto_approve_delivery=True,
        )
        self.assertTrue(ok)
        self.assertEqual(reason, "auto_approve_delivery")

    def test_write_sandbox_bundle_creates_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            result = write_sandbox_delivery_bundle(
                case_ref="additional_demo",
                case_dir=str(_ADDITIONAL_DEMO),
                experiment_id="test-exp-12345678",
                output_guard={"status": "ok", "removal_ratio": 0.25},
                run_execution={"ok": True, "tools_executed": ["export.delivery_bundle"]},
                repo_root=_REPO_ROOT,
                outbox_root_override=str(outbox),
            )
            self.assertTrue(result["ok"])
            self.assertTrue(result.get("sandbox"))
            self.assertFalse(result.get("notify_triggered"))
            manifest_path = Path(result["manifest_path"])
            if not manifest_path.is_absolute():
                manifest_path = _REPO_ROOT / manifest_path
            self.assertTrue(manifest_path.is_file())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertTrue(manifest.get("sandbox"))
            self.assertFalse(manifest.get("production_contract"))
            self.assertFalse(manifest.get("notify_triggered"))
            self.assertEqual(manifest.get("case_ref"), "additional_demo")

    def test_find_latest_sandbox_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Path(tmp) / "outbox"
            write_sandbox_delivery_bundle(
                case_ref="additional_demo",
                case_dir=str(_ADDITIONAL_DEMO),
                experiment_id="find-latest-test",
                output_guard={"status": "ok"},
                repo_root=_REPO_ROOT,
                outbox_root_override=str(outbox),
            )
            latest = find_latest_sandbox_bundle(
                "additional_demo",
                repo_root=_REPO_ROOT,
                outbox_root_override=str(outbox),
            )
            self.assertIsNotNone(latest)
            assert latest is not None
            self.assertEqual(latest["source_kind"], "sandbox_delivery")
            self.assertTrue(latest["payload"].get("sandbox"))


if __name__ == "__main__":
    unittest.main()
