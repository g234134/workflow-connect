"""Send adapter layer for ticket comms (WC-T2).

Default implementation writes JSON lines to a local outbox directory.
Future channels (webhook, email, Slack) implement the same CommsSender protocol.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class CommsSender(ABC):
    """Pluggable outbound adapter for ticket comms payloads."""

    @abstractmethod
    def send(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Deliver payload; return dict with ok / message / channel / artifact_path."""


class NullSender(CommsSender):
    """No-op sender for dry-run or tests."""

    def send(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "ok": True,
            "message": "dry_run_no_send",
            "channel": "null",
            "artifact_path": None,
            "ticket_id": payload.get("ticket_id"),
        }


class FileLogSender(CommsSender):
    """Append each payload as one JSON line under outbox_dir (fake sender v0.1)."""

    def __init__(self, outbox_dir: str | Path) -> None:
        self.outbox_dir = Path(outbox_dir)

    def send(self, payload: dict[str, Any]) -> dict[str, Any]:
        ticket_id = str(payload.get("ticket_id") or "unknown")
        try:
            self.outbox_dir.mkdir(parents=True, exist_ok=True)
            log_path = self.outbox_dir / "ticket_comms.jsonl"
            record = {
                "sent_at": _utc_now_iso(),
                "channel": "file_log",
                "simulated": True,
                "external_dispatch": False,
                "payload": payload,
            }
            with log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError as exc:
            return {
                "ok": False,
                "message": f"file_log_write_failed: {exc}",
                "channel": "file_log",
                "artifact_path": None,
                "ticket_id": ticket_id,
            }

        rel = self._relative_path(log_path)
        return {
            "ok": True,
            "message": "written_to_file_log",
            "channel": "file_log",
            "artifact_path": rel,
            "ticket_id": ticket_id,
        }

    def _relative_path(self, path: Path) -> str:
        raw = path.as_posix()
        for marker in ("artifacts/", "04_Workflows/"):
            if marker in raw:
                return raw[raw.index(marker) :]
        return path.name
