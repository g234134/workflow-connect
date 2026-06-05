"""
Export real ibridge / metrics records to JSONL artifacts (dev/staging only).

Each output line is a flat record aligned with ``tests/fixtures/eval/ibridge_records.jsonl``
so ``observability.eval_exporter`` and ``eval_ci_check`` can consume the file as-is.

Sources:
  - ``collector``: in-process ``metrics.MetricsCollector`` ended tasks (ask / K-1 / K-2).
  - ``file``: existing ``.json`` / ``.jsonl`` (API dumps, wrapped ``ibridge_record`` lines).
  - ``shadow``: K-2 prod shadow / merge spool lines → flat ibridge for ``eval_ci_check``.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Iterator, Literal

from observability.eval_exporter import iter_records

SourceKind = Literal["collector", "file", "shadow"]
ArtifactProfile = Literal["ibridge", "shadow"]

ENV_EXPORT_ENABLED = "IBRIDGE_EXPORT_ENABLED"
ENV_DEPLOY_ENV = "GOV_DEPLOY_ENV"
ENV_EXPORT_ROOT = "IBRIDGE_EXPORT_ROOT"
ENV_ALLOW_PRODUCTION = "IBRIDGE_EXPORT_ALLOW_PRODUCTION"

DEFAULT_ARTIFACT_SUBDIR: Final[str] = "artifacts/eval"
LATEST_FILENAME: Final[str] = "ibridge_records.latest.jsonl"
SHADOW_LATEST_FILENAME: Final[str] = "shadow_ibridge_records.latest.jsonl"
SHADOW_DATED_PREFIX: Final[str] = "shadow_ibridge_records"
IBRIDGE_DATED_PREFIX: Final[str] = "ibridge_records"

# Fixture-aligned minimum + common metrics fields (eval_gate / eval_exporter).
EXPORT_FIELD_NAMES: Final[tuple[str, ...]] = (
    "task_id",
    "trace_id",
    "agent_name",
    "start_time",
    "end_time",
    "timestamp",
    "success",
    "retry_count",
    "handoff_count",
    "error_type",
    "tags",
    "context_token_usage",
    "trace_completeness",
    "step_count",
    "success_rate",
    "memory_hit_rate",
    "external_call_count",
)

_ALLOWED_DEPLOY_ENVS: Final[frozenset[str]] = frozenset(
    {"dev", "development", "local", "test", "staging", "stage", "ci"}
)
_BLOCKED_DEPLOY_ENVS: Final[frozenset[str]] = frozenset({"prod", "production"})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _today_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def resolve_deploy_env(explicit: str | None = None) -> str:
    """Resolve deploy environment label (lowercase)."""
    if explicit is not None and str(explicit).strip():
        return str(explicit).strip().lower()
    for key in (ENV_DEPLOY_ENV, "GOV_ENV", "DEPLOY_ENV"):
        raw = os.environ.get(key, "").strip()
        if raw:
            return raw.lower()
    return "dev"


def export_allowed(*, deploy_env: str | None = None, force: bool = False) -> dict[str, Any]:
    """
    Return whether JSONL export is permitted for this process.

    Enabled when ``IBRIDGE_EXPORT_ENABLED=1`` or deploy env is dev/staging-like.
    Blocked for production unless ``IBRIDGE_EXPORT_ALLOW_PRODUCTION=1`` (tests only).
    """
    if force:
        return {"ok": True, "allowed": True, "deploy_env": resolve_deploy_env(deploy_env), "reason": "force"}

    env = resolve_deploy_env(deploy_env)
    enabled_flag = os.environ.get(ENV_EXPORT_ENABLED, "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

    if env in _BLOCKED_DEPLOY_ENVS:
        allow_prod = os.environ.get(ENV_ALLOW_PRODUCTION, "").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        if not allow_prod:
            return {
                "ok": False,
                "allowed": False,
                "deploy_env": env,
                "reason": "production export blocked (set IBRIDGE_EXPORT_ALLOW_PRODUCTION=1 only in tests)",
            }

    if enabled_flag or env in _ALLOWED_DEPLOY_ENVS:
        return {
            "ok": True,
            "allowed": True,
            "deploy_env": env,
            "reason": "enabled_flag" if enabled_flag else "deploy_env",
        }

    return {
        "ok": False,
        "allowed": False,
        "deploy_env": env,
        "reason": (
            f"export disabled for deploy_env={env!r}; "
            f"set {ENV_EXPORT_ENABLED}=1 or use dev/staging"
        ),
    }


def resolve_artifact_dir(
    *,
    repo_root: Path | None = None,
    deploy_env: str | None = None,
) -> Path:
    """``artifacts/eval`` under repo root (or ``IBRIDGE_EXPORT_ROOT``)."""
    _ = deploy_env  # reserved for per-env subdirs later
    custom = os.environ.get(ENV_EXPORT_ROOT, "").strip()
    if custom:
        return Path(custom)
    root = repo_root or _find_repo_root()
    return root / DEFAULT_ARTIFACT_SUBDIR


def latest_filename_for_profile(profile: ArtifactProfile) -> str:
    if profile == "shadow":
        return SHADOW_LATEST_FILENAME
    return LATEST_FILENAME


def dated_prefix_for_profile(profile: ArtifactProfile) -> str:
    if profile == "shadow":
        return SHADOW_DATED_PREFIX
    return IBRIDGE_DATED_PREFIX


def default_output_paths(
    artifact_dir: Path,
    *,
    dated: bool = True,
    profile: ArtifactProfile = "ibridge",
) -> tuple[Path, Path | None]:
    """Return ``(dated_path, latest_path)`` for the given artifact profile."""
    latest = artifact_dir / latest_filename_for_profile(profile)
    if not dated:
        return latest, latest
    dated_name = f"{dated_prefix_for_profile(profile)}.{_today_stamp()}.jsonl"
    return artifact_dir / dated_name, latest


def _find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "observability" / "eval_gate.py").is_file():
            return parent
    return Path.cwd()


def normalize_ibridge_record(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize a metrics / ibridge dict to fixture-compatible JSONL shape.

    Unwraps nested ``ibridge_record`` / ``record`` / ``metrics_record`` when present.
    Ensures ``end_time`` falls back to ``timestamp`` / ``start_time``.
    """
    record = dict(raw)
    for key in ("ibridge_record", "record", "metrics_record"):
        nested = record.get(key)
        if isinstance(nested, dict):
            record = dict(nested)
            break

    if not record.get("end_time"):
        for fallback in ("timestamp", "start_time"):
            if record.get(fallback):
                record["end_time"] = record[fallback]
                break

    if record.get("timestamp") is None and record.get("end_time"):
        record["timestamp"] = record["end_time"]

    if not record.get("trace_id") and record.get("task_id"):
        record["trace_id"] = f"trace-{record['task_id']}"

    out: dict[str, Any] = {}
    for key in EXPORT_FIELD_NAMES:
        if key in record:
            out[key] = record[key]

    # Always retain identifiers even if absent from EXPORT_FIELD_NAMES iteration order issues.
    for required in ("task_id", "trace_id", "success"):
        if required in record and required not in out:
            out[required] = record[required]

    return out


