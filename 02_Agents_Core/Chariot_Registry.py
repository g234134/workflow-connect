# Chariot_Registry.py — 兵部·SQLite 內容雜湊登記
# 提供多 Agent 併行去重檢索；亦提供舊雜湊文字檔遷移 CLI。

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional, Set, Tuple

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from gov_paths import get_tang_gov_root, resolve_agent_output_path  # type: ignore


DEFAULT_DB_NAME = "Chariot_Registry.db"


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_db_path(dest_root: Optional[str] = None) -> str:
    base = resolve_agent_output_path(dest_root, "04_Workflows")
    return os.path.join(base, DEFAULT_DB_NAME)


class Chariot_Registry:
    """SQLite 雜湊登記：表 content_hashes (sha256 PK) 與 events (audit log)。"""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or default_db_path()
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init()

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.db_path, timeout=60, isolation_level=None)
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        return c

    def _init(self) -> None:
        with self._conn() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS content_hashes (
                    sha256 TEXT PRIMARY KEY,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at  TEXT,
                    agent         TEXT,
                    source_path   TEXT,
                    clean_status  TEXT,
                    extension     TEXT,
                    original_type TEXT
                )
                """
            )
            c.execute(
                "CREATE INDEX IF NOT EXISTS ix_clean_status ON content_hashes(clean_status)"
            )
            c.execute(
                "CREATE INDEX IF NOT EXISTS ix_extension ON content_hashes(extension)"
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts        TEXT NOT NULL,
                    agent     TEXT,
                    run_id    TEXT,
                    kind      TEXT,
                    payload   TEXT
                )
                """
            )

    def has(self, sha256: str) -> bool:
        with self._conn() as c:
            row = c.execute(
                "SELECT 1 FROM content_hashes WHERE sha256=?", (sha256,)
            ).fetchone()
            return row is not None

    def add(self, sha256: str, **fields: Any) -> bool:
        ts = _utc_iso()
        agent = fields.get("agent")
        src = fields.get("source_path")
        st = fields.get("clean_status")
        ext = fields.get("extension")
        otype = fields.get("original_type")
        with self._conn() as c:
            cur = c.execute(
                """
                INSERT INTO content_hashes
                    (sha256, first_seen_at, last_seen_at, agent, source_path,
                     clean_status, extension, original_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sha256) DO UPDATE SET
                    last_seen_at  = excluded.last_seen_at,
                    agent         = COALESCE(excluded.agent,         content_hashes.agent),
                    source_path   = COALESCE(excluded.source_path,   content_hashes.source_path),
                    clean_status  = COALESCE(excluded.clean_status,  content_hashes.clean_status),
                    extension     = COALESCE(excluded.extension,     content_hashes.extension),
                    original_type = COALESCE(excluded.original_type, content_hashes.original_type)
                """,
                (sha256, ts, ts, agent, src, st, ext, otype),
            )
            return cur.rowcount > 0

    def add_event(self, *, agent: str, run_id: str, kind: str, payload: Dict[str, Any]) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO events (ts, agent, run_id, kind, payload) VALUES (?, ?, ?, ?, ?)",
                (_utc_iso(), agent, run_id, kind, json.dumps(payload, ensure_ascii=False)),
            )

    def count(self) -> int:
        with self._conn() as c:
            row = c.execute("SELECT COUNT(*) FROM content_hashes").fetchone()
            return int(row[0] if row else 0)

    def count_by_status(self) -> Dict[str, int]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT COALESCE(clean_status,'(null)'), COUNT(*) FROM content_hashes GROUP BY clean_status"
            ).fetchall()
        return {str(k): int(v) for k, v in rows}

    # 已進入下游處理鏈的狀態：不得因 raw_inbound 哨兵而降回 pending
    PRESERVE_CLEAN_STATUSES: frozenset = frozenset({"indexed", "success", "cleaned", "validated"})

    def get_clean_status(self, sha256: str) -> Optional[str]:
        with self._conn() as c:
            row = c.execute(
                "SELECT clean_status FROM content_hashes WHERE sha256 = ?",
                (sha256,),
            ).fetchone()
            return str(row[0]) if row and row[0] is not None else None

    def count_raw_inbound_pending(self) -> int:
        with self._conn() as c:
            row = c.execute(
                """
                SELECT COUNT(*) FROM content_hashes
                WHERE original_type = ? AND COALESCE(clean_status,'') = ?
                """,
                ("raw_inbound", "pending"),
            ).fetchone()
            return int(row[0] if row else 0)

    def count_raw_inbound_rows(self) -> int:
        with self._conn() as c:
            row = c.execute(
                "SELECT COUNT(*) FROM content_hashes WHERE original_type = ?",
                ("raw_inbound",),
            ).fetchone()
            return int(row[0] if row else 0)

    def register_raw_inbound_pending(
        self,
        sha256: str,
        *,
        agent: str,
        source_path: str,
        extension: str,
        original_type: str = "raw_inbound",
    ) -> str:
        """
        刑部生料入隊：新內容寫入 pending；已存在且為 PRESERVE_CLEAN_STATUSES 者只刷新 last_seen。
        回傳：inserted_pending | promoted_pending | skipped_indexed
        """
        ts = _utc_iso()
        ext = extension or ""
        with self._conn() as c:
            row = c.execute(
                "SELECT clean_status FROM content_hashes WHERE sha256 = ?",
                (sha256,),
            ).fetchone()
            if row is None:
                c.execute(
                    """
                    INSERT INTO content_hashes
                        (sha256, first_seen_at, last_seen_at, agent, source_path,
                         clean_status, extension, original_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (sha256, ts, ts, agent, source_path, "pending", ext, original_type),
                )
                return "inserted_pending"
            prev = row[0]
            if prev in self.PRESERVE_CLEAN_STATUSES:
                c.execute(
                    """
                    UPDATE content_hashes
                    SET last_seen_at = ?, source_path = COALESCE(?, source_path)
                    WHERE sha256 = ?
                    """,
                    (ts, source_path, sha256),
                )
                return "skipped_indexed"
            c.execute(
                """
                UPDATE content_hashes
                SET last_seen_at = ?, agent = ?, source_path = ?, clean_status = ?,
                    extension = ?, original_type = ?
                WHERE sha256 = ?
                """,
                (ts, agent, source_path, "pending", ext, original_type, sha256),
            )
            return "promoted_pending"

    def migrate_from_textfile(
        self,
        txt_path: str,
        *,
        agent: str = "Code_Cleaner_Throttled_Agent",
    ) -> Dict[str, Any]:
        if not os.path.isfile(txt_path):
            return {"file_missing": True, "rows_seen": 0, "rows_inserted": 0, "src": txt_path}
        ts = _utc_iso()
        seen = 0
        inserted = 0
        with self._conn() as c:
            with open(txt_path, "r", encoding="utf-8") as f:
                c.execute("BEGIN")
                try:
                    for line in f:
                        h = line.strip()
                        if len(h) != 64:
                            continue
                        seen += 1
                        cur = c.execute(
                            """
                            INSERT OR IGNORE INTO content_hashes
                                (sha256, first_seen_at, last_seen_at, agent)
                            VALUES (?, ?, ?, ?)
                            """,
                            (h, ts, ts, agent),
                        )
                        if cur.rowcount > 0:
                            inserted += 1
                    c.execute("COMMIT")
                except Exception:
                    c.execute("ROLLBACK")
                    raise
        return {
            "file_missing": False,
            "rows_seen": seen,
            "rows_inserted": inserted,
            "src": txt_path,
        }

    def register_directory_files(
        self,
        root: str,
        *,
        agent: str,
        extensions: Optional[Set[str]] = None,
        skip_dirs: Optional[Set[str]] = None,
    ) -> Dict[str, Any]:
        """遞迴掃描目錄，將檔案內容 SHA256 登錄（INSERT OR REPLACE 語意見 add）。"""
        root = os.path.abspath(root)
        if not os.path.isdir(root):
            return {"error": "not_a_directory", "root": root, "files": 0, "added_rows": 0}

        ext_ok = extensions or {
            ".py", ".pyi", ".md", ".json", ".yaml", ".yml", ".toml", ".txt",
            ".html", ".htm", ".css", ".js", ".mjs", ".cjs", ".ts", ".tsx",
            ".sh", ".ps1", ".sql", ".vue", ".xml",
        }
        skips = skip_dirs or {
            ".git", "__pycache__", "node_modules", ".venv", "venv",
            "dist", "build", ".pytest_cache", ".mypy_cache",
        }

        def _sha256_file(fp: str) -> str:
            h = hashlib.sha256()
            with open(fp, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            return h.hexdigest()

        files = 0
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns if d not in skips]
            for fn in fns:
                fp = os.path.join(dp, fn)
                ext = os.path.splitext(fn)[1].lower()
                if ext_ok is not None and ext not in ext_ok:
                    continue
                try:
                    digest = _sha256_file(fp)
                except OSError:
                    continue
                files += 1
                rel = os.path.relpath(fp, root)
                self.add(
                    digest,
                    agent=agent,
                    source_path=rel.replace("\\", "/"),
                    clean_status="indexed",
                    extension=ext or "",
                    original_type="agency_repo_file",
                )

        self.add_event(
            agent=agent,
            run_id="registry_batch",
            kind="register_directory",
            payload={"root": root, "files_hashed": files},
        )
        return {"root": root, "files_hashed": files}


def main() -> int:
    parser = argparse.ArgumentParser(description="Chariot_Registry SQLite manager")
    parser.add_argument("--db", default=None, help="自訂 DB 路徑（預設 04_Workflows/Chariot_Registry.db）")
    parser.add_argument("--migrate-from", help="從指定文字檔遷入既有 SHA256 雜湊")
    parser.add_argument("--register-dir", help="遞迴登錄目錄內檔案 SHA256 至 SQLite")
    parser.add_argument(
        "--agent-label",
        default="Chariot_Registry_CLI",
        help="register-dir 時寫入 content_hashes.agent",
    )
    parser.add_argument("--count", action="store_true", help="顯示總筆數")
    args = parser.parse_args()
    get_tang_gov_root()
    reg = Chariot_Registry(db_path=args.db)
    out: Dict[str, Any] = {"db_path": reg.db_path}
    if args.migrate_from:
        out["migration"] = reg.migrate_from_textfile(args.migrate_from)
    if args.register_dir:
        out["register_directory"] = reg.register_directory_files(
            args.register_dir, agent=args.agent_label
        )
    if args.count or not args.migrate_from:
        out["count"] = reg.count()
        out["by_status"] = reg.count_by_status()
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
