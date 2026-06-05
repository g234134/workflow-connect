"""
CI enforcement preview wrapper (Phase A — preview only).

Reads dry-run per-record JSONL, evaluates ENF-RULE candidates, and emits
structured [GOV-ENF-PREVIEW] lines. Always exits 0 — never influences pipeline pass/fail.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Final, Literal

from observability.enf_config import load_enf_config, log_enf_config

LOG_PREFIX = "[GOV-ENF-PREVIEW]"
DECISION_SUMMARY_PREFIX: Final[str] = "[GOV-ENF-SHADOW-SUMMARY]"
SHADOW_SAMPLE_LIMIT: Final[int] = 5
PREVIEW_DISCLAIMER: Final[str] = (
    "⚠ PREVIEW — 未實施 enforcement，不影響 pipeline 結果"
)

# ENF-RULE-1 (L2 candidate) — POLICY-MINING-01 §3.1 C-01
ENF_RULE_1_NAME: Final[str] = "ENF-RULE-1"
ENF_RULE_1_DRYRUN_RULE: Final[str] = "gate_fail_deny"
ENF_RULE_1_RISK_TAGS: Final[frozenset[str]] = frozenset({"infra_risk", "security:critical"})
ENF_RULE_1_DEFAULT_MIN_SCORE: Final[float] = 0.7

# ENF-RULE-2 (L1 observe) — POLICY-MINING-01 §3.1 C-03
ENF_RULE_2_NAME: Final[str] = "ENF-RULE-2"
ENF_RULE_2_DRYRUN_RULE: Final[str] = "gate_fail_needs_review"
ENF_RULE_2_TAG: Final[str] = "high_retry"
ENF_RULE_2_MIN_RETRY: Final[int] = 2

# C3-05-L1-INFRA-RISK-SUCCESS — POLICY-MINING-01 §3.1 C-05
ENF_RULE_C3_05_NAME: Final[str] = "C3-05-L1-INFRA-RISK-SUCCESS"
ENF_RULE_C3_05_TAG: Final[str] = "infra_risk"
ENF_WARN_PREFIX: Final[str] = "[ENF-WARN]"
_ALLOW_VERDICTS: Final[frozenset[str]] = frozenset({"allow", "pass", "approve"})
_DENY_VERDICTS: Final[frozenset[str]] = frozenset({"deny", "fail", "rejected", "blocked"})

PreviewOutcome = Literal["block", "warn", "noop"]


def _block_sample_fields(row: dict[str, Any]) -> dict[str, Any]:
    """Key fields for would_block samples in shadow decision summary."""
    metrics = row.get("metrics") or {}
    tags = list(row.get("tags") or [])
    sample: dict[str, Any] = {
        "task_id": row.get("task_id"),
        "dryrun_rule": row.get("dryrun_rule"),
        "gate_result": row.get("gate_result"),
        "error_type": metrics.get("error_type"),
    }
    if tags:
        sample["tags"] = tags
    return sample


def build_decision_summary_payload(
    *,
    status: str,
    input_path: str | None = None,
    min_score: float | None = None,
    total: int = 0,
    would_block: int = 0,
    would_warn: int = 0,
    would_noop: int = 0,
    rule1_blocks: int = 0,
    rule2_warns: int = 0,
    c3_05_warns: int = 0,
    block_samples: list[dict[str, Any]] | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Structured shadow/dryrun decision summary (parseable JSON object)."""
    payload: dict[str, Any] = {
        "mode": "shadow",
        "status": status,
        "exit_policy": "preview_only",
        "total": total,
        "would_block": would_block,
        "would_warn": would_warn,
        "would_noop": would_noop,
        "rules": {
            ENF_RULE_1_NAME: {"would_block": rule1_blocks},
            ENF_RULE_2_NAME: {
                "would_warn": rule2_warns,
                "shadow_retries": rule2_warns,
            },
            ENF_RULE_C3_05_NAME: {"would_warn": c3_05_warns},
        },
    }
    if input_path is not None:
        payload["input"] = input_path
    if min_score is not None:
        payload["min_score"] = min_score
    if reason is not None:
        payload["reason"] = reason
    if block_samples:
        payload["samples"] = {
            "would_block": [_block_sample_fields(row) for row in block_samples],
        }
    return payload


def _emit_decision_summary(payload: dict[str, Any]) -> None:
    """Emit a single JSON line for nightly log grep/parse (shadow/dryrun only)."""
    line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    print(f"{DECISION_SUMMARY_PREFIX} {line}", flush=True)


def _emit(event: str, *, warn: bool = False, **fields: object) -> None:
    parts = [LOG_PREFIX]
    if warn:
        parts.append("[WARN]")
    parts.append(f"event={event}")
    for key, value in fields.items():
        if value is None:
            continue
        text = str(value).replace("\n", " ")
        parts.append(f"{key}={text}")
    print(" ".join(parts), flush=True)


def _discover_latest_per_record(input_dir: Path) -> Path | None:
    candidates = sorted(input_dir.glob("*_per_record.jsonl"), key=lambda p: p.name)
    return candidates[-1] if candidates else None


