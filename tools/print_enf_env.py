"""
Read-only control-plane helper: print governance / ENF-related env values.

Usage:
  python -m tools.print_enf_env
  python -m tools.print_enf_env --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Literal

EffectiveState = Literal["on", "off", "unset", "value"]


@dataclass(frozen=True)
class EnvSpec:
    key: str
    group: str
    note: str = ""


# Keys referenced by nightly eval / ENF preview paths (read-only observation).
GOVERNANCE_ENV_SPECS: tuple[EnvSpec, ...] = (
    EnvSpec("ENF_ENABLE", "enf", "Master enforcement switch (future Phase B)."),
    EnvSpec("GOV_ENF_ENABLE", "enf", "Repo-prefixed alias for ENF_ENABLE."),
    EnvSpec("GOV_ENF_PREVIEW_MIN_SCORE", "enf", "Preview threshold; nightly CI uses 0.7."),
    EnvSpec("GOV_ENF_BLOCKING_CANARY", "enf", "Limited blocking canary (future)."),
    EnvSpec(
        "GOV_ENF_BLOCKING_CANARY_DISABLE",
        "enf",
        "Explicit disable alias for blocking canary (audit warning when true).",
    ),
    EnvSpec("GOV_DEPLOY_ENV", "deploy", "Deploy label (dev/staging/production)."),
    EnvSpec("GOV_K2_PROD_SHADOW", "deploy", "K-2 Phase 1 prod shadow flag."),
    EnvSpec("IBRIDGE_EXPORT_ENABLED", "export", "Ibridge export master switch."),
    EnvSpec("IBRIDGE_EXPORT_ALLOW_PRODUCTION", "export", "Allow export under production deploy env."),
    EnvSpec("EVAL_EXPORT_INPUT", "nightly", "eval_export step input JSONL."),
    EnvSpec("EVAL_CI_MAX_NEEDS_REVIEW_RATIO", "nightly", "eval_ci_check ratio gate."),
    EnvSpec("EVAL_CI_FAIL_ON_TAGS", "nightly", "Comma-separated tags that fail CI."),
    EnvSpec("EVAL_CI_LIMIT", "nightly", "Max rows for eval_ci_check."),
    EnvSpec("SHADOW_EXPORT_OUT", "nightly", "Shadow pipeline flat ibridge JSONL."),
)

_TRUTHY = frozenset({"1", "true", "yes", "on", "enabled"})
_FALSY = frozenset({"0", "false", "no", "off", "disabled"})


def _effective_state(raw: str | None) -> EffectiveState:
    if raw is None:
        return "unset"
    normalized = raw.strip().lower()
    if normalized in _TRUTHY:
        return "on"
    if normalized in _FALSY:
        return "off"
    return "value"


def collect_env_snapshot() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for spec in GOVERNANCE_ENV_SPECS:
        raw = os.environ.get(spec.key)
        rows.append(
            {
                "key": spec.key,
                "group": spec.group,
                "value": raw if raw is not None else "unset",
                "effective": _effective_state(raw),
                "note": spec.note,
            }
        )
    return rows


def format_text(rows: list[dict[str, str]]) -> str:
    lines = [
        "# governance / ENF control-plane (read-only; does not modify env)",
        "",
    ]
    current_group = ""
    for row in rows:
        if row["group"] != current_group:
            current_group = row["group"]
            lines.append(f"[{current_group}]")
        lines.append(f"{row['key']}={row['value']} effective={row['effective']}")
    return "\n".join(lines) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print governance / ENF-related environment variables (read-only).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON array instead of plain text.",
    )
    parser.add_argument(
        "--group",
        choices=sorted({spec.group for spec in GOVERNANCE_ENV_SPECS}),
        action="append",
        dest="groups",
        help="Limit output to one or more groups (enf, deploy, export, nightly).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    rows = collect_env_snapshot()
    if args.groups:
        allowed = set(args.groups)
        rows = [row for row in rows if row["group"] in allowed]

    if args.json:
        json.dump(rows, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(format_text(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
