"""Unit tests for Wave 7 artifact storage and path governance."""

from __future__ import annotations

import json
import re
import unittest
import uuid
from pathlib import Path
from tests._repo_bootstrap import bootstrap_gov_core_tests

bootstrap_gov_core_tests(test_file=Path(__file__))

from core.schemas.envelope_v2 import _LEAKY_PATH_RE  # noqa: E402
from core.wave7_artifact_storage import (  # noqa: E402
    compute_inputs_fingerprint,
    store_wave7_artifacts,
    w6_logical_ref,
)

SHA_A = "a" * 64
SHA_B = "b" * 64


def _repo_root() -> Path:
    from core.repo_paths import find_repo_root

    root = find_repo_root(start=Path(__file__).resolve())
    assert root is not None
    return root


def _leak_scan(payload: object) -> list[str]:
    hits: list[str] = []
    if isinstance(payload, dict):
        for v in payload.values():
            hits.extend(_leak_scan(v))
    elif isinstance(payload, list):
        for item in payload:
            hits.extend(_leak_scan(item))
    elif (
        isinstance(payload, str)
        and not payload.startswith("w6://delivery/")
        and _LEAKY_PATH_RE.search(payload)
    ):
        hits.append(payload)
    return hits


def _sample_envelope(*, file_id: str, sha: str) -> dict[str, object]:
    return {
        "schema_version": "2.0",
        "file_id": file_id,
        "content_sha256": sha,
        "clean_status": "ok",
        "name": f"{file_id}.py",
        "extension": ".py",
        "original_type": "python_source",
        "size_bytes": 64,
        "encoding": "utf-8",
        "stored_logical_path": f"cleaned_full/{file_id}.py.json",
        "content_summary": {"line_count": 2, "char_count": 20, "imports": []},
        "groq_used": False,
        "groq_reason": None,
        "parse_strategy": "ast",
        "warnings": [],
    }


def _sample_manifest(job_id: str) -> dict[str, object]:
    return {
        "schema_version": "manifest_v2.0",
        "job_id": job_id,
        "sku": "CLEAN-BASIC",
        "accepted_units": 2,
        "billing_units": {"U": 2, "L": 0},
        "rows": [],
    }


