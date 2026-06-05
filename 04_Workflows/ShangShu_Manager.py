# ShangShu_Manager.py — 尚書省 V1（系統入口 / 執行引擎）
# 調用中書省 → 執行任務（script / API / migration）→ 門下省審核 → 更新 Status.json → 工部入庫。

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_workflows = os.path.dirname(os.path.abspath(__file__))
_agents_core = os.path.normpath(os.path.join(_workflows, "..", "02_Agents_Core"))
for _p in (_agents_core, _workflows):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bridge_agency  # noqa: E402
from MenXia_Audit import LogAuditResult, MenXia_Audit  # noqa: E402
from ZhongShu_Planner import PlanDocument, Task, ZhongShu_Planner  # noqa: E402


def _load_base_agent():
    agents_core = os.path.normpath(os.path.join(_workflows, "..", "02_Agents_Core"))
    if agents_core not in sys.path:
        sys.path.insert(0, agents_core)
    from Base_Agent import AgentStatus, Base_Agent  # type: ignore

    return Base_Agent, AgentStatus


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _merge_status_json(dest_root: str, patch: Dict[str, Any]) -> None:
    from gov_paths import resolve_artifact_under_root

    path = resolve_artifact_under_root(dest_root, "status_json")
    data: Dict[str, Any] = {}
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data.update(patch)
    data["updated_at"] = _utc_iso()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class ShangShu_Manager:
    def __init__(self, *, dest_root: Optional[str] = None) -> None:
        Base_Agent, AgentStatus = _load_base_agent()
        self._AgentStatus = AgentStatus
        from gov_paths import get_department_under, get_tang_gov_root

        self.dest_root = os.path.abspath(dest_root or get_tang_gov_root())
        self.agent = Base_Agent(dest_root=self.dest_root, department="尚書省", agent_name="ShangShu_Manager")
        self.planner = ZhongShu_Planner(dest_root=self.dest_root)
        self.auditor = MenXia_Audit(dest_root=self.dest_root)
        self.exports_final = os.path.join(
            get_department_under(self.dest_root, "06_Exports_Output"),
            "final",
        )

    def _run_script_task(self, task: Task) -> Dict[str, Any]:
        """執行 02_Agents_Core 內 .py：優先 task.extra['script_path']，否則若 input_path 為 .py 則直接執行。"""
        script = task.extra.get("script_path")
        if not script and task.input_path.lower().endswith(".py"):
            script = task.input_path
        if not script or not os.path.isfile(script):
            self.agent.log_event(event="task_script_skip", task_id=task.task_id, reason="no_script")
            return {"ok": True, "skipped": True, "task_id": task.task_id}

        proc = subprocess.run(
            [sys.executable, script],
            cwd=os.path.dirname(script) or self.dest_root,
            capture_output=True,
            text=True,
            timeout=3600,
        )
        ok = proc.returncode == 0
        return {
            "ok": ok,
            "task_id": task.task_id,
            "returncode": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-2000:],
            "stderr_tail": (proc.stderr or "")[-2000:],
        }

    def _run_api_task(self, task: Task, goal: str) -> Dict[str, Any]:
        payload = {
            "goal": goal,
            "task": asdict(task),
            "user_input": task.extra.get("user_input", {}),
        }
        return bridge_agency.run_api_task(payload)

    def _run_migration_task(self, task: Task) -> Dict[str, Any]:
        from gov_paths import get_department_under

        mm = os.path.join(get_department_under(self.dest_root, "04_Workflows"), "Migration_Manager.py")
        if not os.path.isfile(mm):
            return {"ok": False, "error": "Migration_Manager.py not found"}
        # V1：僅示例；實際搬遷請帶足參數
        self.agent.log_event(event="migration_task_stub", task_id=task.task_id)
        return {"ok": True, "note": "migration placeholder; configure CLI in extra", "task_id": task.task_id}

    def run(self, goal: str, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        主流程：create_plan → 執行 tasks → MenXia 審核 → Status → 工部交付 JSON。
        """
        user_input = dict(user_input or {})
        self.agent.set_status(self._AgentStatus.Running.value, reason="shangshu_run_start")
        self.agent.log_event(event="shangshu_run", goal=goal)

        _merge_status_json(
            self.dest_root,
            {
                "pipeline_status": "Running",
                "shangshu_run_id": self.agent.run_id,
                "migration_last_wave": None,
            },
        )

        plan: PlanDocument = self.planner.create_plan(goal, user_input=user_input)
        results: List[Dict[str, Any]] = []
        task_errors = 0

        for task in plan.tasks:
            if task.agent_type.upper() == "API":
                r = self._run_api_task(task, goal)
            elif task.agent_type == "migration":
                r = self._run_migration_task(task)
            elif task.agent_type == "noop":
                r = {"ok": True, "noop": True, "task_id": task.task_id}
            else:
                r = self._run_script_task(task)

            results.append({"task": asdict(task), "result": r})
            if not r.get("ok", False):
                task_errors += 1

        final_audit: LogAuditResult = self.auditor.audit_after_execution(self.agent.run_id, task_errors=task_errors)

        if final_audit.terminate_pipeline or final_audit.veto:
            self.agent.set_status(self._AgentStatus.Manual.value, reason="shangshu_veto")
            _merge_status_json(
                self.dest_root,
                {"pipeline_status": "Manual", "shangshu_run_id": self.agent.run_id},
            )
            return {
                "ok": False,
                "terminated": True,
                "plan_id": plan.plan_id,
                "audit": asdict(final_audit),
                "results": results,
            }

        os.makedirs(self.exports_final, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = os.path.join(self.exports_final, f"shangshu_delivery_{plan.plan_id}_{ts}.json")
        delivery = {
            "plan_id": plan.plan_id,
            "goal": goal,
            "manager_run_id": self.agent.run_id,
            "results": results,
            "audit": {
                "latest_run_id": final_audit.latest_run_id,
                "failure_count": final_audit.failure_count,
                "veto": final_audit.veto,
            },
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(delivery, f, ensure_ascii=False, indent=2)

        self.agent.set_status(self._AgentStatus.Success.value, reason="shangshu_complete")
        _merge_status_json(
            self.dest_root,
            {
                "pipeline_status": "Success",
                "shangshu_run_id": self.agent.run_id,
                "migration_last_wave": {
                    "status": "Success",
                    "run_id": self.agent.run_id,
                    "plan_id": plan.plan_id,
                    "export_path": out_path,
                    "updated_at": _utc_iso(),
                },
            },
        )

        return {
            "ok": True,
            "plan_id": plan.plan_id,
            "export_path": out_path,
            "audit": asdict(final_audit),
            "results": results,
        }


def main() -> None:
    from gov_paths import get_tang_gov_root

    dest = os.environ.get("TANG_GOV_ROOT", "").strip() or get_tang_gov_root()
    goal = os.environ.get("SHANGSHU_GOAL", "default")
    mgr = ShangShu_Manager(dest_root=dest)
    print(json.dumps(mgr.run(goal, user_input={}), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
