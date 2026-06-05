"""
Deny rule tables for context entry v0.1 (R-3a · foundation for deny engine v1).

ContentRuleTable: regex / text patterns scanned on serialized context blobs.
ActionRuleTable: forbidden top-level keys on ``task_input`` (pre-injection only).
GateRunner (R-3b): phase-keyed pipeline over pre_injection / post_assembly gates.
R-3c: A-3 high-risk content rules + optional ``metadata.deny.observability``.

See ``context/context_entry_contract.md`` §2.4 and
``workflow_upgrade/01_context-entry/30_ignore_deny_rules.md`` §5.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Callable, Pattern

RULE_TABLE_VERSION = "deny-rules-v0.3-r3def"
ENV_DENY_OBSERVABILITY = "GOV_CONTEXT_DENY_OBSERVABILITY"
ENV_DENY_POLICY_DEBUG = "GOV_CONTEXT_DENY_POLICY_DEBUG"

# A-3 §5.1 / §5.2 spec inventory (for coverage self-check; not runtime rules).
A3_CONTENT_SPEC_IDS: tuple[str, ...] = (
    "env_secret_plaintext",
    "env_key_literal",
    "instance_absolute_path",
    "checkpoint_binary_blob",
    "full_constitution_mirror",
    "full_cli_trace",
    "eval_sample_raw",
    "rag_hit_with_secrets",
)
A3_ACTION_SPEC_IDS: tuple[str, ...] = (
    "hand_assemble_three_layer_context",
    "hline_bypass_trim",
    "dual_telegram_listener",
    "main_cabin_heavy_ml_stack",
    "new_hashes_txt_fingerprint",
    "unauthorized_z_dark_ops_edit",
    "unauthorized_z_hq_liquidation",
    "unauthorized_z_env_edit",
)
Z_ACTION_SKELETON_IDS: frozenset[str] = frozenset(
    {
        "unauthorized_z_env_edit",
        "unauthorized_z_runtime_cp",
        "unauthorized_z_dark_ops_edit",
        "unauthorized_z_hq_liquidation",
    }
)

# --- ContentRuleTable schema (keys per row) ---
# id, gates, fields, pattern, enabled (optional, default True)

CONTENT_RULE_TABLE: list[dict[str, Any]] = [
    {
        "id": "env_secret_plaintext",
        "phase": "pre_injection",
        "gates": ["pre_injection", "post_assembly", "subtree"],
        "fields": ["task_input", "assembled_layers", "assembled_text", "subtree_context"],
        "pattern": (
            r"(?i)(?:api[_-]?key|secret|token|password)\s*[=:]\s*\S{8,}|"
            r"sk-[a-zA-Z0-9]{20,}|"
            r"Bearer\s+[a-zA-Z0-9._-]{20,}|"
            r"(?:postgresql|mysql|mongodb|redis)://\S+:\S+@"
        ),
        "enabled": True,
    },
    {
        "id": "env_key_literal",
        "phase": "pre_injection",
        "gates": ["pre_injection", "post_assembly", "subtree"],
        "fields": ["task_input", "assembled_layers", "assembled_text", "subtree_context"],
        "pattern": (
            r"(?i)(?:OPENAI|ANTHROPIC|TELEGRAM|GOV_CORE)_[A-Z0-9_]+\s*=\s*(?!\[(?:OK|FAILED)\])"
        ),
        "enabled": True,
    },
    {
        "id": "instance_absolute_path",
        "phase": "pre_injection",
        "gates": ["pre_injection", "post_assembly", "subtree"],
        "fields": ["task_input", "assembled_layers", "assembled_text", "subtree_context"],
        "pattern": (
            r"[A-Za-z]:[\\/][^\s\"']{2,}|"
            r"(?:/[Uu]sers/|/home/)[^\s\"']{2,}"
        ),
        "enabled": True,
    },
    {
        "id": "checkpoint_binary_blob",
        "phase": "pre_injection",
        "gates": ["pre_injection", "post_assembly", "subtree"],
        "fields": ["task_input", "assembled_layers", "assembled_text", "subtree_context"],
        "pattern": (
            r"(?i)(?:runtime[/\\]checkpoints[/\\]|"
            r"checkpoint[_-]?(?:binary|blob|pickle|safetensors)|"
            r"CHECKPOINT_BINARY_BLOB|"
            r"BEGIN\s+CHECKPOINT\s+BLOB)"
        ),
        "enabled": True,
    },
    {
        "id": "full_constitution_mirror",
        "phase": "pre_injection",
        "gates": ["pre_injection", "post_assembly", "subtree"],
        "fields": ["task_input", "assembled_layers", "assembled_text", "subtree_context"],
        "pattern": (
            r"(?is)(?:FULL_CONSTITUTION_MIRROR|CONSTITUTION_FULL_TEXT_MIRROR_BEGIN|"
            r"#+\s*HARNESS\s+CONSTITUTION.{0,400}"
            r"(?:\*\*MUST\*\*|\*\*FORBID\*\*).{0,800}"
            r"(?:\*\*MUST\*\*|\*\*FORBID\*\*).{0,800}"
            r"(?:\*\*MUST\*\*|\*\*FORBID\*\*))"
        ),
        "enabled": True,
    },
    {
        "id": "eval_sample_raw",
        "phase": "pre_injection",
        "gates": ["pre_injection", "post_assembly", "subtree"],
        "fields": ["task_input", "assembled_layers", "assembled_text", "subtree_context"],
        "pattern": (
            r"(?i)(?:EVAL_SAMPLE_RAW(?:_v\d+)?|"
            r"\"eval_sample_raw\"\s*:\s*\{|"
            r"eval_sample_raw\s*[=:]\s*[\"'{]|"
            r"\"raw_prompt\"\s*:\s*\".{200,})"
        ),
        "enabled": True,
    },
    {
        "id": "full_cli_trace",
        "phase": "pre_injection",
        "gates": ["pre_injection", "post_assembly", "subtree"],
        "fields": ["task_input", "assembled_layers", "assembled_text", "subtree_context"],
        "pattern": (
            r"(?i)(?:FULL_CLI_TRACE|"
            r"\"(?:cli_trace|full_trace|command_trace)\"\s*:\s*\{|"
            r"\"trace_id\"\s*:\s*\"[^\"]+\".{0,800}\"(?:events|spans|command_line)\"\s*:)"
        ),
        "enabled": True,
    },
]

# --- ActionRuleTable schema (keys per row) ---
# id, phase, gate, keys, enabled (optional, default True)

ACTION_RULE_TABLE: list[dict[str, Any]] = [
    {
        "id": "hand_assemble_three_layer_context",
        "phase": "pre_injection",
        "gate": "pre_injection",
        "keys": ["root_context", "working_context", "long_term_memory"],
        "enabled": True,
    },
    {
        "id": "hline_bypass_trim",
        "phase": "pre_injection",
        "gate": "pre_injection",
        "keys": [
            "_hline_bypass",
            "hline_bypass_trim",
            "skip_build_context",
            "_hand_assembled_context",
        ],
        "enabled": True,
    },
    {
        "id": "unauthorized_z_env_edit",
        "phase": "pre_injection",
        "gate": "pre_injection",
        "keys": ["_z_env_edit", "z_env_edit", "edit_root_env", "modify_dotenv"],
        "enabled": True,
        "audit": {
            "z_type": "Z-HQ-ENV-EDIT",
            "skeleton": True,
            "detail": "detected unauthorized env edit intent on task_input (skeleton only)",
        },
    },
    {
        "id": "unauthorized_z_runtime_cp",
        "phase": "pre_injection",
        "gate": "pre_injection",
        "keys": [
            "_z_runtime_cp",
            "z_runtime_checkpoint_write",
            "write_checkpoint_unauthorized",
        ],
        "enabled": True,
        "audit": {
            "z_type": "Z-RUNTIME-CP",
            "skeleton": True,
            "detail": "detected unauthorized checkpoint write intent (skeleton only)",
        },
    },
]

_PATTERN_CACHE: dict[tuple[str, ...], tuple[tuple[str, re.Pattern[str]], ...]] = {}


def _rule_enabled(rule: dict[str, Any]) -> bool:
    return bool(rule.get("enabled", True))


def _filter_rules_for_gate(
    rules: list[dict[str, Any]],
    *,
    gate: str | None = None,
) -> list[dict[str, Any]]:
    if gate is None:
        return [r for r in rules if _rule_enabled(r)]
    out: list[dict[str, Any]] = []
    for rule in rules:
        if not _rule_enabled(rule):
            continue
        gates = rule.get("gates")
        if gates is None:
            if str(rule.get("gate") or "") == gate:
                out.append(rule)
            continue
        if gate in gates:
            out.append(rule)
    return out


def compile_content_patterns(
    content_rules: list[dict[str, Any]] | None = None,
    *,
    gate: str | None = None,
) -> tuple[tuple[str, re.Pattern[str]], ...]:
    """Compile enabled content rules to (id, pattern) pairs in table order."""
    table = content_rules if content_rules is not None else CONTENT_RULE_TABLE
    filtered = _filter_rules_for_gate(table, gate=gate)
    cache_key = tuple(
        (str(r.get("id")), str(r.get("pattern")), bool(r.get("enabled", True)))
        for r in filtered
    )
    cached = _PATTERN_CACHE.get(cache_key)
    if cached is not None:
        return cached
    compiled: list[tuple[str, re.Pattern[str]]] = []
    for rule in filtered:
        rule_id = str(rule.get("id") or "").strip()
        raw = rule.get("pattern")
        if not rule_id or not raw:
            continue
        compiled.append((rule_id, re.compile(str(raw))))
    result = tuple(compiled)
    _PATTERN_CACHE[cache_key] = result
    return result


def scan_content_deny_types(
    text: str,
    *,
    content_rules: list[dict[str, Any]] | None = None,
    gate: str | None = None,
) -> list[str]:
    """Return ordered unique content deny type codes found in *text*."""
    if not text:
        return []
    hits: list[str] = []
    for code, pattern in compile_content_patterns(content_rules, gate=gate):
        if pattern.search(text) and code not in hits:
            hits.append(code)
    return hits


def scan_action_deny_types(
    task_input: dict[str, Any],
    *,
    action_rules: list[dict[str, Any]] | None = None,
    gate: str = "pre_injection",
) -> list[str]:
    """Return ordered action deny types from forbidden keys on *task_input*."""
    table = action_rules if action_rules is not None else ACTION_RULE_TABLE
    hits: list[str] = []
    keys_present = set(task_input.keys())
    for rule in table:
        if not _rule_enabled(rule):
            continue
        if str(rule.get("gate") or "pre_injection") != gate:
            continue
        forbidden = rule.get("keys")
        if not isinstance(forbidden, (list, tuple, set, frozenset)):
            continue
        if keys_present.intersection(forbidden) and rule.get("id") not in hits:
            hits.append(str(rule["id"]))
    return hits


def content_rule_ids(
    content_rules: list[dict[str, Any]] | None = None,
    *,
    gate: str | None = None,
) -> list[str]:
    """Ordered ids of enabled content rules (for tests / introspection)."""
    table = content_rules if content_rules is not None else CONTENT_RULE_TABLE
    return [str(r["id"]) for r in _filter_rules_for_gate(table, gate=gate) if r.get("id")]


def action_rule_ids(
    action_rules: list[dict[str, Any]] | None = None,
    *,
    gate: str = "pre_injection",
) -> list[str]:
    """Ordered ids of enabled action rules for a gate."""
    table = action_rules if action_rules is not None else ACTION_RULE_TABLE
    return [
        str(r["id"])
        for r in table
        if _rule_enabled(r) and str(r.get("gate") or "pre_injection") == gate and r.get("id")
    ]


def deny_observability_enabled() -> bool:
    """Return False when ``GOV_CONTEXT_DENY_OBSERVABILITY`` is explicitly off."""
    raw = os.environ.get(ENV_DENY_OBSERVABILITY)
    if raw is None:
        return True
    return raw.strip().lower() not in ("0", "false", "no", "off")


def _gate_phase_label(gate: str) -> str:
    if gate == "pre_injection":
        return "pre"
    if gate == "subtree":
        return "subtree"
    return "post"


def build_deny_observability(
    *,
    gate: str,
    deny_types: list[str],
) -> dict[str, Any]:
    """
    Lightweight deny stats for ``metadata.deny.observability`` (R-3c).

    Records type histogram and pre/post phase for the current deny event only.
    Does not log secret payloads.
    """
    phase = _gate_phase_label(gate)
    hist = {code: 1 for code in deny_types}
    phase_hist = {"pre": 0, "post": 0, "subtree": 0}
    if phase in phase_hist:
        phase_hist[phase] = 1
    return {
        "enabled": True,
        "deny_total_count": len(deny_types),
        "deny_types_hist": hist,
        "phase_hist": phase_hist,
        "rule_table_version": RULE_TABLE_VERSION,
        "events": [
            {
                "gate": gate,
                "phase": phase,
                "deny_types": list(deny_types),
            }
        ],
    }


def cleared_deny_observability() -> dict[str, Any]:
    """Observability block when no deny fired (happy path)."""
    if not deny_observability_enabled():
        return {"enabled": False}
    return {
        "enabled": True,
        "deny_total_count": 0,
        "deny_types_hist": {},
        "phase_hist": {"pre": 0, "post": 0, "subtree": 0},
        "rule_table_version": RULE_TABLE_VERSION,
        "events": [],
    }


def _collect_forbidden_types_from_mapping(mapping: dict[str, Any]) -> tuple[set[str], set[str]]:
    content: set[str] = set()
    action: set[str] = set()
    for key in ("forbidden_content_types", "append_forbidden_content_types"):
        raw = mapping.get(key)
        if isinstance(raw, (list, tuple, set, frozenset)):
            content.update(str(x) for x in raw if str(x).strip())
    for key in ("forbidden_action_types", "append_forbidden_action_types"):
        raw = mapping.get(key)
        if isinstance(raw, (list, tuple, set, frozenset)):
            action.update(str(x) for x in raw if str(x).strip())
    return content, action


def merge_subtree_deny_union(
    *,
    root_context: dict[str, Any],
    subtree_context: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Step ③ union: root ``hard_rules`` ∪ active subtree ``scope_constraints`` / ``forbidden_*``.

    Subtree may only append stricter deny types; this helper collects the effective union
  for audit and subtree gate scanning (R-3d).
    """
    root_hard = root_context.get("hard_rules")
    root_hard = root_hard if isinstance(root_hard, dict) else {}
    content_types, action_types = _collect_forbidden_types_from_mapping(root_hard)

    active_subtree_ids: list[str] = []
    scope_constraints: list[dict[str, Any]] = []

    for record in subtree_context:
        if not isinstance(record, dict) or not record.get("active"):
            continue
        subtree_id = str(record.get("subtree_id") or "").strip()
        if subtree_id:
            active_subtree_ids.append(subtree_id)
        sub_content, sub_action = _collect_forbidden_types_from_mapping(record)
        content_types.update(sub_content)
        action_types.update(sub_action)

        sc = record.get("scope_constraints")
        if isinstance(sc, dict):
            scope_constraints.append({"subtree_id": subtree_id, **sc})
            sc_content, sc_action = _collect_forbidden_types_from_mapping(sc)
            content_types.update(sc_content)
            action_types.update(sc_action)
        elif isinstance(sc, list):
            for item in sc:
                if not isinstance(item, dict):
                    continue
                scope_constraints.append({"subtree_id": subtree_id, **item})
                sc_content, sc_action = _collect_forbidden_types_from_mapping(item)
                content_types.update(sc_content)
                action_types.update(sc_action)

    return {
        "forbidden_content_types": sorted(content_types),
        "forbidden_action_types": sorted(action_types),
        "active_subtree_ids": active_subtree_ids,
        "scope_constraints": scope_constraints,
    }


