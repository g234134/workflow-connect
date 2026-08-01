# TICKET STATE · W-MVP-W2-P4-DELIVERY-BUNDLE · 单案交付包 + delivery_signoff 模板

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 2 · P4 — Delivery bundle + signoff template（**不做** UI、邮件、自动发送）

---

## FRAME

- Goal: 为每个 `case_dir` 产出标准交付 bundle（cleaned + reports + eligibility + signoff），并约定模板位置与维护角色。
- Scope:
  - `case_dir` 内 bundle 结构约定（`cleaned/`、`reports/`、`delivery_signoff.md`）
  - `reports/eligibility_result.json`（P2 结果落盘）
  - `report.json` / `report.md` v1 契约轻量字段（case_id、client_ref、product_sku、cleaning_stats、issues_summary）
  - `scripts/build_case_delivery_bundle.py` 打包 CLI
  - `cases/_TEMPLATE_case/delivery_signoff.md` 模板正文
  - `tests/test_case_delivery_bundle.py`
- NonScope:
  - UI、邮件发送、计费、dispatch 自动触发
  - 重写清洗或 eligibility 逻辑
  - prod pipeline / W4-T1/T2 链
- AllowedPaths:
  - `cases/_TEMPLATE_case/delivery_signoff.md`
  - `cases/demo_phase/intake.json`（product_sku）
  - `notebooks/csv_cleaning/case_delivery_bundle.py`
  - `notebooks/csv_cleaning/clean_phase_demo.py`（report v1 字段）
  - `scripts/build_case_delivery_bundle.py`
  - `tests/test_case_delivery_bundle.py`
  - `04_Workflows/tickets/W-MVP-W2-P4-DELIVERY-BUNDLE_state.md`
- BlockedPaths:
  - `core/*`、`AGENTS.md`、`.cursor/rules/*`
  - 暗部 prod runner
- Dependencies:
  - W-MVP-W2-P1（case 目录结构）
  - W-MVP-W2-P2（`case_eligibility.py`）
  - W-MVP-W2-P3（`clean_phase_demo.py --case-dir`）
  - `docs/C2-P2_RUNBOOK.md` §19（Stage D signoff）
- AcceptanceCriteria:
  - `demo_phase` 上 `build_case_delivery_bundle.py` 成功
  - `eligibility_result.json`、`delivery_signoff.md`、report 文件齐全
  - 模板路径与维护角色写入 B_REPORT
  - 单元测试通过

---

## STATE

- overall_status: in_progress
- current_owner: implementer
- next_action: Reviewer 对照 AC 验收 bundle 结构与 demo 验证；Scribe 可选更新 C2-P2 附录路径
- last_updated: 2026-06-08 · implementer
- status_by_role:
  - orchestrator: pending
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

### changed_files

- `notebooks/csv_cleaning/case_delivery_bundle.py`（新建 · bundle 核心逻辑）
- `scripts/build_case_delivery_bundle.py`（新建 · CLI）
- `notebooks/csv_cleaning/clean_phase_demo.py`（report.json/md v1 契约字段）
- `cases/_TEMPLATE_case/delivery_signoff.md`（P4 正文模板）
- `cases/demo_phase/intake.json`（补 `product_sku`）
- `tests/test_case_delivery_bundle.py`（新建）
- `04_Workflows/tickets/W-MVP-W2-P4-DELIVERY-BUNDLE_state.md`（本档）

### bundle_structure_summary

```
case_dir/
  intake.json
  delivery_signoff.md          # Stage D 签核（人工 reviewer/signer 待填）
  raw/
    <source>.csv
  cleaned/
    <stem>_cleaned.csv
  reports/
    cleaning_stats.json        # 可选 · B/C 剖析
    report.json                # v1: case_id, client_ref, product_sku, cleaning_stats, issues_summary
    report.md                  # 人读：数据概览 / 清洗动作 / 已知限制
    eligibility_result.json    # P4 新增 · P2 gate 落盘
```

### cli_usage_examples

