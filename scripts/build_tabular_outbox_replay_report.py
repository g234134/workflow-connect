#!/usr/bin/env python3
"""Offline tabular outbox replay report generator v1 (W3-TL-T4 follow-up).

Builds read-only Markdown/HTML reports from tabular MVP outbox records.
Does not re-execute tools or write outbox run files.

Usage:
    python scripts/build_tabular_outbox_replay_report.py --case-ref demo_phase
    python scripts/build_tabular_outbox_replay_report.py --case-ref demo_phase --format both --json
    python scripts/build_tabular_outbox_replay_report.py --outbox-root tests/fixtures/outbox --format md
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.tabular_outbox_consumer import (  # noqa: E402
    get_outbox_run,
    join_with_case_history,
    list_outbox_runs,
)
from tools.tabular_outbox_writer import EVENTS_FILENAME  # noqa: E402

_SCHEMA_VERSION = "tabular_outbox_replay_report_v1"
_DEFAULT_OUTPUT_DIR = "outbox/reports"

FormatChoice = Literal["md", "html", "both"]


def default_output_dir(repo_root: Optional[Path] = None) -> Path:
    root = repo_root or _REPO_ROOT
    return root / _DEFAULT_OUTPUT_DIR


def _utc_stamp(when: Optional[datetime] = None) -> str:
    dt = when or datetime.now(timezone.utc)
    return dt.strftime("%Y%m%dT%H%M%SZ")


def _resolve_outbox_root(
    repo_root: Path,
    outbox_root_override: Optional[str],
) -> Path:
    if outbox_root_override:
        path = Path(outbox_root_override)
        if not path.is_absolute():
            path = repo_root / path
        return path.resolve()
    return (repo_root / "outbox").resolve()


def load_events_jsonl(outbox_root: Path) -> List[Dict[str, Any]]:
    """Read optional append-only events.jsonl (best-effort)."""
    events_path = outbox_root / EVENTS_FILENAME
    if not events_path.is_file():
        return []

    events: List[Dict[str, Any]] = []
    try:
        with events_path.open(encoding="utf-8") as fh:
            for line in fh:
                text = line.strip()
                if not text:
                    continue
                try:
                    item = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict):
                    events.append(item)
    except OSError:
        return []
    return events


def _discover_case_refs(
    outbox_root: Path,
    *,
    outbox_root_override: Optional[str] = None,
) -> List[str]:
    runs = list_outbox_runs(outbox_root_override=outbox_root_override)
    refs: Set[str] = set()
    for run in runs:
        case_ref = run.get("case_ref")
        if isinstance(case_ref, str) and case_ref.strip():
            refs.add(case_ref.replace("\\", "/").strip("/"))
    if refs:
        return sorted(refs)

    if not outbox_root.is_dir():
        return []
    discovered: List[str] = []
    for child in sorted(outbox_root.iterdir()):
        if child.is_dir() and child.name != "reports":
            discovered.append(child.name.replace("\\", "/"))
    return discovered


def _enrich_runs_with_artifacts(
    runs: List[Dict[str, Any]],
    case_ref: str,
    *,
    outbox_root_override: Optional[str] = None,
) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []
    for summary in runs:
        run_id = summary.get("run_id")
        if not isinstance(run_id, str):
            enriched.append(dict(summary))
            continue
        detail = get_outbox_run(
            case_ref,
            run_id,
            outbox_root_override=outbox_root_override,
        )
        row = dict(summary)
        if detail.get("ok") and isinstance(detail.get("record"), dict):
            record = detail["record"]
            row["artifacts"] = record.get("artifacts") or []
            if record.get("stderr_tail"):
                row["stderr_tail"] = record.get("stderr_tail")
        else:
            row["artifacts"] = []
        enriched.append(row)
    return enriched


def collect_case_replay_view(
    case_ref: str,
    *,
    outbox_root_override: Optional[str] = None,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Build one case replay view (join + artifact enrichment)."""
    join = join_with_case_history(
        case_ref,
        repo_root=repo_root,
        outbox_root_override=outbox_root_override,
    )
    runs = join.get("runs") or []
    join["runs"] = _enrich_runs_with_artifacts(
        runs,
        case_ref,
        outbox_root_override=outbox_root_override,
    )
    join["run_count"] = len(join["runs"])
    return join


