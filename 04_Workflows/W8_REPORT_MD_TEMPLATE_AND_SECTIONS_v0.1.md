# Wave 8 – REPORT-MD-TEMPLATE（v0.1）

> **票号**：`REPORT-MD-TEMPLATE`  
> **性质**：spec / template contract ticket  
> **范围**：`ART-DATA-CLEAN-REPORT` Markdown 结构、段落、表格、可选图表占位  
> **依据**：R3 §G.5–G.7；R4 `report_md`；`WAVE8_REPORT_MARKDOWN_OVERVIEW_v0.1.md` §2  
> **不做**：渲染代码、改 `report.json`、M2 逻辑

---

## 0. 背景

R2/R3 已裁定人读报告与 `report.json` 字段对齐（R3 §G.6），R4 已命名 `w6://delivery/{job_id}/report_md`。Wave 7 仅写入 `report.md` 占位。本票锁定 **对外 Markdown 章节契约**，供渲染器与快照测试引用。

---

## 1. 目标

定义 **客户版 / 内部版** 共用骨架与差异裁剪规则；固定表格列、徽章语义、免责声明文案 ID（便于 i18n 后续替换）。

---

## 2. 输入 / 输出

| 方向 | 内容 |
|------|------|
| **输入** | `report.json` 字段清单（§3 映射表）；配置 `audience`、`locale`（默认 `zh-CN`） |
| **输出** | 模板契约文档 + 2 份 **静态样例**（pass/skipped 与 pass_with_warnings+failures 各一，存 `04_Workflows/wave8/samples/`，路径由地图工单独登） |

---

## 3. Done 条件

- [ ] §0–§8 章节 ID 与总览 §2.2 一致；每节标明必填/条件/可选。  
- [ ] 客户版与内部版差异表（至少 5 条裁剪规则，如 failures 展开度）。  
- [ ] QA、cost、disclaimers 使用 **固定措辞 ID**（如 `DISCLAIMER-NOT-INVOICE`）。  
- [ ] 可选图表占位：§2 `volume` 可插「accepted/rejected 占比」ASCII 或 `<!-- chart:volume_pie -->` 注释，默认关闭。  
- [ ] 样例 Markdown 经人工评审，不依赖渲染器即可对照 R3 表。

---

## 4. 边界

- 不定义 PDF/CSS。  
- 不新增 `report.json` 键。  
- 不把 `customer_ack` / invoice 状态编进模板必填区。

---

*Wave 8 spec ticket · `04_Workflows/W8_REPORT_MD_TEMPLATE_AND_SECTIONS_v0.1.md`*
