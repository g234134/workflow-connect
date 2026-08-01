# Fleet Metrics Dashboard — Operator Doc (v1)

> **Ticket**: `FP-G5-T1-fleet-metrics-dashboard-doc-v1` · Full-Phase G5 · P5 · **doc/spec** · evidence_tier **L-local**  
> **Date**: 2026-07-10  
> **对齐**：`W-MASTER-full-phase-plan_state.md#G5` · MP-METRICS／MC-METRICS · INDEX §1.5 · Dashboard §Metrics（只读引用 · **不写 %**）

---

## non_claims（置顶 · 必读）

| 本档 **不是** | 说明 |
|---------------|------|
| ≠ **Grafana** 已部署／已接 PG | 本页仅 CLI／HTTP **operator 读法**；Grafana／PG soak 见 `grafana-pg-soak-deferred-index-v1.md` |
| ≠ **P5 closure**／Phase% 上调 | doc 齐 ≠ Phase 5 结案；**禁止**改 Dashboard 数字格 |
| ≠ 新建 metrics runtime／改 exporter 行为 | 只读引用既有脚本；本票 **不改** `scripts/**`／`core/**` |
| ≠ fleet「已上线」产品承诺 | MC-METRICS = 本地／CI 可复跑的 **fleet rollup**；≠ 生产监控台 |

**位阶**

| 文件 | 角色 |
|------|------|
| **本档** | Fleet 视图 **operator 读法／聚合边界** |
| [`04_Workflows/WORKFLOW_INDEX.md`](../04_Workflows/WORKFLOW_INDEX.md) **§1.5** | MP／MC／CI-SMOKE runner 索引 SSOT |
| [`docs/WAVE_PROGRESS_DASHBOARD.md`](./WAVE_PROGRESS_DASHBOARD.md) §Metrics | 完成度叙事（**只读**；本票不改 %） |
| [`docs/grafana-pg-soak-deferred-index-v1.md`](./grafana-pg-soak-deferred-index-v1.md) | Grafana／PG soak **deferred**（另票 T2） |
| [`docs/p5-metrics-grafana-stub-contract-v1.md`](./p5-metrics-grafana-stub-contract-v1.md) | 本地 Grafana／JSON 对照 stub（Wave 4 字段；≠ 真 Grafana） |
| [`docs/audit-quickview-fleet-extension-frame-v1.md`](./audit-quickview-fleet-extension-frame-v1.md) | audit fleet 聚合 FRAME（下游 T4 · 依赖本档） |

---

## 1. Purpose

说明如何用既有 **MP-METRICS**（单 case）与 **MC-METRICS**（多 case fleet）读 backlog／notification ack，并与 metrics HTTP 交叉引用——供 lane chat／Scribe／发版前 sanity 使用。

---

## 2. 读法：单 case → fleet

### 2.1 单 case（MP-METRICS）

| 入口 | 命令（索引） | 读什么 |
|------|--------------|--------|
| Exporter | `python scripts/export_std_case_metrics_v1.py --case-ref demo_phase --format json` | per-case pending／blocked／completed + notification ack |
| Prometheus text | 同上 `--format prometheus` | scrape 友好文本 |
| HTTP | `python scripts/metrics_http_endpoint_v1.py --port 9090` → `GET /metrics?case_ref=<slug>` | 本地 scrape；错误以 `# error:` + HTTP 200 |

票：`MP-METRICS-std-case-metrics-exporter-v1` · `MP-METRICS-HTTP-std-case-metrics-endpoint-v1`

### 2.2 Fleet 聚合（MC-METRICS）

| 入口 | 命令（索引） | 读什么 |
|------|--------------|--------|
| Aggregator | `python scripts/aggregate_multi_case_metrics_v1.py --format json` | `schema_version=multi_case_metrics_v1` · `metrics.total_*` · 可选 `per_case` |
| 覆盖 case 集 | `--cases demo_phase,sampleco/2026-0001` | 逗号分隔；默认代表性集合 |

票：`MC-METRICS-multi-case-metrics-aggregation-v1`

**默认代表性 case（与 Dashboard／INDEX 对齐）**

| case_ref | 用途 |
|----------|------|
| `demo_phase` | 标准 cleaning · 主 run lab |
| `sampleco/2026-0001` | 受控 profile · Checkpoint B |

### 2.3 与 smoke／CI 交叉

| 工具 | 关系 |
|------|------|
| MC-SMOKE | fleet **smoke** 扫；metrics 另看 MC-METRICS |
| CI-SMOKE | 单 case MP-SMOKE + MP-METRICS gate；**不**替代 fleet rollup |
| Release-sanity | `docs/phase6-release-sanity-runbook-v1.md`（MP→MC→CI-SMOKE） |

---

## 3. 聚合边界（operator 必守）

| 可做 | 不可做 |
|------|--------|
| 只读 rollup `total_pending_cases`／`total_blocked_cases`／`total_notifications_*_ack` | 把本地 JSON 写成「生产 Grafana 已绿」 |
| 用 `--cases` 缩小／扩大观察集 | 改 exporter／HTTP／aggregator 源码（另票） |
| 对照 per-case drill-down 查异常 case | 上调 Phase% 或宣称 P5 closure |
| 链 INDEX §1.5 runner 复跑 | 硬编本机绝对路径／打印金钥 |

**数据源诚实边界**：aggregator 对每案调用 `export_std_case_metrics`（library）——只读 backlog／event／feedback 视图；**不写** outbox。

---

## 4. Mini checklist（发版前／lane chat）

- [ ] 单 case：`export_std_case_metrics_v1.py --case-ref demo_phase --format json` → `ok` 语义可读  
- [ ] Fleet：`aggregate_multi_case_metrics_v1.py --format json` → 无意外 `total_notifications_failed_ack` 累积  
- [ ] 需要 scrape 时：HTTP endpoint 本地起 → `curl` `/metrics?case_ref=...`  
- [ ] 文案未写「Grafana 已上线」「P5 已 closure」  

---

## 5. Verification（本票 AC · `rg`）

```bash
rg "fleet|MC-METRICS|non_claims" docs/fleet-metrics-dashboard-operator-v1.md
```

期望命中：`non_claims`、fleet 读法、MC-METRICS／聚合边界、Grafana／P5 否定句。
