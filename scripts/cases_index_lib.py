"""Shared helpers for cases/index.json refresh and lookup (Wave 4A MEMO · W4-MEM-01/02)."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_INDEX_PATH = _REPO_ROOT / "cases" / "index.json"
_CSV_CLEANING = _REPO_ROOT / "notebooks" / "csv_cleaning"

# Anchor registry (W4-MEM-01); W4-MEM-02 merges with glob discovery under cases/.
REGISTERED_CASE_DIRS: tuple[str, ...] = (
    "cases/demo_phase",
    "cases/sampleco/2026-0001",
    "cases/internal-approved/2026-0001",
)

_DEFAULT_DELIVERY_TEMPLATE = "04_Workflows/WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md"

_CLEANING_PROFILE_BY_CASE: dict[str, str] = {
    "cases/demo_phase": "phase_demo_v1",
    "cases/sampleco/2026-0001": "sampleco_order_profile",
    "cases/internal-approved/2026-0001": "generic_low_risk_profile",
}

_STATIC_KNOWN_LIMITS: dict[str, list[str]] = {
    "cases/demo_phase": [
        "phase_one_row_per_phase_value",
        "not_prod_pipeline",
    ],
    "cases/sampleco/2026-0001": [
        "multi_row_milestone_export",
        "phase_dedup_semantics_unstable",
        "marginal_cleaning_quality",
    ],
    "cases/internal-approved/2026-0001": [
        "internal_use_only",
        "source_derived_from_demo_phase",
        "rows<100",
        "manual_payment_and_external_delivery_required",
    ],
}

_INDEX_DISCLAIMER = "Stub registry for Wave 2 MVP; not a production job queue."
_LOOKUP_NOTE = "anchors + glob under cases/ (excl. _TEMPLATE / _* stubs); W4-MEM-02"


def repo_root() -> Path:
    return _REPO_ROOT


def default_index_path() -> Path:
    return _DEFAULT_INDEX_PATH


def schema_fingerprint(headers: list[str] | None) -> str | None:
    """Stable short fingerprint: sorted headers joined by | → sha256 hex[:16]."""
    if not headers:
        return None
    cleaned = [str(h).strip() for h in headers if str(h).strip()]
    if not cleaned:
        return None
    payload = "|".join(sorted(cleaned))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _is_excluded_case_rel(case_rel: str) -> bool:
    """Exclude template / underscore stub trees (e.g. _TEMPLATE_case, _experiment_samples)."""
    parts = case_rel.replace("\\", "/").split("/")
    return any(part.startswith("_") for part in parts)


def discover_case_dirs(repo_root: Path | None = None) -> list[str]:
    """Merge REGISTERED anchors with glob of cases/*/intake.json and cases/*/*/intake.json."""
    root = repo_root or _REPO_ROOT
    cases_root = root / "cases"
    found: set[str] = set()

    for anchor in REGISTERED_CASE_DIRS:
        found.add(anchor.replace("\\", "/"))

    if cases_root.is_dir():
        for pattern in ("*/intake.json", "*/*/intake.json"):
            for intake_path in sorted(cases_root.glob(pattern)):
                case_dir = intake_path.parent
                try:
                    rel = case_dir.relative_to(root).as_posix()
                except ValueError:
                    continue
                if _is_excluded_case_rel(rel):
                    continue
                found.add(rel)

    anchors = [a.replace("\\", "/") for a in REGISTERED_CASE_DIRS]
    extras = sorted(p for p in found if p not in anchors)
    return anchors + extras


def _read_intake(case_dir: Path) -> dict[str, Any] | None:
    intake_path = case_dir / "intake.json"
    if not intake_path.is_file():
        return None
    try:
        data = json.loads(intake_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _read_csv_header(path: Path, encoding: str = "utf-8-sig") -> list[str] | None:
    if not path.is_file():
        return None
    for enc in (encoding, "utf-8-sig", "utf-8", "gbk"):
        try:
            with path.open(encoding=enc, newline="") as fh:
                row = next(csv.reader(fh), None)
                if row:
                    return [cell.strip() for cell in row if cell.strip() or cell == ""]
        except (OSError, UnicodeDecodeError, csv.Error):
            continue
    return None


def read_schema_headers(case_dir: Path, intake: dict[str, Any] | None = None) -> list[str]:
    """Read header row from raw/ (preferred) or cleaned/ CSV."""
    intake = intake or _read_intake(case_dir) or {}
    candidates: list[Path] = []

    data_file = intake.get("data_file")
    if isinstance(data_file, str) and data_file.strip():
        candidates.append(case_dir / data_file.strip())

    raw_dir = case_dir / "raw"
    if raw_dir.is_dir():
        candidates.extend(sorted(raw_dir.glob("*.csv")))
        candidates.extend(sorted(raw_dir.glob("*.tsv")))

    cleaned_dir = case_dir / "cleaned"
    if cleaned_dir.is_dir():
        candidates.extend(sorted(cleaned_dir.glob("*_cleaned.csv")))
        candidates.extend(sorted(cleaned_dir.glob("*.csv")))

    encoding = intake.get("encoding")
    enc = encoding if isinstance(encoding, str) and encoding.strip() else "utf-8-sig"

    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        headers = _read_csv_header(path, enc)
        if headers:
            return headers
    return []


def read_gate_status(case_dir: Path) -> str:
    """Return gate status from reports/eligibility_result.json or not_run."""
    result_path = case_dir / "reports" / "eligibility_result.json"
    if not result_path.is_file():
        return "not_run"
    try:
        data = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "not_run"
    if isinstance(data, dict):
        status = data.get("status")
        if isinstance(status, str) and status.strip():
            return status.strip()
    return "not_run"


def _load_report(case_dir: Path) -> dict[str, Any] | None:
    report_path = case_dir / "reports" / "report.json"
    if not report_path.is_file():
        return None
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _read_gate_schema_notes(case_dir: Path) -> list[str]:
    """Read-only gate probe for schema notes (does not write eligibility_result.json)."""
    if str(_CSV_CLEANING) not in sys.path:
        sys.path.insert(0, str(_CSV_CLEANING))
    try:
        from case_eligibility import check_case_eligibility  # noqa: WPS433
    except ImportError:
        return []

    try:
        gate = check_case_eligibility(case_dir)
    except (OSError, ValueError, TypeError):
        return []

    dimensions = gate.get("dimensions") or {}
    schema = dimensions.get("schema") or {}
    notes = schema.get("notes") or []
    return [str(n).strip() for n in notes if str(n).strip()]


def _extract_cleaning_rules(report: dict[str, Any] | None) -> list[str]:
    if not report:
        return []
    rules = report.get("cleaning_rules_applied")
    if not isinstance(rules, list):
        return []
    out: list[str] = []
    for item in rules:
        if isinstance(item, dict):
            rule_id = item.get("rule")
            if isinstance(rule_id, str) and rule_id.strip():
                out.append(rule_id.strip())
        elif isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def _extract_qa_summary(report: dict[str, Any] | None) -> dict[str, Any]:
    if not report:
        return {}
    summary = report.get("summary") or {}
    cleaning = report.get("cleaning_stats") or {}
    stats = report.get("stats") or {}
    row_counts = cleaning.get("row_counts") or stats.get("row_counts") or {}

    intake = row_counts.get("intake")
    accepted = row_counts.get("ok", row_counts.get("accepted"))
    ratio: float | None = None
    if isinstance(intake, int) and isinstance(accepted, int) and intake > 0:
        ratio = round(accepted / intake, 4)

    qa_status = summary.get("qa_status")
    return {
        "qa_status": qa_status if isinstance(qa_status, str) else None,
        "accepted_rows": accepted if isinstance(accepted, int) else None,
        "intake_rows": intake if isinstance(intake, int) else None,
        "accepted_ratio": ratio,
    }


def _known_limits_for(
    case_rel: str,
    gate_status: str,
    eligibility: dict[str, Any] | None,
    *,
    schema_notes: list[str] | None = None,
    qa_summary: dict[str, Any] | None = None,
) -> list[str]:
    limits: list[str] = []
    seen: set[str] = set()

    def _add(tag: str) -> None:
        token = tag.strip()
        if token and token not in seen:
            seen.add(token)
            limits.append(token)

    if case_rel == "cases/demo_phase":
        _add("legacy_demo_path")

    for tag in _STATIC_KNOWN_LIMITS.get(case_rel, []):
        _add(tag)

    if eligibility:
        reasons = eligibility.get("reasons")
        if isinstance(reasons, list):
            for item in reasons:
                if isinstance(item, str):
                    _add(item)

    for note in schema_notes or []:
        if note in ("multi_row_export", "schema_ambiguous", "schema_mismatch"):
            _add(note)

    qa = qa_summary or {}
    qa_status = qa.get("qa_status")
    if qa_status == "pass_with_warnings":
        _add("pass_with_warnings")
    ratio = qa.get("accepted_ratio")
    if isinstance(ratio, (int, float)) and ratio < 0.5:
        _add("low_accepted_ratio")

    if gate_status == "review_needed" and case_rel == "cases/demo_phase":
        _add("manual_review_required")

    return limits


def _load_eligibility(case_dir: Path) -> dict[str, Any] | None:
    result_path = case_dir / "reports" / "eligibility_result.json"
    if not result_path.is_file():
        return None
    try:
        data = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def build_case_entry(case_rel: str, repo_root: Path | None = None) -> dict[str, Any] | None:
    root = repo_root or _REPO_ROOT
    case_dir = (root / case_rel).resolve()
    if not case_dir.is_dir():
        return None

    intake = _read_intake(case_dir) or {}
    client_ref = intake.get("client_ref")
    if not isinstance(client_ref, str) or not client_ref.strip():
        client_ref = case_dir.parent.name if case_dir.name != "demo_phase" else "demo"

    product_sku = intake.get("product_sku")
    if not isinstance(product_sku, str) or not product_sku.strip():
        product_sku = "CLEAN-BASIC"

    case_id = intake.get("case_id")
    if not isinstance(case_id, str) or not case_id.strip():
        case_id = case_dir.name

    gate_status = read_gate_status(case_dir)
    eligibility = _load_eligibility(case_dir)
    case_key = case_rel.replace("\\", "/")
    report = _load_report(case_dir)
    schema_notes = _read_gate_schema_notes(case_dir)
    qa_summary = _extract_qa_summary(report)
    cleaning_rules = _extract_cleaning_rules(report)

    template_ref = _DEFAULT_DELIVERY_TEMPLATE
    if report:
        meta = report.get("meta") or {}
        ref = meta.get("template_ref")
        if isinstance(ref, str) and ref.strip():
            template_ref = ref.strip()

    schema_headers = read_schema_headers(case_dir, intake)

    entry: dict[str, Any] = {
        "case_dir": case_key,
        "client_ref": client_ref.strip(),
        "case_id": case_id.strip(),
        "product_sku": product_sku.strip(),
        "schema_headers": schema_headers,
        "schema_fingerprint": schema_fingerprint(schema_headers),
        "schema_notes": schema_notes,
        "gate_status": gate_status,
        "cleaning_profile": _CLEANING_PROFILE_BY_CASE.get(case_key, "unknown"),
        "cleaning_rules_applied": cleaning_rules,
        "delivery_template_ref": template_ref,
        "qa_status": qa_summary.get("qa_status"),
        "accepted_ratio": qa_summary.get("accepted_ratio"),
        "known_limits": _known_limits_for(
            case_key,
            gate_status,
            eligibility,
            schema_notes=schema_notes,
            qa_summary=qa_summary,
        ),
        "intake_path": f"{case_key}/intake.json",
    }

    if case_key == "cases/demo_phase":
        entry["status"] = "demo_anchor"
        entry["source_file"] = intake.get("data_file") or "raw/Phase.csv"
        entry["notes"] = "C2-D1 demo; internal structure aligned with _TEMPLATE_case"
    elif case_key == "cases/sampleco/2026-0001":
        entry["notes"] = (
            "First real-sample experiment; gate accepted but cleaning quality marginal "
            "(115 intake → 8 accepted; pass_with_warnings)"
        )
        data_file = intake.get("data_file")
        if isinstance(data_file, str) and data_file.strip():
            entry["source_file"] = data_file.strip()
    else:
        data_file = intake.get("data_file")
        if isinstance(data_file, str) and data_file.strip():
            entry["source_file"] = data_file.strip()

    return entry


def _match_summary(item: dict[str, Any], *, verbose: bool) -> dict[str, Any]:
    base: dict[str, Any] = {
        "case_dir": item.get("case_dir"),
        "client_ref": item.get("client_ref"),
        "product_sku": item.get("product_sku"),
        "gate_status": item.get("gate_status", "not_run"),
        "cleaning_profile": item.get("cleaning_profile"),
        "known_limits": item.get("known_limits") if isinstance(item.get("known_limits"), list) else [],
    }
    if verbose:
        base.update(
            {
                "schema_headers": item.get("schema_headers") if isinstance(item.get("schema_headers"), list) else [],
                "schema_fingerprint": item.get("schema_fingerprint"),
                "schema_notes": item.get("schema_notes") if isinstance(item.get("schema_notes"), list) else [],
                "cleaning_rules_applied": item.get("cleaning_rules_applied")
                if isinstance(item.get("cleaning_rules_applied"), list)
                else [],
                "delivery_template_ref": item.get("delivery_template_ref"),
                "qa_status": item.get("qa_status"),
                "accepted_ratio": item.get("accepted_ratio"),
                "notes": item.get("notes"),
            }
        )
    return base


def refresh_cases_index(
    index_path: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Discover case dirs (anchors + glob) and write cases/index.json."""
    root = repo_root or _REPO_ROOT
    path = index_path or (root / "cases" / "index.json")

    entries: list[dict[str, Any]] = []
    skipped: list[str] = []
    for case_rel in discover_case_dirs(root):
        entry = build_case_entry(case_rel, root)
        if entry:
            entries.append(entry)
        else:
            skipped.append(case_rel)

    payload: dict[str, Any] = {
        "schema_version": "gov-cases-index-v0.1",
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "disclaimer": _INDEX_DISCLAIMER,
        "naming": {
            "client_ref": "lowercase [a-z0-9-]; customer or project slug",
            "case_id": "lowercase [a-z0-9-]; batch or ticket slug",
            "legacy_demo": "cases/demo_phase/ kept for C2-D1 backward anchor",
        },
        "template_path": "cases/_TEMPLATE_case",
        "required_paths": [
            "intake.json",
            "raw/",
            "cleaned/",
            "reports/",
            "delivery_signoff.md",
        ],
        "cases": entries,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "ok": True,
        "index_path": str(path.relative_to(root)).replace("\\", "/"),
        "cases_written": len(entries),
        "skipped": skipped,
    }


