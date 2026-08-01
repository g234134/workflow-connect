# TICKET STATE · W-MVP-W4B-GUARD-SCHEMA · Wave 4B · schema header 轻探针

> handoff 摘要档；跨 chat 交棒以本档为准。

---

## FRAME

- Goal: 在现有 P2 eligibility gate 的 `schema` 维度增加 header/schema 轻探针；CLEAN-BASIC Phase-like 表与多行导出歧义时写入结构化 `notes`/`warnings`，不改清洗算法。
- Scope:
  - 复用 `case_eligibility.py` / `check_case_eligibility.py`；仅增强 `dimensions.schema`
  - 规则：header 名比对；Phase demo 预期列；多行/Sprint 模式检测
  - 测试：`cases/demo_phase` · `cases/sampleco/2026-0001`
- NonScope:
  - 不改 `clean_phase_demo` 去重规则
  - 不实现 output ratio 护栏（W-MVP-W4B-GUARD-RATIO）
  - 不引入 SKU 路由或多清洗器框架
- AllowedPaths:
  - `notebooks/csv_cleaning/case_eligibility.py`
  - `scripts/check_case_eligibility.py`
  - `tests/test_case_eligibility.py`
  - `04_Workflows/tickets/W-MVP-W4B-GUARD-SCHEMA_state.md`
- BlockedPaths:
  - `core/*`、暗部 `core/*`
  - `notebooks/csv_cleaning/clean_phase_demo.py`（清洗逻辑）
  - `AGENTS.md`、`.cursor/rules/*`、`04_Workflows/00_Agent_Work_Progress.md`
- Dependencies:
  - W-MVP-W2-P2（`case_eligibility.py` gate）
  - `cases/demo_phase/**`（预期 schema 锚点）
  - `cases/sampleco/2026-0001/**`（多行导出实验）
- AcceptanceCriteria:
  - demo_phase：`schema.status=accepted`，`notes` 含 `phase_demo`/`phase_like`，无 `multi_row_export`
  - sampleco：`gate_status` 仍 `accepted`，`schema.notes` 含 `multi_row_export` + `schema_ambiguous`
  - CLI `--json` 输出含 `dimensions.schema.notes` / `warnings`
  - unittest 全绿

---

## STATE

- overall_status: in_review
- current_owner: scribe
- next_action: Scribe 依 C_REPORT 归档；Orchestrator 可评估开 W-MVP-W4B-GUARD-RATIO
- last_updated: 2026-06-08 · reviewer
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: pending

---

## B_REPORT

### Step 0 — Module Reuse Check

| 复用对象 | 用途 |
|----------|------|
| `case_eligibility.py` 六维度（scale/provenance/sensitivity/structure/schema/encoding） | 本票**仅**在既有 `schema` 维度追加探针字段，不新造第二套 gate |
| `scripts/check_case_eligibility.py` + JSON 输出形状 | CLI 透传 `dimensions.schema` 新字段 |
| `cases/sampleco/2026-0001` intake + reports | sampleco fixture；对照「原静默 accepted」 |
| `cases/demo_phase` raw `Phase.csv` | CLEAN-BASIC Phase demo 预期 header 锚点 |

### Step 1 — Schema 探针规则（轻量版）

1. **Header 精确匹配 Phase demo 四列**（`Phase` · `名稱` · `之前` · `現在（建議）`）→ `phase_like`；`case_id=demo_phase` 追加 `phase_demo`。
2. **CLEAN-BASIC SKU 且 header 缺关键列**（缺 `Phase` 或 `名稱`）或 header 集合与 Phase demo 不兼容 → `schema` 维度 `review_needed` + `schema_mismatch`。
3. **phase_like + 多行/Sprint 模式**（`row_count ≥ 20` 且（`名稱` 含 Sprint 模式 **或** 行数 > 2×唯一 Phase 数））→ 追加 `multi_row_export` + `schema_ambiguous`；**不**升格整体 `gate_status`（观测信号写入 `notes`/`warnings`）。
4. **非 CLEAN-BASIC SKU** 或非 Phase 表头 → `non_phase_schema`，**不**因 schema 探针单独升格（避免误伤通用 CSV fixture）。

