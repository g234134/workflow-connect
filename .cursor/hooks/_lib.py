"""Shared helpers for B Hooks v0.1 (read-only config, fail-open)."""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
LIFECYCLE_CONFIG_PATH = HOOKS_DIR / "lifecycle_config.json"
SCOPE_LEDGER_SCHEMA = "scope-ledger-v0.1"
HOOK_VERSION = "b-hooks-v0.1"

_RUN_QUEUE_CACHE: Optional[Set[str]] = None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def local_date_iso() -> str:
    return datetime.now().date().isoformat()


def read_stdin_json() -> Dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def load_lifecycle_config() -> Dict[str, Any]:
    with open(LIFECYCLE_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_repo_root(payload: Dict[str, Any]) -> Path:
    roots = payload.get("workspace_roots") or []
    for root in roots:
        if not root:
            continue
        candidate = Path(str(root)).resolve()
        if (candidate / ".cursor" / "hooks" / "lifecycle_config.json").is_file():
            return candidate
    return REPO_ROOT.resolve()


def repo_relative_path(abs_path: str, repo_root: Path) -> str:
    try:
        rel = Path(abs_path).resolve().relative_to(repo_root.resolve())
        return rel.as_posix()
    except ValueError:
        return Path(abs_path).name


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    fd, tmp_name = tempfile.mkstemp(prefix=".hook_tmp_", suffix=".json", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except OSError:
                pass


def read_json_file(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def config_path(cfg: Dict[str, Any], key: str, default: str) -> Path:
    return REPO_ROOT / str(cfg.get(key, default))


def compile_patterns(patterns: List[str]) -> List[re.Pattern[str]]:
    compiled: List[re.Pattern[str]] = []
    for pattern in patterns:
        try:
            compiled.append(re.compile(pattern, re.IGNORECASE))
        except re.error:
            continue
    return compiled


def path_matches_any(rel_path: str, patterns: List[re.Pattern[str]]) -> bool:
    normalized = rel_path.replace("\\", "/")
    return any(p.search(normalized) for p in patterns)


def parse_run_queue_ids(cfg: Dict[str, Any]) -> Set[str]:
    global _RUN_QUEUE_CACHE
    if _RUN_QUEUE_CACHE is not None:
        return _RUN_QUEUE_CACHE

    ids: Set[str] = set()
    for rel in cfg.get("run_queue_paths") or []:
        queue_path = REPO_ROOT / str(rel)
        if not queue_path.is_file():
            continue
        try:
            text = queue_path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 2:
                continue
            cell_id = cells[0]
            if cell_id in ("ID", "----", "---") or not cell_id or cell_id.startswith("-"):
                continue
            if re.match(r"^[A-Z0-9][A-Z0-9'\-]*$", cell_id):
                ids.add(cell_id)

    _RUN_QUEUE_CACHE = ids
    return ids


def infer_ticket_id(prompt: str, cfg: Dict[str, Any]) -> Tuple[Optional[str], str]:
    text = prompt or ""
    patterns = cfg.get("ticket_id_patterns") or [
        r"TEST-SUB-[0-9]{3}",
        r"HQ-[A-Z0-9-]+",
        r"[A-Z]+[-']?[0-9]+",
    ]

    # Priority 1: TEST-SUB-*
    for pattern in patterns:
        if "TEST-SUB" not in pattern:
            continue
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(0).upper(), "prompt"

    # Priority 2: HQ-*
    for pattern in patterns:
        if "HQ-" not in pattern:
            continue
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(0).upper(), "prompt"

    # Priority 3: run_queue IDs mentioned in prompt
    run_ids = parse_run_queue_ids(cfg)
    for ticket_id in sorted(run_ids, key=len, reverse=True):
        if re.search(rf"\b{re.escape(ticket_id)}\b", text):
            return ticket_id, "run_queue"

    # Priority 4: any remaining configured pattern
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            token = m.group(0)
            if token in run_ids:
                return token, "run_queue"
            return token.upper() if token.upper().startswith("HQ-") else token, "prompt"

    return None, "unknown"


def ticket_is_eligible(ticket_id: Optional[str], cfg: Dict[str, Any]) -> bool:
    if not ticket_id:
        return False
    prefixes = cfg.get("eligible_ticket_prefixes") or ["TEST-SUB-"]
    for prefix in prefixes:
        if ticket_id.upper().startswith(str(prefix).upper()):
            return True
    return ticket_id in parse_run_queue_ids(cfg)


def empty_scope_ledger() -> Dict[str, Any]:
    return {
        "schema_version": SCOPE_LEDGER_SCHEMA,
        "updated_at": utc_now_iso(),
        "current_conversation_id": None,
        "sessions": {},
        "by_ticket": {},
    }


def load_scope_ledger(cfg: Dict[str, Any]) -> Dict[str, Any]:
    path = config_path(cfg, "scope_ledger_path", ".cursor/scope_ledger.json")
    data = read_json_file(path)
    if not data:
        return empty_scope_ledger()
    data.setdefault("schema_version", SCOPE_LEDGER_SCHEMA)
    data.setdefault("sessions", {})
    data.setdefault("by_ticket", {})
    return data


def save_scope_ledger(cfg: Dict[str, Any], ledger: Dict[str, Any]) -> None:
    path = config_path(cfg, "scope_ledger_path", ".cursor/scope_ledger.json")
    ledger["updated_at"] = utc_now_iso()
    atomic_write_json(path, ledger)


def get_session_context(cfg: Dict[str, Any]) -> Dict[str, Any]:
    path = config_path(cfg, "session_context_path", ".cursor/hooks_state/session_context.json")
    return read_json_file(path) or {}


def save_session_context(cfg: Dict[str, Any], context: Dict[str, Any]) -> None:
    path = config_path(cfg, "session_context_path", ".cursor/hooks_state/session_context.json")
    atomic_write_json(path, context)


def merge_file_change(
    session: Dict[str, Any],
    rel_path: str,
    *,
    skipped: bool,
    hook_name: str,
    now: str,
) -> None:
    files = session.setdefault("files_changed", [])
    for entry in files:
        if entry.get("path") == rel_path:
            entry["last_seen_at"] = now
            entry["edit_count"] = int(entry.get("edit_count") or 0) + 1
            entry["source_hook"] = hook_name
            entry["skipped"] = skipped
            return
    files.append(
        {
            "path": rel_path,
            "first_seen_at": now,
            "last_seen_at": now,
            "edit_count": 1,
            "source_hook": hook_name,
            "skipped": skipped,
        }
    )


def rebuild_by_ticket(ledger: Dict[str, Any]) -> None:
    by_ticket: Dict[str, Any] = {}
    for conv_id, session in (ledger.get("sessions") or {}).items():
        ticket_id = session.get("ticket_id")
        if not ticket_id:
            continue
        paths = sorted(
            {
                e.get("path")
                for e in (session.get("files_changed") or [])
                if e.get("path") and not e.get("skipped")
            }
        )
        by_ticket[ticket_id] = {
            "conversation_id": conv_id,
            "files": paths,
        }
    ledger["by_ticket"] = by_ticket


def load_subagent_artifact(cfg: Dict[str, Any], ticket_id: str, name: str) -> Optional[Dict[str, Any]]:
    base = config_path(cfg, "subagent_artifact_dir", ".cursor/hooks_state/subagent_out")
    path = base / ticket_id / f"{name}.json"
    return read_json_file(path)


def build_executed_list(
    ledger_files: List[str],
    implementation: Optional[Dict[str, Any]],
) -> List[str]:
    executed: List[str] = []
    for path in ledger_files:
        executed.append(f"edit: {path}")
    if implementation:
        for path in implementation.get("files_changed") or []:
            token = f"edit: {path}"
            if token not in executed:
                executed.append(token)
        for path in implementation.get("files_created") or []:
            token = f"create: {path}"
            if token not in executed:
                executed.append(token)
        for cmd in implementation.get("commands_run") or []:
            if isinstance(cmd, dict) and cmd.get("command"):
                executed.append(f"command: {cmd['command']}")
    return executed or ["（hook 未記錄改動）"]


def build_results_summary(
    implementation: Optional[Dict[str, Any]],
    checker: Optional[Dict[str, Any]],
) -> str:
    parts: List[str] = []
    if implementation:
        parts.append(f"implementation.ok={implementation.get('ok')}")
        if implementation.get("message"):
            parts.append(str(implementation.get("message")))
    if checker:
        parts.append(f"checker.verdict={checker.get('verdict')}")
        parts.append(f"checker.accepted={checker.get('accepted')}")
    return "; ".join(parts) if parts else "hook merge only; no subagent artifacts"


def build_blockers(
    implementation: Optional[Dict[str, Any]],
    checker: Optional[Dict[str, Any]],
) -> str:
    blockers: List[str] = []
    if implementation and implementation.get("blocked"):
        reason = implementation.get("block_reason") or "implementation blocked"
        blockers.append(str(reason))
    if checker:
        for gap in checker.get("gaps") or []:
            blockers.append(f"gap: {gap}")
        for risk in checker.get("risks") or []:
            blockers.append(f"risk: {risk}")
    return "; ".join(blockers) if blockers else "無"


def build_next_steps(
    implementation: Optional[Dict[str, Any]],
    checker: Optional[Dict[str, Any]],
) -> List[str]:
    steps: List[str] = ["人工 review 戰報草稿"]
    if checker and checker.get("follow_up_tickets"):
        steps.extend(str(x) for x in checker.get("follow_up_tickets") or [])
    elif implementation:
        deferred = implementation.get("deferred") or []
        if deferred:
            steps.extend(f"deferred: {x}" for x in deferred)
        else:
            steps.append("交 checker-reviewer 或 validate-report")
    else:
        steps.append("python 04_Workflows/_ops_cycle.py validate-report --json .cursor/hooks_state/latest_battle_report_draft.json")
    return steps


def build_battle_report_draft(
    *,
    cfg: Dict[str, Any],
    ticket_id: str,
    conversation_id: str,
    stop_status: str,
    ledger_files: List[str],
    implementation: Optional[Dict[str, Any]],
    checker: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    default = cfg.get("default_battle_report") or {}
    checker_draft = (checker or {}).get("battle_report_json_draft") or {}
    if not isinstance(checker_draft, dict):
        checker_draft = {}

    draft: Dict[str, Any] = {
        "ticket_id": ticket_id,
        "role": default.get("role") or "Cursor Agent（hook 草稿，待人工定稿）",
        "status": "draft",
        "date_local": local_date_iso(),
        "executed": build_executed_list(ledger_files, implementation),
        "results": build_results_summary(implementation, checker),
        "blockers": build_blockers(implementation, checker),
        "next_steps": build_next_steps(implementation, checker),
        "metrics": {
            "hook_version": HOOK_VERSION,
            "conversation_id": conversation_id,
            "stop_status": stop_status,
            "files_changed_count": len(ledger_files),
            "scope_ledger_path": cfg.get("scope_ledger_path", ".cursor/scope_ledger.json"),
            "implementation_ok": (implementation or {}).get("ok"),
            "checker_verdict": (checker or {}).get("verdict"),
        },
        "forbidden_zone_note": "hook 未觸及禁區路徑；執行期產物見 .cursor/hooks_state/",
    }

    for key, value in checker_draft.items():
        if key in draft and isinstance(draft[key], list) and isinstance(value, list):
            merged = list(draft[key])
            for item in value:
                if item not in merged:
                    merged.append(item)
            draft[key] = merged
        elif value is not None:
            draft[key] = value

    draft["ticket_id"] = ticket_id
    draft["status"] = "draft"
    return draft


def write_battle_report_drafts(cfg: Dict[str, Any], ticket_id: str, conversation_id: str, draft: Dict[str, Any]) -> None:
    draft_dir = config_path(cfg, "battle_report_draft_dir", ".cursor/hooks_state/battle_report_drafts")
    ensure_dir(draft_dir)
    safe_ticket = re.sub(r"[^\w\-]+", "_", ticket_id)
    safe_conv = re.sub(r"[^\w\-]+", "_", conversation_id or "unknown")
    per_session = draft_dir / f"{safe_ticket}__{safe_conv}.json"
    latest = config_path(cfg, "latest_battle_report_draft", ".cursor/hooks_state/latest_battle_report_draft.json")
    atomic_write_json(per_session, draft)
    atomic_write_json(latest, draft)
