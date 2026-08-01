# boot_context.py — 三層接戰讀檔計畫（HQ boot bootstrap）
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from gov_paths import get_tang_gov_root, load_master_map
from ops_cycle import get_cycle_artifact_paths
from task_routing import enrich_route_with_runners, route_task

BOOT_SCHEMA_VERSION = "v1"

# Tier 2：一般接戰最小讀檔（非治理票）
TIER2_BASE: List[Dict[str, Any]] = [
    {
        "tier": 2,
        "path": "04_Workflows/HARNESS_CONSTITUTION.md",
        "scope": "§7 禁區類型",
        "reason": "確認禁區類型與授權邊界",
    },
    {
        "tier": 2,
        "path": "04_Workflows/00_Agent_Work_Progress.md",
        "scope": "末尾 N 行（見 progress_tail）",
        "reason": "最近戰報與阻塞",
    },
    {
        "tier": 2,
        "path": "04_Workflows/project_status/master_status.md",
        "scope": "最近 1 段里程碑",
        "reason": "跨 agent 里程碑快照",
    },
]

# Tier 4：治理／制度票全文
TIER4_DOCS: List[Dict[str, Any]] = [
    {
        "tier": 4,
        "path": "04_Workflows/HARNESS_CONSTITUTION.md",
        "scope": "full",
        "reason": "治理票需完整憲法上下文",
    },
    {
        "tier": 4,
        "path": "04_Workflows/ENGINEERING_CONTRACT.md",
        "scope": "full",
        "reason": "治理票需完整合約",
    },
    {
        "tier": 4,
        "path": "04_Workflows/DEPARTMENT_MAP.md",
        "scope": "full",
        "reason": "組織拓撲",
    },
    {
        "tier": 4,
        "path": "04_Workflows/INSTANCE_ANCHOR_TANG.md",
        "scope": "full",
        "reason": "實例路徑與禁區清單",
    },
    {
        "tier": 4,
        "path": "04_Workflows/_PORTABLE_CORE_INDEX.md",
        "scope": "full",
        "reason": "W0 可移植 vs 錨點分流",
    },
]

SKIP_DEFAULT: List[str] = [
    "04_Workflows/ENGINEERING_CONTRACT.md（全文；`.cursor/rules/engineering-contract.mdc` 已 alwaysApply）",
    "04_Workflows/WORKFLOW_INDEX.md（全文；僅讀 boot 指派的 §1.x 節）",
    "04_Workflows/TASK_ROUTING.md（由 `_route_task.py` / boot JSON 替代）",
    "04_Workflows/OPS_CYCLE.md（接戰不必讀；封存時對照 `_ops_cycle.py checklist`）",
]

TASK_TYPE_HINTS: Dict[str, Dict[str, Any]] = {
    "hq.governance": {
        "tier_label": "4",
        "tier4": True,
        "workflow_index_section": "1.5",
    },
    "hq.qa": {
        "tier_label": "2+3",
        "extra_read": [
            {
                "tier": 3,
                "path": "04_Workflows/00_Agent_Work_Conditions.md",
                "scope": "Smoke Test 對應條目",
                "reason": "QA 驗收標準",
            },
        ],
    },
    "hq.tooling": {
        "tier_label": "2+3",
        "extra_read": [
            {
                "tier": 3,
                "path": "04_Workflows/runbooks/GOV_CORE_OPERATING_MAP_v0.1.md",
                "scope": "HQ 工具層路徑",
                "reason": "tooling 任務常涉 config 樹",
            },
        ],
    },
    "chariot.smoke": {
        "tier_label": "2+3",
        "workflow_index_section": "1.1",
        "extra_read": [
            {
                "tier": 3,
                "path": "04_Workflows/runbooks/GOV_CORE_SMOKE_TEST_RUNBOOK_v0.1.md",
                "scope": "full",
                "reason": "Smoke 步驟與驗收",
            },
            {
                "tier": 3,
                "path": "04_Workflows/00_Agent_Work_Conditions.md",
                "scope": "Gov Core V1 最小 Smoke Test 條目",
                "reason": "驗收標準",
            },
        ],
    },
    "chariot.factory": {
        "tier_label": "2+3",
        "workflow_index_section": "1.1",
        "extra_read": [
            {
                "tier": 3,
                "path": "04_Workflows/runbooks/GOV_CORE_OPERATING_MAP_v0.1.md",
                "scope": "full",
                "reason": "主艙／工廠路徑",
            },
        ],
    },
    "chariot.scout": {
        "tier_label": "2+3",
        "extra_read": [
            {
                "tier": 3,
                "path": "04_Workflows/runbooks/GOV_CORE_OPERATING_MAP_v0.1.md",
                "scope": "副艙路徑",
                "reason": "agency 偵察工作目錄",
            },
        ],
    },
    "hq.coordination": {
        "tier_label": "2",
        "extra_read": [
            {
                "tier": 3,
                "path": "docs/GOVERNANCE_ONBOARDING_v1.md",
                "scope": "三層接戰對照",
                "reason": "協調／待命時快速對齊",
            },
        ],
    },
}

