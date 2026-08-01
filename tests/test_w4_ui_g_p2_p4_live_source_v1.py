"""W4-UI-G: P2–P4 mock|live switch via shared loadPageData (thin extension of F)."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHELL_JS = REPO_ROOT / "ui" / "command_center" / "js" / "shell.js"
P2_HTML = REPO_ROOT / "ui" / "command_center" / "p2.html"
P3_HTML = REPO_ROOT / "ui" / "command_center" / "p3.html"
P4_HTML = REPO_ROOT / "ui" / "command_center" / "p4.html"
LIVE_P2 = REPO_ROOT / "ui" / "command_center" / "live" / "p2_skills_resources_v1.json"
LIVE_P3 = REPO_ROOT / "ui" / "command_center" / "live" / "p3_dark_loop_v1.json"
LIVE_P4 = REPO_ROOT / "ui" / "command_center" / "live" / "p4_command_desk_v1.json"
MOCK_P2 = REPO_ROOT / "ui" / "command_center" / "mock" / "p2_skills_resources_v1.json"
MOCK_P3 = REPO_ROOT / "ui" / "command_center" / "mock" / "p3_dark_loop_v1.json"
MOCK_P4 = REPO_ROOT / "ui" / "command_center" / "mock" / "p4_command_desk_v1.json"
PROJECTOR = REPO_ROOT / "scripts" / "project_command_center_live_v1.py"
RUNBOOK = REPO_ROOT / "docs" / "wave4-ui-g-p2-p4-live-source-runbook-v1.md"
TICKET = (
    REPO_ROOT
    / "04_Workflows"
    / "tickets"
    / "W4-UI-G-p2-p4-live-source-v1_state.md"
)

SECRET_LEAK_RE = re.compile(
    r"(sk-[A-Za-z0-9]{16,}|api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}|Bearer\s+[A-Za-z0-9\-._~+/]{12,})",
    re.IGNORECASE,
)


class TestW4UiGP2P4LiveSourceV1(unittest.TestCase):
    def test_assets_exist(self) -> None:
        for path in (
            SHELL_JS,
            P2_HTML,
            P3_HTML,
            P4_HTML,
            LIVE_P2,
            LIVE_P3,
            LIVE_P4,
            MOCK_P2,
            MOCK_P3,
            MOCK_P4,
            PROJECTOR,
            RUNBOOK,
            TICKET,
        ):
            self.assertTrue(path.is_file(), f"missing: {path.relative_to(REPO_ROOT)}")

    def test_p2_p3_p4_use_load_page_data(self) -> None:
        pages = {
            P2_HTML: ("mock/p2_skills_resources_v1.json", "live/p2_skills_resources_v1.json"),
            P3_HTML: ("mock/p3_dark_loop_v1.json", "live/p3_dark_loop_v1.json"),
            P4_HTML: ("mock/p4_command_desk_v1.json", "live/p4_command_desk_v1.json"),
        }
        for html_path, (mock_u, live_u) in pages.items():
            text = html_path.read_text(encoding="utf-8")
            self.assertIn("loadPageData", text, html_path.name)
            self.assertIn(mock_u, text, html_path.name)
            self.assertIn(live_u, text, html_path.name)

    def test_live_p2_p3_p4_contract(self) -> None:
        for path, schema_prefix in (
            (LIVE_P2, "w4_ui_g_p2"),
            (LIVE_P3, "w4_ui_g_p3"),
            (LIVE_P4, "w4_ui_g_p4"),
        ):
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(data["ok"], path.name)
            self.assertFalse(data["demo"], path.name)
            self.assertTrue(data["read_only"], path.name)
            self.assertEqual(data["data_source"], "live_projection", path.name)
            self.assertEqual(data["secrets_policy"], "mask_only", path.name)
            self.assertTrue(
                str(data.get("schema_version", "")).startswith(schema_prefix),
                path.name,
            )
            self.assertIn("operator_fields", data)
            self.assertIn("live_overlays", data)
            self.assertIn("≠ Operator prod", " ".join(data["non_claims"]))
            self.assertNotRegex(json.dumps(data, ensure_ascii=False), SECRET_LEAK_RE)

    def test_mock_still_demo_default(self) -> None:
        for path in (MOCK_P2, MOCK_P3, MOCK_P4):
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(data["demo"], path.name)
            self.assertTrue(data["read_only"], path.name)

    def test_projector_includes_p2_p4(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "project_command_center_live_v1", PROJECTOR
        )
        self.assertIsNotNone(spec)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for page in ("p2", "p3", "p4"):
            data = mod.project_page(page, case_ref="demo_phase")
            self.assertTrue(data["ok"], page)
            self.assertEqual(data["data_source"], "live_projection", page)
            self.assertFalse(data["demo"], page)

    def test_runbook_and_ticket_non_claims(self) -> None:
        rb = RUNBOOK.read_text(encoding="utf-8")
        tk = TICKET.read_text(encoding="utf-8")
        for needle in (
            "source=live",
            "apply_phase_pct=false",
            "≠ Grafana",
            "≠ Round-2",
            "loadPageData",
            "P2",
            "P3",
            "P4",
        ):
            self.assertIn(needle, rb)
        self.assertIn("apply_phase_pct: false", tk)
        self.assertIn("≠ Operator prod", tk)


if __name__ == "__main__":
    unittest.main()
