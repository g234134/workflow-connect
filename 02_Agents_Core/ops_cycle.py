# ops_cycle.py — HQ Phase 4 營運週期（戰報／封存／回顧）
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Dict, List, Optional

from gov_paths import get_artifact_path, get_tang_gov_root, load_master_map

_SCHEMA_ARTIFACT_KEY = "ops_cycle_schema"
_PROGRESS_ARTIFACT_KEY = "agent_work_progress"
_REVIEWS_SUBDIR = os.path.join("04_Workflows", "project_status", "reviews")


@lru_cache(maxsize=1)
def load_ops_cycle_schema() -> Dict[str, Any]:
    path = get_artifact_path(_SCHEMA_ARTIFACT_KEY)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "battle_report" not in data or "archive_protocol" not in data:
        raise ValueError("ops_cycle_schema.json: missing battle_report or archive_protocol")
    return data


def invalidate_ops_cycle_cache() -> None:
    load_ops_cycle_schema.cache_clear()


def _artifact_rel_path(schema: Dict[str, Any], logical_key: str) -> Optional[str]:
    arts = schema.get("artifacts") or {}
    candidates: List[str] = [logical_key]
    alias = arts.get(logical_key)
    if alias and str(alias) not in candidates:
        candidates.append(str(alias))
    for key in candidates:
        try:
            return get_artifact_path(key)
        except KeyError:
            continue
    if logical_key == "ops_reviews_dir" or alias == "ops_reviews_dir":
        return _REVIEWS_SUBDIR
    return None


def _resolve_path(rel: str) -> str:
    root = get_tang_gov_root()
    return os.path.normpath(os.path.join(root, rel.replace("/", os.sep)))


def validate_battle_report(data: Dict[str, Any]) -> Dict[str, Any]:
    schema = load_ops_cycle_schema()
    br = schema.get("battle_report") or {}
    required = list(br.get("required_fields") or [])
    optional = set(br.get("optional_fields") or [])
    allowed_status = set(br.get("status_values") or [])

    missing: List[str] = []
    warnings: List[str] = []

    for field in required:
        val = data.get(field)
        if val is None or (isinstance(val, str) and not str(val).strip()):
            missing.append(field)

    status = data.get("status")
    if status is not None and str(status).strip():
        if str(status).strip() not in allowed_status:
            warnings.append(f"status {status!r} not in {sorted(allowed_status)}")
    else:
        warnings.append("status omitted; defaulting to draft on render")

    extra_keys = set(data.keys()) - set(required) - optional
    if extra_keys:
        warnings.append(f"unknown fields (allowed): {sorted(extra_keys)}")

    return {
        "ok": len(missing) == 0,
        "missing_fields": missing,
        "warnings": warnings,
        "ops_cycle_schema_version": schema.get("ops_cycle_schema_version"),
        "ticket": schema.get("ticket"),
    }


def _format_section(title: str, body: Any) -> str:
    if body is None:
        return ""
    if isinstance(body, list):
        lines = [str(x).strip() for x in body if str(x).strip()]
        content = "\n".join(f"- {line}" for line in lines) if lines else "（無）"
    elif isinstance(body, dict):
        content = "```json\n" + json.dumps(body, ensure_ascii=False, indent=2) + "\n```"
    else:
        text = str(body).strip()
        content = text if text else "（無）"
    return f"#### {title}\n\n{content}\n"


def render_battle_report_markdown(data: Dict[str, Any]) -> str:
    schema = load_ops_cycle_schema()
    br = schema.get("battle_report") or {}
    titles = br.get("section_titles") or {}

    ticket = str(data.get("ticket_id", "UNKNOWN")).strip()
    status = str(data.get("status") or "done").strip()
    role = str(data.get("role", "")).strip()
    date_local = str(data.get("date_local") or datetime.now().strftime("%Y-%m-%d"))

    lines = [
        f"## {ticket}（{date_local} · {role}）",
        "",
        f"**任務 ID**：`{ticket}`  ",
        f"**狀態**：**{status}**",
        "",
        "### Work Report",
        "",
    ]

    order = [
        "executed",
        "results",
        "metrics",
        "blockers",
        "next_steps",
        "runbook_delta",
        "standards_delta",
        "forbidden_zone_note",
        "override_note",
    ]
    for key in order:
        if key not in data:
            continue
        title = titles.get(key, key)
        block = _format_section(title, data.get(key))
        if block.strip():
            lines.append(block)

    return "\n".join(lines).rstrip() + "\n"


def append_battle_report(data: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    validation = validate_battle_report(data)
    if not validation.get("ok"):
        return {
            "ok": False,
            "dry_run": dry_run,
            "validation": validation,
            "message": "Battle report validation failed",
        }

    schema = load_ops_cycle_schema()
    rel = _artifact_rel_path(schema, "progress")
    if not rel:
        return {"ok": False, "message": "progress artifact not configured"}

    path = _resolve_path(rel)
    markdown = render_battle_report_markdown(data)
    separator = "\n\n---\n\n"

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "path": path,
            "bytes": len(markdown.encode("utf-8")),
            "preview": markdown[:500],
            "validation": validation,
            "message": "Dry run: report not written",
        }

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        if os.path.getsize(path) > 0:
            f.write(separator)
        f.write(markdown)

    return {
        "ok": True,
        "dry_run": False,
        "path": path,
        "validation": validation,
        "message": f"Appended battle report for {data.get('ticket_id')}",
    }


def _step_defs(schema: Dict[str, Any], mode: str) -> List[Dict[str, Any]]:
    proto = schema.get("archive_protocol") or {}
    step_ids = proto.get("full_steps") if mode == "full" else proto.get("minimal_steps")
    if not step_ids:
        step_ids = proto.get("minimal_steps") or []
    by_id = {s["id"]: s for s in (proto.get("steps") or []) if s.get("id")}
    return [by_id[sid] for sid in step_ids if sid in by_id]


