"""End-to-end test: run clean_generic.py on 3 dirty datasets."""
import json, sys, time
from pathlib import Path

# Bootstrap — absolute paths to avoid relative confusion
TANG = Path(r"D:\大唐三省六部")
sys.path.insert(0, str(TANG / "01_Environments" / "python_venvs" / "mcp-excel-venv" / "Lib" / "site-packages"))
sys.path.insert(0, str(TANG / "notebooks" / "csv_cleaning"))
sys.path.insert(0, str(TANG / "01_Environments" / "python_venvs" / "mcp-excel" / "src"))
# Remove hermes pollution
sys.path[:] = [p for p in sys.path if "Hermes" not in p and "hermes" not in p.lower()]

from clean_generic import (
    read_rows, profile, clean, write_rows,
    build_quality_report, write_quality_report_md,
)
from pathlib import Path as _P

TEST_DIR = _P(__file__).resolve().parent
OUTPUT_DIR = TEST_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ===== Profile configs for each dataset =====

PROFILES = {
    "dirty_sales_500.csv": {
        "profile_id": "fiverr_sales_v1",
        "columns": ["id", "sales_rep", "region", "product", "deal_amount", "close_date", "status", "commission_pct", "notes"],
        "primary_key": "id",
        "field_roles": {
            "id": "primary_key",
            "sales_rep": "text",
            "region": "category",
            "product": "category",
            "deal_amount": "numeric",
            "close_date": "text",
            "status": "category",
            "commission_pct": "numeric",
            "notes": "text",
        },
        "dedup_keys": ["id"],
        "dedup_compare_column": "deal_amount",
        "drop_if_blank": [],
        "numeric_range": {
            "deal_amount": {"min": 0, "max": 50000},
            "commission_pct": {"min": 0, "max": 1},
        },
        "cleaning_rules_applied": [
            "trim_whitespace", "deduplicate_by_pk", "flag_numeric_outliers",
            "normalize_category_casing", "drop_blank_pk"
        ],
    },
    "titanic_raw.csv": {
        "profile_id": "fiverr_titanic_v1",
        "columns": ["PassengerId", "Survived", "Pclass", "Name", "Sex", "Age", "SibSp", "Parch", "Ticket", "Fare", "Cabin", "Embarked"],
        "primary_key": "PassengerId",
        "field_roles": {
            "PassengerId": "primary_key",
            "Survived": "numeric",
            "Pclass": "category",
            "Name": "text",
            "Sex": "category",
            "Age": "numeric",
            "SibSp": "numeric",
            "Parch": "numeric",
            "Ticket": "text",
            "Fare": "numeric",
            "Cabin": "text",
            "Embarked": "category",
        },
        "dedup_keys": ["PassengerId"],
        "dedup_compare_column": "Fare",
        "drop_if_blank": [],
        "cleaning_rules_applied": [
            "trim_whitespace", "deduplicate_by_pk", "flag_numeric_outliers"
        ],
    },
    "netflix_raw.csv": {
        "profile_id": "fiverr_netflix_v1",
        "columns": ["show_id", "type", "title", "director", "cast", "country", "date_added", "release_year", "rating", "duration", "listed_in", "description"],
        "primary_key": "show_id",
        "field_roles": {
            "show_id": "primary_key",
            "type": "category",
            "title": "text",
            "director": "text",
            "cast": "text",
            "country": "text",
            "date_added": "text",
            "release_year": "numeric",
            "rating": "category",
            "duration": "text",
            "listed_in": "text",
            "description": "text",
        },
        "dedup_keys": ["show_id"],
        "dedup_compare_column": "release_year",
        "drop_if_blank": [],
        "cleaning_rules_applied": [
            "trim_whitespace", "deduplicate_by_pk", "flag_numeric_outliers"
        ],
    },
}

results = []

