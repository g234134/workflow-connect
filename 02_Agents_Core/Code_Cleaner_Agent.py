# Code_Cleaner_Agent.py — 兵部·舊代碼抽樣清剿器
# 目標：從六部根目錄遞迴枚舉「源碼／文本」候選檔，隨機抽樣 N 件，
# 偵測類型 → 解碼 → 摘要 → 標準化 JSON → 入 05_Temp_Cache/cleaned_sample。
# 嚴格守則：不修改原檔；僅讀取與外送。

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from Base_Agent import AgentStatus, Base_Agent  # type: ignore
from gov_paths import (  # type: ignore
    get_tang_gov_root,
    resolve_agent_output_path,
)


# 接受的源碼／文本副檔名 → original_type 映射
EXT_TYPE: Dict[str, str] = {
    ".py": "python", ".pyi": "python_stub",
    ".php": "php", ".phtml": "php",
    ".sql": "sql",
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".jsx": "javascript_react", ".tsx": "typescript_react",
    ".ts": "typescript", ".d.ts": "typescript_decl",
    ".vue": "vue",
    ".html": "html", ".htm": "html",
    ".css": "css", ".scss": "scss", ".less": "less",
    ".json": "json", ".jsonc": "jsonc", ".json5": "json5",
    ".yaml": "yaml", ".yml": "yaml",
    ".toml": "toml", ".ini": "ini", ".cfg": "ini",
    ".md": "markdown", ".rst": "rst", ".txt": "text",
    ".csv": "csv", ".tsv": "tsv",
    ".xml": "xml",
    ".sh": "shell", ".bash": "shell", ".zsh": "shell",
    ".ps1": "powershell", ".psm1": "powershell",
    ".bat": "batch", ".cmd": "batch",
    ".c": "c", ".h": "c_header",
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".hpp": "cpp_header",
    ".rs": "rust",
    ".go": "go",
    ".java": "java", ".kt": "kotlin",
    ".rb": "ruby",
    ".pl": "perl",
    ".lua": "lua",
    ".swift": "swift",
    ".dart": "dart",
    ".scala": "scala",
    ".dockerfile": "dockerfile",
}

# 二進位／無意義抽樣副檔名（一律排除）
SKIP_EXT = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".o", ".obj",
    ".jar", ".class", ".zip", ".tar", ".gz", ".7z", ".bz2",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".ico", ".svg",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".mp3", ".wav", ".mp4", ".mov", ".avi",
    ".woff", ".woff2", ".ttf", ".otf",
    ".lock", ".log",  # 大量噪音
}

# 路徑黑名單（不得抽樣自己／日誌／輸出）
PATH_BLACKLIST_DIRS = {
    "C3_Logs", "Snapshots",
    "reports", "Archive",
    "cleaned_sample",
    "__pycache__",
    "node_modules", ".git", ".idea", ".vscode", "dist", "build",
    ".cache", ".pytest_cache", ".mypy_cache",
}


def _detect_type(path: str) -> str:
    name = os.path.basename(path).lower()
    if name == "dockerfile":
        return "dockerfile"
    # 兩段尾綴（.d.ts）
    for double in (".d.ts",):
        if name.endswith(double):
            return EXT_TYPE.get(double, "unknown")
    ext = os.path.splitext(name)[1]
    return EXT_TYPE.get(ext, "unknown")


def _decode(raw: bytes) -> Tuple[Optional[str], Optional[str]]:
    for enc in ("utf-8-sig", "utf-8", "utf-16", "cp950", "big5", "cp936", "gbk", "cp932", "shift_jis", "latin-1"):
        try:
            return raw.decode(enc), enc
        except (UnicodeDecodeError, LookupError):
            continue
    return None, None


def _summary_python(text: str) -> Dict[str, Any]:
    imports = []
    for ln in text.splitlines()[:200]:
        s = ln.strip()
        if s.startswith("import ") or s.startswith("from "):
            imports.append(s[:120])
    classes = re.findall(r"^class\s+([A-Za-z_][\w]*)", text, flags=re.MULTILINE)
    funcs = re.findall(r"^def\s+([A-Za-z_][\w]*)", text, flags=re.MULTILINE)
    return {"imports": imports[:20], "classes": classes[:20], "functions": funcs[:30]}


def _summary_php(text: str) -> Dict[str, Any]:
    has_open = "<?php" in text
    namespaces = re.findall(r"namespace\s+([\w\\\\]+)\s*;", text)
    uses = re.findall(r"^use\s+([\w\\\\]+)\s*;", text, flags=re.MULTILINE)
    classes = re.findall(r"^\s*class\s+([A-Za-z_][\w]*)", text, flags=re.MULTILINE)
    funcs = re.findall(r"function\s+([A-Za-z_][\w]*)\s*\(", text)
    return {
        "has_php_tag": has_open,
        "namespaces": namespaces[:10],
        "uses": uses[:20],
        "classes": classes[:20],
        "functions": funcs[:30],
    }