CATALOG_KEYWORD_ENTRIES: List[Dict[str, Any]] = [
    {
        "id": "tabular_mvp",
        "keywords": ["tabular", "清洗", "delivery", "sampleco", "demo_phase", "mvp mainline"],
        "workflow_index_section": "1.7",
        "read": [
            {
                "tier": 3,
                "path": "docs/TABULAR_MVP_SSOT.md",
                "scope": "full",
                "reason": "Tabular 產品主線 SSOT",
            },
        ],
    },
    {
        "id": "rag_smoke",
        "keywords": ["rag smoke", "rag_smoke", "document_chunks", "retrieval", "向量"],
        "workflow_index_section": "1.2",
        "read": [
            {
                "tier": 3,
                "path": "04_Workflows/runbooks/RAG_SMOKE_TEST_RUNBOOK_v0.1.md",
                "scope": "full",
                "reason": "RAG smoke 步驟",
            },
        ],
    },
    {
        "id": "bridge_p85",
        "keywords": ["bridge", "p85", "orchestration/bridge", "minimal_intake_browser", "phase 8.6"],
        "workflow_index_section": "1.4",
        "read": [
            {
                "tier": 3,
                "path": "docs/phase8_5-bridge-smoke-runbook-v1.md",
                "scope": "full",
                "reason": "P85 bridge smoke SSOT",
            },
        ],
    },
    {
        "id": "phase5_probe",
        "keywords": ["phase5", "seed_pg", "task_runs", "probe"],
        "workflow_index_section": "1.3",
        "read": [
            {
                "tier": 3,
                "path": "01_Environments/python_venvs/gov_core_system/Departments/05_Data_Vault/README.md",
                "scope": "§4–§5",
                "reason": "Phase 5 probe runbook",
            },
        ],
    },
    {
        "id": "multi_chat",
        "keywords": ["multi-chat", "multi chat", "orchestrator", "implementer", "scribe", "b-f2"],
        "read": [
            {
                "tier": 3,
                "path": ".cursor/rules/multi_chat_roles.mdc",
                "scope": "對應角色小節",
                "reason": "Multi-Chat 四角色邊界",
            },
        ],
    },
]


def _normalize(text: str) -> str:
    return text.strip().lower()


def _score_catalog(text: str, keywords: List[str]) -> int:
    hay = _normalize(text)
    score = 0
    for kw in keywords or []:
        token = _normalize(str(kw))
        if not token:
            continue
        if token in hay:
            score += 2
        elif re.search(re.escape(token), hay):
            score += 1
    return score


