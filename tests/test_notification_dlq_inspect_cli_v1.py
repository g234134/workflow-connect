"""Unittest for notification DLQ inspect CLI (WH-P7-NOTIF-DLQ-inspect-cli-impl-v1)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE = _REPO_ROOT / "tests" / "fixtures" / "notification_dlq" / "events.jsonl"
_CLI = _REPO_ROOT / "tools" / "inspect_notification_dlq_v1.py"

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.inspect_notification_dlq_v1 import inspect_list, inspect_stats, main  # noqa: E402


class TestNotificationDlqInspectCliV1(unittest.TestCase):
    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, str(_CLI), *args]
        return subprocess.run(
            cmd,
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_uc1_list_json_basic(self) -> None:
        result = inspect_list(_FIXTURE, limit=10)
        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 4)
        self.assertEqual(len(result["entries"]), 4)

        first = result["entries"][0]
        for field in (
            "dlq_written_at",
            "timestamp",
            "event_id",
            "event_type",
            "endpoint",
            "tier",
            "attempt_count",
            "retry_exhausted",
            "last_error",
            "http_status",
        ):
            self.assertIn(field, first)

        proc = self._run_cli(
            "list",
            "--dlq-path",
            str(_FIXTURE),
            "--json",
            "--limit",
            "10",
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["count"], 4)
        self.assertEqual(payload["entries"][0]["event_id"], "evt-prod-004")

    def test_uc2_filter_by_tier_endpoint_code(self) -> None:
        tier_result = inspect_list(_FIXTURE, tier="prod", limit=20)
        self.assertEqual(tier_result["count"], 2)
        self.assertTrue(all(entry["tier"] == "prod" for entry in tier_result["entries"]))

        endpoint_result = inspect_list(
            _FIXTURE,
            tier="staging",
            endpoint="hooks.staging.example.com",
            limit=20,
        )
        self.assertEqual(endpoint_result["count"], 1)
        self.assertEqual(endpoint_result["entries"][0]["event_id"], "evt-staging-002")

        code_result = inspect_list(_FIXTURE, tier="prod", http_status=500, limit=20)
        self.assertEqual(code_result["count"], 1)
        self.assertEqual(code_result["entries"][0]["event_id"], "evt-prod-003")

        proc = self._run_cli(
            "list",
            "--dlq-path",
            str(_FIXTURE),
            "--tier",
            "prod",
            "--code",
            "500",
            "--json",
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["entries"][0]["http_status"], 500)

    def test_uc3_stats_json(self) -> None:
        result = inspect_stats(_FIXTURE)
        self.assertTrue(result["ok"])
        self.assertEqual(result["total_count"], 4)
        self.assertEqual(result["by_http_status"]["500"], 2)
        self.assertEqual(result["by_http_status"]["503"], 1)
        self.assertEqual(result["by_http_status"]["null"], 1)
        self.assertEqual(
            result["by_endpoint"]["https://api.customer.com/webhooks/gov"],
            2,
        )
        self.assertEqual(result["by_tier"]["prod"], 2)

        proc = self._run_cli(
            "stats",
            "--dlq-path",
            str(_FIXTURE),
            "--tier",
            "staging",
            "--endpoint",
            "hooks.staging.example.com",
            "--json",
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["total_count"], 1)
        self.assertEqual(payload["by_http_status"]["500"], 1)
        self.assertIn("hooks.staging.example.com", next(iter(payload["by_endpoint"])))

    def test_uc4_missing_or_empty_file(self) -> None:
        missing = _REPO_ROOT / "tests" / "fixtures" / "notification_dlq" / "missing.jsonl"
        result = inspect_list(missing, limit=5)
        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["entries"], [])

        stats_result = inspect_stats(missing)
        self.assertTrue(stats_result["ok"])
        self.assertEqual(stats_result["total_count"], 0)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as handle:
            empty_path = Path(handle.name)

        try:
            empty_result = inspect_list(empty_path, limit=5)
            self.assertTrue(empty_result["ok"])
            self.assertEqual(empty_result["count"], 0)

            proc = self._run_cli(
                "list",
                "--dlq-path",
                str(missing),
                "--json",
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["count"], 0)
        finally:
            empty_path.unlink(missing_ok=True)

    def test_skips_invalid_json_line(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as handle:
            handle.write(_FIXTURE.read_text(encoding="utf-8"))
            handle.write("not-json\n")
            mixed_path = Path(handle.name)

        try:
            result = inspect_list(mixed_path, limit=10)
            self.assertTrue(result["ok"])
            self.assertEqual(result["count"], 4)
        finally:
            mixed_path.unlink(missing_ok=True)

    def test_default_subcommand_is_list(self) -> None:
        exit_code = main(
            [
                "--dlq-path",
                str(_FIXTURE),
                "--json",
                "--limit",
                "1",
            ]
        )
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
