# Cleanup_Check.py
# 比對 C 槽「舊目錄」與 D 槽「新目錄」：以 SHA256 內容比對，找出已在 D 槽存在相同內容的檔案，
# 供您手動刪除 C 槽冗餘檔（遷移時檔名可能帶前綴，故不用路徑 1:1 對照）。

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict, Iterator, List, Optional, Tuple


CHUNK = 1024 * 1024


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: str) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                b = f.read(CHUNK)
                if not b:
                    break
                h.update(b)
        return h.hexdigest()
    except OSError:
        return None


def iter_files(root: str, skip_dir_names: frozenset) -> Iterator[str]:
    root = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dir_names]
        for fn in filenames:
            yield os.path.join(dirpath, fn)


def build_dest_index(
    dest_roots: List[str],
    skip_dir_names: frozenset,
    progress_every: int,
) -> Dict[str, List[str]]:
    """hash -> 在 D 槽上的相對/絕對路徑列表（同一 hash 可能多個檔）。"""
    index: Dict[str, List[str]] = {}
    n = 0
    for droot in dest_roots:
        droot_abs = os.path.abspath(droot)
        for fp in iter_files(droot_abs, skip_dir_names):
            n += 1
            if progress_every and n % progress_every == 0:
                print(f"[D] indexed {n} files...", flush=True)
            digest = sha256_file(fp)
            if digest is None:
                continue
            index.setdefault(digest, []).append(fp)
    print(f"[D] done. Total files hashed: {n}, unique hashes: {len(index)}", flush=True)
    return index


@dataclass
class MatchRow:
    c_path: str
    sha256: str
    d_matches: List[str]
    c_size: int


def main() -> None:
    p = argparse.ArgumentParser(
        description="List C: files whose content already exists on D: (by SHA256). Safe-delete candidates for manual cleanup."
    )
    p.add_argument(
        "--c-root",
        action="append",
        required=True,
        help="可重複；要檢查的 C 槽（或任意）舊目錄，例如 C:\\Users\\666LAG 或 C:\\AI_Project",
    )
    p.add_argument(
        "--d-root",
        action="append",
        default=None,
        help="新目錄根（可重複）；預設由 Master_Map / gov_paths 推導",
    )
    p.add_argument(
        "--skip-dirs",
        default=".git,__pycache__,node_modules,.venv,venv",
        help="走訪時忽略的目錄名，逗號分隔",
    )
    p.add_argument(
        "--progress-every",
        type=int,
        default=5000,
        help="每處理 N 個檔案印一次進度（0 關閉）",
    )
    p.add_argument(
        "--report",
        default=None,
        help="輸出 JSON 報表路徑；預設 04_Workflows/cleanup_check_report_<timestamp>.json",
    )
    args = p.parse_args()

    skip_dir_names = frozenset(s.strip() for s in args.skip_dirs.split(",") if s.strip())

    if args.d_root:
        dest_roots = args.d_root
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        agents_core = os.path.normpath(os.path.join(here, "..", "02_Agents_Core"))
        if agents_core not in sys.path:
            sys.path.insert(0, agents_core)
        from gov_paths import get_tang_gov_root

        dest_roots = [get_tang_gov_root()]
    c_roots = [os.path.abspath(x) for x in args.c_root]

    here = os.path.dirname(os.path.abspath(__file__))
    default_report = os.path.join(
        here,
        f"cleanup_check_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    )
    report_path = os.path.abspath(args.report or default_report)

    print("=== Cleanup_Check: build D index (by content hash) ===", flush=True)
    dest_index = build_dest_index(dest_roots, skip_dir_names, args.progress_every)

    print("=== Cleanup_Check: scan C roots ===", flush=True)
    matched: List[MatchRow] = []
    unmatched: List[str] = []
    errors: List[Dict[str, str]] = []
    scanned = 0

    for croot in c_roots:
        if not os.path.isdir(croot):
            errors.append({"path": croot, "error": "not a directory"})
            continue
        for fp in iter_files(croot, skip_dir_names):
            scanned += 1
            if args.progress_every and scanned % args.progress_every == 0:
                print(f"[C] scanned {scanned} files...", flush=True)
            try:
                st = os.stat(fp)
                c_size = st.st_size
            except OSError as e:
                errors.append({"path": fp, "error": str(e)})
                continue

            digest = sha256_file(fp)
            if digest is None:
                errors.append({"path": fp, "error": "hash_failed"})
                continue

            d_list = dest_index.get(digest)
            if d_list:
                matched.append(
                    MatchRow(
                        c_path=fp,
                        sha256=digest,
                        d_matches=list(d_list),
                        c_size=c_size,
                    )
                )
            else:
                unmatched.append(fp)

    payload = {
        "generated_at": _utc_iso(),
        "c_roots": c_roots,
        "d_roots": [os.path.abspath(x) for x in dest_roots],
        "stats": {
            "c_files_scanned": scanned,
            "matched_on_d_count": len(matched),
            "not_found_on_d_count": len(unmatched),
            "errors_count": len(errors),
        },
        "safe_delete_candidates": [asdict(m) for m in matched],
        "not_found_on_d_sample": unmatched[:500],
        "not_found_on_d_total": len(unmatched),
        "errors": errors[:200],
        "note": "以 SHA256 內容一致視為已複製；請仍自行確認後再刪除 C 槽檔案。",
    }

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print("", flush=True)
    print(f"報表已寫入: {report_path}", flush=True)
    print(
        f"摘要: C 掃描 {scanned} 個檔案 | 已在 D 找到相同內容 {len(matched)} | 未在 D 找到 {len(unmatched)} | 錯誤 {len(errors)}",
        flush=True,
    )
    if matched:
        print("\n範例（已複製，可考慮自 C 刪除，請自行再確認）:", flush=True)
        for row in matched[:15]:
            print(f"  C: {row.c_path}", flush=True)
            print(f"     D: {row.d_matches[0]}{' …' if len(row.d_matches) > 1 else ''}", flush=True)


if __name__ == "__main__":
    main()
