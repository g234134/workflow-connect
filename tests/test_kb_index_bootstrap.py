"""Unit tests for Wave B repo index bootstrap (WAVE-B-P1-REPO-INDEX-GOV-SCOPE-LIVE)."""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from workflow_v2.kb.repo_index_bootstrap import (  # noqa: E402
    STATUS_SCHEMA,
    build_manifest,
    build_status,
    canonical_scope_digest,
    fields_from_status,
    iter_scope_files,
    load_scope_config,
    run_bootstrap,
)
from workflow_v2.kb.rag_index_smoke import run_smoke, search_manifest  # noqa: E402

_PILOT_STATUS = _REPO_ROOT / "workflow_v2/20_pilot/W3-B/index_status_W2-1.json"
_PILOT_CASE = _REPO_ROOT / "workflow_v2/20_pilot/W2-1_case/W2-1_case.md"
_SCOPE_CONFIG = _REPO_ROOT / "workflow_v2/kb/wave_b_gov_scope.json"


class TestScopeDigest(unittest.TestCase):
    def test_digest_stable(self) -> None:
        scope = json.loads(_SCOPE_CONFIG.read_text(encoding="utf-8"))
        d1 = canonical_scope_digest(scope)
        d2 = canonical_scope_digest(scope)
        self.assertEqual(d1, d2)
        self.assertEqual(len(d1), 64)


class TestFieldsFromStatus(unittest.TestCase):
    def test_succeeded_maps_to_ready(self) -> None:
        status = {
            "schema_version": STATUS_SCHEMA,
            "job_type": "repo_index_v1",
            "job_id": "job-1",
            "status": "succeeded",
            "finished_at": "2026-06-05T12:00:00Z",
            "scope": {
                "kb_index_scope_kind": "repo_subtree_list",
                "kb_index_subtree": "gov_wave_b_bootstrap",
                "kb_index_baseline_ref": "unpinned",
            },
        }
        mapped = fields_from_status(status, status_rel="workflow_v2/20_pilot/W3-B/index_status_W2-1.json")
        self.assertTrue(mapped["ok"])
        self.assertEqual(mapped["fields"]["kb_index_status"], "ready")
        self.assertEqual(mapped["fields"]["kb_index_blocker"], "-")

    def test_infra_failed_maps_to_missing_with_blocker(self) -> None:
        status = {
            "schema_version": STATUS_SCHEMA,
            "job_type": "repo_index_v1",
            "job_id": "job-2",
            "status": "failed",
            "error_type": "infra_unavailable",
            "error_message": "connection timeout",
            "scope": {},
        }
        mapped = fields_from_status(status, status_rel="index_status.json")
        self.assertTrue(mapped["ok"])
        self.assertEqual(mapped["fields"]["kb_index_status"], "missing")
        self.assertIn("infra_unavailable", mapped["fields"]["kb_index_blocker"])


class TestBootstrapIntegration(unittest.TestCase):
    def test_run_bootstrap_on_real_repo(self) -> None:
        result = run_bootstrap(_REPO_ROOT, case_id="W2-1", dry_run=True)
        self.assertTrue(result["ok"], result.get("message"))
        self.assertGreater(result["file_count"], 0)
        self.assertGreater(result["chunk_count"], 0)

    def test_committed_status_not_sample_job_id(self) -> None:
        if not _PILOT_STATUS.is_file():
            self.skipTest("index_status_W2-1.json not yet generated")
        status = json.loads(_PILOT_STATUS.read_text(encoding="utf-8"))
        self.assertEqual(status["schema_version"], STATUS_SCHEMA)
        self.assertEqual(status["status"], "succeeded")
        self.assertNotIn("sample", status["job_id"])
        summary = status.get("result_summary") or {}
        self.assertGreater(summary.get("file_count", 0), 0)
        self.assertGreater(summary.get("chunk_count", 0), 0)
        manifest_ref = str(summary.get("manifest_ref", ""))
        self.assertNotIn(".sample.", manifest_ref)

    def test_rag_smoke_agents_md(self) -> None:
        manifest_path = _REPO_ROOT / "workflow_v2/20_pilot/W3-B/index_manifest_W2-1.json"
        if not manifest_path.is_file():
            self.skipTest("manifest not yet generated — run bootstrap first")
        result = run_smoke(_REPO_ROOT, "AGENTS.md", case_id="W2-1", top_k=5)
        self.assertTrue(result["ok"], result.get("message"))
        self.assertGreaterEqual(result["hit_count"], 1)
        paths = [h["path"] for h in result["hits"]]
        self.assertTrue(any("AGENTS.md" in p for p in paths))


class TestIterScopeFiles(unittest.TestCase):
    def test_temp_mini_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "core").mkdir()
            (root / "core" / "alpha.py").write_text("print('hi')\n", encoding="utf-8")
            (root / "core" / "skip.pyc").write_bytes(b"\x00")
            scope = {
                "kb_index_subtrees": ["core"],
                "include_globs": ["*.py"],
                "exclude_dir_names": ["__pycache__"],
                "exclude_globs": ["*.pyc"],
            }
            files = list(iter_scope_files(root, scope))
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0].name, "alpha.py")

    def test_manifest_build_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "context").mkdir()
            text = "\n".join(f"line {i}" for i in range(100))
            (root / "context" / "doc.md").write_text(text, encoding="utf-8")
            scope = {
                "kb_index_subtrees": ["context"],
                "include_globs": ["*.md"],
                "exclude_dir_names": [],
                "exclude_globs": [],
            }
            manifest = build_manifest(root, case_id="T1", job_id="job-t1", scope=scope)
            self.assertEqual(manifest["summary"]["file_count"], 1)
            self.assertGreater(manifest["summary"]["chunk_count"], 1)

            hits = search_manifest(manifest, "line 50", top_k=3)
            self.assertTrue(hits["ok"])
            self.assertGreaterEqual(hits["hit_count"], 1)


class TestLoadScopeConfig(unittest.TestCase):
    def test_load_wave_b_scope(self) -> None:
        loaded = load_scope_config(_REPO_ROOT, "workflow_v2/kb/wave_b_gov_scope.json")
        self.assertTrue(loaded["ok"])
        self.assertIn("core", loaded["scope"]["kb_index_subtrees"])


class TestCaseStatusConsistency(unittest.TestCase):
    def _case_field(self, case_text: str, field: str) -> str:
        pattern = rf"\|\s*\*\*`{re.escape(field)}`\*\*\s*\|\s*`([^`]*)`\s*\|"
        match = re.search(pattern, case_text)
        self.assertIsNotNone(match, f"{field} not found in case markdown")
        return match.group(1).strip()  # type: ignore[union-attr]

    def test_w2_1_case_kb_index_matches_status_json(self) -> None:
        if not _PILOT_STATUS.is_file() or not _PILOT_CASE.is_file():
            self.skipTest("pilot status or case markdown not present")
        status = json.loads(_PILOT_STATUS.read_text(encoding="utf-8"))
        mapped = fields_from_status(
            status,
            status_rel="workflow_v2/20_pilot/W3-B/index_status_W2-1.json",
        )
        self.assertTrue(mapped["ok"])
        case_text = _PILOT_CASE.read_text(encoding="utf-8")
        for key, expected in mapped["fields"].items():
            actual = self._case_field(case_text, key)
            self.assertEqual(actual, expected, f"mismatch on {key}")


if __name__ == "__main__":
    unittest.main()
