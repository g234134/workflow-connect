# MenXia_Audit.py — 門下省 V1
# 讀取 03_RAG_Database/C3_Logs，依「最新 Run_ID」統計失敗；失敗計數 >= 2 → 封駁（Manual + 終止信號）。

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


def _load_base_agent():
    here = os.path.dirname(os.path.abspath(__file__))
    agents_core = os.path.normpath(os.path.join(here, "..", "02_Agents_Core"))
    if agents_core not in sys.path:
        sys.path.insert(0, agents_core)
    from Base_Agent import AgentStatus, Base_Agent  # type: ignore

    return Base_Agent, AgentStatus


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class LogAuditResult:
    latest_run_id: Optional[str]
    failure_count: int
    veto: bool  # 封駁：failure_count >= 2
    terminate_pipeline: bool  # 尚書省應立即停止
    sample_events: List[Dict[str, Any]]


class MenXia_Audit:
    """門下省：合規檢查、封駁、寫入 Status.json。"""

    VETO_MIN_FAILURES = 2  # 失敗計數 >= 2 → 封駁

    def __init__(self, *, dest_root: Optional[str] = None) -> None:
        Base_Agent, AgentStatus = _load_base_agent()
        self._AgentStatus = AgentStatus
        from gov_paths import get_department_under, get_tang_gov_root, resolve_artifact_under_root

        self.dest_root = os.path.abspath(dest_root or get_tang_gov_root())
        self.agent = Base_Agent(dest_root=self.dest_root, department="門下省", agent_name="MenXia_Audit")
        rag = get_department_under(self.dest_root, "03_RAG_Database")
        self.logs_dir = os.path.join(rag, "C3_Logs")
        self.status_path = resolve_artifact_under_root(self.dest_root, "status_json")

    def _iter_log_entries(self) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        if not os.path.isdir(self.logs_dir):
            return rows
        for fn in os.listdir(self.logs_dir):
            if not fn.endswith(".jsonl"):
                continue
            fp = os.path.join(self.logs_dir, fn)
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rows.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            except OSError:
                continue
        return rows

    @staticmethod
    def _is_failure_entry(o: Dict[str, Any]) -> bool:
        st = str(o.get("status", ""))
        ev = str(o.get("event", ""))
        if st == "Failed":
            return True
        if ev in ("copy_failed", "pipeline_halted", "audit_fail", "status_json_merge_failed"):
            return True
        if "fail" in ev.lower() and ev.lower() != "copy_skipped_exists":
            return True
        return False

    def resolve_latest_run_id(
        self,
        entries: Optional[List[Dict[str, Any]]] = None,
        *,
        exclude_departments: Optional[Tuple[str, ...]] = None,
    ) -> Optional[str]:
        """以日誌欄位 timestamp 最新者決定 Run_ID（預設排除門下省，避免審核程序自身變成『最新』）。"""
        ex = exclude_departments if exclude_departments is not None else ("門下省",)
        rows = entries if entries is not None else self._iter_log_entries()
        best_ts = ""
        best_rid: Optional[str] = None
        for o in rows:
            if o.get("department") in ex:
                continue
            ts = str(o.get("timestamp", ""))
            rid = o.get("run_id")
            if not rid:
                continue
            if ts >= best_ts:
                best_ts = ts
                best_rid = str(rid)
        return best_rid

    def count_failures_for_run(self, run_id: str, entries: Optional[List[Dict[str, Any]]] = None) -> Tuple[int, List[Dict[str, Any]]]:
        rows = entries if entries is not None else self._iter_log_entries()
        n = 0
        samples: List[Dict[str, Any]] = []
        for o in rows:
            if str(o.get("run_id")) != run_id:
                continue
            if self._is_failure_entry(o):
                n += 1
                if len(samples) < 5:
                    samples.append({"event": o.get("event"), "status": o.get("status"), "timestamp": o.get("timestamp")})
        return n, samples

    def audit_c3_logs(self) -> LogAuditResult:
        """檢查 C3_Logs 最新 Run_ID 的失敗計數。"""
        self.agent.set_status(self._AgentStatus.Running.value, reason="menxia_audit_c3")
        self.agent.log_event(event="menxia_c3_audit_start")

        entries = self._iter_log_entries()
        latest = self.resolve_latest_run_id(entries, exclude_departments=("門下省",))
        if not latest:
            res = LogAuditResult(
                latest_run_id=None,
                failure_count=0,
                veto=False,
                terminate_pipeline=False,
                sample_events=[],
            )
            self.agent.log_event(event="menxia_no_logs")
            self.agent.set_status(self._AgentStatus.Success.value, reason="menxia_no_run_id")
            return res

        fc, samples = self.count_failures_for_run(latest, entries)
        veto = fc >= self.VETO_MIN_FAILURES
        terminate = veto

        res = LogAuditResult(
            latest_run_id=latest,
            failure_count=fc,
            veto=veto,
            terminate_pipeline=terminate,
            sample_events=samples,
        )

        self.agent.log_event(
            event="menxia_c3_audit_done",
            latest_run_id=latest,
            failure_count=fc,
            veto=veto,
        )

        if veto:
            self.apply_manual_veto(f"封駁：Run_ID {latest} 失敗計數 {fc} >= {self.VETO_MIN_FAILURES}")
            self.agent.set_status(self._AgentStatus.Manual.value, reason="menxia_fengbo")
        else:
            self.agent.set_status(self._AgentStatus.Success.value, reason="menxia_audit_pass")

        return res

    def apply_manual_veto(self, reason: str) -> None:
        """強制將 Status.json 標為 Manual（封駁）。"""
        try:
            data: Dict[str, Any] = {}
            if os.path.isfile(self.status_path):
                with open(self.status_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data.setdefault("schema_version", "1.0")
            data["pipeline_status"] = "Manual"
            data["menxia_veto"] = {
                "reason": reason,
                "updated_at": _utc_iso(),
            }
            data["updated_at"] = _utc_iso()
            os.makedirs(os.path.dirname(self.status_path), exist_ok=True)
            with open(self.status_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.agent.log_event(event="menxia_status_write_failed", error=str(e))

    def audit_after_execution(self, manager_run_id: str, task_errors: int) -> LogAuditResult:
        """
        任務全部完畢後：讀 C3 最新（非門下省）Run_ID 的失敗數；若 >=2 或 task_errors >=2 → 封駁。
        """
        self.agent.set_status(self._AgentStatus.Running.value, reason="menxia_post_pipeline")
        self.agent.log_event(event="menxia_post_audit_start", manager_run_id=manager_run_id, task_errors=task_errors)

        entries = self._iter_log_entries()
        latest = self.resolve_latest_run_id(entries, exclude_departments=("門下省",))
        fc_logs, samples = (0, [])
        if latest:
            fc_logs, samples = self.count_failures_for_run(latest, entries)

        veto = fc_logs >= self.VETO_MIN_FAILURES or task_errors >= self.VETO_MIN_FAILURES
        terminate = veto

        res = LogAuditResult(
            latest_run_id=latest or manager_run_id,
            failure_count=max(fc_logs, task_errors),
            veto=veto,
            terminate_pipeline=terminate,
            sample_events=samples,
        )

        self.agent.log_event(
            event="menxia_post_audit_done",
            latest_run_id=res.latest_run_id,
            c3_failure_count=fc_logs,
            task_errors=task_errors,
            veto=veto,
        )

        if veto:
            reason = []
            if fc_logs >= self.VETO_MIN_FAILURES:
                reason.append(f"C3 Run {latest} 失敗 {fc_logs} 次")
            if task_errors >= self.VETO_MIN_FAILURES:
                reason.append(f"任務失敗 {task_errors} 次")
            self.apply_manual_veto("封駁：" + "；".join(reason))
            self.agent.set_status(self._AgentStatus.Manual.value, reason="menxia_fengbo_post")
        else:
            self.agent.set_status(self._AgentStatus.Success.value, reason="menxia_post_pass")

        return res


def audit_c3_logs(dest_root: Optional[str] = None) -> LogAuditResult:
    return MenXia_Audit(dest_root=dest_root).audit_c3_logs()
