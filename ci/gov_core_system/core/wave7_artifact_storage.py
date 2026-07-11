"""
Wave 7 artifact storage and path governance.

Persists per-file envelopes, manifest.json, report.json (placeholder allowed),
and job-level failed/quarantine recovery. All returned paths are repo-relative
logical segments or ``w6://delivery/{job_id}/{kind}`` refs — never absolute paths.

Idempotency: same ``job_id`` + identical inputs fingerprint skips re-write.
On IO failure: partial state moved under job ``failed/`` and audit copied to
staging quarantine logical zone (last-good manifest optional if present).
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from core.schemas.envelope_v2 import _LEAKY_PATH_RE
from core.wave7_runner_env_bootstrap import bootstrap_runner_env

WAVE7_STORE_SCHEMA_VERSION = "wave7_artifact_storage_v0.1"
W6_DELIVERY_SCHEME = "w6://delivery"
W6_ARTIFACT_KINDS = frozenset({"manifest", "report_json", "report_md", "deliverables"})

ERR_BOOTSTRAP = "bootstrap_failed"
ERR_INVALID_JOB = "invalid_job_id"
ERR_INVALID_MODE = "invalid_mode"
ERR_IO = "io_error"
ERR_PATH_LEAK = "path_leak"

StoreMode = str  # "create" | "overwrite_stage" | "finalize"

_REPORT_PLACEHOLDER: dict[str, Any] = {
    "schema_version": "wave7_report_placeholder_v0.1",
    "status": "skeleton",
    "summary": {
        "accepted_units": None,
        "note": "report.summary production deferred to REPORT-SUMMARY-PRODUCER ticket",
    },
}

_FILENAME_SAFE_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _fail(
    *,
    code: str,
    message: str,
    paths_logical: dict[str, str] | None = None,
    artifact_refs: dict[str, str] | None = None,
    idempotent_hit: bool = False,
) -> dict[str, Any]:
    return {
        "ok": False,
        "artifact_refs": artifact_refs or {},
        "paths_logical": paths_logical or {},
        "idempotent_hit": idempotent_hit,
        "message": message,
        "error_code": code,
        "schema_version": WAVE7_STORE_SCHEMA_VERSION,
    }


def _ok(
    *,
    artifact_refs: dict[str, str],
    paths_logical: dict[str, str],
    idempotent_hit: bool = False,
    message: str = "artifacts_stored",
) -> dict[str, Any]:
    return {
        "ok": True,
        "artifact_refs": artifact_refs,
        "paths_logical": paths_logical,
        "idempotent_hit": idempotent_hit,
        "message": message,
        "error_code": None,
        "schema_version": WAVE7_STORE_SCHEMA_VERSION,
    }


def w6_logical_ref(job_id: str, kind: str) -> str:
    """R4 #H-2: ``w6://delivery/{job_id}/{artifact_kind}``."""
    if kind not in W6_ARTIFACT_KINDS:
        raise ValueError(f"unsupported w6 artifact_kind: {kind!r}")
    ref = f"{W6_DELIVERY_SCHEME}/{job_id}/{kind}"
    if len(ref) > 200:
        raise ValueError("w6 logical ref exceeds 200 characters")
    return ref


def _sanitize_job_id(job_id: str) -> str | None:
    text = str(job_id or "").strip()
    if not text or _LEAKY_PATH_RE.search(text):
        return None
    if ".." in text or "/" in text or "\\" in text:
        return None
    return text


def _sanitize_segment(name: str) -> str:
    cleaned = _FILENAME_SAFE_RE.sub("_", str(name).strip())
    return cleaned[:128] or "unnamed"


def _envelope_basename(envelope: Mapping[str, Any]) -> str:
    file_id = envelope.get("file_id")
    if file_id:
        return f"{_sanitize_segment(str(file_id))}.json"
    sha = envelope.get("content_sha256")
    if sha:
        return f"{_sanitize_segment(str(sha))}.json"
    raise ValueError("envelope requires file_id or content_sha256")


def _canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def compute_inputs_fingerprint(
    *,
    envelopes: Sequence[Mapping[str, Any]] | None,
    manifest: Mapping[str, Any] | None,
    report: Mapping[str, Any] | None,
    sku: str,
    mode: str,
) -> str:
    """Stable hash for idempotent re-run detection."""
    env_list = list(envelopes or [])
    env_names = sorted(_envelope_basename(e) for e in env_list)
    body = {
        "sku": str(sku or ""),
        "mode": mode,
        "envelope_names": env_names,
        "envelopes": [_sorted_dict(e) for e in env_list],
        "manifest": _sorted_dict(manifest) if manifest is not None else None,
        "report": _sorted_dict(report) if report is not None else None,
    }
    digest = hashlib.sha256(_canonical_json_bytes(body)).hexdigest()
    return digest


