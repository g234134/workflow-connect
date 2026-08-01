"""Tabular cleaning profile registry (v1).

Profiles drive column roles and cleaning parameters for ``clean_phase_demo.py``.
See ``docs/tabular-cleaning-profiles-v1.md`` for human-readable spec.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

PROFILE_SCHEMA = "tabular-cleaning-profile-v1"

# Case-dir → default profile when intake.json omits cleaning_profile
_CASE_DIR_PROFILE: dict[str, str] = {
    "cases/demo_phase": "phase_demo_v1",
    "cases/sampleco/2026-0001": "sampleco_order_profile",
    "cases/internal/generic-low-risk": "generic_low_risk_profile",
}

ALLOWED_COLUMN_TYPES = frozenset({"primary_key", "numeric", "category", "text"})

_PROFILES: dict[str, dict[str, Any]] = {
    "phase_demo_v1": {
        "profile_id": "phase_demo_v1",
        "display_name": "Phase Demo (C2-D1 anchor)",
        "risk_level": "low",
        "runner": "clean.phase_demo",
        "hitl": {
            "checkpoint_a": {"required": True, "skip_when": []},
            "checkpoint_b": {
                "required_when": ["output_guard.warning"],
                "skip_when": ["output_guard.ok"],
            },
        },
        "columns": ["Phase", "名稱", "之前", "現在（建議）"],
        "field_roles": {
            "Phase": "segment_key",
            "名稱": "label",
            "之前": "percent_before",
            "現在（建議）": "percent_target",
        },
        "percent_columns": ["之前", "現在（建議）"],
        "dedup_keys": ["Phase"],
        "dedup_strategy": "keep_max_percent_column",
        "dedup_compare_column": "現在（建議）",
        "drop_if_blank": ["Phase"],
        "rules": {
            "missing": [
                "drop row when Phase and 名稱 both blank",
                "reject row when Phase blank after trim",
            ],
            "duplicate": [
                "dedup by Phase; keep row with highest 現在（建議）",
            ],
            "anomaly": [
                "flag percent columns outside 0–100; do not auto-truncate",
            ],
            "format": [
                "normalize Phase to 'Phase N' casing",
                "parse percent strings and 0–1 fractions to 0–100 scale",
                "trim 名稱 whitespace",
            ],
        },
        "cleaning_rules_applied": [
            "normalize_phase_name",
            "dedup_by_phase",
            "drop_missing_phase",
            "parse_percent",
            "flag_out_of_range",
        ],
    },
    "sampleco_order_profile": {
        "profile_id": "sampleco_order_profile",
        "display_name": "SampleCo milestone export (2026-0001)",
        "risk_level": "low",
        "runner": "clean.phase_demo",
        "hitl": {
            "checkpoint_a": {"required": True, "skip_when": []},
            "checkpoint_b": {
                "required_when": ["output_guard.warning"],
                "skip_when": ["output_guard.ok"],
            },
        },
        "columns": ["Phase", "名稱", "之前", "現在（建議）"],
        "field_roles": {
            "Phase": "milestone_phase",
            "名稱": "workstream_name",
            "之前": "percent_before",
            "現在（建議）": "percent_target",
        },
        "percent_columns": ["之前", "現在（建議）"],
        "dedup_keys": ["Phase"],
        "dedup_strategy": "keep_max_percent_column",
        "dedup_compare_column": "現在（建議）",
        "drop_if_blank": ["Phase"],
        "rules": {
            "missing": [
                "drop row when Phase and 名稱 both blank",
                "reject row when Phase blank; retain partial percent gaps as warnings",
            ],
            "duplicate": [
                "dedup by Phase only (multi-row export); keep max 現在（建議） per phase",
                "document: business key is Phase+名稱 but v1 uses phase-level dedup for regression stability",
            ],
            "anomaly": [
                "flag percent columns outside 0–100",
                "high removal_ratio expected on multi-row milestone exports",
            ],
            "format": [
                "normalize phase casing (phase 1 → Phase 1)",
                "parse % suffix and fractional 0–1 values",
                "trim whitespace on percent fields",
            ],
        },
        "cleaning_rules_applied": [
            "normalize_phase_name",
            "dedup_by_phase",
            "drop_missing_phase",
            "parse_percent",
            "flag_out_of_range",
        ],
        "known_limits": [
            "multi_row_milestone_export",
            "phase_dedup_semantics_unstable",
            "marginal_cleaning_quality",
        ],
        "hitl": {
            "checkpoint_a": {"required": True, "skip_when": []},
            "checkpoint_b": {
                "required_when": ["output_guard.warning"],
                "skip_when": ["output_guard.ok"],
            },
        },
    },
    "generic_low_risk_profile": {
        "profile_id": "generic_low_risk_profile",
        "display_name": "Generic low-risk (primary key + numeric table)",
        "risk_level": "low",
        "runner": "clean.generic",
        "schema_from_intake": True,
        "allowed_column_types": sorted(ALLOWED_COLUMN_TYPES),
        "min_columns": 2,
        "max_columns": 20,
        "dedup_strategy": "keep_max_numeric_column",
        "rules": {
            "missing": [
                "drop row when primary_key column is blank after trim",
                "retain rows with blank category/text as warnings (not auto-drop)",
            ],
            "duplicate": [
                "dedup by primary_key; keep row with highest first numeric compare column",
            ],
            "anomaly": [
                "flag numeric values outside optional intake.schema.numeric_range per column",
                "flag unparseable numeric strings; retain row with empty numeric field",
            ],
            "format": [
                "trim whitespace on category and text columns",
                "parse numeric strings (strip commas)",
            ],
        },
        "cleaning_rules_applied": [
            "trim_text_fields",
            "dedup_by_primary_key",
            "drop_missing_primary_key",
            "parse_numeric",
            "flag_out_of_range",
        ],
        "hitl": {
            "checkpoint_a": {"required": True, "skip_when": []},
            "checkpoint_b": {
                "required_when": ["output_guard.warning"],
                "skip_when": ["output_guard.ok"],
            },
        },
    },
}


def _intake_schema(intake: dict[str, Any] | None) -> dict[str, Any]:
    if not intake:
        return {}
    schema = intake.get("schema")
    if isinstance(schema, dict):
        return schema
    schema_def = intake.get("schema_definition")
    return schema_def if isinstance(schema_def, dict) else {}


def _build_column_roles_from_intake(schema: dict[str, Any]) -> dict[str, str]:
    explicit = schema.get("column_roles")
    if isinstance(explicit, dict) and explicit:
        return {str(k): str(v) for k, v in explicit.items() if k and v}

    roles: dict[str, str] = {}
    pk = schema.get("primary_key") or schema.get("id_column")
    if isinstance(pk, str) and pk.strip():
        roles[pk.strip()] = "primary_key"

    for col in schema.get("numeric_columns") or []:
        if isinstance(col, str) and col.strip():
            roles[col.strip()] = "numeric"
    for col in schema.get("category_columns") or []:
        if isinstance(col, str) and col.strip():
            roles[col.strip()] = "category"
    for col in schema.get("text_columns") or []:
        if isinstance(col, str) and col.strip():
            roles[col.strip()] = "text"

    return roles


def validate_profile_schema(
    profile_cfg: dict[str, Any],
    intake: dict[str, Any] | None,
    csv_headers: list[str] | None,
) -> tuple[bool, str | None]:
    """Validate that intake schema satisfies profile requirements."""
    if not profile_cfg.get("schema_from_intake"):
        return True, None

    schema = _intake_schema(intake)
    roles = _build_column_roles_from_intake(schema)
    if not roles:
        return False, "generic_profile_missing_column_roles"

    if "primary_key" not in roles.values():
        pk = schema.get("primary_key") or schema.get("id_column")
        if not (isinstance(pk, str) and pk.strip()):
            return False, "generic_profile_missing_primary_key"

    allowed = frozenset(profile_cfg.get("allowed_column_types") or ALLOWED_COLUMN_TYPES)
    for col, role in roles.items():
        if role not in allowed:
            return False, f"generic_profile_invalid_column_type:{col}:{role}"

    min_cols = int(profile_cfg.get("min_columns") or 2)
    max_cols = int(profile_cfg.get("max_columns") or 20)
    if len(roles) < min_cols:
        return False, "generic_profile_too_few_columns"
    if len(roles) > max_cols:
        return False, "generic_profile_too_many_columns"

    if csv_headers is not None:
        header_set = frozenset(csv_headers)
        missing = [col for col in roles if col not in header_set]
        if missing:
            return False, "generic_profile_header_mismatch:" + ",".join(missing)

    return True, None


def build_runtime_profile(
    profile_cfg: dict[str, Any],
    intake: dict[str, Any] | None,
    csv_headers: list[str] | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Merge registry profile with intake schema for runtime cleaning."""
    runtime = dict(profile_cfg)
    if not profile_cfg.get("schema_from_intake"):
        return runtime, None

    schema = _intake_schema(intake)
    roles = _build_column_roles_from_intake(schema)
    ok, err = validate_profile_schema(profile_cfg, intake, csv_headers)
    if not ok:
        return None, err

    pk_col = next((c for c, r in roles.items() if r == "primary_key"), None)
    if pk_col is None:
        pk_raw = schema.get("primary_key") or schema.get("id_column")
        if isinstance(pk_raw, str):
            pk_col = pk_raw.strip()
            roles[pk_col] = "primary_key"

    numeric_cols = [c for c, r in roles.items() if r == "numeric"]
    columns = list(roles.keys())
    if csv_headers:
        columns = [c for c in csv_headers if c in roles] + [c for c in roles if c not in csv_headers]

    runtime.update(
        {
            "field_roles": roles,
            "columns": columns,
            "primary_key": pk_col,
            "dedup_keys": [pk_col] if pk_col else [],
            "dedup_compare_column": numeric_cols[0] if numeric_cols else None,
            "drop_if_blank": [pk_col] if pk_col else [],
            "numeric_range": schema.get("numeric_range") or {},
            "numeric_min": schema.get("numeric_min"),
            "numeric_max": schema.get("numeric_max"),
        }
    )
    return runtime, None


