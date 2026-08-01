"""
Routing Policy v1 loader (B-F3).

Loads ``config/routing_policy.yaml``, validates tool_id references against the
B-F1 Gov Tool Catalog, and exposes query helpers for Wave B route resolution.
Does not execute tools or wire into ask/selector pipelines.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

from skills.gov_tool_registry import find_repo_root, load_gov_tool_cards

_SCHEMA_VERSION = "routing_policy_v1"
_DEFAULT_CONFIG = Path("config/routing_policy.yaml")
_DEFAULT_EVAL_ROUTE_ID = "wave_b.eval_report"


def default_config_path(repo_root: Path | None = None) -> Path:
    root = repo_root or find_repo_root()
    return root / _DEFAULT_CONFIG


def load_routing_policy(config_path: Path | str | None = None, *, repo_root: Path | None = None) -> dict[str, Any]:
    """Read routing policy YAML and return the parsed dict."""
    if yaml is None:
        raise RuntimeError("PyYAML is required to load routing policy config")

    root = repo_root or find_repo_root()
    path = Path(config_path) if config_path is not None else default_config_path(root)
    if not path.is_absolute():
        path = root / path

    if not path.is_file():
        raise FileNotFoundError(f"routing policy config not found: {path}")

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("routing policy root must be a mapping")
    return payload


def _registry_context_from_cards(cards: list[dict[str, Any]]) -> dict[str, Any]:
    catalog_tool_ids: set[str] = set()
    skeleton_tool_ids: set[str] = set()
    composite_tool_ids: set[str] = set()
    cards_by_id: dict[str, dict[str, Any]] = {}

    for card in cards:
        tool_id = str(card.get("tool_id", "")).strip()
        if not tool_id:
            continue
        catalog_tool_ids.add(tool_id)
        cards_by_id[tool_id] = card
        if card.get("skeleton"):
            skeleton_tool_ids.add(tool_id)
        if str(card.get("entry_kind", "")).strip() == "composite":
            composite_tool_ids.add(tool_id)

    return {
        "catalog_tool_ids": catalog_tool_ids,
        "skeleton_tool_ids": skeleton_tool_ids,
        "composite_tool_ids": composite_tool_ids,
        "cards_by_id": cards_by_id,
    }


def build_registry_context(
    registry: list[dict[str, Any]] | dict[str, Any] | None = None,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Build catalog lookup tables from gov cards or an explicit registry payload."""
    if registry is None:
        cards = load_gov_tool_cards(repo_root=repo_root or find_repo_root())
        return _registry_context_from_cards(cards)
    if isinstance(registry, dict):
        if "catalog_tool_ids" in registry:
            return registry
        cards = registry.get("cards")
        if isinstance(cards, list):
            return _registry_context_from_cards(cards)
    if isinstance(registry, list):
        return _registry_context_from_cards(registry)
    raise TypeError("registry must be None, a card list, or a registry context dict")


def _append_error(errors: list[dict[str, Any]], *, code: str, message: str, **extra: Any) -> None:
    item: dict[str, Any] = {"code": code, "message": message}
    item.update(extra)
    errors.append(item)


