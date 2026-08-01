"""Tabular tool-executor hook (v1.1).

When ``use_tool_executor=True``, routes cleaning through ``tools/tabular_tool_executor.py``
and returns real artifact paths. Default path remains local subprocess CLIs.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

DEFAULT_CLEANING_TOOL_ID = "clean.phase_demo"
TOOL_EXECUTOR_ENTRYPOINT = "tools/tabular_tool_executor.py"


def _case_ref(case_dir: Path) -> str:
    try:
        return case_dir.resolve().relative_to((_REPO_ROOT / "cases").resolve()).as_posix()
    except ValueError:
        return case_dir.name


def maybe_invoke_tool_executor(
    *,
    use_tool_executor: bool,
    tool_id: str,
    case_dir: Path,
    step_name: str = "cleaning",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Invoke tool executor when requested; otherwise record local-script intent."""
    case_ref = _case_ref(case_dir)
    if not use_tool_executor:
        return {
            "ok": True,
            "invoked": False,
            "stub": False,
            "step_name": step_name,
            "tool_id": tool_id,
            "message": "local script path (default); use_tool_executor=False",
        }

    from tools.tabular_tool_executor import execute_tabular_tool  # noqa: WPS433

    exec_extra = dict(extra or {})
    exec_extra.setdefault("case_dir", str(case_dir))
    exec_extra.setdefault("json", True)
    if step_name == "cleaning":
        exec_extra.setdefault("skip_eligibility", True)

    result = execute_tabular_tool(
        case_ref,
        tool_id,
        dry_run=False,
        extra_args=exec_extra,
    )

    logger.info(
        "tabular tool-executor invoked %s for %s: ok=%s",
        tool_id,
        case_ref,
        result.get("ok"),
    )

    return {
        "ok": result.get("ok") is True,
        "invoked": True,
        "stub": False,
        "step_name": step_name,
        "tool_id": tool_id,
        "entrypoint": TOOL_EXECUTOR_ENTRYPOINT,
        "message": result.get("message", ""),
        "executor_result": result,
        "artifacts": result.get("artifacts") or [],
    }
