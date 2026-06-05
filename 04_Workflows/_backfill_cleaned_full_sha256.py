"""_backfill_cleaned_full_sha256.py — 為既有 cleaned_full JSON 補齊 content_sha256。

優先順序：
  1) 若 source_path 指向之檔案仍存在 → 對該檔案 raw bytes 做 SHA256（與清剿管線一致）
  2) 否則 → 對本 JSON 檔案 bytes 做 SHA256（artifact digest，僅作索引穩定用）

不修改其他欄位；以 tmp + replace 寫回。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from typing import Any, Dict, Tuple

from _tang_paths import bootstrap_sys_path, sha256_file  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
_root = bootstrap_sys_path(_here)

from gov_paths import get_tang_gov_root, resolve_agent_output_path  # type: ignore


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _patch_one(fp: str) -> Tuple[str, str]:
    """回傳 (action, digest_or_empty)。"""
    with open(fp, "rb") as f:
        raw_json = f.read()
    try:
        rec: Dict[str, Any] = json.loads(raw_json.decode("utf-8"))
    except Exception:  # noqa: BLE001
        return ("skip_invalid_json", "")

    existing = str(rec.get("content_sha256") or "").strip().lower()
    if len(existing) == 64 and re.fullmatch(r"[0-9a-f]{64}", existing):
        return ("already_set", existing)

    src = str(rec.get("source_path") or "").strip()
    digest = ""
    if src and os.path.isfile(src):
        try:
            digest = sha256_file(src)
        except OSError:
            digest = ""
    if not digest:
        digest = _sha256_bytes(raw_json)

    rec["content_sha256"] = digest
    tmp = fp + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    os.replace(tmp, fp)
    return ("patched", digest)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-files", type=int, default=0, help="0=不限制")
    args = ap.parse_args()

    root = get_tang_gov_root()
    cleaned = resolve_agent_output_path(root, "05_Temp_Cache", "cleaned_full")
    if not os.path.isdir(cleaned):
        print(json.dumps({"ok": False, "error": "cleaned_full_missing", "cleaned": cleaned}, ensure_ascii=False))
        return 2

    paths = sorted(
        os.path.join(cleaned, fn) for fn in os.listdir(cleaned) if fn.endswith(".json")
    )
    if args.max_files and args.max_files > 0:
        paths = paths[: int(args.max_files)]

    stats = {"total": len(paths), "patched": 0, "already": 0, "skipped": 0}
    for fp in paths:
        act, _dig = _patch_one(fp)
        if act == "patched":
            stats["patched"] += 1
        elif act == "already_set":
            stats["already"] += 1
        else:
            stats["skipped"] += 1

    print(json.dumps({"ok": True, "cleaned_full": cleaned, "stats": stats}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
