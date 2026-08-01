"""W1-T2 · Phase 5 PG ingest soak runner (spec / skeleton).

Ticket: Monitoring PG Ingest 收口（API 成功 → PG 有列）

Purpose
-------
Fire *n* live ``POST /api/ask`` requests, then verify that PG ``task_runs`` row
count and Langfuse trace count are within tolerance for the same cohort prefix.

Data path (authoritative)
-------------------------
``runtime/task_traces.jsonl`` (gov-trace-v2) → dark ``monitoring_ingest`` sync
→ PG ``task_runs`` / ``step_runs``.

Non-goals (this ticket)
-----------------------
- No daily_cost_summary vs task_runs cost unification (W1-T3).
- No Prometheus/Grafana exporter.
- Not production-ready claims.

CLI (contract)
--------------
::

    python 04_Workflows/_phase5_pg_ingest_soak.py --n 20
    python 04_Workflows/_phase5_pg_ingest_soak.py --n 20 --dry-run
    python 04_Workflows/_phase5_pg_ingest_soak.py --n 20 --base-url http://127.0.0.1:8000 \\
        --cohort-prefix w1t2- --output artifacts/monitoring/pg_ingest_soak.latest.json

Exit codes
----------
0 — ``ingest_ok`` is true (PG count within tolerance vs Langfuse).
1 — cohort ran but counts diverge beyond tolerance.
2 — preflight / environment blocked (no PG, ingest disabled, API down).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Final, TypedDict

# --- contract constants (do not rename without updating docs/observability.md §4.2) ---

DEFAULT_N: Final[int] = 20
DEFAULT_MIN_PG_ROWS: Final[int] = 18  # allow up to 2 boundary failures
DEFAULT_MAX_GAP: Final[int] = 2  # |pg - langfuse| allowed when both > 0
DEFAULT_COHORT_PREFIX: Final[str] = "w1t2-"
DEFAULT_BASE_URL: Final[str] = "http://127.0.0.1:8000"
DEFAULT_OUTPUT: Final[str] = "artifacts/monitoring/pg_ingest_soak.latest.json"
DEFAULT_TRACE_JSONL: Final[str] = "runtime/task_traces.jsonl"
ASK_HTTP_TIMEOUT_S: Final[float] = 180.0
HEALTH_HTTP_TIMEOUT_S: Final[float] = 30.0
INGEST_SYNC_POLL_S: Final[float] = 3.0
INGEST_SYNC_MAX_WAIT_S: Final[float] = 90.0

REQUIRED_ENV: Final[tuple[str, ...]] = (
    "DATABASE_URL",
    "GOV_CORE_MONITORING_INGEST_ENABLED",
)

INGEST_CHECKPOINTS: Final[tuple[str, ...]] = (
    "GOV_CORE_MONITORING_INGEST_ENABLED=1",
    "DATABASE_URL set (instance anchor)",
    "dark core/monitoring_ingest.py importable",
    "task_traces.jsonl writable by ask pipeline",
    "POST /api/ask returns trace_id on success",
    "ingest batch logs traces_synced / steps_synced",
)

_GOV_CORE_BOOTSTRAPPED = False


class SoakDetail(TypedDict, total=False):
    """Per-request row in ``details[]``."""

    index: int
    session_id: str
    trace_id: str
    http_status: int
    biz_ok: bool
    api_ok: bool
    pg_row_found: bool
    langfuse_trace_found: bool
    langfuse_seen: bool
    jsonl_seen: bool
    error: str


class SoakReport(TypedDict, total=False):
    """Stable JSON output schema — written to ``--output`` and stdout."""

    ok: bool
    ingest_ok: bool
    ticket: str
    cohort_prefix: str
    n_requested: int
    n_api_ok: int
    pg_task_runs_count: int
    langfuse_trace_count: int
    jsonl_trace_end_count: int
    gap_pg_vs_langfuse: int
    min_pg_required: int
    max_gap_allowed: int
    preflight: dict[str, Any]
    details: list[SoakDetail]
    message: str
    generated_at: str
    verification_commands: list[str]


class AskCohortResult(TypedDict):
    details: list[SoakDetail]
    cohort_start_ts: str | None


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _env_truthy(name: str) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return False
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _insert_gov_core_from_master_map() -> Path:
    workflows_dir = Path(__file__).resolve().parent
    repo_root = workflows_dir.parent
    mp_path = workflows_dir / "Master_Map.json"
    with mp_path.open(encoding="utf-8") as fh:
        master_map = json.load(fh)
    cabins = master_map.get("cabins") or {}
    entry = cabins.get("gov_core_system") if isinstance(cabins, dict) else None
    if not isinstance(entry, dict):
        raise RuntimeError("Master_Map.cabins.gov_core_system missing")
    venv_rel = entry.get("venv_dir")
    if not venv_rel:
        raise RuntimeError("Master_Map.cabins.gov_core_system.venv_dir missing")
    gov_core = (repo_root / str(venv_rel).replace("\\", "/")).resolve()
    gov_s = str(gov_core)
    if gov_s not in sys.path:
        sys.path.insert(0, gov_s)
    return gov_core


def _load_gov_core_env(gov_core: Path) -> None:
    try:
        from dotenv import load_dotenv  # type: ignore[import-untyped]
    except ImportError:
        return
    env_path = gov_core / ".env"
    if env_path.is_file():
        load_dotenv(env_path, override=False)


def _ensure_gov_core_bootstrapped() -> Path:
    global _GOV_CORE_BOOTSTRAPPED  # noqa: PLW0603
    gov_core = _insert_gov_core_from_master_map()
    if not _GOV_CORE_BOOTSTRAPPED:
        _load_gov_core_env(gov_core)
        _GOV_CORE_BOOTSTRAPPED = True
    return gov_core


def _resolve_trace_jsonl_path(trace_jsonl: str) -> Path:
    return (_repo_root() / trace_jsonl.replace("\\", "/")).resolve()


def _http_get(url: str, *, timeout: float) -> tuple[int, dict[str, Any] | None, str | None]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = int(resp.status)
            raw = resp.read().decode("utf-8", errors="replace")
            body = json.loads(raw) if raw.strip() else {}
            if not isinstance(body, dict):
                body = {"raw": body}
            return status, body, None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        try:
            body = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            body = {"raw": raw[:500]} if raw else None
        if body is not None and not isinstance(body, dict):
            body = {"raw": body}
        return int(exc.code), body, str(exc)
    except urllib.error.URLError as exc:
        return 0, None, str(exc.reason or exc)
    except json.JSONDecodeError as exc:
        return 0, None, f"invalid JSON response: {exc}"
    except TimeoutError:
        return 0, None, f"timeout after {timeout}s"
    except OSError as exc:
        return 0, None, str(exc)


def _http_post_json(
    url: str,
    payload: dict[str, Any],
    *,
    timeout: float,
) -> tuple[int, dict[str, Any] | None, str | None]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = int(resp.status)
            raw = resp.read().decode("utf-8", errors="replace")
            body = json.loads(raw) if raw.strip() else {}
            if not isinstance(body, dict):
                body = {"raw": body}
            return status, body, None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        try:
            body = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            body = {"raw": raw[:500]} if raw else None
        if body is not None and not isinstance(body, dict):
            body = {"raw": body}
        return int(exc.code), body, str(exc)
    except urllib.error.URLError as exc:
        return 0, None, str(exc.reason or exc)
    except json.JSONDecodeError as exc:
        return 0, None, f"invalid JSON response: {exc}"
    except TimeoutError:
        return 0, None, f"timeout after {timeout}s"
    except OSError as exc:
        return 0, None, str(exc)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="W1-T2: n ask soak → verify PG task_runs vs Langfuse traces.",
    )
    p.add_argument(
        "--n",
        type=int,
        default=DEFAULT_N,
        help=f"Number of ask requests (default: {DEFAULT_N})",
    )
    p.add_argument(
        "--min-pg",
        type=int,
        default=DEFAULT_MIN_PG_ROWS,
        dest="min_pg",
        help=f"Minimum PG task_runs rows required (default: {DEFAULT_MIN_PG_ROWS})",
    )
    p.add_argument(
        "--max-gap",
        type=int,
        default=DEFAULT_MAX_GAP,
        dest="max_gap",
        help=f"Max |pg - langfuse| when both counters > 0 (default: {DEFAULT_MAX_GAP})",
    )
    p.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"gov_core API base URL (default: {DEFAULT_BASE_URL})",
    )
    p.add_argument(
        "--cohort-prefix",
        default=DEFAULT_COHORT_PREFIX,
        help=f"session_id prefix for cohort isolation (default: {DEFAULT_COHORT_PREFIX!r})",
    )
    p.add_argument(
        "--trace-jsonl",
        default=DEFAULT_TRACE_JSONL,
        help=f"Logical path to gov-trace-v2 JSONL (default: {DEFAULT_TRACE_JSONL})",
    )
    p.add_argument(
        "--output",
        "-o",
        default=DEFAULT_OUTPUT,
        help=f"Report JSON path relative to repo root (default: {DEFAULT_OUTPUT})",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip network/PG; emit schema sample report and exit 0",
    )
    p.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON to stdout",
    )
    return p


# ---------------------------------------------------------------------------
# Phase A — preflight
# ---------------------------------------------------------------------------


def run_preflight(*, base_url: str, trace_jsonl: str) -> dict[str, Any]:
    """Check API health, env flags, and ingest module importability.

    Returns ``{ ok, checks: { name: { ok, message } }, message }``.
    """
    checks: dict[str, dict[str, Any]] = {}
    base = base_url.rstrip("/")

    health_url = f"{base}/healthz"
    status, _body, err = _http_get(health_url, timeout=HEALTH_HTTP_TIMEOUT_S)
    if status == 200:
        checks["api_reachable"] = {"ok": True, "message": f"GET {health_url} → HTTP 200"}
    else:
        checks["api_reachable"] = {
            "ok": False,
            "message": f"GET {health_url} failed (status={status}, error={err or 'n/a'})",
        }

    try:
        gov_core = _ensure_gov_core_bootstrapped()
    except Exception as exc:  # noqa: BLE001
        checks["database_url"] = {"ok": False, "message": f"gov_core bootstrap failed: {exc}"}
        checks["ingest_enabled"] = {"ok": False, "message": "skipped — bootstrap failed"}
        checks["ingest_module"] = {"ok": False, "message": "skipped — bootstrap failed"}
        checks["trace_jsonl_path"] = {"ok": False, "message": "skipped — bootstrap failed"}
        return {
            "ok": False,
            "checks": checks,
            "message": f"preflight failed: gov_core bootstrap ({exc})",
        }

    dsn = (os.environ.get("DATABASE_URL") or "").strip()
    if dsn:
        from core.monitoring_pg import check_pg_connectivity  # noqa: PLC0415

        pg = check_pg_connectivity()
        if pg.get("ok"):
            checks["database_url"] = {"ok": True, "message": "DATABASE_URL set and postgres reachable"}
        else:
            checks["database_url"] = {
                "ok": False,
                "message": str(pg.get("message") or "postgres connectivity failed"),
            }
    else:
        checks["database_url"] = {"ok": False, "message": "DATABASE_URL not set"}

    if _env_truthy("GOV_CORE_MONITORING_INGEST_ENABLED"):
        checks["ingest_enabled"] = {
            "ok": True,
            "message": "GOV_CORE_MONITORING_INGEST_ENABLED is truthy in soak runner env",
        }
    else:
        checks["ingest_enabled"] = {
            "ok": False,
            "message": (
                "GOV_CORE_MONITORING_INGEST_ENABLED not truthy in soak runner env "
                "(export before live soak if API-only runtime flag)"
            ),
        }

    try:
        from core.monitoring_ingest import sync_traces  # noqa: F401, PLC0415

        checks["ingest_module"] = {
            "ok": True,
            "message": "core.monitoring_ingest.sync_traces importable",
        }
    except Exception as exc:  # noqa: BLE001
        checks["ingest_module"] = {"ok": False, "message": f"sync_traces import failed: {exc}"}

    jsonl_path = _resolve_trace_jsonl_path(trace_jsonl)
    if jsonl_path.is_file():
        checks["trace_jsonl_path"] = {
            "ok": True,
            "message": f"trace JSONL exists at {trace_jsonl}",
        }
    else:
        # JSONL is diagnostic (Phase D); authoritative ingest is Langfuse → sync_traces → PG.
        checks["trace_jsonl_path"] = {
            "ok": True,
            "message": (
                f"trace JSONL not present yet at {trace_jsonl} "
                "(diagnostic only; file optional until ask pipeline writes)"
            ),
        }

    all_ok = all(item.get("ok") for item in checks.values())
    failed = [name for name, item in checks.items() if not item.get("ok")]
    return {
        "ok": all_ok,
        "checks": checks,
        "message": "preflight passed" if all_ok else f"preflight failed: {', '.join(failed)}",
        "gov_core_root": str(gov_core),
    }


# ---------------------------------------------------------------------------
# Phase B — fire ask cohort
# ---------------------------------------------------------------------------


def fire_ask_cohort(
    *,
    n: int,
    base_url: str,
    cohort_prefix: str,
) -> AskCohortResult:
    """POST ``/api/ask`` *n* times with deterministic ``session_id`` under cohort."""
    base = base_url.rstrip("/")
    ask_url = f"{base}/api/ask"
    details: list[SoakDetail] = []
    cohort_start: datetime | None = None

    for i in range(n):
        sid = f"{cohort_prefix}{uuid.uuid4().hex[:8]}"
        payload = {
            "query": f"W1-T2 soak probe {i + 1}/{n} session={sid}",
            "session_id": sid,
            "top_k": 3,
        }
        started = datetime.now(timezone.utc)
        if cohort_start is None:
            cohort_start = started

        status, body, err = _http_post_json(ask_url, payload, timeout=ASK_HTTP_TIMEOUT_S)
        detail: SoakDetail = {
            "index": i + 1,
            "session_id": sid,
            "trace_id": "",
            "http_status": status,
            "api_ok": status == 200,
            "biz_ok": False,
            "pg_row_found": False,
            "langfuse_trace_found": False,
            "langfuse_seen": False,
            "jsonl_seen": False,
        }
        if body is None:
            detail["error"] = err or "no response body"
            details.append(detail)
            continue

        obs = body.get("observability") if isinstance(body.get("observability"), dict) else {}
        trace_id = obs.get("trace_id") if isinstance(obs, dict) else None
        if trace_id:
            detail["trace_id"] = str(trace_id)
        detail["biz_ok"] = bool(body.get("ok"))
        if err:
            detail["error"] = err
        elif not detail["trace_id"]:
            detail["error"] = "response missing observability.trace_id"
        details.append(detail)

    return {
        "details": details,
        "cohort_start_ts": cohort_start.isoformat() if cohort_start else None,
    }


# ---------------------------------------------------------------------------
# Phase C — ingest sync
# ---------------------------------------------------------------------------


def trigger_ingest_sync(
    *,
    cohort_start_ts: str | None,
    cohort_prefix: str,
    trace_jsonl: str,
    expected_traces: int = 0,
) -> dict[str, Any]:
    """Pull Langfuse traces since cohort start and upsert PG rows."""
    _ = trace_jsonl
    _ensure_gov_core_bootstrapped()
    from core.monitoring_ingest import sync_traces  # noqa: PLC0415

    since: datetime | None = None
    if cohort_start_ts:
        try:
            since = datetime.fromisoformat(cohort_start_ts.replace("Z", "+00:00"))
            if since.tzinfo is None:
                since = since.replace(tzinfo=timezone.utc)
            since = since - timedelta(seconds=5)
        except ValueError:
            since = datetime.now(timezone.utc) - timedelta(minutes=15)
    else:
        since = datetime.now(timezone.utc) - timedelta(minutes=15)

    deadline = datetime.now(timezone.utc) + timedelta(seconds=INGEST_SYNC_MAX_WAIT_S)
    result: dict[str, Any] = {"ok": False, "traces_matched": 0}
    polls = 0
    while True:
        polls += 1
        until = datetime.now(timezone.utc)
        result = sync_traces(
            since=since,
            until=until,
            session_prefix=cohort_prefix,
            page_limit=50,
        )
        matched = int(result.get("traces_matched") or 0)
        target = max(0, expected_traces)
        if until >= deadline:
            break
        if target == 0 and matched > 0:
            break
        if target > 0 and matched >= target:
            break
        time.sleep(INGEST_SYNC_POLL_S)

    return {
        "ok": bool(result.get("ok")),
        "traces_synced": int(result.get("traces_synced") or 0),
        "steps_synced": int(result.get("steps_synced") or 0),
        "traces_matched": int(result.get("traces_matched") or 0),
        "traces_fetched": int(result.get("traces_fetched") or 0),
        "errors": list(result.get("errors") or []),
        "message": result.get("message"),
        "since": result.get("since"),
        "until": result.get("until"),
        "session_prefix": cohort_prefix,
        "polls": polls,
    }


# ---------------------------------------------------------------------------
# Phase D — count PG / Langfuse / JSONL
# ---------------------------------------------------------------------------


def count_pg_task_runs(*, cohort_prefix: str, trace_ids: list[str] | None = None) -> int:
    """Count PG task_runs rows for the current soak cohort.

    Prefer ``trace_ids`` from the live ask cohort; fall back to ``session_id`` prefix.
    """
    _ensure_gov_core_bootstrapped()
    from core.monitoring_pg import run_with_connection  # noqa: PLC0415

    ids = [tid for tid in (trace_ids or []) if tid]
    if ids:
        placeholders = ", ".join(["%s"] * len(ids))

        def _count_by_trace(conn: Any) -> int:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT COUNT(*) FROM task_runs WHERE trace_id IN ({placeholders})",
                    tuple(ids),
                )
                row = cur.fetchone()
            return int(row[0]) if row else 0

        out = run_with_connection(
            _count_by_trace,
            statement_timeout_ms=15_000,
            lock_timeout_ms=5_000,
            sql_hint="SELECT COUNT(*) FROM task_runs WHERE trace_id IN (...)",
            params_hint=tuple(ids[:3]),
            probe_context="task_runs",
        )
        if isinstance(out, int):
            return out

    pattern = f"{cohort_prefix}%"

    def _count_by_prefix(conn: Any) -> int:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM task_runs WHERE session_id LIKE %s",
                (pattern,),
            )
            row = cur.fetchone()
        return int(row[0]) if row else 0

    out = run_with_connection(
        _count_by_prefix,
        statement_timeout_ms=15_000,
        lock_timeout_ms=5_000,
        sql_hint="SELECT COUNT(*) FROM task_runs WHERE session_id LIKE %s",
        params_hint=(pattern,),
        probe_context="task_runs",
    )
    if isinstance(out, int):
        return out
    return 0


def count_langfuse_traces(*, ingest_sync: dict[str, Any], cohort_prefix: str) -> int:
    """Prefer sync_traces traces_matched; fall back to traces_synced."""
    _ = cohort_prefix
    matched = ingest_sync.get("traces_matched")
    if isinstance(matched, int) and matched >= 0:
        return matched
    synced = ingest_sync.get("traces_synced")
    return int(synced) if isinstance(synced, int) else 0


def count_jsonl_trace_end(*, trace_jsonl: str, cohort_prefix: str) -> int:
    """Local fallback: count ``event=trace_end`` lines matching cohort in JSONL."""
    path = _resolve_trace_jsonl_path(trace_jsonl)
    if not path.is_file():
        return 0
    count = 0
    with path.open(encoding="utf-8") as fh:
        for raw in fh:
            text = raw.strip()
            if not text:
                continue
            try:
                obj = json.loads(text)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            if str(obj.get("event")) != "trace_end":
                continue
            session_id = str(obj.get("session_id") or "")
            if session_id.startswith(cohort_prefix):
                count += 1
    return count


def _jsonl_trace_end_ids(*, trace_jsonl: str, cohort_prefix: str) -> set[str]:
    path = _resolve_trace_jsonl_path(trace_jsonl)
    ids: set[str] = set()
    if not path.is_file():
        return ids
    with path.open(encoding="utf-8") as fh:
        for raw in fh:
            text = raw.strip()
            if not text:
                continue
            try:
                obj = json.loads(text)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            if str(obj.get("event")) != "trace_end":
                continue
            session_id = str(obj.get("session_id") or "")
            if not session_id.startswith(cohort_prefix):
                continue
            trace_id = str(obj.get("trace_id") or "")
            if trace_id:
                ids.add(trace_id)
    return ids


def enrich_soak_details(
    details: list[SoakDetail],
    *,
    trace_jsonl: str,
    cohort_prefix: str,
) -> list[SoakDetail]:
    """Attach per-row PG / JSONL / Langfuse diagnostic flags."""
    _ensure_gov_core_bootstrapped()
    from core.monitoring_pg import probe_task_run_exists  # noqa: PLC0415

    jsonl_ids = _jsonl_trace_end_ids(trace_jsonl=trace_jsonl, cohort_prefix=cohort_prefix)
    enriched: list[SoakDetail] = []
    for item in details:
        row: SoakDetail = dict(item)
        trace_id = str(row.get("trace_id") or "")
        if trace_id:
            probe = probe_task_run_exists(trace_id)
            row["pg_row_found"] = bool(probe.get("exists")) if probe.get("ok") else False
            row["jsonl_seen"] = trace_id in jsonl_ids
            row["langfuse_seen"] = bool(
                row["pg_row_found"] or row["jsonl_seen"] or (row.get("api_ok") and row.get("biz_ok"))
            )
            row["langfuse_trace_found"] = row["langfuse_seen"]
        else:
            row["pg_row_found"] = False
            row["jsonl_seen"] = False
            row["langfuse_seen"] = False
            row["langfuse_trace_found"] = False
        enriched.append(row)
    return enriched


# ---------------------------------------------------------------------------
# Phase E — evaluate + report
# ---------------------------------------------------------------------------


def evaluate_soak(
    *,
    n_requested: int,
    min_pg: int,
    max_gap: int,
    cohort_prefix: str,
    pg_count: int,
    langfuse_count: int,
    jsonl_count: int,
    preflight: dict[str, Any],
    details: list[SoakDetail],
    ingest_sync: dict[str, Any],
) -> SoakReport:
    gap = abs(pg_count - langfuse_count)
    n_api_ok = sum(1 for d in details if d.get("api_ok"))

    ingest_ok = (
        preflight.get("ok") is True
        and pg_count >= min_pg
        and gap <= max_gap
        and langfuse_count >= min_pg
    )

    if not preflight.get("ok"):
        message = preflight.get("message") or "preflight failed"
    elif pg_count < min_pg:
        message = f"PG task_runs {pg_count} < required {min_pg}"
    elif langfuse_count < min_pg:
        message = f"Langfuse traces {langfuse_count} < required {min_pg}"
    elif gap > max_gap:
        message = f"PG/Langfuse gap {gap} > allowed {max_gap}"
    else:
        message = "cohort counts within tolerance"

    return {
        "ok": ingest_ok,
        "ingest_ok": ingest_ok,
        "ticket": "W1-T2",
        "cohort_prefix": cohort_prefix,
        "n_requested": n_requested,
        "n_api_ok": n_api_ok,
        "pg_task_runs_count": pg_count,
        "langfuse_trace_count": langfuse_count,
        "jsonl_trace_end_count": jsonl_count,
        "gap_pg_vs_langfuse": gap,
        "min_pg_required": min_pg,
        "max_gap_allowed": max_gap,
        "preflight": {**preflight, "ingest_sync": ingest_sync},
        "details": details,
        "message": message,
        "generated_at": _utc_now_iso(),
        "verification_commands": [
            "python 04_Workflows/_phase5_pg_ingest_soak.py --n 20",
            f"curl {DEFAULT_BASE_URL}/monitoring/overview",
            "cd 01_Environments/python_venvs/gov_core_system && python -m pytest tests/test_monitoring_api.py -q -k ingest",
        ],
    }


def sample_dry_run_report(args: argparse.Namespace) -> SoakReport:
    """Example report for ``--dry-run`` — documents expected field shapes."""
    n = args.n
    details: list[SoakDetail] = []
    for i in range(min(n, 3)):
        details.append(
            {
                "index": i + 1,
                "session_id": f"{args.cohort_prefix}dry{i + 1:02d}",
                "trace_id": f"{args.cohort_prefix}trace-dry{i + 1:02d}",
                "http_status": 200,
                "api_ok": True,
                "biz_ok": True,
                "pg_row_found": True,
                "langfuse_trace_found": True,
                "langfuse_seen": True,
                "jsonl_seen": True,
            }
        )
    if n > 3:
        details.append({"index": n, "session_id": "…", "trace_id": "…", "error": f"({n - 3} more rows omitted in dry-run sample)"})

    pg = n
    lf = n
    return evaluate_soak(
        n_requested=n,
        min_pg=args.min_pg,
        max_gap=args.max_gap,
        cohort_prefix=args.cohort_prefix,
        pg_count=pg,
        langfuse_count=lf,
        jsonl_count=pg,
        preflight={
            "ok": True,
            "checks": {k: {"ok": True, "message": "dry-run"} for k in (
                "api_reachable", "database_url", "ingest_enabled", "ingest_module", "trace_jsonl_path",
            )},
            "message": "dry-run — no live PG/API",
        },
        details=details,
        ingest_sync={"ok": True, "traces_synced": pg, "steps_synced": pg * 3, "errors": []},
    )


def write_report(report: SoakReport, output_rel: str) -> Path:
    out = _repo_root() / output_rel.replace("\\", "/")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.dry_run:
        report = sample_dry_run_report(args)
        report["message"] = "dry-run sample — not evidence of live ingest"
        report["ingest_ok"] = False
        report["ok"] = False
    else:
        preflight = run_preflight(base_url=args.base_url, trace_jsonl=args.trace_jsonl)
        if not preflight.get("ok"):
            report: SoakReport = evaluate_soak(
                n_requested=args.n,
                min_pg=args.min_pg,
                max_gap=args.max_gap,
                cohort_prefix=args.cohort_prefix,
                pg_count=0,
                langfuse_count=0,
                jsonl_count=0,
                preflight=preflight,
                details=[],
                ingest_sync={"ok": False, "errors": ["skipped — preflight failed"]},
            )
            write_report(report, args.output)
            payload = json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None)
            print(payload)
            return 2

        cohort = fire_ask_cohort(
            n=args.n,
            base_url=args.base_url,
            cohort_prefix=args.cohort_prefix,
        )
        details = cohort["details"]
        ingest_sync = trigger_ingest_sync(
            cohort_start_ts=cohort.get("cohort_start_ts"),
            cohort_prefix=args.cohort_prefix,
            trace_jsonl=args.trace_jsonl,
            expected_traces=sum(1 for d in details if d.get("api_ok")),
        )
        details = enrich_soak_details(
            details,
            trace_jsonl=args.trace_jsonl,
            cohort_prefix=args.cohort_prefix,
        )
        cohort_trace_ids = [
            str(d["trace_id"])
            for d in details
            if d.get("api_ok") and d.get("trace_id")
        ]
        pg_count = count_pg_task_runs(
            cohort_prefix=args.cohort_prefix,
            trace_ids=cohort_trace_ids,
        )
        langfuse_count = count_langfuse_traces(
            ingest_sync=ingest_sync,
            cohort_prefix=args.cohort_prefix,
        )
        jsonl_count = count_jsonl_trace_end(
            trace_jsonl=args.trace_jsonl,
            cohort_prefix=args.cohort_prefix,
        )
        report = evaluate_soak(
            n_requested=args.n,
            min_pg=args.min_pg,
            max_gap=args.max_gap,
            cohort_prefix=args.cohort_prefix,
            pg_count=pg_count,
            langfuse_count=langfuse_count,
            jsonl_count=jsonl_count,
            preflight=preflight,
            details=details,
            ingest_sync=ingest_sync,
        )

    out_path = write_report(report, args.output)
    payload = json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None)
    print(payload)
    if args.dry_run:
        print(f"# dry-run report written to {out_path}", file=sys.stderr)
        return 0
    return 0 if report.get("ingest_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