def build_subtree_deny_payload(payload: dict[str, Any]) -> str:
    """Serialize active subtree layer + merged deny union for subtree gate scan."""
    result = payload.get("result")
    if not isinstance(result, dict):
        result = {}
    subtree_context = payload.get("subtree_context")
    if not isinstance(subtree_context, list):
        subtree_context = result.get("subtree_context")
    if not isinstance(subtree_context, list):
        subtree_context = []
    root_context = result.get("root_context")
    if not isinstance(root_context, dict):
        root_context = {}
    deny_union = payload.get("deny_union")
    if not isinstance(deny_union, dict):
        deny_union = merge_subtree_deny_union(
            root_context=root_context,
            subtree_context=subtree_context,
        )
    active_records = [r for r in subtree_context if isinstance(r, dict) and r.get("active")]
    return json.dumps(
        {
            "subtree_context": active_records,
            "deny_union": deny_union,
        },
        ensure_ascii=False,
        default=str,
    )


def _action_audit_details(
    deny_types: list[str],
    *,
    action_rules: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    table = action_rules if action_rules is not None else ACTION_RULE_TABLE
    by_id = {str(r.get("id")): r for r in table if r.get("id")}
    details: list[dict[str, Any]] = []
    for code in deny_types:
        rule = by_id.get(code)
        audit = rule.get("audit") if isinstance(rule, dict) else None
        if not isinstance(audit, dict):
            continue
        details.append(
            {
                "deny_type": code,
                "z_type": audit.get("z_type"),
                "skeleton": bool(audit.get("skeleton")),
                "detail": str(audit.get("detail") or ""),
            }
        )
    return details


def list_builtin_deny_rules(
    *,
    content_rules: list[dict[str, Any]] | None = None,
    action_rules: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return enabled builtin rule ids grouped by table (debug / policy self-check)."""
    return {
        "rule_table_version": RULE_TABLE_VERSION,
        "content_rule_ids": content_rule_ids(content_rules),
        "action_rule_ids": action_rule_ids(action_rules),
        "registered_gates": list(registered_gates(active_only=True)),
    }


def summarize_deny_policy(
    *,
    content_rules: list[dict[str, Any]] | None = None,
    action_rules: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Policy coverage self-check against A-3 §5 inventory (R-3f).

    Does not alter runtime deny behavior; intended for REPL / debug introspection.
    """
    content_table = content_rules if content_rules is not None else CONTENT_RULE_TABLE
    action_table = action_rules if action_rules is not None else ACTION_RULE_TABLE
    implemented_content = set(content_rule_ids(content_table))
    implemented_action = set(action_rule_ids(action_table))

    # rag_hit_with_secrets is post-derived, not a CONTENT_RULE_TABLE row.
    content_spec = [x for x in A3_CONTENT_SPEC_IDS if x != "rag_hit_with_secrets"]
    missing_content = [x for x in content_spec if x not in implemented_content]
    missing_action = [x for x in A3_ACTION_SPEC_IDS if x not in implemented_action]

    content_impl_count = len([x for x in content_spec if x in implemented_content])
    action_impl_count = len([x for x in A3_ACTION_SPEC_IDS if x in implemented_action])

    z_skeletons = sorted(implemented_action.intersection(Z_ACTION_SKELETON_IDS))

    return {
        "ok": True,
        "rule_table_version": RULE_TABLE_VERSION,
        "content": {
            "implemented_ids": sorted(implemented_content),
            "builtin_count": len(content_rule_ids(content_table)),
            "a3_spec_total": len(content_spec),
            "a3_spec_implemented": content_impl_count,
            "coverage": f"{content_impl_count}/{len(content_spec)}",
            "missing_from_a3": missing_content,
            "post_derived": ["rag_hit_with_secrets"],
        },
        "action": {
            "implemented_ids": sorted(implemented_action),
            "builtin_count": len(action_rule_ids(action_table)),
            "a3_spec_total": len(A3_ACTION_SPEC_IDS),
            "a3_spec_implemented": action_impl_count,
            "coverage": f"{action_impl_count}/{len(A3_ACTION_SPEC_IDS)}",
            "missing_from_a3": missing_action,
            "z_action_skeletons": z_skeletons,
        },
        "registered_gates": list(registered_gates(active_only=True)),
    }


def deny_policy_debug_enabled() -> bool:
    raw = os.environ.get(ENV_DENY_POLICY_DEBUG)
    if raw is None:
        return False
    return raw.strip().lower() in ("1", "true", "yes", "on")


# --- GateRunner pipeline (R-3b) ---

DenyGateName = str
PayloadBuilder = Callable[[dict[str, Any]], str]
DenyPostProcessor = Callable[[list[str]], list[str]]

def _pre_injection_payload_blob(payload: dict[str, Any]) -> str:
    task_input = payload.get("task_input")
    if not isinstance(task_input, dict):
        task_input = {}
    return json.dumps(task_input, ensure_ascii=False, default=str)


def _post_assembly_payload_blob(payload: dict[str, Any]) -> str:
    result = payload.get("result")
    if not isinstance(result, dict):
        result = {}
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    layers = {
        "root_context": result.get("root_context") or {},
        "working_context": result.get("working_context") or {},
        "long_term_memory": result.get("long_term_memory") or {},
    }
    assembled = str(result.get("assembled_text") or "")
    return json.dumps(
        {**layers, "assembled_text": assembled, "metadata": metadata},
        ensure_ascii=False,
        default=str,
    )


def _post_assembly_deny_post_process(deny_types: list[str]) -> list[str]:
    if deny_types and "rag_hit_with_secrets" not in deny_types:
        return [*deny_types, "rag_hit_with_secrets"]
    return deny_types


GATE_PIPELINE: dict[DenyGateName, dict[str, Any]] = {
    "pre_injection": {
        "contract_phase": "P0",
        "detail": "task_input blocked before context assembly",
        "scan_action": True,
        "scan_content": True,
        "build_blob": _pre_injection_payload_blob,
        "post_process": None,
    },
    "post_assembly": {
        "contract_phase": "P1",
        "detail": "assembled context blocked after build_context",
        "scan_action": False,
        "scan_content": True,
        "build_blob": _post_assembly_payload_blob,
        "post_process": _post_assembly_deny_post_process,
    },
    # R-3d: subtree gate — step ③ deny union on active subtree layer (P0.5).
    "subtree": {
        "contract_phase": "P0.5",
        "detail": "subtree layer blocked after trim; root ∪ active subtree deny union",
        "scan_action": False,
        "scan_content": True,
        "build_blob": build_subtree_deny_payload,
        "post_process": None,
        "enabled": True,
    },
}


def registered_gates(*, active_only: bool = True) -> tuple[str, ...]:
    """Gate names known to the pipeline (``active_only`` skips disabled stubs)."""
    if not active_only:
        return tuple(GATE_PIPELINE.keys())
    return tuple(
        name
        for name, spec in GATE_PIPELINE.items()
        if spec.get("enabled", True) is not False
    )


def run_deny_gates(
    gate: DenyGateName,
    payload: dict[str, Any],
    *,
    content_rules: list[dict[str, Any]] | None = None,
    action_rules: list[dict[str, Any]] | None = None,
) -> list[str]:
    """
    Run deny scans for *gate* on *payload* and return ordered deny type codes.

    *payload* shape depends on gate (see ``GATE_PIPELINE``):
    - ``pre_injection``: ``{"task_input": dict}``
    - ``post_assembly``: ``{"result": dict, "metadata": dict}``
    """
    spec = GATE_PIPELINE.get(gate)
    if spec is None or spec.get("enabled", True) is False:
        return []

    deny_types: list[str] = []

    if spec.get("scan_action"):
        task_input = payload.get("task_input")
        if not isinstance(task_input, dict):
            task_input = {}
        for code in scan_action_deny_types(
            task_input, action_rules=action_rules, gate=gate
        ):
            if code not in deny_types:
                deny_types.append(code)

    if spec.get("scan_content"):
        build_blob = spec.get("build_blob")
        if callable(build_blob):
            blob = build_blob(payload)
        else:
            blob = ""
        for code in scan_content_deny_types(blob, content_rules=content_rules, gate=gate):
            if code not in deny_types:
                deny_types.append(code)

    post_process = spec.get("post_process")
    if callable(post_process):
        deny_types = post_process(deny_types)

    return deny_types


def attach_deny_observability(deny: dict[str, Any]) -> dict[str, Any]:
    """Merge optional observability into an existing ``metadata.deny`` dict (R-3c)."""
    if not deny_observability_enabled():
        deny["observability"] = {"enabled": False}
        return deny
    gate = str(deny.get("gate") or "")
    deny_types = list(deny.get("deny_types") or [])
    if deny.get("denied"):
        deny["observability"] = build_deny_observability(gate=gate, deny_types=deny_types)
    else:
        deny["observability"] = cleared_deny_observability()
    return deny


def format_deny_hit(
    gate: DenyGateName,
    deny_types: list[str],
    *,
    extra: dict[str, Any] | None = None,
    action_rules: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Map gate hits to ``metadata.deny`` contract shape; ``None`` when no hits."""
    if not deny_types:
        return None
    spec = GATE_PIPELINE.get(gate) or {}
    deny: dict[str, Any] = {
        "denied": True,
        "gate": gate,
        "phase": str(spec.get("contract_phase") or ""),
        "deny_types": deny_types,
        "detail": str(spec.get("detail") or ""),
    }
    audit = _action_audit_details(deny_types, action_rules=action_rules)
    if audit:
        deny["action_audit"] = audit
    if isinstance(extra, dict):
        deny.update(extra)
    return attach_deny_observability(deny)


class GateRunner:
    """Configurable deny gate runner over content + action rule tables."""

    def __init__(
        self,
        *,
        content_rules: list[dict[str, Any]] | None = None,
        action_rules: list[dict[str, Any]] | None = None,
    ) -> None:
        self.content_rules = content_rules
        self.action_rules = action_rules

    def run(self, gate: DenyGateName, payload: dict[str, Any]) -> list[str]:
        return run_deny_gates(
            gate,
            payload,
            content_rules=self.content_rules,
            action_rules=self.action_rules,
        )

    def run_hit(
        self,
        gate: DenyGateName,
        payload: dict[str, Any],
        *,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        return format_deny_hit(
            gate,
            self.run(gate, payload),
            extra=extra,
            action_rules=self.action_rules,
        )