def _load_per_record_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _record_has_risk_tag(tags: list[str]) -> bool:
    return any(tag in ENF_RULE_1_RISK_TAGS for tag in tags)


def _emit_enf_warn(rule: str, **fields: object) -> None:
    """Emit a structured L1 warning line (does not affect exit code or verdict)."""
    parts = [ENF_WARN_PREFIX, f"rule={rule}"]
    for key, value in fields.items():
        if value is None:
            continue
        text = str(value).replace("\n", " ")
        parts.append(f"{key}={text}")
    print(" ".join(parts), flush=True)


def _resolve_actual_verdict(row: dict[str, Any]) -> str | None:
    raw = row.get("actual_verdict") or row.get("verdict")
    if isinstance(raw, str) and raw.strip():
        return raw.strip().lower()
    return None


def _is_allow_verdict(row: dict[str, Any]) -> bool:
    actual = _resolve_actual_verdict(row)
    return actual in _ALLOW_VERDICTS if actual is not None else False


def _is_deny_record(row: dict[str, Any]) -> bool:
    """True when record is already denied — C3-05 must stay silent to avoid noise."""
    actual = _resolve_actual_verdict(row)
    if actual in _DENY_VERDICTS:
        return True
    return row.get("dryrun_rule") == ENF_RULE_1_DRYRUN_RULE


def should_emit_c3_05_warning(row: dict[str, Any]) -> bool:
    """
    C3-05-L1-INFRA-RISK-SUCCESS: allow + infra_risk tag → L1 warning only.

    Independent of ENF-RULE-1/2; never changes verdict or exit code.
    """
    tags = list(row.get("tags") or [])
    if ENF_RULE_C3_05_TAG not in tags:
        return False
    if _is_deny_record(row):
        return False
    return _is_allow_verdict(row)


def classify_preview_outcome(
    row: dict[str, Any],
    *,
    min_score: float,
) -> tuple[PreviewOutcome, str | None]:
    """
    Apply ENF-RULE-1 then ENF-RULE-2; everything else is would_noop.

    Returns (outcome, rule_name_or_none).
    """
    dryrun_rule = row.get("dryrun_rule")
    metrics = row.get("metrics") or {}
    tags = list(row.get("tags") or [])
    error_type = metrics.get("error_type")
    retry_count = int(metrics.get("retry_count") or 0)
    score_raw = metrics.get("trace_completeness_score")

    # ENF-RULE-1 (L2 candidate): gate_fail_deny + error_type + risk tag + score threshold
    if dryrun_rule == ENF_RULE_1_DRYRUN_RULE:
        if error_type is not None and _record_has_risk_tag(tags):
            if score_raw is not None:
                try:
                    score = float(score_raw)
                except (TypeError, ValueError):
                    score = None
                if score is not None and score >= min_score:
                    return "block", ENF_RULE_1_NAME

    # ENF-RULE-2 (L1 observe): gate_fail_needs_review + high_retry + retry_count
    elif dryrun_rule == ENF_RULE_2_DRYRUN_RULE:
        if ENF_RULE_2_TAG in tags and retry_count >= ENF_RULE_2_MIN_RETRY:
            return "warn", ENF_RULE_2_NAME

    return "noop", None