def _coerce_tags(raw: Any) -> list[str]:
    """Normalize k2_summary tags to list[str]; missing or invalid → []."""
    if raw is None:
        return []
    if not isinstance(raw, list):
        return []
    return [str(t) for t in raw]


def _k2_summary_to_ibridge(
    summary: dict[str, Any],
    parent: dict[str, Any],
) -> dict[str, Any]:
    """Map ``compare_shadow_profiles`` k2_summary → flat ibridge metrics row."""
    task_id = (
        parent.get("task_id")
        or parent.get("case_name")
        or summary.get("task_id")
        or "shadow-k2-unknown"
    )
    trace_id = parent.get("trace_id") or f"trace-{task_id}"
    end_time = parent.get("end_time") or parent.get("timestamp")
    ok_val = summary.get("ok")
    success = bool(ok_val) if ok_val is not None else True
    tags = _coerce_tags(summary.get("tags") or [])

    record: dict[str, Any] = {
        "task_id": str(task_id),
        "trace_id": str(trace_id),
        "agent_name": "k2_shadow",
        "success": success,
        "retry_count": summary.get("retry_count", 0),
        "handoff_count": summary.get("handoff_count", 0),
        "error_type": summary.get("error_type"),
        "tags": tags,
        "context_token_usage": parent.get("context_token_usage") or {"total_tokens": 0},
        "trace_completeness": parent.get("trace_completeness") or {"score": 1.0},
    }
    if end_time:
        record["end_time"] = end_time
        record["timestamp"] = end_time
    return record


