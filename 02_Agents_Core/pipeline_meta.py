"""pipeline_meta — 碼源清洗戰役 v2 的 jobs + events metadata SDK（薄層、零依賴）。

設計原則
========
- 純 stdlib（`sqlite3`、`uuid`、`json`、`contextlib`、`datetime`），不引入新依賴。
- **低侵入**：既有 cleaner 不必重構，只需在啟動／結束／關鍵節點呼叫幾個函式。
- **崩潰安全**：`job_run()` context manager 在例外發生時自動寫
  `pipeline_aborted` 事件並把 jobs.status 設為 'failed'。
- **時間一律 UTC ISO-8601 seconds**，與 Base_Agent 慣例對齊。
- **WAL 模式**：寫入時其他 reader 可以即時 `sqlite3` 查詢，方便 tail。

對外 API（穩定面）
==================
    DEFAULT_DB                  : Path           # 預設 db 位置
    init_db(db_path)            : None           # 冪等建表
    start_job(...)              -> job_id (str)
    record_event(...)           -> event_id (int)
    update_job_counts(...)      -> None
    finish_job(...)             -> None
    job_run(...)                : context mgr    # yield job_id；含 crash-safety

事件型別建議清單（不強制，event_type 為自由字串）：
    pipeline_started           pipeline_finished       pipeline_aborted
    scan_raw_inbound_started   scan_raw_inbound_finished
    clean_record_started       clean_record_ok         clean_record_failed
    write_cleaned_full         write_format_error
    groq_called                groq_failed
    benchmark_recorded         checkpoint_wave_end
"""
from __future__ import annotations

import contextlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Optional


DEFAULT_DB = Path(
    r"D:\大唐三省六部\01_Environments\python_venvs\gov_core_system"
    r"\Departments\05_Data_Vault\pipeline_meta\code_cleaning_pipeline_v2_meta.db"
)

PIPELINE_NAME_DEFAULT = "code_cleaning_pipeline_v2"

VALID_JOB_STATUS = {"pending", "running", "success", "failed", "partial"}
VALID_LEVELS = {"info", "warning", "error"}


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA journal_mode = WAL")
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db(db_path: Path = DEFAULT_DB) -> None:
    """Apply schema (idempotent)。重複呼叫安全。"""
    from importlib import import_module  # 延遲匯入避免循環
    # 為避免硬耦合 04_Workflows 模組路徑，schema 內嵌一份（與 init_pipeline_meta 對齊）。
    stmts = [
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
        "CREATE INDEX IF NOT EXISTS idx_events_job_ts ON events(job_id, timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_events_type   ON events(event_type)",
        "CREATE INDEX IF NOT EXISTS idx_events_level  ON events(status_level)",
    ]
    con = _connect(db_path)
    try:
        for s in stmts:
            con.execute(s)
        con.commit()
    finally:
        con.close()
    _ = import_module  # silence unused warning（保留 hook 以後擴充）


def start_job(
    *,
    input_root: str,
    cleaned_output_root: str,
    failed_output_root: str,
    pipeline_name: str = PIPELINE_NAME_DEFAULT,
    run_id: Optional[str] = None,
    wave: Optional[int] = None,
    triggered_by: Optional[str] = None,
    notes: Optional[str] = None,
    db_path: Path = DEFAULT_DB,
) -> str:
    """建立一筆 job 列；初始 status='running'。回傳 job_id（UUID hex）。"""
    job_id = uuid.uuid4().hex
    now = _utc_iso()
    con = _connect(db_path)
    try:
        con.execute(
            """
            INSERT INTO jobs (
                job_id, pipeline_name, run_id, wave,
                input_root, cleaned_output_root, failed_output_root,
                status, started_at, finished_at,
                total_files_seen, cleaned_success_count, cleaned_failed_count,
                notes, triggered_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'running', ?, NULL, 0, 0, 0, ?, ?, ?, ?)
            """,
            (
                job_id, pipeline_name, run_id, wave,
                input_root, cleaned_output_root, failed_output_root,
                now, notes, triggered_by, now, now,
            ),
        )
        con.commit()
    finally:
        con.close()
    return job_id


