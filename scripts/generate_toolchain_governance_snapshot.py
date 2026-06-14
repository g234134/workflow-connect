#!/usr/bin/env python3
"""Non-blocking toolchain governance snapshot (WC-PRE-06/07 · L0/L1 observability).

Aggregates smoke matrix metadata, optional CI smoke observations, toolchain
health dashboard embed, coverage counts, recent error summaries, and L1
advisory findings for missing critical signals. Does not change any PR gate
pass/fail semantics.

Usage:
    python scripts/generate_toolchain_governance_snapshot.py --write
    python scripts/generate_toolchain_governance_snapshot.py --ci-context eval-gate-pr --write --non-blocking
    python scripts/generate_toolchain_governance_snapshot.py --format json --no-write
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_SCHEMA_VERSION = "toolchain_governance_snapshot_v1"
_GATE_CLASS = "optional"
_BLOCKS_MAINLINE = False
_DEFAULT_OUTPUT_DIR = "output/toolchain"
_MATRIX_REL = "routing/toolchain_smoke_matrix_v1.yaml"

AdvisorySeverity = Literal["warn", "critical"]
AdvisoryLevel = Literal["none", "warn", "critical"]

CiContext = Literal[
    "none",
    "eval-gate-pr",
    "eval-gate-nightly",
    "core-agent-smoke-pr",
]

# smoke_id -> (ci_step_label,) when the hosting workflow job succeeded.
_CI_OBSERVED_SMOKES: Dict[str, Tuple[str, ...]] = {
    "eval-gate-pr": (
        "TS-ROUTING-EVAL-UNIT",
        "TS-ROUTING-EVAL-DRYRUN",
    ),
    "eval-gate-nightly": (
        "TS-ROUTING-EVAL-UNIT",
        "TS-ROUTING-EVAL-DRYRUN",
    ),
    "core-agent-smoke-pr": (
        "TS-CORE-AGENT-SMOKE-PR",
    ),
}


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _rel_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _load_smoke_matrix(repo_root: Path) -> Dict[str, Any]:
    from scripts.run_toolchain_smoke_matrix import run_toolchain_smoke_matrix

    matrix_path = repo_root / _MATRIX_REL
    if not matrix_path.is_file():
        return {
            "loaded_ok": False,
            "load_message": f"matrix file not found: {_MATRIX_REL}",
            "matrix_schema_version": None,
            "matrix_revision": None,
            "source_yaml": _MATRIX_REL,
            "dry_run": {
                "ok": False,
                "entries_requested": 0,
                "results": [],
            },
            "entries": [],
        }

    dry_run = run_toolchain_smoke_matrix(
        tier="all",
        dry_run=True,
        repo_root=repo_root,
        matrix_path=matrix_path,
    )
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
        entries = data.get("entries") if isinstance(data, dict) else []
        if not isinstance(entries, list):
            entries = []
    except ImportError:
        entries = []
    return {
        "loaded_ok": dry_run.get("ok") is True,
        "load_message": dry_run.get("message"),
        "matrix_schema_version": dry_run.get("matrix_schema_version"),
        "matrix_revision": dry_run.get("matrix_revision"),
        "source_yaml": _MATRIX_REL,
        "dry_run": dry_run,
        "entries": entries,
    }


def _compute_coverage(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_tier: Dict[str, int] = {}
    by_gate_class: Dict[str, int] = {}
    blocks_mainline_count = 0
    for entry in entries:
        tier = str(entry.get("tier") or "unknown")
        gate_class = str(entry.get("gate_class") or "unknown")
        by_tier[tier] = by_tier.get(tier, 0) + 1
        by_gate_class[gate_class] = by_gate_class.get(gate_class, 0) + 1
        if entry.get("blocks_mainline") is True:
            blocks_mainline_count += 1
    total = len(entries)
    return {
        "smoke_entries_total": total,
        "by_tier": by_tier,
        "by_gate_class": by_gate_class,
        "blocks_mainline_count": blocks_mainline_count,
        "mandatory_count": by_gate_class.get("mandatory", 0),
        "optional_count": by_gate_class.get("optional", 0),
        "shadow_count": by_gate_class.get("shadow", 0),
    }


def _external_smoke_results(
    *,
    repo_root: Path,
    smoke_results_json: Optional[Path],
) -> Dict[str, Dict[str, Any]]:
    """Map smoke_id -> {last_result, message, source}."""
    mapped: Dict[str, Dict[str, Any]] = {}
    if smoke_results_json is None:
        return mapped

    path = smoke_results_json if smoke_results_json.is_absolute() else repo_root / smoke_results_json
    payload = _load_json(path)
    if payload is None:
        return mapped

    source = _rel_path(path, repo_root)

    # Core agent smoke CI summary shape.
    if isinstance(payload.get("smoke_result"), dict):
        smoke = payload["smoke_result"]
        ok = payload.get("ok") if "ok" in payload else smoke.get("ok")
        mapped["TS-CORE-AGENT-SMOKE-PR"] = {
            "last_result": "passed" if ok is True else "failed",
            "message": smoke.get("message") or payload.get("message"),
            "source": source,
            "observed_at": payload.get("generated_at") or _utc_now_iso(),
        }
        failed_tests = smoke.get("failed_tests") or []
        if failed_tests:
            mapped["TS-CORE-AGENT-SMOKE-PR"]["error_summary"] = "; ".join(
                str(item.get("message") or item.get("test_id") or "failure")
                for item in failed_tests[:5]
            )
        return mapped

    # Generic list of smoke runner result items.
    results = payload.get("results")
    if isinstance(results, list):
        for item in results:
            if not isinstance(item, dict):
                continue
            smoke_id = str(item.get("smoke_id") or "")
            if not smoke_id:
                continue
            ok_flag = item.get("ok")
            mapped[smoke_id] = {
                "last_result": (
                    "passed"
                    if ok_flag is True
                    else "failed"
                    if ok_flag is False
                    else "unknown"
                ),
                "message": item.get("message"),
                "source": source,
                "observed_at": _utc_now_iso(),
            }
            if ok_flag is False:
                mapped[smoke_id]["error_summary"] = str(
                    item.get("message") or f"exit_code={item.get('exit_code')}"
                )
    return mapped


def _build_component_rows(
    entries: List[Dict[str, Any]],
    *,
    ci_context: CiContext,
    external_results: Dict[str, Dict[str, Any]],
    generated_at: str,
) -> List[Dict[str, Any]]:
    observed_ids = set(_CI_OBSERVED_SMOKES.get(ci_context, ()))
    rows: List[Dict[str, Any]] = []
    for entry in entries:
        smoke_id = str(entry.get("smoke_id") or "")
        ext = external_results.get(smoke_id) or {}
        if smoke_id in ext:
            last_result = ext.get("last_result", "unknown")
            source = ext.get("source")
            error_summary = ext.get("error_summary")
            observed_at = ext.get("observed_at", generated_at)
        elif smoke_id in observed_ids and ci_context != "none":
            last_result = "passed"
            source = f"ci_context:{ci_context}"
            error_summary = None
            observed_at = generated_at
        else:
            last_result = "not_observed"
            source = None
            error_summary = None
            observed_at = None

        rows.append(
            {
                "smoke_id": smoke_id,
                "tier": entry.get("tier"),
                "gate_class": entry.get("gate_class"),
                "blocks_mainline": entry.get("blocks_mainline"),
                "last_result": last_result,
                "last_observed_at": observed_at,
                "source": source,
                "error_summary": error_summary,
            }
        )

    known_ids = {str(entry.get("smoke_id") or "") for entry in entries}
    for smoke_id, ext in external_results.items():
        if smoke_id in known_ids:
            continue
        rows.append(
            {
                "smoke_id": smoke_id,
                "tier": None,
                "gate_class": "optional",
                "blocks_mainline": False,
                "last_result": ext.get("last_result", "unknown"),
                "last_observed_at": ext.get("observed_at", generated_at),
                "source": ext.get("source"),
                "error_summary": ext.get("error_summary"),
            }
        )
    return rows


def _embed_toolchain_health(repo_root: Path) -> Dict[str, Any]:
    from scripts.run_toolchain_health_dashboard import build_toolchain_health

    payload = build_toolchain_health(repo_root=repo_root, dry_run=True)
    sections = payload.get("sections") or {}
    degraded_sections = [
        name
        for name, section in sections.items()
        if isinstance(section, dict) and section.get("status") == "degraded"
    ]
    return {
        "ok": payload.get("ok"),
        "schema_version": payload.get("schema_version"),
        "gate_class": payload.get("gate_class"),
        "blocks_mainline": payload.get("blocks_mainline"),
        "dry_run": payload.get("dry_run"),
        "aggregated_health_score": payload.get("aggregated_health_score"),
        "sections_populated": payload.get("sections_populated"),
        "sections_ok": payload.get("sections_ok"),
        "degraded_sections": degraded_sections,
        "message": payload.get("message"),
    }


def _collect_recent_errors(
    *,
    components: List[Dict[str, Any]],
    health_embed: Dict[str, Any],
) -> List[Dict[str, Any]]:
    errors: List[Dict[str, Any]] = []
    for row in components:
        if row.get("last_result") == "failed" and row.get("error_summary"):
            errors.append(
                {
                    "source": f"smoke:{row.get('smoke_id')}",
                    "severity": "failed",
                    "message": row.get("error_summary"),
                }
            )
    for section in health_embed.get("degraded_sections") or []:
        errors.append(
            {
                "source": f"toolchain_health.{section}",
                "severity": "degraded",
                "message": f"health section {section} is degraded",
            }
        )
    return errors[:20]


def _advisory_finding(
    *,
    code: str,
    severity: AdvisorySeverity,
    message: str,
    remedial_action: str,
) -> Dict[str, str]:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "remedial_action": remedial_action,
    }


def evaluate_governance_advisory(
    payload: Dict[str, Any],
    *,
    external_smoke_ids: Optional[Set[str]] = None,
    write_attempted: bool = False,
) -> Dict[str, Any]:
    """Evaluate MissingSignalRules v1 against an assembled snapshot payload."""
    findings: List[Dict[str, str]] = []
    ci_context = str(payload.get("ci_context") or "none")
    smoke_matrix = payload.get("smoke_matrix") or {}
    coverage = payload.get("coverage") or {}
    health = payload.get("toolchain_health_embed") or {}
    components = payload.get("components") or []
    output_paths = payload.get("output_paths") or {}
    external_ids = external_smoke_ids or set()

    by_id = {
        str(row.get("smoke_id")): row
        for row in components
        if row.get("smoke_id")
    }

    def _last_result(smoke_id: str) -> str:
        row = by_id.get(smoke_id)
        if row is None:
            return "not_observed"
        return str(row.get("last_result") or "not_observed")

    if smoke_matrix.get("loaded_ok") is not True:
        findings.append(
            _advisory_finding(
                code="MS-MATRIX-LOAD",
                severity="critical",
                message=(
                    "Smoke matrix failed to load "
                    f"({smoke_matrix.get('load_message') or 'loaded_ok != true'})"
                ),
                remedial_action=(
                    "Check routing/toolchain_smoke_matrix_v1.yaml exists and YAML is valid; "
                    "locally run: python scripts/run_toolchain_smoke_matrix.py "
                    "--list --format json"
                ),
            )
        )

    if coverage.get("smoke_entries_total", 0) == 0:
        findings.append(
            _advisory_finding(
                code="MS-MATRIX-EMPTY",
                severity="critical",
                message="Smoke matrix has zero entries (coverage.smoke_entries_total == 0)",
                remedial_action=(
                    "Ensure matrix entries is non-empty; do not delete the SSOT YAML"
                ),
            )
        )

    if health.get("ok") is not True:
        findings.append(
            _advisory_finding(
                code="MS-HEALTH-ASSEMBLY",
                severity="critical",
                message=(
                    "Toolchain health embed assembly failed "
                    f"({health.get('message') or 'ok != true'})"
                ),
                remedial_action=(
                    "Locally run: python scripts/run_toolchain_health_dashboard.py "
                    "--format json --dry-run --no-write and inspect message"
                ),
            )
        )

    sections_populated = health.get("sections_populated")
    if not isinstance(sections_populated, int) or sections_populated < 3:
        findings.append(
            _advisory_finding(
                code="MS-HEALTH-SECTIONS",
                severity="critical",
                message=(
                    "Toolchain health embed has fewer than 3 populated sections "
                    f"(sections_populated={sections_populated!r})"
                ),
                remedial_action=(
                    "Backfill outbox sources (agent_ci / metrics_summary / catalog); "
                    "see docs/toolchain-health-dashboard-v1.md"
                ),
            )
        )

    if ci_context != "none":
        observed_smokes = _CI_OBSERVED_SMOKES.get(ci_context, ())  # type: ignore[arg-type]
        missing_smokes = [
            smoke_id
            for smoke_id in observed_smokes
            if _last_result(smoke_id) == "not_observed"
            and smoke_id not in external_ids
        ]
        if missing_smokes:
            findings.append(
                _advisory_finding(
                    code="MS-CI-SMOKE-MISSING",
                    severity="critical",
                    message=(
                        f"CI context {ci_context!r} expects smoke observations but "
                        f"{len(missing_smokes)} smoke(s) are not_observed without external "
                        f"results: {', '.join(missing_smokes)}"
                    ),
                    remedial_action=(
                        "Confirm hosting workflow ran the expected smokes; for "
                        "core-agent-smoke ensure smoke_ci_summary.json is passed via "
                        "--smoke-results-json"
                    ),
                )
            )

        failed_smokes = [
            smoke_id
            for smoke_id in observed_smokes
            if _last_result(smoke_id) == "failed"
        ]
        if failed_smokes:
            findings.append(
                _advisory_finding(
                    code="MS-CI-SMOKE-FAILED",
                    severity="critical",
                    message=(
                        f"CI context {ci_context!r} has failed smoke(s): "
                        f"{', '.join(failed_smokes)}"
                    ),
                    remedial_action=(
                        "Read error_summary / artifacts and fix the corresponding unittest "
                        "or smoke runner"
                    ),
                )
            )

    optional_ci_rows = [
        row for row in components if row.get("tier") == "optional_ci"
    ]
    if optional_ci_rows and all(
        row.get("last_result") == "not_observed" for row in optional_ci_rows
    ):
        smoke_ids = ", ".join(str(row.get("smoke_id")) for row in optional_ci_rows)
        findings.append(
            _advisory_finding(
                code="MS-OPTIONAL-CI-GAP",
                severity="warn",
                message=(
                    "All optional_ci tier matrix entries are not_observed "
                    f"({smoke_ids})"
                ),
                remedial_action=(
                    "Expected when WC-PRE-07 smoke CI step is not wired or not run; "
                    "locally: python scripts/run_toolchain_smoke_matrix.py "
                    "--tier optional_ci --dry-run"
                ),
            )
        )

    degraded_sections = health.get("degraded_sections") or []
    if degraded_sections:
        findings.append(
            _advisory_finding(
                code="MS-HEALTH-DEGRADED",
                severity="warn",
                message=(
                    "Toolchain health embed has degraded sections: "
                    f"{', '.join(str(item) for item in degraded_sections)}"
                ),
                remedial_action=(
                    "Classify infra_gap vs regression; see rollout plan section 4.1 "
                    "outbox gap mitigation"
                ),
            )
        )

    if write_attempted and not output_paths.get("json"):
        findings.append(
            _advisory_finding(
                code="MS-SNAPSHOT-ARTIFACT",
                severity="warn",
                message=(
                    "Snapshot write was requested but output_paths.json is missing "
                    "(artifact write may have failed)"
                ),
                remedial_action=(
                    "Check output/toolchain/ permissions and workflow upload path"
                ),
            )
        )

    has_critical = any(item["severity"] == "critical" for item in findings)
    has_warn = any(item["severity"] == "warn" for item in findings)
    if has_critical:
        advisory_level: AdvisoryLevel = "critical"
    elif has_warn:
        advisory_level = "warn"
    else:
        advisory_level = "none"

    critical_count = sum(1 for item in findings if item["severity"] == "critical")
    warn_count = sum(1 for item in findings if item["severity"] == "warn")
    if advisory_level == "none":
        advisory_summary = "No missing-signal advisories detected"
    else:
        advisory_summary = (
            f"L1 advisory_level={advisory_level}: "
            f"{critical_count} critical, {warn_count} warn finding(s)"
        )

    return {
        "advisory_level": advisory_level,
        "advisory_findings": findings,
        "advisory_summary": advisory_summary,
    }


def attach_governance_advisory(
    payload: Dict[str, Any],
    *,
    external_smoke_ids: Optional[Set[str]] = None,
    write_attempted: bool = False,
) -> Dict[str, Any]:
    """Merge MissingSignalRules v1 advisory fields into snapshot payload."""
    advisory = evaluate_governance_advisory(
        payload,
        external_smoke_ids=external_smoke_ids,
        write_attempted=write_attempted,
    )
    payload.update(advisory)
    return payload


def build_toolchain_governance_snapshot(
    *,
    repo_root: Path,
    ci_context: CiContext = "none",
    smoke_results_json: Optional[Path] = None,
    github_run_id: Optional[str] = None,
    github_sha: Optional[str] = None,
) -> Dict[str, Any]:
    """Assemble toolchain_governance_snapshot_v1 dict (read-only)."""
    root = repo_root.resolve()
    generated_at = _utc_now_iso()
    matrix_bundle = _load_smoke_matrix(root)
    entries = matrix_bundle.get("entries") or []
    coverage = _compute_coverage(entries)
    external = _external_smoke_results(
        repo_root=root,
        smoke_results_json=smoke_results_json,
    )
    components = _build_component_rows(
        entries,
        ci_context=ci_context,
        external_results=external,
        generated_at=generated_at,
    )
    health_embed = _embed_toolchain_health(root)
    recent_errors = _collect_recent_errors(
        components=components,
        health_embed=health_embed,
    )

    observed_passed = sum(1 for row in components if row.get("last_result") == "passed")
    observed_failed = sum(1 for row in components if row.get("last_result") == "failed")
    not_observed = sum(1 for row in components if row.get("last_result") == "not_observed")

    overall_ok = matrix_bundle.get("loaded_ok") is True and bool(entries)

    payload = {
        "ok": overall_ok,
        "schema_version": _SCHEMA_VERSION,
        "generated_at": generated_at,
        "gate_class": _GATE_CLASS,
        "blocks_mainline": _BLOCKS_MAINLINE,
        "non_blocking": True,
        "ci_context": ci_context,
        "github_run_id": github_run_id or os.environ.get("GITHUB_RUN_ID"),
        "github_sha": github_sha or os.environ.get("GITHUB_SHA"),
        "message": (
            f"governance snapshot assembled "
            f"({coverage.get('smoke_entries_total', 0)} matrix entries; "
            f"observed passed={observed_passed} failed={observed_failed} "
            f"not_observed={not_observed})"
        ),
        "coverage": coverage,
        "smoke_matrix": {
            "loaded_ok": matrix_bundle.get("loaded_ok"),
            "load_message": matrix_bundle.get("load_message"),
            "matrix_schema_version": matrix_bundle.get("matrix_schema_version"),
            "matrix_revision": matrix_bundle.get("matrix_revision"),
            "source_yaml": matrix_bundle.get("source_yaml"),
        },
        "components": components,
        "recent_errors": recent_errors,
        "toolchain_health_embed": health_embed,
        "output_paths": {},
    }
    return attach_governance_advisory(payload, external_smoke_ids=set(external.keys()))


def format_toolchain_governance_snapshot_markdown(payload: Dict[str, Any]) -> str:
    coverage = payload.get("coverage") or {}
    health = payload.get("toolchain_health_embed") or {}
    lines = [
        "# Toolchain Governance Snapshot",
        "",
        f"> Schema: `{payload.get('schema_version')}` · "
        f"Generated: `{payload.get('generated_at')}` · "
        f"Non-blocking: `{payload.get('non_blocking')}`",
        "",
        f"- **Overall ok**: `{payload.get('ok')}`",
        f"- **CI context**: `{payload.get('ci_context')}`",
        f"- **Gate class**: `{payload.get('gate_class')}` · "
        f"**blocks_mainline**: `{payload.get('blocks_mainline')}`",
        "",
        "## Coverage",
        "",
        f"- smoke entries total: **{coverage.get('smoke_entries_total', 0)}**",
        f"- by tier: `{coverage.get('by_tier')}`",
        f"- by gate_class: `{coverage.get('by_gate_class')}`",
        f"- blocks_mainline count: `{coverage.get('blocks_mainline_count', 0)}`",
        "",
        "## Toolchain health embed",
        "",
        f"- ok: `{health.get('ok')}` · score: `{health.get('aggregated_health_score')}` · "
        f"sections populated: `{health.get('sections_populated')}`",
        f"- degraded sections: `{health.get('degraded_sections') or []}`",
        "",
        "## Components (latest smoke observation)",
        "",
        "| smoke_id | tier | last_result | error |",
        "|----------|------|-------------|-------|",
    ]
    for row in payload.get("components") or []:
        err = row.get("error_summary") or ""
        if len(err) > 80:
            err = err[:77] + "..."
        lines.append(
            f"| {row.get('smoke_id')} | {row.get('tier')} | "
            f"{row.get('last_result')} | {err or '—'} |"
        )
    recent_errors = payload.get("recent_errors") or []
    lines.extend(["", "## Recent errors", ""])
    if recent_errors:
        for item in recent_errors:
            lines.append(
                f"- `{item.get('source')}` ({item.get('severity')}): {item.get('message')}"
            )
    else:
        lines.append("- *(none)*")
    findings = payload.get("advisory_findings") or []
    lines.extend(
        [
            "",
            "## Advisory (L1 · non-blocking)",
            "",
            f"- **advisory_level**: `{payload.get('advisory_level')}`",
            f"- **advisory_summary**: {payload.get('advisory_summary')}",
            "",
        ]
    )
    if findings:
        lines.append("| code | severity | message |")
        lines.append("|------|----------|---------|")
        for item in findings:
            msg = str(item.get("message") or "")
            if len(msg) > 100:
                msg = msg[:97] + "..."
            lines.append(
                f"| {item.get('code')} | {item.get('severity')} | {msg} |"
            )
    else:
        lines.append("- *(none)*")
    lines.append("")
    return "\n".join(lines)


def write_toolchain_governance_snapshot_artifacts(
    payload: Dict[str, Any],
    *,
    repo_root: Path,
    output_dir: Path,
) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "governance_snapshot.json"
    md_path = output_dir / "governance_snapshot.md"
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(
        format_toolchain_governance_snapshot_markdown(payload),
        encoding="utf-8",
    )
    log_path = output_dir / "governance_advisory.log"
    log_path.write_text(
        "\n".join(format_ci_log_summary_lines(payload)) + "\n",
        encoding="utf-8",
    )
    return {
        "json": _rel_path(json_path, repo_root),
        "markdown": _rel_path(md_path, repo_root),
        "advisory_log": _rel_path(log_path, repo_root),
    }


def print_github_advisory_annotations(findings: List[Dict[str, Any]]) -> None:
    for item in findings:
        if item.get("severity") != "critical":
            continue
        code = str(item.get("code") or "MS-UNKNOWN")
        message = str(item.get("message") or "critical advisory finding")
        # GitHub Actions workflow commands: keep title short, message on same line.
        print(f"::warning title={code}::{message}")


def format_ci_log_summary_lines(payload: Dict[str, Any]) -> List[str]:
    """Plain-text CI log lines (L0 snapshot trailer + L1 advisory block)."""
    paths = payload.get("output_paths") or {}
    coverage = payload.get("coverage") or {}
    health = payload.get("toolchain_health_embed") or {}
    errors = payload.get("recent_errors") or []
    findings = payload.get("advisory_findings") or []
    advisory_level = payload.get("advisory_level", "none")
    lines = [
        "=== Toolchain governance snapshot (non-blocking · WC-PRE-06/07 L0) ===",
        f"ok={payload.get('ok')} ci_context={payload.get('ci_context')}",
        (
            f"smoke_entries={coverage.get('smoke_entries_total')} "
            f"health_score={health.get('aggregated_health_score')} "
            f"sections_populated={health.get('sections_populated')}"
        ),
        f"recent_errors={len(errors)}",
    ]
    if paths:
        lines.append(f"artifact_json={paths.get('json')}")
        lines.append(f"artifact_markdown={paths.get('markdown')}")
        if paths.get("advisory_log"):
            lines.append(f"artifact_advisory_log={paths.get('advisory_log')}")
    lines.extend(
        [
            "This step does not affect PR gate pass/fail.",
            "=== end governance snapshot ===",
            "=== L1 governance advisory (non-blocking · WC-IMPL-L1) ===",
            f"advisory_level={advisory_level}",
            f"advisory_summary={payload.get('advisory_summary')}",
            f"advisory_findings={len(findings)}",
        ]
    )
    for item in findings:
        lines.append(
            f"  [{item.get('severity')}] {item.get('code')}: {item.get('message')}"
        )
    lines.extend(
        [
            "L1 advisory does not affect PR gate pass/fail.",
            "=== end L1 advisory ===",
        ]
    )
    return lines


def print_ci_log_summary(payload: Dict[str, Any]) -> None:
    for line in format_ci_log_summary_lines(payload):
        print(line)
    print_github_advisory_annotations(payload.get("advisory_findings") or [])


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate non-blocking toolchain governance snapshot "
            "(WC-PRE-06/07 L0/L1 observability)."
        ),
    )
    parser.add_argument(
        "--repo-root",
        default=str(_REPO_ROOT),
        help="Repository root",
    )
    parser.add_argument(
        "--ci-context",
        choices=(
            "none",
            "eval-gate-pr",
            "eval-gate-nightly",
            "core-agent-smoke-pr",
        ),
        default="none",
        help="Hosting CI workflow label for observed smokes (default: none)",
    )
    parser.add_argument(
        "--smoke-results-json",
        default=None,
        help="Optional JSON file with external smoke observations (e.g. smoke_ci_summary.json)",
    )
    parser.add_argument(
        "--output-dir",
        default=_DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {_DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write output/toolchain/governance_snapshot.{json,md}",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Skip writing snapshot files (stdout only)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Stdout format (default: text summary)",
    )
    parser.add_argument(
        "--non-blocking",
        action="store_true",
        help="Always exit 0 even when snapshot ok=false (CI observability mode)",
    )
    parser.add_argument(
        "--print-ci-summary",
        action="store_true",
        help="Print short CI log trailer (default when --write)",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    smoke_results = Path(args.smoke_results_json) if args.smoke_results_json else None
    external_ids = set(
        _external_smoke_results(
            repo_root=repo_root,
            smoke_results_json=smoke_results,
        ).keys()
    )

    payload = build_toolchain_governance_snapshot(
        repo_root=repo_root,
        ci_context=args.ci_context,  # type: ignore[arg-type]
        smoke_results_json=smoke_results,
    )

    should_write = args.write and not args.no_write
    if should_write:
        out_dir = (
            Path(args.output_dir)
            if Path(args.output_dir).is_absolute()
            else repo_root / args.output_dir
        )
        payload["output_paths"] = write_toolchain_governance_snapshot_artifacts(
            payload,
            repo_root=repo_root,
            output_dir=out_dir.resolve(),
        )
        attach_governance_advisory(
            payload,
            external_smoke_ids=external_ids,
            write_attempted=True,
        )
        # Refresh artifacts so JSON/Markdown include final advisory fields.
        write_toolchain_governance_snapshot_artifacts(
            payload,
            repo_root=repo_root,
            output_dir=out_dir.resolve(),
        )
    else:
        attach_governance_advisory(
            payload,
            external_smoke_ids=external_ids,
            write_attempted=False,
        )

    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif args.print_ci_summary or should_write:
        print_ci_log_summary(payload)
    else:
        print(format_toolchain_governance_snapshot_markdown(payload))

    if args.non_blocking:
        return 0
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