def collect_replay_report_data(
    *,
    case_ref: Optional[str] = None,
    outbox_root_override: Optional[str] = None,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Aggregate replay data for one case or all discovered cases."""
    root = (repo_root or _REPO_ROOT).resolve()
    outbox_root = _resolve_outbox_root(root, outbox_root_override)

    if case_ref:
        case_refs = [case_ref.replace("\\", "/").strip("/")]
    else:
        case_refs = _discover_case_refs(
            outbox_root,
            outbox_root_override=outbox_root_override,
        )

    cases: List[Dict[str, Any]] = []
    for ref in case_refs:
        view = collect_case_replay_view(
            ref,
            outbox_root_override=outbox_root_override,
            repo_root=root,
        )
        cases.append(view)

    events = load_events_jsonl(outbox_root)
    if case_ref:
        safe = case_ref.replace("\\", "/").strip("/")
        events = [e for e in events if e.get("case_ref") == safe]

    total_runs = sum(int(c.get("run_count") or 0) for c in cases)
    return {
        "ok": True,
        "schema_version": _SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "case_ref": case_ref,
        "case_count": len(cases),
        "run_count": total_runs,
        "cases": cases,
        "events_jsonl_count": len(events),
        "events_jsonl": events,
        "outbox_root": outbox_root.as_posix(),
    }


def _artifact_lines(artifacts: List[Any]) -> List[str]:
    lines: List[str] = []
    for item in artifacts:
        if not isinstance(item, dict):
            continue
        path = item.get("path", "?")
        kind = item.get("kind", "?")
        key = item.get("logical_key")
        suffix = f" (`{key}`)" if key else ""
        lines.append(f"- `{kind}` → `{path}`{suffix}")
    return lines or ["- _(none)_"]


def render_replay_markdown(data: Dict[str, Any]) -> str:
    """Render replay report as Markdown."""
    scope = data.get("case_ref") or "all"
    lines = [
        f"# Tabular Outbox Replay Report — `{scope}`",
        "",
        f"> Schema: `{data.get('schema_version')}` · generated: `{data.get('generated_at')}`",
        "> **Read-only replay** — does not re-execute tools.",
        "",
        "## Summary",
        "",
        f"- Cases: **{data.get('case_count', 0)}**",
        f"- Runs: **{data.get('run_count', 0)}**",
        f"- `events.jsonl` lines (filtered): **{data.get('events_jsonl_count', 0)}**",
        "",
    ]

    for case_view in data.get("cases") or []:
        if not case_view.get("ok"):
            lines.extend(
                [
                    f"## Case `{case_view.get('case_ref')}` — error",
                    "",
                    f"- message: `{case_view.get('message', 'unknown')}`",
                    "",
                ]
            )
            continue

        ref = case_view.get("case_ref", "?")
        case = case_view.get("case") or {}
        lines.extend(
            [
                f"## Case `{ref}`",
                "",
                "| Field | Value |",
                "|-------|-------|",
                f"| client_ref | `{case.get('client_ref', '—')}` |",
                f"| product_sku | `{case.get('product_sku', '—')}` |",
                f"| gate_status | `{case.get('gate_status', '—')}` |",
                f"| run_count | {case_view.get('run_count', 0)} |",
                "",
            ]
        )

        last = case_view.get("last_by_tool_id") or {}
        if last:
            lines.extend(["### Last run by tool_id", ""])
            for tool_id, row in sorted(last.items()):
                lines.append(
                    f"- `{tool_id}`: ok={row.get('ok')} exit={row.get('exit_code')} "
                    f"run_id=`{row.get('run_id')}`"
                )
            lines.append("")

        runs = case_view.get("runs") or []
        if runs:
            lines.extend(
                [
                    "### Timeline (chronological)",
                    "",
                    "| started_at | tool_id | ok | exit | run_id | message |",
                    "|------------|---------|----|------|--------|---------|",
                ]
            )
            for run in runs:
                msg = str(run.get("message") or "")
                if len(msg) > 60:
                    msg = msg[:57] + "..."
                lines.append(
                    f"| {run.get('started_at', '—')} | `{run.get('tool_id', '—')}` | "
                    f"{run.get('ok')} | {run.get('exit_code')} | "
                    f"`{run.get('run_id', '—')}` | {msg} |"
                )
            lines.append("")

            lines.extend(["### Artifacts by run", ""])
            for run in runs:
                lines.append(f"#### `{run.get('run_id')}`")
                lines.extend(_artifact_lines(run.get("artifacts") or []))
                if run.get("stderr_tail"):
                    lines.append("")
                    lines.append(f"_stderr tail_: `{run.get('stderr_tail')}`")
                lines.append("")

    events = data.get("events_jsonl") or []
    if events:
        lines.extend(["## events.jsonl appendix", ""])
        for event in events:
            lines.append(
                f"- `{event.get('started_at')}` {event.get('case_ref')} "
                f"{event.get('tool_id')} ok={event.get('ok')} exit={event.get('exit_code')}"
            )
        lines.append("")

    lines.extend(
        [
            "## Notes",
            "",
            "- Replay report is **investigation-only**; see `docs/tabular-outbox-replay-report-v1.md`.",
            "- Re-execute from outbox is **not** implemented (Phase 8.8 / future ticket).",
            "",
        ]
    )
    return "\n".join(lines)


def render_replay_html(data: Dict[str, Any]) -> str:
    """Render self-contained HTML (inline CSS, no external deps)."""
    scope = html.escape(str(data.get("case_ref") or "all"))
    body_parts = [
        f"<h1>Tabular Outbox Replay Report — <code>{scope}</code></h1>",
        f"<p class='meta'>Schema: <code>{html.escape(str(data.get('schema_version')))}</code> "
        f"· generated: <code>{html.escape(str(data.get('generated_at')))}</code></p>",
        "<p><strong>Read-only replay</strong> — does not re-execute tools.</p>",
        "<h2>Summary</h2>",
        "<ul>",
        f"<li>Cases: <strong>{data.get('case_count', 0)}</strong></li>",
        f"<li>Runs: <strong>{data.get('run_count', 0)}</strong></li>",
        f"<li>events.jsonl lines: <strong>{data.get('events_jsonl_count', 0)}</strong></li>",
        "</ul>",
    ]

    for case_view in data.get("cases") or []:
        ref = html.escape(str(case_view.get("case_ref", "?")))
        body_parts.append(f"<h2>Case <code>{ref}</code></h2>")
        if not case_view.get("ok"):
            body_parts.append(
                f"<p class='err'>Error: {html.escape(str(case_view.get('message', 'unknown')))}</p>"
            )
            continue

        case = case_view.get("case") or {}
        body_parts.extend(
            [
                "<table>",
                "<tr><th>Field</th><th>Value</th></tr>",
                f"<tr><td>client_ref</td><td><code>{html.escape(str(case.get('client_ref', '—')))}</code></td></tr>",
                f"<tr><td>product_sku</td><td><code>{html.escape(str(case.get('product_sku', '—')))}</code></td></tr>",
                f"<tr><td>gate_status</td><td><code>{html.escape(str(case.get('gate_status', '—')))}</code></td></tr>",
                f"<tr><td>run_count</td><td>{case_view.get('run_count', 0)}</td></tr>",
                "</table>",
            ]
        )

        last = case_view.get("last_by_tool_id") or {}
        if last:
            body_parts.append("<h3>Last run by tool_id</h3><ul>")
            for tool_id, row in sorted(last.items()):
                body_parts.append(
                    f"<li><code>{html.escape(tool_id)}</code>: ok={row.get('ok')} "
                    f"exit={row.get('exit_code')} run_id="
                    f"<code>{html.escape(str(row.get('run_id')))}</code></li>"
                )
            body_parts.append("</ul>")

        runs = case_view.get("runs") or []
        if runs:
            body_parts.append("<h3>Timeline</h3><table><tr>")
            for col in ("started_at", "tool_id", "ok", "exit_code", "run_id", "message"):
                body_parts.append(f"<th>{col}</th>")
            body_parts.append("</tr>")
            for run in runs:
                body_parts.append("<tr>")
                for col in ("started_at", "tool_id", "ok", "exit_code", "run_id", "message"):
                    val = html.escape(str(run.get(col, "—")))
                    body_parts.append(f"<td>{val}</td>")
                body_parts.append("</tr>")
            body_parts.append("</table>")

    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>Tabular Outbox Replay Report</title>"
        "<style>"
        "body{font-family:system-ui,sans-serif;margin:2rem;max-width:960px;line-height:1.45}"
        "table{border-collapse:collapse;width:100%;margin:1rem 0}"
        "th,td{border:1px solid #ccc;padding:0.4rem 0.6rem;text-align:left;font-size:0.9rem}"
        "th{background:#f4f4f4}"
        "code{background:#f0f0f0;padding:0.1rem 0.3rem;border-radius:3px}"
        ".meta{color:#555}"
        ".err{color:#a00}"
        "</style></head><body>"
        + "".join(body_parts)
        + "</body></html>"
    )


def _slug_case_ref(case_ref: Optional[str]) -> str:
    if not case_ref:
        return "all"
    return case_ref.replace("\\", "/").strip("/").replace("/", "__")


def build_tabular_outbox_replay_report(
    *,
    case_ref: Optional[str] = None,
    outbox_root_override: Optional[str] = None,
    repo_root: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    fmt: FormatChoice = "both",
    write_outputs: bool = True,
) -> Dict[str, Any]:
    """Build replay report files and return structured result dict."""
    root = (repo_root or _REPO_ROOT).resolve()
    data = collect_replay_report_data(
        case_ref=case_ref,
        outbox_root_override=outbox_root_override,
        repo_root=root,
    )

    stamp = _utc_stamp()
    slug = _slug_case_ref(case_ref)
    markdown = render_replay_markdown(data) if fmt in {"md", "both"} else None
    html_doc = render_replay_html(data) if fmt in {"html", "both"} else None

    report_paths: Dict[str, str] = {}
    out_dir = (output_dir or default_output_dir(root)).resolve()

    if write_outputs:
        out_dir.mkdir(parents=True, exist_ok=True)
        if markdown is not None:
            md_path = out_dir / f"replay_{slug}_{stamp}.md"
            md_path.write_text(markdown, encoding="utf-8")
            try:
                report_paths["markdown"] = md_path.relative_to(root).as_posix()
            except ValueError:
                report_paths["markdown"] = md_path.as_posix()
        if html_doc is not None:
            html_path = out_dir / f"replay_{slug}_{stamp}.html"
            html_path.write_text(html_doc, encoding="utf-8")
            try:
                report_paths["html"] = html_path.relative_to(root).as_posix()
            except ValueError:
                report_paths["html"] = html_path.as_posix()

    return {
        "ok": True,
        "message": "replay report generated",
        "schema_version": _SCHEMA_VERSION,
        "case_ref": case_ref,
        "case_count": data.get("case_count"),
        "run_count": data.get("run_count"),
        "format": fmt,
        "report_paths": report_paths,
        "markdown": markdown,
        "html": html_doc,
        "data": data,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build read-only tabular outbox replay report (MD/HTML)."
    )
    parser.add_argument(
        "--case-ref",
        help="Case slug (e.g. demo_phase). Omit to scan all cases in outbox.",
    )
    parser.add_argument(
        "--outbox-root",
        help="Override outbox root (repo-relative or absolute)",
    )
    parser.add_argument(
        "--output-dir",
        help=f"Report output directory (default: {_DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--format",
        choices=["md", "html", "both"],
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print report body to stdout instead of writing files",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON result on stdout",
    )
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir) if args.output_dir else None
    result = build_tabular_outbox_replay_report(
        case_ref=args.case_ref,
        outbox_root_override=args.outbox_root,
        output_dir=out_dir,
        fmt=args.format,  # type: ignore[arg-type]
        write_outputs=not args.stdout,
    )

    if args.json:
        payload = {k: v for k, v in result.items() if k not in {"markdown", "html", "data"}}
        payload["summary"] = {
            "case_count": result.get("case_count"),
            "run_count": result.get("run_count"),
            "report_paths": result.get("report_paths"),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.stdout:
        if args.format in {"md", "both"} and result.get("markdown"):
            print(result["markdown"])
        elif args.format == "html" and result.get("html"):
            print(result["html"])
    else:
        paths = result.get("report_paths") or {}
        print(f"ok: {result.get('run_count', 0)} run(s) across {result.get('case_count', 0)} case(s)")
        for kind, path in paths.items():
            print(f"  {kind}: {path}")

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
