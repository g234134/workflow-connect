"""W4-UI-F: command_center mock|live fetch switch + live projection contract."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHELL_JS = REPO_ROOT / "ui" / "command_center" / "js" / "shell.js"
P1_HTML = REPO_ROOT / "ui" / "command_center" / "p1.html"
P5_HTML = REPO_ROOT / "ui" / "command_center" / "p5.html"
LIVE_P1 = REPO_ROOT / "ui" / "command_center" / "live" / "p1_overview_v1.json"
LIVE_P5 = REPO_ROOT / "ui" / "command_center" / "live" / "p5_swimlane_v1.json"
MOCK_P1 = REPO_ROOT / "ui" / "command_center" / "mock" / "p1_overview_v1.json"
MOCK_P5 = REPO_ROOT / "ui" / "command_center" / "mock" / "p5_swimlane_v1.json"
PROJECTOR = REPO_ROOT / "scripts" / "project_command_center_live_v1.py"
RUNBOOK = REPO_ROOT / "docs" / "wave4-ui-f-live-api-mount-runbook-v1.md"
TICKET = (
    REPO_ROOT
    / "04_Workflows"
    / "tickets"
    / "W4-UI-F-command-center-live-api-mount-v1_state.md"
)

P89_KEYS = (
    "event_id",
    "ack_status",
    "handler_id",
    "dispatch_registry_hit",
    "dlq_flag",
)

SECRET_LEAK_RE = re.compile(
    r"(sk-[A-Za-z0-9]{16,}|api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}|Bearer\s+[A-Za-z0-9\-._~+/]{12,})",
    re.IGNORECASE,
)


class TestW4UiFLiveApiMountV1(unittest.TestCase):
    def test_assets_exist(self) -> None:
        for path in (
            SHELL_JS,
            P1_HTML,
            P5_HTML,
            LIVE_P1,
            LIVE_P5,
            MOCK_P1,
            MOCK_P5,
            PROJECTOR,
            RUNBOOK,
            TICKET,
        ):
            self.assertTrue(path.is_file(), f"missing: {path.relative_to(REPO_ROOT)}")

    def test_shell_has_fetch_switch(self) -> None:
        js = SHELL_JS.read_text(encoding="utf-8")
        self.assertIn("function resolveDataSource", js)
        self.assertIn("function loadPageData", js)
        self.assertIn('q === "live"', js)
        self.assertIn("mock_fallback", js)
        self.assertIn("loadPageData: loadPageData", js)

    def test_p1_p5_use_load_page_data(self) -> None:
        p1 = P1_HTML.read_text(encoding="utf-8")
        p5 = P5_HTML.read_text(encoding="utf-8")
        self.assertIn("loadPageData", p1)
        self.assertIn("mock/p1_overview_v1.json", p1)
        self.assertIn("live/p1_overview_v1.json", p1)
        self.assertIn("loadPageData", p5)
        self.assertIn("mock/p5_swimlane_v1.json", p5)
        self.assertIn("live/p5_swimlane_v1.json", p5)

    def test_live_p1_contract(self) -> None:
        data = json.loads(LIVE_P1.read_text(encoding="utf-8"))
        self.assertTrue(data["ok"])
        self.assertFalse(data["demo"])
        self.assertTrue(data["read_only"])
        self.assertEqual(data["data_source"], "live_projection")
        self.assertEqual(data["secrets_policy"], "mask_only")
        self.assertEqual(data["secrets"]["api_key_display"], "••••••••")
        self.assertGreaterEqual(len(data["kpis"]), 1)
        op = data["operator_fields"]
        self.assertTrue(op["ok"])
        self.assertEqual(list(op["fields"]), list(P89_KEYS))
        self.assertGreaterEqual(len(op["rows"]), 1)
        for row in op["rows"]:
            for key in P89_KEYS:
                self.assertIn(key, row)
        self.assertIn("≠ Grafana", " ".join(data["non_claims"]))
        self.assertNotRegex(json.dumps(data, ensure_ascii=False), SECRET_LEAK_RE)

    def test_live_p5_contract(self) -> None:
        data = json.loads(LIVE_P5.read_text(encoding="utf-8"))
        self.assertTrue(data["ok"])
        self.assertFalse(data["demo"])
        self.assertTrue(data["read_only"])
        self.assertEqual(data["data_source"], "live_projection")
        self.assertIn("swimlane", data)
        self.assertGreaterEqual(len(data["swimlane"]["tasks"]), 1)
        self.assertGreaterEqual(len(data["kpis"]), 1)
        overlays = data["live_overlays"]
        self.assertIn("p89_operator_fields", overlays)
        self.assertIn("command_queue", overlays)
        self.assertIn("metrics_note", overlays)
        self.assertIn("gate_note", overlays)
        self.assertNotRegex(json.dumps(data, ensure_ascii=False), SECRET_LEAK_RE)

    def test_mock_still_demo_default(self) -> None:
        p1 = json.loads(MOCK_P1.read_text(encoding="utf-8"))
        p5 = json.loads(MOCK_P5.read_text(encoding="utf-8"))
        self.assertTrue(p1["demo"])
        self.assertTrue(p5["demo"])
        self.assertTrue(p1["read_only"])
        self.assertTrue(p5["read_only"])

    def test_projector_write_roundtrip(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "project_command_center_live_v1", PROJECTOR
        )
        self.assertIsNotNone(spec)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        data = mod.project_page("p1", case_ref="demo_phase")
        self.assertTrue(data["ok"])
        self.assertEqual(data["data_source"], "live_projection")
        self.assertFalse(data["demo"])
        op = data["operator_fields"]
        self.assertEqual(list(op["fields"]), list(P89_KEYS))

    def test_runbook_and_ticket_non_claims(self) -> None:
        rb = RUNBOOK.read_text(encoding="utf-8")
        tk = TICKET.read_text(encoding="utf-8")
        for needle in (
            "source=live",
            "apply_phase_pct=false",
            "≠ Grafana",
            "≠ Round-2",
            "fallback",
        ):
            self.assertIn(needle, rb)
        self.assertIn("apply_phase_pct: false", tk)
        self.assertIn("≠ Operator prod", tk)


if __name__ == "__main__":
    unittest.main()
