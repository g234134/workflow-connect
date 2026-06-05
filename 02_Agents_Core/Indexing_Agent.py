# Indexing_Agent.py — 戶部·數據戶籍化執行器
# 對 03_RAG_Database/C2_核心知識庫 之檔案產生統一 metadata_index.json。
# 路徑統一經 gov_paths 解析；嚴禁寫死磁碟路徑。

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from Base_Agent import AgentStatus, Base_Agent  # type: ignore
from gov_paths import (  # type: ignore
    get_tang_gov_root,
    resolve_agent_output_path,
)

INDEX_FILENAME = "metadata_index.json"


def _human_size(n: int) -> str:
    if n < 0:
        return "?"
    units = ("B", "KB", "MB", "GB", "TB")
    x = float(n)
    for u in units:
        if x < 1024 or u == units[-1]:
            return f"{x:.2f} {u}"
        x /= 1024
    return f"{n} B"


class Indexing_Agent:
    """戶部·數據戶籍化：對 C2_核心知識庫掃描、雜湊、抽取頂層結構，輸出 metadata_index.json。"""

    AGENT_NAME = "Indexing_Agent"
    DEPARTMENT = "戶部"

    def __init__(self, *, dest_root: Optional[str] = None) -> None:
        self.dest_root = os.path.abspath(dest_root or get_tang_gov_root())
        self.agent = Base_Agent(
            dest_root=self.dest_root,
            department=self.DEPARTMENT,
            agent_name=self.AGENT_NAME,
        )
        self.c2_dir = resolve_agent_output_path(self.dest_root, "03_RAG_Database", "c2_core")
        self.reports_dir = resolve_agent_output_path(self.dest_root, "06_Exports_Output", "reports")
        os.makedirs(self.reports_dir, exist_ok=True)

    @staticmethod
    def _sha256(path: str, chunk: int = 65536) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for blk in iter(lambda: f.read(chunk), b""):
                h.update(blk)
        return h.hexdigest()

    @staticmethod
    def _inspect_json(path: str) -> Dict[str, Any]:
        rec: Dict[str, Any] = {
            "root_type": None,
            "top_keys": [],
            "items_count": None,
            "preview": "",
        }
        try:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
        except UnicodeDecodeError:
            with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
                try:
                    obj = json.load(f)
                except Exception as e:  # noqa: BLE001
                    rec["root_type"] = "ERROR"
                    rec["error"] = f"{type(e).__name__}: {e}"
                    return rec
        except Exception as e:  # noqa: BLE001
            rec["root_type"] = "ERROR"
            rec["error"] = f"{type(e).__name__}: {e}"
            return rec

        if isinstance(obj, dict):
            rec["root_type"] = "dict"
            rec["top_keys"] = list(obj.keys())[:30]
            rec["items_count"] = len(obj)
        elif isinstance(obj, list):
            rec["root_type"] = "list"
            rec["items_count"] = len(obj)
            if obj and isinstance(obj[0], dict):
                rec["top_keys"] = list(obj[0].keys())[:30]
        else:
            rec["root_type"] = type(obj).__name__

        try:
            s = json.dumps(obj, ensure_ascii=False)
            rec["preview"] = s[:240] + ("..." if len(s) > 240 else "")
        except Exception:  # noqa: BLE001
            rec["preview"] = ""
        return rec

    def _list_target_files(self) -> List[str]:
        files: List[str] = []
        if not os.path.isdir(self.c2_dir):
            return files
        for dp, _, fns in os.walk(self.c2_dir):
            for fn in fns:
                if fn == INDEX_FILENAME:
                    continue
                if fn.lower().endswith(".json"):
                    files.append(os.path.join(dp, fn))
        files.sort()
        return files

    def build_index(self) -> Dict[str, Any]:
        self.agent.set_status(AgentStatus.Running.value, reason="indexing_start")
        self.agent.log_event(event="indexing_start", c2_dir=self.c2_dir)

        files = self._list_target_files()
        records: List[Dict[str, Any]] = []
        root_type_counter: Counter[str] = Counter()
        top_key_counter: Counter[str] = Counter()
        size_total = 0
        error_count = 0

        for fp in files:
            try:
                stat = os.stat(fp)
                size = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
            except OSError as e:
                size = -1
                mtime = ""
                self.agent.log_event(event="indexing_stat_failed", path=fp, error=str(e))
            sha = self._sha256(fp) if size >= 0 else ""
            insp = self._inspect_json(fp)
            rec = {
                "name": os.path.basename(fp),
                "path": fp,
                "size_bytes": size,
                "size_human": _human_size(size),
                "mtime_utc": mtime,
                "sha256": sha,
                "root_type": insp["root_type"],
                "top_keys": insp["top_keys"],
                "items_count": insp["items_count"],
                "preview": insp["preview"],
            }
            if "error" in insp:
                rec["error"] = insp["error"]
                error_count += 1
            records.append(rec)
            if size > 0:
                size_total += size
            root_type_counter[insp["root_type"] or "?"] += 1
            for k in insp["top_keys"]:
                top_key_counter[str(k)] += 1

        index = {
            "schema_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "run_id": self.agent.run_id,
            "department": self.DEPARTMENT,
            "agent_name": self.AGENT_NAME,
            "scan_root": self.c2_dir,
            "file_count": len(files),
            "total_size_bytes": size_total,
            "total_size_human": _human_size(size_total),
            "error_count": error_count,
            "stats": {
                "by_root_type": dict(root_type_counter),
                "top_keys_top20": top_key_counter.most_common(20),
            },
            "records": records,
        }

        canonical_path = os.path.join(self.c2_dir, INDEX_FILENAME)
        backup_path = os.path.join(self.reports_dir, f"metadata_index_{self.agent.run_id}.json")
        for p in (canonical_path, backup_path):
            with open(p, "w", encoding="utf-8") as f:
                json.dump(index, f, ensure_ascii=False, indent=2)

        self.agent.log_event(
            event="indexing_done",
            file_count=len(files),
            total_size_bytes=size_total,
            error_count=error_count,
            canonical_path=canonical_path,
            backup_path=backup_path,
        )
        self.agent.set_status(AgentStatus.Success.value, reason="indexing_complete")
        return {
            "canonical_path": canonical_path,
            "backup_path": backup_path,
            "file_count": len(files),
            "total_size_bytes": size_total,
            "stats": index["stats"],
            "run_id": self.agent.run_id,
            "error_count": error_count,
        }


def main() -> int:
    out = Indexing_Agent().build_index()
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
