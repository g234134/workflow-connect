# _dry_run_liquidation.py — 數據清算戰役·Dry-run 入口
# 1) 中書省立案（current_plan.json）
# 2) 兵部清算器 dry-run 掃描（liquidation_preview_<run_id>.json）
# 嚴禁任何物理位移；本檔僅讀取與寫報告。

from __future__ import annotations

import json
import os
import sys
from collections import Counter

_workflows = os.path.dirname(os.path.abspath(__file__))
_agents_core = os.path.normpath(os.path.join(_workflows, "..", "02_Agents_Core"))
for _p in (_agents_core, _workflows):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from Liquidation_Agent import Liquidation_Agent  # type: ignore
from ZhongShu_Planner import ZhongShu_Planner  # type: ignore


def main() -> int:
    planner = ZhongShu_Planner()
    plan = planner.create_plan(
        goal="liquidate_quarantine_json",
        user_input={"dry_run": True, "scope": "quarantine", "extensions": [".json"]},
    )
    plan_path = planner._plan_path  # noqa: SLF001 — 取得 current_plan.json 絕對路徑

    liq = Liquidation_Agent(dry_run=True)
    out = liq.scan_quarantine_json()
    report = out["report"]

    # 額外彙整：副檔名／頂層鍵分布、最大 5 件、原因 Top10、format_error 樣本 5 件
    ext_counter: Counter[str] = Counter()
    top_key_counter: Counter[str] = Counter()
    reason_counter: Counter[str] = Counter()
    largest = []
    fmt_err_samples = []
    for r in report["records"]:
        ext_counter[os.path.splitext(r["name"])[1].lower()] += 1
        for k in r["top_keys"]:
            top_key_counter[str(k)] += 1
        reason_counter[r["reason"]] += 1
        largest.append((r["size_bytes"], r["name"], r["category"]))
        if r["category"] == "format_error" and len(fmt_err_samples) < 5:
            fmt_err_samples.append({
                "name": r["name"],
                "error": r["format_error"],
                "size_bytes": r["size_bytes"],
            })
    largest.sort(reverse=True)
    largest_top5 = [{"size_bytes": s, "name": n, "category": c} for (s, n, c) in largest[:5]]

    summary = {
        "plan_id": plan.plan_id,
        "plan_path": plan_path,
        "report_path": out["report_path"],
        "run_id": report["run_id"],
        "file_count": report["file_count"],
        "total_size_mb": round(report["total_size_bytes"] / (1024 * 1024), 2),
        "counters": report["counters"],
        "size_by_category_mb": {
            k: round(v / (1024 * 1024), 2) for k, v in report["size_by_category_bytes"].items()
        },
        "destinations": report["destinations"],
        "ext_top": ext_counter.most_common(5),
        "reason_top": reason_counter.most_common(10),
        "top_keys_top": top_key_counter.most_common(15),
        "largest_top5": largest_top5,
        "format_error_samples": fmt_err_samples,
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
