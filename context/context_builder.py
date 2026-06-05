"""
Context builder for D2 — layered context assembly with mock memory retrieval.

Layers:
  - root_context: system rules / navigation / global instructions
  - working_context: current task (short-lived)
  - long_term_memory: semantic (Qdrant mock) + structured (Postgres mock)

See: context/context_model.md, context/memory_routing_rules.md
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Final

from contract.constants import MAX_TOTAL_TOKEN_BUDGET

# --- Token budget (v0.1 placeholders; see context_model.md §4) ---

ROOT_RESERVED_TOKENS: Final[int] = 12_000
ROOT_MIN_TOKENS: Final[int] = 4_000
MEMORY_MAX_TOKENS: Final[int] = 40_000
WORKING_MAX_TOKENS: Final[int] = 76_000

# Trim priority: lower number = trim first (evict first)
TRIM_PRIORITY: Final[tuple[str, ...]] = (
    "working_context.scratch",
    "working_context.conversation_turns",
    "working_context.tool_results",
    "long_term_memory.semantic",
    "long_term_memory.structured",
    "working_context.constraints",
    "working_context.task_input",
    "root_context",
)

_CHARS_PER_TOKEN: Final[int] = 4


def estimate_tokens(text: str) -> int:
    """Rough token estimate for v0.1 (no tiktoken)."""
    if not text:
        return 0
    return max(1, len(text) // _CHARS_PER_TOKEN)


def _estimate_tokens_obj(obj: Any) -> int:
    return estimate_tokens(json.dumps(obj, ensure_ascii=False, default=str))


@dataclass
class TrimResult:
    data: dict[str, Any]
    trimming_applied: list[str] = field(default_factory=list)
    token_usage: dict[str, int] = field(default_factory=dict)


def _load_root_context() -> dict[str, Any]:
    """Static root slice (mock). Real impl: versioned registry + constitution refs."""
    return {
        "version": "v0.1",
        "role": "大唐副官 / D2 context builder",
        "global_instructions": [
            "遵守 HARNESS_CONSTITUTION 禁區类型；不输出密钥原文。",
            "路径使用 Master_Map 逻辑名，禁止硬编码磁盘路径。",
            "核心接口返回结构化 dict（ok / message / result）。",
        ],
        "navigation": {
            "agents_entry": "AGENTS.md",
            "constitution": "04_Workflows/HARNESS_CONSTITUTION.md",
            "contract": "04_Workflows/ENGINEERING_CONTRACT.md",
            "runners_index": "04_Workflows/Master_Map.json",
        },
        "red_lines_summary": [
            "禁止打印 .env 或密钥",
            "禁止双 Telegram 监听",
            "禁止主舱安装 crewai/langchain 等重套件",
        ],
    }


def _mock_retrieve_semantic(query: str, *, top_k: int = 5) -> dict[str, Any]:
    """Mock Qdrant semantic retrieval."""
    if not query.strip():
        return {"hits": [], "lookup_count": 0}
    hits = [
        {
            "chunk_id": f"mock-chunk-{i}",
            "score": round(0.95 - i * 0.08, 3),
            "text": f"[mock semantic] 与「{query[:40]}」相关的规程摘录 #{i}。",
            "source_type": "document_chunk",
        }
        for i in range(min(top_k, 3))
    ]
    return {"hits": hits, "lookup_count": 1}


def _mock_retrieve_structured(
    *,
    task_id: str | None,
    work_order_id: str | None,
) -> dict[str, Any]:
    """Mock Postgres structured retrieval."""
    if not task_id and not work_order_id:
        return {"rows": [], "lookup_count": 0}
    key = work_order_id or task_id or "unknown"
    return {
        "rows": [
            {
                "schema_version": "task_memory_entry_v1",
                "work_order_id": work_order_id or f"wo-{key}",
                "task_id": task_id,
                "outcome": "success",
                "request_type": "mock",
                "gate_scores_at_intake": {"cost": 0.3, "risk": 0.1},
            }
        ],
        "lookup_count": 1,
    }


def _assemble_working_context(
    task_input: dict[str, Any],
    *,
    semantic: dict[str, Any],
    structured: dict[str, Any],
) -> dict[str, Any]:
    """Merge task-local fields with retrieved memory references."""
    return {
        "task_input": deepcopy(task_input),
        "goal": task_input.get("goal") or task_input.get("query") or "",
        "constraints": list(task_input.get("constraints") or []),
        "conversation_turns": list(task_input.get("conversation_turns") or []),
        "tool_results": list(task_input.get("tool_results") or []),
        "prior_outputs": list(task_input.get("prior_outputs") or []),
        "scratch": dict(task_input.get("scratch") or {}),
        "retrieved_semantic_refs": semantic.get("hits") or [],
        "retrieved_structured_refs": structured.get("rows") or [],
    }


def _text_slice_to_token_budget(text: str, max_tokens: int) -> tuple[str, bool]:
    """Truncate text to fit max_tokens; returns (text, was_trimmed)."""
    current = estimate_tokens(text)
    if current <= max_tokens:
        return text, False
    max_chars = max_tokens * _CHARS_PER_TOKEN
    return text[:max_chars] + "\n…[trimmed]", True


def _trim_list_by_tokens(items: list[Any], max_tokens: int, *, label: str) -> tuple[list[Any], list[str]]:
    """Drop items from the end until list serializes under max_tokens."""
    log: list[str] = []
    trimmed = list(items)
    while trimmed and _estimate_tokens_obj(trimmed) > max_tokens:
        trimmed.pop()
        log.append(f"{label}: dropped trailing item")
    return trimmed, log


def _apply_trimming(
    root: dict[str, Any],
    working: dict[str, Any],
    memory: dict[str, Any],
) -> TrimResult:
    """
    Enforce MAX_TOTAL_TOKEN_BUDGET using TRIM_PRIORITY (low priority trimmed first).
    """
    data = {
        "root_context": deepcopy(root),
        "working_context": deepcopy(working),
        "long_term_memory": deepcopy(memory),
    }
    log: list[str] = []

    def total_tokens() -> int:
        return _estimate_tokens_obj(data)

    def section_tokens(key: str) -> int:
        return _estimate_tokens_obj(data[key])

    # --- Pass 1: cap memory sub-layers ---
    sem = data["long_term_memory"].get("semantic") or {}
    hits = list(sem.get("hits") or [])
    hits, sem_log = _trim_list_by_tokens(
        hits,
        MEMORY_MAX_TOKENS // 2,
        label="long_term_memory.semantic",
    )
    log.extend(sem_log)
    sem["hits"] = hits
    data["long_term_memory"]["semantic"] = sem

    struct = data["long_term_memory"].get("structured") or {}
    rows = list(struct.get("rows") or [])
    rows, row_log = _trim_list_by_tokens(
        rows,
        MEMORY_MAX_TOKENS // 2,
        label="long_term_memory.structured",
    )
    log.extend(row_log)
    struct["rows"] = rows
    data["long_term_memory"]["structured"] = struct

    # --- Pass 2: global budget — walk trim priority ---
    for path in TRIM_PRIORITY:
        if total_tokens() <= MAX_TOTAL_TOKEN_BUDGET:
            break
        if path == "working_context.scratch":
            if data["working_context"].get("scratch"):
                data["working_context"]["scratch"] = {}
                log.append(path)
        elif path == "working_context.conversation_turns":
            turns = data["working_context"].get("conversation_turns") or []
            if turns:
                data["working_context"]["conversation_turns"], tlog = _trim_list_by_tokens(
                    turns, max(estimate_tokens(json.dumps(turns[-1:], default=str)), 1), label=path
                )
                log.extend(tlog)
        elif path == "working_context.tool_results":
            tools = data["working_context"].get("tool_results") or []
            if tools:
                data["working_context"]["tool_results"], tlog = _trim_list_by_tokens(
                    tools, WORKING_MAX_TOKENS // 4, label=path
                )
                log.extend(tlog)
        elif path == "long_term_memory.semantic":
            h = sem.get("hits") or []
            if len(h) > 1:
                sem["hits"] = h[:-1]
                log.append(f"{path}: removed lowest-score chunk")
        elif path == "long_term_memory.structured":
            r = struct.get("rows") or []
            if r:
                struct["rows"] = r[:-1]
                log.append(f"{path}: dropped row")
        elif path == "working_context.task_input":
            ti = data["working_context"].get("task_input") or {}
            attachments = ti.get("attachments")
            if isinstance(attachments, str) and attachments:
                ti["attachments"], _ = _text_slice_to_token_budget(attachments, 2_000)
                data["working_context"]["task_input"] = ti
                log.append(f"{path}: trimmed attachments")
        elif path == "root_context":
            # Compress narrative fields only; keep red_lines / navigation keys
            sections = data["root_context"].get("global_instructions") or []
            if len(sections) > 2:
                data["root_context"]["global_instructions"] = sections[:2]
                log.append(f"{path}: compressed global_instructions")

    # --- Pass 3: hard floor on root ---
    root_t = section_tokens("root_context")
    if root_t > ROOT_RESERVED_TOKENS:
        blob = json.dumps(data["root_context"], ensure_ascii=False)
        blob, _ = _text_slice_to_token_budget(blob, ROOT_RESERVED_TOKENS)
        try:
            data["root_context"] = json.loads(blob.replace("\n…[trimmed]", ""))
        except json.JSONDecodeError:
            data["root_context"] = _load_root_context()
        log.append("root_context: reserved cap applied")

    if section_tokens("root_context") < ROOT_MIN_TOKENS // 2:
        # Restore minimal root if over-trimmed
        data["root_context"] = _load_root_context()
        log.append("root_context: restored to mock minimum")

    usage = {
        "root": section_tokens("root_context"),
        "working": section_tokens("working_context"),
        "memory": section_tokens("long_term_memory"),
        "total": total_tokens(),
    }
    return TrimResult(data=data, trimming_applied=log, token_usage=usage)


def _compute_memory_hit_rate(
    semantic: dict[str, Any],
    structured: dict[str, Any],
) -> float:
    lookups = int(semantic.get("lookup_count") or 0) + int(structured.get("lookup_count") or 0)
    if lookups == 0:
        return 0.0
    hits = len(semantic.get("hits") or []) + len(structured.get("rows") or [])
    return min(1.0, hits / lookups)


def _assemble_prompt_text(layers: dict[str, Any]) -> str:
    """Single string view for LLM prompt (debug / legacy adapters)."""
    parts = [
        "# Root Context",
        json.dumps(layers.get("root_context") or {}, ensure_ascii=False, indent=2),
        "# Working Context",
        json.dumps(layers.get("working_context") or {}, ensure_ascii=False, indent=2),
        "# Long-term Memory",
        json.dumps(layers.get("long_term_memory") or {}, ensure_ascii=False, indent=2),
    ]
    return "\n\n".join(parts)


def build_context(task_input: dict[str, Any]) -> dict[str, Any]:
    """
    Build layered context for one agent invocation.

    Parameters
    ----------
    task_input:
        Expected keys (all optional except useful query/goal):
        ``task_id``, ``goal``, ``query``, ``work_order_id``, ``constraints``,
        ``conversation_turns``, ``tool_results``, ``prior_outputs``, ``scratch``.

    Returns
    -------
    dict
        Contract shape: ``ok``, ``message``, ``result``, ``metadata``.
    """
    if not isinstance(task_input, dict):
        return {
            "ok": False,
            "message": "task_input must be a dict",
            "result": {},
            "metadata": {},
        }

    task_id = task_input.get("task_id")
    work_order_id = task_input.get("work_order_id")
    query = str(task_input.get("query") or task_input.get("goal") or "").strip()

    root = _load_root_context()
    semantic = _mock_retrieve_semantic(query, top_k=int(task_input.get("semantic_top_k") or 5))
    structured = _mock_retrieve_structured(
        task_id=str(task_id) if task_id else None,
        work_order_id=str(work_order_id) if work_order_id else None,
    )
    memory = {
        "semantic": semantic,
        "structured": structured,
    }
    working = _assemble_working_context(task_input, semantic=semantic, structured=structured)

    trimmed = _apply_trimming(root, working, memory)
    layers = trimmed.data
    assembled_text = _assemble_prompt_text(layers)

    overflow = trimmed.token_usage["total"] > MAX_TOTAL_TOKEN_BUDGET
    memory_hit_rate = _compute_memory_hit_rate(semantic, structured)

    return {
        "ok": not overflow,
        "message": (
            "context assembled"
            if not overflow
            else f"context exceeds budget after trim ({trimmed.token_usage['total']} > {MAX_TOTAL_TOKEN_BUDGET})"
        ),
        "result": {
            **layers,
            "assembled_text": assembled_text,
        },
        "metadata": {
            "token_budget": {
                "max_total": MAX_TOTAL_TOKEN_BUDGET,
                "root_reserved": ROOT_RESERVED_TOKENS,
                "root_min": ROOT_MIN_TOKENS,
                "memory_max": MEMORY_MAX_TOKENS,
                "working_max": WORKING_MAX_TOKENS,
            },
            "token_usage": trimmed.token_usage,
            "trimming_applied": trimmed.trimming_applied,
            "memory_hit_rate": memory_hit_rate,
            "trim_priority": list(TRIM_PRIORITY),
        },
    }


def main() -> None:
    """CLI smoke for local verification."""
    sample = {
        "task_id": "task-demo-001",
        "work_order_id": "wo-demo-001",
        "goal": "设计 D2 context 分层并验证裁剪",
        "constraints": ["仅 mock，不连真实 DB"],
        "conversation_turns": [
            {"role": "user", "content": "接战"},
            {"role": "assistant", "content": "已读 AGENTS"},
        ],
        "tool_results": [{"tool": "grep", "output": "x" * 5000}],
        "scratch": {"note": "ephemeral"},
    }
    out = build_context(sample)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