**权衡**：sampleco 类案保持 `eligibility=accepted`（scale/provenance 等仍低风险），歧义仅暴露在 `dimensions.schema.notes`，供 W4B-RATIO / 人工 review 消费；若将 `multi_row_export` 直接升格 `review_needed` 会改变已跑通 E2E 的 sampleco 行为，故本票选择 **warning-only**。

### Step 2–3 — 实现与 CLI 输出

`dimensions.schema` 扩展字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | enum | 沿用 field_count 规则 + CLEAN-BASIC mismatch 时可 `review_needed` |
| `field_count` | int \| null | 列数 |
| `column_names` | string[] \| null | raw CSV header |
| `notes` | string[] | 探针标签（见下表） |
| `warnings` | string[] | 下游 guard / 人工可读 warning token |

**`notes` 可能取值**

| 值 | 含义 |
|----|------|
| `phase_demo` | 已知内部 demo_phase 案 |
| `phase_like` | header 与 Phase demo 一致或超集 |
| `phase_like_partial` | 含 Phase+名稱 但缺可选百分列 |
| `extra_columns` | Phase demo 列 + 额外列 |
| `multi_row_export` | Phase-like header 但观测到多行/Sprint 导出 |
| `schema_ambiguous` | 结构类似 Phase demo 但语义可能不同 |
| `schema_mismatch` | CLEAN-BASIC 下 header 与预期差异过大 |
| `missing_required_columns` | 缺 Phase 或名稱 |
| `non_phase_schema` | 非 Phase demo 表头（非 CLEAN-BASIC 时不升格） |
| `header_unreadable` | 无法读取 header |

### changed_files

- `notebooks/csv_cleaning/case_eligibility.py` — `_probe_schema_dimension`、schema 维度扩展
- `scripts/check_case_eligibility.py` — docstring/help 说明 `dimensions.schema.notes`
- `tests/test_case_eligibility.py` — demo_phase + sampleco schema 断言
- `04_Workflows/tickets/W-MVP-W4B-GUARD-SCHEMA_state.md` — 本档 B_REPORT

### artifacts

- 无（逻辑内嵌 gate JSON）

### verification

```bash
python -m unittest tests.test_case_eligibility -v
# → Ran 10 tests OK

python scripts/check_case_eligibility.py --case-dir cases/demo_phase --json
# → eligibility=review_needed (rows<100) · schema.notes=[phase_like, phase_demo] · warnings=[]

python scripts/check_case_eligibility.py --case-dir cases/sampleco/2026-0001 --json
# → eligibility=accepted · schema.notes=[phase_like, multi_row_export, schema_ambiguous]
# · warnings=[phase_like_headers_but_multi_row_or_sprint_pattern]
```

### behavior_notes

- **demo_phase**：整体仍 `review_needed`（scale 小样本）；`dimensions.schema.status=accepted`，仅标记 `phase_demo` + `phase_like`。
- **sampleco**：整体仍 `accepted`（与实验 B 一致）；新增可见信号 `phase_like` + `multi_row_export` + `schema_ambiguous`，解决「115 行 milestone 导出静默通过」问题。
- 探针只读 raw header + 前 500 行样本，**不**调用 `clean_phase_demo`。
- 后续票接口：
  - **W-MVP-W4B-GUARD-RATIO**：读取同一 `eligibility_result.json` / gate JSON 的 `dimensions.schema.notes`
  - **W-MVP-W4B-GUARD-REVIEW**：复跑 demo_phase + sampleco 对照本 B_REPORT

### deferred_items

- output ratio 护栏（W-MVP-W4B-GUARD-RATIO）
- `cases/index.json` 写入 `schema_notes`（W4A LOOKUP 票）
- CLEAN-BASIC 非 Phase 表头的专用 SKU 路由

---

## C_REPORT

**Reviewer · W-MVP-W4B-GUARD-REVIEW · 2026-06-08**

### Step 0 — GUARD-SCHEMA 关键点（对照 B_REPORT）

