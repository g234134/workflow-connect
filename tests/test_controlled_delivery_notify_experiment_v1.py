"""Unit tests for controlled delivery / notify experiment v1 (W7-T3)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from delivery.controlled_notify_experiment_v1 import (
    SCHEMA_VERSION,
    generate_client_summary,
    is_experiment_case_allowed,
    load_delivery_context,
    run_controlled_notify_experiment,
)
from tools.tabular_outbox_writer import outbox_root

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEMO_PHASE = _REPO_ROOT / "cases" / "demo_phase"


class TestControlledDeliveryNotifyExperimentV1(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)
        self.outbox = outbox_root(self.repo_root)
        self.extra = {
            "repo_root": self.repo_root,
            "outbox_root_override": str(self.outbox),
        }

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_demo_phase_happy_path_dry_run(self) -> None:
        result = run_controlled_notify_experiment(
            _DEMO_PHASE,
            dry_run=True,
            repo_root=_REPO_ROOT,
        )

        self.assertTrue(result["ok"])
        self.assertTrue(result["dry_run"])
        self.assertTrue(result["simulated"])
        self.assertFalse(result["external_dispatch"])
        self.assertEqual(result["case_ref"], "demo_phase")
        self.assertIsNone(result["outbox_path"])
        self.assertIn("Dear internal-demo team", result["client_summary_text"])
        self.assertIn("sandbox only", result["client_summary_text"].lower())

    def test_demo_phase_writes_outbox_record(self) -> None:
        result = run_controlled_notify_experiment(
            _DEMO_PHASE,
            dry_run=False,
            repo_root=_REPO_ROOT,
            outbox_root_override=str(_REPO_ROOT / "outbox"),
        )

        self.assertTrue(result["ok"])
        self.assertFalse(result["dry_run"])
        self.assertIsNotNone(result["outbox_path"])
        outbox_path = _REPO_ROOT / str(result["outbox_path"])
        self.assertTrue(outbox_path.is_file())

        record = json.loads(outbox_path.read_text(encoding="utf-8"))
        self.assertEqual(record["schema_version"], SCHEMA_VERSION)
        self.assertEqual(record["case_ref"], "demo_phase")
        self.assertTrue(record["simulated"])
        self.assertFalse(record["external_dispatch"])
        self.assertIn("notify_payload", record)
        self.assertIn("client_summary_text", record)
        self.assertEqual(record["notify_payload"]["channel"], "experiment_log")

        outbox_path.unlink()

    def test_non_allowlist_case_ref_blocked(self) -> None:
        case_dir = self.repo_root / "cases" / "acme" / "2026-0001"
        case_dir.mkdir(parents=True)
        (case_dir / "intake.json").write_text(
            json.dumps(
                {
                    "case_id": "2026-0001",
                    "client_ref": "acme",
                    "sensitivity": "internal",
                }
            ),
            encoding="utf-8",
        )
        (case_dir / "delivery_signoff.md").write_text("# signoff\n", encoding="utf-8")
        reports = case_dir / "reports"
        reports.mkdir()
        (reports / "report.json").write_text(json.dumps({"summary": {}}), encoding="utf-8")

        result = run_controlled_notify_experiment(
            case_dir,
            dry_run=True,
            **self.extra,
        )

        self.assertFalse(result["ok"])
        self.assertTrue(result.get("blocked"))
        self.assertIn("allowlist", result["message"])

    def test_notify_experiment_json_structure(self) -> None:
        context = load_delivery_context(_DEMO_PHASE, repo_root=_REPO_ROOT)
        self.assertTrue(context["ok"])

        summary = generate_client_summary(context)
        result = run_controlled_notify_experiment(
            _DEMO_PHASE,
            dry_run=False,
            repo_root=_REPO_ROOT,
            outbox_root_override=str(self.outbox),
        )
        self.assertTrue(result["ok"])

        record = result["record"]
        required_keys = {
            "schema_version",
            "experiment_version",
            "case_ref",
            "case_dir",
            "generated_at",
            "dry_run",
            "simulated",
            "external_dispatch",
            "notify_channel",
            "delivery_sources",
            "bundle_artifacts",
            "client_summary_text",
            "notify_payload",
        }
        self.assertTrue(required_keys.issubset(record.keys()))
        self.assertEqual(record["client_summary_text"], summary)
        self.assertFalse(record["notify_payload"]["external_dispatch"])

        written = list((self.outbox / "demo_phase").glob("notify_experiment_*.json"))
        self.assertEqual(len(written), 1)

    def test_is_experiment_case_allowed_rejects_non_internal(self) -> None:
        allowed, _ = is_experiment_case_allowed(
            "demo_phase",
            {"sensitivity": "confidential", "client_ref": "demo"},
        )
        self.assertFalse(allowed)


if __name__ == "__main__":
    unittest.main()
