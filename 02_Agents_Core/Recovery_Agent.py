# Recovery_Agent.py — 工部·編碼／BOM 修復執行器
# 對 Archive/format_error 內非 0-byte 檔案：嘗試多編碼解碼 → BOM／空白清理 → JSON 解析。
# 修復成功者依 Liquidation_Agent 規則重判分類，移往 C2_核心知識庫 或 Archive/。
# 不可修復者移往 Archive/format_error/unrecoverable/。
# 嚴格守則：未提供 signed_token 直接拒絕；以 UTF-8（無 BOM）重序列化。

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Counter as TCounter, Dict, List, Optional, Tuple

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from Base_Agent import AgentStatus, Base_Agent  # type: ignore
from gov_paths import (  # type: ignore
    get_tang_gov_root,
    resolve_agent_output_path,
)
from Liquidation_Agent import (  # type: ignore
    IMPORTANT_NAME_HINTS,
    IMPORTANT_TOP_KEYS,
    JUNK_NAME_PATTERNS,
)


# 解碼候選（優先序）：Windows ZH-TW 環境通常 cp950 ≈ Big5+MS 擴充
ENCODING_FALLBACKS: List[str] = [
    "utf-8-sig",
    "utf-8",
    "utf-16",
    "utf-16-le",
    "utf-16-be",
    "cp950",
    "big5",
    "cp936",
    "gbk",
    "gb18030",
    "cp932",
    "shift_jis",
    "cp949",
    "euc-kr",
    "latin-1",  # 最後兜底：永遠成功，僅在前述全敗時嘗試
]


def _name_match(name: str, patterns: List[str]) -> Optional[str]:
    n = name.lower()
    for pat in patterns:
        if re.search(pat, n, re.IGNORECASE):
            return pat
    return None


def classify_repaired(name: str, obj: Any) -> Tuple[str, str]:
    """回傳 (category, reason)：important_data / junk_log。"""
    pat = _name_match(name, IMPORTANT_NAME_HINTS)
    if pat:
        return "important_data", f"name_hint:{pat}"
    pat = _name_match(name, JUNK_NAME_PATTERNS)
    if pat:
        return "junk_log", f"name_pattern:{pat}"
    if isinstance(obj, dict):
        keys_l = {str(k).lower() for k in list(obj.keys())[:30]}
        if keys_l & {k.lower() for k in IMPORTANT_TOP_KEYS}:
            return "important_data", "top_keys_match_important"
    return "junk_log", "default_classification"


