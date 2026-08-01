"""
Gov Tool Catalog registry v1 (B-F1).

Loads and validates ``skills/gov_cards/*.json`` against ``gov_tool_card_schema.json``.
Does not execute tools or wire into ask/selector pipelines.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None  # type: ignore[assignment]

_SCHEMA_VERSION = "gov_tool_card_v1"
_DEFAULT_CARDS_DIR = Path("skills/gov_cards")
_SCHEMA_FILE = Path("skills/gov_tool_card_schema.json")
_TOOL_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(\.[a-z][a-z0-9_]*){2,}$")
_VALID_ROLES = frozenset({"orchestrator", "implementer", "reviewer", "scribe"})


def find_repo_root(start: Path | None = None) -> Path:
    """Walk parents until AGENTS.md or Master_Map.json is found."""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "AGENTS.md").is_file() or (candidate / "Master_Map.json").is_file():
            return candidate
    return current


def default_cards_dir(repo_root: Path | None = None) -> Path:
    root = repo_root or find_repo_root()
    return root / _DEFAULT_CARDS_DIR


def default_schema_path(repo_root: Path | None = None) -> Path:
    root = repo_root or find_repo_root()
    return root / _SCHEMA_FILE


def load_schema(schema_path: Path | None = None, *, repo_root: Path | None = None) -> dict[str, Any]:
    path = schema_path or default_schema_path(repo_root)
    return json.loads(path.read_text(encoding="utf-8"))


def load_gov_tool_cards(
    cards_dir: Path | str | None = None,
    *,
    repo_root: Path | None = None,
) -> list[dict[str, Any]]:
    """Load all ``*.json`` cards from ``cards_dir`` (sorted by tool_id)."""
    root = repo_root or find_repo_root()
    directory = Path(cards_dir) if cards_dir is not None else default_cards_dir(root)
    if not directory.is_absolute():
        directory = root / directory

    cards: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            cards.append(payload)
    cards.sort(key=lambda card: str(card.get("tool_id", "")))
    return cards


_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "tool_id",
        "title",
        "brief",
        "domain",
        "module_path",
        "entry_kind",
        "entrypoint",
        "inputs",
        "outputs",
        "verify_command",
        "wave_ticket",
        "review_status",
    }
)
_VALID_DOMAINS = frozenset({"obs", "kb", "route"})
_VALID_ENTRY_KINDS = frozenset({"python_module", "python_cli", "composite"})
_VALID_REVIEW = frozenset({"approved", "draft", "rejected"})


def _manual_schema_errors(card: dict[str, Any]) -> list[str]:
    """Minimal schema checks when jsonschema is unavailable."""
    errors: list[str] = []
    for field in sorted(_REQUIRED_FIELDS):
        if field not in card:
            errors.append(f"schema: missing required field '{field}'")

    domain = card.get("domain")
    if domain is not None and str(domain) not in _VALID_DOMAINS:
        errors.append(f"schema: invalid domain '{domain}'")

    entry_kind = card.get("entry_kind")
    if entry_kind is not None and str(entry_kind) not in _VALID_ENTRY_KINDS:
        errors.append(f"schema: invalid entry_kind '{entry_kind}'")

    review = card.get("review_status")
    if review is not None and str(review) not in _VALID_REVIEW:
        errors.append(f"schema: invalid review_status '{review}'")

    for list_field in ("inputs", "outputs"):
        value = card.get(list_field)
        if value is not None and (not isinstance(value, list) or not value):
            errors.append(f"schema: '{list_field}' must be a non-empty array")

    if entry_kind == "python_cli" and not str(card.get("cli_invocation", "")).strip():
        errors.append("schema: cli_invocation required when entry_kind=python_cli")

    return errors


def _schema_errors(card: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    if jsonschema is not None:
        validator = jsonschema.Draft202012Validator(schema)
        return [f"schema: {err.message}" for err in sorted(validator.iter_errors(card), key=str)]
    return _manual_schema_errors(card)


def _business_errors(card: dict[str, Any], *, repo_root: Path, known_tool_ids: set[str]) -> list[str]:
    errors: list[str] = []
    tool_id = str(card.get("tool_id", "")).strip()
    entry_kind = str(card.get("entry_kind", "")).strip()
    module_path = card.get("module_path")
    entrypoint = card.get("entrypoint")
    verify_command = str(card.get("verify_command", "")).strip()

    if not tool_id:
        errors.append("tool_id is required")
    elif not _TOOL_ID_PATTERN.match(tool_id):
        errors.append(f"tool_id '{tool_id}' does not match <domain>.<action>.<target> pattern")

    if card.get("schema_version") != _SCHEMA_VERSION:
        errors.append(f"schema_version must be '{_SCHEMA_VERSION}'")

    if not verify_command:
        errors.append("verify_command must be non-empty")

    roles = card.get("applicable_roles")
    if roles is not None:
        for role in roles:
            if str(role) not in _VALID_ROLES:
                errors.append(f"applicable_roles contains invalid role '{role}'")

    depends_on = card.get("depends_on") or []
    for dep in depends_on:
        dep_id = str(dep).strip()
        if dep_id and dep_id not in known_tool_ids:
            errors.append(f"depends_on references unknown tool_id '{dep_id}'")
        if dep_id == tool_id:
            errors.append("depends_on must not reference self")

    if entry_kind == "composite":
        if module_path is not None:
            errors.append("composite card must have module_path=null")
        if entrypoint is not None:
            errors.append("composite card must have entrypoint=null")
        return errors

    if not module_path:
        errors.append("module_path is required for non-composite cards")
    else:
        module_file = repo_root / str(module_path)
        if not module_file.is_file():
            errors.append(f"module_path not found: {module_path}")

    if not entrypoint:
        errors.append("entrypoint is required for non-composite cards")

    if entry_kind == "python_cli" and not str(card.get("cli_invocation", "")).strip():
        errors.append("cli_invocation is required when entry_kind=python_cli")

    return errors


def validate_gov_tool_card(
    card: dict[str, Any],
    *,
    repo_root: Path | None = None,
    schema: dict[str, Any] | None = None,
    known_tool_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Validate one card; return ``{ok, message, tool_id, errors}``."""
    root = repo_root or find_repo_root()
    schema_doc = schema or load_schema(repo_root=root)
    tool_id = str(card.get("tool_id", "")).strip()
    ids = known_tool_ids or {tool_id} if tool_id else set()

    errors = _schema_errors(card, schema_doc) + _business_errors(card, repo_root=root, known_tool_ids=ids)
    ok = not errors
    return {
        "ok": ok,
        "message": "valid" if ok else f"{len(errors)} validation error(s)",
        "tool_id": tool_id or None,
        "errors": errors,
    }