for filename, cfg in PROFILES.items():
    src = TEST_DIR / filename
    if not src.exists():
        print(f"SKIP {filename} — file not found")
        continue

    print(f"\n{'='*60}")
    print(f"  TEST: {filename}")
    print(f"{'='*60}")

    t0 = time.time()

    # 1. Read
    raw_rows = read_rows(src)
    print(f"  [1] Read: {len(raw_rows)} rows, {len(raw_rows[0]) if raw_rows else 0} cols")

    # 2. Profile BEFORE cleaning
    before = profile(raw_rows, profile_cfg=cfg)
    total_missing = sum(v["count"] for v in before["missing_by_column"].values())
    print(f"  [2] Profile (before): {total_missing} missing values, "
          f"{before['duplicate_full_rows']} full-row dupes, "
          f"{before['duplicate_primary_keys']} PK dupes, "
          f"{len(before['format_issues'])} format issues, "
          f"{len(before['range_issues'])} range issues")

    # 3. Clean
    cleaned, meta = clean(raw_rows, profile_cfg=cfg)
    print(f"  [3] Clean: {meta['output_row_count']} rows accepted, "
          f"{len(meta['dropped_rows'])} dropped, "
          f"{len(meta['deduped_rows'])} deduped, "
          f"{len(meta['range_flags'])} range flags")

    # 4. Profile AFTER cleaning (convert all values to str since clean() returns mixed types)
    cleaned_as_str = [{k: str(v) if v is not None else "" for k, v in row.items()} for row in cleaned]
    after = profile(cleaned_as_str, profile_cfg=cfg)
    total_missing_after = sum(v["count"] for v in after["missing_by_column"].values())
    print(f"  [4] Profile (after): {total_missing_after} missing values, "
          f"{after['duplicate_full_rows']} full-row dupes")

    # 5. Write cleaned CSV
    out_csv = OUTPUT_DIR / f"cleaned_{filename}"
    write_rows(out_csv, cleaned, columns=cfg["columns"])
    print(f"  [5] Written: {out_csv} ({out_csv.stat().st_size} bytes)")

    # 6. Build quality report JSON
    report = build_quality_report(
        before=before, after=after, clean_meta=meta,
        raw_rows=raw_rows, input_rows=len(raw_rows), output_rows=len(cleaned),
        job_id=f"test-{cfg['profile_id']}", profile_cfg=cfg,
    )
    out_json = OUTPUT_DIR / f"report_{filename.replace('.csv', '.json')}"
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  [6] Report JSON: {out_json} ({out_json.stat().st_size} bytes)")

    # 7. Write quality report MD
    out_md = OUTPUT_DIR / f"report_{filename.replace('.csv', '.md')}"
    write_quality_report_md(report, out_md)
    print(f"  [7] Report MD: {out_md}")

    elapsed_ms = round((time.time() - t0) * 1000)
    print(f"  [✓] DONE in {elapsed_ms}ms")

    results.append({
        "file": filename,
        "rows_in": len(raw_rows),
        "rows_out": len(cleaned),
        "missing_before": total_missing,
        "missing_after": total_missing_after,
        "dupes_removed": len(meta["dropped_rows"]),
        "deduped": len(meta["deduped_rows"]),
        "format_issues": len(before["format_issues"]),
        "range_issues": len(before["range_issues"]),
        "elapsed_ms": elapsed_ms,
    })

# ===== Summary =====
print(f"\n{'='*60}")
print("  SUMMARY")
print(f"{'='*60}")
print(f"  {'Dataset':<25} {'In':>6} {'Out':>6} {'Miss↓':>6} {'Dups':>5} {'Fmt!':>5} {'Range':>6} {'ms':>6}")
print(f"  {'-'*25} {'-'*6} {'-'*6} {'-'*6} {'-'*5} {'-'*5} {'-'*6} {'-'*6}")
for r in results:
    miss_saved = r["missing_before"] - r["missing_after"]
    print(f"  {r['file']:<25} {r['rows_in']:>6} {r['rows_out']:>6} {miss_saved:>6} {r['deduped']:>5} {r['format_issues']:>5} {r['range_issues']:>6} {r['elapsed_ms']:>6}")
print(f"\n  All outputs → {OUTPUT_DIR}")

# Write summary JSON
summary_path = OUTPUT_DIR / "test_summary.json"
summary_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"  Summary JSON → {summary_path}")
