# Liquidation_Agent.py — 兵部·數據清算執行器
# 對刑部 quarantine 之 .json 檔案進行讀取、解析、分類；
# 嚴格守則：dry_run=True（預設）僅讀取與寫報告，禁止任何物理位移。

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from Base_Agent import AgentStatus, Base_Agent  # type: ignore
from gov_paths import (  # type: ignore
    get_department_under,
    get_tang_gov_root,
    resolve_agent_output_path,
)


# 檔名啟發式：被視為「垃圾日誌／設定快照」的命名特徵（命中即歸檔）
JUNK_NAME_PATTERNS: List[str] = [
    r"queue.*\.json$",
    r".*log.*\.json$",
    r".*cache.*\.json$",
    r".*state.*\.json$",
    r".*config.*\.json$",
    r".*configuration.*\.json$",
    r".*settings.*\.json$",
    r".*manifest.*\.json$",
    r".*supportstate.*\.json$",
    r".*recommendations.*\.json$",
    r".*whitelist.*\.json$",
    r".*ecsconfig.*\.json$",
    r".*updatering.*\.json$",
    r".*presignin.*\.json$",
    r".*dashboard\d*\[?\d*\]?\.json$",
    r".*headlines.*\.json$",
    r".*shim.*\.json$",
    r".*gallerysettings.*\.json$",
    r".*quietmode.*\.json$",
    r".*batteryboost.*\.json$",
    r".*account.*\.json$",
    r".*languagepacks.*\.json$",
    r".*version_cache.*\.json$",
    r"cp\d+\.json$",
    r"big5.*\.json$",
    r"shiftjis\.json$",
    r"eucjp\.json$",
    r"gbk-added\.json$",
    r"gb18030.*\.json$",
    r"labels-to-names\.json$",
    r"supported-names\.json$",
    r"mappingTable\.json$",
    r"decode\.json$",
    r"entities\.json$",
    r"legacy\.json$",
    r"xml\.json$",
    r"types\.json$",
    r"tslint\.json$",
    r"\.sync-manifest\.json$",
    r"release-please-config\.json$",
    r"annotations\.json$",
    r"descriptor\.json$",
    r"http\.json$",
    r"api\.json$",
    r"rules\.json$",
    r"mothersday.*\.json$",
]

# 頂層鍵啟發式：命中視為「重要資料」（待歸入 C2 核心知識庫）
IMPORTANT_TOP_KEYS = {
    "schema",
    "$schema",
    "data",
    "items",
    "records",
    "documents",
    "entries",
    "knowledge",
    "facts",
    "metadata",
    "dataset",
    "corpus",
    "specs",
    "spec",
    "openapi",
    "swagger",
}

# 重要檔名提示（即使結構不明，命中也提升為重要）
IMPORTANT_NAME_HINTS = [
    r".*knowledge.*\.json$",
    r".*dataset.*\.json$",
    r".*openapi.*\.json$",
    r".*swagger.*\.json$",
    r".*schema.*\.json$",
]