def _check_json_field(rel_path: str, json_path: str) -> str:
    full = _resolve_path(rel_path)
    if not os.path.isfile(full):
        return "fail"
    try:
        with open(full, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return "fail"
    cur: Any = data
    for part in json_path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return "fail"
        cur = cur[part]
    if cur is None or (isinstance(cur, str) and not cur.strip()):
        return "fail"
    return "pass"


def evaluate_archive_step(step: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    check = str(step.get("check", "manual"))
    artifact_key = step.get("artifact_key")
    step_id = str(step.get("id", ""))

    if check == "manual":
        return {
            "id": step_id,
            "title": step.get("title"),
            "status": "manual",
            "message": step.get("description", ""),
        }

    if check == "artifact_exists" and artifact_key:
        rel = _artifact_rel_path(schema, str(artifact_key))
        if not rel:
            return {
                "id": step_id,
                "title": step.get("title"),
                "status": "fail",
                "message": f"Unknown artifact_key: {artifact_key}",
            }
        full = _resolve_path(rel)
        ok = os.path.exists(full)
        return {
            "id": step_id,
            "title": step.get("title"),
            "status": "pass" if ok else "fail",
            "message": full,
        }

    if check == "json_field" and artifact_key:
        rel = _artifact_rel_path(schema, str(artifact_key))
        json_path = str(step.get("json_path", ""))
        if not rel or not json_path:
            return {
                "id": step_id,
                "title": step.get("title"),
                "status": "fail",
                "message": "json_field step misconfigured",
            }
        status = _check_json_field(rel, json_path)
        return {
            "id": step_id,
            "title": step.get("title"),
            "status": status,
            "message": f"{rel} → {json_path}",
        }

    return {
        "id": step_id,
        "title": step.get("title"),
        "status": "manual",
        "message": f"Unhandled check type: {check}",
    }


def get_archive_checklist(mode: str = "full") -> Dict[str, Any]:
    schema = load_ops_cycle_schema()
    steps = _step_defs(schema, mode)
    evaluated = [evaluate_archive_step(s, schema) for s in steps]
    auto = [s for s in evaluated if s["status"] in ("pass", "fail")]
    ok = all(s["status"] != "fail" for s in auto) if auto else True
    return {
        "ok": ok,
        "mode": mode,
        "ops_cycle_schema_version": schema.get("ops_cycle_schema_version"),
        "steps": evaluated,
        "message": f"Archive checklist ({mode}): {len(evaluated)} steps",
    }


def validate_archive(mode: str = "full") -> Dict[str, Any]:
    result = get_archive_checklist(mode)
    manual_count = sum(1 for s in result["steps"] if s["status"] == "manual")
    fail_count = sum(1 for s in result["steps"] if s["status"] == "fail")
    result["manual_count"] = manual_count
    result["fail_count"] = fail_count
    result["ready_for_archive"] = fail_count == 0
    if fail_count:
        result["message"] = f"Archive not ready: {fail_count} automatic check(s) failed"
    elif manual_count:
        result["message"] = f"Automatic checks passed; {manual_count} step(s) require manual confirmation"
    else:
        result["message"] = "All automatic archive checks passed"
    return result


def _slug(text: str) -> str:
    slug = re.sub(r"[^\w\-]+", "_", text.strip(), flags=re.UNICODE)
    return slug.strip("_") or "review"


def render_review_template(
    review_type: str,
    project_id: str,
    ticket: Optional[str] = None,
) -> str:
    schema = load_ops_cycle_schema()
    types = schema.get("review_types") or {}
    if review_type not in types:
        raise ValueError(f"Unknown review_type: {review_type!r}; expected one of {sorted(types)}")

    meta = types[review_type]
    title = meta.get("title", review_type)
    sections = list(meta.get("sections") or [])
    date_local = datetime.now().strftime("%Y-%m-%d")
    ticket_line = f"**票號**：`{ticket}`  \n" if ticket else ""

    lines = [
        f"# {title}",
        "",
        f"**專案**：`{project_id}`  ",
        ticket_line + f"**日期**：{date_local}  ",
        f"**類型**：`{review_type}`",
        "",
        "---",
        "",
    ]
    for sec in sections:
        heading = sec.replace("_", " ").title()
        lines.append(f"## {heading}")
        lines.append("")
        lines.append("（待填）")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_review_template(
    review_type: str,
    project_id: str,
    ticket: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    schema = load_ops_cycle_schema()
    content = render_review_template(review_type, project_id, ticket=ticket)
    rel_dir = _artifact_rel_path(schema, "ops_reviews_dir") or _REVIEWS_SUBDIR
    dir_path = _resolve_path(rel_dir)
    fname = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{_slug(project_id)}_{review_type}.md"
    full = os.path.join(dir_path, fname)

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "path": full,
            "preview": content[:400],
            "message": "Dry run: review not written",
        }

    os.makedirs(dir_path, exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "ok": True,
        "dry_run": False,
        "path": full,
        "review_type": review_type,
        "project_id": project_id,
        "message": f"Created review template: {fname}",
    }


def get_cycle_artifact_paths() -> Dict[str, str]:
    """回傳營運週期相關 artifact 絕對路徑（供副官交接）。"""
    schema = load_ops_cycle_schema()
    out: Dict[str, str] = {}
    for key in schema.get("artifacts") or {}:
        rel = _artifact_rel_path(schema, key)
        if rel:
            out[key] = _resolve_path(rel)
    m = load_master_map()
    out["map_version"] = str(m.get("version", ""))
    return out
