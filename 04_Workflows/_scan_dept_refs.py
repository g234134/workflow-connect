"""掃描 gov_core_system 戰車內，含特定字串的引用點（部門編號對齊小工具）。

用途
====
這是一個小型審計工具，用來掃描整個大唐戰車（`D:\\大唐三省六部`）的
`Chariot_Registry.db`，尋找包含某段字串（例如「某個部門路徑片段」）的列。
典型使用情境：

- 將 `Departments/02_Strategy` 改名為 `Departments/06_Strategy` 之前 / 之後，
  用這支工具確認指紋資料庫內是否還殘留舊名引用。
- 任何「整體編號重整 / 路徑搬遷 / 別名汰換」之前的 dry-run 探勘。

掃描範圍
========
目前僅掃描 `04_Workflows/Chariot_Registry.db`（戰車唯一指紋權威）的所有
表、所有欄位，逐欄 `LIKE '%<needle>%'`。
專案內 markdown / json / yaml 等檔案的字串掃描，請改用 Cursor 的 Grep
或 ripgrep 直接執行，不在本工具範圍。

使用方式
========
    python 04_Workflows/_scan_dept_refs.py
    python 04_Workflows/_scan_dept_refs.py --needle "02_Strategy"
    python 04_Workflows/_scan_dept_refs.py --needle "06_Strategy" --db D:\\大唐三省六部\\04_Workflows\\Chariot_Registry.db
    python 04_Workflows/_scan_dept_refs.py --needle "raw_inbound" --limit 10

回傳碼：總是 0（即使 DB 不存在亦不視為失敗，方便管線串接）。
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(r"D:\大唐三省六部\04_Workflows\Chariot_Registry.db")
DEFAULT_NEEDLE = "02_Strategy"
DEFAULT_SAMPLE_LIMIT = 5


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="_scan_dept_refs.py",
        description="Scan Chariot_Registry.db for any row whose text column contains the given needle.",
    )
    p.add_argument(
        "--needle",
        default=DEFAULT_NEEDLE,
        help=f"Substring to search for (default: {DEFAULT_NEEDLE!r}).",
    )
    p.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help=f"Path to Chariot_Registry.db (default: {DEFAULT_DB}).",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_SAMPLE_LIMIT,
        help=f"Sample rows to print per hit column (default: {DEFAULT_SAMPLE_LIMIT}).",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    db: Path = args.db
    needle: str = args.needle
    sample_limit: int = max(0, int(args.limit))

    if not db.exists():
        print(f"[INFO] DB not found: {db}")
        return 0

    print(f"[INFO] db     = {db}")
    print(f"[INFO] needle = {needle!r}")

    con = sqlite3.connect(str(db))
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print(f"[INFO] tables: {tables}")

    total_hits = 0
    for t in tables:
        cols_info = con.execute(f"PRAGMA table_info({t})").fetchall()
        text_cols = [c[1] for c in cols_info]
        print(f"  [TABLE {t}] columns: {text_cols}")
        for c in text_cols:
            q = f"SELECT COUNT(*) FROM {t} WHERE CAST({c} AS TEXT) LIKE ?"
            try:
                n = con.execute(q, (f"%{needle}%",)).fetchone()[0]
            except sqlite3.Error as exc:
                print(f"    [WARN] {t}.{c}: {exc}")
                continue
            if n > 0:
                print(f"    [HIT ] {t}.{c} matches={n}")
                total_hits += n
                if sample_limit > 0:
                    rows = con.execute(
                        f"SELECT rowid, {c} FROM {t} WHERE CAST({c} AS TEXT) LIKE ? LIMIT ?",
                        (f"%{needle}%", sample_limit),
                    ).fetchall()
                    for rid, val in rows:
                        print(f"      rowid={rid}  value={val}")
    con.close()
    print(f"[DONE] total hits in DB: {total_hits}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
