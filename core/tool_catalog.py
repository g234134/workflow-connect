"""
Phase 8.8 Tool Catalog loader — SSOT: shared/schemas/tool_catalog_v1.json.

See docs/TOOL_CATALOG_AUTHORITY.md for track boundaries vs Tabular / Gov / Wave8.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_SCHEMA_VERSION = "tool_catalog_v1"
_CATALOG_REL = Path("shared/schemas/tool_catalog_v1.json")

_REQUIRED_TOOL_FIELDS = frozenset(
    {
        "tool_id",
        "type",
        "enabled",
        "input_schema",
        "expected_output",
        "cost_hint",
        "risk_level",
        "latency_hint",
        "executor_binding",
    }
)
_REQUIRED_TOP_FIELDS = frozenset({"schema_version", "catalog_revision", "tools"})


def _find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "AGENTS.md").is_file() or (candidate / "Master_Map.json").is_file():
            return candidate
    return current


def default_catalog_path(repo_root: Path | None = None) -> Path:
    root = repo_root or _find_repo_root()
    return root / _CATALOG_REL


def _validate_tool(tool: Any, *, index: int) -> str | None:
    if not isinstance(tool, dict):
        return f"tools[{index}] must be an object"
    missing = sorted(_REQUIRED_TOOL_FIELDS - set(tool.keys()))
    if missing:
        return f"tools[{index}] missing required fields: {', '.join(missing)}"
    tool_id = tool.get("tool_id")
    if not isinstance(tool_id, str) or not tool_id.strip():
        return f"tools[{index}] tool_id must be a non-empty string"
    return None


def validate_catalog_document(data: Any) -> dict[str, Any]:
    """Validate parsed catalog JSON; return {ok, message, ...} without loading from disk."""
    if not isinstance(data, dict):
        return {"ok": False, "message": "catalog root must be a JSON object"}

    missing_top = sorted(_REQUIRED_TOP_FIELDS - set(data.keys()))
    if missing_top:
        return {
            "ok": False,
            "message": f"catalog missing required fields: {', '.join(missing_top)}",
        }

    if data.get("schema_version") != _SCHEMA_VERSION:
        return {
            "ok": False,
            "message": f"unsupported schema_version: {data.get('schema_version')!r}",
        }

    revision = data.get("catalog_revision")
    if not isinstance(revision, str) or not revision.strip():
        return {"ok": False, "message": "catalog_revision must be a non-empty string"}

    tools = data.get("tools")
    if not isinstance(tools, list):
        return {"ok": False, "message": "tools must be an array"}

    seen_ids: set[str] = set()
    enabled_count = 0
    for idx, tool in enumerate(tools):
        err = _validate_tool(tool, index=idx)
        if err:
            return {"ok": False, "message": err}
        tool_id = str(tool["tool_id"])
        if tool_id in seen_ids:
            return {"ok": False, "message": f"duplicate tool_id: {tool_id}"}
        seen_ids.add(tool_id)
        if tool.get("enabled") is True:
            enabled_count += 1

    return {
        "ok": True,
        "message": "catalog valid",
        "schema_version": _SCHEMA_VERSION,
        "catalog_revision": revision,
        "tool_count": len(tools),
        "enabled_count": enabled_count,
        "tools": tools,
    }


def load_catalog(*, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Load and validate tool catalog from repo SSOT path."""
    root = Path(repo_root).resolve() if repo_root is not None else _find_repo_root()
    path = default_catalog_path(root)

    if not path.is_file():
        return {"ok": False, "message": f"catalog not found: {path.relative_to(root)}"}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"ok": False, "message": f"invalid JSON in catalog: {exc}"}

    result = validate_catalog_document(data)
    if result["ok"]:
        result["catalog_path"] = str(path.relative_to(root))
    return result
