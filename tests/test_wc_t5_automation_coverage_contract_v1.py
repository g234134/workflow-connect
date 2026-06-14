"""Contract tests for WC-T5 Control Plane automation coverage SSOT."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONTRACT = _REPO_ROOT / "docs" / "wave_c" / "WC_T5_automation_coverage_contract.md"

# Authoritative path_id registry — must match contract JSON appendix 1:1.
IMPLEMENTED_PATH_IDS = frozenset(
    {
        "wc.m2.eligibility.check",
        "wc.m2.eligibility.check_role",
        "wc.m2.eligibility.serve",
        "wc.m2.dispatch.cards_generate",
        "wc.m2.dispatch.refresh_and_cards",
        "wc.m2.dispatch.eligibility_gate_warn",
        "wc.m2.dispatch.force_eligibility_override",
        "wc.m2.comms.state_transition",
        "wc.m2.comms.state_transition_dry_run",
        "wc.m2.order.create",
        "wc.m2.order.lookup",
        "wc.m2.order.list",
        "wc.m2.loop.order_handoff",
        "wc.m2.comms.order_event",
        "wc.m2.state.write_ticket",
        "wc.m2.chat.open_cursor",
    }
)

_CLI_ENTRIES = frozenset(
    {
        "scripts/run_ticket_eligibility.py",
        "scripts/run_dispatch_cards.py",
        "scripts/run_ticket_state_update_with_comms.py",
        "scripts/run_order_intake.py",
        "scripts/run_control_plane_order_handoff.py",
    }
)

_REQUIRED_PATH_KEYS = frozenset(
    {
        "path_id",
        "description",
        "automation_tier",
        "risk_class",
        "cli_entry",
        "verification_command",
    }
)

_VALID_TIERS = frozenset({"auto", "HITL", "forbidden"})
_VALID_RISK = frozenset({"low", "medium", "high"})


def _extract_json_appendix(text: str) -> dict:
    marker = "## 附录 A"
    start = text.find(marker)
    if start < 0:
        raise ValueError("contract missing appendix section")
    fence = "```json"
    json_start = text.find(fence, start)
    if json_start < 0:
        raise ValueError("contract missing JSON appendix block")
    body_start = json_start + len(fence)
    body_end = text.find("```", body_start)
    if body_end < 0:
        raise ValueError("contract JSON appendix not closed")
    return json.loads(text[body_start:body_end].strip())


class TestWcT5AutomationCoverageContractV1(unittest.TestCase):
    """Structural contract: path registry, tiers, CLI entrypoints, no orphans."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = _CONTRACT.read_text(encoding="utf-8")
        cls.registry = _extract_json_appendix(cls.text)
        cls.paths = cls.registry["paths"]
        cls.path_ids = [p["path_id"] for p in cls.paths]

    def test_contract_file_exists(self) -> None:
        self.assertTrue(_CONTRACT.is_file())

    def test_required_sections_present(self) -> None:
        for section in (
            "## 1. 目的",
            "## 2. 默认只读与写入边界",
            "## 3. 禁止假设（必读）",
            "## 4. 路径矩阵",
            "## 附录 A",
        ):
            self.assertIn(section, self.text, msg=f"missing {section}")

    def test_schema_version(self) -> None:
        self.assertEqual(self.registry["schema_version"], "wc_t5_paths_v0.1")

    def test_minimum_path_count(self) -> None:
        self.assertGreaterEqual(len(self.paths), 8)

    def test_path_ids_no_duplicates(self) -> None:
        self.assertEqual(len(self.path_ids), len(set(self.path_ids)))

    def test_path_ids_match_implementation_registry(self) -> None:
        contract_ids = set(self.path_ids)
        self.assertEqual(
            contract_ids,
            IMPLEMENTED_PATH_IDS,
            msg=(
                f"orphan in contract: {contract_ids - IMPLEMENTED_PATH_IDS}; "
                f"orphan in impl: {IMPLEMENTED_PATH_IDS - contract_ids}"
            ),
        )

    def test_each_path_has_required_fields_and_valid_enums(self) -> None:
        for path in self.paths:
            missing = _REQUIRED_PATH_KEYS - path.keys()
            self.assertFalse(missing, msg=f"{path.get('path_id')}: missing {missing}")
            self.assertIn(path["automation_tier"], _VALID_TIERS)
            self.assertIn(path["risk_class"], _VALID_RISK)

    def test_auto_paths_have_verification_command(self) -> None:
        for path in self.paths:
            if path["automation_tier"] != "auto":
                continue
            cmd = path.get("verification_command")
            self.assertTrue(cmd, msg=f"{path['path_id']}: auto path needs verification_command")

    def test_forbidden_paths_have_no_cli_entry(self) -> None:
        for path in self.paths:
            if path["automation_tier"] != "forbidden":
                continue
            self.assertIsNone(path["cli_entry"], msg=path["path_id"])
            self.assertIsNone(path["verification_command"], msg=path["path_id"])

    def test_cli_entry_scripts_exist(self) -> None:
        for path in self.paths:
            entry = path.get("cli_entry")
            if not entry:
                continue
            self.assertIn(entry, _CLI_ENTRIES, msg=path["path_id"])
            script = _REPO_ROOT / entry
            self.assertTrue(script.is_file(), msg=f"missing script {entry}")

    def test_four_m2_cli_scripts_covered(self) -> None:
        covered = {p["cli_entry"] for p in self.paths if p.get("cli_entry")}
        self.assertTrue(_CLI_ENTRIES <= covered)

    def test_markdown_table_lists_all_path_ids(self) -> None:
        for path_id in IMPLEMENTED_PATH_IDS:
            self.assertIn(f"`{path_id}`", self.text, msg=f"matrix missing {path_id}")


if __name__ == "__main__":
    unittest.main()
