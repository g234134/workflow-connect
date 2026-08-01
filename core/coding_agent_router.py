#!/usr/bin/env python3
"""Hermes Task Router — decides where to execute a coding task.

Routes:
  simple  → LangChain coding agent (free, fast, automatic)
  complex → Cursor dispatch (paid, powerful, manual trigger)

Usage:
    python core/coding_agent_router.py --goal "在 core/ 加一個 hello.py"
    python core/coding_agent_router.py --goal "重构整个 RAG pipeline" --force cursor
    python core/coding_agent_router.py --goal "..." --json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent  # D:\大唐三省六部
_LANGCHAIN_PY = str(_REPO / "01_Environments" / "python_venvs" / "langchain_latest" / "Scripts" / "python.exe")

# Ensure repo root on sys.path for `core.` imports
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# --- Path contamination fix: hermes-agent's pydantic_core conflicts ---
# Must run BEFORE any langchain imports. Remove hermes-agent paths.
_SITE = str(_REPO / "01_Environments" / "python_venvs" / "langchain_latest" / "lib" / "site-packages")
sys.path = [p for p in sys.path if "hermes" not in p.lower() or "langchain" in p.lower()]
if _SITE not in sys.path:
    sys.path.insert(0, _SITE)

# ---------------------------------------------------------------------------
# Complexity classifier — decides agent vs cursor
# ---------------------------------------------------------------------------

COMPLEX_KEYWORDS = [
    "重构", "refactor", "重构", "redesign",
    "跨模组", "cross-module", "跨模块",
    "migration", "迁移",
    "pipeline", "管线",
    "architecture", "架构",
    "multi-file", "多文件",
    "integration", "整合",
    "database", "数据库", "schema",
    "deploy", "部署",
    "security", "安全",
]

SIMPLE_KEYWORDS = [
    "加一個", "add a", "创建", "create",
    "修改", "fix", "repair", "修復",
    "改名", "rename",
    "格式", "format", "lint",
    "測試", "test",
    "註釋", "comment",
    "import",
    "單一", "single",
]


def classify_complexity(goal: str, files: list[str] | None = None) -> dict:
    """Classify task complexity. Returns {route, reason, confidence}."""
    goal_lower = goal.lower()
    hits_complex = [kw for kw in COMPLEX_KEYWORDS if kw in goal_lower]
    hits_simple = [kw for kw in SIMPLE_KEYWORDS if kw in goal_lower]

    # File count heuristic
    file_count = len(files) if files else 0
    if file_count > 5:
        hits_complex.append(f"{file_count} files")

    # Score
    score = len(hits_simple) - len(hits_complex)

    if score >= 2:
        route, confidence = "agent", "high"
        reason = f"simple signals: {hits_simple}"
    elif score <= -2:
        route, confidence = "cursor", "high"
        reason = f"complex signals: {hits_complex}"
    elif hits_complex:
        route, confidence = "cursor", "medium"
        reason = f"has complex keywords: {hits_complex}"
    elif file_count > 3:
        route, confidence = "cursor", "medium"
        reason = f"touches {file_count} files"
    else:
        route, confidence = "agent", "medium"
        reason = "no strong complexity signals"

    return {"route": route, "reason": reason, "confidence": confidence}


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def route_task(goal: str, files: list[str] | None = None,
               force: str | None = None) -> dict:
    """Route a task to the appropriate executor.

    Returns:
        {
            "route": "agent" | "cursor",
            "classification": {...},
            "dispatch": <result from chosen executor>
        }
    """
    classification = classify_complexity(goal, files)

    if force:
        route = force.lower()
        classification["reason"] = f"forced to {route}"
        classification["confidence"] = "forced"
    else:
        route = classification["route"]

    if route == "agent":
        return _run_agent(goal, files, classification)
    else:
        return _dispatch_to_cursor(goal, files, classification)


def _run_agent(goal: str, files: list[str] | None, classification: dict) -> dict:
    """Run task through LangChain coding agent (via subprocess to avoid path contamination)."""
    agent_script = _REPO / "core" / "coding_agent.py"
    cmd = [
        _LANGCHAIN_PY, str(agent_script),
        "--goal", goal,
        "--json", "--max-steps", "15",
    ]
    if files:
        cmd += ["--context"] + files

    # Clean PYTHONPATH: only langchain venv + repo root (no hermes-agent contamination)
    import subprocess, os
    clean_env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    site = str(_REPO / "01_Environments" / "python_venvs" / "langchain_latest" / "lib" / "site-packages")
    clean_env["PYTHONPATH"] = f"{site};{str(_REPO)}"

    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300,
            cwd=str(_REPO), env=clean_env,
        )
        if r.returncode == 0 and r.stdout.strip():
            result = json.loads(r.stdout)
        else:
            result = {
                "status": "error",
                "error": (r.stderr or r.stdout or "agent failed")[:2000],
            }
    except Exception as e:
        result = {"status": "error", "error": str(e)}

    return {
        "route": "agent",
        "classification": classification,
        "result": result,
    }


def _dispatch_to_cursor(goal: str, files: list[str] | None, classification: dict) -> dict:
    """Dispatch task to Cursor via hermes_dispatch.py."""
    dispatch_script = _REPO / ".cursor" / "hooks" / "hermes_dispatch.py"
    if not dispatch_script.exists():
        return {
            "route": "cursor",
            "classification": classification,
            "result": {
                "status": "error",
                "error": f"Dispatch script not found: {dispatch_script}",
            },
        }

    # Build dispatch command
    cmd = [
        sys.executable, str(dispatch_script), "dispatch",
        "--ticket-id", f"HERMES-{int(datetime.now(timezone.utc).timestamp())}",
        "--goal", goal,
        "--primary-target", (files[0] if files else "unknown"),
    ]
    if files:
        cmd += ["--allowed"] + files

    import subprocess
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10, cwd=str(_REPO))
        output = json.loads(r.stdout) if r.stdout.strip() else {}
        return {
            "route": "cursor",
            "classification": classification,
            "result": {
                "status": "dispatched",
                "message": "Task card written. Run /hermes-dispatch in Cursor to execute.",
                "ticket_id": output.get("ticket_id"),
                "dispatch_output": output,
            },
        }
    except Exception as e:
        return {
            "route": "cursor",
            "classification": classification,
            "result": {"status": "error", "error": str(e)},
        }


def _inject_clean_path():
    """Inject clean sys.path for langchain imports."""
    import os
    site = str(_REPO / "01_Environments" / "python_venvs" / "langchain_latest" / "lib" / "site-packages")
    sys.path = [p for p in sys.path if "hermes" not in p.lower() or "langchain" in p.lower()]
    if site not in sys.path:
        sys.path.insert(0, site)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Hermes Task Router")
    parser.add_argument("--goal", required=True, help="Task description")
    parser.add_argument("--files", nargs="*", default=[], help="Relevant files")
    parser.add_argument("--force", choices=["agent", "cursor"], help="Force route")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    result = route_task(args.goal, args.files, args.force)

    if args.json:
        # Strip raw_output for cleaner JSON
        r = result.get("result", {})
        if "raw_output" in r:
            r = {k: v for k, v in r.items() if k != "raw_output"}
            result["result"] = r
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        cls = result["classification"]
        res = result["result"]
        print(f"Route: {result['route']} ({cls['confidence']})")
        print(f"Reason: {cls['reason']}")
        print(f"Status: {res.get('status', 'unknown')}")
        if res.get("files_changed"):
            print(f"Files: {res['files_changed']}")
        if res.get("error"):
            print(f"Error: {res['error']}")

    return 0 if result["result"].get("status") != "error" else 1


if __name__ == "__main__":
    sys.exit(main())
