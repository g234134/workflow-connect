# TICKET STATE · W-MVP-W2-P1-CASE-BOOTSTRAP · 案件目录 + intake 清单落盘

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 2 · P1 — Case folder + intake SSOT（**不做** eligibility 逻辑、**不做** prod 链、**不重写**清洗引擎）

---

## FRAME

- Goal: 为「低风险单表 CSV 清洗案」建立统一案件落盘结构与 intake 清单，使 P2（eligibility）、P3（`--case-dir` runner）、P4（delivery/signoff）可引用同一 SSOT。
- Scope:
  - 设计并落盘 `cases/_TEMPLATE_case/` 标准目录
  - `cases/README.md` + `cases/index.json` stub
  - `intake.json` 结构草案（对齐 Wave6 ACCEPT 维度 + C2-P1 §2.1/§2.4）
  - `cases/demo_phase/` 对齐新结构（raw/cleaned/reports + intake.json）
  - `delivery_signoff.md` 路径预留（P4 填内容）
  - 本票 B_REPORT 回写
- NonScope:
  - 不新建第二套清洗引擎；不改 W4-T1/T2 prod 链行为
  - 不实现 eligibility 自动判定（P2）
  - 不实现 `--case-dir` 通用 runner 参数化（P3；本票仅最小路径常量对齐 demo）
  - 不引入 RAG 主路径；不改 `core/*`、`tests/*`、`AGENTS.md`
  - 不更新 C2-D1/C2-P2 既有文档中的历史 flat 路径引用（留给 Scribe/P4）
- AllowedPaths:
  - `cases/**`
  - `notebooks/csv_cleaning/clean_phase_demo.py`（demo 路径常量最小对齐）
  - `notebooks/csv_cleaning/run_tabular_cleaning_plan.py`（demo_anchor 路径更新）
  - `04_Workflows/tickets/W-MVP-W2-P1-CASE-BOOTSTRAP_state.md`
- BlockedPaths:
  - `core/*`、`skills/*`、`config/*`、`tests/*`
  - `AGENTS.md`、`.cursor/rules/*`、`04_Workflows/00_Agent_Work_Progress.md`
  - W4-T1/T2 prod runner 实现
- Dependencies:
  - C2-P1 `docs/PRODUCT_TABULAR_CLEANING.md`（accepted*）
  - C2-P2 `docs/C2-P2_RUNBOOK.md`（Reviewer 收口后 AllowedPaths 冻结）
  - C2-D1 `cases/demo_phase/` + `clean_phase_demo.py`（demo 锚点）
  - Wave 1 `W-MVP-W1-INVENTORY_state.md` B_REPORT（Wave 2 P1 缺口）
  - `04_Workflows/WAVE6_CLEAN_INTAKE_ELIGIBILITY_v0.1.md`
- AcceptanceCriteria:
  - `cases/_TEMPLATE_case/` 存在且结构清晰
  - 至少一例（`demo_phase`）按新结构落盘
  - intake 字段在 README / index / template 中说明
  - 无新清洗引擎、无 prod 链改动
  - demo 可重跑（`clean_phase_demo.py` → `ok: true`）

---

## STATE

- overall_status: in_progress
- current_owner: implementer
- next_action: Reviewer 对照 AC 验收目录与 intake 结构；Orchestrator 开 P2 eligibility 票
- last_updated: 2026-06-08 · implementer
- status_by_role:
  - orchestrator: pending
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

### changed_files

- `cases/README.md`（新建 · 目录约定 + intake 字段说明）
- `cases/index.json`（新建 · case registry stub）
- `cases/_TEMPLATE_case/intake.json`
- `cases/_TEMPLATE_case/delivery_signoff.md`
- `cases/_TEMPLATE_case/raw/.gitkeep`
- `cases/_TEMPLATE_case/cleaned/.gitkeep`
- `cases/_TEMPLATE_case/reports/.gitkeep`
- `cases/demo_phase/intake.json`
- `cases/demo_phase/delivery_signoff.md`
- `cases/demo_phase/raw/Phase.csv`（自根目录迁入）
- `cases/demo_phase/cleaned/Phase_cleaned.csv`（自根目录迁入）
- `cases/demo_phase/reports/cleaning_stats.json`（自根目录迁入）
- `cases/demo_phase/reports/report.json`（自根目录迁入）
- `cases/demo_phase/reports/report.md`（自根目录迁入）
- `notebooks/csv_cleaning/clean_phase_demo.py`（CASE_DIR + raw/cleaned/reports 路径）
- `notebooks/csv_cleaning/run_tabular_cleaning_plan.py`（demo_anchor 路径 + intake 键）
- `04_Workflows/tickets/W-MVP-W2-P1-CASE-BOOTSTRAP_state.md`（本档）

