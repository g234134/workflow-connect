# TICKET STATE · W-MVP-W4A-MEMO-LOOKUP · 历史案例 lookup CLI

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 4A · W-MVP — MEMO lookup（**只读索引**；**不触发**清洗 / gate / RAG）

---

## FRAME

> 冻结来源：`W-MVP-W4A-MEMO-ORCH_state.md`（Orchestrator · Wave 4A MEMO）

- Goal: 实现薄的「历史案例/规则 lookup」CLI，扩展 `cases/index.json`，供结构化参数查询已登记 case。
- Scope:
  - 扩展 `cases/index.json`（`schema_headers` · `gate_status` · `known_limits[]`）
  - 最小 index 刷新工具（扫描 `demo_phase` + `sampleco/2026-0001`）
  - `scripts/lookup_case_history.py` CLI（`--client-ref` · `--product-sku` · `--schema-headers` · `--list-all`）
  - 1–2 个 pytest / unittest
- NonScope:
  - 不构建向量库 / RAG
  - 不修改 gate / cleaning / bundle 逻辑
  - 不对自然语言 query 做解析（只收结构化参数）
  - 不改 core pipeline
- AllowedPaths:
  - `cases/index.json`
  - `scripts/cases_index_lib.py`
  - `scripts/build_cases_index.py`
  - `scripts/lookup_case_history.py`
  - `tests/test_lookup_case_history.py`
  - `04_Workflows/tickets/W-MVP-W4A-MEMO-LOOKUP_state.md`
- BlockedPaths:
  - `core/*` · `notebooks/csv_cleaning/*`（gate/cleaning 引擎）
  - `AGENTS.md` · `.cursor/rules/*`
- Dependencies:
  - `W-MVP-W4A-MEMO-ORCH`（FRAME 冻结）
  - 既有 `cases/demo_phase/**` · `cases/sampleco/2026-0001/**`
  - `intake.json` · `reports/eligibility_result.json`（只读）
- AcceptanceCriteria:
  - `cases/index.json` 含两案 FRAME 字段
  - lookup CLI 只读 index，过滤输出 `{ ok, matches[], notes[] }`
  - `--list-all` 含 demo_phase 与 sampleco；`--client-ref SAMPLECO` 仅 sampleco
  - B_REPORT 含 index_structure / cli_usage / limitations / reuse_notes / scope out

---

## STATE

- overall_status: in_progress
- current_owner: reviewer
- next_action: Reviewer 对照 AC 验收 lookup CLI 与 index 结构；Scribe 可引用 B_REPORT 写 Wave 4C demo 文案
- last_updated: 2026-06-08 · implementer
- status_by_role:
  - orchestrator: pending
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

### reuse_notes（Step 0 · Module Reuse Check）

**复用模块：**

| 模块 | 用途 |
|------|------|
| `cases/index.json` | 既有 registry 壳；本票扩展 `schema_headers` / `gate_status` / `known_limits` |
| `notebooks/csv_cleaning/case_intake_loader.py` | 参考 intake 路径解析（本票未 import，避免动 dark 路径） |
| `scripts/new_cleaning_case.py` | 参考 `client_ref` slug 与 case_dir 布局 |
| `scripts/check_case_eligibility.py` | 参考 gate 输出字段（`status` ← `eligibility_result.json`） |
| `cases/demo_phase/**` · `cases/sampleco/2026-0001/**` | 首批登记扫描对象 |

**确认：** 本票不触发任何额外清洗或 gate，只读文件生成索引与 lookup 结果。

### changed_files

- `scripts/cases_index_lib.py`（新建 · index 刷新 + lookup 共享逻辑）
- `scripts/build_cases_index.py`（新建 · 刷新 `cases/index.json`）
- `scripts/lookup_case_history.py`（新建 · lookup CLI）
- `tests/test_lookup_case_history.py`（新建 · 5 条 unittest）
- `cases/index.json`（扩展两案 MEMO 字段）
- `04_Workflows/tickets/W-MVP-W4A-MEMO-LOOKUP_state.md`（本档）

### index_structure

顶层仍为 `gov-cases-index-v0.1` 对象；`cases[]` 每项新增 MEMO 字段：

