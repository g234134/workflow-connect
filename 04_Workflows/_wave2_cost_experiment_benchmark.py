#!/usr/bin/env python3
"""
Wave 2 Chat D — synthetic cost benchmark (no live LLM).

Compares baseline vs cost_experiment profile for ask pipeline using
pricing.yaml rates and a fixed token profile derived from monitoring samples.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_GOV_CORE = _REPO / "01_Environments" / "python_venvs" / "gov_core_system"
if str(_GOV_CORE) not in sys.path:
    sys.path.insert(0, str(_GOV_CORE))

from core.cost_calculator import estimate_cost_usd  # noqa: E402
from core.cost_experiment import (  # noqa: E402
    ENV_COST_EXPERIMENT_CONFIG,
    active_profile,
    reload_cost_experiment_config,
)

_SAMPLE_COUNT = 20
# Per-trace token profile (ask): embed + 3x snippet context + answer generation.
_EMBED_IN = 120
_ANSWER_IN_BASELINE = 4200
_ANSWER_OUT = 280
_TOP_K = 3


def _per_trace_cost(model: str, answer_in: int) -> float:
    return estimate_cost_usd(
        model_name=model,
        input_tokens=_EMBED_IN + answer_in,
        output_tokens=_ANSWER_OUT,
    )


def _run_batch(*, experiment: bool) -> dict:
    if experiment:
        bench_cfg = _GOV_CORE / "config" / "cost_experiment.benchmark.yaml"
        os.environ[ENV_COST_EXPERIMENT_CONFIG] = str(bench_cfg)
    else:
        os.environ.pop(ENV_COST_EXPERIMENT_CONFIG, None)

    reload_cost_experiment_config()
    prof = active_profile("ask")
    model = str(prof["answer_model"])
    snippet = int(prof["snippet_max_chars"])
    # Scale input tokens vs baseline snippet cap (2000).
    answer_in = int(_ANSWER_IN_BASELINE * (snippet / 2000.0))
    if prof.get("experiment") and prof.get("compact_prompts"):
        answer_in = int(answer_in * 0.92)

    costs: list[float] = []
    ok = 0
    t0 = time.perf_counter()
    for _ in range(_SAMPLE_COUNT):
        c = _per_trace_cost(model, answer_in)
        costs.append(c)
        ok += 1
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    return {
        "experiment": bool(prof.get("experiment")),
        "profile": prof,
        "n": ok,
        "success_rate": ok / _SAMPLE_COUNT,
        "avg_cost_usd": sum(costs) / len(costs) if costs else 0.0,
        "total_cost_usd": sum(costs),
        "p50_cost_usd": sorted(costs)[len(costs) // 2] if costs else 0.0,
        "simulated_latency_ms_per_trace": elapsed_ms / _SAMPLE_COUNT,
    }


def main() -> int:
    baseline = _run_batch(experiment=False)
    optimized = _run_batch(experiment=True)

    b_avg = baseline["avg_cost_usd"]
    o_avg = optimized["avg_cost_usd"]
    savings = b_avg - o_avg
    savings_pct = (savings / b_avg * 100.0) if b_avg else 0.0

    report = {
        "pipeline": "dark_ops/ask (ask_pipeline)",
        "sample_count": _SAMPLE_COUNT,
        "baseline": baseline,
        "optimized": optimized,
        "delta": {
            "avg_cost_usd_saved": round(savings, 6),
            "avg_cost_pct_saved": round(savings_pct, 2),
            "success_rate_delta": optimized["success_rate"] - baseline["success_rate"],
        },
    }

    out_path = _GOV_CORE / "output" / "wave2_cost_experiment_benchmark.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
