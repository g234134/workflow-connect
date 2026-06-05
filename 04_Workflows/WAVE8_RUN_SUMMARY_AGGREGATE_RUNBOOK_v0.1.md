# Wave 8 Run Summary 聚合 Runbook v0.1

> **用途**：对 Wave 8 job 运行结果做批量汇总，形成最小运营视图。

---

## 目的

本脚本扫描指定目录（通常是 `delivery/`）下的所有 `run_summary.json` 文件，提取关键字段（job_id、product_sku、qa_status、M2 告警等），输出聚合统计报告。

适用于：
- 每日/批次作业完成后的快速健康检查
- 按产品维度统计成功率
- 识别需要关注的 M2 告警

---

## 前置条件

1. 已经有一批跑完的 job，每个 job 目录下有 `run_summary.json`
2. 目录结构示例：
   ```
   delivery/
   └── {job_id}/
       └── run_summary.json
   ```

---

## 使用示例

### 最简单用法（仅打印）

```bash
python 04_Workflows/_wave8_aggregate_run_summaries.py --root delivery/ --pretty
```

### 带输出文件（保存结果）

```bash
python 04_Workflows/_wave8_aggregate_run_summaries.py \
    --root delivery/ \
    --output 04_Workflows/outputs/run_summary_agg.json \
    --pretty
```

### 管道使用（供下游脚本消费）

```bash
python 04_Workflows/_wave8_aggregate_run_summaries.py --root delivery/ | jq '.total_jobs'
```

---

## 输出字段解读

### 顶层字段

| 字段 | 含义 |
|------|------|
| `generated_at` | 本报告生成时间（UTC） |
| `scan_summary.total_jobs` | 扫描到的 job 总数 |
| `scan_summary.valid_summaries` | 成功解析的 summary 数 |

### by_product_sku

按产品 SKU 分组统计：

```json
"CLEAN-BASIC": {
    "total": 10,   // 该 SKU 总 job 数
    "ok": 9,       // 成功数
    "fail": 1,     // 失败数
    "unknown": 0   // 状态不明数
}
```

### by_qa_status

全局 QA 状态分布：

```json
{
    "pass": 18,     // 通过
    "fail": 3,      // 失败
    "unknown": 2    // 未知（如缺少 qa_status）
}
```

### by_date

按日期分组（便于观察趋势）：

```json
"2026-06-04": {
    "total": 5,
    "ok": 4,
    "fail": 1
}
```

### m2_summary

M2 采样检查统计：

| 字段 | 含义 |
|------|------|
| `jobs_with_m2_alerts` | 有 M2 P0/P1 告警的 job 数 |
| `jobs_m2_checked` | 实际执行 M2 检查的 job 数 |
| `m2_alert_rate` | M2 告警率（小数） |

### details

每个 job 的明细列表（供调试或导出）：

```json
{
    "job_id": "w8-md-xxx",
    "product_sku": "CLEAN-BASIC",
    "status": "pass",
    "m2_status": "ok",
    "has_m2_alert": false
}
```

---

## 退出码

| 退出码 | 含义 |
|--------|------|
| `0` | 成功，至少找到 1 个合法 summary |
| `1` | 未找到任何合法 summary，或执行出错 |

---

## 故障排查

### 找不到任何 summary

```
[ERROR] 未找到任何 run_summary.json 文件
```

- 检查 `--root` 路径是否正确
- 确认目录下确实存在 `run_summary.json` 文件

### 解析失败过多

```
[WARN] JSON 解析失败: ...
```

- 查看 stderr 中的警告，定位损坏的文件
- 检查 run_summary.json 是否完整写入

---

## 版本历史

- **v0.1** (2026-06-05): 初始版本，支持按 SKU、日期、QA 状态、M2 告警聚合
