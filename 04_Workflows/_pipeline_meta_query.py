"""
_pipeline_meta_query.py — 碼源清洗戰役 v2（code_cleaning_pipeline_v2）metadata 查詢 CLI

查詢來源：SQLite jobs + events（由 02_Agents_Core/pipeline_meta.py 建表與寫入）
限制：只查詢，不改 schema；純 stdlib。
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


DEFAULT_DB = Path(
    r"D:\大唐三省六部\01_Environments\python_venvs\gov_core_system"
    r"\Departments\05_Data_Vault\pipeline_meta\code_cleaning_pipeline_v2_meta.db"
)


def _connect(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    return con


def _parse_iso_utc(s: str) -> str:
    """
    Accepts ISO-8601 timestamps. Returns a canonical UTC ISO string (seconds precision).
    Supports:
      - '2026-05-11T01:02:03Z'
      - '2026-05-11T01:02:03+00:00'
      - '2026-05-11T09:02:03' (assumed UTC)
    """
    s = s.strip()
    if not s:
        raise ValueError("empty time string")

    raw = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt_utc = dt.astimezone(timezone.utc)
    return dt_utc.isoformat(timespec="seconds")


def _truncate(s: Optional[str], *, max_len: int) -> str:
    if not s:
        return ""
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


def _dash_if_null(v: Optional[str]) -> str:
    return v if v else "-"


def _print_recent_jobs(rows: list[sqlite3.Row]) -> int:
    if not rows:
        print("No jobs found.")
        return 0

    # Simple aligned output (pure text).
    for r in rows:
        job_id = str(r["job_id"])
        pipeline_name = str(r["pipeline_name"])
        status = str(r["status"])
        started_at = str(r["started_at"])
        finished_at = _dash_if_null(r["finished_at"])
        total_files_seen = int(r["total_files_seen"] or 0)
        ok_n = int(r["cleaned_success_count"] or 0)
        fail_n = int(r["cleaned_failed_count"] or 0)
        triggered_by = (r["triggered_by"] or "").strip()

        print(
            f"{started_at:19}  "
            f"job_id={job_id}  "
            f"pipeline={pipeline_name:28.28}  "
            f"status={status:8.8}  "
            f"finished={finished_at:19}  "
            f"seen={total_files_seen:6d}  "
            f"cleaned={ok_n:6d}/{fail_n:<6d}  "
            f"by={triggered_by}"
        )
    return len(rows)


def _job_exists(con: sqlite3.Connection, job_id: str) -> bool:
    cur = con.execute("SELECT 1 FROM jobs WHERE job_id=? LIMIT 1", (job_id,))
    return cur.fetchone() is not None


def _print_events(rows: list[sqlite3.Row], *, job_id: str, job_exists: bool) -> int:
    if not job_exists:
        print(f"No job found with job_id={job_id}。")
        return 0
    if not rows:
        print(f"No events found for job_id={job_id}。")
        return 0

    for r in rows:
        ts = str(r["timestamp"])
        event_type = str(r["event_type"])
        level = str(r["status_level"])
        msg = (r["message"] or "").strip()
        rel = (r["related_path"] or "").strip()
        payload = _truncate(r["detail_payload"], max_len=80)

        line = f"{ts:19}  {event_type:28.28}  {level:7.7}"
        extras = []
        if msg:
            extras.append(f"msg={_truncate(msg, max_len=120)}")
        if rel:
            extras.append(f"path={_truncate(rel, max_len=120)}")
        if payload:
            extras.append(f"payload={payload}")
        if extras:
            line += "  " + "  ".join(extras)
        print(line)
    return len(rows)


def _print_error_events(rows: list[sqlite3.Row], *, since_iso: str) -> int:
    if not rows:
        print(f"No error events found since {since_iso}.")
        return 0
    for r in rows:
        ts = str(r["timestamp"])
        job_id = str(r["job_id"])
        event_type = str(r["event_type"])
        msg = (r["message"] or "").strip()
        if msg:
            print(f"{ts:19}  {job_id}  {event_type:28.28}  {msg}")
        else:
            print(f"{ts:19}  {job_id}  {event_type:28.28}")
    return len(rows)


def query_recent_jobs(con: sqlite3.Connection, n: int) -> int:
    cur = con.execute(
        """
        SELECT
          job_id, pipeline_name, run_id, wave, status,
          started_at, finished_at,
          total_files_seen, cleaned_success_count, cleaned_failed_count,
          triggered_by, notes
        FROM jobs
        ORDER BY (started_at IS NULL) ASC, started_at DESC
        LIMIT ?
        """,
        (int(n),),
    )
    return _print_recent_jobs(cur.fetchall())


def query_job_events(con: sqlite3.Connection, job_id: str) -> int:
    job_exists = _job_exists(con, job_id)
    cur = con.execute(
        """
        SELECT
          event_id, job_id, timestamp, event_type, status_level,
          message, related_path, detail_payload
        FROM events
        WHERE job_id = ?
        ORDER BY (timestamp IS NULL) ASC, timestamp ASC, event_id ASC
        """,
        (job_id,),
    )
    return _print_events(cur.fetchall(), job_id=job_id, job_exists=job_exists)


def query_errors_since(con: sqlite3.Connection, since_iso: str) -> int:
    cur = con.execute(
        """
        SELECT
          event_id, job_id, timestamp, event_type, status_level,
          message, related_path, detail_payload
        FROM events
        WHERE status_level = 'error' AND timestamp >= ?
        ORDER BY (timestamp IS NULL) ASC, timestamp ASC, event_id ASC
        """,
        (since_iso,),
    )
    return _print_error_events(cur.fetchall(), since_iso=since_iso)


def build_parser() -> argparse.ArgumentParser:
    epilog = textwrap.dedent(
        """
        Examples:
          python 04_Workflows/_pipeline_meta_query.py --recent-jobs 20
          python 04_Workflows/_pipeline_meta_query.py --events <JOB_ID>
          python 04_Workflows/_pipeline_meta_query.py --errors-since 2026-05-11T00:00:00Z
        """
    ).strip()

    p = argparse.ArgumentParser(
        prog="_pipeline_meta_query.py",
        description="碼源清洗戰役 v2（code_cleaning_pipeline_v2）SQLite metadata 查詢 CLI。",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--db",
        default=str(DEFAULT_DB),
        help=f"SQLite DB 路徑（預設：{DEFAULT_DB}）",
    )

    g = p.add_mutually_exclusive_group(required=False)
    g.add_argument(
        "--recent-jobs",
        type=int,
        nargs="?",
        const=10,
        default=None,
        metavar="N",
        help="列出最近 N 筆 jobs（ORDER BY started_at DESC）。可省略 N，預設 10。",
    )
    g.add_argument(
        "--events",
        metavar="JOB_ID",
        help="列出指定 job_id 的所有 events（ORDER BY timestamp ASC）。",
    )
    g.add_argument(
        "--errors-since",
        metavar="ISO_TIME",
        help="列出指定時間之後的所有 error 級別事件（timestamp >= ISO_TIME）。",
    )
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"DB not found: {db_path}", file=sys.stderr)
        return 2

    try:
        con = _connect(db_path)
    except sqlite3.Error as e:
        print(f"sqlite connect error: {e}", file=sys.stderr)
        return 2

    try:
        if args.events is None and args.errors_since is None and args.recent_jobs is None:
            args.recent_jobs = 10

        if args.recent_jobs is not None:
            n = int(args.recent_jobs)
            if n <= 0:
                print("--recent-jobs N must be > 0", file=sys.stderr)
                return 2
            query_recent_jobs(con, n)
        elif args.events is not None:
            query_job_events(con, args.events.strip())
        else:
            since_iso = _parse_iso_utc(args.errors_since)
            query_errors_since(con, since_iso)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    except sqlite3.Error as e:
        print(f"sqlite query error: {e}", file=sys.stderr)
        return 2
    finally:
        try:
            con.close()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