class TestWave7ArtifactStorage(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = _repo_root()
        self.job_id = f"w7-test-{uuid.uuid4().hex[:10]}"
        scratch = self.repo / "05_Temp_Cache" / "staging" / "wave7" / "_ut_artifact_storage"
        scratch.mkdir(parents=True, exist_ok=True)
        self.test_delivery = scratch / "delivery"
        self.test_staging = scratch / "staging"
        self.test_delivery.mkdir(parents=True, exist_ok=True)
        self.test_staging.mkdir(parents=True, exist_ok=True)
        delivery_rel = self.test_delivery.relative_to(self.repo).as_posix()
        staging_rel = self.test_staging.relative_to(self.repo).as_posix()
        self.paths_resolved = {
            "cleaned_full": "05_Temp_Cache/cleaned_full",
            "staging_root": staging_rel,
            "delivery_root": delivery_rel,
        }

    def _store(self, **kwargs: object) -> dict[str, object]:
        return store_wave7_artifacts(
            self.job_id,
            "CLEAN-BASIC",
            paths_resolved=self.paths_resolved,
            repo_root=self.repo,
            **kwargs,  # type: ignore[arg-type]
        )

    def test_create_success(self) -> None:
        manifest = _sample_manifest(self.job_id)
        envelopes = [
            _sample_envelope(file_id="f1", sha=SHA_A),
            _sample_envelope(file_id="f2", sha=SHA_B),
        ]
        result = self._store(
            envelopes=envelopes,
            manifest=manifest,
            report={"schema_version": "wave7_report_draft_v0.1", "summary": {"accepted_units": 2}},
            mode="create",
        )

        self.assertTrue(result["ok"], result.get("message"))
        self.assertFalse(result["idempotent_hit"])
        self.assertIsNone(result["error_code"])
        refs = result["artifact_refs"]
        self.assertEqual(refs["manifest"], w6_logical_ref(self.job_id, "manifest"))
        self.assertEqual(refs["report_json"], w6_logical_ref(self.job_id, "report_json"))
        self.assertIn("deliverables", refs)
        self.assertIn("envelopes_dir", refs)

        paths = result["paths_logical"]
        manifest_abs = self.repo / paths["manifest"]
        self.assertTrue(manifest_abs.is_file())
        self.assertTrue((self.repo / paths["report_json"]).is_file())
        self.assertTrue((self.repo / paths["envelopes_dir"] / "f1.json").is_file())
        self.assertTrue((self.repo / paths["envelopes_dir"] / "f2.json").is_file())
        self.assertEqual(_leak_scan(result), [])

    def test_idempotent_rerun_same_inputs(self) -> None:
        manifest = _sample_manifest(self.job_id)
        envelopes = [_sample_envelope(file_id="f1", sha=SHA_A)]
        kwargs = {"envelopes": envelopes, "manifest": manifest, "mode": "create"}

        first = self._store(**kwargs)
        self.assertTrue(first["ok"])
        self.assertFalse(first["idempotent_hit"])

        manifest_mtime = (self.repo / first["paths_logical"]["manifest"]).stat().st_mtime

        second = self._store(**kwargs)
        self.assertTrue(second["ok"])
        self.assertTrue(second["idempotent_hit"])
        self.assertEqual(second["message"], "idempotent_hit")

        manifest_mtime_after = (self.repo / second["paths_logical"]["manifest"]).stat().st_mtime
        self.assertEqual(manifest_mtime, manifest_mtime_after)

        fp = compute_inputs_fingerprint(
            envelopes=envelopes,
            manifest=manifest,
            report=None,
            sku="CLEAN-BASIC",
            mode="create",
        )
        gen_path = self.repo / second["paths_logical"]["generation"]
        with gen_path.open(encoding="utf-8") as f:
            gen = json.load(f)
        self.assertEqual(gen["fingerprint"], fp)

    def test_io_error_recovery_failed_and_quarantine(self) -> None:
        manifest = _sample_manifest(self.job_id)
        envelopes = [_sample_envelope(file_id="f1", sha=SHA_A)]
        call_count = {"n": 0}

        def flaky_writer(path: Path, text: str) -> None:
            call_count["n"] += 1
            if path.name == "manifest.json":
                raise OSError("simulated disk full")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

        result = self._store(
            envelopes=envelopes,
            manifest=manifest,
            mode="create",
            json_writer=flaky_writer,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "io_error")
        paths = result["paths_logical"]
        self.assertIn("failed", paths)
        failed_audit = self.repo / paths["failed_audit"]
        self.assertTrue(failed_audit.is_file())
        with failed_audit.open(encoding="utf-8") as f:
            audit = json.load(f)
        self.assertIn("simulated", audit["reason"])
        self.assertEqual(audit["job_id"], self.job_id)

        quar_audit = self.repo / paths["quarantine"] / "recovery_audit.json"
        self.assertTrue(quar_audit.is_file())
        self.assertEqual(_leak_scan(result), [])

    def test_return_structure_has_no_absolute_path_leak(self) -> None:
        manifest = _sample_manifest(self.job_id)
        result = self._store(envelopes=[], manifest=manifest, mode="create")
        self.assertTrue(result["ok"])
        blob = json.dumps(result, ensure_ascii=False)
        self.assertIsNone(re.search(r"^[a-zA-Z]:[/\\]", blob, flags=re.MULTILINE))
        self.assertNotIn("file://", blob)
        for ref in result["artifact_refs"].values():
            self.assertTrue(ref.startswith("w6://delivery/"))
        for path in result["paths_logical"].values():
            self.assertNotRegex(path, r"^[a-zA-Z]:[/\\]")


if __name__ == "__main__":
    unittest.main()