def _summary_sql(text: str) -> Dict[str, Any]:
    s = text.upper()
    keywords = {
        "SELECT": s.count("SELECT"),
        "INSERT": s.count("INSERT INTO"),
        "UPDATE": s.count("UPDATE "),
        "DELETE": s.count("DELETE FROM"),
        "CREATE_TABLE": s.count("CREATE TABLE"),
        "ALTER": s.count("ALTER "),
        "DROP": s.count("DROP "),
    }
    tables = re.findall(r"(?:FROM|JOIN|UPDATE|INTO|TABLE)\s+`?([\w\.]+)`?", s)
    return {"keywords": keywords, "tables_seen": list(dict.fromkeys(tables))[:20]}


def _summary_json(text: str) -> Dict[str, Any]:
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return {"json_valid": False}
    if isinstance(obj, dict):
        return {"json_valid": True, "root_type": "dict", "top_keys": list(obj.keys())[:20], "items_count": len(obj)}
    if isinstance(obj, list):
        return {"json_valid": True, "root_type": "list", "items_count": len(obj)}
    return {"json_valid": True, "root_type": type(obj).__name__}


def _summary_text_generic(text: str) -> Dict[str, Any]:
    lines = text.splitlines()
    non_empty = [ln for ln in lines if ln.strip()]
    return {
        "line_count": len(lines),
        "non_empty_lines": len(non_empty),
        "char_count": len(text),
        "preview_lines": non_empty[:10],
    }


def _summarize(otype: str, text: str) -> Dict[str, Any]:
    base = _summary_text_generic(text)
    extras: Dict[str, Any] = {}
    if otype == "python" or otype == "python_stub":
        extras = _summary_python(text)
    elif otype == "php":
        extras = _summary_php(text)
    elif otype == "sql":
        extras = _summary_sql(text)
    elif otype in ("json", "jsonc", "json5"):
        extras = _summary_json(text)
    base.update(extras)
    return base


