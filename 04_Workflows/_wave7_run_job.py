"""Wave 7 single BASIC job CLI — bootstrap, entry, orchestrator (ORCH-JOB-LIFECYCLE)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

# Keys printed on successful orchestrator completion (runbook contract).
_ORCH_STDOUT_KEYS = (
    "ok",
    "status",
    "stage",
    "artifacts",
    "qa",
    "completion_variant",
    "message",
    "error_code",
)


def _insert_gov_core_from_master_map(workflows_dir: Path) -> Path:
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
    return gov_core


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Wave 7: run one CLEAN job end-to-end "
            "(bootstrap → job input → run_wave7_job)."
        ),
    )
    parser.add_argument("--sku", required=True, help="CLEAN-BASIC or CLEAN-ENRICH")
    parser.add_argument("--client-ref", required=True, dest="client_ref")
    parser.add_argument("--cleaned-dir", dest="cleaned_dir", default=None)
    parser.add_argument("--queue-json", dest="queue_json", default=None)
    parser.add_argument("--job-id", dest="job_id", default=None)
    parser.add_argument("--manifest", dest="manifest_path", default=None)
    parser.add_argument("--intake-json", dest="intake_json", default=None)
    parser.add_argument(
        "--base-dir",
        dest="base_dir",
        default=None,
        help="Base for relative paths (default: repo root)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON result",
    )
    parser.add_argument(
        "--enable-m2",
        dest="enable_m2",
        action="store_true",
        help="Run Wave 8 M2 sample validation before report build (default: off)",
    )
    parser.add_argument(
        "--render-report-md",
        dest="render_report_md",
        action="store_true",
        help="Render report.json to report.md after artifact finalize (default: off)",
    )
    parser.add_argument(
        "--strict-report-md",
        dest="strict_report_md",
        action="store_true",
        help="Treat report.md render/write failure as job failure (default: off)",
    )
    return parser


def _load_json_mapping(path: Path) -> tuple[dict[str, Any] | None, str | None]:
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


def _format_stdout(payload: dict[str, Any], *, pretty: bool) -> str:
    if pretty:
        return json.dumps(payload, ensure_ascii=False, indent=2)
    return json.dumps(payload, ensure_ascii=False)


def _project_orch_stdout(out: dict[str, Any]) -> dict[str, Any]:
    return {key: out.get(key) for key in _ORCH_STDOUT_KEYS}


def run_job(
    argv: Sequence[str] | None = None,
    *,
    workflows_dir: Path | None = None,
) -> tuple[int, dict[str, Any]]:
    """
    Run Wave 7 single-job CLI.

    Returns ``(exit_code, last_structured_payload)``.
    """
    wf = workflows_dir or Path(__file__).resolve().parent
    _insert_gov_core_from_master_map(wf)

    from core.repo_paths import find_repo_root  # noqa: PLC0415
    from core.wave7_orch_job_lifecycle import run_wave7_job  # noqa: PLC0415
    from core.wave7_runner_entry_job_input import (  # noqa: PLC0415
        ERR_INVALID_JSON,
        build_runner_job_input,
    )
    from core.wave7_runner_env_bootstrap import bootstrap_runner_env  # noqa: PLC0415

    args = build_parser().parse_args(list(argv) if argv is not None else None)
    pretty = bool(args.pretty)

    repo = find_repo_root(start=wf)
    if repo is None:
        payload = {
            "ok": False,
            "message": "repo root not found",
            "error_code": "repo_root_not_found",
        }
        print(_format_stdout(payload, pretty=pretty))
        return 2, payload

    boot = bootstrap_runner_env(check=False, start=wf)
    if not boot.get("ok"):
        print(_format_stdout(boot, pretty=pretty))
        return 2, boot

    intake_request: dict[str, Any] | None = None
    if args.intake_json:
        ipath = Path(args.intake_json)
        if not ipath.is_file():
            payload = {
                "ok": False,
                "message": f"intake JSON not found: {ipath.name}",
                "error_code": ERR_INVALID_JSON,
            }
            print(_format_stdout(payload, pretty=pretty))
            return 1, payload
        data, err = _load_json_mapping(ipath)
        if err:
            payload = {
                "ok": False,
                "message": err,
                "error_code": ERR_INVALID_JSON,
            }
            print(_format_stdout(payload, pretty=pretty))
            return 1, payload
        intake_request = data

    queue_payload: dict[str, Any] | None = None
    if args.queue_json:
        qpath = Path(args.queue_json)
        if not qpath.is_file():
            payload = {
                "ok": False,
                "message": f"queue JSON not found: {qpath.name}",
                "error_code": ERR_INVALID_JSON,
            }
            print(_format_stdout(payload, pretty=pretty))
            return 1, payload
        data, err = _load_json_mapping(qpath)
        if err:
            payload = {
                "ok": False,
                "message": err,
                "error_code": ERR_INVALID_JSON,
            }
            print(_format_stdout(payload, pretty=pretty))
            return 1, payload
        queue_payload = data

    base_dir = Path(args.base_dir) if args.base_dir else repo

    entry = build_runner_job_input(
        sku=args.sku,
        client_ref=args.client_ref,
        cleaned_dir=args.cleaned_dir,
        manifest_path=args.manifest_path,
        queue_payload=queue_payload,
        job_id=args.job_id,
        intake_request=intake_request,
        base_dir=base_dir,
    )
    if not entry.get("ok"):
        print(_format_stdout(entry, pretty=pretty))
        return 1, entry

    job_in = {
        "job_record": entry["job_record"],
        "raw_files": entry["raw_files"],
    }
    out = run_wave7_job(
        job_in,
        paths_resolved=boot["paths_resolved"],
        repo_root=repo,
        enable_m2=bool(args.enable_m2),
        render_report_md=bool(args.render_report_md),
        strict_report_md=bool(args.strict_report_md),
    )
    stdout_payload = _project_orch_stdout(out)
    print(_format_stdout(stdout_payload, pretty=pretty))
    return (0 if out.get("ok") else 1), stdout_payload


def main(argv: Sequence[str] | None = None) -> int:
    code, _ = run_job(argv)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
