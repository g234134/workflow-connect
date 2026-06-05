# Wave 8 – REPORT-MD-RENDER（v0.1）

> **票号**：`REPORT-MD-RENDER`  
> **性质**：implementation ticket  
> **范围**：`report.json` → Markdown 文本；纯函数 + CLI  
> **依据**：`W8_REPORT_MD_TEMPLATE_AND_SECTIONS_v0.1.md`；`wave7_report_summary_producer` 输出形状  
> **不做**：编排挂钩、M2、invoice/ack/bridge、修改 `report.json`

---

## 0. 背景

模板契约锁定后，需可重复、可单测的渲染入口，供 CI 与 CS 离线从既有 `report.json` 生成 `report.md`，且失败时不污染真相层。

---

## 1. 目标

实现 **`render_data_clean_report(report, *, config, display_context=None) -> {ok, markdown, message}`** 及 CLI（逻辑名见 `Master_Map.json` runners，本票不硬编码路径）。

---

## 2. 输入 / 输出

| 输入 | 说明 |
|------|------|
| `report` | 已解析的 `report.json` dict 或路径 |
| `config` | `audience`、`locale`、`include_appendix_internal` 等 |
| `display_context` | 可选；见总览 §5.2 |

| 输出 | 说明 |
|------|------|
| `markdown` | UTF-8 字符串 |
| `ok` / `message` | 缺必填块时 `ok=false`，**不写盘** |

---

## 3. Done 条件

- [ ] 纯函数：相同输入字节级稳定输出（除 `generated_at` 可注入固定值测快照）。  
- [ ] 覆盖：`qa_status` 三态、`sample_validation.status=skipped`、非空 `failures[]`、cost 全 null、`chargeable_hint` true/false。  
- [ ] CLI：`--report`、`--out`、`--audience`；退出码与 `ok` 对齐。  
- [ ] 单测 ≥8 用例，含「禁止重算 accepted_units」回归（改 manifest 不影响仅 report 输入之输出）。  
- [ ] 静态扫描：输出 Markdown 无 `:\` 磁盘根、无 env 键泄漏。

---

## 4. 边界

- 不调用 manifest / QA-M1 模块。  
- 不写 artifact store（落盘属 ORCH 票）。  
- 不使用外部模板引擎依赖（v0.1：标准库字符串/format 即可；若引入 Jinja 须另开依赖票）。

---

*Wave 8 implementation ticket · `04_Workflows/W8_REPORT_MD_RENDER_ENGINE_v0.1.md`*