def validate_all_gov_tool_cards(
    cards_dir: Path | str | None = None,
    *,
    repo_root: Path | None = None,
    schema_path: Path | None = None,
) -> dict[str, Any]:
    """Validate every card in the catalog directory."""
    root = repo_root or find_repo_root()
    schema = load_schema(schema_path, repo_root=root)
    cards = load_gov_tool_cards(cards_dir, repo_root=root)

    tool_ids = [str(c.get("tool_id", "")).strip() for c in cards]
    duplicate_ids = sorted({tid for tid in tool_ids if tool_ids.count(tid) > 1 and tid})

    known_ids = {tid for tid in tool_ids if tid}
    results: list[dict[str, Any]] = []
    passed = 0
    failed = 0

    for card in cards:
        result = validate_gov_tool_card(
            card,
            repo_root=root,
            schema=schema,
            known_tool_ids=known_ids,
        )
        tid = str(card.get("tool_id", "")).strip()
        if tid in duplicate_ids:
            result["errors"] = list(result.get("errors", [])) + [f"duplicate tool_id '{tid}'"]
            result["ok"] = False
            result["message"] = f"{len(result['errors'])} validation error(s)"
        results.append(result)
        if result["ok"]:
            passed += 1
        else:
            failed += 1

    total = len(cards)
    ok = failed == 0 and total > 0
    return {
        "ok": ok,
        "message": "all cards valid" if ok else f"{failed} of {total} card(s) failed validation",
        "total": total,
        "passed": passed,
        "failed": failed,
        "results": results,
    }


def list_gov_tool_cards(
    cards_dir: Path | str | None = None,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Return a structured list of catalog tool IDs."""
    cards = load_gov_tool_cards(cards_dir, repo_root=repo_root)
    entries = [
        {
            "tool_id": card.get("tool_id"),
            "title": card.get("title"),
            "domain": card.get("domain"),
            "entry_kind": card.get("entry_kind"),
            "module_path": card.get("module_path"),
        }
        for card in cards
    ]
    return {
        "ok": True,
        "message": f"listed {len(entries)} tool card(s)",
        "total": len(entries),
        "tools": entries,
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gov Tool Catalog registry v1")
    parser.add_argument(
        "command",
        choices=("list", "validate"),
        help="list tool IDs or validate all cards",
    )
    parser.add_argument(
        "--cards-dir",
        default=str(_DEFAULT_CARDS_DIR),
        help="Catalog directory relative to repo root (default: skills/gov_cards)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repo root override (default: auto-detect)",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="text",
        help="Output format (default: text)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_root = args.repo_root or find_repo_root()

    if args.command == "list":
        result = list_gov_tool_cards(args.cards_dir, repo_root=repo_root)
    else:
        result = validate_all_gov_tool_cards(args.cards_dir, repo_root=repo_root)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == "list":
        for entry in result.get("tools", []):
            print(f"{entry.get('tool_id')}\t{entry.get('domain')}\t{entry.get('entry_kind')}")
        print(f"\n{result.get('message')}")
    else:
        print(f"ok={result.get('ok')} total={result.get('total')} passed={result.get('passed')} failed={result.get('failed')}")
        print(result.get("message"))
        if result.get("failed"):
            for item in result.get("results", []):
                if not item.get("ok"):
                    print(f"  FAIL {item.get('tool_id')}: {', '.join(item.get('errors', []))}")

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
