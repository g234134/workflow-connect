#!/usr/bin/env python3
"""
mcp_excel_pipeline.py — Excel/CSV 清洗管線
Stage 0: 探索（inspect + columns）
Stage 1: 偵測（nulls + duplicates + unique profile）
Stage 2: 清洗（fill nulls + drop duplicates + standardize）
Stage 3: 驗證 + 報告

用法：
  python core/mcp_excel_pipeline.py <input.xlsx> [--output clean.xlsx] [--stage 1-2]

NOTE: MUST be run with the mcp-excel-venv Python, not the Hermes venv:
  01_Environments/python_venvs/mcp-excel-venv/Scripts/python.exe core/mcp_excel_pipeline.py ...
"""
import json
import sys
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# --- Auto-detect and re-exec with mcp-excel-venv if needed ---
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
_MCP_VENV_PY = Path(_REPO_ROOT) / "01_Environments" / "python_venvs" / "mcp-excel-venv" / "Scripts" / "python.exe"

def _ensure_right_python():
    """Re-exec with mcp-excel-venv Python if current interpreter is contaminated."""
    if not _MCP_VENV_PY.exists():
        return  # venv missing, let it fail naturally
    cur = Path(sys.executable).resolve()
    if cur == _MCP_VENV_PY.resolve():
        return  # already correct
    # Check if numpy import will fail (indicating Hermes venv contamination)
    try:
        import numpy
        # If numpy loads but from a different location than mcp-excel-venv, re-exec
        expected = str(Path(_REPO_ROOT) / "01_Environments" / "python_venvs" / "mcp-excel-venv" / "Lib" / "site-packages")
        if expected not in numpy.__file__:
            raise ImportError("numpy from wrong venv")
    except Exception:
        # Re-exec with correct Python
        print(f"[bootstrap] Switching to mcp-excel-venv Python: {_MCP_VENV_PY}")
        os.execv(str(_MCP_VENV_PY), [str(_MCP_VENV_PY)] + sys.argv)

_ensure_right_python()

# --- Bootstrap MCP path ---
MCP_VENV = Path(__file__).resolve().parent.parent / "01_Environments" / "python_venvs" / "mcp-excel-venv"
MCP_SRC = Path(__file__).resolve().parent.parent / "01_Environments" / "python_venvs" / "mcp-excel" / "src"

sys.path[:] = [p for p in sys.path if "Hermes" not in p and "hermes" not in p.lower()]
if str(MCP_VENV / "Lib" / "site-packages") not in sys.path:
    sys.path.insert(0, str(MCP_VENV / "Lib" / "site-packages"))
if str(MCP_SRC) not in sys.path:
    sys.path.insert(0, str(MCP_SRC))
os.environ.pop("PYTHONPATH", None)

# Add repo root so 'from core.mcp_excel_cleaner import ...' works
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import pandas as pd
from core.mcp_excel_cleaner import MCPExcelCleaner


