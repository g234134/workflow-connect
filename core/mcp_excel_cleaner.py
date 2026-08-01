#!/usr/bin/env python3
"""
mcp_excel_cleaner.py — 封裝 jwadow/mcp-excel 工具的清洗包裝層
Stage 0-3 全流程：探索 → 偵測 → 清洗 → 驗證
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# --- MCP-Excel venv path injection ---
MCP_VENV = Path(__file__).resolve().parent.parent / "01_Environments" / "python_venvs" / "mcp-excel-venv"
MCP_SRC = Path(__file__).resolve().parent.parent / "01_Environments" / "python_venvs" / "mcp-excel" / "src"


def _bootstrap():
    """Inject mcp-excel venv into sys.path, stripping Hermes pollution."""
    venv_site = str(MCP_VENV / "Lib" / "site-packages")
    src = str(MCP_SRC)
    # Remove any Hermes/hermes paths
    sys.path[:] = [p for p in sys.path if "Hermes" not in p and "hermes" not in p.lower()]
    # Insert mcp paths at front
    if venv_site not in sys.path:
        sys.path.insert(0, venv_site)
    if src not in sys.path:
        sys.path.insert(0, src)
    # Also clear PYTHONPATH env to prevent leakage
    os.environ.pop("PYTHONPATH", None)


_bootstrap()

from mcp_excel.operations.inspection import InspectionOperations
from mcp_excel.operations.validation import ValidationOperations
from mcp_excel.operations.statistics import StatisticsOperations
from mcp_excel.core.file_loader import FileLoader
from mcp_excel.models.requests import (
    InspectFileRequest,
    GetColumnNamesRequest,
    FindNullsRequest,
    FindDuplicatesRequest,
    GetColumnStatsRequest,
    GetDataProfileRequest,
    DetectOutliersRequest,
)


class MCPExcelCleaner:
    """
    Wraps mcp-excel operations into a data-cleaning workflow.

    Stages:
      Stage 0 — Inspect: file structure + column names
      Stage 1 — Detect: nulls, duplicates, unique values
      Stage 2 — Profile: column stats, outliers, value distributions
      Stage 3 — Report: JSON summary for downstream consumption
    """

    def __init__(self, file_path: str, sheet_name: Optional[str] = None):
        self.file_path = str(Path(file_path).resolve())
        self.sheet_name = sheet_name
        self.loader = FileLoader()
        self.insp = InspectionOperations(self.loader)
        self.val = ValidationOperations(self.loader)
        self.stat = StatisticsOperations(self.loader)
        self.columns: list[str] = []
        self.report: dict = {
            "file": self.file_path,
            "sheet": self.sheet_name,
            "stages": {},
            "timestamp": datetime.now().isoformat(),
        }

    # ---- Stage 0: Inspect ----
    def inspect(self) -> dict:
        """Get file structure and column names."""
        # File info
        r = self.insp.inspect_file(InspectFileRequest(file_path=self.file_path))
        sheets = [{"name": s["sheet_name"], "rows": s["row_count"], "cols": s["column_count"]} for s in r.sheets_info]
        self.sheet_name = self.sheet_name or sheets[0]["name"] if sheets else None

        # Column names
        cols_r = self.insp.get_column_names(
            GetColumnNamesRequest(file_path=self.file_path, sheet_name=self.sheet_name)
        )
        self.columns = list(cols_r.column_names)

        result = {
            "format": r.format,
            "size_bytes": r.size_bytes,
            "sheets": sheets,
            "active_sheet": self.sheet_name,
            "columns": self.columns,
            "column_count": cols_r.column_count,
        }
        self.report["stages"]["0_inspect"] = result
        return result

    # ---- Stage 1: Detect (nulls + duplicates + unique values) ----
    def detect(self) -> dict:
        """Find nulls, duplicates, and unique values per column."""
        if not self.columns:
            self.inspect()

        # Nulls
        nulls_r = self.val.find_nulls(
            FindNullsRequest(file_path=self.file_path, sheet_name=self.sheet_name, columns=self.columns)
        )
        nulls = {}
        for col, info in nulls_r.null_info.items():
            # info can be a dict or pydantic model
            nc = info.get("null_count", 0) if isinstance(info, dict) else info.null_count
            np_ = info.get("null_percentage", 0) if isinstance(info, dict) else info.null_percentage
            tr = info.get("total_rows", 0) if isinstance(info, dict) else info.total_rows
            nulls[col] = {
                "null_count": nc,
                "null_pct": round(np_, 1),
                "total_rows": tr,
            }
        total_nulls = nulls_r.total_nulls

        # Duplicates
        dups_r = self.val.find_duplicates(
            FindDuplicatesRequest(file_path=self.file_path, sheet_name=self.sheet_name, columns=self.columns)
        )
        dups = {
            "duplicate_count": dups_r.duplicate_count,
            "columns_checked": dups_r.columns_checked,
        }

        # Unique values per column via get_data_profile (replaces non-existent get_unique_values)
        uniques = {}
        try:
            profile_r = self.insp.get_data_profile(
                GetDataProfileRequest(file_path=self.file_path, sheet_name=self.sheet_name, columns=self.columns)
            )
            for col in self.columns:
                p = profile_r.profiles.get(col)
                if p:
                    uniques[col] = {
                        "unique_count": p.unique_count,
                        "data_type": p.data_type,
                        "top_values": p.top_values[:5] if p.top_values else [],
                    }
                else:
                    uniques[col] = {"unique_count": "unknown", "data_type": None}
        except Exception:
            uniques = {col: {"unique_count": "error", "data_type": None} for col in self.columns}

        result = {
            "nulls": nulls,
            "total_nulls": total_nulls,
            "duplicates": dups,
            "unique_values": uniques,
        }
        self.report["stages"]["1_detect"] = result
        return result

    # ---- Stage 2: Profile (column stats + outliers) ----
    def profile(self) -> dict:
        """Get statistics and outlier info for each column."""
        if not self.columns:
            self.inspect()

        stats = {}
        outliers = {}
        for col in self.columns:
            # Column stats
            try:
                s = self.stat.get_column_stats(
                    GetColumnStatsRequest(file_path=self.file_path, sheet_name=self.sheet_name, column=col)
                )
                st = s.stats
                stats[col] = {
                    "count": st.count,
                    "mean": round(st.mean, 2) if st.mean else None,
                    "median": st.median,
                    "std": round(st.std, 2) if st.std else None,
                    "min": st.min,
                    "max": st.max,
                    "null_count": st.null_count,
                }
            except Exception as e:
                stats[col] = {"error": str(e)}

            # Outliers (IQR method)
            try:
                o = self.stat.detect_outliers(
                    DetectOutliersRequest(file_path=self.file_path, sheet_name=self.sheet_name, column=col)
                )
                outliers[col] = {
                    "outlier_count": o.outlier_count,
                    "method": o.method if hasattr(o, "method") else "IQR",
                }
            except Exception:
                outliers[col] = {"outlier_count": 0, "method": "N/A"}

        result = {
            "column_stats": stats,
            "outliers": outliers,
        }
        self.report["stages"]["2_profile"] = result
        return result

    # ---- Stage 3: Full Report ----
    def full_report(self) -> dict:
        """Run all stages and return combined JSON report."""
        self.inspect()
        self.detect()
        self.profile()
        return self.report

    def save_report(self, output_path: Optional[str] = None) -> str:
        """Save report to JSON file."""
        if not self.report.get("stages"):
            self.full_report()
        if not output_path:
            stem = Path(self.file_path).stem
            output_path = str(Path(__file__).parent / f"mcp_clean_report_{stem}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        return output_path


# ---- CLI ----
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MCP-Excel Cleaner: inspect → detect → profile → report")
    parser.add_argument("file", help="Path to Excel/CSV file")
    parser.add_argument("--sheet", default=None, help="Sheet name (default: first sheet)")
    parser.add_argument("--stage", choices=["0", "1", "2", "all"], default="all", help="Stage to run")
    parser.add_argument("--output", default=None, help="Output JSON path")
    args = parser.parse_args()

    cleaner = MCPExcelCleaner(args.file, args.sheet)

    if args.stage == "0":
        result = cleaner.inspect()
    elif args.stage == "1":
        cleaner.inspect()
        result = cleaner.detect()
    elif args.stage == "2":
        cleaner.inspect()
        result = cleaner.profile()
    else:
        result = cleaner.full_report()

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.stage == "all":
        out = cleaner.save_report(args.output)
        print(f"\nReport saved: {out}", file=sys.stderr)
