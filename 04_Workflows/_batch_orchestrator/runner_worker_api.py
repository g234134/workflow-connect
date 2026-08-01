"""HTTP Worker API runner for batch orchestrator (P8 toward-100).

Calls the real Worker HTTP endpoint (see ``worker_api.py``) instead of
``runner_mock`` simulated latency. Returns ``ExecutionResult`` list compatible
with collector / reporter.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Mapping, Sequence

from .prompt_builder import build_implementer_prompt
from .runner_mock import ExecutionResult
from .worker_api import DEFAULT_PATH, ENV_WORKER_API_URL, SCHEMA_VERSION

DEFAULT_TIMEOUT_SECONDS = 30


def resolve_worker_base_url(
    *,
    worker_base_url: str | None = None,
) -> str | None:
    """Resolve Worker API base URL from arg or env. No hard-coded disk paths."""
    if worker_base_url and str(worker_base_url).strip():
        return str(worker_base_url).strip().rstrip("/")
    env = os.getenv(ENV_WORKER_API_URL, "").strip().rstrip("/")
    return env or None


def _subtask_id(subtask: Mapping[str, Any], index: int) -> str:
    sid = str(subtask.get("subtask_id") or "").strip()
    return sid or f"anon-{index}"


def _post_json(url: str, payload: dict[str, Any], *, timeout: float) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            status = int(getattr(resp, "status", 200) or 200)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = {"ok": False, "message": raw or str(exc), "error": "http_error"}
        if not isinstance(body, dict):
            body = {"ok": False, "message": str(exc), "error": "http_error"}
        body.setdefault("ok", False)
        body.setdefault("http_status", int(exc.code))
        body.setdefault("error", "http_error")
        return body
    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "status": "failed",
            "message": f"worker API unreachable: {exc.reason}",
            "error": "url_error",
        }
    except TimeoutError:
        return {
            "ok": False,
            "status": "timeout",
            "message": "worker API timeout",
            "error": "timeout",
        }

    try:
        body = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {
            "ok": False,
            "status": "failed",
            "message": "worker API returned non-JSON",
            "error": "invalid_json",
            "http_status": status,
        }
    if not isinstance(body, dict):
        return {
            "ok": False,
            "status": "failed",
            "message": "worker API JSON must be an object",
            "error": "invalid_body",
            "http_status": status,
        }
    body.setdefault("http_status", status)
    return body


def _run_one(
    subtask: Mapping[str, Any],
    index: int,
    *,
    parent_frame: Mapping[str, Any] | None,
    run_url: str,
    timeout: float,
    build_prompt: bool,
    force_fail_ids: set[str],
) -> ExecutionResult:
    sid = _subtask_id(subtask, index)
    started = time.perf_counter()
    frame = dict(parent_frame or {})
    prompt: dict[str, Any] | None = None
    if build_prompt:
        prompt = build_implementer_prompt(dict(subtask), frame)

    payload: dict[str, Any] = {
        "subtask_id": sid,
        "subtask": dict(subtask),
        "parent_frame": frame,
        "force_fail": sid in force_fail_ids,
    }
    if prompt is not None:
        payload["prompt"] = prompt

    remote = _post_json(run_url, payload, timeout=timeout)
    elapsed_ms = round((time.perf_counter() - started) * 1000.0, 3)

    ok = bool(remote.get("ok"))
    status = str(remote.get("status") or ("success" if ok else "failed"))
    message = str(remote.get("message") or "")
    error = remote.get("error")
    if error is not None:
        error = str(error)

    remote_prompt = remote.get("prompt")
    if isinstance(remote_prompt, dict):
        prompt = remote_prompt

    return ExecutionResult(
        subtask_id=sid,
        ok=ok,
        status=status,
        latency_ms=float(remote.get("latency_ms") or elapsed_ms),
        message=message or ("worker_api ok" if ok else "worker_api failed"),
        prompt=prompt,
        error=error,
        extras={
            "runner": "worker_api",
            "schema_version": SCHEMA_VERSION,
            "external_http": True,
            "worker_url": run_url,
            "http_status": remote.get("http_status"),
        },
    )


def run_subtasks_worker_api(
    subtasks: list[dict],
    concurrency_limit: int = 2,
    *,
    worker_base_url: str | None = None,
    endpoint_path: str = DEFAULT_PATH,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    parent_frame: Mapping[str, Any] | None = None,
    build_prompt: bool = True,
    force_failures: Sequence[str] | None = None,
) -> list[ExecutionResult]:
    """Run subtasks via real Worker HTTP API.

    Fail-close when base URL is unset (arg and env both empty).
    """
    base = resolve_worker_base_url(worker_base_url=worker_base_url)
    if not base:
        return [
            ExecutionResult(
                subtask_id="config",
                ok=False,
                status="blocked",
                message=(
                    f"fail-close: set --worker-url or env {ENV_WORKER_API_URL} "
                    "for --mode worker_api"
                ),
                error="missing_worker_url",
                extras={"runner": "worker_api", "external_http": False},
            )
        ]

    if not isinstance(subtasks, list):
        return [
            ExecutionResult(
                subtask_id="invalid",
                ok=False,
                status="failed",
                message="subtasks must be a list",
                error="subtasks must be a list",
            )
        ]

    path = endpoint_path if endpoint_path.startswith("/") else f"/{endpoint_path}"
    run_url = f"{base}{path}"
    limit = max(1, int(concurrency_limit or 1))
    total = len(subtasks)
    if total == 0:
        return []

    force_ids = set(force_failures or [])
    results_by_index: dict[int, ExecutionResult] = {}

    def _job(idx: int, item: Any) -> tuple[int, ExecutionResult]:
        if not isinstance(item, Mapping):
            return idx, ExecutionResult(
                subtask_id=f"anon-{idx}",
                ok=False,
                status="failed",
                message="subtask must be a mapping",
                error="subtask must be a mapping",
            )
        return idx, _run_one(
            item,
            idx,
            parent_frame=parent_frame,
            run_url=run_url,
            timeout=float(timeout_seconds),
            build_prompt=build_prompt,
            force_fail_ids=force_ids,
        )

    with ThreadPoolExecutor(max_workers=limit) as pool:
        futures = [pool.submit(_job, i, st) for i, st in enumerate(subtasks)]
        for fut in as_completed(futures):
            idx, result = fut.result()
            results_by_index[idx] = result

    return [results_by_index[i] for i in range(total)]


def run_subtasks_worker_api_as_dicts(
    subtasks: list[dict],
    concurrency_limit: int = 2,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    return [
        r.to_dict()
        for r in run_subtasks_worker_api(subtasks, concurrency_limit, **kwargs)
    ]
