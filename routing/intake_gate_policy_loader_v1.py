"""Load and validate Intake Gate policy YAML (P75-G3)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

try:
    from jsonschema import Draft7Validator
    from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
except ImportError:  # pragma: no cover
    Draft7Validator = None  # type: ignore[assignment,misc]
    JsonSchemaValidationError = Exception  # type: ignore[assignment,misc]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_POLICY_PATH = _REPO_ROOT / "routing" / "intake_gate_policy_v1.yaml"
_DEFAULT_SCHEMA_PATH = _REPO_ROOT / "shared" / "schemas" / "intake_gate_policy_v1.json"
_POLICY_VERSION = "intake_gate_policy_v1"


def default_policy_path(*, repo_root: Optional[Path] = None) -> Path:
    root = repo_root or _REPO_ROOT
    return root / "routing" / "intake_gate_policy_v1.yaml"


def default_schema_path(*, repo_root: Optional[Path] = None) -> Path:
    root = repo_root or _REPO_ROOT
    return root / "shared" / "schemas" / "intake_gate_policy_v1.json"


def _load_schema(schema_path: Path) -> Dict[str, Any]:
    with schema_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("policy schema root must be an object")
    return payload


_ALLOWED_DENY_REASON_CODES = frozenset(
    {
        "policy_deny_phi",
        "policy_deny_web_scraping",
        "policy_deny_audio_video",
        "policy_deny_scale_exceeds",
    }
)


def _basic_validate_policy(policy: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for index, rule in enumerate(policy.get("deny_rules") or []):
        if not isinstance(rule, dict):
            errors.append(f"deny_rules[{index}]: must be an object")
            continue
        reason_code = rule.get("reason_code")
        if reason_code not in _ALLOWED_DENY_REASON_CODES:
            errors.append(
                f"deny_rules[{index}].reason_code: unknown deny reason_code {reason_code!r}"
            )
    return errors


def _validate_policy_schema(
    policy: Dict[str, Any],
    *,
    schema_path: Optional[Path] = None,
    repo_root: Optional[Path] = None,
) -> List[str]:
    if Draft7Validator is None:
        return _basic_validate_policy(policy)
    path = schema_path or default_schema_path(repo_root=repo_root)
    schema = _load_schema(path)
    validator = Draft7Validator(schema)
    errors: List[str] = []
    for error in sorted(validator.iter_errors(policy), key=lambda err: list(err.path)):
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        errors.append(f"{location}: {error.message}")
    return errors


def load_intake_gate_policy(
    path: Optional[str | Path] = None,
    *,
    validate_schema: bool = True,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Load intake gate policy YAML from disk.

    Returns ``{"ok": true/false, "policy": ..., "error": ...}``.
    """
    root = repo_root or _REPO_ROOT
    policy_path = Path(path) if path is not None else default_policy_path(repo_root=root)
    if not policy_path.is_absolute():
        policy_path = root / policy_path

    if yaml is None:
        return {
            "ok": False,
            "policy": None,
            "error": "PyYAML is required to load intake gate policy",
        }

    if not policy_path.is_file():
        return {
            "ok": False,
            "policy": None,
            "error": f"policy file not found: {policy_path.as_posix()}",
        }

    try:
        raw = policy_path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"ok": False, "policy": None, "error": f"policy read failed: {exc}"}

    try:
        payload = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return {"ok": False, "policy": None, "error": f"invalid yaml: {exc}"}

    if not isinstance(payload, dict):
        return {"ok": False, "policy": None, "error": "policy root must be a mapping"}

    if validate_schema:
        schema_errors = _validate_policy_schema(payload, repo_root=root)
        if schema_errors:
            return {
                "ok": False,
                "policy": None,
                "error": "; ".join(schema_errors),
            }

    if payload.get("policy_version") != _POLICY_VERSION:
        return {
            "ok": False,
            "policy": None,
            "error": f"policy_version must be {_POLICY_VERSION}",
        }

    return {"ok": True, "policy": payload, "error": None}
