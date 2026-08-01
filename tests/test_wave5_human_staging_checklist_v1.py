"""Parse/structure checks for Wave 5 human/staging checklist YAML (doc-only).

Does NOT claim Round-2 GO, prod unblock, or env edits.
"""

from __future__ import annotations

import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_YAML_PATH = (
    _REPO_ROOT
    / "04_Workflows"
    / "plans"
    / "wave5-human-staging-checklist-2026-07-13.yaml"
)
_MD_PATH = (
    _REPO_ROOT
    / "04_Workflows"
    / "plans"
    / "wave5-human-staging-checklist-2026-07-13.md"
)

_REQUIRED_TOP = frozenset(
    {
        "schema_version",
        "ticket_id",
        "non_claims",
        "items",
        "adjacent_gaps",
        "post_unblock_ai_ticket",
    }
)
_REQUIRED_ITEM = frozenset(
    {
        "id",
        "title",
        "owner",
        "status",
        "blocked_reason",
        "prerequisites",
        "acceptance_evidence",
        "next_eng_ticket",
        "must_human_or_infra",
    }
)
_H_IDS = ("H1", "H2", "H3", "H4", "H5")
_NON_CLAIMS_REQUIRED = frozenset(
    {
        "not_unblocked",
        "not_round2_go",
        "not_prod_go",
        "not_env_secret_edit",
        "not_dashboard_authorize",
    }
)


def _load_yaml() -> dict:
    text = _YAML_PATH.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise unittest.SkipTest("pyyaml not installed; skip YAML parse test") from exc
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise AssertionError("checklist YAML root must be a mapping")
    return data


class TestWave5HumanStagingChecklistV1(unittest.TestCase):
    def test_yaml_parse_and_h1_h5_shape(self) -> None:
        self.assertTrue(_YAML_PATH.is_file(), f"missing {_YAML_PATH.as_posix()}")
        data = _load_yaml()
        missing_top = _REQUIRED_TOP - set(data)
        self.assertFalse(missing_top, f"missing top keys: {sorted(missing_top)}")
        self.assertEqual(data["schema_version"], "wave5_human_staging_checklist_v1")
        self.assertEqual(data["ticket_id"], "WAVE5-human-staging-checklist-v1")

        non_claims = set(data["non_claims"])
        self.assertTrue(
            _NON_CLAIMS_REQUIRED <= non_claims,
            f"non_claims missing {_NON_CLAIMS_REQUIRED - non_claims}",
        )

        items = data["items"]
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 5)
        by_id = {row["id"]: row for row in items}
        self.assertEqual(tuple(by_id), _H_IDS)
        _ALLOWED_STATUS = frozenset(
            {"blocked", "approved_pending_countersign", "approved"}
        )
        for hid in _H_IDS:
            row = by_id[hid]
            missing = _REQUIRED_ITEM - set(row)
            self.assertFalse(missing, f"{hid} missing fields: {sorted(missing)}")
            self.assertIn(
                row["status"],
                _ALLOWED_STATUS,
                f"{hid} status={row['status']!r} not in {_ALLOWED_STATUS}",
            )
            # H2–H5 must stay blocked until human/infra deliver; H1 may advance.
            if hid != "H1":
                self.assertEqual(row["status"], "blocked", f"{hid} must remain blocked")
            self.assertTrue(row["must_human_or_infra"] is True)
            self.assertTrue(row["blocked_reason"] or hid == "H1")
            self.assertTrue(row["next_eng_ticket"])
            self.assertIsInstance(row["prerequisites"], list)
            self.assertIsInstance(row["acceptance_evidence"], list)
            self.assertGreaterEqual(len(row["acceptance_evidence"]), 1)
        h1 = by_id["H1"]
        if h1["status"] in {"approved_pending_countersign", "approved"}:
            self.assertIn("approval_id", h1)
            self.assertTrue(str(h1["approval_id"]).startswith("GOV-DUAL-APPROVAL-"))

        post = data["post_unblock_ai_ticket"]
        self.assertEqual(
            post["id"], "WH-P7-NOTIF-staging-integration-execute-v2"
        )

    def test_markdown_companion_exists_and_anchors(self) -> None:
        self.assertTrue(_MD_PATH.is_file(), f"missing {_MD_PATH.as_posix()}")
        text = _MD_PATH.read_text(encoding="utf-8")
        for needle in (
            "non_claims",
            "**H1**",
            "**H5**",
            "Round-2",
            "prod browser",
            "Z-ENV",
            "WH-P7-NOTIF-staging-integration-execute-v2",
        ):
            self.assertIn(needle, text, f"checklist md missing anchor: {needle}")


if __name__ == "__main__":
    unittest.main()
