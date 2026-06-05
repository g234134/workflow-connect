#!/usr/bin/env python3
"""
Wave 8 Run Summary 聚合脚本

扫描指定目录下的所有 run_summary.json 文件，生成运营视图聚合报告。

用法:
    python 04_Workflows/_wave8_aggregate_run_summaries.py --root delivery/ --pretty
    python 04_Workflows/_wave8_aggregate_run_summaries.py --root delivery/ --output agg.json --pretty
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def find_run_summaries(root_dir: str) -> list[Path]:
    """递归查找所有 run_summary.json 文件。"""
    root = Path(root_dir)
    if not root.exists():
        raise FileNotFoundError(f"根目录不存在: {root_dir}")
    return list(root.rglob("run_summary.json"))


def parse_summary_file(path: Path) -> dict[str, Any] | None:
    """解析单个 run_summary.json 文件。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[WARN] JSON 解析失败: {path} - {e}", file=sys.stderr)
    except Exception as e:
        print(f"[WARN] 读取失败: {path} - {e}", file=sys.stderr)
    return None


def extract_summary_data(data: dict, source_path: Path) -> dict[str, Any] | None:
    """提取关键字段，返回标准化摘要数据。"""
    try:
        identity = data.get("identity", {})
        outcome = data.get("outcome", {})
        qa_layers = data.get("qa_layers", {})
        runtime = data.get("runtime_stats", {})

        job_id = identity.get("job_id")
        product_sku = identity.get("product_sku")

        # 关键字段缺失则跳过
        if not job_id:
            print(f"[WARN] 缺少 job_id: {source_path}", file=sys.stderr)
            return None

        # 解析日期
        generated_at = data.get("generated_at", "")
        date_str = ""
        if generated_at:
            try:
                dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        # 解析 QA 状态
        qa_status = outcome.get("qa_status")
        overall_ok = outcome.get("overall_ok", False)
        job_status = outcome.get("job_status", "unknown")

        # 标准化 qa_status
        if qa_status is None:
            if job_status == "done" and overall_ok:
                effective_status = "pass"
            elif job_status == "failed":
                effective_status = "fail"
            else:
                effective_status = "unknown"
        else:
            effective_status = qa_status.lower() if isinstance(qa_status, str) else "unknown"

        # M2 信息
        m2_summary = qa_layers.get("m2_summary", {})
        m2_status = m2_summary.get("status", "unknown")
        m2_p0 = m2_summary.get("p0_failure_count", 0) or 0
        m2_p1 = m2_summary.get("p1_failure_count", 0) or 0

        return {
            "job_id": job_id,
            "product_sku": product_sku or "unknown",
            "date": date_str or "unknown",
            "effective_status": effective_status,
            "overall_ok": overall_ok,
            "job_status": job_status,
            "m2_status": m2_status,
            "m2_p0_failures": m2_p0,
            "m2_p1_failures": m2_p1,
            "has_m2_alert": m2_p0 > 0 or m2_p1 > 0,
        }
    except Exception as e:
        print(f"[WARN] 数据提取失败: {source_path} - {e}", file=sys.stderr)
        return None


def aggregate_summaries(summaries: list[dict]) -> dict[str, Any]:
    """聚合多个摘要数据为运营视图。"""
    total = len(summaries)

    # 按 product_sku 统计
    by_sku = defaultdict(lambda: {"total": 0, "ok": 0, "fail": 0, "unknown": 0})
    for s in summaries:
        sku = s["product_sku"]
        by_sku[sku]["total"] += 1
        status = s["effective_status"]
        if status == "pass":
            by_sku[sku]["ok"] += 1
        elif status in ("fail", "failed"):
            by_sku[sku]["fail"] += 1
        else:
            by_sku[sku]["unknown"] += 1

    # 按 qa_status 统计
    by_status = defaultdict(int)
    for s in summaries:
        by_status[s["effective_status"]] += 1

    # 按日期统计
    by_date = defaultdict(lambda: {"total": 0, "ok": 0, "fail": 0})
    for s in summaries:
        d = s["date"]
        by_date[d]["total"] += 1
        status = s["effective_status"]
        if status == "pass":
            by_date[d]["ok"] += 1
        elif status in ("fail", "failed"):
            by_date[d]["fail"] += 1

    # M2 告警统计
    m2_alerts = sum(1 for s in summaries if s["has_m2_alert"])
    m2_total_checked = sum(1 for s in summaries if s["m2_status"] != "skipped")

    # 构建结果
    result = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scan_summary": {
            "total_jobs": total,
            "valid_summaries": len(summaries),
        },
        "by_product_sku": dict(by_sku),
        "by_qa_status": dict(by_status),
        "by_date": dict(by_date),
        "m2_summary": {
            "jobs_with_m2_alerts": m2_alerts,
            "jobs_m2_checked": m2_total_checked,
            "m2_alert_rate": round(m2_alerts / m2_total_checked, 4) if m2_total_checked > 0 else 0.0,
        },
        "details": [
            {
                "job_id": s["job_id"],
                "product_sku": s["product_sku"],
                "status": s["effective_status"],
                "m2_status": s["m2_status"],
                "has_m2_alert": s["has_m2_alert"],
            }
            for s in summaries
        ],
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description="聚合 run_summary.json 文件，生成运营视图报告"
    )
    parser.add_argument(
        "--root",
        required=True,
        help="扫描的根目录（通常是 delivery/）",
    )
    parser.add_argument(
        "--output",
        help="可选，将聚合结果写入指定 JSON 文件",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="以缩进形式输出 JSON",
    )

    args = parser.parse_args()

    try:
        # 查找所有 run_summary.json
        print(f"[INFO] 扫描目录: {args.root}", file=sys.stderr)
        summary_paths = find_run_summaries(args.root)
        print(f"[INFO] 找到 {len(summary_paths)} 个 run_summary.json", file=sys.stderr)

        if not summary_paths:
            print(f"[ERROR] 未找到任何 run_summary.json 文件", file=sys.stderr)
            sys.exit(1)

        # 解析所有文件
        valid_summaries = []
        for path in summary_paths:
            data = parse_summary_file(path)
            if data is None:
                continue

            extracted = extract_summary_data(data, path)
            if extracted:
                valid_summaries.append(extracted)

        print(f"[INFO] 成功解析 {len(valid_summaries)}/{len(summary_paths)} 个文件", file=sys.stderr)

        if not valid_summaries:
            print(f"[ERROR] 未找到任何合法的 summary 数据", file=sys.stderr)
            sys.exit(1)

        # 聚合
        result = aggregate_summaries(valid_summaries)

        # 输出 JSON
        indent = 2 if args.pretty else None
        json_output = json.dumps(result, indent=indent, ensure_ascii=False)

        # 总是打印到 stdout
        print(json_output)

        # 可选写入文件
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_output)
                if not args.pretty:
                    f.write("\n")
            print(f"[INFO] 结果已写入: {args.output}", file=sys.stderr)

        sys.exit(0)

    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 执行失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
