# _destruction_test.py — 毀滅級 JSON 救援壓力測試
# 1) 在 Archive/format_error/ 投入一個語義全毀、缺括號、混雜亂碼的「假 JSON」
# 2) 調用 GroqHybridRecovery_Agent 進行救援；本地策略應失敗→觸發 Groq llama-3.3-70b
# 3) 從 C2_核心知識庫 取回修復後內容，記錄 before/after 對比與是否經 Groq

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_workflows = os.path.dirname(os.path.abspath(__file__))
_agents_core = os.path.normpath(os.path.join(_workflows, "..", "02_Agents_Core"))
for _p in (_agents_core, _workflows):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gov_paths import (  # type: ignore
    get_department_under,
    get_tang_gov_root,
    resolve_agent_output_path,
)
from GroqHybridRecovery_Agent import GroqHybridRecovery_Agent  # type: ignore


DESTRUCTION_FILENAME = "destruction_test.json"


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _make_payload() -> bytes:
    """組一段確保「無法用任何本地策略修通」、卻仍可被 LLM 推得語義的破檔。"""
    parts: List[str] = []
    parts.append("%%%CORRUPTED_MAGIC_HEADER%%%")
    parts.append("亂碼噪音：你好世界@@@!!! €£¥ §¶†‡")
    parts.append("// note: this is supposed to be JSON but somebody fed it through a paper shredder")
    # 故意：沒有開頭的 {，欄位散落，逗號／引號錯亂，陣列沒收尾
    parts.append('   "project": "tang_chariot,')
    parts.append('   "version" 1.2.3   description= production JSON crashed')
    parts.append('   modules : [ "core", "rag", "agents",')
    parts.append('   ; legacy //tail_garbage <<<<>>>>')
    parts.append('   "owner": { "name": 666LAG  username  ZXL95270  ')
    parts.append('   "tags": ["api,"telegram","groq"\\\\\\')
    parts.append('   日誌行: 2026-05-08 18:30  cpu=0.2 mem=32MB')
    parts.append("¿¿¿extra trailing trash¿¿¿")
    text = "\n".join(parts) + "\n"
    # 加入一個非法 BOM-like 前綴 + Latin-1 高位元噪音
    noise = bytes([0xFE, 0xFF, 0x00, 0xA4, 0xC3, 0xAF, 0xC2, 0xBB])
    return noise + text.encode("utf-8")


def _read_text(path: str, max_bytes: int = 32768) -> Dict[str, Any]:
    try:
        with open(path, "rb") as f:
            raw = f.read(max_bytes)
    except OSError as e:
        return {"ok": False, "error": str(e)}
    out = {"ok": True, "size_bytes": len(raw)}
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            out["text"] = raw.decode(enc)
            out["encoding"] = enc
            break
        except UnicodeDecodeError:
            continue
    if "text" not in out:
        out["text"] = raw.hex()
        out["encoding"] = "hex"
    return out


def _scan_log_for_destruction(log_path: str, src_name: str) -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "events": [],
        "via_groq": False,
        "warning_count": 0,
        "groq_reasons": [],
    }
    if not os.path.isfile(log_path):
        return info
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            ev = o.get("event")
            path = o.get("path") or o.get("dst") or o.get("src") or ""
            if src_name in str(path):
                info["events"].append({k: o.get(k) for k in ("event", "path", "dst", "strategy", "encoding", "via_groq", "groq_reason", "size_in", "size_out")})
                if ev == "hybrid_recovered" and o.get("via_groq"):
                    info["via_groq"] = True
                if ev == "json_format_warning":
                    info["warning_count"] += 1
                    if o.get("groq_reason"):
                        info["groq_reasons"].append(o.get("groq_reason"))
    return info


def main() -> int:
    dest_root = get_tang_gov_root()
    archive_dir = resolve_agent_output_path(dest_root, "06_Exports_Output", "archive")
    fed_dir = os.path.join(archive_dir, "format_error")
    c2_dir = resolve_agent_output_path(dest_root, "03_RAG_Database", "c2_core")
    reports_dir = resolve_agent_output_path(dest_root, "06_Exports_Output", "reports")
    os.makedirs(fed_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    # 1) 投入毀滅檔
    payload = _make_payload()
    src_path = os.path.join(fed_dir, DESTRUCTION_FILENAME)
    with open(src_path, "wb") as f:
        f.write(payload)

    before_view = {
        "size_bytes": len(payload),
        "first_120_bytes_hex": payload[:120].hex(),
        "first_400_chars_latin1": payload[:400].decode("latin-1", errors="replace"),
    }

    # 2) 救援
    agent = GroqHybridRecovery_Agent(dest_root=dest_root)
    started = _utc_iso()
    result = agent.run_batch()
    finished = _utc_iso()

    # 3) 檢查日誌與輸出
    c3_logs = get_department_under(dest_root, "03_RAG_Database")
    log_path = os.path.join(c3_logs, "C3_Logs", f"{result['run_id']}.jsonl")
    log_info = _scan_log_for_destruction(log_path, DESTRUCTION_FILENAME)

    # 偵測 C2 是否出現以該名稱為主的新檔（含 __hyb 後綴）
    after_paths: List[str] = []
    if os.path.isdir(c2_dir):
        stem = os.path.splitext(DESTRUCTION_FILENAME)[0]
        for fn in os.listdir(c2_dir):
            if fn.startswith(stem) and fn.endswith(".json") and fn != "metadata_index.json":
                after_paths.append(os.path.join(c2_dir, fn))
    after_paths.sort()
    after_view: Optional[Dict[str, Any]] = None
    if after_paths:
        latest = after_paths[-1]
        rv = _read_text(latest)
        after_view = {"path": latest, **rv}

    success = bool(after_view) and result.get("ok_groq", 0) >= 1
    rec = {
        "schema_version": "1.0",
        "started_at": started,
        "finished_at": finished,
        "src_path": src_path,
        "destination_candidates": after_paths,
        "agent_run_id": result.get("run_id"),
        "agent_summary": result,
        "log_path": log_path,
        "log_match": log_info,
        "before": before_view,
        "after": after_view,
        "verdict": {
            "groq_invoked": log_info.get("via_groq", False),
            "groq_only_path": log_info.get("via_groq", False) and result.get("ok_local", 0) == 0,
            "stored_in_c2": bool(after_view),
            "success": success,
        },
    }
    out_path = os.path.join(reports_dir, f"destruction_test_{result.get('run_id')}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    rec["report_path"] = out_path

    print(json.dumps(rec, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
