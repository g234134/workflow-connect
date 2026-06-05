"""讀取 wave_benchmark.jsonl 最後兩筆，輸出耗時與 Groq / 案例庫對照（含 429 韌性指標）。"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, Optional

from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
_root = bootstrap_sys_path(_here)

from gov_paths import get_tang_gov_root, resolve_agent_output_path  # type: ignore


def _groq_success_rate(row: Dict[str, Any]) -> Optional[float]:
    c = row.get("groq_calls")
    s = row.get("groq_success")
    try:
        c = int(c) if c is not None else 0
        s = int(s) if s is not None else 0
    except (TypeError, ValueError):
        return None
    if c <= 0:
        return None
    return round(100.0 * s / c, 2)


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--min-sampled",
        type=int,
        default=0,
        help="僅選 sampled≥此值的列做對照（例如 30000 避免混入小煙測）",
    )
    args = ap.parse_args()

    root = get_tang_gov_root()
    p = os.path.join(resolve_agent_output_path(root, "06_Exports_Output", "reports"), "wave_benchmark.jsonl")
    if not os.path.isfile(p):
        print(json.dumps({"ok": False, "error": "no_wave_benchmark_jsonl"}, ensure_ascii=False))
        return 0
    raw_rows = [json.loads(ln.strip()) for ln in open(p, "r", encoding="utf-8") if ln.strip()]
    m = int(args.min_sampled or 0)
    rows = raw_rows
    if m > 0:
        rows = [r for r in raw_rows if int(r.get("sampled") or 0) >= m]
        if len(rows) < 2:
            print(
                json.dumps(
                    {
                        "ok": True,
                        "hint": "need_at_least_two_benchmark_rows_after_filter",
                        "min_sampled": m,
                        "matched_rows": len(rows),
                        "last_match": rows[-1] if rows else None,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            print(
                "\n提示：套用 --min-sampled 後不足兩筆，無法對照前後波次；"
                "請再跑一輪同規模 Warpath 或暫時改用較小的 --min-sampled。\n",
                flush=True,
            )
            return 0
    if len(rows) < 1:
        print(json.dumps({"ok": False, "error": "empty_jsonl"}, ensure_ascii=False))
        return 0

    def _sec(x: dict) -> dict:
        return {
            "factory_wall_sec": x.get("factory_wall_sec"),
            "evaluate_duration_sec": x.get("evaluate_duration_sec"),
            "warpath_transcript_sec": x.get("warpath_transcript_sec"),
        }

    def _pct(old: float, new: float) -> float:
        if old is None or new is None or old <= 0:
            return 0.0
        return round(100.0 * (old - new) / old, 2)

    b = rows[-1]
    a = None
    for j in range(len(rows) - 2, -1, -1):
        if isinstance(rows[j].get("factory_wall_sec"), (int, float)):
            a = rows[j]
            break
    if a is None and len(rows) >= 2:
        a = rows[-2]
    if a is None:
        a = {}

    fa, ea, ta = (
        a.get("factory_wall_sec"),
        a.get("evaluate_duration_sec"),
        a.get("warpath_transcript_sec"),
    )
    fb, eb, tb = (
        b.get("factory_wall_sec"),
        b.get("evaluate_duration_sec"),
        b.get("warpath_transcript_sec"),
    )

    pair = None
    if isinstance(fa, (int, float)) and isinstance(fb, (int, float)):
        pair = ("factory_wall_sec", fa, fb)
    elif isinstance(ea, (int, float)) and isinstance(eb, (int, float)):
        pair = ("evaluate_duration_sec", ea, eb)
    elif isinstance(ta, (int, float)) and isinstance(tb, (int, float)):
        pair = ("warpath_transcript_sec", ta, tb)
    elif isinstance(ta, (int, float)) and isinstance(fb, (int, float)):
        pair = ("warpath_transcript_sec_vs_factory_wall_sec", ta, fb)

    ra, rb = _groq_success_rate(a), _groq_success_rate(b)
    groq_delta = None
    if ra is not None and rb is not None:
        groq_delta = round(rb - ra, 2)

    summary: Dict[str, Any] = {
        "ok": True,
        "path": p,
        "previous": {
            "run_id": a.get("run_id"),
            "label": a.get("label"),
            **_sec(a),
            "groq_calls": a.get("groq_calls"),
            "groq_success": a.get("groq_success"),
            "groq_success_rate_pct": ra,
            "case_library_hits": a.get("case_library_hits"),
            "local_judge_skips": a.get("local_judge_skips"),
        },
        "latest": {
            "run_id": b.get("run_id"),
            "label": b.get("label"),
            **_sec(b),
            "groq_calls": b.get("groq_calls"),
            "groq_success": b.get("groq_success"),
            "groq_success_rate_pct": rb,
            "case_library_hits": b.get("case_library_hits"),
            "local_judge_skips": b.get("local_judge_skips"),
        },
        "groq_success_rate_delta_pct_points": groq_delta,
    }
    if pair:
        name, old_v, new_v = pair
        summary["compare_field"] = name
        summary["speedup_pct_vs_previous"] = _pct(float(old_v), float(new_v))

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if pair:
        name, old_v, new_v = pair
        sp = summary.get("speedup_pct_vs_previous", 0)
        note = ""
        if name == "warpath_transcript_sec_vs_factory_wall_sec":
            note = "（口徑：前次為 PowerShell 轉錄全鏈秒數，本次為精煉工廠 process wall；僅供趨勢參考）"
        print(
            f"\n對照欄位「{name}」：前次 {old_v}s → 本次 {new_v}s；"
            f"本次相對前次數值 {'較低' if new_v < old_v else '較高'}，換算比例約 {abs(sp)}%。{note}\n",
            flush=True,
        )
    else:
        print(
            "\n無法自動對照秒數：請確認至少有一筆含 factory_wall_sec 或 evaluate_duration_sec，"
            "或兩筆皆為 warpath_transcript_sec。\n",
            flush=True,
        )

    if groq_delta is not None:
        direction = "改善" if groq_delta > 0 else "下降"
        print(
            f"Groq 成功率（成功/呼叫）：前次 {ra}% → 本次 {rb}%（{direction} {abs(groq_delta)} 個百分點；"
            f"正值通常代表 429/失敗負擔減輕）。\n",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
