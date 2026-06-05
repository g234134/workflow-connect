"""_factory_wave_01.py — 全自動數據清洗工廠 · Wave-01

任務：
  · 載入 01_Environments/config/factory_pipeline.yaml 骨架（記錄 stages / cabin）
  · 對 05_Temp_Cache/cleaned_full 進行 100 件自動精煉（Asset_Value_Evaluator）
  · 每 10 件回報一次 Telegram + 局部更新 Status.json
  · 嚴守保密：絕不輸出任何金鑰原文

執行端建議：副艙 gov_agency 也可，以下 Agent 全 stdlib，雙艙皆可。
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
_root = bootstrap_sys_path(_here)

from Asset_Value_Evaluator_Agent import Asset_Value_Evaluator_Agent  # type: ignore
from Code_Cleaner_Throttled_Agent import _telegram_alert  # type: ignore
from GroqHybridRecovery_Agent import format_groq_quota_telegram_suffix  # type: ignore
from gov_paths import get_tang_gov_root, resolve_agent_output_path  # type: ignore


def _append_wave_benchmark(root: str, payload: Dict[str, Any]) -> str:
    rep = resolve_agent_output_path(root, "06_Exports_Output", "reports")
    os.makedirs(rep, exist_ok=True)
    path = os.path.join(rep, "wave_benchmark.jsonl")
    line = json.dumps(payload, ensure_ascii=False)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    return path


def _load_pipeline_yaml() -> Dict[str, Any]:
    """嘗試載入 factory_pipeline.yaml（PyYAML 缺席時降級為純文字偵測）"""
    cfg = os.path.join(_root, "01_Environments", "config", "factory_pipeline.yaml")
    if not os.path.isfile(cfg):
        return {"_source": cfg, "_status": "missing"}
    try:
        import yaml  # type: ignore
    except Exception:  # noqa: BLE001
        with open(cfg, "r", encoding="utf-8") as f:
            text = f.read()
        return {"_source": cfg, "_status": "raw_text", "size_chars": len(text)}
    with open(cfg, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data["_source"] = cfg
    data["_status"] = "loaded"
    return data


def _make_progress_callback() -> Any:
    def _cb(state: Dict[str, Any]) -> None:
        text = (
            "[Wave-01 進度]\n"
            f"已精煉 {state.get('processed')} / {state.get('of')}（池中 {state.get('pool_size')}）\n"
            f"當前均分 {state.get('avg_so_far')}  分布 {state.get('grades_so_far')}\n"
            f"Groq 呼叫 {state.get('groq_calls')}（成功 {state.get('groq_success')}） 案例庫 {state.get('case_library_hits', 0)} 預判 {state.get('local_judge_skips', 0)}"
        )
        try:
            ammo, cost = format_groq_quota_telegram_suffix()
            text += "\n" + ammo + "\n" + cost
        except Exception:  # noqa: BLE001
            pass
        try:
            _telegram_alert(text)
        except Exception:  # noqa: BLE001
            # 安全：絕不洩漏 token，且失敗不阻塞流水線
            pass

    return _cb


def main() -> int:
    parser = argparse.ArgumentParser(description="全自動清洗工廠 · Wave-01 (100 件精煉)")
    parser.add_argument("--n", "--wave", dest="n", type=int, default=100,
                        help="本波處理件數（--wave 為別名，與 --n 等價）")
    parser.add_argument("--every", type=int, default=10, help="每 N 件回報一次")
    parser.add_argument("--seed", type=int, default=None, help="隨機種子（不給則隨機）")
    args = parser.parse_args()

    seed = args.seed if args.seed is not None else random.SystemRandom().randint(1, 2**31 - 1)

    pipe = _load_pipeline_yaml()
    print("==== Wave-01 啟動 ====")
    print(f"  pipeline yaml : {pipe.get('_source')}  status={pipe.get('_status')}")
    if pipe.get("_status") == "loaded":
        stages = pipe.get("stages") or []
        print(f"  stages declared : {len(stages)}  ({[s.get('id') for s in stages]})")
    print(f"  cleaned_full pool root : {os.path.join(get_tang_gov_root(), '05_Temp_Cache', 'cleaned_full')}")
    print(f"  N={args.n}  progress_every={args.every}  seed={seed}")

    # 起戰前 Telegram 通報
    try:
        _telegram_alert(
            "[Wave-01 啟動]\n"
            f"目標：cleaned_full 抽樣精煉 {args.n} 件\n"
            f"節流：每 {args.every} 件回報；雲端僅介入灰區白名單副檔。"
        )
    except Exception:  # noqa: BLE001
        pass

    evaluator = Asset_Value_Evaluator_Agent(
        sample_size=args.n,
        seed=seed,
        progress_every=args.every,
        progress_callback=_make_progress_callback(),
    )
    wall0 = time.perf_counter()
    out = evaluator.run()
    wall_sec = round(time.perf_counter() - wall0, 3)
    if isinstance(out, dict) and "error" not in out:
        out["factory_wall_sec"] = wall_sec
        bench = {
            "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "wave_n": args.n,
            "progress_every": args.every,
            "seed": seed,
            "factory_wall_sec": wall_sec,
            **{k: out[k] for k in out if k in (
                "run_id", "pool_size", "sampled", "avg_score", "grades",
                "groq_calls", "groq_success", "case_library_loaded", "case_library_hits",
                "local_judge_skips",
                "evaluate_duration_sec", "report_path",
            )},
        }
        try:
            p = _append_wave_benchmark(_root, bench)
            print(f"  benchmark → {p}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"  benchmark append failed: {e}", flush=True)

    print("==== Wave-01 完成 ====")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
