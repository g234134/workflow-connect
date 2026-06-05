# Wave 8 总览（v0.1）

> **文档用途**：快速理解 Wave 8 版图与依赖关系  
> **受众**：接手工程师、CS、运营、尚書省  
> **更新日期**：2026-06-04  
> **状态**：草稿（随子域进展更新）

---

## 0. 一句话目标

Wave 8 在 Wave 6/7 数据清洗平台之上，交付 **客户可读的 Markdown 报告**、**抽样深度 QA（M2）** 及后续 **财务开票与桥接能力**，打通从原始数据到客户交付的「最后一公里」。

---

## 1. 子域清单

| 子域 | 票前缀 | 当前状态 | 关键文档 |
|------|--------|----------|----------|
| **M2 抽样 QA** | `W8-M2-*` | **DONE** | `WAVE8_M2_RUNBOOK_v0.1.md` |
| **REPORT-MD 报告** | `W8-REPORT-MD-*` | **IN_PROGRESS** | 4 份 runbook 见下方 |
| **Invoice 开票** | `W8-INVOICE-*` | **PLANNED** | 待创建 |
| **Bridge 桥接** | `W8-BRIDGE-*` | **PLANNED** | 待创建 |

### REPORT-MD 子票详情

| 子票 | 票号 | 性质 | 当前状态 |
|------|------|------|----------|
| RUNBOOK | `REPORT-MD-RUNBOOK` | operations / CS 指南 | 草稿待评审 |
| ORCH 集成 | `REPORT-MD-ORCH` | implementation | 待开工 |
| 渲染引擎 | `REPORT-MD-RENDER` | implementation | 待开工 |
| 模板契约 | `REPORT-MD-TEMPLATE` | spec | 草稿 |

---

## 2. 依赖关系图（文字版）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              上游平台层                                       │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐  │
│  │   Wave 6 清洗    │    │   Wave 7 存储    │    │   Wave 7 生命周期编排    │  │
│  │  (clean_engine)  │───▶│ (artifact_store)│◀───│    (job_lifecycle)      │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────┘  │
│           │                      │                      │                  │
│           └──────────────────────┴──────────────────────┘                  │
│                                  │                                         │
│                                  ▼                                         │
│  ╔═══════════════════════════════════════════════════════════════════════╗  │
│  ║                           Wave 8 子域层                              ║  │
│  ╠═══════════════════════════════════════════════════════════════════════╣  │
│  ║                                                                       ║  │
│  ║  ┌──────────────┐    ┌──────────────┐    ┌──────────┐    ┌─────────┐ ║  │
│  ║  │ M2 抽样 QA   │    │ REPORT-MD    │    │ Invoice  │    │ Bridge  │ ║  │
│  ║  │(抽样深检)    │    │(人读报告)    │    │ (开票)   │    │ (桥接)  │ ║  │
│  ║  └──────┬───────┘    └──────┬───────┘    └────┬─────┘    └────┬────┘ ║  │
│  ║         │                    │               │               │      ║  │
│  ║         └────────────────────┴───────────────┴───────────────┘      ║  │
│  ║                              │                                       ║  │
│  ╚══════════════════════════════╪═══════════════════════════════════════╝  │
│                                 │                                         │
│                                 ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                           下游消费者层                              │  │
│  │                                                                     │  │
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │  │
│  │   │   CS/客户     │    │    财务      │    │   外部系统        │   │  │
│  │   │ (report.md)   │◀───│ (invoice)    │◀───│ (bridge export)  │   │  │
│  │   └──────────────┘    └──────────────┘    └──────────────────┘   │  │
│  │                                                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘

关键依赖说明：
• M2 抽样 QA 依赖 Wave 7 manifest.json（M1 通过后才执行 M2）
• REPORT-MD 依赖 Wave 7 report.json + lifecycle 回传
• Invoice 依赖 REPORT-MD 中的 cost skeleton 与计费单位
• Bridge 依赖所有上游数据完成且 QA 通过
```

---

## 3. 子域详细说明

### 3.1 M2 抽样 QA（DONE）

M2 是对 `deliverables/envelopes/*.json` 进行**抽样深度检查**的 QA 层，与 M1 的全量 manifest 扫描形成互补。支持分层抽样、种子重现，P0 失败同样阻断 `Done` / `Chargeable`。

- **核心文件**：`core/wave8_m2_execution_engine.py`、`core/wave8_m2_sampling_design.py`
- **运维手册**：`WAVE8_M2_RUNBOOK_v0.1.md` §3–§7
- **典型调用**：`python .\04_Workflows\_wave8_m2_rerun.py --job-id xxx --sample-rate 0.1`

### 3.2 REPORT-MD 报告（IN_PROGRESS）

将 Wave 7 的 `report.json` 渲染为**客户可读的 Markdown 报告**（≤5 页），替代占位文案。包含章节导读、交通灯判定、FAQ 及升级排障路径。

- **模板契约**：`W8_REPORT_MD_TEMPLATE_AND_SECTIONS_v0.1.md`
- **渲染引擎**：`W8_REPORT_MD_RENDER_ENGINE_v0.1.md`
- **编排集成**：`W8_REPORT_MD_ORCH_INTEGRATION_v0.1.md`
- **CS 指南**：`W8_REPORT_MD_RUNBOOK_v0.1.md`（含附录 B 人话解释与 FAQ）

### 3.3 Invoice 开票（PLANNED）

基于 REPORT-MD 中的 `cost skeleton` 与计费单位，生成正式财务开票数据。当前 `chargeable_hint: false` 仅为提示，本域将对接财务系统实现真正的开票流转。

- **依赖**：REPORT-MD 完成 cost 章节规格锁定
- **状态**：待创建规划票

### 3.4 Bridge 桥接（PLANNED）

将验收通过的数据包桥接至下游系统（客户自建系统、第三方 API 或数据仓库）。可能包含格式转换、增量同步、失败重试等机制。

- **依赖**：M2 QA 通过 + REPORT-MD 确认交付
- **状态**：待创建规划票

---

## 4. 快速索引

### 4.1 文件路径（相对于战车根）

```
04_Workflows/
├── WAVE8_OVERVIEW_v0.1.md              ← 本文档
├── WAVE8_M2_RUNBOOK_v0.1.md            ← M2 运维手册
├── W8_REPORT_MD_RUNBOOK_v0.1.md          ← CS 阅读指南
├── W8_REPORT_MD_ORCH_INTEGRATION_v0.1.md ← 编排集成
├── W8_REPORT_MD_RENDER_ENGINE_v0.1.md   ← 渲染引擎
└── W8_REPORT_MD_TEMPLATE_AND_SECTIONS_v0.1.md ← 模板契约

01_Environments/python_venvs/gov_core_system/core/
├── wave8_m2_execution_engine.py          ← M2 执行引擎
└── wave8_m2_sampling_design.py           ← M2 抽样设计
```

### 4.2 关键 Checklist（接手工程师速查）

- [ ] 阅读 `WAVE8_M2_RUNBOOK_v0.1.md` §3 重跑 M2 场景
- [ ] 阅读 `W8_REPORT_MD_RUNBOOK_v0.1.md` 附录 B（CS 话术）
- [ ] 确认 `Master_Map.json` 中 `wave8_paths` 与 `wave8_bootstrap` 配置
- [ ] 跑通 M2 自检：`python .\04_Workflows\_wave8_m2_bootstrap.py --check --pretty`

---

## 5. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-06-04 | 初始草稿：M2（DONE）、REPORT-MD（IN_PROGRESS）、Invoice/Bridge（PLANNED）|

---

*Wave 8 总览 · `04_Workflows/WAVE8_OVERVIEW_v0.1.md` · v0.1*
