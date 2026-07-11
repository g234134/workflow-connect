"""Sandbox end-to-end delivery bundle v1 (W12-T1).

Materializes a sandbox-only delivery bundle under outbox/sandbox_delivery/ for
allowlisted experimental fixtures. Does not trigger production notify or
production delivery contracts.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

EXPERIMENT_VERSION = "v1"
SCHEMA_VERSION = "sandbox_delivery_bundle_v1"

SANDBOX_E2E_ALLOWLIST = frozenset({"additional_demo"})
SANDBOX_DELIVERY_DIRNAME = "sandbox_delivery"

_ARTIFACT_REL_PATHS = (
    "reports/report.json",
    "reports/report.md",
    "reports/cleaning_stats.json",
    "reports/eligibility_result.json",
    "delivery_signoff.md",
)

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _repo_root(repo_root: Optional[Path] = None) -> Path:
    return repo_root.resolve() if repo_root is not None else _REPO_ROOT


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _format_ts_for_dir() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def is_sandbox_e2e_allowed(case_ref: str) -> Tuple[bool, str]:
    """Return (allowed, reason) for --sandbox-end-to-end flag."""
    ref = str(case_ref or "").replace("\\", "/").strip("/")
    if ref not in SANDBOX_E2E_ALLOWLIST:
        return False, (
            f"case_ref {ref!r} not in sandbox e2e allowlist: "
            f"{sorted(SANDBOX_E2E_ALLOWLIST)}"
        )
    return True, "ok"


def can_proceed_sandbox_bundle(
    output_guard: Dict[str, Any],
    *,
    auto_approve_delivery: bool = False,
) -> Tuple[bool, str]:
    """Checkpoint B gate for sandbox bundle: guard OK or explicit approve."""
    if auto_approve_delivery:
        return True, "auto_approve_delivery"
    status = str(output_guard.get("status") or "").lower()
    if status == "ok":
        return True, "output_guard_ok"
    ratio = output_guard.get("removal_ratio")
    if isinstance(ratio, (int, float)) and ratio <= 0.5 and status != "warning":
        return True, "removal_ratio_within_threshold"
    return False, f"output_guard_blocked: status={status!r}"


def sandbox_delivery_root(
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Path:
    """Resolve outbox/sandbox_delivery root (or override parent/outbox)."""
    root = _repo_root(repo_root)
    if outbox_root_override:
        base = Path(outbox_root_override)
        if not base.is_absolute():
            base = root / base
        return (base / SANDBOX_DELIVERY_DIRNAME).resolve()
    return (root / "outbox" / SANDBOX_DELIVERY_DIRNAME).resolve()


def _copy_artifact(
    case_path: Path,
    rel_path: str,
    dest_dir: Path,
    repo_root: Path,
) -> Optional[Dict[str, Any]]:
    src = case_path / rel_path
    if not src.is_file():
        return None
    dest = dest_dir / Path(rel_path).name
    shutil.copy2(src, dest)
    try:
        rel_dest = dest.relative_to(repo_root).as_posix()
    except ValueError:
        rel_dest = dest.as_posix()
    return {
        "kind": Path(rel_path).suffix.lstrip(".") or "file",
        "source": rel_path.replace("\\", "/"),
        "path": rel_dest,
    }


def _copy_cleaned_csvs(case_path: Path, dest_dir: Path, repo_root: Path) -> List[Dict[str, Any]]:
    cleaned_dir = case_path / "cleaned"
    copied: List[Dict[str, Any]] = []
    if not cleaned_dir.is_dir():
        return copied
    csv_dest = dest_dir / "cleaned"
    csv_dest.mkdir(parents=True, exist_ok=True)
    for csv_path in sorted(cleaned_dir.glob("*.csv")):
        dest = csv_dest / csv_path.name
        shutil.copy2(csv_path, dest)
        try:
            rel_dest = dest.relative_to(repo_root).as_posix()
        except ValueError:
            rel_dest = dest.as_posix()
        copied.append(
            {
                "kind": "cleaned_csv",
                "source": f"cleaned/{csv_path.name}",
                "path": rel_dest,
            }
        )
    return copied


def write_sandbox_delivery_bundle(
    *,
    case_ref: str,
    case_dir: Union[str, Path],
    experiment_id: str,
    output_guard: Dict[str, Any],
    run_execution: Optional[Dict[str, Any]] = None,
    checkpoint_a: Optional[Dict[str, Any]] = None,
    checkpoint_b: Optional[Dict[str, Any]] = None,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Copy bundle artifacts to sandbox_delivery and write manifest.json."""
    root = _repo_root(repo_root)
    case_path = Path(case_dir)
    if not case_path.is_absolute():
        case_path = root / case_path
    case_path = case_path.resolve()

    allowed, reason = is_sandbox_e2e_allowed(case_ref)
    if not allowed:
        return {"ok": False, "message": reason, "case_ref": case_ref}

    ts = _format_ts_for_dir()
    short_id = (experiment_id or "unknown")[:8]
    bundle_dir = sandbox_delivery_root(root, outbox_root_override) / case_ref / f"{ts}_{short_id}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    artifacts: List[Dict[str, Any]] = []
    for rel in _ARTIFACT_REL_PATHS:
        entry = _copy_artifact(case_path, rel, bundle_dir, root)
        if entry:
            artifacts.append(entry)
    artifacts.extend(_copy_cleaned_csvs(case_path, bundle_dir, root))

    manifest: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "experiment_version": EXPERIMENT_VERSION,
        "sandbox": True,
        "production_contract": False,
        "notify_triggered": False,
        "case_ref": case_ref,
        "experiment_id": experiment_id,
        "written_at": _utc_now_iso(),
        "bundle_dir": None,
        "output_guard": {
            "status": output_guard.get("status"),
            "removal_ratio": output_guard.get("removal_ratio"),
            "checks": output_guard.get("checks"),
            "source": output_guard.get("source"),
        },
        "checkpoint_trace": {
            "checkpoint_a_status": (checkpoint_a or {}).get("status"),
            "checkpoint_b_status": (checkpoint_b or {}).get("status"),
            "checkpoint_b_would_trigger": (checkpoint_b or {}).get("would_trigger"),
        },
        "run_execution_summary": {
            "tools_executed": (run_execution or {}).get("tools_executed") or [],
            "ok": (run_execution or {}).get("ok"),
        },
        "artifacts": artifacts,
        "notes": [
            "sandbox-only delivery bundle; not a production contract",
            "no client notify dispatched",
        ],
    }
    try:
        manifest["bundle_dir"] = bundle_dir.relative_to(root).as_posix()
    except ValueError:
        manifest["bundle_dir"] = bundle_dir.as_posix()

    manifest_path = bundle_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    try:
        manifest_rel = manifest_path.relative_to(root).as_posix()
    except ValueError:
        manifest_rel = manifest_path.as_posix()

    return {
        "ok": True,
        "message": "sandbox delivery bundle written",
        "case_ref": case_ref,
        "sandbox": True,
        "bundle_dir": manifest["bundle_dir"],
        "manifest_path": manifest_rel,
        "artifacts_count": len(artifacts),
        "notify_triggered": False,
    }


def find_latest_sandbox_bundle(
    case_ref: str,
    *,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Return newest sandbox manifest for case_ref, or None."""
    root = _repo_root(repo_root)
    scan_root = sandbox_delivery_root(root, outbox_root_override) / case_ref
    if not scan_root.is_dir():
        return None

    candidates: List[Tuple[str, Path, Dict[str, Any]]] = []
    for subdir in scan_root.iterdir():
        if not subdir.is_dir():
            continue
        manifest_path = subdir / "manifest.json"
        if not manifest_path.is_file():
            continue
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        ts = subdir.name.split("_")[0] if "_" in subdir.name else subdir.name
        candidates.append((ts, manifest_path, data))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    ts, path, data = candidates[0]
    try:
        rel_path = path.relative_to(root).as_posix()
    except ValueError:
        rel_path = path.as_posix()

    return {
        "source_kind": "sandbox_delivery",
        "artifact_path": rel_path,
        "artifact_timestamp": ts,
        "written_at": data.get("written_at"),
        "payload": data,
    }
