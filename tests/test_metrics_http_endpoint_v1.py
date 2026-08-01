"""Unit tests for standard-case metrics HTTP endpoint v1 (MP-METRICS-HTTP)."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen

from hitl.checkpoints_v1 import CHECKPOINT_A_ID, write_checkpoint
from scripts.metrics_http_endpoint_v1 import get_metrics_text, serve
from tools.tabular_outbox_writer import outbox_root

_METRIC_KEYS = (
    "pending_cases_count",
    "blocked_cases_count",
    "completed_cases_count",
    "notifications_emitted_count",
    "notifications_with_pending_ack_count",
    "notifications_failed_ack_count",
)


class TestMetricsHttpEndpointV1(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)
        self.outbox = outbox_root(self.repo_root)
        self.extra = {
            "repo_root": self.repo_root,
            "outbox_root_override": str(self.outbox),
        }
        self._server = serve(
            0,
            host="127.0.0.1",
            repo_root=self.repo_root,
            outbox_root_override=str(self.outbox),
        )
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        _host, self.port = self._server.server_address

    def tearDown(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)
        self._tmpdir.cleanup()

    def _fetch(self, path: str) -> tuple[int, str]:
        with urlopen(f"http://127.0.0.1:{self.port}{path}") as resp:
            return resp.status, resp.read().decode("utf-8")

    def test_metrics_endpoint_returns_prometheus_text_for_demo_case(self) -> None:
        status, body = self._fetch("/metrics?case_ref=demo_phase")
        self.assertEqual(status, 200)
        for key in _METRIC_KEYS:
            self.assertIn(f"# HELP {key}", body)
            self.assertIn(f"# TYPE {key} gauge", body)
            self.assertIn(f'{key}{{case_ref="demo_phase"}}', body)

    def test_metrics_endpoint_respects_case_ref_query(self) -> None:
        pending_ref = "http_metrics_pending_case"
        write_checkpoint(
            {
                "schema_version": "hitl_checkpoint_v1",
                "checkpoint_id": CHECKPOINT_A_ID,
                "case_ref": pending_ref,
                "status": "awaiting_human",
                "created_at": "2026-06-19T12:00:00Z",
                "task_type": "tabular.cleaning.mvp",
                "agent_output": {"task_type": "tabular.cleaning.mvp"},
                "human_decision": None,
                "resume_context": None,
            },
            **self.extra,
        )

        status, body = self._fetch(f"/metrics?case_ref={pending_ref}")
        self.assertEqual(status, 200)
        self.assertIn(f'pending_cases_count{{case_ref="{pending_ref}"}} 1', body)
        self.assertIn(f'blocked_cases_count{{case_ref="{pending_ref}"}} 0', body)

        default_status, default_body = self._fetch("/metrics")
        self.assertEqual(default_status, 200)
        self.assertIn('case_ref="demo_phase"', default_body)
        self.assertNotIn(f'case_ref="{pending_ref}"', default_body)

    def test_get_metrics_text_surfaces_exporter_error_as_comment(self) -> None:
        with patch("scripts.metrics_http_endpoint_v1.export_std_case_metrics") as mock_export:
            mock_export.return_value = {
                "ok": False,
                "case_ref": "demo_phase",
                "message": "workflow consumer failed",
                "std_case_metrics_v1": {key: 0 for key in _METRIC_KEYS},
            }
            status, body = get_metrics_text(case_ref="demo_phase", repo_root=self.repo_root)
        self.assertEqual(status, 200)
        self.assertIn("# error: workflow consumer failed", body)
        for key in _METRIC_KEYS:
            self.assertIn(f'{key}{{case_ref="demo_phase"}} 0', body)

    def test_health_endpoint_returns_json(self) -> None:
        status, body = self._fetch("/health")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["service"], "metrics_http_endpoint_v1")

    def test_unknown_path_returns_404(self) -> None:
        with self.assertRaises(HTTPError) as ctx:
            self._fetch("/unknown")
        self.assertEqual(ctx.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