### case_structure_summary

```
cases/
  README.md
  index.json
  _TEMPLATE_case/
    intake.json
    delivery_signoff.md      # P4 占位
    raw/
    cleaned/
    reports/
  demo_phase/                # 遗留 demo 锚点（结构已对齐 template）
    intake.json
    delivery_signoff.md
    raw/Phase.csv
    cleaned/Phase_cleaned.csv
    reports/cleaning_stats.json
    reports/report.json
    reports/report.md
```

正式新案推荐：`cases/<client_ref>/<case_id>/`（同 `_TEMPLATE_case` 子结构）。

### intake_schema_summary

契约版本 `gov-case-intake-v0.1`：

| 字段 | 用途 |
|------|------|
| `schema_version` | intake JSON 契约版本 |
| `case_id` · `client_ref` | 案号与客户引用 |
| `product_sku` | 产品 SKU（如 CLEAN-BASIC） |
| `intake_status` | draft / complete |
| `source.source_file` | raw 下相对路径 |
| `source.file_format` · `encoding` · `delimiter` | 解析参数 |
| `schema.id_column` · `required_columns` · `nullable_columns` | C2-P1 主键与可缺失栏 |
| `schema.date_columns` · `percent_columns` · `pii_columns` | 格式/合规 hint |
| `scale.expected_row_count` · `file_size_bytes` | Wave6 §3.1 规模 hint |
| `cleaning_goals` · `dedup_strategy` | 清洗目标与去重策略 |
| `provenance.source_type` · `data_owner` | Wave6 §3.2 来源 |
| `sensitivity.labels` · `contains_pii` | Wave6 §3.3 敏感度 |
| `structure.structure_type` | Wave6 §3.4（tabular = text_only） |
| `eligibility_hint` | 人工预判 accept/review/reject（非自动） |
| `eligibility_refs` | 引用的 eligibility / C2-P1 条文 |

### demo_alignment_notes

- `cases/demo_phase/` **内部**已迁入 `raw/`、`cleaned/`、`reports/`；新增 `intake.json` 填齐 C2-D1 维度。
- `clean_phase_demo.py` 已用 `CASE_DIR` 指向新子路径，demo 仍默认 `cases/demo_phase`（P3 再泛化为 `--case-dir`）。
- **留给 P3**：CLI `--case-dir`、从 `intake.json` 读 `source.source_file`、通用列规则配置。
- **留给 P2**：eligibility CLI 消费 `intake.json` 各维度做 ACCEPT/REVIEW/REJECT。
- **留给 P4**：`delivery_signoff.md` 正文模板与打包 manifest。
- **留给 Scribe**：更新 `docs/C2-D1_*`、`docs/C2-P2_RUNBOOK.md` 附录 B 中的 flat 路径引用 → 新子路径。

### artifacts

- `cases/_TEMPLATE_case/` — 可复制模板
- `cases/demo_phase/intake.json` — 填好的 demo 样例

### verification

- 命令：`python notebooks/csv_cleaning/clean_phase_demo.py`
- 预期：`{"ok": true, "input_rows": 7, "output_rows": 5, "report_json": "cases/demo_phase/reports/report.json"}`

### behavior_notes

- 保留 `cases/demo_phase/` 顶层路径作为 C2-D1 历史锚点，避免 `--case-dir` 默认值与 Wave 1 盘点不一致。
- `index.json` 为 stub registry，非 prod job queue。
- 最小改动 `clean_phase_demo.py` 仅为维持 demo 可重跑；完整参数化属 P3。

### deferred_items

- P2：eligibility 校验逻辑
- P3：`--case-dir` runner + intake-driven paths
- P4：`delivery_signoff.md` 模板正文 + delivery bundle 脚本
- Scribe：C2-D1/C2-P2 文档路径 cross-ref 更新

---

## C_REPORT

<!-- Reviewer 填 -->

---

## D_REPORT

<!-- Scribe 填 -->