class Code_Cleaner_Agent:
    AGENT_NAME = "Code_Cleaner_Agent"
    DEPARTMENT = "兵部"

    def __init__(self, *, dest_root: Optional[str] = None, sample_size: int = 100, seed: Optional[int] = None) -> None:
        self.dest_root = os.path.abspath(dest_root or get_tang_gov_root())
        self.sample_size = int(sample_size)
        self.rng = random.Random(seed) if seed is not None else random.Random()
        self.agent = Base_Agent(
            dest_root=self.dest_root,
            department=self.DEPARTMENT,
            agent_name=self.AGENT_NAME,
        )
        self.scan_root = self.dest_root
        self.out_dir = resolve_agent_output_path(self.dest_root, "05_Temp_Cache", "cleaned_sample")
        self.reports_dir = resolve_agent_output_path(self.dest_root, "06_Exports_Output", "reports")
        os.makedirs(self.out_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)

    def _eligible(self, fp: str) -> bool:
        # 黑名單目錄
        parts = set(os.path.normpath(fp).split(os.sep))
        if parts & PATH_BLACKLIST_DIRS:
            return False
        ext = os.path.splitext(fp)[1].lower()
        if ext in SKIP_EXT:
            return False
        # 不在白名單副檔名亦排除（避免把純資產／隨機檔抽進來）
        if _detect_type(fp) == "unknown":
            return False
        return True

    def enumerate_candidates(self) -> List[str]:
        cand: List[str] = []
        for dp, dns, fns in os.walk(self.scan_root):
            # 黑名單目錄就地剪枝
            dns[:] = [d for d in dns if d not in PATH_BLACKLIST_DIRS]
            for fn in fns:
                fp = os.path.join(dp, fn)
                if self._eligible(fp):
                    cand.append(fp)
        return cand

    @staticmethod
    def _sha256(path: str, chunk: int = 65536) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for blk in iter(lambda: f.read(chunk), b""):
                h.update(blk)
        return h.hexdigest()

    def _process_one(self, fp: str) -> Dict[str, Any]:
        rec: Dict[str, Any] = {
            "source_path": fp,
            "name": os.path.basename(fp),
            "extension": os.path.splitext(fp)[1].lower(),
            "original_type": _detect_type(fp),
            "size_bytes": -1,
            "encoding": None,
            "sha256": None,
            "content_summary": {},
            "clean_status": "ok",
            "warnings": [],
        }
        try:
            rec["size_bytes"] = os.path.getsize(fp)
        except OSError as e:
            rec["clean_status"] = "failed"
            rec["warnings"].append(f"stat_failed:{e}")
            return rec
        # 跳過超大檔（避免摘要超載）
        if rec["size_bytes"] > 4 * 1024 * 1024:
            rec["clean_status"] = "warning"
            rec["warnings"].append("size_exceeds_4MB_summary_truncated")
        try:
            rec["sha256"] = self._sha256(fp)
        except OSError as e:
            rec["warnings"].append(f"sha256_failed:{e}")
        try:
            with open(fp, "rb") as f:
                raw = f.read(2 * 1024 * 1024)  # 最多讀 2MB 進行摘要
        except OSError as e:
            rec["clean_status"] = "failed"
            rec["warnings"].append(f"read_failed:{e}")
            return rec

        text, enc = _decode(raw)
        rec["encoding"] = enc
        if text is None:
            rec["clean_status"] = "warning"
            rec["warnings"].append("decode_failed_all_codecs")
            rec["content_summary"] = {"hex_head": raw[:32].hex(), "byte_size_read": len(raw)}
            return rec
        try:
            rec["content_summary"] = _summarize(rec["original_type"], text)
        except Exception as e:  # noqa: BLE001
            rec["clean_status"] = "warning"
            rec["warnings"].append(f"summary_error:{type(e).__name__}:{e}")
            rec["content_summary"] = _summary_text_generic(text)
        return rec

    def run(self) -> Dict[str, Any]:
        self.agent.set_status(AgentStatus.Running.value, reason="code_cleaner_start")
        self.agent.log_event(event="code_cleaner_scan_start", scan_root=self.scan_root, sample_size=self.sample_size)

        candidates = self.enumerate_candidates()
        total_pool = len(candidates)
        if total_pool == 0:
            self.agent.set_status(AgentStatus.Manual.value, reason="no_candidates")
            return {"ok": False, "reason": "no_candidates"}

        n = min(self.sample_size, total_pool)
        sampled = self.rng.sample(candidates, n)
        self.agent.log_event(event="code_cleaner_sampled", pool_size=total_pool, sampled=n)

        results: List[Dict[str, Any]] = []
        type_counter: Counter[str] = Counter()
        status_counter: Counter[str] = Counter()
        ok = warn = failed = 0
        for fp in sampled:
            r = self._process_one(fp)
            type_counter[r["original_type"]] += 1
            status_counter[r["clean_status"]] += 1
            if r["clean_status"] == "ok":
                ok += 1
            elif r["clean_status"] == "warning":
                warn += 1
            else:
                failed += 1
            # 寫單一標準化 JSON
            stem = (r["sha256"] or "nohash")[:12]
            base = re.sub(r"[^A-Za-z0-9._-]+", "_", r["name"])[:80]
            out_name = f"sample_{stem}_{base}.json"
            out_path = os.path.join(self.out_dir, out_name)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "schema_version": "1.0",
                        "run_id": self.agent.run_id,
                        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        **r,
                        "stored_path": out_path,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            r["stored_path"] = out_path
            results.append(r)
            self.agent.log_event(
                event="code_cleaner_one_done",
                path=fp,
                original_type=r["original_type"],
                clean_status=r["clean_status"],
                stored=out_path,
            )

        rate = round((ok + warn) / max(1, n), 4)
        report = {
            "schema_version": "1.0",
            "run_id": self.agent.run_id,
            "scan_root": self.scan_root,
            "candidate_pool": total_pool,
            "sampled": n,
            "ok": ok,
            "warning": warn,
            "failed": failed,
            "success_rate": rate,
            "by_type": dict(type_counter),
            "by_status": dict(status_counter),
            "out_dir": self.out_dir,
            "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "samples": [
                {k: v for k, v in r.items() if k not in ("content_summary",)}
                for r in results
            ],
        }
        report_path = os.path.join(
            self.reports_dir,
            f"code_cleaner_report_{self.agent.run_id}.json",
        )
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        report["report_path"] = report_path
        self.agent.log_event(event="code_cleaner_done", **{k: v for k, v in report.items() if k != "samples"})
        self.agent.set_status(AgentStatus.Success.value, reason="code_cleaner_complete")
        return report


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Code_Cleaner_Agent CLI")
    parser.add_argument("--n", type=int, default=100, help="抽樣數量")
    parser.add_argument("--seed", type=int, default=None, help="隨機種子（可重現）")
    args = parser.parse_args()
    out = Code_Cleaner_Agent(sample_size=args.n, seed=args.seed).run()
    summary = {
        "run_id": out.get("run_id"),
        "candidate_pool": out.get("candidate_pool"),
        "sampled": out.get("sampled"),
        "ok": out.get("ok"),
        "warning": out.get("warning"),
        "failed": out.get("failed"),
        "success_rate": out.get("success_rate"),
        "by_type_top": Counter(out.get("by_type", {})).most_common(8),
        "out_dir": out.get("out_dir"),
        "report_path": out.get("report_path"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