class Liquidation_Agent:
    """兵部·清算執行器：對 quarantine 內 .json 進行 dry-run 分類；簽押後方可執行物理位移。"""

    AGENT_NAME = "Liquidation_Agent"
    DEPARTMENT = "兵部"

    def __init__(self, *, dest_root: Optional[str] = None, dry_run: bool = True) -> None:
        self.dest_root = os.path.abspath(dest_root or get_tang_gov_root())
        self.dry_run = bool(dry_run)
        self.agent = Base_Agent(
            dest_root=self.dest_root,
            department=self.DEPARTMENT,
            agent_name=self.AGENT_NAME,
        )
        self.quarantine_dir = os.path.join(
            get_department_under(self.dest_root, "05_Temp_Cache"),
            "quarantine",
        )
        # 目的地：依 Master_Map v2.1 解析（不在 dry-run 階段建立）
        self.archive_dir = resolve_agent_output_path(self.dest_root, "06_Exports_Output", "archive")
        self.c2_core_dir = resolve_agent_output_path(self.dest_root, "03_RAG_Database", "c2_core")
        self.reports_dir = resolve_agent_output_path(self.dest_root, "06_Exports_Output", "reports")
        os.makedirs(self.reports_dir, exist_ok=True)

    @staticmethod
    def _name_match(name: str, patterns: List[str]) -> Optional[str]:
        n = name.lower()
        for pat in patterns:
            if re.search(pat, n, re.IGNORECASE):
                return pat
        return None

    def classify_file(self, path: str) -> Dict[str, Any]:
        rec: Dict[str, Any] = {
            "path": path,
            "name": os.path.basename(path),
            "size_bytes": 0,
            "ok_json": False,
            "format_error": None,
            "category": "unknown",
            "reason": "",
            "top_keys": [],
        }
        try:
            rec["size_bytes"] = os.path.getsize(path)
        except OSError as e:
            rec["format_error"] = f"stat_failed: {e}"

        try:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            rec["ok_json"] = True
            if isinstance(obj, dict):
                rec["top_keys"] = list(obj.keys())[:20]
            elif isinstance(obj, list):
                rec["top_keys"] = ["[list]"]
            else:
                rec["top_keys"] = [f"[{type(obj).__name__}]"]
        except json.JSONDecodeError as e:
            rec["format_error"] = f"json_decode: {e.msg} (line {e.lineno} col {e.colno})"
        except UnicodeDecodeError as e:
            rec["format_error"] = f"unicode_decode: {e}"
        except OSError as e:
            rec["format_error"] = f"read_failed: {e}"
        except Exception as e:  # noqa: BLE001
            rec["format_error"] = f"unknown: {type(e).__name__}: {e}"

        if rec["format_error"]:
            rec["category"] = "format_error"
            rec["reason"] = rec["format_error"]
            return rec

        name = rec["name"]
        important_pat = self._name_match(name, IMPORTANT_NAME_HINTS)
        if important_pat:
            rec["category"] = "important_data"
            rec["reason"] = f"name_hint:{important_pat}"
            return rec

        junk_pat = self._name_match(name, JUNK_NAME_PATTERNS)
        if junk_pat:
            rec["category"] = "junk_log"
            rec["reason"] = f"name_pattern:{junk_pat}"
            return rec

        if rec["top_keys"] and rec["top_keys"][0] not in ("[list]",):
            keys_l = {str(k).lower() for k in rec["top_keys"]}
            if keys_l & {k.lower() for k in IMPORTANT_TOP_KEYS}:
                rec["category"] = "important_data"
                rec["reason"] = "top_keys_match_important"
                return rec

        rec["category"] = "junk_log"
        rec["reason"] = "default_classification"
        return rec

    def _list_json_files(self) -> List[str]:
        files: List[str] = []
        if not os.path.isdir(self.quarantine_dir):
            return files
        for dp, _, fns in os.walk(self.quarantine_dir):
            for fn in fns:
                if fn.lower().endswith(".json"):
                    files.append(os.path.join(dp, fn))
        files.sort()
        return files

    def scan_quarantine_json(self) -> Dict[str, Any]:
        """Dry-run 掃描：解析所有 .json，產出分類報告；不做任何位移。"""
        self.agent.set_status(AgentStatus.Running.value, reason="liquidation_scan_start")
        self.agent.log_event(
            event="liquidation_scan_start",
            quarantine=self.quarantine_dir,
            dry_run=self.dry_run,
        )

        files = self._list_json_files()
        records: List[Dict[str, Any]] = []
        counters = {"format_error": 0, "junk_log": 0, "important_data": 0, "unknown": 0}
        size_by_cat = {"format_error": 0, "junk_log": 0, "important_data": 0, "unknown": 0}
        total_size = 0

        for fp in files:
            r = self.classify_file(fp)
            records.append(r)
            sz = int(r.get("size_bytes") or 0)
            total_size += sz
            cat = r["category"]
            counters[cat] = counters.get(cat, 0) + 1
            size_by_cat[cat] = size_by_cat.get(cat, 0) + sz
            if cat == "format_error":
                self.agent.log_event(
                    event="json_format_warning",
                    path=fp,
                    error=r["format_error"],
                )

        report = {
            "run_id": self.agent.run_id,
            "dry_run": self.dry_run,
            "scan_root": self.quarantine_dir,
            "scanned_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "file_count": len(files),
            "total_size_bytes": total_size,
            "counters": counters,
            "size_by_category_bytes": size_by_cat,
            "destinations": {
                "junk_log": self.archive_dir,
                "important_data": self.c2_core_dir,
            },
            "records": records,
        }

        report_path = os.path.join(self.reports_dir, f"liquidation_preview_{self.agent.run_id}.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        self.agent.log_event(
            event="liquidation_preview_written",
            path=report_path,
            file_count=len(files),
            **counters,
        )

        if self.dry_run:
            self.agent.set_status(AgentStatus.Success.value, reason="liquidation_dry_run_done")
        else:
            # 物理位移階段：須由尚書省簽押後另以 execute() 觸發
            self.agent.log_event(event="liquidation_execution_blocked", reason="not_yet_signed_off")
            self.agent.set_status(AgentStatus.Manual.value, reason="liquidation_awaiting_signature")

        return {"report_path": report_path, "report": report}

    def execute_signed(self, *, signed_token: Optional[str] = None) -> Dict[str, Any]:
        """簽押後物理位移：未提供 signed_token 直接拒絕，避免誤觸。
        路由：
          junk_log       -> 06_Exports_Output/Archive/
          format_error   -> 06_Exports_Output/Archive/format_error/   （事證封存）
          important_data -> 03_RAG_Database/C2_核心知識庫/
        同名檔案以 __dupNNN 後綴避讓，禁止覆蓋。
        """
        if not signed_token:
            self.agent.log_event(event="liquidation_execute_refused", reason="missing_signed_token")
            self.agent.set_status(AgentStatus.Manual.value, reason="liquidation_no_signature")
            return {"ok": False, "reason": "missing_signed_token"}

        self.agent.set_status(AgentStatus.Running.value, reason="liquidation_execute_start")
        self.agent.log_event(event="liquidation_execute_start", signed_token=signed_token)

        format_error_dir = os.path.join(self.archive_dir, "format_error")
        os.makedirs(self.archive_dir, exist_ok=True)
        os.makedirs(self.c2_core_dir, exist_ok=True)
        os.makedirs(format_error_dir, exist_ok=True)

        files = self._list_json_files()
        moved = {"junk_log": 0, "important_data": 0, "format_error": 0}
        errors = 0
        for fp in files:
            r = self.classify_file(fp)
            cat = r["category"]
            if cat == "junk_log":
                dest_dir = self.archive_dir
            elif cat == "important_data":
                dest_dir = self.c2_core_dir
            elif cat == "format_error":
                dest_dir = format_error_dir
            else:
                continue
            try:
                dest = os.path.join(dest_dir, os.path.basename(fp))
                if os.path.exists(dest):
                    base, ext = os.path.splitext(dest)
                    n = 1
                    while os.path.exists(f"{base}__dup{n:03d}{ext}"):
                        n += 1
                    dest = f"{base}__dup{n:03d}{ext}"
                shutil.move(fp, dest)
                moved[cat] = moved.get(cat, 0) + 1
                self.agent.log_event(event="liquidation_moved", src=fp, dst=dest, category=cat)
            except OSError as e:
                errors += 1
                self.agent.log_event(
                    event="liquidation_move_failed",
                    status=AgentStatus.Failed.value,
                    src=fp,
                    error=str(e),
                )
        self.agent.set_status(
            AgentStatus.Success.value if errors == 0 else AgentStatus.Manual.value,
            reason=f"liquidation_execute_done errors={errors}",
        )
        return {"ok": errors == 0, "moved": moved, "errors": errors, "signed_token": signed_token}


def dry_run(dest_root: Optional[str] = None) -> Dict[str, Any]:
    return Liquidation_Agent(dest_root=dest_root, dry_run=True).scan_quarantine_json()


def execute(signed_token: str, dest_root: Optional[str] = None) -> Dict[str, Any]:
    """簽押後實搬：不接 dry_run 模式，必須帶 signed_token。"""
    return Liquidation_Agent(dest_root=dest_root, dry_run=False).execute_signed(signed_token=signed_token)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Liquidation_Agent CLI")
    parser.add_argument("--execute", action="store_true", help="執行物理搬移（須提供 --signed-token）")
    parser.add_argument("--signed-token", default="", help="尚書省簽押 token")
    args = parser.parse_args()

    if args.execute:
        if not args.signed_token:
            print(json.dumps({"ok": False, "reason": "missing_signed_token"}, ensure_ascii=False))
            raise SystemExit(2)
        out = execute(signed_token=args.signed_token)
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        out = dry_run()
        summary = {
            "run_id": out["report"]["run_id"],
            "file_count": out["report"]["file_count"],
            "counters": out["report"]["counters"],
            "report_path": out["report_path"],
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
