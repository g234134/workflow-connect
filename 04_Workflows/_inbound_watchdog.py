"""_inbound_watchdog.py — 刑部 raw_inbound 生料哨兵（watchdog + 指紋入隊）。

啟動時可選擇先 bootstrap 全目錄；執行中對新檔以 subprocess 呼叫
`_register_fingerprints.py --files ... --clean-status pending`，並更新
`Status.json` 的 `business_metrics`。
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
_root = bootstrap_sys_path(_here)

from pathlib import Path
from gov_paths import get_artifact_path, resolve_agent_output_path  # type: ignore

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
    _watchdog_ok = True
except ImportError:
    FileSystemEventHandler = object  # fallback — _InboundHandler 變無操作
    Observer = None
    _watchdog_ok = False


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _raw_inbound_dir() -> str:
    return os.path.normpath(resolve_agent_output_path(None, "05_Temp_Cache", "raw_inbound"))


def _lock_path() -> str:
    return os.path.join(_here, ".inbound_watchdog.lock")


def _try_acquire_lock() -> bool:
    """單例：若 lock 內 PID 仍存活則退出。"""
    lp = _lock_path()
    if os.path.isfile(lp):
        try:
            with open(lp, "r", encoding="utf-8") as f:
                j = json.load(f)
            old = int(j.get("pid", 0))
            if old > 0:
                try:
                    import psutil  # type: ignore

                    if psutil.pid_exists(old):
                        return False
                except Exception:
                    # 無 psutil 時以 os.kill 探活（Windows 亦可用）
                    try:
                        os.kill(old, 0)
                        return False
                    except OSError:
                        pass
        except Exception:
            pass
    payload = {"pid": os.getpid(), "since": _utc_iso()}
    with open(lp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return True


def _release_lock() -> None:
    try:
        if os.path.isfile(_lock_path()):
            with open(_lock_path(), "r", encoding="utf-8") as f:
                j = json.load(f)
            if int(j.get("pid", 0)) == os.getpid():
                os.remove(_lock_path())
    except OSError:
        pass


def _merge_status_business_metrics(
    *,
    disk_files: int,
    bootstrap: Dict[str, Any],
    last_files: Optional[List[str]] = None,
) -> None:
    status_path = get_artifact_path("status_json")
    try:
        with open(status_path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
    except Exception:
        data = {"schema_version": "1.0", "updated_at": _utc_iso(), "runs": [], "telegram_running": []}

    from Chariot_Registry import Chariot_Registry  # type: ignore

    reg = Chariot_Registry()
    pending_n = reg.count_raw_inbound_pending()
    metrics = data.get("business_metrics") or {}
    metrics.setdefault("schema_version", "1.0")
    metrics["potential_case_sources"] = pending_n
    if "estimated_roi_rate" not in metrics:
        metrics["estimated_roi_rate"] = None
    iw = metrics.get("inbound_watchdog") or {}
    iw["version"] = "v2.55"
    iw["raw_inbound_dir_resolved"] = True
    iw["disk_file_count"] = disk_files
    iw["registry_raw_inbound_rows"] = reg.count_raw_inbound_rows()
    iw["registry_pending_raw_inbound"] = pending_n
    iw["last_bootstrap_at"] = bootstrap.get("at")
    iw["last_bootstrap_outcomes"] = bootstrap.get("outcomes", {})
    iw["last_bootstrap_disk_files"] = bootstrap.get("disk_files", 0)
    if last_files:
        iw["last_file_events"] = last_files[-32:]
    metrics["inbound_watchdog"] = iw
    data["business_metrics"] = metrics
    data["updated_at"] = _utc_iso()
    tmp = status_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, status_path)


def _count_disk_files(root: str) -> int:
    n = 0
    skip = {"__pycache__", ".git"}
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in skip]
        for fn in fns:
            fp = os.path.join(dp, fn)
            if os.path.isfile(fp):
                n += 1
    return n


def _run_register_files(paths: List[str], run_id: str) -> int:
    if not paths:
        return 0
    script = os.path.join(_here, "_register_fingerprints.py")
    cmd = [
        sys.executable,
        script,
        "--files",
        *paths,
        "--label",
        "raw_inbound",
        "--clean-status",
        "pending",
        "--run-id",
        run_id,
        "--agent",
        "inbound_watchdog_v2_55",
    ]
    r = subprocess.run(cmd, cwd=_here, capture_output=True, text=True, encoding="utf-8", errors="replace")
    sys.stdout.write(r.stdout or "")
    sys.stderr.write(r.stderr or "")
    return int(r.returncode)


class _InboundHandler(FileSystemEventHandler):
    def __init__(self, *, raw_root: str, debounce_s: float, on_flush) -> None:
        super().__init__()
        self._raw_root = os.path.normpath(raw_root)
        self._debounce_s = debounce_s
        self._on_flush = on_flush
        self._pending: Set[str] = set()
        self._lock = threading.Lock()
        self._timer: Optional[threading.Timer] = None

    def _schedule(self) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce_s, self._flush)
            self._timer.daemon = True
            self._timer.start()

    def _flush(self) -> None:
        with self._lock:
            paths = sorted(self._pending)
            self._pending.clear()
            self._timer = None
        if paths:
            self._on_flush(paths)

    def on_created(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.is_directory:
            return
        path = os.path.normpath(getattr(event, "src_path", ""))
        if not path.startswith(self._raw_root):
            return
        if not self._stable_file(path):
            return
        with self._lock:
            self._pending.add(path)
        self._schedule()

    def on_moved(self, event) -> None:  # type: ignore[no-untyped-def]
        dest = getattr(event, "dest_path", None)
        if not dest or event.is_directory:
            return
        path = os.path.normpath(dest)
        if not path.startswith(self._raw_root):
            return
        if not self._stable_file(path):
            return
        with self._lock:
            self._pending.add(path)
        self._schedule()

    @staticmethod
    def _stable_file(path: str, attempts: int = 25, delay: float = 0.15) -> bool:
        for _ in range(attempts):
            try:
                if os.path.isfile(path) and os.path.getsize(path) >= 0:
                    with open(path, "rb") as f:
                        f.read(1)
                    return True
            except OSError:
                pass
            time.sleep(delay)
        return False


def bootstrap_scan(raw_root: str) -> Dict[str, Any]:
    """全目錄走 `_register_fingerprints.py --dir ... --clean-status pending`（不降級 indexed）。"""
    script = os.path.join(_here, "_register_fingerprints.py")
    rid = f"inbound_bootstrap_{uuid.uuid4().hex[:12]}"
    cmd = [
        sys.executable,
        script,
        "--dir",
        raw_root,
        "--label",
        "raw_inbound",
        "--clean-status",
        "pending",
        "--run-id",
        rid,
        "--agent",
        "inbound_watchdog_v2_55",
    ]
    r = subprocess.run(cmd, cwd=_here, capture_output=True, text=True, encoding="utf-8", errors="replace")
    sys.stdout.write(r.stdout or "")
    sys.stderr.write(r.stderr or "")
    disk_n = _count_disk_files(raw_root)
    outcomes: Dict[str, int] = {}
    try:
        block = (r.stdout or "").split("---- 指紋補登 ----")[-1].strip()
        if block.startswith("{"):
            j = json.loads(block)
            outcomes = j.get("outcomes") or {}
    except Exception:
        outcomes = {}
    return {
        "at": _utc_iso(),
        "returncode": r.returncode,
        "disk_files": disk_n,
        "outcomes": outcomes,
    }


def check_inbox(
    inbox_path: str | None = None,
    output_path: str | None = None,
) -> dict:
    """掃描 inbox 資料夾，回傳新檔案清單（原 check_inbox.py 核心邏輯）。"""
    INBOX = Path(inbox_path or "D:/大唐三省六部/05_Temp_Cache/inbox")
    OUTPUT = Path(output_path or "D:/大唐三省六部/05_Temp_Cache/output")
    LOG = INBOX / "check_log.json"
    EXTENSIONS = {'.xlsx', '.xls', '.csv'}

    if not INBOX.exists():
        return {"status": "empty", "files": [], "message": "Inbox folder not found"}

    files = []
    for f in INBOX.iterdir():
        if f.is_file() and f.suffix.lower() in EXTENSIONS:
            stat = f.stat()
            files.append({
                "name": f.name,
                "size_kb": round(stat.st_size / 1024, 1),
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "path": str(f),
            })

    files.sort(key=lambda x: x["modified"], reverse=True)
    result = {
        "status": "has_work" if files else "empty",
        "count": len(files),
        "files": files,
        "timestamp": _utc_iso(),
    }

    # 存 log
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="刑部 raw_inbound 生料哨兵")
    parser.add_argument("--debounce", type=float, default=1.75, help="事件合併秒數")
    parser.add_argument("--no-bootstrap", action="store_true", help="啟動時不掃描全目錄")
    parser.add_argument("--bootstrap-only", action="store_true", help="僅執行一次 bootstrap 後退出")
    parser.add_argument("--skip-lock", action="store_true", help="略過單例 lock（除錯用）")
    parser.add_argument("--inbox-check", action="store_true", help="單次掃描 inbox 後退出（合併自 check_inbox.py）")
    args = parser.parse_args()

    if args.inbox_check:
        r = check_inbox()
        if r["status"] == "has_work":
            print(f"📬 收到 {r['count']} 個新檔案：")
            for f in r["files"]:
                print(f"  - {f['name']} ({f['size_kb']} KB)")
        else:
            print("📭 目前沒有新工作")
        return 0

    raw_root = _raw_inbound_dir()
    os.makedirs(raw_root, exist_ok=True)

    if not args.skip_lock and not _try_acquire_lock():
        print("[ERR] 已有 inbound_watchdog 實例在執行（見 04_Workflows/.inbound_watchdog.lock）", file=sys.stderr)
        return 3

    boot: Dict[str, Any] = {"at": None, "returncode": 0, "disk_files": 0, "outcomes": {}}
    try:
        if not args.no_bootstrap or args.bootstrap_only:
            boot = bootstrap_scan(raw_root)
        disk_n = _count_disk_files(raw_root)
        _merge_status_business_metrics(
            disk_files=disk_n,
            bootstrap=boot,
        )
        if args.bootstrap_only:
            return 0 if boot.get("returncode", 0) == 0 else 1

        if not _watchdog_ok:
            print("[ERR] 需要 watchdog 套件：pip install watchdog（inbox-check 與 bootstrap 仍可用）", file=sys.stderr)
            return 2

        def on_flush(paths: List[str]) -> None:
            rid = f"inbound_evt_{uuid.uuid4().hex[:12]}"
            rc = _run_register_files(paths, rid)
            disk_n2 = _count_disk_files(raw_root)
            _merge_status_business_metrics(
                disk_files=disk_n2,
                bootstrap=boot,
                last_files=paths,
            )
            if rc != 0:
                print(f"[WARN] _register_fingerprints 回傳 {rc}", file=sys.stderr)

        handler = _InboundHandler(raw_root=raw_root, debounce_s=args.debounce, on_flush=on_flush)
        obs = Observer()
        obs.schedule(handler, raw_root, recursive=True)
        obs.start()
        print(f"[OK] inbound_watchdog 監聽：{raw_root}")
        try:
            while True:
                time.sleep(1.0)
        except KeyboardInterrupt:
            obs.stop()
            obs.join(timeout=5.0)
        return 0
    finally:
        if not args.skip_lock:
            _release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
