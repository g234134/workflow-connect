"""
System_Check.py — 流程部（04_Workflows）維護模式：對齊 Master_Map.sub_directories 實體資料夾。

依 Base_Agent.get_path 遍歷所有邏輯 sub_type，若實體路徑不存在則 os.makedirs 補齊。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Tuple


def _bootstrap_agents_core(dest_root: str) -> str:
    dest_root_abs = os.path.abspath(dest_root)
    mp = os.path.join(dest_root_abs, "04_Workflows", "Master_Map.json")
    if not os.path.isfile(mp):
        raise FileNotFoundError(f"Master_Map.json not found: {mp}")
    with open(mp, "r", encoding="utf-8") as f:
        m: Dict[str, Any] = json.load(f)
    dept = m.get("departments") or {}
    agents_rel = str(dept.get("02_Agents_Core", "02_Agents_Core")).replace("/", os.sep)
    return os.path.normpath(os.path.join(dest_root_abs, agents_rel))


def _load_map(dest_root: str) -> Dict[str, Any]:
    mp = os.path.join(os.path.abspath(dest_root), "04_Workflows", "Master_Map.json")
    with open(mp, "r", encoding="utf-8") as f:
        return json.load(f)


def run_system_check(*, dest_root: str, dry_run: bool = False) -> Tuple[int, int, int, List[str]]:
    """
    Returns: (total_checked, already_existed, created, messages)
    """
    agents_core = _bootstrap_agents_core(dest_root)
    if agents_core not in sys.path:
        sys.path.insert(0, agents_core)

    from Base_Agent import AgentStatus, Base_Agent  # type: ignore

    m = _load_map(dest_root)
    raw_sub = m.get("sub_directories") or {}
    if not isinstance(raw_sub, dict):
        raise TypeError("Master_Map.sub_directories must be an object")

    agent = Base_Agent(dest_root=dest_root, department="流程部", agent_name="System_Check")
    agent.set_status(AgentStatus.Running.value, reason="system_check_start")

    total = 0
    existed = 0
    created = 0
    lines: List[str] = []

    for dept_key in sorted(raw_sub.keys()):
        bucket = raw_sub[dept_key]
        if not isinstance(bucket, dict):
            msg = f"[skip] {dept_key}: sub_directories entry is not an object"
            lines.append(msg)
            agent.log_event(event="system_check_skip_dept", department_key=dept_key, reason="not_a_dict")
            continue
        for sub_type in sorted(bucket.keys()):
            total += 1
            path = Base_Agent.get_path(str(dept_key), str(sub_type), dest_root=dest_root)
            path = os.path.normpath(path)
            if os.path.isdir(path):
                existed += 1
                lines.append(f"[ok] exists: {dept_key}/{sub_type} -> {path}")
                agent.log_event(
                    event="system_check_path_ok",
                    department_key=dept_key,
                    sub_type=sub_type,
                    path=path,
                )
                continue
            if dry_run:
                lines.append(f"[dry-run] would create: {dept_key}/{sub_type} -> {path}")
                agent.log_event(
                    event="system_check_would_mkdir",
                    department_key=dept_key,
                    sub_type=sub_type,
                    path=path,
                )
                continue
            os.makedirs(path, exist_ok=True)
            created += 1
            lines.append(f"[created] {dept_key}/{sub_type} -> {path}")
            agent.log_event(
                event="system_check_mkdir",
                department_key=dept_key,
                sub_type=sub_type,
                path=path,
            )

    agent.set_status(AgentStatus.Success.value, reason="system_check_done")
    agent.log_event(
        event="system_check_summary",
        total_checked=total,
        already_existed=existed,
        created=created,
        dry_run=dry_run,
    )
    return total, existed, created, lines


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="對齊 Master_Map.sub_directories：檢查並（必要時）建立實體資料夾。",
    )
    p.add_argument(
        "--dest-root",
        default="",
        help="六部根目錄；留空則由 gov_paths / Master_Map 推導。",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="只列出將建立的資料夾，不實際建立。",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    dest_root = (args.dest_root or "").strip()
    if not dest_root:
        here = os.path.dirname(os.path.abspath(__file__))
        mp_local = os.path.join(here, "Master_Map.json")
        if os.path.isfile(mp_local):
            with open(mp_local, "r", encoding="utf-8") as f:
                _boot = json.load(f)
            _d = _boot.get("departments") or {}
            _agents_rel = str(_d.get("02_Agents_Core", "02_Agents_Core")).replace("/", os.sep)
            agents_core = os.path.normpath(os.path.join(here, "..", _agents_rel))
        else:
            agents_core = os.path.normpath(os.path.join(here, "..", "02_Agents_Core"))
        if agents_core not in sys.path:
            sys.path.insert(0, agents_core)
        from gov_paths import get_tang_gov_root

        dest_root = get_tang_gov_root()

    total, existed, created, lines = run_system_check(dest_root=dest_root, dry_run=bool(args.dry_run))
    print(f"dest_root: {os.path.abspath(dest_root)}")
    print(f"checked={total}, already_existed={existed}, created={created}, dry_run={bool(args.dry_run)}")
    for line in lines:
        print(line)


if __name__ == "__main__":
    main()
