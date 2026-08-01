"""CLI entry for batch orchestrator (BATCH-MVP-04 + Worker API mode).

Usage (from repo root, with ``04_Workflows`` on ``sys.path``)::

    python -m _batch_orchestrator.cli run --manifest tests/fixtures/sample_manifest.json --mode mock --limit 2
    python -m _batch_orchestrator.cli run --manifest tests/fixtures/sample_manifest.json --mode worker_api --worker-url http://127.0.0.1:8765 --limit 2

Or::

    python 04_Workflows/_batch_orchestrator/cli.py run --manifest ... --mode mock --limit 2
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Allow ``python 04_Workflows/_batch_orchestrator/cli.py`` and ``python -m``.
_WORKFLOWS = Path(__file__).resolve().parents[1]
_REPO_ROOT = _WORKFLOWS.parent
if str(_WORKFLOWS) not in sys.path:
    sys.path.insert(0, str(_WORKFLOWS))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from _batch_orchestrator.collector import collect_results  # noqa: E402
from _batch_orchestrator.loader import load_batch_manifest_from_path  # noqa: E402
from _batch_orchestrator.prompt_builder import build_implementer_prompt  # noqa: E402
from _batch_orchestrator.reporter import (  # noqa: E402
    render_batch_result_json,
    render_state_patch_suggestion,
)
from _batch_orchestrator.runner_mock import run_subtasks_mock  # noqa: E402
from _batch_orchestrator.runner_worker_api import run_subtasks_worker_api  # noqa: E402
from _batch_orchestrator.scheduler import plan_from_subtasks  # noqa: E402
from _batch_orchestrator.worker_api import ENV_WORKER_API_URL  # noqa: E402


def _resolve_manifest_path(raw: str) -> Path:
    path = Path(raw)
    if path.is_file():
        return path.resolve()
    cand = _REPO_ROOT / raw
    if cand.is_file():
        return cand.resolve()
    cand2 = _WORKFLOWS / raw
    if cand2.is_file():
        return cand2.resolve()
    return path.resolve()


def run_batch_pipeline(
    *,
    manifest_path: Path,
    mode: str = "mock",
    limit: int | None = None,
    concurrency_limit: int = 2,
    output_dir: Path | None = None,
    worker_base_url: str | None = None,
) -> dict[str, Any]:
    """Load → schedule → prompt → run (mock|worker_api) → collect → report."""
    loaded = load_batch_manifest_from_path(manifest_path)
    if not loaded.get("ok"):
        return {
            "ok": False,
            "message": "manifest load failed",
            "errors": loaded.get("errors") or [],
            "batch_result": None,
            "state_patch_suggestion": None,
            "mode": mode,
        }

    data = loaded["data"] or {}
    subtasks = list(data.get("subtasks") or [])
    batch_id = str(data.get("batch_id") or f"batch-{mode}")
    parent_ticket_id = str(data.get("parent_ticket_id") or "")

    plan = plan_from_subtasks(subtasks)
    if not plan.get("ok"):
        return {
            "ok": False,
            "message": plan.get("message") or "scheduler refused",
            "errors": (plan.get("eligibility") or {}).get("errors") or [],
            "plan": plan,
            "batch_result": None,
            "state_patch_suggestion": None,
            "mode": mode,
        }

    order = list(plan.get("order") or [])
    by_id = {str(st.get("subtask_id")): st for st in subtasks}
    ordered = [by_id[sid] for sid in order if sid in by_id]
    if limit is not None and limit >= 0:
        ordered = ordered[: int(limit)]

    parent_frame = {
        "parent_ticket_id": parent_ticket_id,
        "goal": f"{mode} batch run for {batch_id}",
    }
    prompts = [build_implementer_prompt(st, parent_frame) for st in ordered]

    if mode == "mock":
        results = run_subtasks_mock(
            ordered,
            concurrency_limit=concurrency_limit,
            parent_frame=parent_frame,
            build_prompt=True,
            base_latency_ms=1.0,
        )
        runner_kind = "mock"
        external_http = False
    elif mode == "worker_api":
        results = run_subtasks_worker_api(
            ordered,
            concurrency_limit=concurrency_limit,
            worker_base_url=worker_base_url,
            parent_frame=parent_frame,
            build_prompt=True,
        )
        runner_kind = "worker_api"
        external_http = True
    else:
        return {
            "ok": False,
            "message": f"unsupported mode={mode!r}",
            "batch_result": None,
            "state_patch_suggestion": None,
            "mode": mode,
        }

    batch = collect_results(results, batch_id=batch_id)
    batch_json = render_batch_result_json(batch)
    suggestion = render_state_patch_suggestion(
        batch,
        parent_ticket_id=parent_ticket_id or None,
    )

    written: dict[str, str] = {}
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        batch_path = output_dir / "batch_result.json"
        suggest_path = output_dir / "state_patch_suggestion.json"
        batch_path.write_text(
            json.dumps(batch_json, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        suggest_path.write_text(
            json.dumps(suggestion, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written = {
            "batch_result_json": str(batch_path.as_posix()),
            "state_patch_suggestion_json": str(suggest_path.as_posix()),
        }

    return {
        "ok": bool(batch.ok),
        "message": batch.message,
        "mode": mode,
        "runner": runner_kind,
        "external_http": external_http,
        "plan": {
            "waves": plan.get("waves"),
            "order": plan.get("order"),
            "eligibility": plan.get("eligibility"),
        },
        "prompt_count": len(prompts),
        "batch_result": batch_json,
        "state_patch_suggestion": suggestion,
        "written": written,
        "writes_ticket_state": False,
        "worker_url_env": ENV_WORKER_API_URL,
    }


def run_mock_pipeline(
    *,
    manifest_path: Path,
    limit: int | None = None,
    concurrency_limit: int = 2,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Backward-compatible alias for ``run_batch_pipeline(..., mode='mock')``."""
    return run_batch_pipeline(
        manifest_path=manifest_path,
        mode="mock",
        limit=limit,
        concurrency_limit=concurrency_limit,
        output_dir=output_dir,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Batch orchestrator CLI (mock | worker_api).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run batch pipeline from a manifest JSON")
    run_p.add_argument("--manifest", required=True, help="Path to batch manifest JSON")
    run_p.add_argument(
        "--mode",
        choices=("mock", "worker_api"),
        default="mock",
        help="Execution mode: mock (local sim) or worker_api (real HTTP Worker)",
    )
    run_p.add_argument(
        "--worker-url",
        default=None,
        help=f"Worker API base URL (else env {ENV_WORKER_API_URL})",
    )
    run_p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional max subtasks after scheduler order",
    )
    run_p.add_argument(
        "--concurrency",
        type=int,
        default=2,
        help="Runner concurrency_limit (default 2)",
    )
    run_p.add_argument(
        "--output-dir",
        default=None,
        help="Optional directory for batch_result.json + state_patch_suggestion.json",
    )
    run_p.add_argument(
        "--format",
        choices=("json",),
        default="json",
        help="Stdout format (json)",
    )

    serve_p = sub.add_parser(
        "serve-worker",
        help="Start local Batch Worker API HTTP server (for worker_api mode)",
    )
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8765)

    args = parser.parse_args(argv)
    if args.command == "serve-worker":
        from _batch_orchestrator.worker_api import serve_forever

        serve_forever(host=args.host, port=args.port)
        return 0

    if args.command != "run":
        parser.error(f"unsupported command: {args.command}")

    manifest_path = _resolve_manifest_path(args.manifest)
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    result = run_batch_pipeline(
        manifest_path=manifest_path,
        mode=args.mode,
        limit=args.limit,
        concurrency_limit=args.concurrency,
        output_dir=output_dir,
        worker_base_url=args.worker_url,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