def load_cases_index(index_path: Path | None = None, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _REPO_ROOT
    path = index_path or (root / "cases" / "index.json")
    if not path.is_file():
        return {"ok": False, "message": "index_not_found", "cases": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "message": f"invalid_index_json:{exc}", "cases": []}
    if not isinstance(data, dict):
        return {"ok": False, "message": "invalid_index_root", "cases": []}
    cases = data.get("cases")
    if not isinstance(cases, list):
        return {"ok": False, "message": "missing_cases_array", "cases": []}
    return {"ok": True, "raw": data, "cases": cases}


def _normalize_token(value: str) -> str:
    return value.strip().lower()


def _parse_header_list(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    return parts


def schema_headers_match(case_headers: list[str], query_headers: list[str]) -> bool:
    """Simple subset or exact set match (case-insensitive, order ignored)."""
    if not query_headers:
        return True
    case_set = {_normalize_token(h) for h in case_headers}
    query_set = {_normalize_token(h) for h in query_headers}
    return query_set <= case_set or query_set == case_set


def lookup_cases(
    *,
    client_ref: str | None = None,
    product_sku: str | None = None,
    schema_headers: list[str] | None = None,
    list_all: bool = False,
    verbose: bool = False,
    index_path: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    loaded = load_cases_index(index_path, repo_root)
    notes = [_LOOKUP_NOTE]
    if not loaded.get("ok"):
        return {
            "ok": False,
            "matches": [],
            "notes": notes + [f"index_error:{loaded.get('message', 'unknown')}"],
        }

    matches: list[dict[str, Any]] = []
    for item in loaded["cases"]:
        if not isinstance(item, dict):
            continue
        if not list_all:
            if client_ref is not None:
                entry_ref = item.get("client_ref")
                if not isinstance(entry_ref, str) or _normalize_token(entry_ref) != _normalize_token(client_ref):
                    continue
            if product_sku is not None:
                entry_sku = item.get("product_sku")
                if not isinstance(entry_sku, str) or _normalize_token(entry_sku) != _normalize_token(product_sku):
                    continue
            if schema_headers is not None:
                headers = item.get("schema_headers")
                if not isinstance(headers, list):
                    headers = []
                if not schema_headers_match([str(h) for h in headers], schema_headers):
                    continue

        matches.append(_match_summary(item, verbose=verbose))

    return {"ok": True, "matches": matches, "notes": notes}