def list_profile_ids() -> list[str]:
    return sorted(_PROFILES.keys())


def get_profile(profile_id: str) -> dict[str, Any] | None:
    return _PROFILES.get(profile_id)


def _normalize_case_key(case_dir: Path, repo_root: Path | None = None) -> str:
    resolved = case_dir.resolve()
    if repo_root is not None:
        try:
            rel = resolved.relative_to(repo_root.resolve())
            return rel.as_posix()
        except ValueError:
            pass
    parts = resolved.parts
    if "cases" in parts:
        idx = parts.index("cases")
        return "/".join(parts[idx:])
    return resolved.name


def resolve_cleaning_profile(
    case_dir: Path,
    intake: dict[str, Any] | None = None,
    *,
    profile_id_override: str | None = None,
    repo_root: Path | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Resolve profile dict for a case. Returns (profile, error_message)."""
    if profile_id_override:
        profile = get_profile(profile_id_override)
        if profile is None:
            return None, f"unknown_cleaning_profile:{profile_id_override}"
        return dict(profile), None

    profile_id: str | None = None
    if intake and isinstance(intake.get("cleaning_profile"), str):
        profile_id = intake["cleaning_profile"].strip() or None

    if not profile_id:
        case_key = _normalize_case_key(case_dir, repo_root)
        profile_id = _CASE_DIR_PROFILE.get(case_key)

    if not profile_id:
        return None, "cleaning_profile_not_configured"

    profile = get_profile(profile_id)
    if profile is None:
        return None, f"unknown_cleaning_profile:{profile_id}"
    return dict(profile), None


def resolve_runtime_profile(
    case_dir: Path,
    intake: dict[str, Any] | None = None,
    *,
    profile_id_override: str | None = None,
    repo_root: Path | None = None,
    csv_headers: list[str] | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Resolve profile and merge intake schema when required."""
    profile_cfg, err = resolve_cleaning_profile(
        case_dir, intake, profile_id_override=profile_id_override, repo_root=repo_root
    )
    if profile_cfg is None:
        return None, err
    return build_runtime_profile(profile_cfg, intake, csv_headers)
