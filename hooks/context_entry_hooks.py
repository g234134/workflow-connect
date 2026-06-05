"""
Context Entry hooks (Sprint 1 · B-1) — optional pre/post around ``build_rooted_context``.

Default off. Enable via ``GOV_CONTEXT_ENTRY_HOOKS=1`` or per-request
``task_input["_context_entry_hooks"]`` (truthy).

Not a plugin registry: only ``pre_context_entry_hook`` / ``post_context_entry_hook``.
"""

from __future__ import annotations

import copy
import logging
import os
from typing import Any

from context import deny_rules

logger = logging.getLogger(__name__)

ENV_CONTEXT_ENTRY_HOOKS = "GOV_CONTEXT_ENTRY_HOOKS"
_HOOKS_VERSION = "context-entry-hooks-b1-v0.1"
_TASK_INPUT_ENABLE_KEY = "_context_entry_hooks"


def context_entry_hooks_enabled(task_input: dict[str, Any] | None = None) -> bool:
    """Return True when hooks should run (env or per-request flag)."""
    if isinstance(task_input, dict) and task_input.get(_TASK_INPUT_ENABLE_KEY) in (
        True,
        1,
        "1",
        "true",
        "yes",
        "on",
    ):
        return True
    raw = os.environ.get(ENV_CONTEXT_ENTRY_HOOKS)
    if raw is None:
        return False
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _sanity_check_pre(context_entry_input: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    ti = context_entry_input.get("task_input")
    if not isinstance(ti, dict):
        warnings.append("task_input_not_dict")
    mode = str(context_entry_input.get("entry_mode") or "").strip()
    if not mode:
        warnings.append("missing_entry_mode")
    return warnings


def _sanity_check_post(context_entry_output: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if not isinstance(context_entry_output, dict):
        return ["output_not_dict"]
    if context_entry_output.get("ok") is True:
        for key in ("root_context", "working_context", "long_term_memory", "task_input"):
            if key not in context_entry_output:
                warnings.append(f"missing_{key}")
    meta = context_entry_output.get("metadata")
    if meta is not None and not isinstance(meta, dict):
        warnings.append("metadata_not_dict")
    return warnings


def pre_context_entry_hook(context_entry_input: dict[str, Any]) -> None:
    """
    Pre ``build_rooted_context`` hook: log + sanity check (in-place metadata only).

    ``context_entry_input`` keys: ``task_input``, ``entry_mode``.
    """
    warnings = _sanity_check_pre(context_entry_input)
    if warnings:
        logger.warning(
            "context_entry pre_hook sanity: %s mode=%s",
            ",".join(warnings),
            context_entry_input.get("entry_mode"),
        )
    ti = context_entry_input.get("task_input")
    task_id = ti.get("task_id") if isinstance(ti, dict) else None
    logger.info(
        "context_entry pre_hook ok task_id=%s mode=%s",
        task_id,
        context_entry_input.get("entry_mode"),
    )


def post_context_entry_hook(context_entry_output: dict[str, Any]) -> None:
    """
    Post ``build_rooted_context`` hook: log + sanity + harmless ``metadata.hooks`` stamp.
    """
    warnings = _sanity_check_post(context_entry_output)
    if warnings:
        logger.warning(
            "context_entry post_hook sanity: %s ok=%s",
            ",".join(warnings),
            context_entry_output.get("ok"),
        )
    meta = context_entry_output.get("metadata")
    if not isinstance(meta, dict):
        meta = {}
        context_entry_output["metadata"] = meta
    hooks_meta = meta.setdefault("hooks", {})
    if isinstance(hooks_meta, dict):
        hooks_meta["post_ran"] = True
        hooks_meta["version"] = _HOOKS_VERSION
        hooks_meta["post_warnings"] = warnings
        hooks_meta["ok"] = context_entry_output.get("ok")
    deny_meta = meta.get("deny")
    if isinstance(deny_meta, dict):
        obs = deny_meta.get("observability")
        if isinstance(obs, dict) and obs.get("enabled"):
            logger.info(
                "context_entry deny_obs gate=%s denied=%s deny_total=%s phase_hist=%s types_hist=%s",
                deny_meta.get("gate"),
                deny_meta.get("denied"),
                obs.get("deny_total_count"),
                obs.get("phase_hist"),
                obs.get("deny_types_hist"),
            )
    if deny_rules.deny_policy_debug_enabled():
        summary = deny_rules.summarize_deny_policy()
        logger.info(
            "context_entry deny_policy_summary content=%s action=%s gates=%s",
            summary.get("content", {}).get("coverage"),
            summary.get("action", {}).get("coverage"),
            summary.get("registered_gates"),
        )
    logger.info(
        "context_entry post_hook ok=%s entry=%s",
        context_entry_output.get("ok"),
        meta.get("entry"),
    )


def apply_pre_context_entry_hooks(context_entry_input: dict[str, Any]) -> dict[str, Any]:
    """Run pre hook when enabled; return a (possibly copied) input payload."""
    task_input = context_entry_input.get("task_input")
    if not context_entry_hooks_enabled(task_input if isinstance(task_input, dict) else None):
        return context_entry_input
    payload = copy.deepcopy(context_entry_input)
    pre_context_entry_hook(payload)
    return payload


def apply_post_context_entry_hooks(context_entry_output: dict[str, Any]) -> dict[str, Any]:
    """Run post hook when enabled; return a (possibly copied) output dict."""
    task_input = context_entry_output.get("task_input")
    if not context_entry_hooks_enabled(task_input if isinstance(task_input, dict) else None):
        return context_entry_output
    out = copy.deepcopy(context_entry_output)
    post_context_entry_hook(out)
    return out