class MCPExcelPipeline:
    """
    End-to-end Excel/CSV cleaning pipeline using mcp-excel for detection
    and pandas for actual cleaning operations.

    Flow:
      1. MCP inspect → understand file structure
      2. MCP detect → find nulls, duplicates
      3. Pandas clean → fill/drop/standardize
      4. MCP validate → verify cleaning results
      5. Output clean file + JSON report
    """

    def __init__(self, input_path: str, output_path: str = None, sheet_name: str = None):
        self.input_path = str(Path(input_path).resolve())
        self.sheet_name = sheet_name
        stem = Path(self.input_path).stem
        ext = Path(self.input_path).suffix

        if output_path:
            self.output_path = str(Path(output_path).resolve())
        else:
            self.output_path = str(Path(self.input_path).parent / f"{stem}_clean{ext}")

        self.report = {
            "input": self.input_path,
            "output": self.output_path,
            "start_time": datetime.now().isoformat(),
            "stages": {},
            "stats": {},
        }

    def run(self, stages: str = "0-1-2-3") -> dict:
        """Run pipeline for specified stages (e.g. '0-1-2-3', '1-2')."""
        stage_list = [s.strip() for s in stages.split("-")]

        # Stage 0: Inspect
        if "0" in stage_list:
            self._stage_inspect()

        # Stage 1: Detect
        if "1" in stage_list:
            self._stage_detect()

        # Stage 2: Clean
        if "2" in stage_list:
            self._stage_clean()

        # Stage 3: Validate
        if "3" in stage_list:
            self._stage_validate()

        self.report["end_time"] = datetime.now().isoformat()
        return self.report

    def _stage_inspect(self):
        """Stage 0: Use mcp-excel to inspect file structure."""
        cleaner = MCPExcelCleaner(self.input_path, self.sheet_name)
        info = cleaner.inspect()
        self.sheet_name = cleaner.sheet_name
        self._cleaner = cleaner  # reuse for later stages
        self.report["stages"]["0_inspect"] = info
        self.report["stats"]["format"] = info["format"]
        self.report["stats"]["columns"] = info["columns"]
        self.report["stats"]["active_sheet"] = self.sheet_name
        print(f"[Stage 0] Inspected: {info['format']}, sheet={self.sheet_name}, cols={info['column_count']}")

    def _stage_detect(self):
        """Stage 1: Use mcp-excel to detect issues."""
        if not hasattr(self, "_cleaner"):
            self._stage_inspect()
        detect = self._cleaner.detect()
        self.report["stages"]["1_detect"] = detect
        total_nulls = detect["total_nulls"]
        dup_count = detect["duplicates"]["duplicate_count"]
        self.report["stats"]["total_nulls"] = total_nulls
        self.report["stats"]["duplicate_count"] = dup_count
        print(f"[Stage 1] Detected: {total_nulls} nulls, {dup_count} duplicates")

    def _stage_clean(self):
        """Stage 2: Use pandas to clean based on mcp-excel detection."""
        if not hasattr(self, "_cleaner"):
            self._stage_inspect()
            self._stage_detect()

        detect = self.report["stages"].get("1_detect", {})
        nulls_info = detect.get("nulls", {})
        dups_count = detect.get("duplicates", {}).get("duplicate_count", 0)

        # Load data
        df = self._load_dataframe()
        rows_before = len(df)
        cols_before = list(df.columns)

        # --- Cleaning operations ---

        # 2a. Strip whitespace from string columns
        str_cols = df.select_dtypes(include=["object"]).columns
        for col in str_cols:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace("nan", pd.NA)

        # 2b. Drop fully-empty rows
        df = df.dropna(how="all")

        # 2c. Drop duplicate rows
        if dups_count > 0:
            df = df.drop_duplicates()

        # 2d. Handle nulls per column strategy
        for col, info in nulls_info.items():
            if col not in df.columns:
                continue
            null_count = info.get("null_count", 0)
            if null_count == 0:
                continue
            # Numeric: fill with median
            if pd.api.types.is_numeric_dtype(df[col]):
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
            else:
                # Categorical: fill with mode or "UNKNOWN"
                mode = df[col].mode()
                fill_val = mode[0] if len(mode) > 0 else "UNKNOWN"
                df[col] = df[col].fillna(fill_val)

        # 2e. Standardize column names (snake_case)
        df.columns = [
            c.strip().lower().replace(" ", "_").replace("-", "_").replace(".", "_")
            for c in df.columns
        ]

        rows_after = len(df)
        rows_cleaned = rows_before - rows_after

        # Save cleaned file
        self._save_dataframe(df)

        result = {
            "rows_before": rows_before,
            "rows_after": rows_after,
            "rows_cleaned": rows_cleaned,
            "nulls_filled": sum(1 for info in nulls_info.values() if info.get("null_count", 0) > 0),
            "duplicates_removed": dups_count,
            "columns_standardized": True,
        }
        self.report["stages"]["2_clean"] = result
        self.report["stats"]["rows_before"] = rows_before
        self.report["stats"]["rows_after"] = rows_after
        print(f"[Stage 2] Cleaned: {rows_before} → {rows_after} rows ({rows_cleaned} removed)")

    def _stage_validate(self):
        """Stage 3: Validate the cleaned output with mcp-excel."""
        if not Path(self.output_path).exists():
            self.report["stages"]["3_validate"] = {"error": "Output file not found"}
            return

        cleaner = MCPExcelCleaner(self.output_path, self.sheet_name)
        try:
            info = cleaner.inspect()
            detect = cleaner.detect()
            profile = cleaner.profile()
            self.report["stages"]["3_validate"] = {
                "output_exists": True,
                "output_rows": info["sheets"][0]["rows"] if info["sheets"] else 0,
                "output_cols": info["column_count"],
                "remaining_nulls": detect["total_nulls"],
                "remaining_dups": detect["duplicates"]["duplicate_count"],
                "valid": detect["total_nulls"] == 0 and detect["duplicates"]["duplicate_count"] == 0,
            }
            v = self.report["stages"]["3_validate"]
            status = "PASS" if v["valid"] else "WARN"
            print(f"[Stage 3] Validate: {status} — rows={v['output_rows']}, nulls={v['remaining_nulls']}, dups={v['remaining_dups']}")
        except Exception as e:
            self.report["stages"]["3_validate"] = {"error": str(e), "valid": False}
            print(f"[Stage 3] Validate: ERROR — {e}")

    def _load_dataframe(self) -> pd.DataFrame:
        """Load Excel or CSV into pandas DataFrame."""
        ext = Path(self.input_path).suffix.lower()
        if ext in (".xlsx", ".xls"):
            return pd.read_excel(self.input_path, sheet_name=self.sheet_name)
        elif ext == ".csv":
            return pd.read_csv(self.input_path)
        else:
            raise ValueError(f"Unsupported format: {ext}")

    def _save_dataframe(self, df: pd.DataFrame):
        """Save DataFrame to the output path."""
        ext = Path(self.output_path).suffix.lower()
        if ext in (".xlsx", ".xls"):
            df.to_excel(self.output_path, index=False, sheet_name=self.sheet_name or "Cleaned")
        elif ext == ".csv":
            df.to_csv(self.output_path, index=False)
        else:
            raise ValueError(f"Unsupported output format: {ext}")

    def save_report(self, path: str = None) -> str:
        """Save pipeline report to JSON."""
        if not path:
            stem = Path(self.input_path).stem
            path = str(Path(__file__).parent / f"mcp_pipeline_report_{stem}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        print(f"Report saved: {path}")
        return path


# ---- CLI ----
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MCP Excel/CSV Cleaning Pipeline")
    parser.add_argument("input", help="Input Excel/CSV file path")
    parser.add_argument("--output", "-o", default=None, help="Output file path")
    parser.add_argument("--sheet", default=None, help="Sheet name")
    parser.add_argument("--stage", default="0-1-2-3", help="Stages to run (e.g. '1-2', '0-1-2-3')")
    parser.add_argument("--report", default=None, help="Report output path")
    args = parser.parse_args()

    pipeline = MCPExcelPipeline(args.input, args.output, args.sheet)
    result = pipeline.run(args.stage)

    # Print summary
    stats = result.get("stats", {})
    print(f"\n{'='*50}")
    print(f"Pipeline Summary")
    print(f"{'='*50}")
    print(f"Input:     {result['input']}")
    print(f"Output:    {result['output']}")
    print(f"Format:    {stats.get('format', '?')}")
    print(f"Columns:   {stats.get('columns', [])}")
    print(f"Rows:      {stats.get('rows_before', '?')} → {stats.get('rows_after', '?')}")
    print(f"Nulls:     {stats.get('total_nulls', '?')} (filled)")
    print(f"Dups:      {stats.get('duplicate_count', '?')} (removed)")

    # Save report
    out_path = pipeline.save_report(args.report)