def validate_routing_policy(
    policy: dict[str, Any],
    *,
    registry: list[dict[str, Any]] | dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Validate routing policy structure and tool_id references."""
    errors: list[dict[str, Any]] = []
    root = repo_root or find_repo_root()

    if policy.get("schema_version") != _SCHEMA_VERSION:
        _append_error(
            errors,
            code="schema_version",
            message=f"schema_version must be '{_SCHEMA_VERSION}'",
            actual=policy.get("schema_version"),
        )

    tools = policy.get("tools")
    routes = policy.get("routes")
    if not isinstance(tools, list) or not tools:
        _append_error(errors, code="tools", message="tools must be a non-empty list")
        tools = []
    if not isinstance(routes, list) or not routes:
        _append_error(errors, code="routes", message="routes must be a non-empty list")
        routes = []

    ctx = build_registry_context(registry, repo_root=root)
    catalog_tool_ids: set[str] = ctx["catalog_tool_ids"]
    skeleton_tool_ids: set[str] = ctx["skeleton_tool_ids"]
    composite_tool_ids: set[str] = ctx["composite_tool_ids"]

    declared_tools: dict[str, dict[str, Any]] = {}
    for index, tool in enumerate(tools):
        if not isinstance(tool, dict):
            _append_error(errors, code="tools.item", message="tool entry must be a mapping", index=index)
            continue
        tool_id = str(tool.get("tool_id", "")).strip()
        if not tool_id:
            _append_error(errors, code="tools.tool_id", message="tool_id is required", index=index)
            continue
        if tool_id not in catalog_tool_ids:
            _append_error(
                errors,
                code="tools.unknown_catalog",
                message=f"tool_id '{tool_id}' not found in B-F1 Gov Tool Catalog",
                tool_id=tool_id,
                index=index,
            )
        if tool_id in declared_tools:
            _append_error(
                errors,
                code="tools.duplicate",
                message=f"duplicate tool_id '{tool_id}' in tools section",
                tool_id=tool_id,
                index=index,
            )
        declared_tools[tool_id] = tool

    route_ids_seen: set[str] = set()
    for index, route in enumerate(routes):
        if not isinstance(route, dict):
            _append_error(errors, code="routes.item", message="route entry must be a mapping", index=index)
            continue
        route_id = str(route.get("route_id", "")).strip()
        if not route_id:
            _append_error(errors, code="routes.route_id", message="route_id is required", index=index)
            continue
        if route_id in route_ids_seen:
            _append_error(
                errors,
                code="routes.duplicate",
                message=f"duplicate route_id '{route_id}'",
                route_id=route_id,
                index=index,
            )
        route_ids_seen.add(route_id)

        steps = route.get("steps")
        if not isinstance(steps, list) or not steps:
            _append_error(
                errors,
                code="routes.steps",
                message="steps must be a non-empty list",
                route_id=route_id,
                index=index,
            )
            continue

        for step_index, step in enumerate(steps):
            if not isinstance(step, dict):
                _append_error(
                    errors,
                    code="routes.step.item",
                    message="step entry must be a mapping",
                    route_id=route_id,
                    step_index=step_index,
                )
                continue
            kind = str(step.get("kind", "tool")).strip() or "tool"
            tool_id = str(step.get("tool_id", "")).strip()
            if kind != "tool":
                _append_error(
                    errors,
                    code="routes.step.kind",
                    message=f"unsupported step kind '{kind}' (only 'tool' is supported in v1)",
                    route_id=route_id,
                    step_index=step_index,
                    kind=kind,
                )
                continue
            if not tool_id:
                _append_error(
                    errors,
                    code="routes.step.tool_id",
                    message="step tool_id is required when kind=tool",
                    route_id=route_id,
                    step_index=step_index,
                )
                continue
            if tool_id not in declared_tools:
                _append_error(
                    errors,
                    code="routes.step.undeclared_tool",
                    message=f"step tool_id '{tool_id}' is not declared in tools section",
                    route_id=route_id,
                    step_index=step_index,
                    tool_id=tool_id,
                )
            tool_meta = declared_tools.get(tool_id, {})
            if tool_meta and not bool(tool_meta.get("enabled", True)):
                _append_error(
                    errors,
                    code="routes.step.disabled_tool",
                    message=f"step tool_id '{tool_id}' is disabled in tools section",
                    route_id=route_id,
                    step_index=step_index,
                    tool_id=tool_id,
                )
            if tool_id in skeleton_tool_ids:
                _append_error(
                    errors,
                    code="routes.step.skeleton_tool",
                    message=f"step tool_id '{tool_id}' is a skeleton/reference catalog tool",
                    route_id=route_id,
                    step_index=step_index,
                    tool_id=tool_id,
                )
            if tool_id in composite_tool_ids:
                _append_error(
                    errors,
                    code="routes.step.composite_tool",
                    message=(
                        f"step tool_id '{tool_id}' is composite; expand to underlying tools "
                        "(e.g. obs.eval.correlate + obs.trace.query)"
                    ),
                    route_id=route_id,
                    step_index=step_index,
                    tool_id=tool_id,
                )

    total_tools = len(declared_tools)
    total_routes = len(route_ids_seen)
    ok = not errors
    return {
        "ok": ok,
        "message": "valid" if ok else f"{len(errors)} validation error(s)",
        "total_tools": total_tools,
        "total_routes": total_routes,
        "errors": errors,
    }


def get_route(policy: dict[str, Any], route_id: str, *, env: str | None = None) -> dict[str, Any] | None:
    """Return one route dict by route_id, optionally filtered by env."""
    target = str(route_id).strip()
    if not target:
        return None
    for route in policy.get("routes") or []:
        if not isinstance(route, dict):
            continue
        if str(route.get("route_id", "")).strip() != target:
            continue
        if env is not None and str(route.get("env", "")).strip() != str(env).strip():
            continue
        return route
    return None


def resolve_route_tool_ids(
    policy: dict[str, Any],
    route_id: str,
    *,
    env: str | None = None,
) -> dict[str, Any]:
    """
    Resolve a route to ordered tool_id steps from policy config.

    Wave B downstream callers can use this helper to read default routing without
    hard-coding tool sequences in Python.
    """
    route = get_route(policy, route_id, env=env)
    if route is None:
        return {
            "ok": False,
            "message": f"route not found: {route_id}",
            "route_id": route_id,
            "tool_ids": [],
        }

    tool_ids: list[str] = []
    for step in route.get("steps") or []:
        if not isinstance(step, dict):
            continue
        if str(step.get("kind", "tool")).strip() != "tool":
            continue
        tool_id = str(step.get("tool_id", "")).strip()
        if tool_id:
            tool_ids.append(tool_id)

    return {
        "ok": True,
        "message": f"resolved {len(tool_ids)} step(s) for route '{route_id}'",
        "route_id": route_id,
        "env": route.get("env"),
        "description": route.get("description"),
        "tool_ids": tool_ids,
    }


def get_default_wave_b_eval_route_tool_ids(
    *,
    config_path: Path | str | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Load default policy and resolve the Wave B eval report route steps."""
    root = repo_root or find_repo_root()
    policy = load_routing_policy(config_path, repo_root=root)
    result = resolve_route_tool_ids(policy, _DEFAULT_EVAL_ROUTE_ID)
    result["route_id"] = _DEFAULT_EVAL_ROUTE_ID
    return result


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Routing Policy v1 loader (B-F3)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate routing policy config")
    validate_parser.add_argument(
        "--config",
        default=str(_DEFAULT_CONFIG),
        help="Policy YAML path relative to repo root (default: config/routing_policy.yaml)",
    )
    validate_parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repo root override (default: auto-detect)",
    )
    validate_parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="text",
        help="Output format (default: text)",
    )

    resolve_parser = subparsers.add_parser(
        "resolve-route",
        help="resolve a route_id to ordered tool_id steps from policy config",
    )
    resolve_parser.add_argument("--route-id", required=True, help="Route identifier to resolve")
    resolve_parser.add_argument(
        "--config",
        default=str(_DEFAULT_CONFIG),
        help="Policy YAML path relative to repo root",
    )
    resolve_parser.add_argument("--env", default=None, help="Optional env filter")
    resolve_parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repo root override (default: auto-detect)",
    )
    resolve_parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="text",
        help="Output format (default: text)",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_root = args.repo_root or find_repo_root()

    try:
        policy = load_routing_policy(args.config, repo_root=repo_root)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        result = {"ok": False, "message": str(exc), "total_tools": 0, "total_routes": 0, "errors": []}
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"ok=False message={result['message']}")
        return 1

    if args.command == "validate":
        result = validate_routing_policy(policy, repo_root=repo_root)
    else:
        result = resolve_route_tool_ids(policy, args.route_id, env=args.env)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == "validate":
        print(
            f"ok={result.get('ok')} total_tools={result.get('total_tools')} "
            f"total_routes={result.get('total_routes')} errors={len(result.get('errors', []))}"
        )
        print(result.get("message"))
        for item in result.get("errors", []):
            print(f"  - [{item.get('code')}] {item.get('message')}")
    else:
        print(f"ok={result.get('ok')} route_id={result.get('route_id')} tool_ids={result.get('tool_ids')}")
        print(result.get("message"))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