```json
{
  "schema_version": "gov-cases-index-v0.1",
  "cases": [
    {
      "case_dir": "cases/demo_phase",
      "client_ref": "internal-demo",
      "case_id": "demo_phase",
      "product_sku": "CLEAN-BASIC",
      "schema_headers": ["Phase", "名稱", "之前", "現在（建議）"],
      "gate_status": "review_needed",
      "known_limits": ["legacy_demo_path", "rows<100", "size<1024", "manual_review_required"],
      "intake_path": "cases/demo_phase/intake.json",
      "status": "demo_anchor",
      "source_file": "raw/Phase.csv"
    },
    {
      "case_dir": "cases/sampleco/2026-0001",
      "client_ref": "sampleco",
      "case_id": "2026-0001",
      "product_sku": "CLEAN-BASIC",
      "schema_headers": ["Phase", "名稱", "之前", "現在（建議）"],
      "gate_status": "accepted",
      "known_limits": [],
      "intake_path": "cases/sampleco/2026-0001/intake.json",
      "source_file": "raw/sampleco_milestone_export.csv"
    }
  ]
}
```

刷新命令：`python scripts/build_cases_index.py`（扫描 `REGISTERED_CASE_DIRS` 固定两案，不写 gate 结果）。

### cli_usage_examples

```bash
# 1) 列出全部登记
python scripts/lookup_case_history.py --list-all
# 预期片段：ok=true；matches 含 cases/demo_phase 与 cases/sampleco/2026-0001

# 2) 按 client_ref 精确匹配（大小写不敏感）
python scripts/lookup_case_history.py --client-ref SAMPLECO
# 预期：matches 长度 1；case_dir=cases/sampleco/2026-0001

# 3) schema 子集匹配
python scripts/lookup_case_history.py --schema-headers Phase,名稱
# 预期：两案均匹配（headers 为 Phase 表四列的超集）
```

stdout 形状：

```json
{
  "ok": true,
  "matches": [
    {
      "case_dir": "cases/sampleco/2026-0001",
      "client_ref": "sampleco",
      "product_sku": "CLEAN-BASIC",
      "gate_status": "accepted",
      "known_limits": []
    }
  ],
  "notes": ["只登记 demo_phase, sampleco/2026-0001"]
}
```

### limitations

- 当前仅登记 `cases/demo_phase` 与 `cases/sampleco/2026-0001`（`REGISTERED_CASE_DIRS` 硬编码）。
- `schema_headers` 比对为简化逻辑（query 集合 ⊆ case 集合或相等；大小写不敏感），**并非**通用 schema fingerprint。
- lookup **不**主动扫描 `cases/`；新案须先跑 `build_cases_index.py` 并扩展登记列表。
- `gate_status` 来自既有 `reports/eligibility_result.json`；无文件时为 `not_run`。

### reuse_notes（下游）

| 下游 | 支撑方式 |
|------|----------|
| **W-MVP-W4A-MEMO-SCRIBE** | 可直接引用 `index_structure` 与 `cli_usage_examples` 写操作说明；`known_limits[]` 作 demo 话术标签 |
| **Wave 4C demo** | `--client-ref` / `--schema-headers` 演示「结构化历史 lookup」；`gate_status` + `known_limits` 可接 Scribe 规则摘要 |
| **后续 Wave** | 扩展 `REGISTERED_CASE_DIRS` 或改为 intake 驱动登记，无需改 lookup 过滤逻辑 |

### scope_out（Step 5 · 不做的事）

- 不构建向量库 / RAG。
- 不修改 gate / cleaning / bundle 逻辑。
- 不对用户自然语言 query 做解析（只收结构化 CLI 参数）。

### verification

| 命令 | 结果 |
|------|------|
| `python scripts/build_cases_index.py --json` | `ok=true`, `cases_written=2` |
| `python -m unittest tests.test_lookup_case_history -v` | 5 passed |
| `python scripts/lookup_case_history.py --client-ref SAMPLECO` | 1 match → `cases/sampleco/2026-0001` |

### behavior_notes

- `client_ref` / `product_sku` 过滤：大小写不敏感精确匹配。
- 多 filter 同时提供时为 **AND** 语义。
- `--list-all` 忽略其它 filter。
- `known_limits`：`demo_phase` 硬编码 `legacy_demo_path`；其余从 `eligibility_result.reasons` 合并。

### deferred_items

- 自动发现 `cases/<client>/<case_id>/` 全树（需 Orchestrator 扩 scope）
- 将 `REGISTERED_CASE_DIRS` 改为 config / index meta
- 与 Scribe 规则库 YAML 的双向链接

---

## C_REPORT

<!-- Reviewer 填 -->

---

## D_REPORT

<!-- Scribe 填 -->
