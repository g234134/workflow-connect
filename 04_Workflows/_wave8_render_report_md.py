"""Wave 8 CLI — render Wave 7 report.json to Markdown (REPORT-MD-RENDER)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence


def _insert_gov_core_from_master_map(workflows_dir: Path) -> None:
    repo_root = workflows_dir.parent
    mp_path = workflows_dir / "Master_Map.json"
    with mp_path.open(encoding="utf-8") as f:
        master_map = json.load(f)
    cabins = master_map.get("cabins") or {}
    entry = cabins.get("gov_core_system") if isinstance(cabins, dict) else None
    if not isinstance(entry, dict):
        raise RuntimeError("Master_Map.cabins.gov_core_system missing")
    venv_rel = entry.get("venv_dir")
    if not venv_rel:
        raise RuntimeError("Master_Map.cabins.gov_core_system.venv_dir missing")
    gov_core = (repo_root / str(venv_rel).replace("\\", "/")).resolve()
    gov_s = str(gov_core)
    if gov_s not in sys.path:
        sys.path.insert(0, gov_s)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Wave 8: render report.json to Markdown (read-only).",
    )
    parser.add_argument(
        "--report-json",
        "--report",
        dest="report_json",
        required=True,
        help="Path to report.json",
    )
    parser.add_argument(
        "--audience",
        default="external",
        help="external|customer or internal (default: external)",
    )
    parser.add_argument(
        "--out-md",
        "--out",
        dest="out_md",
        default=None,
        help="Write Markdown to file (default: stdout)",
    )
    parser.add_argument(
        "--display-context-json",
        dest="display_context_json",
        default=None,
        help="Optional JSON file with display_context sidecar",
    )
    parser.add_argument(
        "--generated-at",
        dest="generated_at",
        default=None,
        help="Fixed ISO8601 timestamp for deterministic output",
    )
    return parser


def _load_json_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, str(exc)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, str(exc)
    if not isinstance(data, dict):
        return None, "expected JSON object"
    return data, None


def run_render(
    argv: Sequence[str] | None = None,
    *,
    workflows_dir: Path | None = None,
) -> tuple[int, dict[str, Any]]:
    wf = workflows_dir or Path(__file__).resolve().parent
    _insert_gov_core_from_master_map(wf)

    from core.wave8_report_md_renderer import render_data_clean_report  # noqa: PLC0415

    args = build_parser().parse_args(list(argv) if argv is not None else None)

    report_path = Path(args.report_json)
    if not report_path.is_file():
        payload = {"ok": False, "message": f"report JSON not found: {report_path.name}"}
        print(json.dumps(payload, ensure_ascii=False))
        return 1, payload

    report, err = _load_json_object(report_path)
    if err:
        payload = {"ok": False, "message": err}
        print(json.dumps(payload, ensure_ascii=False))
        return 1, payload

    display_context: dict[str, Any] | None = None
    if args.display_context_json:
        dpath = Path(args.display_context_json)
        display_context, derr = _load_json_object(dpath)
        if derr:
            payload = {"ok": False, "message": f"display_context: {derr}"}
            print(json.dumps(payload, ensure_ascii=False))
            return 1, payload

    config: dict[str, Any] = {"audience": args.audience}
    if args.generated_at:
        config["generated_at"] = args.generated_at

    out = render_data_clean_report(report, config=config, display_context=display_context)
    if not out.get("ok"):
        print(json.dumps(out, ensure_ascii=False))
        return 1, out

    markdown = str(out["markdown"])
    if args.out_md:
        Path(args.out_md).write_text(markdown, encoding="utf-8")
    else:
        sys.stdout.write(markdown)

    payload = {"ok": True, "message": out.get("message", "report_md_rendered")}
    if args.out_md:
        payload["out_md"] = str(Path(args.out_md))
    return 0, payload


def main(argv: Sequence[str] | None = None) -> int:
    code, _ = run_render(argv)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
