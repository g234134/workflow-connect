"""Contract tests for audit-quickview-and-case-history-spec-v1 (WB-T5).

Doc + projection contract only; no audit CLI behavior changes.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

from audit.audit_investigation_projection_v1 import project_audit_investigation_view

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SPEC = _REPO_ROOT / "docs" / "audit-quickview-and-case-history-spec-v1.md"
_OUTBOX_CONTRACT = _REPO_ROOT / "docs" / "outbox-and-feedback-layer-contract-v1.md"
_CLI_PATH = _REPO_ROOT / "scripts" / "run_agent_audit_quickview.py"
_CASES_INDEX = _REPO_ROOT / "cases" / "index.json"

_REQUIRED_SECTIONS = (
    "## §1 Purpose and scope",
    "## §2 CLI input and output shapes",
    "## §3 Data source priority",
    "## §4 Case history join",
    "## §5 Read-only · investigation-only",
    "## §6 Observability",
    "## §7 Cross-references",
    "## §8 Verification",
)

_WIRE_REQUIRED_KEYS = (
    "ok",
    "read_only",
    "schema_version",
    "case_ref",
    "message",
    "latest_run",
    "decision",
    "planned_route",
    "checkpoint_a",
    "checkpoint_b",
    "delivery_approval",
)

_INVESTIGATION_REQUIRED_KEYS = (
    "ok",
    "read_only",
    "schema_version",
    "case_ref",
    "sections",
    "timeline",
    "gaps",
    "audit_sections_found",
    "audit_gaps_count",
    "message",
)

_SECTION_IDS = (
    "latest_run",
    "decision",
    "planned_route",
    "checkpoint_a",
    "checkpoint_b",
    "delivery_approval",
    "workflow_notifications",
)

_ACK_GAP_IDS = (
    "missing_downstream_ack",
    "downstream_ack_failed",
)

_CASE_HISTORY_FIELDS = (
    "case_dir",
    "client_ref",
    "case_id",
    "product_sku",
    "gate_status",
    "schema_headers",
    "known_limits",
)

_WB_T3_AUDIT_NAMESPACE_PATHS = (
    "outbox/agent_ci/",
    "outbox/agent_experiment_regression/",
    "outbox/non_tabular_experiment/",
    "outbox/sandbox_delivery/",
    "outbox/<case_ref>/",
)

_SOURCE_PRIORITY = (
    "agent_ci",
    "agent_experiment_regression",
    "non_tabular_experiment",
)


def _read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing required file: {path.relative_to(_REPO_ROOT)}")
    return path.read_text(encoding="utf-8")


def _load_cli_module():
    spec = importlib.util.spec_from_file_location("run_agent_audit_quickview", _CLI_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_agent_audit_quickview_spec"] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_fake_regression_artifact(
    outbox_root: Path,
    *,
    timestamp: str,
    case_ref: str,
) -> None:
    slug = case_ref.replace("/", "_")
    dest = outbox_root / "agent_experiment_regression" / f"{timestamp}_{slug}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "case_summary": {"case_ref": case_ref, "mode": "run", "final_status": "ok"},
        "experiment": {
            "case_ref": case_ref,
            "decision": {"decision": "needs_review", "risk_level": "medium"},
            "planned_route": {"planned_tools": ["validate.eligibility"], "selector_task_type": "e2e"},
            "checkpoint_a_status": {"would_trigger": True, "status": "auto_approved"},
            "checkpoint_b_status": {"would_trigger": True, "status": "skipped"},
        },
    }
    dest.write_text(json.dumps(payload), encoding="utf-8")


class TestAuditQuickviewAndCaseHistorySpecV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _SPEC.is_file():
            raise unittest.SkipTest(f"missing spec: {_SPEC}")
        cls.spec = _read(_SPEC)
        cls.outbox_contract = _read(_OUTBOX_CONTRACT)

    def test_spec_file_exists_with_required_sections(self) -> None:
        missing = [h for h in _REQUIRED_SECTIONS if h not in self.spec]
        self.assertEqual(missing, [], f"missing headings: {missing}")

    def test_spec_section2_defines_sections_timeline_gaps(self) -> None:
        section2 = self._section("## §2", "## §3")
        for token in ("sections[]", "timeline[]", "gaps[]", "audit_sections_found", "audit_gaps_count"):
            with self.subTest(token=token):
                self.assertIn(token, section2)

    def test_spec_section3_source_priority_order(self) -> None:
        section3 = self._section("## §3", "## §4")
        idx_ci = section3.find("agent_ci")
        idx_reg = section3.find("agent_experiment_regression")
        idx_nt = section3.find("non_tabular_experiment")
        idx_tabular = section3.find("Tabular per-run")
        self.assertTrue(0 <= idx_ci < idx_reg < idx_nt)
        self.assertGreater(idx_tabular, idx_nt)

    def test_spec_section4_case_history_fields_match_index(self) -> None:
        section4 = self._section("## §4", "## §5")
        for field in _CASE_HISTORY_FIELDS:
            with self.subTest(field=field):
                self.assertIn(field, section4)
        index = json.loads(_read(_CASES_INDEX))
        demo = next(c for c in index["cases"] if c["case_id"] == "demo_phase")
        self.assertIn("client_ref", demo)
        self.assertIn("known_limits", demo)

    def test_spec_section5_investigation_only_and_state_boundary(self) -> None:
        section5 = self._section("## §5", "## §6")
        self.assertIn("investigation-only", section5.lower())
        self.assertIn("not** production SLA", section5)
        self.assertIn("Orchestrator-only", section5)

    def test_spec_cross_refs_wb_t3_namespaces(self) -> None:
        section7 = self._section("## §7", "## §8")
        for path in _WB_T3_AUDIT_NAMESPACE_PATHS:
            with self.subTest(path=path):
                self.assertIn(path, section7)
        for ns in _SOURCE_PRIORITY:
            with self.subTest(ns=ns):
                self.assertIn(ns, self.outbox_contract)

    def test_wire_format_keys_from_fixture_run(self) -> None:
        if not _CLI_PATH.is_file():
            self.skipTest("missing CLI")
        mod = _load_cli_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outbox = root / "outbox"
            _write_fake_regression_artifact(
                outbox, timestamp="20260610T120000Z", case_ref="demo_phase"
            )
            wire = mod.run_agent_audit_quickview("demo_phase", repo_root=root)
            self.assertEqual(wire["schema_version"], "agent_audit_quickview_v1")
            for key in _WIRE_REQUIRED_KEYS:
                with self.subTest(key=key):
                    self.assertIn(key, wire)

    def test_investigation_projection_shape(self) -> None:
        if not _CLI_PATH.is_file():
            self.skipTest("missing CLI")
        mod = _load_cli_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outbox = root / "outbox"
            _write_fake_regression_artifact(
                outbox, timestamp="20260610T120000Z", case_ref="demo_phase"
            )
            wire = mod.run_agent_audit_quickview("demo_phase", repo_root=root)
            view = project_audit_investigation_view(wire, case_history={"ok": False})
            for key in _INVESTIGATION_REQUIRED_KEYS:
                with self.subTest(key=key):
                    self.assertIn(key, view)
            self.assertEqual(view["schema_version"], "audit_investigation_view_v1")
            self.assertIsInstance(view["sections"], list)
            self.assertIsInstance(view["timeline"], list)
            self.assertIsInstance(view["gaps"], list)
            self.assertEqual(view["audit_sections_found"], sum(1 for s in view["sections"] if s["found"]))
            self.assertEqual(view["audit_gaps_count"], len(view["gaps"]))
            section_ids = {s["section_id"] for s in view["sections"]}
            for sid in _SECTION_IDS:
                with self.subTest(section_id=sid):
                    self.assertIn(sid, section_ids)

    def test_timeline_events_have_step_id_and_namespace(self) -> None:
        wire = {
            "ok": True,
            "case_ref": "demo_phase",
            "message": "test",
            "latest_run": {
                "found": True,
                "source_kind": "agent_experiment_regression",
                "artifact_path": "outbox/agent_experiment_regression/t.json",
                "artifact_timestamp": "20260610T120000Z",
            },
            "decision": {"decision": "needs_review"},
            "planned_route": {"planned_tools": ["a"]},
            "checkpoint_a": {"status": "ok", "on_disk": False, "would_trigger": True},
            "checkpoint_b": {"status": "skipped", "on_disk": False, "would_trigger": False},
            "delivery_approval": None,
        }
        view = project_audit_investigation_view(wire)
        self.assertTrue(view["timeline"])
        for event in view["timeline"]:
            self.assertRegex(event["step_id"], r"^S\d+")
            self.assertIn("namespace_prefix", event)
            self.assertIn("source_path", event)

    def test_missing_cp_b_on_disk_emits_gap(self) -> None:
        wire = {
            "ok": True,
            "case_ref": "demo_phase",
            "message": "test",
            "latest_run": {"found": False},
            "decision": {"decision": None},
            "planned_route": {},
            "checkpoint_a": {"would_trigger": False},
            "checkpoint_b": {"would_trigger": True, "on_disk": False, "status": None},
            "delivery_approval": None,
        }
        view = project_audit_investigation_view(wire)
        gap_ids = {g["gap_id"] for g in view["gaps"]}
        self.assertIn("missing_run_artifact", gap_ids)
        self.assertIn("missing_checkpoint_b_on_disk", gap_ids)

    def test_spec_documents_downstream_ack_gaps(self) -> None:
        section2 = self._section("## §2", "## §3")
        for gap_id in _ACK_GAP_IDS:
            with self.subTest(gap_id=gap_id):
                self.assertIn(gap_id, section2)

    def test_investigation_view_emits_downstream_ack_gaps(self) -> None:
        if str(_REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(_REPO_ROOT))
        from delivery import feedback_ingest_v1 as ingest
        from delivery import notification_gateway_v1 as gw

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outbox = root / "outbox"
            pending_event = gw.build_notification_event("run.completed", case_ref="demo_phase")
            gw.send_notification(pending_event, enabled=True, outbox_root_override=str(outbox))
            failed_event = gw.build_notification_event("run.blocked", case_ref="demo_phase")
            gw.send_notification(failed_event, enabled=True, outbox_root_override=str(outbox))
            ingest.record_downstream_ack(
                failed_event["event_id"],
                "h1",
                "failed",
                message="err",
                repo_root=root,
                outbox_root_override=str(outbox),
            )
            mod = _load_cli_module()
            wire = mod.run_agent_audit_quickview("demo_phase", repo_root=root)
            view = project_audit_investigation_view(wire)
            gap_ids = {g["gap_id"] for g in view["gaps"]}
            self.assertIn("missing_downstream_ack", gap_ids)
            self.assertIn("downstream_ack_failed", gap_ids)

    def test_cli_subprocess_demo_phase_json_wire_format(self) -> None:
        if not _CLI_PATH.is_file():
            self.skipTest("missing CLI")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fake_regression_artifact(
                root / "outbox",
                timestamp="20260610T120000Z",
                case_ref="demo_phase",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(_CLI_PATH),
                    "--case-ref",
                    "demo_phase",
                    "--format",
                    "json",
                    "--repo-root",
                    str(root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            wire = json.loads(proc.stdout)
            view = project_audit_investigation_view(wire)
            self.assertTrue(wire["ok"])
            self.assertGreaterEqual(view["audit_sections_found"], 1)
            self.assertIsInstance(view["audit_gaps_count"], int)
            self.assertGreaterEqual(view["audit_gaps_count"], 0)

    def test_readme_v2_points_to_spec_not_dual_maintenance(self) -> None:
        readme = _read(_REPO_ROOT / "docs" / "agent-and-non-tabular-lines-readme-v2.md")
        section4 = re.search(r"## §4 CI / Metrics / Audit(.*?)## §5", readme, re.DOTALL)
        self.assertIsNotNone(section4)
        assert section4 is not None
        body = section4.group(1)
        self.assertIn("audit-quickview-and-case-history-spec-v1.md", body)
        self.assertIn("雙維護", body)

    def _section(self, start: str, end: str) -> str:
        start_idx = self.spec.index(start)
        end_idx = self.spec.index(end, start_idx + 1)
        return self.spec[start_idx:end_idx]


if __name__ == "__main__":
    unittest.main()