class Recovery_Agent:
    AGENT_NAME = "Recovery_Agent"
    DEPARTMENT = "工部"

    def __init__(self, *, dest_root: Optional[str] = None, signed_token: str = "") -> None:
        if not signed_token:
            raise ValueError("Recovery_Agent 拒絕無簽押啟動：missing_signed_token")
        self.signed_token = signed_token
        self.dest_root = os.path.abspath(dest_root or get_tang_gov_root())
        self.agent = Base_Agent(
            dest_root=self.dest_root,
            department=self.DEPARTMENT,
            agent_name=self.AGENT_NAME,
        )
        self.archive_dir = resolve_agent_output_path(self.dest_root, "06_Exports_Output", "archive")
        self.format_error_dir = os.path.join(self.archive_dir, "format_error")
        self.unrecoverable_dir = os.path.join(self.format_error_dir, "unrecoverable")
        self.c2_dir = resolve_agent_output_path(self.dest_root, "03_RAG_Database", "c2_core")
        os.makedirs(self.unrecoverable_dir, exist_ok=True)

    @staticmethod
    def _list_nonzero_targets(format_error_dir: str) -> List[str]:
        files: List[str] = []
        if not os.path.isdir(format_error_dir):
            return files
        # 僅掃當層；不遞迴 unrecoverable 子目錄
        for entry in os.listdir(format_error_dir):
            if entry == ".department.txt":
                continue
            fp = os.path.join(format_error_dir, entry)
            if not os.path.isfile(fp):
                continue
            try:
                if os.path.getsize(fp) > 0:
                    files.append(fp)
            except OSError:
                continue
        files.sort()
        return files

    @staticmethod
    def _decode(raw: bytes) -> Tuple[Optional[str], Optional[str]]:
        for enc in ENCODING_FALLBACKS:
            try:
                text = raw.decode(enc)
                return text, enc
            except UnicodeDecodeError:
                continue
            except LookupError:
                continue
        return None, None

    @staticmethod
    def _try_parse(text: str) -> Tuple[Optional[Any], Optional[str]]:
        # 第一輪：原文
        try:
            return json.loads(text), "raw"
        except json.JSONDecodeError:
            pass
        # 第二輪：去 BOM / 去空白
        cleaned = text.lstrip("\ufeff").strip()
        if cleaned != text:
            try:
                return json.loads(cleaned), "stripped"
            except json.JSONDecodeError:
                pass
        # 第三輪：擷取首個 { ... } 或 [ ... ] 片段
        if cleaned:
            for opener, closer in (("{", "}"), ("[", "]")):
                start = cleaned.find(opener)
                end = cleaned.rfind(closer)
                if start != -1 and end > start:
                    candidate = cleaned[start : end + 1]
                    try:
                        return json.loads(candidate), f"substring_{opener}{closer}"
                    except json.JSONDecodeError:
                        continue
        return None, None

    def _unique_dest(self, dest: str) -> str:
        if not os.path.exists(dest):
            return dest
        base, ext = os.path.splitext(dest)
        n = 1
        while os.path.exists(f"{base}__rec{n:03d}{ext}"):
            n += 1
        return f"{base}__rec{n:03d}{ext}"

    def repair_all(self) -> Dict[str, Any]:
        self.agent.set_status(AgentStatus.Running.value, reason="recovery_start")
        files = self._list_nonzero_targets(self.format_error_dir)
        self.agent.log_event(event="recovery_start", target_count=len(files), signed_token=self.signed_token)

        os.makedirs(self.archive_dir, exist_ok=True)
        os.makedirs(self.c2_dir, exist_ok=True)

        encoding_counter: TCounter[str] = Counter()
        parse_strategy_counter: TCounter[str] = Counter()
        destination_counter: TCounter[str] = Counter()
        category_counter: TCounter[str] = Counter()

        repaired = 0
        unrecoverable = 0
        decode_failed = 0
        parse_failed = 0
        write_errors = 0

        unrecoverable_samples: List[Dict[str, Any]] = []

        for fp in files:
            name = os.path.basename(fp)
            try:
                with open(fp, "rb") as f:
                    raw = f.read()
            except OSError as e:
                write_errors += 1
                self.agent.log_event(
                    event="recovery_read_failed",
                    status=AgentStatus.Failed.value,
                    path=fp,
                    error=str(e),
                )
                continue

            text, enc = self._decode(raw)
            if text is None or enc is None:
                decode_failed += 1
                # 移入 unrecoverable
                try:
                    dst = self._unique_dest(os.path.join(self.unrecoverable_dir, name))
                    shutil.move(fp, dst)
                    self.agent.log_event(
                        event="recovery_unrecoverable_decode",
                        src=fp,
                        dst=dst,
                        size_bytes=len(raw),
                    )
                    if len(unrecoverable_samples) < 10:
                        unrecoverable_samples.append({"name": name, "reason": "decode_failed", "size": len(raw)})
                except OSError as e:
                    write_errors += 1
                    self.agent.log_event(event="recovery_move_failed", status=AgentStatus.Failed.value, path=fp, error=str(e))
                unrecoverable += 1
                continue

            obj, strategy = self._try_parse(text)
            encoding_counter[enc] += 1
            if obj is None:
                parse_failed += 1
                try:
                    dst = self._unique_dest(os.path.join(self.unrecoverable_dir, name))
                    shutil.move(fp, dst)
                    self.agent.log_event(
                        event="recovery_unrecoverable_parse",
                        src=fp,
                        dst=dst,
                        decoded_with=enc,
                        size_bytes=len(raw),
                    )
                    if len(unrecoverable_samples) < 10:
                        unrecoverable_samples.append({"name": name, "reason": "parse_failed", "encoding": enc, "size": len(raw)})
                except OSError as e:
                    write_errors += 1
                    self.agent.log_event(event="recovery_move_failed", status=AgentStatus.Failed.value, path=fp, error=str(e))
                unrecoverable += 1
                continue

            parse_strategy_counter[strategy or "?"] += 1
            category, reason = classify_repaired(name, obj)
            category_counter[category] += 1

            if category == "important_data":
                dest_dir = self.c2_dir
            else:
                dest_dir = self.archive_dir
            dst = self._unique_dest(os.path.join(dest_dir, name))

            try:
                # 以 UTF-8（無 BOM）重序列化寫出，並刪除原檔
                with open(dst, "w", encoding="utf-8", newline="\n") as f:
                    json.dump(obj, f, ensure_ascii=False, indent=2)
                os.remove(fp)
                destination_counter[dest_dir] += 1
                repaired += 1
                self.agent.log_event(
                    event="recovery_repaired",
                    src=fp,
                    dst=dst,
                    category=category,
                    reason=reason,
                    encoding=enc,
                    parse_strategy=strategy,
                    size_in=len(raw),
                    size_out=os.path.getsize(dst),
                )
            except OSError as e:
                write_errors += 1
                self.agent.log_event(
                    event="recovery_write_failed",
                    status=AgentStatus.Failed.value,
                    path=dst,
                    error=str(e),
                )

        total = len(files)
        rate = (repaired / total) if total else 0.0
        self.agent.log_event(
            event="recovery_done",
            target_count=total,
            repaired=repaired,
            unrecoverable=unrecoverable,
            decode_failed=decode_failed,
            parse_failed=parse_failed,
            write_errors=write_errors,
            success_rate=round(rate, 4),
        )
        self.agent.set_status(
            AgentStatus.Success.value if write_errors == 0 else AgentStatus.Manual.value,
            reason=f"recovery_done repaired={repaired}/{total}",
        )
        return {
            "ok": write_errors == 0,
            "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "target_count": total,
            "repaired": repaired,
            "unrecoverable": unrecoverable,
            "decode_failed": decode_failed,
            "parse_failed": parse_failed,
            "write_errors": write_errors,
            "success_rate": round(rate, 4),
            "by_encoding": dict(encoding_counter),
            "by_parse_strategy": dict(parse_strategy_counter),
            "by_category": dict(category_counter),
            "by_destination": {k: v for k, v in destination_counter.items()},
            "unrecoverable_samples": unrecoverable_samples,
        }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Recovery_Agent CLI")
    parser.add_argument("--signed-token", required=True)
    args = parser.parse_args()
    a = Recovery_Agent(signed_token=args.signed_token)
    out = a.repair_all()
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
