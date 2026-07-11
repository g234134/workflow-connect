"""
Wave 7 runner/orchestrator — single environment bootstrap entry.

Reuses ``core.repo_paths.ensure_repo_root_on_path`` for repo discovery; resolves
Wave 7 logical paths from ``Master_Map.json`` (``wave7_paths``) via ``gov_paths``.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any

from core.repo_paths import ensure_repo_root_on_path, find_repo_root

REPO_ROOT_LOGICAL = "tang_gov_root"
WAVE7_PATH_KEYS = ("cleaned_full", "staging_root", "delivery_root")


def _agents_core_on_path(repo_root: Path) -> None:
    agents = str(repo_root / "02_Agents_Core")
    if agents not in sys.path:
        sys.path.insert(1, agents)


def _load_master_map_at(repo_root: Path) -> dict[str, Any]:
    mp = repo_root / "04_Workflows" / "Master_Map.json"
    if not mp.is_file():
        raise FileNotFoundError(f"Master_Map.json not found: {mp}")
    with mp.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Master_Map.json root must be an object")
    return data


def resolve_wave7_logical_paths(
    master_map: dict[str, Any],
    *,
    repo_root: Path,
) -> tuple[dict[str, str], list[str]]:
    """
    Resolve ``wave7_paths`` entries to repo-relative logical path strings.

    Returns ``(paths_resolved, errors)``.
    """
    import gov_paths  # noqa: PLC0415 — after repo + Agents_Core on sys.path

    spec = master_map.get("wave7_paths")
    if not isinstance(spec, dict):
        return {}, ["Master_Map.wave7_paths missing or not an object"]

    errors: list[str] = []
    resolved: dict[str, str] = {}
    root_s = str(repo_root)

    for key in WAVE7_PATH_KEYS:
        entry = spec.get(key)
        if not isinstance(entry, dict):
            errors.append(f"Master_Map.wave7_paths[{key!r}] missing or not an object")
            continue
        department = entry.get("department")
        sub_type = entry.get("sub_type")
        if not department or not sub_type:
            errors.append(
                f"Master_Map.wave7_paths[{key!r}] requires department and sub_type"
            )
            continue
        try:
            abs_path = gov_paths.resolve_agent_output_path(
                root_s,
                str(department),
                str(sub_type),
            )
        except (KeyError, FileNotFoundError, TypeError) as exc:
            errors.append(f"wave7_paths[{key!r}]: {exc}")
            continue
        try:
            rel = Path(abs_path).resolve().relative_to(repo_root.resolve())
        except ValueError:
            errors.append(f"wave7_paths[{key!r}]: path outside repo root")
            continue
        resolved[key] = rel.as_posix()

    return resolved, errors


def _cabin_venv_marker(
    master_map: dict[str, Any],
    repo_root: Path,
    cabin: str,
) -> tuple[bool, str]:
    cabins = master_map.get("cabins") or {}
    entry = cabins.get(cabin) if isinstance(cabins, dict) else None
    if not isinstance(entry, dict):
        return False, f"Master_Map.cabins[{cabin!r}] missing"
    venv_rel = entry.get("venv_dir")
    if not venv_rel:
        return False, f"Master_Map.cabins[{cabin!r}].venv_dir missing"
    venv_dir = (repo_root / str(venv_rel).replace("\\", "/")).resolve()
    marker = venv_dir / "pyvenv.cfg"
    if not marker.is_file():
        rel = str(venv_rel).replace("\\", "/")
        return False, f"venv marker missing: {rel}/pyvenv.cfg"
    return True, ""


def _read_json_schema(repo_root: Path, rel_path: str) -> tuple[bool, str]:
    path = (repo_root / rel_path.replace("\\", "/")).resolve()
    if not path.is_file():
        return False, f"schema file missing: {rel_path}"
    try:
        with path.open(encoding="utf-8") as f:
            doc = json.load(f)
    except json.JSONDecodeError as exc:
        return False, f"schema JSON invalid ({rel_path}): {exc}"
    if not isinstance(doc, dict):
        return False, f"schema root must be object: {rel_path}"
    if not any(k in doc for k in ("$schema", "type", "properties", "definitions")):
        return False, f"schema not a recognizable JSON Schema document: {rel_path}"
    return True, ""


def _import_core_modules(module_names: list[str]) -> list[str]:
    errors: list[str] = []
    for name in module_names:
        try:
            importlib.import_module(name)
        except ImportError as exc:
            errors.append(f"import {name}: {exc}")
    return errors


def run_bootstrap_check(
    master_map: dict[str, Any],
    *,
    repo_root: Path,
    cabin: str,
) -> tuple[bool, list[str], list[str]]:
    """
    Smoke check: venv marker, core imports, JSON schemas readable.

    Returns ``(ok, errors, warnings)``.
    """
    errors: list[str] = []
    warnings: list[str] = []

    ok_venv, venv_msg = _cabin_venv_marker(master_map, repo_root, cabin)
    if not ok_venv:
        errors.append(venv_msg)

    boot = master_map.get("wave7_bootstrap")
    if not isinstance(boot, dict):
        errors.append("Master_Map.wave7_bootstrap missing or not an object")
        return False, errors, warnings

    imports = boot.get("core_imports")
    if not isinstance(imports, list) or not imports:
        errors.append("Master_Map.wave7_bootstrap.core_imports missing or empty")
    else:
        errors.extend(_import_core_modules([str(m) for m in imports]))

    schema_files = boot.get("schema_files")
    if not isinstance(schema_files, dict) or not schema_files:
        errors.append("Master_Map.wave7_bootstrap.schema_files missing or empty")
    else:
        for label, rel in schema_files.items():
            if not rel:
                errors.append(f"wave7_bootstrap.schema_files[{label!r}] empty")
                continue
            ok_schema, msg = _read_json_schema(repo_root, str(rel))
            if not ok_schema:
                errors.append(msg)

    return (len(errors) == 0), errors, warnings


def bootstrap_runner_env(
    *,
    cabin: str | None = None,
    check: bool = False,
    dry_run: bool = False,
    start: Path | None = None,
    master_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Single bootstrap entry for Wave 7 runner/orchestrator.

    Returns ``{ok, repo_root_logical, paths_resolved, warnings, message?}``.
    """
    warnings: list[str] = []
    repo_root = ensure_repo_root_on_path(start=start)
    if repo_root is None:
        return {
            "ok": False,
            "repo_root_logical": REPO_ROOT_LOGICAL,
            "paths_resolved": {},
            "warnings": warnings,
            "message": "repo root not found (markers: 00_master_plan.md or 01_Environments+context/context_builder.py)",
        }

    _agents_core_on_path(repo_root)

    try:
        m = master_map if master_map is not None else _load_master_map_at(repo_root)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {
            "ok": False,
            "repo_root_logical": REPO_ROOT_LOGICAL,
            "paths_resolved": {},
            "warnings": warnings,
            "message": f"Master_Map load failed: {exc}",
        }

    boot = m.get("wave7_bootstrap") if isinstance(m.get("wave7_bootstrap"), dict) else {}
    cabin_name = cabin or str(boot.get("cabin_default") or "gov_core_system")

    paths_resolved, path_errors = resolve_wave7_logical_paths(m, repo_root=repo_root)
    if path_errors:
        return {
            "ok": False,
            "repo_root_logical": REPO_ROOT_LOGICAL,
            "paths_resolved": paths_resolved,
            "warnings": warnings,
            "message": "; ".join(path_errors),
        }

    if dry_run and not check:
        warnings.append("dry_run: path resolution only; skipped venv/schema checks")
        return {
            "ok": True,
            "repo_root_logical": REPO_ROOT_LOGICAL,
            "paths_resolved": paths_resolved,
            "warnings": warnings,
        }

    if check:
        check_ok, check_errors, check_warnings = run_bootstrap_check(
            m, repo_root=repo_root, cabin=cabin_name
        )
        warnings.extend(check_warnings)
        if not check_ok:
            return {
                "ok": False,
                "repo_root_logical": REPO_ROOT_LOGICAL,
                "paths_resolved": paths_resolved,
                "warnings": warnings,
                "message": "; ".join(check_errors),
            }

    return {
        "ok": True,
        "repo_root_logical": REPO_ROOT_LOGICAL,
        "paths_resolved": paths_resolved,
        "warnings": warnings,
    }


__all__ = [
    "REPO_ROOT_LOGICAL",
    "WAVE7_PATH_KEYS",
    "bootstrap_runner_env",
    "find_repo_root",
    "resolve_wave7_logical_paths",
    "run_bootstrap_check",
]
