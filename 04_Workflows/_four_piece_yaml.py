#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / ".cursor" / "hooks_state" / "four_piece_inventory.json"
OUT = REPO / ".cursor" / "hooks_state" / "four_piece_inventory.yaml"


def yaml_list(items: list[str], indent: int = 4) -> list[str]:
    pad = " " * indent
    if not items:
        return [f"{pad}[]"]
    return [f"{pad}- {item}" for item in items]


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    order = ["done_4piece", "partial_3piece", "partial_2piece", "design_only", "unclear"]
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in data:
        groups[row["classification"]].append(row)

    lines = [
        "# Workstream B · Four-Piece Inventory (126 tickets)",
        "# Generated from repo on-disk existence; state wording not upgraded.",
        "summary:",
    ]
    for key in order:
        lines.append(f"  {key}: {len(groups[key])}")
    lines.append(f"  total: {len(data)}")
    lines.append("tickets:")

    for row in sorted(data, key=lambda x: x["ticket_id"]):
        lines.append(f"  - ticket_id: {row['ticket_id']}")
        lines.append(f"    classification: {row['classification']}")
        if row.get("overall_status"):
            lines.append(f"    overall_status: \"{row['overall_status']}\"")
        if row.get("reviewer_conclusion"):
            lines.append(f"    reviewer_conclusion: \"{row['reviewer_conclusion']}\"")
        lines.append("    state_path: " + row["state_path"])
        lines.append("    code_paths:")
        lines.extend(yaml_list(row.get("code_paths") or []))
        lines.append("    test_paths:")
        lines.extend(yaml_list(row.get("test_paths") or []))
        lines.append("    doc_paths:")
        lines.extend(yaml_list(row.get("doc_paths") or []))
        warns = row.get("overclaim_warnings") or []
        if warns:
            lines.append("    overclaim_warnings:")
            lines.extend(yaml_list(warns))

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"WROTE {OUT}")


if __name__ == "__main__":
    main()