def normalize_shadow_record(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize prod shadow spool lines to flat ibridge shape for ``eval_ci_check``.

  Accepts:
    - flat / wrapped ibridge rows (delegates to ``normalize_ibridge_record``)
    - K-2 ``run_k2_flow`` payloads with nested ``record``
    - merge envelopes with ``k2_metrics_record``
    - shadow comparison dicts with ``k2_summary`` (K-2 path only)
    """
    if not isinstance(raw, dict):
        raise ValueError(f"expected object, got {type(raw).__name__}")

    nested_record = raw.get("record")
    if isinstance(nested_record, dict) and (
        nested_record.get("task_id")
        or nested_record.get("retry_count") is not None
        or nested_record.get("success") is not None
    ):
        merged = dict(nested_record)
        for key in ("task_id", "trace_id", "end_time", "timestamp", "agent_name"):
            if raw.get(key) is not None and merged.get(key) is None:
                merged[key] = raw[key]
        return normalize_ibridge_record(merged)

    kmr = raw.get("k2_metrics_record")
    if isinstance(kmr, dict):
        merged = dict(kmr)
        task_id = raw.get("task_id") or merged.get("task_id")
        if task_id is None:
            task_id = f"shadow-{raw.get('case_name') or 'merge'}"
        merged.setdefault("task_id", task_id)
        for key in ("trace_id", "end_time", "timestamp", "agent_name", "error_type"):
            if raw.get(key) is not None and merged.get(key) is None:
                merged[key] = raw[key]
        if merged.get("context_token_usage") is None:
            merged["context_token_usage"] = {"total_tokens": 0}
        if merged.get("trace_completeness") is None:
            merged["trace_completeness"] = {"score": 1.0}
        return normalize_ibridge_record(merged)

    k2_summary = raw.get("k2_summary")
    if isinstance(k2_summary, dict):
        return normalize_ibridge_record(_k2_summary_to_ibridge(k2_summary, raw))

    if raw.get("pipeline") == "k2" and raw.get("retry_count") is not None:
        return normalize_ibridge_record(_k2_summary_to_ibridge(raw, raw))

    return normalize_ibridge_record(raw)


def validate_normalized_record(record: dict[str, Any]) -> dict[str, Any]:
    """Check fixture-minimum fields for eval_exporter consumption."""
    missing = [k for k in ("task_id", "trace_id") if not record.get(k)]
    if missing:
        return {"ok": False, "message": f"missing required fields: {missing}"}
    if record.get("end_time") is None and record.get("timestamp") is None:
        return {"ok": False, "message": "missing end_time or timestamp"}
    if "success" not in record:
        return {"ok": False, "message": "missing success"}
    return {"ok": True, "message": "ok"}


def iter_collector_records(*, ended_only: bool = True) -> Iterator[dict[str, Any]]:
    """Yield normalized records from the process-wide metrics collector."""
    from metrics import get_collector

    listed = get_collector().list_tasks()
    if not listed.get("ok"):
        return
    records = listed.get("records") or []
    for raw in records:
        if not isinstance(raw, dict):
            continue
        if ended_only and not raw.get("end_time"):
            continue
        yield normalize_ibridge_record(raw)


def iter_file_records(path: Path) -> Iterator[dict[str, Any]]:
    """Yield normalized records from JSON/JSONL input."""
    for record, _line_index in iter_records(path):
        yield normalize_ibridge_record(record)


def iter_shadow_records(path: Path) -> Iterator[dict[str, Any]]:
    """Yield flat ibridge rows from prod shadow / K-2 spool JSONL."""
    for record, _line_index in iter_records(path):
        yield normalize_shadow_record(record)


def iter_source_records(
    source: SourceKind,
    *,
    input_path: Path | None = None,
    ended_only: bool = True,
) -> Iterator[dict[str, Any]]:
    if source == "collector":
        yield from iter_collector_records(ended_only=ended_only)
        return
    if source == "file":
        if input_path is None:
            raise ValueError("input_path required when source=file")
        yield from iter_file_records(input_path)
        return
    if source == "shadow":
        if input_path is None:
            raise ValueError("input_path required when source=shadow")
        yield from iter_shadow_records(input_path)
        return
    raise ValueError(f"unsupported source: {source}")


def _sort_key(record: dict[str, Any]) -> str:
    for key in ("end_time", "timestamp", "start_time", "task_id"):
        val = record.get(key)
        if val is not None:
            return str(val)
    return ""


def export_ibridge_jsonl(
    *,
    source: SourceKind = "collector",
    input_path: Path | None = None,
    output_path: Path | None = None,
    artifact_dir: Path | None = None,
    limit: int | None = None,
    deploy_env: str | None = None,
    write_latest: bool = True,
    ended_only: bool = True,
    force: bool = False,
    profile: ArtifactProfile = "ibridge",
) -> dict[str, Any]:
    """
    Write normalized ibridge records to JSONL.

    Returns structured dict with ``ok``, ``message``, ``written``, paths, etc.
    """
    gate = export_allowed(deploy_env=deploy_env, force=force)
    if not gate.get("allowed"):
        return {
            "ok": False,
            "message": gate.get("reason", "export not allowed"),
            "written": 0,
            "skipped_invalid": 0,
            "deploy_env": gate.get("deploy_env"),
        }

    env_label = gate.get("deploy_env") or resolve_deploy_env(deploy_env)
    out_dir = artifact_dir or resolve_artifact_dir(deploy_env=env_label)
    dated_path, latest_path = default_output_paths(out_dir, profile=profile)
    primary_out = output_path or dated_path
    primary_out.parent.mkdir(parents=True, exist_ok=True)

    collected: list[dict[str, Any]] = []
    skipped_invalid = 0
    for record in iter_source_records(source, input_path=input_path, ended_only=ended_only):
        check = validate_normalized_record(record)
        if not check.get("ok"):
            skipped_invalid += 1
            continue
        collected.append(record)

    collected.sort(key=_sort_key, reverse=True)
    if limit is not None and limit > 0:
        collected = collected[:limit]

    written = 0
    lines: list[str] = []
    for record in collected:
        lines.append(json.dumps(record, ensure_ascii=False))
        written += 1

    payload = "\n".join(lines)
    if payload:
        payload += "\n"

    primary_out.write_text(payload, encoding="utf-8")
    latest_written: str | None = None
    if write_latest and latest_path is not None and latest_path != primary_out:
        latest_path.parent.mkdir(parents=True, exist_ok=True)
        latest_path.write_text(payload, encoding="utf-8")
        latest_written = str(latest_path)

    return {
        "ok": True,
        "message": (
            f"exported {written} ibridge record(s) from source={source} "
            f"(deploy_env={env_label})"
        ),
        "written": written,
        "skipped_invalid": skipped_invalid,
        "source": source,
        "deploy_env": env_label,
        "output_path": str(primary_out),
        "latest_path": latest_written,
        "exported_at": _utc_now_iso(),
        "profile": profile,
    }


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export real ibridge/metrics records to JSONL (dev/staging only).",
    )
    parser.add_argument(
        "--source",
        choices=("collector", "file", "shadow"),
        default="collector",
        help="Record source: collector, JSON/JSONL file, or K-2 shadow spool",
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        type=Path,
        help="Input path when --source=file or --source=shadow",
    )
    parser.add_argument(
        "--profile",
        choices=("ibridge", "shadow"),
        default=None,
        help="Artifact naming profile (default: shadow when --source=shadow, else ibridge)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output JSONL path (default: artifacts/eval/ibridge_records.YYYYMMDD.jsonl)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max records to write (most recent by end_time)",
    )
    parser.add_argument(
        "--env",
        "--mode",
        dest="deploy_env",
        default=None,
        help="Deploy environment label (dev, staging, production); default from GOV_DEPLOY_ENV",
    )
    parser.add_argument(
        "--no-latest",
        action="store_true",
        help="Do not also write ibridge_records.latest.jsonl",
    )
    parser.add_argument(
        "--include-in-progress",
        action="store_true",
        help="Include collector tasks without end_time",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass deploy_env gate (unit tests only)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_cli().parse_args(argv)
    if args.source in ("file", "shadow") and args.input_path is None:
        print(
            json.dumps(
                {
                    "ok": False,
                    "message": f"input_path required when --source={args.source}",
                },
                ensure_ascii=False,
            )
        )
        return 1

    profile: ArtifactProfile = args.profile or (
        "shadow" if args.source == "shadow" else "ibridge"
    )
    out_path = args.output
    artifact_dir = out_path.parent if out_path else None

    result = export_ibridge_jsonl(
        source=args.source,
        input_path=args.input_path,
        output_path=out_path,
        artifact_dir=artifact_dir,
        limit=args.limit,
        deploy_env=args.deploy_env,
        write_latest=not args.no_latest,
        ended_only=not args.include_in_progress,
        force=args.force,
        profile=profile,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
