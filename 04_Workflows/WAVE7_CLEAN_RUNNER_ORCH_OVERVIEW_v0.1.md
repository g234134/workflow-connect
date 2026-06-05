# Wave 7 – CLEAN-RUNNER/ORCH · 总览（v0.1）

> **轮次**：Wave 7 · **性质**：planning / implementation wave overview  
> **前置**：Wave 6 v1.0 规格已冻结；ENVELOPE-V2 / MANIFEST-V2 / QA-M1 已实现并通过单测  
> **Wave 8 分界**：M2 抽样、Markdown 报告渲染、customer_ack、invoice、bridge sidecar 均不在本波  
> **状态**：**PLANNED-v0.1**

---

## 1. 范围摘要

Wave 7 把 Wave 6 **已冻结的单模块能力**装配成 **一次可重跑、可审计的 job 执行链**，但不扩规格（不做 M2 抽样 QA、不做 Phase 6.5 开票/bridge 实作、不做 BASIC→ENRICH 升级 job）。

路径一律经 `Master_Map.json` / `gov_paths`；交付引用用 R4 裁定的 `w6://delivery/{job_id}/{kind}`，**禁止**绝对路径泄漏。

Wave 7 结束时：一条 CLI/runner 命令能对 **真实 cleaned_full 批次或队列消息**跑完 BASIC job，产出四件套目录骨架 + 结构化 `dict` 回传。

---

## 2. 与 Wave 6 / Wave 8 的边界

### 2.1 Wave 6（已完成 · 本波只消费）

- ENVELOPE-V2、MANIFEST-V2、QA-M1 模块层能力已交付。
- 现有 E2E smoke 在内存里手工构造 `job_record` + `raw_files`，串起 `write_envelopes → write_manifest → run_m1_checks`。
- QA-M1 的 `M1-COUNT` 依赖 `report.summary.accepted_units`，但测试里用 `_qa_report()` stub，**尚无正式 report 生产者**。

### 2.2 Wave 7（本波交付）

- **runner 入口**（真实 input → `job_record` + raw 列表）
- **pipeline orchestrator**（阶段顺序 + 失败语义）
- **artifact store**（envelope/manifest/report 落盘 + 幂等）
- **report.summary 生产者**（供 QA-M1 与 Done 判定）
- **job lifecycle 持久化**
- **集成回归门禁**（含现有 E2E smoke 升格）

### 2.3 Wave 8（明确不在本波）

- M2 抽样 QA
- Markdown 报告渲染（`ART-DATA-CLEAN-REPORT`）
- `customer_ack` / invoice
- bridge sidecar 实作
- BASIC→ENRICH 升级 job（§I）
- Phase 6.5 `delivery.status` 实体

---

## 3. 核心交付链路

```text
runner entry
  → orchestrator（阶段顺序 + 失败语义）
  → artifact store（envelope / manifest / report 落盘 + 幂等）
  → report summary 生产者（供 QA-M1 与 Done 判定）
  → job lifecycle 持久化
```

**runner 入口**：从真实文件批次或队列消息构造 `job_record` 与原始 input 列表。

**orchestrator**：串联 intake（可选）→ raw 加载 → envelope → manifest → report summary → QA-M1 → 落盘 finalize。

**artifact store**：统一管理 per-file envelope、`manifest.json`、`report.json` 草稿目录、失败回收区；支持幂等重跑与部分失败隔离。

**report summary**：正式 `report.json` 生产者，尤其 `report.summary.*` 与 QA 区块骨架。

**lifecycle**：单 job 状态机（`pending` / `running` / `blocked` / `done` / `failed`），含失败处理与重试策略。

---

## 4. 票面索引

| 票名 | 文件 | 一句话 |
|------|------|--------|
| `RUNNER-ENV-BOOTSTRAP` | `WAVE7_RUNNER_ENV_BOOTSTRAP_v0.1.md` | runner/orchestrator 唯一环境引导入口 |
| `RUNNER-ENTRY-JOB-INPUT` | `WAVE7_RUNNER_ENTRY_JOB_INPUT_v0.1.md` | 从真实批次/队列构造 `job_record` + `raw_files[]` |
| `ARTIFACT-STORAGE-PATH-GOV` | `WAVE7_ARTIFACT_STORAGE_PATH_GOV_v0.1.md` | 工件落盘、路径治理、幂等重跑与错误回收 |
| `ORCH-PIPELINE-WIRE` | `WAVE7_ORCH_PIPELINE_WIRE_v0.1.md` | Wave 6 四模块按冻结顺序硬接线 |
| `REPORT-SUMMARY-PRODUCER` | `WAVE7_REPORT_SUMMARY_PRODUCER_v0.1.md` | 正式 `report.json` 与 `report.summary.*` 生产者 |
| `ORCH-JOB-LIFECYCLE` | `WAVE7_ORCH_JOB_LIFECYCLE_v0.1.md` | 单 job 编排器与状态机 |
| `INT-REGRESSION-GATE` | `WAVE7_INT_REGRESSION_GATE_v0.1.md` | Wave 6/7 集成回归门禁 |

---

## 5. 建议实施顺序与依赖

```mermaid
flowchart LR
  A[RUNNER-ENV-BOOTSTRAP] --> B[RUNNER-ENTRY-JOB-INPUT]
  B --> C[ARTIFACT-STORAGE-PATH-GOV]
  C --> D[ORCH-PIPELINE-WIRE]
  D --> E[REPORT-SUMMARY-PRODUCER]
  E --> F[ORCH-JOB-LIFECYCLE]
  F --> G[INT-REGRESSION-GATE]
```

1. **ENV-BOOTSTRAP** → **RUNNER-ENTRY**（能构造 job）
2. **ARTIFACT-STORAGE**（能落盘）
3. **PIPELINE-WIRE** + **REPORT-SUMMARY**（可并行，但 report 依赖 manifest）
4. **JOB-LIFECYCLE**（包住全流程）
5. **INT-REGRESSION-GATE**（最后锁门禁，或随 E 起增量维护）

---

## 6. Wave 6 E2E smoke 升格为集成回归门

现有 `test_wave6_e2e_smoke` 在 Wave 7 完成后升格为 **INT-REGRESSION-GATE Tier-A（必跑）** 子集之一：任何改动 envelope / manifest / QA / orchestrator / runner 时须与模块层单测一并全绿，防止「模块层通过、装配层退化」。Tier-A 明细与不变量表见 `WAVE7_INT_REGRESSION_GATE_v0.1.md`；与 `GOV_CORE` smoke runbook 交叉索引即可，不在本总览展开 Tier 细节。

---

## 7. 本波 Done 判定（Wave 7 级）

一条 CLI/runner 命令能对 **真实 cleaned_full 批次或队列消息**跑完 BASIC job，产出四件套目录骨架 + 结构化 `dict` 回传；现有 `test_wave6_e2e_smoke` 已纳入集成回归门禁 Tier-A。

---

## 8. 占位 / 不在本波（skeleton 声明）

| 项 | 说明 |
|----|------|
| M2 抽样 QA | Wave 8 |
| Markdown 报告（`ART-DATA-CLEAN-REPORT`） | Wave 8 |
| `customer_ack` / invoice | Wave 8 / Phase 6.5 |
| bridge sidecar 实作 | Wave 8 |
| BASIC→ENRICH 升级 job | 不在 Wave 7 |
| Phase 6.5 `delivery.status` 实体 | 不在 Wave 7 |
| 远程 object store | 不在 Wave 7 |

---

*Wave 7 planning overview · `04_Workflows/WAVE7_CLEAN_RUNNER_ORCH_OVERVIEW_v0.1.md`*