def _sorted_dict(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _sorted_dict(value[k]) for k in sorted(value.keys(), key=str)}
    if isinstance(value, list):
        return [_sorted_dict(item) for item in value]
    return value


def _assert_no_leaky_logical_path(value: str) -> None:
    """Repo-relative paths only; ``w6://`` refs are validated separately."""
    if not value or value.startswith(f"{W6_DELIVERY_SCHEME}/"):
        return
    if _LEAKY_PATH_RE.search(value):
        raise ValueError(f"path leak in logical output: {value!r}")


def _build_artifact_refs(job_id: str) -> dict[str, str]:
    return {
        "manifest": w6_logical_ref(job_id, "manifest"),
        "report_json": w6_logical_ref(job_id, "report_json"),
        "report_md": w6_logical_ref(job_id, "report_md"),
        "deliverables": w6_logical_ref(job_id, "deliverables"),
        "envelopes_dir": w6_logical_ref(job_id, "deliverables"),
    }


def _job_paths_logical(
    *,
    base_rel: str,
    job_id: str,
) -> dict[str, str]:
    root = f"{base_rel}/{job_id}".replace("\\", "/")
    paths = {
        "job_root": root,
        "manifest": f"{root}/manifest.json",
        "report_json": f"{root}/report.json",
        "report_md": f"{root}/report.md",
        "deliverables": f"{root}/deliverables",
        "envelopes_dir": f"{root}/envelopes",
        "failed": f"{root}/failed",
        "generation": f"{root}/.wave7_generation.json",
    }
    for path in paths.values():
        _assert_no_leaky_logical_path(path)
    return paths


