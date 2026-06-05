# ZhongShu_Planner.py — 中書省 V1
# 掃描 05_Temp_Cache，依 goal 產出 Task 列表並寫入 current_plan.json。

from __future__ import annotations

import json
import os
import sys
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


def _load_base_agent():
    here = os.path.dirname(os.path.abspath(__file__))
    agents_core = os.path.normpath(os.path.join(here, "..", "02_Agents_Core"))
    if agents_core not in sys.path:
        sys.path.insert(0, agents_core)
    from Base_Agent import AgentStatus, Base_Agent  # type: ignore

    return Base_Agent, AgentStatus


@dataclass
class Task:
    """單一任務：Agent 類型、輸入路徑、預期輸出。"""

    task_id: str
    agent_type: str  # script | API | migration | noop
    input_path: str
    expected_output: str
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlanDocument:
    goal: str
    plan_id: str
    temp_cache_scan: Dict[str, Any]
    tasks: List[Task]
    user_input: Dict[str, Any] = field(default_factory=dict)


class ZhongShu_Planner:
    def __init__(self, *, dest_root: Optional[str] = None) -> None:
        Base_Agent, AgentStatus = _load_base_agent()
        self._AgentStatus = AgentStatus
        from gov_paths import get_department_under, get_tang_gov_root, resolve_artifact_under_root

        self.dest_root = os.path.abspath(dest_root or get_tang_gov_root())
        self.agent = Base_Agent(dest_root=self.dest_root, department="中書省", agent_name="ZhongShu_Planner")
        self.workflows_dir = get_department_under(self.dest_root, "04_Workflows")
        self.temp_cache_root = get_department_under(self.dest_root, "05_Temp_Cache")
        self.exports_final_dir = os.path.join(
            get_department_under(self.dest_root, "06_Exports_Output"),
            "final",
        )
        self._plan_path = resolve_artifact_under_root(self.dest_root, "current_plan")

    def _scan_temp_cache(self) -> Dict[str, Any]:
        files: List[str] = []
        if not os.path.isdir(self.temp_cache_root):
            return {"root": self.temp_cache_root, "files": [], "count": 0}
        for dp, _, fns in os.walk(self.temp_cache_root):
            for fn in fns:
                files.append(os.path.join(dp, fn))
        files.sort()
        return {"root": self.temp_cache_root, "files": files, "count": len(files)}

    def _scan_quarantine_json(self) -> Dict[str, Any]:
        """專為『數據清算戰役』：僅掃描 05_Temp_Cache/quarantine 下之 .json。"""
        qdir = os.path.join(self.temp_cache_root, "quarantine")
        files: List[str] = []
        if os.path.isdir(qdir):
            for dp, _, fns in os.walk(qdir):
                for fn in fns:
                    if fn.lower().endswith(".json"):
                        files.append(os.path.join(dp, fn))
        files.sort()
        return {"root": qdir, "files": files, "count": len(files)}

    def create_plan(self, goal: str, user_input: Optional[Dict[str, Any]] = None) -> PlanDocument:
        """
        依 goal 與 05_Temp_Cache 現況產出計畫，並寫入 04_Workflows/current_plan.json。
        """
        self.agent.set_status(self._AgentStatus.Running.value, reason="zhongshu_create_plan")
        self.agent.log_event(event="create_plan_start", goal=goal)

        user_input = dict(user_input or {})
        scan = self._scan_temp_cache()
        plan_id = f"plan_{uuid.uuid4().hex[:12]}"
        tasks: List[Task] = []

        # 規則化拆解（V1）：可依 goal 擴充；預設對掃到的每個檔案建立後續處理任務
        g = (goal or "").strip().lower()
        file_list = scan["files"]

        if g in ("api", "agency", "dify", "chat"):
            tasks.append(
                Task(
                    task_id="t_api_1",
                    agent_type="API",
                    input_path=scan["root"],
                    expected_output=os.path.join(self.exports_final_dir, "agency_response.json"),
                    extra={"goal": goal, "user_input": user_input},
                )
            )
        elif g in ("migrate", "migration", "搬遷"):
            tasks.append(
                Task(
                    task_id="t_mig_1",
                    agent_type="migration",
                    input_path=scan["root"],
                    expected_output=os.path.join(self.workflows_dir, "migration_done.flag"),
                    extra={"hint": "可改為呼叫 Migration_Manager 參數"},
                )
            )
        elif any(k in g for k in ("liquidate", "清算", "quarantine")) or g in (
            "liquidate_quarantine_json",
            "數據清算戰役",
        ):
            from gov_paths import get_department_under

            qjson = self._scan_quarantine_json()
            scan = qjson  # 紀錄入計畫之 temp_cache_scan 改為過濾後檢視
            agents_core_dir = get_department_under(self.dest_root, "02_Agents_Core")
            exports_dir = get_department_under(self.dest_root, "06_Exports_Output")
            rag_dir = get_department_under(self.dest_root, "03_RAG_Database")
            liq_script = os.path.join(agents_core_dir, "Liquidation_Agent.py")
            tasks.append(
                Task(
                    task_id="t_liquidation_dry_run",
                    agent_type="liquidation",
                    input_path=qjson["root"],
                    expected_output=os.path.join(exports_dir, "reports", "liquidation_preview_<run_id>.json"),
                    extra={
                        "mode": "dry_run",
                        "script_path": liq_script,
                        "extensions": [".json"],
                        "scope": "quarantine",
                        "file_count": qjson["count"],
                        "file_list_preview": qjson["files"][:20],
                        "destinations": {
                            "junk_log": os.path.join(exports_dir, "Archive"),
                            "important_data": os.path.join(rag_dir, "C2_核心知識庫"),
                        },
                        "menxia_policy": {
                            "veto_min_failures": 2,
                            "metric": "json_format_error+task_failed",
                        },
                        "physical_move_blocked": True,
                        "note": "簽押前嚴禁物理位移；execute_signed() 須由尚書省另行調用。",
                    },
                )
            )
        else:
            # 通用：每個暫存檔一個 script 任務（占位：由尚書省解析要跑哪支 .py）
            if not file_list:
                tasks.append(
                    Task(
                        task_id="t_noop",
                        agent_type="noop",
                        input_path="",
                        expected_output="",
                        extra={"reason": "05_Temp_Cache 無檔案"},
                    )
                )
            else:
                for i, fp in enumerate(file_list):
                    tasks.append(
                        Task(
                            task_id=f"t_script_{i+1}",
                            agent_type="script",
                            input_path=fp,
                            expected_output=os.path.join(
                                self.exports_final_dir,
                                f"out_{os.path.basename(fp)}.json",
                            ),
                            extra={"goal": goal},
                        )
                    )

        for t in tasks:
            t.extra.setdefault("user_input", user_input)

        doc = PlanDocument(
            goal=goal,
            plan_id=plan_id,
            temp_cache_scan=scan,
            tasks=tasks,
            user_input=user_input,
        )

        os.makedirs(self.workflows_dir, exist_ok=True)
        os.makedirs(self.exports_final_dir, exist_ok=True)
        plan_path = self._plan_path
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "goal": doc.goal,
                    "plan_id": doc.plan_id,
                    "temp_cache_scan": doc.temp_cache_scan,
                    "tasks": [asdict(t) for t in doc.tasks],
                    "user_input": doc.user_input,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        self.agent.log_event(event="create_plan_done", plan_id=plan_id, task_count=len(tasks), path=plan_path)
        self.agent.set_status(self._AgentStatus.Success.value, reason="zhongshu_plan_written")
        return doc


def create_plan(
    goal: str,
    dest_root: Optional[str] = None,
    user_input: Optional[Dict[str, Any]] = None,
) -> PlanDocument:
    """模組級便捷函式（與類方法語意一致）。"""
    return ZhongShu_Planner(dest_root=dest_root).create_plan(goal, user_input=user_input)
