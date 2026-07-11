"""Unit tests for Wave 7 runner environment bootstrap."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from tests._repo_bootstrap import bootstrap_gov_core_tests

bootstrap_gov_core_tests(test_file=Path(__file__))

from core.wave7_runner_env_bootstrap import (  # noqa: E402
    WAVE7_PATH_KEYS,
    bootstrap_runner_env,
    resolve_wave7_logical_paths,
)


def _repo_root() -> Path:
    from core.repo_paths import find_repo_root

    root = find_repo_root(start=Path(__file__).resolve())
    assert root is not None
    return root


def _load_map() -> dict:
    mp = _repo_root() / "04_Workflows" / "Master_Map.json"
    with mp.open(encoding="utf-8") as f:
        return json.load(f)


class TestWave7RunnerEnvBootstrap(unittest.TestCase):
    def test_bootstrap_check_success(self) -> None:
        result = bootstrap_runner_env(
            check=True,
            start=Path(__file__).resolve(),
        )
        self.assertTrue(result["ok"], result.get("message"))
        self.assertEqual(result["repo_root_logical"], "tang_gov_root")
        for key in WAVE7_PATH_KEYS:
            self.assertIn(key, result["paths_resolved"])
            self.assertNotRegex(
                result["paths_resolved"][key],
                r"^[a-zA-Z]:[/\\]",
                msg=f"absolute path leak in {key}",
            )

    def test_resolve_paths_logical_segments(self) -> None:
        repo = _repo_root()
        m = _load_map()
        paths, errors = resolve_wave7_logical_paths(m, repo_root=repo)
        self.assertEqual(errors, [])
        self.assertIn("cleaned_full", paths["cleaned_full"])
        self.assertIn("staging/wave7", paths["staging_root"])
        self.assertIn("wave7/delivery", paths["delivery_root"])

    def test_missing_wave7_paths_ok_false(self) -> None:
        m = _load_map()
        broken = copy.deepcopy(m)
        broken.pop("wave7_paths", None)
        result = bootstrap_runner_env(
            check=False,
            master_map=broken,
            start=Path(__file__).resolve(),
        )
        self.assertFalse(result["ok"])
        self.assertIn("wave7_paths", result.get("message", ""))

    def test_missing_path_key_ok_false(self) -> None:
        m = _load_map()
        broken = copy.deepcopy(m)
        spec = dict(broken["wave7_paths"])
        spec.pop("delivery_root")
        broken["wave7_paths"] = spec
        result = bootstrap_runner_env(
            check=False,
            master_map=broken,
            start=Path(__file__).resolve(),
        )
        self.assertFalse(result["ok"])
        self.assertIn("delivery_root", result.get("message", ""))

    def test_invalid_sub_type_ok_false(self) -> None:
        m = _load_map()
        broken = copy.deepcopy(m)
        broken["wave7_paths"]["staging_root"] = {
            "department": "05_Temp_Cache",
            "sub_type": "nonexistent_subdir_xyz",
        }
        result = bootstrap_runner_env(
            check=False,
            master_map=broken,
            start=Path(__file__).resolve(),
        )
        self.assertFalse(result["ok"])
        msg = result.get("message", "")
        self.assertTrue("staging_root" in msg or "nonexistent" in msg.lower())

    def test_dry_run_without_check(self) -> None:
        result = bootstrap_runner_env(
            dry_run=True,
            check=False,
            start=Path(__file__).resolve(),
        )
        self.assertTrue(result["ok"])
        self.assertTrue(
            any("dry_run" in w for w in result.get("warnings") or []),
        )

    def test_check_fails_when_schema_file_missing(self) -> None:
        m = _load_map()
        broken = copy.deepcopy(m)
        boot = dict(broken["wave7_bootstrap"])
        schemas = dict(boot["schema_files"])
        schemas["envelope_v2"] = "01_Environments/python_venvs/gov_core_system/shared/schemas/__missing__.json"
        boot["schema_files"] = schemas
        broken["wave7_bootstrap"] = boot
        result = bootstrap_runner_env(
            check=True,
            master_map=broken,
            start=Path(__file__).resolve(),
        )
        self.assertFalse(result["ok"])
        self.assertIn("schema", result.get("message", "").lower())


if __name__ == "__main__":
    unittest.main()
