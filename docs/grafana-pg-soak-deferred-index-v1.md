# Grafana / PG Soak — Deferred Index (v1)

> **Ticket**: `FP-G5-T2-grafana-pg-soak-placeholder-index-v1` · Full-Phase G5 · P5 · **doc/spec · planning/deferred** · evidence_tier **L-local**  
> **Date**: 2026-07-10  
> **对齐**：`W-MASTER-full-phase-plan_state.md#G5` · Dashboard P5「Grafana/PG soak 仍 placeholder」叙事 · INDEX §1.5 metrics（只读）

---

## non_claims（置顶 · 必读）

| 本索引 **不是** | 说明 |
|-----------------|------|
| ≠ **Grafana** 已部署／已接 PG | 本页仅 **deferred 索引**；不执行 soak、不改 infra |
| ≠ soak **已跑通**／7d 绿表已填 | 执行属 **infra-only** 另线；本票禁止冒充验收 |
| ≠ **P5 closure**／Phase% 上调 | 索引齐 ≠ Phase 5 结案 |
| ≠ 授权改 `.github/workflows/**`／暗部／env | 宪法 §7 禁区类型仍适用 |

**位阶**

| 文件 | 角色 |
|------|------|
| **本档** | Grafana／PG soak **Landed vs Deferred** 索引 + 解阻条件 |
| [`docs/fleet-metrics-dashboard-operator-v1.md`](./fleet-metrics-dashboard-operator-v1.md) | CLI／HTTP fleet **operator 读法**（已有；≠ Grafana） |
| [`docs/WAVE_PROGRESS_DASHBOARD.md`](./WAVE_PROGRESS_DASHBOARD.md) | P5 完成度叙事（只读；本票不改 %） |
| INDEX §1.5 | MP／MC metrics runners（本地／CI；**非** Grafana） |

---

## 1. Purpose

诚实区分：

1. **Landed** — 本地／CI 可复跑的 metrics／health 能力（**仍非** Grafana）  
2. **Deferred** — Grafana 部署、PG soak、生产 scrape 等须 **infra／批文** 的项  

本票 **只写索引**；不部署、不跑 soak、不改 infra 脚本。

---

## 2. Landed（诚实已有 · 仍非 Grafana）

| ID | 能力 | 证据／入口 | 诚实边界 |
|----|------|------------|----------|
| L-01 | 单 case metrics exporter | `scripts/export_std_case_metrics_v1.py` · INDEX §1.5 | L-local；≠ Grafana panel |
| L-02 | Metrics HTTP scrape 端点 | `scripts/metrics_http_endpoint_v1.py` · `GET /metrics` | 本地／dev scrape；≠ 生产 Grafana 数据源已接 |
| L-03 | Fleet metrics 聚合 | `scripts/aggregate_multi_case_metrics_v1.py` · MC-METRICS | CLI rollup；≠ 仪表盘已上线 |
| L-04 | Fleet operator 读法 doc | `docs/fleet-metrics-dashboard-operator-v1.md`（FP-G5-T1） | doc ≠ 监控台 |
| L-05 | Toolchain health dashboard（离线） | `run_toolchain_health_dashboard`／WB-T4 叙事 | 离线健康度；≠ Grafana／PG soak |
| L-06 | P5 Grafana／JSON 对照 stub（本地） | `docs/p5-metrics-grafana-stub-contract-v1.md` · `scripts/run_p5_metrics_grafana_stub_v1.py`（P5-metrics-grafana-stub-v1） | Wave 4 可读字段；**仍 ≠** 真 Grafana／PG soak |

---

## 3. Deferred 索引（本票正文）

| Deferred ID | 延后项 | 为何延后 | 解阻 owner／前置 | 指针 |
|-------------|--------|----------|------------------|------|
| D-01 | **Grafana** 实例部署（staging／prod） | infra 资源与账号；非 doc 票范围 | Infra · 尚书省批文 | Dashboard P5 placeholder 句 |
| D-02 | Grafana **数据源接 PG**／metrics HTTP | 须网络／凭证／安全评审；禁本票碰 `.env` | Infra · Security | 宪法 §7 Z-ENV／Z-HQ-ENV-EDIT |
| D-03 | **PG soak** 执行与结果表 | 长时负载；须环境与窗口 | Infra · soak runbook 另票 | **infra-only**；本索引不跑 |
| D-04 | Soak 绿 → **P5 Phase% uplift** | 须证据 + 治理 uplift 流程 | Governance · Dashboard 维护方 | **禁止**本票改 % |
| D-05 | 生产默认 scrape／告警规则 | 产品／运维批文 | Infra · Ops | ≠ L-02 本地 endpoint |
| D-06 | Grafana 面板「fleet」与 MC-METRICS 字段对齐 | 依赖 D-01／D-02 | Infra + 另开 doc／实作票 | 链 T1 operator 字段语义 |

### Deferred 阅读规则

- 任一项未解阻前：Progress／Reviewer **禁止**写「Grafana 已上线」「PG soak 已通过」「P5 因 soak 已 closure」。  
- L-02（本地 HTTP）与 D-02（生产接 PG）**可并存**：有本地 scrape ≠ 生产 Grafana 已接。

### Infra 解阻条件（摘要）

| 条件 | 说明 |
|------|------|
| 环境就绪 | staging／约定 PG 与网络可达（路径见实例锚点；**本文不写绝对路径／密钥**） |
| 批文 | 尚书省／Infra 对部署与 scrape 范围的明示授权 |
| 证据 | soak 命令、窗口、结果摘要入 Progress **末尾 append**（另票／human） |
| 非本票 | 本档更新索引状态 ≠ 已执行 soak |

---

## 4. 与相邻 G5 文档分界

| 文档 | 本索引关系 |
|------|------------|
| `fleet-metrics-dashboard-operator-v1.md`（T1） | **如何读** CLI／HTTP；本档写 **何未落地** |
| `lane-progress-append-template-v1.md`（T3） | Progress 末尾模板；soak 证据若有则用其 append |
| `audit-quickview-fleet-extension-frame-v1.md`（T4） | audit 多 case FRAME；**不含** Grafana soak |

---

## 5. Mini checklist（编排／Reviewer）

- [ ] 提及 Grafana／soak 时：写明 **deferred** 或指向 D-01…D-06  
- [ ] 若声称已部署／已 soak／已 uplift Phase% → **Reject-over-claim**  
- [ ] 未改 infra／core／workflows／Phase%／金钥  

---

## 6. Verification（本票 AC · `rg`）

```bash
rg "Grafana|soak|deferred|infra|non_claims" docs/grafana-pg-soak-deferred-index-v1.md
```

期望命中：`non_claims`、Landed／Deferred、infra 解阻、soak／Grafana 否定句。
