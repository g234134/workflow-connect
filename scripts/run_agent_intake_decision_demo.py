#!/usr/bin/env python3
"""Agent/Orchestrator intake decision demo CLI v1 (W5-T1B) + v2 opt-in (W8-T2 / W9-T2).

Wires W5-T1 ``evaluate_intake_decision`` or W8-T2/W9-T2 ``evaluate_intake_decision_v2``
(which consumes W4-T1 ``plan_tabular_route`` for Tabular, or non_tabular profile
parsing for ``non_tabular.*``) into an Agent-readable entry point.
Plan-only: no Executor subprocess, no outbox writes.

Does not modify main-chain E2E, Local UI, or intake CLIs.

Usage:
    python scripts/run_agent_intake_decision_demo.py \\
        --task-type tabular.cleaning.mvp --case-dir cases/demo_phase
    python scripts/run_agent_intake_decision_demo.py \\
        --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --format json
    python scripts/run_agent_intake_decision_demo.py \\
        --task-type tabular.cleaning.mvp --case-dir cases/sandbox_client --use-v2 --format json
    python scripts/run_agent_intake_decision_demo.py \\
        --task-type non_tabular.document.extract --case-dir cases/docu-corp/2026-0001 \\
        --use-v2 --format json
    python scripts/run_agent_intake_decision_demo.py \\
        --task-type non_tabular.log.analyze --case-dir cases/log-analytics-co/logs-2026-0001 \\
        --use-v2 --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from routing.intake_decision_rules_v1 import evaluate_intake_decision
from routing.intake_decision_rules_v2 import evaluate_intake_decision_v2


def run_agent_intake_decision(
    task_type: str,
    case_dir: str,
    *,
    use_v2: bool = False,
) -> Dict[str, Any]:
    """Evaluate intake decision for Agent/Orchestrator flows (W5-T1B / W8-T2 wrapper)."""
    if use_v2:
        return evaluate_intake_decision_v2(task_type, case_dir, use_v1_fallback=True)
    return evaluate_intake_decision(task_type, case_dir)


def format_decision_summary_text(result: Dict[str, Any]) -> str:
    """Render a human/Agent-readable decision summary from W5-T1 result dict."""
    lines: List[str] = [
        "Intake Decision Summary (W5-T1B)",
        f"task_type: {result.get('task_type', '')}",
        f"case_dir: {result.get('case_dir', '')}",
        f"decision: {result.get('decision', '')}",
        f"risk_level: {result.get('risk_level', '')}",
        "rationale:",
    ]
    for item in result.get("rationale") or []:
        lines.append(f"  - {item}")

    route = result.get("suggested_route")
    lines.append("suggested_route.planned_tools:")
    if isinstance(route, dict):
        for tool_id in route.get("planned_tools") or []:
            lines.append(f"  - {tool_id}")
        selector = route.get("selector_task_type")
        if selector:
            lines.append(f"suggested_route.selector_task_type: {selector}")
    else:
        lines.append("  - (none)")

    message = result.get("message")
    if message:
        lines.append(f"message: {message}")

    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Agent/Orchestrator intake decision demo (W5-T1B, plan-only).",
    )
    parser.add_argument(
        "--task-type",
        required=True,
        help="W2 routing catalog task_type (tabular.* or non_tabular.* with --use-v2)",
    )
    parser.add_argument(
        "--case-dir",
        required=True,
        help="Case directory (repo-relative or absolute)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format: text summary (default) or json (W5-T1 dict)",
    )
    parser.add_argument(
        "--use-v2",
        action="store_true",
        help="Use intake decision rules v2 (W8-T2 Tabular + W9-T2 non_tabular.*); default remains v1",
    )
    args = parser.parse_args(argv)

    result = run_agent_intake_decision(
        args.task_type,
        args.case_dir,
        use_v2=args.use_v2,
    )

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_decision_summary_text(result))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