def run_preview(
    *,
    input_path: Path | None,
    input_dir: Path | None,
    output_path: Path | None,
    min_score: float,
    verbose: bool,
) -> None:
    print(f"{LOG_PREFIX} {PREVIEW_DISCLAIMER}", flush=True)

    resolved: Path | None = input_path
    if resolved is None and input_dir is not None:
        if not input_dir.is_dir():
            _emit(
                "skip",
                warn=True,
                reason="input_dir_not_found",
                input_dir=input_dir.as_posix(),
            )
            _emit_decision_summary(
                build_decision_summary_payload(
                    status="skipped",
                    reason="input_dir_not_found",
                )
            )
            _emit("complete", status="skipped", exit_policy="preview_only")
            return
        resolved = _discover_latest_per_record(input_dir)
        if resolved is None:
            _emit(
                "skip",
                warn=True,
                reason="no_per_record_artefact",
                input_dir=input_dir.as_posix(),
            )
            _emit_decision_summary(
                build_decision_summary_payload(
                    status="skipped",
                    reason="no_per_record_artefact",
                )
            )
            _emit("complete", status="skipped", exit_policy="preview_only")
            return

    if resolved is None or not resolved.is_file():
        target = (input_path or input_dir or Path(".")).as_posix()
        _emit("skip", warn=True, reason="input_not_found", input=target)
        _emit_decision_summary(
            build_decision_summary_payload(
                status="skipped",
                reason="input_not_found",
            )
        )
        _emit("complete", status="skipped", exit_policy="preview_only")
        return

    rows = _load_per_record_rows(resolved)
    if not rows:
        _emit(
            "skip",
            warn=True,
            reason="no_records_loaded",
            input=resolved.as_posix(),
        )
        _emit_decision_summary(
            build_decision_summary_payload(
                status="skipped",
                input_path=resolved.as_posix(),
                reason="no_records_loaded",
            )
        )
        _emit("complete", status="skipped", exit_policy="preview_only")
        return

    would_block = 0
    would_warn = 0
    would_noop = 0
    rule1_blocks = 0
    rule2_warns = 0
    c3_05_warns = 0
    block_samples: list[dict[str, Any]] = []
    warn_samples: list[dict[str, Any]] = []
    c3_05_samples: list[dict[str, Any]] = []

    for row in rows:
        outcome, rule_name = classify_preview_outcome(row, min_score=min_score)
        if outcome == "block":
            would_block += 1
            rule1_blocks += 1
            if len(block_samples) < SHADOW_SAMPLE_LIMIT:
                block_samples.append(row)
        elif outcome == "warn":
            would_warn += 1
            rule2_warns += 1
            if verbose or len(warn_samples) < 5:
                warn_samples.append(row)
        else:
            would_noop += 1

        if should_emit_c3_05_warning(row):
            c3_05_warns += 1
            if verbose or len(c3_05_samples) < 5:
                c3_05_samples.append(row)

    total = len(rows)
    _emit(
        "summary",
        total=total,
        would_block=would_block,
        would_warn=would_warn,
        would_noop=would_noop,
        input=resolved.as_posix(),
    )
    _emit(
        "detail",
        rule=ENF_RULE_1_NAME,
        would_block=rule1_blocks,
        min_score=min_score,
    )
    _emit(
        "detail",
        rule=ENF_RULE_2_NAME,
        would_warn=rule2_warns,
    )
    _emit(
        "detail",
        rule=ENF_RULE_C3_05_NAME,
        would_warn=c3_05_warns,
    )

    _emit_decision_summary(
        build_decision_summary_payload(
            status="ok",
            input_path=resolved.as_posix(),
            min_score=min_score,
            total=total,
            would_block=would_block,
            would_warn=would_warn,
            would_noop=would_noop,
            rule1_blocks=rule1_blocks,
            rule2_warns=rule2_warns,
            c3_05_warns=c3_05_warns,
            block_samples=block_samples,
        )
    )

    for row in c3_05_samples:
        _emit_enf_warn(
            ENF_RULE_C3_05_NAME,
            task_id=row.get("task_id"),
            actual_verdict=row.get("actual_verdict"),
            dryrun_rule=row.get("dryrun_rule"),
            tags=",".join(row.get("tags") or []),
            message="success_with_infra_risk_tag",
        )

    if verbose:
        for row in block_samples:
            _emit(
                "would_block",
                task_id=row.get("task_id"),
                rule=ENF_RULE_1_NAME,
                dryrun_rule=row.get("dryrun_rule"),
            )
        for row in warn_samples:
            _emit(
                "would_warn",
                task_id=row.get("task_id"),
                rule=ENF_RULE_2_NAME,
                dryrun_rule=row.get("dryrun_rule"),
            )

    if output_path is not None:
        payload = {
            "input": resolved.as_posix(),
            "min_score": min_score,
            "total": total,
            "would_block": would_block,
            "would_warn": would_warn,
            "would_noop": would_noop,
            "rules": {
                ENF_RULE_1_NAME: {"would_block": rule1_blocks},
                ENF_RULE_2_NAME: {"would_warn": rule2_warns},
                ENF_RULE_C3_05_NAME: {"would_warn": c3_05_warns},
            },
            "exit_policy": "preview_only",
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        _emit("artefact", summary=output_path.as_posix())

    _emit("complete", status="ok", exit_policy="preview_only")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Enforcement preview wrapper for nightly CI (always exit 0).",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Dry-run per-record JSONL path (repo-relative).",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help="Directory containing *_per_record.jsonl; uses latest by name.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON summary output path.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=ENF_RULE_1_DEFAULT_MIN_SCORE,
        help=f"ENF-RULE-1 trace score threshold (default: {ENF_RULE_1_DEFAULT_MIN_SCORE}).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Emit per-record would_block / would_warn lines.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    enf_config = load_enf_config()
    log_enf_config(enf_config)
    if not enf_config.should_run_enf:
        _emit(
            "skip",
            reason="env_disabled",
            gov_enf_enable=enf_config.gov_enf_enable_raw,
            enf_enable=enf_config.enf_enable_raw,
        )
        _emit("complete", status="skipped", exit_policy="preview_only")
        return 0

    if args.input is None and args.input_dir is None:
        args.input_dir = Path("observability/dryrun")

    try:
        run_preview(
            input_path=args.input,
            input_dir=args.input_dir,
            output_path=args.output,
            min_score=args.min_score,
            verbose=args.verbose,
        )
    except Exception as exc:  # noqa: BLE001 — preview must never fail the job
        _emit("error", warn=True, type=type(exc).__name__, message=str(exc))
        _emit_decision_summary(
            build_decision_summary_payload(
                status="error_logged",
                reason=f"{type(exc).__name__}: {exc}",
            )
        )
        _emit("complete", status="error_logged", exit_policy="preview_only")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
