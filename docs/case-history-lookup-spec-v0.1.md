# Case History Lookup Spec v0.1

> **票号**：`W4-MEM-01`（别名 `W-MVP-W4A-MEMO-LOOKUP` 字段补齐）  
> **类型**：只读轻量索引 · 非 RAG · 非 agent memory  
> **SSOT 索引**：`cases/index.json`  
> **维护脚本**：`scripts/build_cases_index.py`  
> **查询脚本**：`scripts/lookup_case_history.py`

---

## 1. 能回答的三类问题

| # | 问题 | 用法 |
|---|------|------|
| Q1 | 有没有历史案例？ | `--client-ref` · `--product-sku` · `--list-all` |
| Q2 | 这组表头见过吗？ | `--schema-headers Phase,名稱` |
| Q3 | 有什么已知限制 / 用过什么规则？ | 读 `known_limits` · `--verbose` 看 `cleaning_rules_applied` 与 `delivery_template_ref` |

---

## 2. 索引字段（`cases[]` 每项）

| 字段 | 必填 | 来源 |
|------|------|------|
| `case_dir` | 是 | 登记列表 |
| `client_ref` · `case_id` · `product_sku` | 是 | `intake.json` |
| `schema_headers` | 是 | raw/cleaned CSV header |
| `schema_notes` | 否 | 只读 `check_case_eligibility` → `dimensions.schema.notes` |
| `gate_status` | 是 | `reports/eligibility_result.json` |
| `cleaning_profile` | 是 | 登记表（`phase_demo_v1` / `clean_basic_demo`） |
| `cleaning_rules_applied` | 否 | `reports/report.json` |
| `delivery_template_ref` | 否 | `report.json` `meta.template_ref` 或 WAVE6 默认 |
| `qa_status` · `accepted_ratio` | 否 | `report.json` row_counts |
| `known_limits` | 是 | 静态标签 + gate reasons + schema notes + QA 启发式 |

---

## 3. CLI

### 刷新索引

```bash
python scripts/build_cases_index.py
python scripts/build_cases_index.py --json
```

扫描 `REGISTERED_CASE_DIRS`（当前：`demo_phase` · `sampleco/2026-0001`），写入 `cases/index.json`。

### 查询

```bash
python scripts/lookup_case_history.py --list-all
python scripts/lookup_case_history.py --client-ref sampleco
python scripts/lookup_case_history.py --schema-headers Phase,名稱
python scripts/lookup_case_history.py --client-ref sampleco --verbose
```

**stdout**（单一 JSON）：

```json
{
  "ok": true,
  "matches": [ { "case_dir": "...", "cleaning_profile": "...", "known_limits": [] } ],
  "notes": ["只登记 demo_phase, sampleco/2026-0001"]
}
```

---

## 4. 与 MVP 主链关系

- lookup **不**触发 gate / cleaning / bundle。  
- 接案推荐顺序：lookup → `new_cleaning_case.py` → gate → 清洗 → bundle（见 `docs/MVP_CASE_E2E_DoD_v0.1.md` §2）。  
- 护栏（schema 探针 · output ratio）见 `W-MVP-W4B-GUARD-*`；升格策略见 `W4-GUARD-01` 草案。

---

## 5. 限制与 deferred

- 登记列表硬编码；新案须扩展 `REGISTERED_CASE_DIRS` 后 refresh。  
- 无自然语言 query；无向量相似度。  
- 不输出「应选哪条 cleaner」决策。

---

*W4-MEM-01 · read-only case memory · 2026-06-13*
