"""碼源清洗戰役 v2 — pipeline_meta 初始化器（jobs + events）。

冪等：可重複執行；CREATE TABLE IF NOT EXISTS、CREATE INDEX IF NOT EXISTS。
零依賴：stdlib `sqlite3` only。

預設將 SQLite 落於：
    01_Environments/python_venvs/gov_core_system/Departments/05_Data_Vault/pipeline_meta/
        code_cleaning_pipeline_v2_meta.db

可由 --db 覆寫。

Usage:
    python 04_Workflows/_init_pipeline_meta.py
    python 04_Workflows/_init_pipeline_meta.py --db D:\\其他位置.db
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(
    r"D:\大唐三省六部\01_Environments\python_venvs\gov_core_system"
    r"\Departments\05_Data_Vault\pipeline_meta\code_cleaning_pipeline_v2_meta.db"
)

SCHEMA = [
    # ---------- jobs ----------
    """
    CREATE TABLE IF NOT EXISTS jobs (
        job_id                 TEXT PRIMARY KEY,
        pipeline_name          TEXT NOT NULL,
        run_id                 TEXT,
        wave                   INTEGER,
        input_root             TEXT NOT NULL,
        cleaned_output_root    TEXT NOT NULL,
        failed_output_root     TEXT NOT NULL,
        status                 TEXT NOT NULL CHECK (status IN
                                   ('pending','running','success','failed','partial')),
        started_at             TEXT NOT NULL,
        finished_at            TEXT,
        total_files_seen       INTEGER NOT NULL DEFAULT 0,
        cleaned_success_count  INTEGER NOT NULL DEFAULT 0,
        cleaned_failed_count   INTEGER NOT NULL DEFAULT 0,
        notes                  TEXT,
        triggered_by           TEXT,
        created_at             TEXT NOT NULL,
        updated_at             TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_jobs_pipeline_status ON jobs(pipeline_name, status)",
    "CREATE INDEX IF NOT EXISTS idx_jobs_started_at      ON jobs(started_at)",
    "CREATE INDEX IF NOT EXISTS idx_jobs_run_id          ON jobs(run_id)",

    # ---------- events ----------
    """
    CREATE TABLE IF NOT EXISTS events (
        event_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id          TEXT NOT NULL,
        timestamp       TEXT NOT NULL,
        event_type      TEXT NOT NULL,
        status_level    TEXT NOT NULL DEFAULT 'info' CHECK (status_level IN
                            ('info','warning','error')),
        message         TEXT,
        related_path    TEXT,
        detail_payload  TEXT,
        FOREIGN KEY (job_id) REFERENCES jobs(job_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_events_job_ts  ON events(job_id, timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_events_type    ON events(event_type)",
    "CREATE INDEX IF NOT EXISTS idx_events_level   ON events(status_level)",
]


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    try:
        con.execute("PRAGMA journal_mode = WAL")
        con.execute("PRAGMA foreign_keys = ON")
        for stmt in SCHEMA:
            con.execute(stmt)
        con.commit()
    finally:
        con.close()


def describe(db_path: Path) -> None:
    con = sqlite3.connect(str(db_path))
    try:
        for t in ("jobs", "events"):
            cols = con.execute(f"PRAGMA table_info({t})").fetchall()
            print(f"  [{t}] columns ({len(cols)}):")
            for c in cols:
                cid, name, ctype, notnull, _dflt, pk = c
                marks = []
                if pk:
                    marks.append("PK")
                if notnull:
                    marks.append("NOT NULL")
                tail = f"  ({', '.join(marks)})" if marks else ""
                print(f"      - {name:<24} {ctype:<10}{tail}")
            idx = con.execute(f"PRAGMA index_list({t})").fetchall()
            print(f"  [{t}] indexes ({len(idx)}):")
            for i in idx:
                print(f"      - {i[1]} (unique={bool(i[2])})")
    finally:
        con.close()


def main() -> int:
    ap = argparse.ArgumentParser(description="Init code_cleaning_pipeline_v2 meta DB")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = ap.parse_args()

    print(f"[INFO] target db: {args.db}")
    init_db(args.db)
    print("[OK] schema applied (idempotent).")
    describe(args.db)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
