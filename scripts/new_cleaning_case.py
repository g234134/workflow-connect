#!/usr/bin/env python3
"""CLI: manual intake entry — create case_dir + intake.json (+ optional P2 gate).

Usage:
    python scripts/new_cleaning_case.py \\
        --client-ref ACME \\
        --product-sku CLEAN-BASIC \\
        --source-file /path/to/file.csv

    python scripts/new_cleaning_case.py ... --run-gate
    python scripts/new_cleaning_case.py ... --run-p75-gate

Does not run cleaning, bundle, or prod dispatch (Wave 3 W-MVP-W3-INTAKE-CLI).
``--run-p75-gate`` uses P75 ``evaluate_intake_gate`` preview (W1-P75-INTAKE-CLI-MVP-v1).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_TEMPLATE = _REPO_ROOT / "cases" / "_TEMPLATE_case"
_CSV_CLEANING = _REPO_ROOT / "notebooks" / "csv_cleaning"
if str(_CSV_CLEANING) not in sys.path:
    sys.path.insert(0, str(_CSV_CLEANING))

from case_eligibility import check_case_eligibility  # noqa: E402

_DEFAULT_P75_TASK_TYPE = "tabular.cleaning.mvp"

_SLUG_RE = re.compile(r"[^a-z0-9-]+")
_CASE_ID_RE = re.compile(r"^(\d{4})-(\d{4})$")


def _normalize_slug(value: str) -> str:
    slug = _SLUG_RE.sub("-", value.strip().lower())
    return slug.strip("-")


def _allocate_case_id(cases_root: Path, client_ref: str) -> str:
    """Next case_id as YYYY-NNNN under cases/<client_ref>/ (per-year sequence)."""
    year = datetime.now(timezone.utc).strftime("%Y")
    client_dir = cases_root / client_ref
    max_seq = 0
    if client_dir.is_dir():
        for child in client_dir.iterdir():
            if not child.is_dir():
                continue
            match = _CASE_ID_RE.match(child.name)
            if match and match.group(1) == year:
                max_seq = max(max_seq, int(match.group(2)))
    return f"{year}-{max_seq + 1:04d}"


def _infer_file_format(path: Path, explicit: str | None) -> str:
    if explicit and explicit.strip():
        return explicit.strip().lower()
    ext = path.suffix.lstrip(".").lower()
    if ext in ("csv", "tsv", "txt", "xlsx", "xls"):
        return "tsv" if ext == "tsv" else ext
    return "csv"


def _count_csv_rows(path: Path, encoding: str) -> int | None:
    for enc in (encoding, "utf-8-sig", "utf-8", "gbk"):
        try:
            with path.open(encoding=enc, newline="") as fh:
                total = sum(1 for _ in csv.reader(fh))
                return max(total - 1, 0)
        except (OSError, UnicodeDecodeError, csv.Error):
            continue
    return None


def _compute_scale(data_path: Path, encoding: str, file_format: str) -> dict[str, int | None]:
    size_bytes = data_path.stat().st_size
    row_count: int | None = None
    if file_format in ("csv", "tsv", "txt"):
        row_count = _count_csv_rows(data_path, encoding)
    return {"row_count": row_count, "file_size_bytes": size_bytes}


def _build_intake(
    *,
    case_id: str,
    client_ref: str,
    product_sku: str,
    data_file_rel: str,
    file_format: str,
    encoding: str,
    delimiter: str,
    scale: dict[str, int | None],
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "client_ref": client_ref,
        "product_sku": product_sku,
        "data_file": data_file_rel,
        "file_format": file_format,
        "encoding": encoding,
        "delimiter": delimiter,
        "scale": scale,
        "schema": {
            "field_count": None,
            "primary_key": None,
            "pii_fields": [],
        },
        "provenance": {
            "source_type": "owned",
            "data_owner": client_ref,
        },
        "sensitivity": "internal",
        "structure": "text_only",
        "security_compliance": {
            "contains_pii": False,
            "user_acknowledged_limitations": True,
        },
        "cleaning_goals": "",
    }


def _materialize_delivery_signoff(case_dir: Path, case_id: str, client_ref: str, product_sku: str) -> None:
    template = _TEMPLATE / "delivery_signoff.md"
    if template.is_file():
        text = template.read_text(encoding="utf-8")
        text = (
            text.replace("`<case_id>`", case_id)
            .replace("<case_id>", case_id)
            .replace("`<client_ref>`", client_ref)
            .replace("<client_ref>", client_ref)
            .replace("`<product_sku>`", product_sku)
            .replace("<product_sku>", product_sku)
        )
        (case_dir / "delivery_signoff.md").write_text(text, encoding="utf-8")
    else:
        (case_dir / "delivery_signoff.md").write_text(
            f"# Delivery Signoff · {case_id}\n\n_pending_\n",
            encoding="utf-8",
        )


def _ensure_subdirs(case_dir: Path) -> None:
    for sub in ("raw", "cleaned", "reports"):
        path = case_dir / sub
        path.mkdir(parents=True, exist_ok=True)
        gitkeep = _TEMPLATE / sub / ".gitkeep"
        if gitkeep.is_file() and not any(path.iterdir()):
            shutil.copy2(gitkeep, path / ".gitkeep")


def _detect_csv_probe(path: Path) -> dict[str, Any]:
    """Minimal CSV probe for --auto-detect intake draft."""
    encodings = ("utf-8-sig", "utf-8", "gbk", "latin-1")
    delimiters = (",", ";", "\t", "|")
    for enc in encodings:
        for delim in delimiters:
            try:
                with path.open(encoding=enc, newline="") as fh:
                    sample = fh.read(4096)
                    fh.seek(0)
                    reader = csv.reader(fh, delimiter=delim)
                    headers = next(reader, None)
                    if not headers or len(headers) < 2:
                        continue
                    row_count = sum(1 for _ in reader)
                    return {
                        "encoding": enc,
                        "delimiter": delim,
                        "headers": [str(h).strip() for h in headers],
                        "row_count": row_count,
                    }
            except (OSError, UnicodeDecodeError, csv.Error):
                continue
    return {"encoding": "utf-8-sig", "delimiter": ",", "headers": [], "row_count": None}


def _apply_auto_detect(intake: dict[str, Any], probe: dict[str, Any]) -> dict[str, Any]:
    headers = probe.get("headers") or []
    intake["encoding"] = probe.get("encoding") or intake.get("encoding") or "utf-8-sig"
    intake["delimiter"] = probe.get("delimiter") or intake.get("delimiter") or ","
    if probe.get("row_count") is not None:
        intake.setdefault("scale", {})
        intake["scale"]["row_count"] = probe["row_count"]
    if headers:
        schema = intake.setdefault("schema", {})
        schema["field_count"] = len(headers)
        if not schema.get("primary_key"):
            schema["primary_key"] = headers[0]
        roles = schema.setdefault("column_roles", {})
        for idx, col in enumerate(headers):
            if col in roles:
                continue
            roles[col] = "primary_key" if idx == 0 else "text"
    return intake


def create_cleaning_case(
    *,
    client_ref: str,
    product_sku: str,
    source_file: Path,
    encoding: str = "utf-8",
    delimiter: str = ",",
    file_format: str | None = None,
    auto_detect: bool = False,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Create case_dir under cases/ with intake.json and copied raw file."""
    root = (repo_root or _REPO_ROOT).resolve()
    cases_root = root / "cases"

    if not source_file.is_file():
        return {
            "ok": False,
            "message": f"source_file_not_found:{source_file.name}",
            "human_readable": f"Source file not found: {source_file}",
        }

    norm_client = _normalize_slug(client_ref)
    if not norm_client:
        return {
            "ok": False,
            "message": "invalid_client_ref",
            "human_readable": "client_ref must contain at least one alphanumeric character",
        }

    fmt = _infer_file_format(source_file, file_format)
    case_id = _allocate_case_id(cases_root, norm_client)
    case_dir = cases_root / norm_client / case_id
    if case_dir.exists():
        return {
            "ok": False,
            "message": f"case_dir_exists:{case_dir.name}",
            "human_readable": f"Case directory already exists: {case_dir.relative_to(root)}",
        }

    raw_name = source_file.name
    data_file_rel = f"raw/{raw_name}"

    case_dir.mkdir(parents=True, exist_ok=False)
    _ensure_subdirs(case_dir)
    shutil.copy2(source_file, case_dir / "raw" / raw_name)

    raw_copy = case_dir / data_file_rel
    scale = _compute_scale(raw_copy, encoding, fmt)
    intake = _build_intake(
        case_id=case_id,
        client_ref=norm_client,
        product_sku=product_sku.strip(),
        data_file_rel=data_file_rel,
        file_format=fmt,
        encoding=encoding,
        delimiter=delimiter,
        scale=scale,
    )
    if auto_detect:
        probe = _detect_csv_probe(raw_copy)
        intake = _apply_auto_detect(intake, probe)
        intake["auto_detect"] = {
            "headers": probe.get("headers"),
            "encoding": probe.get("encoding"),
            "delimiter": probe.get("delimiter"),
        }
    intake_path = case_dir / "intake.json"
    intake_path.write_text(json.dumps(intake, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _materialize_delivery_signoff(case_dir, case_id, norm_client, product_sku.strip())

    rel_case_dir = case_dir.relative_to(root).as_posix()
    return {
        "ok": True,
        "case_dir": str(case_dir),
        "case_dir_rel": rel_case_dir,
        "case_id": case_id,
        "client_ref": norm_client,
        "product_sku": product_sku.strip(),
        "source_file": data_file_rel,
        "intake_path": str(intake_path),
        "scale": scale,
    }


def _run_p75_gate_preview(
    case_dir_rel: str,
    *,
    task_type: str,
    repo_root: Path,
) -> dict[str, Any]:
    from routing.intake_gate_layer_v1 import evaluate_intake_gate

    return evaluate_intake_gate(
        task_type,
        case_dir_rel,
        mode="preview",
        repo_root=repo_root,
    )


def _print_summary(
    create_result: dict[str, Any],
    *,
    gate_result: dict[str, Any] | None,
    run_gate: bool,
    p75_gate_result: dict[str, Any] | None = None,
    run_p75_gate: bool = False,
) -> None:
    gate_status = "not_run"
    if run_p75_gate and p75_gate_result is not None:
        gate_status = str(p75_gate_result.get("decision") or "review_needed")
    elif run_gate and gate_result is not None:
        gate_status = gate_result.get("eligibility", "review_needed")

    lines = [
        "--- intake summary ---",
        f"case_dir: {create_result.get('case_dir_rel', create_result.get('case_dir', ''))}",
        f"client_ref: {create_result.get('client_ref', '')}",
        f"case_id: {create_result.get('case_id', '')}",
        f"product_sku: {create_result.get('product_sku', '')}",
        f"source_file: {create_result.get('source_file', '')}",
        f"gate_status: {gate_status}",
    ]
    if run_p75_gate and p75_gate_result is not None:
        lines.append(f"reason_codes: {p75_gate_result.get('reason_codes') or []}")
    lines.append("----------------------")
    print("\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a new cleaning case directory with intake.json (Wave 3 intake CLI)."
    )
    parser.add_argument("--client-ref", required=True, help="Client or project slug (normalized to lowercase)")
    parser.add_argument("--product-sku", required=True, help="Product SKU e.g. CLEAN-BASIC")
    parser.add_argument("--source-file", required=True, type=Path, help="Path to customer CSV (copied into raw/)")
    parser.add_argument("--encoding", default="utf-8", help="File encoding (default: utf-8)")
    parser.add_argument("--delimiter", default=",", help="Field delimiter (default: ,)")
    parser.add_argument("--file-format", default=None, help="Override format: csv, tsv, txt (default: from extension)")
    parser.add_argument(
        "--auto-detect",
        action="store_true",
        help="Probe raw CSV for encoding, delimiter, headers; draft intake schema fields",
    )
    gate_group = parser.add_mutually_exclusive_group()
    gate_group.add_argument(
        "--run-gate",
        action="store_true",
        help="Run P2 eligibility gate after creation; print JSON result to stdout",
    )
    gate_group.add_argument(
        "--run-p75-gate",
        action="store_true",
        help="Run P75 intake gate preview after creation; print decision/reason_codes (no outbox write)",
    )
    parser.add_argument(
        "--p75-task-type",
        default=_DEFAULT_P75_TASK_TYPE,
        help=f"task_type for --run-p75-gate (default: {_DEFAULT_P75_TASK_TYPE})",
    )
    args = parser.parse_args(argv)

    result = create_cleaning_case(
        client_ref=args.client_ref,
        product_sku=args.product_sku,
        source_file=args.source_file.resolve(),
        encoding=args.encoding,
        delimiter=args.delimiter,
        file_format=args.file_format,
        auto_detect=args.auto_detect,
    )

    if not result.get("ok"):
        print(result.get("human_readable", result.get("message", "create_failed")), file=sys.stderr)
        return 1

    repo_root = _REPO_ROOT
    gate_result: dict[str, Any] | None = None
    p75_gate_result: dict[str, Any] | None = None
    if args.run_gate:
        gate_result = check_case_eligibility(Path(result["case_dir"]))
        summary = (
            f"eligibility={gate_result.get('eligibility')} "
            f"case={gate_result.get('case_id', result.get('case_id'))}"
        )
        if gate_result.get("reason_code"):
            summary += f" reason={gate_result['reason_code']}"
        print(summary)
        print(json.dumps(gate_result, ensure_ascii=False, indent=2))
    elif args.run_p75_gate:
        case_dir_rel = result.get("case_dir_rel") or result.get("case_dir", "")
        p75_gate_result = _run_p75_gate_preview(
            str(case_dir_rel),
            task_type=args.p75_task_type,
            repo_root=repo_root,
        )
        summary = (
            f"decision={p75_gate_result.get('decision')} "
            f"case={result.get('case_id')}"
        )
        reason_codes = p75_gate_result.get("reason_codes") or []
        if reason_codes:
            summary += f" reason_codes={reason_codes}"
        print(summary)
        print(json.dumps(p75_gate_result, ensure_ascii=False, indent=2))

    _print_summary(
        result,
        gate_result=gate_result,
        run_gate=args.run_gate,
        p75_gate_result=p75_gate_result,
        run_p75_gate=args.run_p75_gate,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
