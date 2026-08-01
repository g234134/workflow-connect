"""Unit tests for operator backlog HTTP API v1 (P8-API)."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from hitl.checkpoints_v1 import CHECKPOINT_A_ID, write_checkpoint
from scripts.operator_http_api_v1 import get_operator_backlog, make_handler
from delivery import notification_gateway_v1 as gw
from tools.tabular_outbox_writer import outbox_root


def _append_notification(
    outbox: Path,
    *,
    case_ref: str,
    event_type: str,
    emitted_at: str | None = None,
) -> dict:
    event = gw.build_notification_event(
        event_type,
        case_ref=case_ref,
        source={"step_id": "S14"},
    )
    if emitted_at:
        event["emitted_at"] = emitted_at
    jsonl = outbox / "notification_events.jsonl"
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    with jsonl.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")
    return event


class TestOperatorHttpApiV1(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)
        self.outbox = outbox_root(self.repo_root)
        self.extra = {
            "repo_root": self.repo_root,
            "outbox_root_override": str(self.outbox),
        }
        handler = make_handler(
            self.repo_root,
            outbox_root_override=str(self.outbox),
        )
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self._tmpdir.cleanup()

    def _url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def _get_json(self, path: str) -> tuple[int, dict]:
        try:
            with urlopen(self._url(path), timeout=5) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return resp.status, body
        except HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            return exc.code, body

    def test_backlog_api_returns_json_for_pending(self) -> None:
        pending_ref = "pending_case"
        write_checkpoint(
            {
                "schema_version": "hitl_checkpoint_v1",
                "checkpoint_id": CHECKPOINT_A_ID,
                "case_ref": pending_ref,
                "status": "awaiting_human",
                "created_at": "2026-06-19T11:00:00Z",
                "task_type": "tabular.cleaning.mvp",
                "agent_output": {"task_type": "tabular.cleaning.mvp"},
                "human_decision": None,
                "resume_context": None,
            },
            **self.extra,
        )
        _append_notification(
            self.outbox,
            case_ref=pending_ref,
            event_type="checkpoint.awaiting_human",
        )

        status, body = self._get_json("/operator/backlog?status=pending")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["schema_version"], "operator_backlog_v1")
        self.assertTrue(body["read_only"])
        self.assertEqual(body["status_filter"], "pending")
        refs = {item["case_ref"] for item in body["items"]}
        self.assertIn(pending_ref, refs)

    def test_backlog_api_filters_by_case_ref(self) -> None:
        target_ref = "filter_target"
        other_ref = "filter_other"
        for ref in (target_ref, other_ref):
            write_checkpoint(
                {
                    "schema_version": "hitl_checkpoint_v1",
                    "checkpoint_id": CHECKPOINT_A_ID,
                    "case_ref": ref,
                    "status": "awaiting_human",
                    "created_at": "2026-06-19T12:00:00Z",
                    "task_type": "tabular.cleaning.mvp",
                    "agent_output": {"task_type": "tabular.cleaning.mvp"},
                    "human_decision": None,
                    "resume_context": None,
                },
                **self.extra,
            )

        status, body = self._get_json(f"/operator/backlog?case_ref={target_ref}")
        self.assertEqual(status, 200)
        self.assertEqual(len(body["items"]), 1)
        self.assertEqual(body["items"][0]["case_ref"], target_ref)

    def test_backlog_api_rejects_invalid_status(self) -> None:
        status, body = self._get_json("/operator/backlog?status=unknown")
        self.assertEqual(status, 400)
        self.assertEqual(body, {"error": "invalid status"})

    def test_get_operator_backlog_empty_returns_200(self) -> None:
        status, body = get_operator_backlog(
            status="pending",
            repo_root=self.repo_root,
            outbox_root_override=str(self.outbox),
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["items"], [])
        self.assertEqual(body["count"], 0)


if __name__ == "__main__":
    unittest.main()
