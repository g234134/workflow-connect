"""Unit tests for agent-lines audit quickview CLI v1 (W10-T3)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CLI_PATH = _REPO_ROOT / "scripts" / "run_agent_audit_quickview.py"

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from delivery import notification_gateway_v1 as gw


def _load_module():
    spec = importlib.util.spec_from_file_location("run_agent_audit_quickview", _CLI_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_agent_audit_quickview"] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_fake_regression_artifact(
    outbox_root: Path,
    *,
    timestamp: str,
    case_ref: str,
    decision: str = "needs_review",
    risk_level: str = "medium",
    cp_a_status: str = "auto_approved",
    cp_b_status: str = "skipped",
    cp_b_would_trigger: bool = True,
) -> Path:
    slug = case_ref.replace("/", "_")
    dest = outbox_root / "agent_experiment_regression" / f"{timestamp}_{slug}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "agent_experiment_regression_v1",
        "written_at": "2026-06-10T12:00:00Z",
        "case_summary": {
            "case_ref": case_ref,
            "mode": "run",
            "final_status": "waiting_for_human",
            "checkpoint_a_status": cp_a_status,
            "checkpoint_b_status": cp_b_status,
            "checkpoint_b_would_trigger": cp_b_would_trigger,
            "decision": decision,
            "experiment_id": "exp-fake-001",
        },
        "experiment": {
            "case_ref": case_ref,
            "task_type": "tabular.cleaning.mvp",
            "mode": "run",
            "final_status": "waiting_for_human",
            "experiment_id": "exp-fake-001",
            "decision": {
                "decision": decision,
                "risk_level": risk_level,
                "message": f"decision={decision} risk={risk_level}",
            },
            "planned_route": {
                "selector_task_type": "e2e",
                "planned_tools": [
                    "validate.eligibility",
                    "clean.phase_demo",
                    "export.delivery_bundle",
                ],
            },
            "checkpoint_a_status": {
                "checkpoint_id": "A-intake-confirmation",
                "would_trigger": True,
                "status": cp_a_status,
            },
            "checkpoint_b_status": {
                "checkpoint_id": "B-delivery-confirmation",
                "would_trigger": cp_b_would_trigger,
                "status": cp_b_status,
            },
        },
    }
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return dest


def _write_fake_checkpoint_b(
    outbox_root: Path,
    *,
    case_ref: str,
    timestamp: str = "2026-06-10T12-05-00Z",
) -> Path:
    case_dir = outbox_root / case_ref
    case_dir.mkdir(parents=True, exist_ok=True)
    dest = case_dir / f"checkpoint_B-delivery-confirmation_{timestamp}.json"
    payload = {
        "schema_version": "hitl_checkpoint_v1",
        "checkpoint_id": "B-delivery-confirmation",
        "case_ref": case_ref.split("/")[-1] if "/" not in case_ref else case_ref,
        "status": "approved",
        "human_decision": {
            "action": "approve_delivery",
            "operator_id": "reviewer_test",
            "comment": "LGTM fake",
            "timestamp": "2026-06-10T12:05:01Z",
        },
    }
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return dest


class TestAgentAuditQuickviewV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _CLI_PATH.is_file():
            raise unittest.SkipTest(f"missing CLI: {_CLI_PATH}")
        cls.mod = _load_module()

    def test_find_latest_run_artifact_picks_newest_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outbox = root / "outbox"
            _write_fake_regression_artifact(
                outbox,
                timestamp="20260610T100000Z",
                case_ref="demo_phase",
                decision="reject",
            )
            _write_fake_regression_artifact(
                outbox,
                timestamp="20260610T120000Z",
                case_ref="demo_phase",
                decision="needs_review",
            )
            found = self.mod.find_latest_run_artifact("demo_phase", repo_root=root)
            self.assertIsNotNone(found)
            assert found is not None
            self.assertEqual(found["artifact_timestamp"], "20260610T120000Z")
            self.assertEqual(found["source_kind"], "agent_experiment_regression")

    def test_quickview_json_shape_demo_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outbox = root / "outbox"
            _write_fake_regression_artifact(outbox, timestamp="20260610T120000Z", case_ref="demo_phase")
            _write_fake_checkpoint_b(outbox, case_ref="demo_phase")

            view = self.mod.run_agent_audit_quickview("demo_phase", repo_root=root)
            self.assertTrue(view["ok"])
            self.assertTrue(view["read_only"])
            self.assertEqual(view["schema_version"], "agent_audit_quickview_v1")
            self.assertEqual(view["decision"]["decision"], "needs_review")
            self.assertEqual(view["decision"]["risk_level"], "medium")
            self.assertEqual(
                view["planned_route"]["planned_tools"],
                ["validate.eligibility", "clean.phase_demo", "export.delivery_bundle"],
            )
            self.assertTrue(view["checkpoint_a"]["would_trigger"])
            self.assertEqual(view["checkpoint_a"]["status"], "auto_approved")
            self.assertTrue(view["checkpoint_b"]["on_disk"])
            self.assertIsNotNone(view["delivery_approval"])
            self.assertEqual(view["delivery_approval"]["action"], "approve_delivery")

    def test_quickview_text_output_contains_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outbox = root / "outbox"
            _write_fake_regression_artifact(outbox, timestamp="20260610T120000Z", case_ref="demo_phase")
            view = self.mod.run_agent_audit_quickview("demo_phase", repo_root=root)
            text = self.mod.format_audit_quickview_text(view)
            self.assertIn("Agent-Lines Audit Quickview", text)
            self.assertIn("decision: needs_review", text)
            self.assertIn("risk_level: medium", text)
            self.assertIn("planned_tools:", text)
            self.assertIn("Checkpoint A", text)
            self.assertIn("Checkpoint B", text)

    def test_missing_case_returns_not_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "outbox").mkdir()
            view = self.mod.run_agent_audit_quickview("nonexistent_case", repo_root=root)
            self.assertFalse(view["ok"])
            self.assertFalse(view["latest_run"]["found"])

    def test_read_only_collects_paths_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outbox = root / "outbox"
            reg_path = _write_fake_regression_artifact(
                outbox,
                timestamp="20260610T120000Z",
                case_ref="demo_phase",
            )
            cp_path = _write_fake_checkpoint_b(outbox, case_ref="demo_phase")

            before = {
                p: p.read_text(encoding="utf-8")
                for p in [reg_path, cp_path]
            }
            paths = self.mod.collect_read_paths("demo_phase", repo_root=root)
            self.mod.run_agent_audit_quickview("demo_phase", repo_root=root)

            self.assertIn(
                "outbox/agent_experiment_regression/20260610T120000Z_demo_phase.json",
                paths,
            )
            self.assertIn(
                "outbox/demo_phase/checkpoint_B-delivery-confirmation_2026-06-10T12-05-00Z.json",
                paths,
            )
            for path, content in before.items():
                self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_investigation_view_projection_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outbox = root / "outbox"
            _write_fake_regression_artifact(outbox, timestamp="20260610T120000Z", case_ref="demo_phase")
            wire = self.mod.run_agent_audit_quickview("demo_phase", repo_root=root)
            from audit.audit_investigation_projection_v1 import project_audit_investigation_view

            view = project_audit_investigation_view(wire)
            self.assertEqual(view["schema_version"], "audit_investigation_view_v1")
            self.assertTrue(view["read_only"])
            self.assertIn("sections", view)
            self.assertIn("timeline", view)
            self.assertIn("gaps", view)
            self.assertIn("audit_sections_found", view)
            self.assertIn("audit_gaps_count", view)

    def test_investigation_view_missing_downstream_ack_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outbox = root / "outbox"
            event = gw.build_notification_event("run.completed", case_ref="demo_phase")
            gw.send_notification(event, enabled=True, outbox_root_override=str(outbox))
            wire = self.mod.run_agent_audit_quickview("demo_phase", repo_root=root)
            from audit.audit_investigation_projection_v1 import project_audit_investigation_view

            view = project_audit_investigation_view(wire)
            gap_ids = {g["gap_id"] for g in view["gaps"]}
            self.assertIn("missing_downstream_ack", gap_ids)
            section_ids = {s["section_id"] for s in view["sections"]}
            self.assertIn("workflow_notifications", section_ids)

    def test_investigation_view_downstream_ack_failed_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outbox = root / "outbox"
            event = gw.build_notification_event("run.blocked", case_ref="demo_phase")
            gw.send_notification(event, enabled=True, outbox_root_override=str(outbox))
            from delivery import feedback_ingest_v1 as ingest

            ingest.record_downstream_ack(
                event["event_id"],
                "local_handler_v1",
                "failed",
                message="simulated failure",
                repo_root=root,
                outbox_root_override=str(outbox),
            )
            wire = self.mod.run_agent_audit_quickview("demo_phase", repo_root=root)
            from audit.audit_investigation_projection_v1 import project_audit_investigation_view

            view = project_audit_investigation_view(wire)
            gap_ids = {g["gap_id"] for g in view["gaps"]}
            self.assertIn("downstream_ack_failed", gap_ids)

    def test_cli_investigation_view_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outbox = root / "outbox"
            _write_fake_regression_artifact(outbox, timestamp="20260610T120000Z", case_ref="demo_phase")
            proc = subprocess.run(
                [
                    sys.executable,
                    str(_CLI_PATH),
                    "--case-ref",
                    "demo_phase",
                    "--view",
                    "investigation",
                    "--format",
                    "json",
                    "--repo-root",
                    str(root),
                ],
                cwd=_REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            view = json.loads(proc.stdout)
            self.assertEqual(view["schema_version"], "audit_investigation_view_v1")
            self.assertIn("sections", view)

    def test_non_tabular_experiment_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nt_dir = root / "outbox" / "non_tabular_experiment"
            nt_dir.mkdir(parents=True)
            payload = {
                "schema_version": "non_tabular_experiment_preview_v1",
                "case_ref": "nt_docu_stub",
                "task_type": "non_tabular.document.extract",
                "mode": "preview",
                "flow_family": "non_tabular",
                "decision": {"decision": "needs_review", "risk_level": "medium"},
                "planned_route": {"selector_task_type": "nt_doc_extract"},
                "planned_tools": ["nt.parse_document", "nt.extract_fields"],
                "final_status": "preview_complete",
            }
            dest = nt_dir / "20260610T130000Z_nt_docu_stub.json"
            dest.write_text(json.dumps(payload), encoding="utf-8")

            view = self.mod.run_agent_audit_quickview("nt_docu_stub", repo_root=root)
            self.assertTrue(view["ok"])
            self.assertEqual(view["latest_run"]["source_kind"], "non_tabular_experiment")
            self.assertEqual(view["planned_route"]["planned_tools"], ["nt.parse_document", "nt.extract_fields"])


if __name__ == "__main__":
    unittest.main()
