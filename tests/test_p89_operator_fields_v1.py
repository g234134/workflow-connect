"""Tests for P8.9 operator fields projection (Wave 2)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from delivery.p89_operator_fields_v1 import (
    SCHEMA_VERSION,
    UI_FIELD_KEYS,
    load_handler_event_index,
    project_operator_fields,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestP89OperatorFieldsProjection(unittest.TestCase):
    def test_handler_registry_includes_webhook_t4(self) -> None:
        index = load_handler_event_index(repo_root=REPO_ROOT)
        self.assertIn("delivery.bundle_ready", index)
        self.assertIn("webhook_dispatch_v1", index["delivery.bundle_ready"])

    def test_empty_case_ref_fails_closed(self) -> None:
        result = project_operator_fields("", repo_root=REPO_ROOT)
        self.assertFalse(result["ok"])
        self.assertEqual(result["schema_version"], SCHEMA_VERSION)
        self.assertEqual(result["t4_alignment"]["ticket"], "WD-P7-T2")
        self.assertEqual(result["t4_alignment"]["status"], "landed")

    def test_fixture_projection_five_ui_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outbox = root / "outbox"
            outbox.mkdir(parents=True)
            (outbox / "notification_events.jsonl").write_text(
                json.dumps(
                    {
                        "event_id": "evt-op-1",
                        "event_type": "delivery.bundle_ready",
                        "case_ref": "demo_phase",
                        "emitted_at": "2026-07-13T00:00:00Z",
                        "source": {"step_id": "S12"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            feedback = outbox / "feedback" / "demo_phase" / "acks"
            feedback.mkdir(parents=True)
            (feedback / "evt-op-1_bundle_ready_log_v1.json").write_text(
                json.dumps(
                    {
                        "schema_version": "feedback_ack_v1",
                        "feedback_kind": "downstream_ack",
                        "event_id": "evt-op-1",
                        "handler_id": "bundle_ready_log_v1",
                        "status": "received",
                        "message": "ok",
                        "recorded_at": "2026-07-13T00:00:01Z",
                    }
                ),
                encoding="utf-8",
            )
            dlq = outbox / "notification_dlq"
            dlq.mkdir(parents=True)
            (dlq / "events.jsonl").write_text(
                json.dumps(
                    {
                        "schema_id": "notification_webhook_dlq_v1",
                        "event_id": "evt-op-1",
                        "case_ref": "demo_phase",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            # Point consumer at temp outbox by copying handlers from repo
            handlers_src = REPO_ROOT / "routing" / "notification_handlers_v1.yaml"
            handlers_dst = root / "routing"
            handlers_dst.mkdir(parents=True)
            handlers_dst.joinpath("notification_handlers_v1.yaml").write_text(
                handlers_src.read_text(encoding="utf-8"), encoding="utf-8"
            )

            result = project_operator_fields(
                "demo_phase",
                repo_root=root,
                outbox_root_override=str(outbox),
                dlq_path_override=str(dlq / "events.jsonl"),
                handlers_path=handlers_dst / "notification_handlers_v1.yaml",
            )
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["fields"], list(UI_FIELD_KEYS))
            self.assertEqual(result["count"], 1)
            row = result["rows"][0]
            self.assertEqual(row["event_id"], "evt-op-1")
            self.assertEqual(row["ack_status"], "acked")
            self.assertEqual(row["handler_id"], "bundle_ready_log_v1")
            self.assertTrue(row["dispatch_registry_hit"])
            self.assertTrue(row["dlq_flag"])
            self.assertEqual(result["t4_alignment"]["alias"], "P8.9-T4")

    def test_no_dlq_file_means_dlq_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outbox = root / "outbox"
            outbox.mkdir(parents=True)
            (outbox / "notification_events.jsonl").write_text(
                json.dumps(
                    {
                        "event_id": "evt-clean",
                        "event_type": "run.completed",
                        "case_ref": "demo_phase",
                        "emitted_at": "2026-07-13T00:00:00Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            handlers_src = REPO_ROOT / "routing" / "notification_handlers_v1.yaml"
            handlers_dst = root / "routing"
            handlers_dst.mkdir(parents=True)
            handlers_dst.joinpath("notification_handlers_v1.yaml").write_text(
                handlers_src.read_text(encoding="utf-8"), encoding="utf-8"
            )
            result = project_operator_fields(
                "demo_phase",
                repo_root=root,
                outbox_root_override=str(outbox),
                dlq_path_override=str(outbox / "missing_dlq.jsonl"),
                handlers_path=handlers_dst / "notification_handlers_v1.yaml",
            )
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["rows"][0]["dlq_flag"], False)
            self.assertEqual(result["rows"][0]["ack_status"], "pending_ack")


if __name__ == "__main__":
    unittest.main()