- 在既有 `dimensions.schema` 追加只读 header 探针，不调用、不改 `clean_phase_demo`。
- 新增 `notes` / `warnings` 标签：`phase_like`、`phase_demo`、`multi_row_export`、`schema_ambiguous` 等。
- Phase demo 四列精确匹配 → `phase_like`；`case_id=demo_phase` 追加 `phase_demo`。
- 多行/Sprint 模式（≥20 行且 Sprint 或行数 > 2×唯一 Phase）→ 追加 `multi_row_export` + `schema_ambiguous`，**不**升格整体 `gate_status`。
- 期望：demo_phase 保持 `phase_like` + `phase_demo`，无歧义标签；sampleco 保持 `accepted` 但暴露结构化 warning。

### Step 1 — demo_phase 复跑

**命令**：`python scripts/check_case_eligibility.py --case-dir cases/demo_phase --json`

| 项 | 实际值 |
|----|--------|
| gate_status (`eligibility`) | `review_needed`（`rows<100` · scale 小样本，与 B_REPORT 一致） |
| `dimensions.schema.status` | `accepted` |
| `schema.notes` | `["phase_like", "phase_demo"]` |
| `schema.warnings` | `[]` |

**检查点**：✅ 无 `multi_row_export` / `schema_ambiguous`；✅ `phase_demo` + `phase_like` 与 Implementer 一致。

### Step 2 — sampleco/2026-0001 复跑

**命令**：`python scripts/check_case_eligibility.py --case-dir cases/sampleco/2026-0001 --json`

| 项 | 实际值 |
|----|--------|
| gate_status (`eligibility`) | `accepted` |
| `dimensions.schema.status` | `accepted` |
| `schema.notes` | `["phase_like", "multi_row_export", "schema_ambiguous"]` |
| `schema.warnings` | `["phase_like_headers_but_multi_row_or_sprint_pattern"]` |

**检查点**：✅ 明确标出 `multi_row_export` + `schema_ambiguous`；✅ 相对原「115 行 milestone 导出静默 accepted」，现 gate 仍 `accepted` 但 `dimensions.schema` 有结构化 warning，可供 ratio guard / 人工 review 消费。

### Step 3 — unittest 交叉验证

**命令**：`python -m unittest tests.test_case_eligibility -v`

- **结果**：10/10 pass（`OK`）。
- **schema 相关用例**：`test_demo_phase_review_small_row_count`（phase_demo/phase_like，排除 multi_row_export/schema_ambiguous）；`test_sampleco_schema_multi_row_export_warning`（multi_row_export + schema_ambiguous + warnings 非空）。

### Step 4 — 判定

| 字段 | 值 |
|------|-----|
| **verdict** | **accepted** |
| **demo_phase_summary** | schema 探针稳定：`accepted` + `phase_like`/`phase_demo`，无歧义标签；整体 `review_needed` 仍仅由 scale 驱动。 |
| **sampleco_summary** | 成功暴露 Phase-like 多行导出风险：`accepted` 不变，`schema.notes`/`warnings` 含 `multi_row_export` + `schema_ambiguous`，解决静默通过问题。 |

**recommendations（下一票 GUARD-RATIO）**

- 读取同一 gate JSON / `eligibility_result.json` 的 `dimensions.schema.notes` 与 `warnings`；当含 `multi_row_export` 或 `schema_ambiguous` 时，与 cleaned/raw 行数比或 Sprint 密度做 ratio 护栏。
- 建议 ratio 规则**同样 warning-only 或 review_needed 分维**，避免与 sampleco 已跑通 E2E 的 `eligibility=accepted` 基线冲突；升格策略由 GUARD-RATIO 票单独定义。
- 人工 signoff 模板可引用 `schema.warnings[0]` 作为「结构歧义已探测」勾选依据。

### Step 5 — scope out

- 本 Review 票**未修改任何代码**，仅复跑 CLI + unittest 并对照 B_REPORT / AcceptanceCriteria。
- **不**扩 scope 至 output ratio、signoff 自动化或 `cases/index.json` schema 字段（留给 W-MVP-W4B-GUARD-RATIO / W4A LOOKUP）。

**→ Orchestrator / Implementer**：GUARD-SCHEMA 验收通过，可继续开 **W-MVP-W4B-GUARD-RATIO**；Implementer 无需返工。

---

## D_REPORT

<!-- Scribe 填 -->