```bash
# 构建交付 bundle（默认读取已有 report；缺 signoff 则从模板生成）
python scripts/build_case_delivery_bundle.py --case-dir cases/demo_phase

# 完整 JSON 摘要
python scripts/build_case_delivery_bundle.py --case-dir cases/demo_phase --json

# 强制重跑 eligibility / 覆盖 signoff
python scripts/build_case_delivery_bundle.py --case-dir cases/demo_phase --refresh-eligibility --refresh-signoff
```

推荐顺序：P3 清洗 → P4 打包：

```bash
python notebooks/csv_cleaning/clean_phase_demo.py --case-dir cases/demo_phase --skip-eligibility --force
python scripts/build_case_delivery_bundle.py --case-dir cases/demo_phase
```

### template_location_and_owner

| 项 | 值 |
|----|-----|
| **模板路径** | `cases/_TEMPLATE_case/delivery_signoff.md` |
| **维护角色** | **Scribe / Product PM** — 更新 Stage D checklist 措辞与签核栏位说明 |
| **Implementer 边界** | 仅保证打包脚本从模板复制并填入 case/eligibility/report 摘要；不代填 Lead 签核 |

Signoff 要素（对齐 C2-P2 §19）：case_id / client_ref / product_sku、清洗摘要、eligibility status、reviewer/signer/signed_at、例外备注、Stage D checklist。

### report_v1_contract

`report.json` 顶层新增（保留既有 Wave6/C2-D1 区块）：

- `case_id` · `client_ref` · `product_sku` · `generated_at`
- `cleaning_stats`（row_counts + missing_value_stats + product_metrics）
- `issues_summary`（qa_status、error_categories、top_errors_sample）

`report.md` 章节：`数据概览` · `執行摘要` · `清洗动作摘要` · `已知限制/注意事项`

### demo_phase_verification

- `python scripts/build_case_delivery_bundle.py --case-dir cases/demo_phase --json` → `ok: true`
- `eligibility_status`: `review_needed`（rows<100 demo 样本）
- `reports/eligibility_result.json` 含 `status`、`checked_at`、`dimensions_summary`、`reasons`
- `delivery_signoff.md` 已存在（demo 保留既有文件；新案缺文件时从模板生成）
- `python -m unittest tests.test_case_delivery_bundle -v` → 3 tests OK

### artifacts

- `cases/demo_phase/reports/eligibility_result.json`（运行 bundle 后生成）

### verification

| 命令 | 结果 |
|------|------|
| `clean_phase_demo.py --case-dir cases/demo_phase --skip-eligibility --force` | `ok: true`, 5 output rows |
| `build_case_delivery_bundle.py --case-dir cases/demo_phase` | `bundle ok`, eligibility=review_needed |
| `python -m unittest tests.test_case_delivery_bundle -v` | 3 passed |

### behavior_notes

- 不重写 P2/P3；bundle 只读已有产物并调用 `check_case_eligibility`。
- 已有 `delivery_signoff.md` 默认不覆盖；`--refresh-signoff` 可从模板重建。
- `eligibility_result.json` 默认缓存；`--refresh-eligibility` 强制重跑。
- 无 UI / 邮件；stdout 打印 bundle 摘要。

### integration_notes_for_future

- **Dispatch**：可在 ticket `in_review` → `done` 前增加 gate：`build_case_delivery_bundle.py` exit 0。
- **Orchestrator**：Stage D 票可引用本 CLI 作为 DoD runner。
- **UI（远期）**：只读展示 `reports/report.md` + signoff checklist；发送仍走人工。
- **Scribe**：C2-P2 附录 B 可补 `reports/eligibility_result.json` 与 bundle CLI cross-ref。

### deferred_items

- `delivery_manifest.md` + SHA 清单（C2-P2 §18 可选产物）
- JSON Schema 落盘（Wave6 规划项）
- 自动邮件 / 客户门户

---

## C_REPORT

<!-- Reviewer 填 -->

---

## D_REPORT

<!-- Scribe 填 -->