def record_event(
    *,
    job_id: str,
    event_type: str,
    status_level: str = "info",
    message: Optional[str] = None,
    related_path: Optional[str] = None,
    detail_payload: Optional[Dict[str, Any]] = None,
    db_path: Path = DEFAULT_DB,
) -> int:
    """寫入一筆 event；detail_payload 接 dict 自動 json.dumps。"""
    if status_level not in VALID_LEVELS:
        raise ValueError(f"invalid status_level: {status_level!r}")
    payload_str = None
    if detail_payload is not None:
        payload_str = json.dumps(detail_payload, ensure_ascii=False, default=str)
    now = _utc_iso()
    con = _connect(db_path)
    try:
        cur = con.execute(
            """
            INSERT INTO events (job_id, timestamp, event_type, status_level,
                                message, related_path, detail_payload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (job_id, now, event_type, status_level, message, related_path, payload_str),
        )
        con.commit()
        return int(cur.lastrowid or 0)
    finally:
        con.close()


def update_job_counts(
    *,
    job_id: str,
    total_files_seen: Optional[int] = None,
    cleaned_success_count: Optional[int] = None,
    cleaned_failed_count: Optional[int] = None,
    db_path: Path = DEFAULT_DB,
) -> None:
    """直接覆寫對應欄位（None 表示不變）。需 delta 累加由呼叫端處理。"""
    sets, args = [], []
    if total_files_seen is not None:
        sets.append("total_files_seen = ?")
        args.append(int(total_files_seen))
    if cleaned_success_count is not None:
        sets.append("cleaned_success_count = ?")
        args.append(int(cleaned_success_count))
    if cleaned_failed_count is not None:
        sets.append("cleaned_failed_count = ?")
        args.append(int(cleaned_failed_count))
    if not sets:
        return
    sets.append("updated_at = ?")
    args.append(_utc_iso())
    args.append(job_id)
    con = _connect(db_path)
    try:
        con.execute(f"UPDATE jobs SET {', '.join(sets)} WHERE job_id = ?", args)
        con.commit()
    finally:
        con.close()


def finish_job(
    *,
    job_id: str,
    status: str,
    notes: Optional[str] = None,
    db_path: Path = DEFAULT_DB,
) -> None:
    """把 job 標記為終態（success/failed/partial），寫 finished_at。"""
    if status not in VALID_JOB_STATUS:
        raise ValueError(f"invalid status: {status!r}")
    now = _utc_iso()
    con = _connect(db_path)
    try:
        if notes is not None:
            con.execute(
                "UPDATE jobs SET status=?, finished_at=?, notes=?, updated_at=? WHERE job_id=?",
                (status, now, notes, now, job_id),
            )
        else:
            con.execute(
                "UPDATE jobs SET status=?, finished_at=?, updated_at=? WHERE job_id=?",
                (status, now, now, job_id),
            )
        con.commit()
    finally:
        con.close()


@contextlib.contextmanager
def job_run(
    *,
    input_root: str,
    cleaned_output_root: str,
    failed_output_root: str,
    pipeline_name: str = PIPELINE_NAME_DEFAULT,
    run_id: Optional[str] = None,
    wave: Optional[int] = None,
    triggered_by: Optional[str] = None,
    notes: Optional[str] = None,
    db_path: Path = DEFAULT_DB,
) -> Iterator[str]:
    """Context manager：

    - 入口：建立 job (status='running') + 寫 `pipeline_started` 事件
    - 正常結束：finish_job('success') + 寫 `pipeline_finished`
    - 例外：finish_job('failed', notes='<exc>') + 寫 `pipeline_aborted` (error)，再 raise

    與既有 Base_Agent 並存：請傳入 Base_Agent.run_id 以便 trace 串接。
    """
    job_id = start_job(
        input_root=input_root,
        cleaned_output_root=cleaned_output_root,
        failed_output_root=failed_output_root,
        pipeline_name=pipeline_name,
        run_id=run_id,
        wave=wave,
        triggered_by=triggered_by,
        notes=notes,
        db_path=db_path,
    )
    record_event(
        job_id=job_id, event_type="pipeline_started",
        message=f"pipeline_name={pipeline_name} run_id={run_id} wave={wave}",
        db_path=db_path,
    )
    try:
        yield job_id
    except BaseException as exc:
        finish_job(
            job_id=job_id, status="failed",
            notes=f"{type(exc).__name__}: {exc}",
            db_path=db_path,
        )
        record_event(
            job_id=job_id, event_type="pipeline_aborted",
            status_level="error",
            message=f"{type(exc).__name__}: {exc}",
            db_path=db_path,
        )
        raise
    else:
        finish_job(job_id=job_id, status="success", db_path=db_path)
        record_event(
            job_id=job_id, event_type="pipeline_finished",
            message="ok", db_path=db_path,
        )
