# Base_Agent.py
# Core monitoring base class for all future agents.

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class AgentStatus(str, Enum):
    Pending = "Pending"
    Running = "Running"
    Success = "Success"
    Failed = "Failed"
    Manual = "Manual"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Base_Agent:
    """
    Requirements implemented:
      - Run_ID generation (UUID) per execution
      - Five status controls: Pending, Running, Success, Failed, Manual
      - Full-chain JSON logging to: 03_RAG_Database/C3_Logs
      - Status.json update in: 04_Workflows/Status.json (Telegram-friendly view)

    路徑：dest_root 未傳入時，由 gov_paths + Master_Map.json 動態解析（禁止寫死磁碟路徑）。
    """

    VALID_STATUSES = {s.value for s in AgentStatus}

    @classmethod
    def get_path(
        cls,
        department: str,
        sub_type: Optional[str] = None,
        *,
        dest_root: Optional[str] = None,
    ) -> str:
        """解析部門下產出路徑；sub_type 對應 Master_Map.json 的 sub_directories 邏輯鍵。"""
        from gov_paths import resolve_agent_output_path

        return resolve_agent_output_path(dest_root, department, sub_type)

    def __init__(self, *, dest_root: Optional[str] = None, department: str, agent_name: Optional[str] = None) -> None:
        if dest_root is None:
            from gov_paths import get_artifact_path, get_tang_gov_root

            self.dest_root = get_tang_gov_root()
            self._status_path = get_artifact_path("status_json")
            self._logs_dir = self.get_path("03_RAG_Database", "c3_logs", dest_root=None)
            self._latest_staging_dir = self.get_path("03_RAG_Database", "snapshots", dest_root=None)
        else:
            self.dest_root = os.path.abspath(dest_root)
            from gov_paths import resolve_artifact_under_root, resolve_agent_output_path

            self._status_path = resolve_artifact_under_root(self.dest_root, "status_json")
            self._logs_dir = resolve_agent_output_path(self.dest_root, "03_RAG_Database", "c3_logs")
            self._latest_staging_dir = resolve_agent_output_path(self.dest_root, "03_RAG_Database", "snapshots")

        self.department = department
        self.agent_name = agent_name or self.__class__.__name__

        # 1) Run_ID generated each instantiation (per run)
        self.run_id = uuid.uuid4().hex
        self.status: str = AgentStatus.Pending.value

        os.makedirs(self._logs_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self._status_path), exist_ok=True)
        os.makedirs(self._latest_staging_dir, exist_ok=True)

        self._ensure_status_file()
        self.set_status(AgentStatus.Pending.value, reason="init")

    def _ensure_status_file(self) -> None:
        if os.path.exists(self._status_path):
            return
        payload = {
            "schema_version": "1.0",
            "updated_at": _utc_now_iso(),
            "runs": [],
            "telegram_running": [],
            "business_metrics": {
                "schema_version": "1.0",
                "potential_case_sources": 0,
                "estimated_roi_rate": None,
                "inbound_watchdog": {},
            },
        }
        with open(self._status_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def _load_status_file(self) -> Dict[str, Any]:
        try:
            with open(self._status_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "schema_version": "1.0",
                "updated_at": _utc_now_iso(),
                "runs": [],
                "telegram_running": [],
                "business_metrics": {
                    "schema_version": "1.0",
                    "potential_case_sources": 0,
                    "estimated_roi_rate": None,
                    "inbound_watchdog": {},
                },
            }

    def _upsert_run_entry(self, new_status: str) -> None:
        payload = self._load_status_file()
        runs = payload.get("runs", [])

        # Upsert by run_id
        found = False
        for r in runs:
            if r.get("run_id") == self.run_id:
                r.update(
                    {
                        "status": new_status,
                        "department": self.department,
                        "agent_name": self.agent_name,
                        "updated_at": _utc_now_iso(),
                    }
                )
                found = True
                break

        if not found:
            runs.append(
                {
                    "run_id": self.run_id,
                    "department": self.department,
                    "status": new_status,
                    "agent_name": self.agent_name,
                    "created_at": _utc_now_iso(),
                    "updated_at": _utc_now_iso(),
                }
            )

        payload["runs"] = runs
        payload["updated_at"] = _utc_now_iso()
        payload["telegram_running"] = [
            {"run_id": r.get("run_id"), "department": r.get("department"), "status": r.get("status")}
            for r in runs
            if r.get("status") == AgentStatus.Running.value
        ]

        with open(self._status_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def log_event(self, *, event: str, status: Optional[str] = None, **fields: Any) -> None:
        """
        Writes one JSON object per action into the RAG 部門 C3 日誌目錄（Master_Map.sub_directories.c3_logs）：
          <logs_dir>/<Run_ID>.jsonl
        """
        entry: Dict[str, Any] = {
            "timestamp": _utc_now_iso(),
            "run_id": self.run_id,
            "department": self.department,
            "agent_name": self.agent_name,
            "event": event,
        }
        if status is not None:
            entry["status"] = status
        else:
            entry["status"] = self.status

        entry.update(fields)

        log_path = os.path.join(self._logs_dir, f"{self.run_id}.jsonl")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def set_status(self, new_status: str, *, reason: str = "") -> None:
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}")
        self.status = new_status
        self.log_event(event="status_changed", status=new_status, reason=reason)
        self._upsert_run_entry(new_status)