def _match_catalog(text: str) -> List[Dict[str, Any]]:
    hits: List[tuple[int, Dict[str, Any]]] = []
    master = load_master_map()
    catalogs: List[Dict[str, Any]] = list(CATALOG_KEYWORD_ENTRIES)
    for entry in master.get("index_catalog") or []:
        if not isinstance(entry, dict):
            continue
        if entry.get("keywords") or entry.get("read_first"):
            catalogs.append(entry)
    for entry in catalogs:
        kws = list(entry.get("keywords") or [])
        score = _score_catalog(text, kws) if kws else 0
        if score > 0:
            hits.append((score, entry))
    hits.sort(key=lambda x: x[0], reverse=True)
    return [h[1] for h in hits[:3]]


def _read_tail_lines(rel_path: str, n: int) -> Dict[str, Any]:
    root = get_tang_gov_root()
    full = f"{root}/{rel_path}".replace("\\", "/")
    try:
        with open(full, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as exc:
        return {"ok": False, "path": rel_path, "message": str(exc), "lines": []}
    tail = lines[-n:] if n > 0 else lines
    return {
        "ok": True,
        "path": rel_path,
        "line_count": len(tail),
        "text": "".join(tail),
    }


def _war_headline() -> Dict[str, Any]:
    m = load_master_map()
    ws = m.get("war_status") or {}
    return {
        "headline": ws.get("headline"),
        "as_of": ws.get("as_of"),
        "constitution_version": ws.get("constitution_version"),
        "map_version": m.get("version"),
    }


def _dedupe_read_plan(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    out: List[Dict[str, Any]] = []
    for item in items:
        key = (str(item.get("path", "")), str(item.get("scope", "")))
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _catalog_to_read(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for rel in entry.get("read_first") or []:
        out.append(
            {
                "tier": 3,
                "path": str(rel),
                "scope": "full",
                "reason": entry.get("summary") or entry.get("id") or "index_catalog",
            }
        )
    for item in entry.get("read") or []:
        if isinstance(item, dict):
            out.append(dict(item))
    path = entry.get("path")
    if path and not any(r.get("path") == path for r in out):
        out.append(
            {
                "tier": 3,
                "path": str(path),
                "scope": "full",
                "reason": entry.get("summary") or entry.get("id") or "index_catalog",
            }
        )
    return out


def build_boot_context(
    *,
    task_type: Optional[str] = None,
    text: Optional[str] = None,
    progress_tail_lines: int = 80,
    mode: str = "full",
    ticket_id: Optional[str] = None,
    ticket_state: Optional[str] = None,
    role: Optional[str] = None,
) -> Dict[str, Any]:
    """
    三層接戰 bootstrap：路由 + 讀檔計畫 + Progress 末段 + 戰情 headline。
    Tier 0（AGENTS + engineering-contract.mdc）由 Cursor 自動載入，不在此列。

    mode:
      - full（預設）：既有三層 read_plan
      - light（續棒）：只讀票 state + multi_chat_roles 對應角色小節
    """
    if not task_type and not text and mode != "light":
        return {
            "ok": False,
            "boot_schema_version": BOOT_SCHEMA_VERSION,
            "message": "Provide --text and/or --type（light 模式可僅 --ticket-id／--ticket-state）",
        }

    mode_norm = (mode or "full").strip().lower()
    if mode_norm in ("light", "lite", "relay", "續棒"):
        mode_norm = "light"
    else:
        mode_norm = "full"

    if mode_norm == "light":
        return _build_light_boot_context(
            task_type=task_type,
            text=text,
            ticket_id=ticket_id,
            ticket_state=ticket_state,
            role=role,
        )

    route = route_task(task_type=task_type, description=text)
    route = enrich_route_with_runners(route)

    combined = " ".join(p for p in [text or "", task_type or ""] if p).strip()
    catalog_hits = _match_catalog(combined) if combined else []

    hint = TASK_TYPE_HINTS.get(str(route.get("task_type") or ""), {})
    tier4 = bool(hint.get("tier4"))
    tier_label = str(hint.get("tier_label") or ("4" if tier4 else "2+3"))

    read_plan: List[Dict[str, Any]] = []
    if tier4:
        read_plan.extend(TIER4_DOCS)
    else:
        read_plan.extend(TIER2_BASE)

    read_plan.extend(hint.get("extra_read") or [])

    workflow_sections: List[str] = []
    if hint.get("workflow_index_section"):
        workflow_sections.append(str(hint["workflow_index_section"]))

    for hit in catalog_hits:
        read_plan.extend(_catalog_to_read(hit))
        sec = hit.get("workflow_index_section")
        if sec:
            workflow_sections.append(str(sec))

    if route.get("cabin") == "gov_core_system" and not route.get("blocked"):
        read_plan.append(
            {
                "tier": 3,
                "path": "04_Workflows/runbooks/GOV_CORE_OPERATING_MAP_v0.1.md",
                "scope": "暗部工作目錄",
                "reason": "cabin=gov_core_system",
            }
        )

    for key, rel in (route.get("runner_paths") or {}).items():
        if rel and rel.endswith(".md"):
            read_plan.append(
                {
                    "tier": 3,
                    "path": rel.replace("\\", "/"),
                    "scope": "full",
                    "reason": f"runner:{key}",
                }
            )

    read_plan = _dedupe_read_plan(read_plan)

    skip = list(SKIP_DEFAULT)
    if route.get("blocked"):
        skip.append("暗部 runbook / 施工（DarkOps blocked；僅回報 block_reason）")

    progress_tail = _read_tail_lines(
        "04_Workflows/00_Agent_Work_Progress.md",
        progress_tail_lines,
    )

    wf_unique = sorted(set(workflow_sections))
    wf_hint = None
    if wf_unique:
        wf_hint = {
            "path": "04_Workflows/WORKFLOW_INDEX.md",
            "sections": [f"§1.{s.lstrip('1.')}" if not str(s).startswith("§") else str(s) for s in wf_unique],
            "scope": "僅所列 §1.x 節，禁止讀全文",
        }

    assignable = route.get("assignable")
    ok = route.get("ok") is True

    return {
        "ok": ok,
        "boot_schema_version": BOOT_SCHEMA_VERSION,
        "boot_mode": "full",
        "tier": tier_label,
        "tier0_note": "AGENTS.md + .cursor/rules/engineering-contract.mdc（Cursor 自動載入）",
        "cli_command": "python 04_Workflows/_boot_context.py --text \"<尚書省指令>\" --pretty",
        "route": route,
        "paths": get_cycle_artifact_paths(),
        "read_plan": read_plan,
        "skip": skip,
        "workflow_index_hint": wf_hint,
        "war_status": _war_headline(),
        "progress_tail": progress_tail,
        "assignable": assignable,
        "blocked": route.get("blocked"),
        "block_reason": route.get("block_reason"),
        "message": (
            f"Boot tier {tier_label}: {len(read_plan)} files to read; "
            f"assignable={assignable}; task_type={route.get('task_type')}"
        ),
    }


_LIGHT_ROLE_SCOPES: Dict[str, str] = {
    "orchestrator": "§Orchestrator / Operator (O)",
    "operator": "§Orchestrator / Operator (O)",
    "o": "§Orchestrator / Operator (O)",
    "implementer": "§Implementer (B-*)",
    "b": "§Implementer (B-*)",
    "reviewer": "§Reviewer (C)",
    "c": "§Reviewer (C)",
    "scribe": "§Scribe (D)",
    "d": "§Scribe (D)",
}


def _resolve_ticket_state_path(
    *,
    ticket_id: Optional[str],
    ticket_state: Optional[str],
    text: Optional[str],
) -> Optional[str]:
    if ticket_state:
        p = ticket_state.replace("\\", "/").lstrip("./")
        return p
    tid = (ticket_id or "").strip()
    if not tid and text:
        m = re.search(
            r"(?:票號|ticket[_ ]?id|ticket)\s*[：:=]?\s*`?([A-Za-z0-9][A-Za-z0-9._-]*)`?",
            text,
            re.I,
        )
        if m:
            tid = m.group(1)
        else:
            m2 = re.search(r"\b([A-Z][A-Z0-9]+(?:-[A-Za-z0-9._]+)+)\b", text or "")
            if m2:
                tid = m2.group(1)
    if not tid:
        return None
    if tid.endswith("_state.md"):
        return f"04_Workflows/tickets/{tid}" if "/" not in tid else tid
    return f"04_Workflows/tickets/{tid}_state.md"


def _build_light_boot_context(
    *,
    task_type: Optional[str],
    text: Optional[str],
    ticket_id: Optional[str],
    ticket_state: Optional[str],
    role: Optional[str],
) -> Dict[str, Any]:
    """續棒輕量：只讀票 state + roles 對應小節；仍跑路由以標 assignable。"""
    desc = text or "Multi-Chat 續棒 light boot"
    route = route_task(task_type=task_type or "hq.coordination", description=desc)
    route = enrich_route_with_runners(route)

    state_path = _resolve_ticket_state_path(
        ticket_id=ticket_id, ticket_state=ticket_state, text=text
    )
    role_key = (role or "orchestrator").strip().lower()
    role_scope = _LIGHT_ROLE_SCOPES.get(role_key)
    if not role_scope:
        return {
            "ok": False,
            "boot_schema_version": BOOT_SCHEMA_VERSION,
            "boot_mode": "light",
            "message": (
                f"unknown --role={role!r}; "
                "use orchestrator|implementer|reviewer|scribe（或 O/B/C/D）"
            ),
        }
    if not state_path:
        return {
            "ok": False,
            "boot_schema_version": BOOT_SCHEMA_VERSION,
            "boot_mode": "light",
            "message": "light 模式需要 --ticket-id 或 --ticket-state（或在 --text 含票號）",
        }

    read_plan = [
        {
            "tier": 1,
            "path": state_path,
            "scope": "full",
            "reason": "續棒 SSOT：本票 FRAME／STATE／REPORT",
        },
        {
            "tier": 1,
            "path": ".cursor/rules/multi_chat_roles.mdc",
            "scope": role_scope,
            "reason": f"續棒角色邊界（{role_key}）",
        },
    ]
    skip = list(SKIP_DEFAULT) + [
        "04_Workflows/HARNESS_CONSTITUTION.md（light：同 session 已讀過則跳過；高風險仍建議 full）",
        "04_Workflows/00_Agent_Work_Progress.md（light：不讀；封存／關票再用 full）",
        "04_Workflows/project_status/master_status.md（light：跳過）",
    ]
    assignable = route.get("assignable")
    ok = route.get("ok") is True
    return {
        "ok": ok,
        "boot_schema_version": BOOT_SCHEMA_VERSION,
        "boot_mode": "light",
        "tier": "light",
        "tier0_note": "AGENTS.md + .cursor/rules/engineering-contract.mdc（Cursor 自動載入）",
        "cli_command": (
            "python 04_Workflows/_boot_context.py --mode light "
            "--ticket-id <TICKET-ID> --role <orchestrator|implementer|reviewer|scribe> --pretty"
        ),
        "route": route,
        "paths": get_cycle_artifact_paths(),
        "read_plan": read_plan,
        "skip": skip,
        "workflow_index_hint": None,
        "war_status": _war_headline(),
        "progress_tail": {
            "ok": True,
            "skipped": True,
            "reason": "boot_mode=light",
            "text": "",
        },
        "ticket_state": state_path,
        "role": role_key,
        "assignable": assignable,
        "blocked": route.get("blocked"),
        "block_reason": route.get("block_reason"),
        "message": (
            f"Boot light: ticket={state_path}; role={role_key}; "
            f"assignable={assignable}; files={len(read_plan)}"
        ),
    }