"""W4-UI-A: P1 static shell + operator-fields mock contract tests."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MOCK_PATH = REPO_ROOT / "ui" / "command_center" / "mock" / "p1_overview_v1.json"
P1_HTML = REPO_ROOT / "ui" / "command_center" / "p1.html"
SHELL_JS = REPO_ROOT / "ui" / "command_center" / "js" / "shell.js"
SHELL_CSS = REPO_ROOT / "ui" / "command_center" / "css" / "shell.css"
PAGE01 = REPO_ROOT / "docs" / "ui-templates" / "page01.html"
RUNBOOK = REPO_ROOT / "docs" / "wave4-ui-a-static-shell-runbook-v1.md"
UNIFIED_P1 = REPO_ROOT / "docs" / "ui-templates" / "unified_P1.png"

P89_KEYS = (
    "event_id",
    "ack_status",
    "handler_id",
    "dispatch_registry_hit",
    "dlq_flag",
)

# Obvious secret-like tokens that must not appear in shell assets.
SECRET_LEAK_RE = re.compile(
    r"(sk-[A-Za-z0-9]{16,}|api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}|Bearer\s+[A-Za-z0-9\-._~+/]{12,})",
    re.IGNORECASE,
)


class TestW4UiAStaticShellV1(unittest.TestCase):
    def test_shell_assets_exist(self) -> None:
        for path in (MOCK_PATH, P1_HTML, SHELL_JS, SHELL_CSS, PAGE01, RUNBOOK, UNIFIED_P1):
            self.assertTrue(path.is_file(), f"missing: {path.relative_to(REPO_ROOT)}")

    def test_mock_ok_and_schema_stable(self) -> None:
        data = json.loads(MOCK_PATH.read_text(encoding="utf-8"))
        self.assertTrue(data["ok"])
        self.assertEqual(data["schema_version"], "w4_ui_a_p1_overview_v1")
        self.assertTrue(data["demo"])
        self.assertTrue(data["read_only"])
        self.assertEqual(data["host"], "ui/command_center")
        self.assertEqual(data["secrets_policy"], "mask_only")
        self.assertEqual(data["secrets"]["api_key_display"], "••••••••")
        self.assertIn("kpis", data)
        self.assertGreaterEqual(len(data["kpis"]), 8)
        self.assertIn("flow", data)
        self.assertIn("departments", data)
        self.assertIn("dark_modules", data)
        self.assertIn("activity", data)
        self.assertIn("non_claims", data)

    def test_operator_fields_p89_five_keys(self) -> None:
        data = json.loads(MOCK_PATH.read_text(encoding="utf-8"))
        op = data["operator_fields"]
        self.assertTrue(op["ok"])
        self.assertEqual(op["schema_version"], "p89_operator_fields_v1")
        self.assertTrue(op["read_only"])
        self.assertEqual(list(op["fields"]), list(P89_KEYS))
        self.assertGreaterEqual(op["count"], 1)
        self.assertEqual(len(op["rows"]), op["count"])
        for row in op["rows"]:
            for key in P89_KEYS:
                self.assertIn(key, row)

    def test_phase_field_drafts_marked_skeleton(self) -> None:
        data = json.loads(MOCK_PATH.read_text(encoding="utf-8"))
        drafts = data["phase_field_drafts"]
        for name in ("p75_intake_gate", "p5_health", "p8_delivery"):
            self.assertEqual(drafts[name]["status"], "skeleton")
            self.assertIn("fields", drafts[name])

    def test_html_has_required_landmarks(self) -> None:
        html = P1_HTML.read_text(encoding="utf-8")
        for needle in (
            'id="brand-title"',
            'id="kpi-grid"',
            'id="flow-row"',
            'id="dept-status"',
            'id="dark-status"',
            'id="activity-log"',
            'id="operator-fields"',
            'id="secret-mask"',
            "mock/p1_overview_v1.json",
        ):
            self.assertIn(needle, html)

    def test_page01_points_at_command_center_assets(self) -> None:
        html = PAGE01.read_text(encoding="utf-8")
        self.assertIn("../../ui/command_center/css/shell.css", html)
        self.assertIn("../../ui/command_center/js/shell.js", html)
        self.assertIn("../../ui/command_center/mock/p1_overview_v1.json", html)

    def test_no_secret_plaintext_in_shell_assets(self) -> None:
        blobs = [
            MOCK_PATH.read_text(encoding="utf-8"),
            SHELL_JS.read_text(encoding="utf-8"),
            P1_HTML.read_text(encoding="utf-8"),
            PAGE01.read_text(encoding="utf-8"),
        ]
        for blob in blobs:
            self.assertIsNone(SECRET_LEAK_RE.search(blob), "possible secret leak in shell asset")

    def test_runbook_declares_host_and_red_lines(self) -> None:
        text = RUNBOOK.read_text(encoding="utf-8")
        self.assertIn("ui/command_center", text)
        self.assertIn("Grafana", text)
        self.assertRegex(text, r"≠.*Grafana|Grafana")
        self.assertIn("金鑰", text)
        self.assertIn("apply_phase_pct=false", text)


if __name__ == "__main__":
    unittest.main()
