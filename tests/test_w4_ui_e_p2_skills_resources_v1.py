"""W4-UI-E: P2 skills & resources static shell + mock contract tests."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MOCK_PATH = REPO_ROOT / "ui" / "command_center" / "mock" / "p2_skills_resources_v1.json"
P2_HTML = REPO_ROOT / "ui" / "command_center" / "p2.html"
SETTINGS_HTML = REPO_ROOT / "ui" / "command_center" / "settings.html"
P1_MOCK = REPO_ROOT / "ui" / "command_center" / "mock" / "p1_overview_v1.json"
P5_MOCK = REPO_ROOT / "ui" / "command_center" / "mock" / "p5_swimlane_v1.json"
P4_MOCK = REPO_ROOT / "ui" / "command_center" / "mock" / "p4_command_desk_v1.json"
P3_MOCK = REPO_ROOT / "ui" / "command_center" / "mock" / "p3_dark_loop_v1.json"
SHELL_JS = REPO_ROOT / "ui" / "command_center" / "js" / "shell.js"
SHELL_CSS = REPO_ROOT / "ui" / "command_center" / "css" / "shell.css"
INDEX = REPO_ROOT / "ui" / "command_center" / "index.html"
RUNBOOK = REPO_ROOT / "docs" / "wave4-ui-e-p2-skills-resources-runbook-v1.md"
UNIFIED_P2 = REPO_ROOT / "docs" / "ui-templates" / "unified_P2.png"

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

MASK_ONLY_RE = re.compile(r"\*+|•+")


class TestW4UiEP2SkillsResourcesV1(unittest.TestCase):
    def test_shell_assets_exist(self) -> None:
        for path in (
            MOCK_PATH,
            P2_HTML,
            SETTINGS_HTML,
            SHELL_JS,
            SHELL_CSS,
            INDEX,
            RUNBOOK,
            UNIFIED_P2,
        ):
            self.assertTrue(path.is_file(), f"missing: {path.relative_to(REPO_ROOT)}")

    def test_mock_ok_and_schema_stable(self) -> None:
        data = json.loads(MOCK_PATH.read_text(encoding="utf-8"))
        self.assertTrue(data["ok"])
        self.assertEqual(data["schema_version"], "w4_ui_e_p2_skills_resources_v1")
        self.assertTrue(data["demo"])
        self.assertTrue(data["read_only"])
        self.assertEqual(data["host"], "ui/command_center")
        self.assertEqual(data["secrets_policy"], "mask_only")
        self.assertEqual(data["secrets"]["api_key_display"], "••••••••")
        self.assertGreaterEqual(len(data["skill_ministries"]), 6)
        self.assertGreaterEqual(len(data["skill_module_map"]["rows"]), 1)
        gov = data["resource_governance"]
        self.assertIn("deploy_mix", gov)
        self.assertIn("api_today", gov)
        self.assertIn("token_today", gov)
        vault_rows = gov["key_vault"]["rows"]
        self.assertGreaterEqual(len(vault_rows), 1)
        for row in vault_rows:
            self.assertTrue(MASK_ONLY_RE.search(row["name_masked"]))
            self.assertNotRegex(row["name_masked"], r"sk-[A-Za-z0-9]{8,}")
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
        html = P2_HTML.read_text(encoding="utf-8")
        for needle in (
            'id="brand-title"',
            'id="p2-skill-cards"',
            'id="p2-skill-map"',
            'id="p2-resource-top"',
            'id="p2-cloud-bars"',
            'id="p2-key-vault"',
            'id="operator-fields"',
            'id="secret-mask"',
            "mock/p2_skills_resources_v1.json",
        ):
            self.assertIn(needle, html)

    def test_nav_all_five_pages_cross_link(self) -> None:
        mocks = [
            json.loads(MOCK_PATH.read_text(encoding="utf-8")),
            json.loads(P1_MOCK.read_text(encoding="utf-8")),
            json.loads(P5_MOCK.read_text(encoding="utf-8")),
            json.loads(P4_MOCK.read_text(encoding="utf-8")),
            json.loads(P3_MOCK.read_text(encoding="utf-8")),
        ]
        for data in mocks:
            nav = {item["id"]: item for item in data["nav"]}
            self.assertEqual(nav["p1"]["href"], "p1.html")
            self.assertEqual(nav["p2"]["href"], "p2.html")
            self.assertEqual(nav["p3"]["href"], "p3.html")
            self.assertEqual(nav["p4"]["href"], "p4.html")
            self.assertEqual(nav["p5"]["href"], "p5.html")
            self.assertEqual(nav["settings"]["href"], "settings.html")
            for page_id in ("p1", "p2", "p3", "p4", "p5", "settings"):
                self.assertNotIn("deferred", nav[page_id])
        p2_nav = {item["id"]: item for item in mocks[0]["nav"]}
        self.assertTrue(p2_nav["p2"]["active"])
        index = INDEX.read_text(encoding="utf-8")
        for href in ("p1.html", "p2.html", "p3.html", "p4.html", "p5.html", "settings.html"):
            self.assertIn(href, index)
        self.assertIn("settings.html", SETTINGS_HTML.read_text(encoding="utf-8"))
        settings_html = SETTINGS_HTML.read_text(encoding="utf-8")
        self.assertIn("薄頁", settings_html)
        self.assertIn("mock/settings_v1.json", settings_html)
        settings_mock = REPO_ROOT / "ui" / "command_center" / "mock" / "settings_v1.json"
        self.assertTrue(settings_mock.is_file())
        settings_data = json.loads(settings_mock.read_text(encoding="utf-8"))
        self.assertEqual(settings_data.get("page_kind"), "settings_thin")
        self.assertIn("mask_only", settings_data.get("secrets_policy", ""))


    def test_shell_js_exports_render_p2(self) -> None:
        js = SHELL_JS.read_text(encoding="utf-8")
        self.assertIn("renderP2", js)
        self.assertIn("maskSecrets", js)
        self.assertIn("renderNavOnly", js)

    def test_no_secret_plaintext_in_shell_assets(self) -> None:
        blobs = [
            MOCK_PATH.read_text(encoding="utf-8"),
            SHELL_JS.read_text(encoding="utf-8"),
            P2_HTML.read_text(encoding="utf-8"),
            SETTINGS_HTML.read_text(encoding="utf-8"),
        ]
        for blob in blobs:
            self.assertIsNone(SECRET_LEAK_RE.search(blob), "possible secret leak in shell asset")

    def test_runbook_declares_host_and_open_url(self) -> None:
        text = RUNBOOK.read_text(encoding="utf-8")
        self.assertIn("ui/command_center", text)
        self.assertIn("p2.html", text)
        self.assertIn("http.server", text)
        self.assertIn("8765", text)
        self.assertIn("Grafana", text)
        self.assertIn("apply_phase_pct=false", text)
        self.assertIn("index.html", text)
        self.assertIn("金鑰", text)


if __name__ == "__main__":
    unittest.main()
