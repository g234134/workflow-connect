#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / ".cursor" / "hooks_state" / "four_piece_inventory.json"
OUT = REPO / ".cursor" / "hooks_state" / "four_piece_inventory_report.md"


def clean_paths(paths: list[str]) -> list[str]:
    out: list[str] = []
    for p in paths:
        p = p.strip()
        if not p:
            continue
        if p.startswith(("python ", "m pytest")):
            continue
        if p in {"__init__.py", "batch_subtask.schema.json"}:
            continue
        if " " in p and not p.endswith(".py"):
            continue
        if not ("/" in p or p.endswith((".py", ".md", ".yml", ".yaml", ".json", ".ps1", ".sh"))):
            continue
        out.append(p)
    return sorted(set(out))


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    for row in data:
        row["code_paths"] = clean_paths(row["code_paths"])
        row["test_paths"] = clean_paths(row["test_paths"])
        row["doc_paths"] = clean_paths(row["doc_paths"])

    groups: dict[str, list[dict]] = defaultdict(list)
    for row in data:
        groups[row["classification"]].append(row)

    order = ["done_4piece", "partial_3piece", "partial_2piece", "design_only", "unclear"]
    lines = [
        "# Workstream B · Four-Piece Inventory",
        "",
        "> Repo-fact scan of `04_Workflows/tickets/*_state.md` (126 tickets).",
        "> Classification uses on-disk existence; state wording is not upgraded.",
        "",
        "## Summary",
        "",
        "| Classification | Count | Meaning |",
        "|---|---:|---|",
        "| done_4piece | {done} | code + tests + docs + state all exist |".format(done=len(groups["done_4piece"])),
        "| partial_3piece | {n} | missing exactly one of four |".format(n=len(groups["partial_3piece"])),
        "| partial_2piece | {n} | exactly two categories present |".format(n=len(groups["partial_2piece"])),
        "| design_only | {n} | docs/state only, no code |".format(n=len(groups["design_only"])),
        "| unclear | {n} | draft/empty B_REPORT or insufficient paths |".format(n=len(groups["unclear"])),
        f"| **TOTAL** | **{len(data)}** | |",
        "",
        "## Overclaim Rules (applied)",
        "",
        "- `accepted_with_gaps` ≠ fully done",
        "- guard draft / design spec ≠ blocking gate implemented",
        "- `plan_only` / feature flag default off ≠ main-chain execute",
        "- L1 advisory / investigation-only ≠ blocking CI or SLA",
        "- nightly / e2e / smoke dispatch ≠ PR required gate unless branch protection says so",
        "- skeleton/reference (e.g. `kb.index.selector_gate`) ≠ prod wiring",
        "",
    ]

    for key in order:
        lines.append(f"## {key} ({len(groups[key])})")
        lines.append("")
        lines.append("| ticket_id | state_status | reviewer | code | tests | docs | overclaim |")
        lines.append("|---|---|---|---:|---:|---:|---|")
        for row in sorted(groups[key], key=lambda x: x["ticket_id"]):
            code_n = len(row["code_paths"])
            test_n = len(row["test_paths"])
            doc_n = len(row["doc_paths"])
            warn = "; ".join(row.get("overclaim_warnings") or []) or "—"
            lines.append(
                "| {id} | {st} | {rv} | {c} | {t} | {d} | {w} |".format(
                    id=row["ticket_id"],
                    st=(row.get("overall_status") or "—").replace("|", "/"),
                    rv=(row.get("reviewer_conclusion") or "—").replace("|", "/"),
                    c=code_n,
                    t=test_n,
                    d=doc_n,
                    w=warn.replace("|", "/"),
                )
            )
        lines.append("")
        for row in sorted(groups[key], key=lambda x: x["ticket_id"]):
            lines.append(f"### `{row['ticket_id']}`")
            lines.append(f"- state_path: `{row['state_path']}`")
            lines.append(f"- code_paths: {row['code_paths'] or []}")
            lines.append(f"- test_paths: {row['test_paths'] or []}")
            lines.append(f"- doc_paths: {row['doc_paths'] or []}")
            if row.get("overclaim_warnings"):
                lines.append(f"- overclaim_warnings: {row['overclaim_warnings']}")
            lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"WROTE {OUT}")


if __name__ == "__main__":
    main()
