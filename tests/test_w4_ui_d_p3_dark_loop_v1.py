"""W4-UI-D: P3 dark execution loop static shell + mock contract tests."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MOCK_PATH = REPO_ROOT / "ui" / "command_center" / "mock" / "p3_dark_loop_v1.json"
P3_HTML = REPO_ROOT / "ui" / "command_center" / "p3.html"
P1_MOCK = REPO_ROOT / "ui" / "command_center" / "mock" / "p1_overview_v1.json"
P5_MOCK = REPO_ROOT / "ui" / "command_center" / "mock" / "p5_swimlane_v1.json"
P4_MOCK = REPO_ROOT / "ui" / "command_center" / "mock" / "p4_command_desk_v1.json"
SHELL_JS = REPO_ROOT / "ui" / "command_center" / "js" / "shell.js"
SHELL_CSS = REPO_ROOT / "ui" / "command_center" / "css" / "shell.css"
INDEX = REPO_ROOT / "ui" / "command_center" / "index.html"
RUNBOOK = REPO_ROOT / "docs" / "wave4-ui-d-p3-dark-loop-runbook-v1.md"
UNIFIED_P3 = REPO_ROOT / "docs" / "ui-templates" / "unified_P3.png"

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


class TestW4UiDP3DarkLoopV1(unittest.TestCase):
    def test_shell_assets_exist(self) -> None:
        for path in (MOCK_PATH, P3_HTML, SHELL_JS, SHELL_CSS, INDEX, RUNBOOK, UNIFIED_P3):
            self.assertTrue(path.is_file(), f"missing: {path.relative_to(REPO_ROOT)}")

    def test_mock_ok_and_schema_stable(self) -> None:
        data = json.loads(MOCK_PATH.read_text(encoding="utf-8"))
        self.assertTrue(data["ok"])
        self.assertEqual(data["schema_version"], "w4_ui_d_p3_dark_loop_v1")
        self.assertTrue(data["demo"])
        self.assertTrue(data["read_only"])
        self.assertEqual(data["host"], "ui/command_center")
        self.assertEqual(data["secrets_policy"], "mask_only")
        self.assertEqual(data["secrets"]["api_key_display"], "••••••••")
        self.assertGreaterEqual(len(data["modules"]), 7)
        stages = data["loop_flow"]["stages"]
        self.assertGreaterEqual(len(stages), 4)
        stage_ids = {s["id"] for s in stages}
        for required in ("ministries_out", "dark_exec", "knowledge", "delivery"):
            self.assertIn(required, stage_ids)
        self.assertGreaterEqual(len(data["side_monitor"]["cards"]), 1)
        self.assertTrue(any(c["id"] == "retries" for c in data["side_monitor"]["cards"]))
        self.assertTrue(any(c["id"] == "alerts" for c in data["side_monitor"]["cards"]))
        self.assertIn("non_claims", data)

    def test_operator_fields_p89_subset(self) -> None:
        data = json.loads(MOCK_PATH.read_text(encoding="utf-8"))
        op = data["operator_fields"]
        self.assertTrue(op["ok"])
        self.assertEqual(list(op["fields"]), list(P89_KEYS))
        for row in op["rows"]:
            for key in P89_KEYS:
                self.assertIn(key, row)

    def test_html_has_required_landmarks(self) -> None:
        html = P3_HTML.read_text(encoding="utf-8")
        for needle in (
            'id="brand-title"',
            'id="p3-modules"',
            'id="p3-loop-stages"',
            'id="p3-side-cards"',
            'id="p3-footer-strip"',
            'id="operator-fields"',
            'id="secret-mask"',
            "mock/p3_dark_loop_v1.json",
        ):
            self.assertIn(needle, html)

    def test_nav_p1_p5_p4_p3_cross_link(self) -> None:
        p3 = json.loads(MOCK_PATH.read_text(encoding="utf-8"))
        p1 = json.loads(P1_MOCK.read_text(encoding="utf-8"))
        p5 = json.loads(P5_MOCK.read_text(encoding="utf-8"))
        p4 = json.loads(P4_MOCK.read_text(encoding="utf-8"))
        for data in (p3, p1, p5, p4):
            nav = {item["id"]: item for item in data["nav"]}
            self.assertEqual(nav["p1"]["href"], "p1.html")
            self.assertEqual(nav["p5"]["href"], "p5.html")
            self.assertEqual(nav["p4"]["href"], "p4.html")
            self.assertEqual(nav["p3"]["href"], "p3.html")
            self.assertNotIn("deferred", nav["p3"])
        p3_nav = {item["id"]: item for item in p3["nav"]}
        self.assertTrue(p3_nav["p3"]["active"])
        self.assertEqual(p3_nav["p2"]["href"], "p2.html")
        self.assertNotIn("deferred", p3_nav["p2"])
        self.assertEqual(p3_nav["settings"]["href"], "settings.html")
        self.assertNotIn("deferred", p3_nav["settings"])
        index = INDEX.read_text(encoding="utf-8")
        self.assertIn("p3.html", index)

    def test_shell_js_exports_render_p3(self) -> None:
        js = SHELL_JS.read_text(encoding="utf-8")
        self.assertIn("renderP3", js)
        self.assertIn("maskSecrets", js)

    def test_no_secret_plaintext_in_shell_assets(self) -> None:
        blobs = [
            MOCK_PATH.read_text(encoding="utf-8"),
            SHELL_JS.read_text(encoding="utf-8"),
            P3_HTML.read_text(encoding="utf-8"),
        ]
        for blob in blobs:
            self.assertIsNone(SECRET_LEAK_RE.search(blob), "possible secret leak in shell asset")

    def test_runbook_declares_host_and_open_url(self) -> None:
        text = RUNBOOK.read_text(encoding="utf-8")
        self.assertIn("ui/command_center", text)
        self.assertIn("p3.html", text)
        self.assertIn("http.server", text)
        self.assertIn("8765", text)
        self.assertIn("Grafana", text)
        self.assertIn("apply_phase_pct=false", text)
        self.assertIn("index.html", text)


if __name__ == "__main__":
    unittest.main()