def _read_generation(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        with path.open(encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    return doc if isinstance(doc, dict) else None


def _write_json_atomic(path: Path, payload: Any, *, writer: Callable[[Path, str], None] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    text += "\n"
    if writer is not None:
        writer(path, text)
        return
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _resolve_repo_root(repo_root: Path | None, start: Path | None) -> Path | None:
    if repo_root is not None:
        return repo_root.resolve()
    from core.repo_paths import find_repo_root

    found = find_repo_root(start=start)
    return found.resolve() if found is not None else None


def _resolve_paths(
    *,
    paths_resolved: dict[str, str] | None,
    repo_root: Path | None,
    start: Path | None,
) -> tuple[dict[str, str] | None, str | None]:
    if paths_resolved is not None:
        for key in ("staging_root", "delivery_root"):
            if key not in paths_resolved:
                return None, f"paths_resolved missing {key!r}"
        return paths_resolved, None

    boot = bootstrap_runner_env(check=False, start=start)
    if not boot.get("ok"):
        return None, str(boot.get("message") or ERR_BOOTSTRAP)
    resolved = boot.get("paths_resolved") or {}
    if not resolved.get("delivery_root") or not resolved.get("staging_root"):
        return None, "bootstrap paths_resolved incomplete"
    return resolved, None


def _quarantine_logical(staging_root: str, job_id: str) -> str:
    base = staging_root.replace("\\", "/").rstrip("/")
    path = f"{base}/quarantine/{job_id}"
    _assert_no_leaky_logical_path(path)
    return path


def _idempotent_hit(
    *,
    repo_root: Path,
    paths_logical: dict[str, str],
    fingerprint: str,
    require_manifest: bool,
) -> bool:
    gen_path = repo_root / paths_logical["generation"]
    gen = _read_generation(gen_path)
    if not gen or gen.get("fingerprint") != fingerprint:
        return False

    manifest_path = repo_root / paths_logical["manifest"]
    if require_manifest and not manifest_path.is_file():
        return False

    report_path = repo_root / paths_logical["report_json"]
    if not report_path.is_file():
        return False

    env_dir = repo_root / paths_logical["envelopes_dir"]
    if gen.get("envelope_count", 0) > 0 and not env_dir.is_dir():
        return False

    return True


def _recover_io_failure(
    *,
    repo_root: Path,
    paths_logical: dict[str, str],
    staging_root: str,
    job_id: str,
    reason: str,
    fingerprint: str,
) -> dict[str, str]:
    """Move partial job tree to failed/ and write quarantine audit."""
    job_abs = repo_root / paths_logical["job_root"]
    failed_rel = paths_logical["failed"]
    failed_abs = repo_root / failed_rel
    failed_abs.mkdir(parents=True, exist_ok=True)

    audit = {
        "schema_version": WAVE7_STORE_SCHEMA_VERSION,
        "job_id": job_id,
        "fingerprint": fingerprint,
        "failed_at": _utc_now_iso(),
        "reason": reason,
        "last_good_manifest": paths_logical["manifest"]
        if (repo_root / paths_logical["manifest"]).is_file()
        else None,
    }
    audit_path = failed_abs / "recovery_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    for name in ("manifest.json", "report.json", "report.md"):
        src = job_abs / name
        if src.is_file():
            dest = failed_abs / name
            try:
                shutil.move(str(src), str(dest))
            except OSError:
                pass

    env_src = job_abs / "envelopes"
    if env_src.is_dir():
        env_dest = failed_abs / "envelopes"
        try:
            if env_dest.exists():
                shutil.rmtree(env_dest)
            shutil.move(str(env_src), str(env_dest))
        except OSError:
            pass

    quar_rel = _quarantine_logical(staging_root, job_id)
    quar_abs = repo_root / quar_rel
    quar_abs.mkdir(parents=True, exist_ok=True)
    quar_audit = quar_abs / "recovery_audit.json"
    quar_audit.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    out = dict(paths_logical)
    out["quarantine"] = quar_rel
    out["failed_audit"] = f"{failed_rel}/recovery_audit.json"
    return out


def _write_envelopes(
    *,
    repo_root: Path,
    envelopes_dir_rel: str,
    envelopes: Sequence[Mapping[str, Any]],
    writer: Callable[[Path, str], None] | None,
) -> int:
    env_dir = repo_root / envelopes_dir_rel
    env_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for envelope in envelopes:
        name = _envelope_basename(envelope)
        target = env_dir / name
        payload = dict(envelope) if isinstance(envelope, Mapping) else envelope
        _write_json_atomic(target, payload, writer=writer)
        count += 1
    return count


def _copy_tree(src: Path, dest: Path) -> None:
    if not src.is_dir():
        return
    dest.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dest / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def store_wave7_artifacts(
    job_id: str,
    sku: str,
    *,
    envelopes: Sequence[Mapping[str, Any]] | None = None,
    manifest: Mapping[str, Any] | None = None,
    report: Mapping[str, Any] | None = None,
    mode: StoreMode = "create",
    paths_resolved: dict[str, str] | None = None,
    repo_root: Path | None = None,
    start: Path | None = None,
    json_writer: Callable[[Path, str], None] | None = None,
) -> dict[str, Any]:
    """
    Store Wave 7 job artifacts under governed logical paths.

    ``mode``:
    - ``create``: write under ``delivery_root/{job_id}/``
    - ``overwrite_stage``: write under ``staging_root/{job_id}/``
    - ``finalize``: promote ``staging_root/{job_id}/`` → ``delivery_root/{job_id}/``
    """
    safe_job = _sanitize_job_id(job_id)
    if not safe_job:
        return _fail(code=ERR_INVALID_JOB, message="invalid or leaky job_id")

    if mode not in ("create", "overwrite_stage", "finalize"):
        return _fail(code=ERR_INVALID_MODE, message=f"unsupported mode: {mode!r}")

    root = _resolve_repo_root(repo_root, start)
    if root is None:
        return _fail(code=ERR_BOOTSTRAP, message="repo root not found")

    resolved, boot_err = _resolve_paths(paths_resolved=paths_resolved, repo_root=root, start=start)
    if resolved is None:
        return _fail(code=ERR_BOOTSTRAP, message=boot_err or ERR_BOOTSTRAP)

    delivery_root = str(resolved["delivery_root"]).replace("\\", "/")
    staging_root = str(resolved["staging_root"]).replace("\\", "/")

    artifact_refs = _build_artifact_refs(safe_job)

    if mode == "overwrite_stage":
        base_rel = staging_root
    else:
        base_rel = delivery_root

    paths_logical = _job_paths_logical(base_rel=base_rel, job_id=safe_job)
    paths_logical["quarantine_root"] = _quarantine_logical(staging_root, safe_job)

    if mode == "finalize":
        staging_paths = _job_paths_logical(base_rel=staging_root, job_id=safe_job)
        staging_abs = root / staging_paths["job_root"]
        delivery_paths = _job_paths_logical(base_rel=delivery_root, job_id=safe_job)
        delivery_abs = root / delivery_paths["job_root"]
        try:
            if staging_abs.is_dir():
                if delivery_abs.exists():
                    shutil.rmtree(delivery_abs)
                shutil.copytree(staging_abs, delivery_abs)
            paths_logical = delivery_paths
            paths_logical["quarantine_root"] = _quarantine_logical(staging_root, safe_job)
            gen = _read_generation(delivery_abs / ".wave7_generation.json")
            fp = str((gen or {}).get("fingerprint") or "")
            return _ok(
                artifact_refs=artifact_refs,
                paths_logical=paths_logical,
                idempotent_hit=bool(fp),
                message="artifacts_finalized",
            )
        except OSError as exc:
            paths_logical = _recover_io_failure(
                repo_root=root,
                paths_logical=delivery_paths,
                staging_root=staging_root,
                job_id=safe_job,
                reason=str(exc),
                fingerprint="",
            )
            return _fail(
                code=ERR_IO,
                message=f"finalize failed: {exc}",
                paths_logical=paths_logical,
                artifact_refs=artifact_refs,
            )

    fingerprint = compute_inputs_fingerprint(
        envelopes=envelopes,
        manifest=manifest,
        report=report,
        sku=sku,
        mode=mode,
    )

    if _idempotent_hit(
        repo_root=root,
        paths_logical=paths_logical,
        fingerprint=fingerprint,
        require_manifest=manifest is not None,
    ):
        return _ok(
            artifact_refs=artifact_refs,
            paths_logical=paths_logical,
            idempotent_hit=True,
            message="idempotent_hit",
        )

    report_payload = dict(report) if report is not None else dict(_REPORT_PLACEHOLDER)
    env_list = list(envelopes or [])

    try:
        job_abs = root / paths_logical["job_root"]
        job_abs.mkdir(parents=True, exist_ok=True)
        (job_abs / "deliverables").mkdir(parents=True, exist_ok=True)

        if manifest is not None:
            _write_json_atomic(
                job_abs / "manifest.json",
                dict(manifest),
                writer=json_writer,
            )

        _write_json_atomic(
            job_abs / "report.json",
            report_payload,
            writer=json_writer,
        )

        report_md = job_abs / "report.md"
        if not report_md.is_file():
            report_md.write_text(
                "# Wave 7 report (placeholder)\n\nMarkdown rendering deferred.\n",
                encoding="utf-8",
            )

        envelope_count = _write_envelopes(
            repo_root=root,
            envelopes_dir_rel=paths_logical["envelopes_dir"],
            envelopes=env_list,
            writer=json_writer,
        )

        generation = {
            "schema_version": WAVE7_STORE_SCHEMA_VERSION,
            "job_id": safe_job,
            "sku": str(sku or ""),
            "mode": mode,
            "fingerprint": fingerprint,
            "stored_at": _utc_now_iso(),
            "envelope_count": envelope_count,
        }
        _write_json_atomic(
            job_abs / ".wave7_generation.json",
            generation,
            writer=json_writer,
        )

    except OSError as exc:
        paths_logical = _recover_io_failure(
            repo_root=root,
            paths_logical=paths_logical,
            staging_root=staging_root,
            job_id=safe_job,
            reason=str(exc),
            fingerprint=fingerprint,
        )
        return _fail(
            code=ERR_IO,
            message=f"artifact write failed: {exc}",
            paths_logical=paths_logical,
            artifact_refs=artifact_refs,
        )
    except ValueError as exc:
        return _fail(
            code=ERR_INVALID_JOB,
            message=str(exc),
            paths_logical=paths_logical,
            artifact_refs=artifact_refs,
        )

    try:
        for value in paths_logical.values():
            _assert_no_leaky_logical_path(value)
        for ref in artifact_refs.values():
            if not ref.startswith(f"{W6_DELIVERY_SCHEME}/"):
                raise ValueError(f"artifact ref must use {W6_DELIVERY_SCHEME}: {ref!r}")
            if _LEAKY_PATH_RE.search(ref.replace(f"{W6_DELIVERY_SCHEME}/", "", 1)):
                raise ValueError(f"path leak in artifact ref: {ref!r}")
    except ValueError as exc:
        return _fail(
            code=ERR_PATH_LEAK,
            message=str(exc),
            paths_logical=paths_logical,
            artifact_refs=artifact_refs,
        )

    return _ok(
        artifact_refs=artifact_refs,
        paths_logical=paths_logical,
        idempotent_hit=False,
        message="artifacts_stored",
    )


__all__ = [
    "W6_ARTIFACT_KINDS",
    "W6_DELIVERY_SCHEME",
    "WAVE7_STORE_SCHEMA_VERSION",
    "compute_inputs_fingerprint",
    "store_wave7_artifacts",
    "w6_logical_ref",
]
