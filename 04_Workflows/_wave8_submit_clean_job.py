#!/usr/bin/env python3
"""
Wave 8 — Submit CleanJob CLI (v0.2)

工程/QA 使用的轻量命令入口，包装 core.wave8_clean_submit_adapter。

Usage:
    # Preview mode (dry-run): 仅验证映射链，不实际提交
    python 04_Workflows/_wave8_submit_clean_job.py --intake-json path/to/intake.json --dry-run --pretty

    # Submit mode: 真正执行 Wave7 lifecycle 提交 job
    python 04_Workflows/_wave8_submit_clean_job.py --intake-json path/to/intake.json --pretty

    # With QA health check gate (requires run_summary.json from orchestrator)
    python 04_Workflows/_wave8_submit_clean_job.py --intake-json path/to/intake.json --pretty --require-qa-pass

Exit codes:
    0 — Success (preview 通过或 submit 完成，且 QA 检查通过)
    1 — Failure (文件错误、验证失败、lifecycle 异常或 QA 检查失败)

Output (stdout):
    结构化 JSON，包含 ok, stage, clean_job, job_record, raw_files, message 等字段。
    --dry-run 时额外包含 recommended_skills（Skill Registry 推荐，非正式提交字段）。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Acceptable QA status values for health check gate
ACCEPTABLE_QA_STATUSES = {"pass", "warning", "info"}

# Coarse volume buckets for Skill Registry input_profile (row/file estimates from clean_job)
_VOLUME_SMALL_MAX_ROWS = 10_000
_VOLUME_LARGE_MIN_ROWS = 100_000
_MAX_RECOMMENDED_SKILLS = 5


def _resolve_core_path() -> Path | None:
    """Resolve gov_core_system core path relative to this script."""
    script_dir = Path(__file__).parent.resolve()
    candidate = (
        script_dir.parent
        / "01_Environments"
        / "python_venvs"
        / "gov_core_system"
    )
    if (candidate / "core").is_dir():
        return candidate
    return None


def _resolve_repo_root() -> Path:
    """Repo root (parent of 04_Workflows)."""
    return Path(__file__).parent.resolve().parent


def _resolve_skills_cards_root() -> Path:
    """Skill Card YAML/JSON tree under repo ``skills/``."""
    return _resolve_repo_root() / "skills"


def _import_submit_adapter(core_root: Path) -> Any:
    """Import submit_intake_record from core with sys.path bootstrap."""
    if str(core_root) not in sys.path:
        sys.path.insert(0, str(core_root))

    try:
        from core.wave8_clean_submit_adapter import submit_intake_record
        return submit_intake_record
    except ImportError as e:
        raise ImportError(f"Failed to import submit_adapter from {core_root}: {e}") from e


def _import_skill_registry(core_root: Path) -> tuple[Any, Any]:
    """Import load_skill_cards and select_skills from gov_core_system core."""
    if str(core_root) not in sys.path:
        sys.path.insert(0, str(core_root))

    try:
        from core.wave8_skill_registry import load_skill_cards, select_skills
        return load_skill_cards, select_skills
    except ImportError as e:
        raise ImportError(f"Failed to import skill_registry from {core_root}: {e}") from e


def _load_skill_cards_at_startup(
    core_root: Path,
    *,
    verbose: bool = False,
) -> list[dict[str, Any]]:
    """
    Load Skill Cards once at CLI startup.

    Failures are warned on stderr and return an empty list (dry-run still proceeds).
    """
    skills_root = _resolve_skills_cards_root()
    try:
        load_skill_cards, _ = _import_skill_registry(core_root)
    except ImportError as e:
        print(f"[warn] Skill Registry import failed: {e}", file=sys.stderr)
        return []

    try:
        cards = load_skill_cards(str(skills_root))
    except Exception as e:
        print(f"[warn] Skill Registry load failed: {e}", file=sys.stderr)
        return []

    if verbose:
        print(
            f"[verbose] Loaded {len(cards)} skill card(s) from: {skills_root}",
            file=sys.stderr,
        )
    return cards


def _sum_row_count_estimates(clean_job: dict[str, Any]) -> int:
    total = 0
    for source in clean_job.get("data_sources") or []:
        if not isinstance(source, dict):
            continue
        estimate = source.get("row_count_estimate")
        if isinstance(estimate, bool):
            continue
        if isinstance(estimate, (int, float)) and estimate >= 0:
            total += int(estimate)
    return total


def _infer_volume_level(clean_job: dict[str, Any]) -> str | None:
    """Map row/file estimates to small | medium | large for Skill Registry."""
    rows = _sum_row_count_estimates(clean_job)
    sources = clean_job.get("data_sources")
    file_count = len(sources) if isinstance(sources, list) else 0

    if rows <= 0 and file_count <= 0:
        return None
    if rows >= _VOLUME_LARGE_MIN_ROWS or file_count >= 10:
        return "large"
    if rows < _VOLUME_SMALL_MAX_ROWS and file_count <= 3:
        return "small"
    return "medium"


def _extract_product_sku(
    clean_job: dict[str, Any] | None,
    job_record: dict[str, Any] | None,
) -> str | None:
    for container in (clean_job, job_record):
        if not isinstance(container, dict):
            continue
        sku = container.get("product_sku")
        if isinstance(sku, str) and sku.strip():
            return sku.strip()
    return None


def _build_job_profile(
    clean_job: dict[str, Any],
    job_record: dict[str, Any] | None,
) -> dict[str, Any]:
    product_sku = _extract_product_sku(clean_job, job_record)
    profile: dict[str, Any] = {}
    if product_sku:
        profile["product_sku"] = product_sku

    volume_level = _infer_volume_level(clean_job)
    if volume_level:
        profile["input_profile"] = {"volume_level": volume_level}
    return profile


def _skill_card_brief(card: dict[str, Any]) -> str:
    brief = card.get("brief")
    if isinstance(brief, str) and brief.strip():
        return brief.strip()
    title = card.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    return ""


def _format_recommended_skills(selected: list[dict[str, Any]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for card in selected[:_MAX_RECOMMENDED_SKILLS]:
        if not isinstance(card, dict):
            continue
        skill_id = card.get("skill_id")
        if not isinstance(skill_id, str) or not skill_id.strip():
            continue
        scope = card.get("product_sku_scope")
        scope_str = scope.strip() if isinstance(scope, str) else ""
        title = card.get("title")
        title_str = title.strip() if isinstance(title, str) else ""
        out.append(
            {
                "skill_id": skill_id.strip(),
                "title": title_str,
                "product_sku_scope": scope_str,
                "brief": _skill_card_brief(card),
            }
        )
    return out


def _attach_recommended_skills(
    result: dict[str, Any],
    *,
    skill_cards: list[dict[str, Any]],
    core_root: Path,
    verbose: bool = False,
) -> None:
    """Mutate dry-run result with recommended_skills; warn and skip on registry errors."""
    clean_job = result.get("clean_job")
    if not isinstance(clean_job, dict):
        result["recommended_skills"] = []
        return

    job_record = result.get("job_record")
    job_record_dict = job_record if isinstance(job_record, dict) else None
    job_profile = _build_job_profile(clean_job, job_record_dict)
    product_sku = job_profile.get("product_sku")
    if not product_sku:
        result["recommended_skills"] = []
        return

    try:
        _, select_skills = _import_skill_registry(core_root)
    except ImportError as e:
        print(f"[warn] Skill Registry import failed: {e}", file=sys.stderr)
        result["recommended_skills"] = []
        return

    input_profile = job_profile.get("input_profile")
    if not isinstance(input_profile, dict):
        input_profile = None

    try:
        selected = select_skills(
            skill_cards,
            product_sku=product_sku,
            input_profile=input_profile,
        )
        result["recommended_skills"] = _format_recommended_skills(selected)
    except Exception as e:
        print(f"[warn] Skill selection failed: {e}", file=sys.stderr)
        result["recommended_skills"] = []

    if verbose:
        print(
            f"[verbose] recommended_skills count={len(result['recommended_skills'])} "
            f"(product_sku={product_sku}, input_profile={input_profile})",
            file=sys.stderr,
        )


def _load_intake_json(path: Path) -> dict[str, Any]:
    """Load and validate intake JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Intake JSON not found: {path}")
    if not path.is_file():
        raise ValueError(f"Intake JSON path is not a file: {path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        if not content.strip():
            raise ValueError(f"Intake JSON file is empty: {path}")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Intake JSON root must be an object, got {type(data).__name__}")

    return data


def _resolve_run_summary_path(run_summary_ref: str) -> Path | None:
    """
    Resolve run_summary_ref (logic path) to actual file path.

    Logic path conventions:
    - relative to repo root (starts with relative path like "04_Workflows/...")
    - absolute path is used as-is
    """
    # If it's already an absolute path, use it directly
    candidate = Path(run_summary_ref).expanduser()
    if candidate.is_absolute():
        if candidate.exists():
            return candidate
        return None

    # Try resolving relative to this script's parent (repo root)
    script_dir = Path(__file__).parent.resolve()
    repo_root = script_dir.parent
    candidate = (repo_root / run_summary_ref).expanduser()
    if candidate.exists():
        return candidate

    # Fallback: try as-is (current working directory or absolute)
    candidate = Path(run_summary_ref).expanduser()
    if candidate.exists():
        return candidate

    return None


def _load_run_summary(run_summary_path: Path) -> dict[str, Any]:
    """Load and validate run_summary JSON file."""
    if not run_summary_path.exists():
        raise FileNotFoundError(f"Run summary not found: {run_summary_path}")
    if not run_summary_path.is_file():
        raise ValueError(f"Run summary path is not a file: {run_summary_path}")

    with open(run_summary_path, "r", encoding="utf-8") as f:
        content = f.read()
        if not content.strip():
            raise ValueError(f"Run summary file is empty: {run_summary_path}")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {run_summary_path}: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Run summary root must be an object, got {type(data).__name__}")

    return data


def _perform_qa_health_check(
    run_result: dict[str, Any],
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Perform QA health check based on run_summary.json.

    Returns:
        dict with keys:
        - ok: bool — True if health check passed or was skipped
        - qa_passed: bool | None — True if QA passed, False if failed, None if skipped
        - qa_status: str | None — The actual qa_status value
        - job_id: str | None — The job ID from run_result
        - message: str — Human-readable status
        - exit_code_override: int | None — If set, override the main exit code
    """
    # Extract job_id from run_result for error messages
    job_id = None
    if isinstance(run_result.get("job_record"), dict):
        job_id = run_result["job_record"].get("job_id")
    if job_id is None:
        job_id = run_result.get("job_id", "unknown")

    # Check if run_summary_ref exists
    run_summary_ref = run_result.get("run_summary_ref")
    if not run_summary_ref:
        return {
            "ok": True,  # No run summary is not a failure, just skip
            "qa_passed": None,
            "qa_status": None,
            "job_id": job_id,
            "message": "No run_summary_ref in result; QA health check skipped",
            "exit_code_override": None,
        }

    # Resolve and load run_summary.json
    run_summary_path = _resolve_run_summary_path(str(run_summary_ref))
    if run_summary_path is None:
        return {
            "ok": True,  # Missing file is not a failure for the job itself
            "qa_passed": None,
            "qa_status": None,
            "job_id": job_id,
            "message": f"Could not resolve run_summary path: {run_summary_ref}; QA health check skipped",
            "exit_code_override": None,
        }

    if verbose:
        print(f"[verbose] Loading run_summary from: {run_summary_path}", file=sys.stderr)

    try:
        run_summary = _load_run_summary(run_summary_path)
    except (FileNotFoundError, ValueError) as e:
        return {
            "ok": True,  # IO error is not a failure for the job itself
            "qa_passed": None,
            "qa_status": None,
            "job_id": job_id,
            "message": f"Failed to load run_summary: {e}; using original job result",
            "exit_code_override": None,
        }

    # Extract qa_status
    qa_status = run_summary.get("qa_status")
    if qa_status is None:
        return {
            "ok": True,
            "qa_passed": None,
            "qa_status": None,
            "job_id": job_id,
            "message": "No qa_status field in run_summary; QA health check skipped",
            "exit_code_override": None,
        }

    # Check if qa_status is acceptable
    qa_passed = qa_status in ACCEPTABLE_QA_STATUSES

    if qa_passed:
        return {
            "ok": True,
            "qa_passed": True,
            "qa_status": qa_status,
            "job_id": job_id,
            "message": f"QA health check passed (qa_status={qa_status})",
            "exit_code_override": None,
        }
    else:
        return {
            "ok": False,
            "qa_passed": False,
            "qa_status": qa_status,
            "job_id": job_id,
            "message": f"QA health check failed: job_id={job_id}, qa_status={qa_status}",
            "exit_code_override": 1,
        }


def run_submit(
    intake_json_path: Path,
    *,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Run the submit adapter: intake → CleanJob → Wave7 lifecycle.

    Args:
        intake_json_path: Path to intake JSON file
        dry_run: If True, only run preview (mapping/bridge only)
        verbose: Print diagnostic info to stderr

    Returns:
        Structured result dict with ok, stage, message, etc.
    """
    schema_version = "wave8_submit_cli_v0.2"

    # Step 0: Load intake JSON
    try:
        intake_record = _load_intake_json(intake_json_path)
    except (FileNotFoundError, ValueError) as e:
        return {
            "ok": False,
            "stage": "intake_load",
            "clean_job": None,
            "job_record": None,
            "raw_files": None,
            "message": f"Failed to load intake JSON: {e}",
            "error_code": "intake_load_failed",
            "schema_version": schema_version,
        }

    if verbose:
        print(f"[verbose] Loaded intake JSON from: {intake_json_path}", file=sys.stderr)
        print(f"[verbose] intake_id: {intake_record.get('intake_id', 'N/A')}", file=sys.stderr)
        print(f"[verbose] product_sku: {intake_record.get('product_sku', 'N/A')}", file=sys.stderr)
        print(f"[verbose] dry_run: {dry_run}", file=sys.stderr)

    # Step 1: Import adapter
    core_root = _resolve_core_path()
    if core_root is None:
        return {
            "ok": False,
            "stage": "core_path_resolution",
            "clean_job": None,
            "job_record": None,
            "raw_files": None,
            "message": "Could not locate gov_core_system core path",
            "error_code": "core_path_not_found",
            "schema_version": schema_version,
        }

    try:
        submit_intake_record = _import_submit_adapter(core_root)
    except ImportError as e:
        return {
            "ok": False,
            "stage": "import",
            "clean_job": None,
            "job_record": None,
            "raw_files": None,
            "message": f"Failed to import submit_adapter: {e}",
            "error_code": "import_error",
            "schema_version": schema_version,
        }

    # Step 2: Call adapter
    if verbose:
        print(f"[verbose] Calling submit_intake_record(dry_run={dry_run})...", file=sys.stderr)

    try:
        result = submit_intake_record(intake_record, dry_run=dry_run)
    except Exception as e:
        return {
            "ok": False,
            "stage": "adapter_exception",
            "clean_job": None,
            "job_record": None,
            "raw_files": None,
            "message": f"Adapter raised exception: {e}",
            "error_code": "adapter_exception",
            "schema_version": schema_version,
        }

    # Augment result with CLI schema version if not present
    if "schema_version" not in result:
        result["schema_version"] = schema_version

    if verbose:
        stage = result.get("stage", "unknown")
        print(f"[verbose] Adapter completed with stage={stage}", file=sys.stderr)

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Submit CleanJob: intake JSON → CleanJob → Wave7 lifecycle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Preview mode (validate mapping chain without submitting)
    python %(prog)s --intake-json fixtures/intake_basic_sample.json --dry-run --pretty

    # Submit mode (actually run Wave7 lifecycle)
    python %(prog)s --intake-json fixtures/intake_basic_sample.json --pretty

    # With verbose logging
    python %(prog)s --intake-json fixtures/intake_enrich_sample.json --pretty --verbose

    # With QA health check gate
    python %(prog)s --intake-json fixtures/intake_basic_sample.json --pretty --require-qa-pass

Exit codes:
    0 — Success (preview OK, submit completed, or QA health check passed)
    1 — Failure (load error, validation error, lifecycle failure, or QA health check failed)

Output fields (JSON):
    ok              bool   — True if operation succeeded
    stage           str    — Current stage reached
    clean_job       dict   — Mapped CleanJob object (if mapping succeeded)
    job_record      dict   — Wave7 job_record (if bridge succeeded)
    raw_files       list   — Raw files list (if bridge succeeded)
    raw_files_count int    — Count of raw files
    sidecar         dict   — Sidecar metadata from bridge
    run_result      dict   — Wave7 lifecycle result (submit mode only, if run)
    message         str    — Human-readable status message
    error_code      str    — Machine-readable error code (if ok=false)
    schema_version  str    — Schema version identifier
    recommended_skills list — Dry-run only: Skill Card suggestions (skill_id, title, ...)

Health check options (--require-qa-pass):
    After successful job submission, reads run_summary.json and checks qa_status.
    Acceptable qa_status values: ["pass", "warning", "info"]
    If qa_status is not acceptable (e.g., "fail", "critical", "unknown"), exits with code 1.
        """,
    )
    parser.add_argument(
        "--intake-json",
        required=True,
        metavar="PATH",
        help="Path to intake JSON file (required)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview mode: validate mapping only, do not submit job",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print output JSON with indentation",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print additional diagnostic info to stderr",
    )
    parser.add_argument(
        "--require-qa-pass",
        action="store_true",
        dest="require_qa_pass",
        help="After job submission, check run_summary.json qa_status. Exit 1 if qa_status not in [pass, warning, info]. Only effective in non-dry-run mode. Requires orchestrator to generate run_summary.json.",
    )

    args = parser.parse_args()
    intake_path = Path(args.intake_json).expanduser().resolve()

    core_root = _resolve_core_path()
    skill_cards: list[dict[str, Any]] = []
    if core_root is not None:
        skill_cards = _load_skill_cards_at_startup(core_root, verbose=args.verbose)

    # Handle --require-qa-pass with --dry-run conflict
    if args.require_qa_pass and args.dry_run:
        print(
            "[warn] --require-qa-pass is ignored in dry-run mode (no job execution, no run_summary to check)",
            file=sys.stderr,
        )
        # Continue with dry-run, ignore the flag

    result = run_submit(
        intake_path,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    if args.dry_run and core_root is not None:
        _attach_recommended_skills(
            result,
            skill_cards=skill_cards,
            core_root=core_root,
            verbose=args.verbose,
        )

    # Perform QA health check if requested (and not in dry-run mode)
    health_check = None
    if args.require_qa_pass and not args.dry_run:
        # Only perform health check if job submission succeeded
        if result.get("ok"):
            run_result = result.get("run_result")
            if isinstance(run_result, dict):
                health_check = _perform_qa_health_check(run_result, verbose=args.verbose)
                if args.verbose and health_check:
                    print(f"[verbose] Health check: {health_check.get('message')}", file=sys.stderr)
                # If health check failed, update result and print message
                if health_check and not health_check.get("ok"):
                    print(f"[qa-check] {health_check.get('message')}", file=sys.stderr)
            else:
                if args.verbose:
                    print(
                        "[verbose] No run_result in submission result; QA health check skipped",
                        file=sys.stderr,
                    )
        else:
            if args.verbose:
                print(
                    "[verbose] Job submission failed; QA health check skipped",
                    file=sys.stderr,
                )

    # Augment result with health check info if performed
    if health_check:
        result["qa_health_check"] = {
            "performed": True,
            "passed": health_check.get("qa_passed"),
            "qa_status": health_check.get("qa_status"),
            "job_id": health_check.get("job_id"),
            "message": health_check.get("message"),
        }

    # Output result as JSON to stdout
    indent = 2 if args.pretty else None
    print(json.dumps(result, indent=indent, ensure_ascii=False))

    # Determine exit code
    # Priority: health check override > original result ok
    if health_check and health_check.get("exit_code_override") is not None:
        return health_check["exit_code_override"]
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
