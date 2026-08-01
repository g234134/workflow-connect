"""Regression tests for explicit profile-selection persistence."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from suggest_cleaning_profile import apply_suggested_profile, suggest_cleaning_profile  # noqa: E402


class TestSuggestCleaningProfile(unittest.TestCase):
    def test_apply_persists_selected_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp) / "case"
            raw_dir = case_dir / "raw"
            raw_dir.mkdir(parents=True)
            (raw_dir / "orders.csv").write_text("order_id,amount\nA-1,10\n", encoding="utf-8")
            (case_dir / "intake.json").write_text(
                json.dumps(
                    {
                        "case_id": "case",
                        "data_file": "raw/orders.csv",
                        "encoding": "utf-8",
                        "delimiter": ",",
                        "schema": {
                            "primary_key": "order_id",
                            "column_roles": {"order_id": "primary_key", "amount": "numeric"},
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = suggest_cleaning_profile(case_dir, repo_root=case_dir.parent)
            applied = apply_suggested_profile(case_dir, result)

            self.assertTrue(applied["ok"], applied)
            self.assertEqual(applied["applied_profile"], "generic_low_risk_profile")
            intake = json.loads((case_dir / "intake.json").read_text(encoding="utf-8"))
            self.assertEqual(intake["cleaning_profile"], "generic_low_risk_profile")


if __name__ == "__main__":
    unittest.main()
