#!/usr/bin/env python3
"""
web_pipeline.py — 全自動網路數據清洗工作流 orchestrator

Stage 1: web_crawler.py  → 網路進料
Stage 2: web_cleaner.py  → 清洗 + 去重 + 進池
Stage 3: _factory_wave_01.py → 評估（已有）
Stage 4: _report_generator.py → 匯報（已有）

用法:
    python core/web_pipeline.py                       # 完整流程
    python core/web_pipeline.py --stage 1             # 只跑 Stage 1
    python core/web_pipeline.py --stage 1-2           # 只跑 Stage 1+2
    python core/web_pipeline.py --target github_trending_python  # 只爬特定目標
    python core/web_pipeline.py --dry-run             # 預覽不執行
    python core/web_pipeline.py --limit 10            # 限制下載數
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# ── Paths ───────────────────────────────────────
_REPO = Path(__file__).resolve().parent.parent
_CONFIG = _REPO / "core" / "web_pipeline_config.yaml"
_CRAWLER = _REPO / "core" / "web_crawler.py"
_CLEANER = _REPO / "core" / "web_cleaner.py"
_FACTORY = _REPO / "04_Workflows" / "_factory_wave_01.py"
_STAGING = _REPO / "05_Temp_Cache" / "web_staging"
_CLEANED_FULL = _REPO / "05_Temp_Cache" / "cleaned_full"
_REPORTS = _REPO / "06_Exports_Output" / "reports"
_LOG_DIR = _REPO / "05_Temp_Cache" / "web_pipeline_logs"

# Python interpreter with langchain venv
_PYTHON = str(_REPO / "01_Environments" / "python_venvs" / "langchain_latest" / "Scripts" / "python.exe")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_stage(cmd: list, stage_name: str, log_path: Path) -> int:
    """Run a stage and capture output to log file."""
    print(f"\n{'═' * 60}")
    print(f"  Stage: {stage_name}")
    print(f"  Cmd: {' '.join(cmd[:6])}...")
    print(f"{'═' * 60}")

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as log_f:
        proc = subprocess.run(
            cmd,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            cwd=str(_REPO),
            timeout=600,  # 10 min max per stage
        )

    # Print last 30 lines of log
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    for line in lines[-30:]:
        print(f"  │ {line.rstrip()}")

    print(f"  └─ Exit code: {proc.returncode}")
    print(f"  └─ Log: {log_path}")
    return proc.returncode


def stage_1_crawl(config: Path, target: Optional[str], dry_run: bool, limit: Optional[int]) -> int:
    """Stage 1: Crawl target websites."""
    cmd = [_PYTHON, str(_CRAWLER), "--config", str(config)]
    if target:
        cmd.extend(["--target", target])
    if dry_run:
        cmd.append("--dry-run")
    if limit:
        cmd.extend(["--limit", str(limit)])

    log = _LOG_DIR / f"stage1_crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    return _run_stage(cmd, "Stage 1: Web Crawler", log)


def stage_2_clean(config: Path, dry_run: bool) -> int:
    """Stage 2: Clean, dedup, add to pool."""
    cmd = [_PYTHON, str(_CLEANER), "--config", str(config)]
    if dry_run:
        cmd.append("--dry-run")

    log = _LOG_DIR / f"stage2_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    return _run_stage(cmd, "Stage 2: Web Cleaner", log)


def stage_3_evaluate(config: Path, sample_size: int = 50) -> int:
    """Stage 3: Evaluate new items in pool."""
    # Load config for evaluation settings
    import yaml  # type: ignore
    with open(config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    eval_cfg = cfg.get("evaluation", {})

    n = eval_cfg.get("sample_size", sample_size)
    factory_script = _REPO / eval_cfg.get("evaluator", "").replace(
        "02_Agents_Core/Asset_Value_Evaluator_Agent.py", ""
    ).parent / "_factory_wave_01.py" if eval_cfg.get("evaluator") else _FACTORY

    if not factory_script.exists():
        factory_script = _FACTORY

    # Use the factory wave script
    cmd = [_PYTHON, str(factory_script), "--n", str(n), "--every", "10"]
    log = _LOG_DIR / f"stage3_evaluate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    return _run_stage(cmd, f"Stage 3: Evaluate (sample {n})", log)


def stage_4_report() -> int:
    """Stage 4: Generate report."""
    report_script = _REPO / "04_Workflows" / "_report_generator.py"
    if not report_script.exists():
        print("  ⚠️ _report_generator.py not found, skipping Stage 4")
        return 0

    cmd = [_PYTHON, str(report_script)]
    log = _LOG_DIR / f"stage4_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    return _run_stage(cmd, "Stage 4: Report", log)


def _pool_size() -> int:
    """Get current cleaned_full pool size."""
    return sum(1 for _ in _CLEANED_FULL.glob("*.json")) if _CLEANED_FULL.exists() else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="全自動網路數據清洗工作流")
    parser.add_argument("--config", default=str(_CONFIG), help="Config YAML path")
    parser.add_argument("--stage", default="1-2-3-4", help="Stage range: 1, 2, 3, 4, 1-2, 1-2-3, 1-2-3-4")
    parser.add_argument("--target", default=None, help="Crawl only this target_id")
    parser.add_argument("--dry-run", action="store_true", help="Don't write files")
    parser.add_argument("--limit", type=int, default=None, help="Global download limit per target")
    parser.add_argument("--skip-eval", action="store_true", help="Skip Stage 3 (evaluation)")
    parser.add_argument("--skip-report", action="store_true", help="Skip Stage 4 (report)")
    args = parser.parse_args()

    # Parse stage range
    stages = args.stage.replace(" ", "").split("-")
    stage_set = set()
    for s in stages:
        if s.isdigit():
            stage_set.add(int(s))

    # Ensure log dir exists
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    pool_before = _pool_size()
    start_time = time.time()

    print(f"{'═' * 60}")
    print(f"  全自動網路數據清洗工作流")
    print(f"  Started: {_ts()}")
    print(f"  Stages: {sorted(stage_set)}")
    print(f"  Pool before: {pool_before}")
    print(f"  Config: {args.config}")
    print(f"  Dry run: {args.dry_run}")
    print(f"{'═' * 60}")

    results = {}

    # Stage 1: Crawl
    if 1 in stage_set:
        rc = stage_1_crawl(Path(args.config), args.target, args.dry_run, args.limit)
        results["stage1"] = rc
        if rc != 0:
            print(f"\n⚠️ Stage 1 failed (exit {rc}), continuing with Stage 2...")

    # Stage 2: Clean
    if 2 in stage_set:
        rc = stage_2_clean(Path(args.config), args.dry_run)
        results["stage2"] = rc

    # Stage 3: Evaluate
    if 3 in stage_set and not args.skip_eval:
        rc = stage_3_evaluate(Path(args.config))
        results["stage3"] = rc

    # Stage 4: Report
    if 4 in stage_set and not args.skip_report:
        rc = stage_4_report()
        results["stage4"] = rc

    pool_after = _pool_size()
    elapsed = time.time() - start_time

    # Summary
    print(f"\n{'═' * 60}")
    print(f"  Pipeline Complete")
    print(f"  Finished: {_ts()}")
    print(f"  Elapsed: {elapsed:.1f}s")
    print(f"  Pool: {pool_before} → {pool_after} (+{pool_after - pool_before})")
    print(f"  Results:")
    for stage, rc in sorted(results.items()):
        status = "✅" if rc == 0 else "❌"
        print(f"    {stage}: {status} (exit {rc})")
    print(f"{'═' * 60}")

    # Save run summary
    summary_path = _LOG_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    summary = {
        "started_at": datetime.fromtimestamp(start_time, tz=timezone.utc).isoformat(),
        "finished_at": _ts(),
        "elapsed_sec": round(elapsed, 2),
        "pool_before": pool_before,
        "pool_after": pool_after,
        "pool_delta": pool_after - pool_before,
        "stages_run": sorted(stage_set),
        "results": {k: {"exit_code": v} for k, v in results.items()},
        "dry_run": args.dry_run,
        "target": args.target,
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return 0 if all(v == 0 for v in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
