# TICKET STATE · W-MVP-W4B-GUARD-RATIO · Wave 4B · output row-ratio 护栏

> handoff 摘要档；跨 chat 交棒以本档为准。

---

## FRAME

- Goal: 在现有 P1–P4 链路上增加 `output_rows / input_rows` 比例护栏 sidecar 观测；比例过低时写入结构化 `output_guard` warning，为 sampleco 类「115→8 行但流程绿」打黄灯；不改清洗算法与主链 exit code。
- Scope:
  - 新增 `output_guard.py`；集成 `case_delivery_bundle.py` · `run_case_e2e_validation.py`
  - 消费 `report.json` `row_counts` 与 gate `dimensions.schema.notes`
  - 测试：`cases/demo_phase` · `cases/sampleco/2026-0001`
- NonScope:
  - 不改 `clean_phase_demo` 去重规则
  - 不改变 gate / bundle / E2E 的 `ok` / `qa_status` exit 语义
  - 不自动 fail E2E（warning + 人工判断）
  - 不按 SKU 或列语义动态调阈值
- AllowedPaths:
  - `notebooks/csv_cleaning/output_guard.py`
  - `notebooks/csv_cleaning/case_delivery_bundle.py`
  - `scripts/build_case_delivery_bundle.py`
  - `scripts/run_case_e2e_validation.py`
  - `tests/test_output_guard.py`
  - `04_Workflows/tickets/W-MVP-W4B-GUARD-RATIO_state.md`
- BlockedPaths:
  - `notebooks/csv_cleaning/clean_phase_demo.py`
  - `core/*`、暗部 `core/*`
  - `AGENTS.md`、`.cursor/rules/*`、`04_Workflows/00_Agent_Work_Progress.md`
- Dependencies:
  - W-MVP-W4B-GUARD-SCHEMA（`dimensions.schema.notes`）
  - W-MVP-W2-P4（`case_delivery_bundle`）
  - W-MVP-W3（`run_case_e2e_validation`）
- AcceptanceCriteria:
  - demo_phase：`output_guard.status=ok`，ratio ≥ 0.5
  - sampleco：`output_guard.status=warning`，ratio ≈ 0.07，含 `schema_flags`
  - `report.json` 与 bundle / E2E `--json` 均含 `output_guard`
  - unittest 全绿；主链 exit code 不变

---

## STATE

- overall_status: in_review
- current_owner: reviewer
- next_action: Scribe 归档 C_REPORT；Orchestrator 裁定 Wave 4B guard 子链 ready
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
| `report.json` → `stats.row_counts` / `cleaning_stats.row_counts`（`intake` · `ok`） | ratio 分子分母 |
| `report.json` → `summary.qa_status` · `issues_summary` | **只读**；本票不修改 |
| `case_delivery_bundle.build_case_delivery_bundle` | bundle 阶段写入 `output_guard` 到 `report.json` 并回传 |
| `run_case_e2e_validation.run_case_e2e_validation` | E2E 汇总附带 `output_guard`（来自 bundle 或 report） |
| `check_case_eligibility` → `dimensions.schema.notes` | 可选 `schema_flags` 透传 |
| `cases/demo_phase/reports/report.json` | 阈值校准：7→5，ratio≈0.714 |
| `cases/sampleco/2026-0001/reports/report.json` | 阈值校准：115→8，ratio≈0.0696 |

**重申**：本票只加护栏观测与 warning，不改 `clean_phase_demo` 算法、不改主脚本 exit 语义。

### Step 1 — ratio_guard 契约

**计算公式**

```
ratio = output_rows / input_rows
output_rows = row_counts.ok  (fallback: row_counts.accepted)
input_rows  = row_counts.intake
```

字段读取顺序：`cleaning_stats.row_counts` → `stats.row_counts`。

**默认阈值（MVP）**

| 条件 | `output_guard.status` |
|------|----------------------|
| `ratio >= 0.5` | `ok` |
| `ratio < 0.5` | `warning` |
| 缺 row_counts 或 `input_rows <= 0` | `unknown` |

阈值 0.5 理由：demo_phase（5/7≈0.71）应绿；sampleco（8/115≈0.07）必黄。可在后续 Wave 按 SKU／业务调参；本票固定常量 `DEFAULT_RATIO_THRESHOLD = 0.5`。

**输出位置**

1. `cases/<case>/reports/report.json` 顶层字段 `output_guard`
2. `build_case_delivery_bundle` 返回 dict 的 `output_guard`
3. `run_case_e2e_validation` 返回 dict 的 `output_guard`

**JSON 结构示例**

demo_phase（ok）：

```json
"output_guard": {
  "guard_version": "output-guard-v0.1",
  "ratio": 0.7143,
  "input_rows": 7,
  "output_rows": 5,
  "threshold": 0.5,
  "status": "ok",
  "notes": []
}
```

sampleco（warning + schema_flags）：

```json
"output_guard": {
  "guard_version": "output-guard-v0.1",
  "ratio": 0.0696,
  "input_rows": 115,
  "output_rows": 8,
  "threshold": 0.5,
  "status": "warning",
  "notes": [
    "output_rows (8) / input_rows (115) = 0.0696 below MVP threshold 0.5; manual review recommended",
    "schema probe flagged ambiguous export pattern; see schema_flags"
  ],
  "schema_flags": ["multi_row_export", "schema_ambiguous"]
}
```

### Step 2 — 实作集成点

选择 **A) `case_delivery_bundle.py`** 为主集成点：

- `enrich_report_json_v1` 之后调用 `apply_output_guard_to_report`
- 读取 `check_case_eligibility(case_dir)` 获取 `dimensions.schema.notes`
- 写回 `reports/report.json`（`enrich_report=True` 时）
- bundle 返回 dict 附加 `output_guard`

**B) `run_case_e2e_validation.py`** 透传：

- bundle `--json` 结果中的 `output_guard` 复制到 E2E 汇总
- fallback：直接读 `report.json` 的 `output_guard`

**不变项**：`ok` / `qa_status` / gate `eligibility` / bundle exit code / E2E exit code 逻辑均未改动。

### Step 3 — schema.notes 集成

当 `dimensions.schema.notes` 含 `multi_row_export` 或 `schema_ambiguous`：

- `output_guard.schema_flags` 列出匹配标签
- `output_guard.notes` 追加人工可读说明（不升格 `review_needed`）

### Step 4 — 测试与 CLI 验证

**unittest**

```bash
python -m unittest tests.test_output_guard tests.test_case_delivery_bundle -v
```

覆盖：compute（demo ok / sampleco warning）、bundle 集成、schema_flags、CLI `--json`。

**CLI 验证（sampleco）**

```bash
python scripts/build_case_delivery_bundle.py --case-dir cases/sampleco/2026-0001 --json
# → output_guard.status=warning · ratio≈0.0696 · schema_flags=[multi_row_export, schema_ambiguous]

python scripts/run_case_e2e_validation.py --case-dir cases/sampleco/2026-0001 --json
# → ok=true（主链仍绿）· output_guard.status=warning
```

### ratio_guard_contract / thresholds / interactions / limitations

| 项 | 内容 |
|----|------|
| **ratio_guard_contract** | 见 Step 1 JSON 示例；键名固定 `output_guard` |
| **thresholds** | `0.5` MVP 默认；`guard_version=output-guard-v0.1` |
| **interactions_with_schema_guard** | 消费 GUARD-SCHEMA 的 `multi_row_export` / `schema_ambiguous` → `schema_flags`；仅附加 notes，不升格 gate |
| **limitations** | 不区分 SKU；不按列语义调阈值；`unknown` 时不阻断；不自动 fail E2E |

### changed_files

- `notebooks/csv_cleaning/output_guard.py` — 新建 ratio guard 逻辑
- `notebooks/csv_cleaning/case_delivery_bundle.py` — bundle 集成写回 report
- `scripts/run_case_e2e_validation.py` — E2E 汇总透传 `output_guard`
- `tests/test_output_guard.py` — 新建测试
- `04_Workflows/tickets/W-MVP-W4B-GUARD-RATIO_state.md` — 本档

### verification

```bash
python -m unittest tests.test_output_guard tests.test_case_delivery_bundle -v
# → 10 tests OK

python scripts/build_case_delivery_bundle.py --case-dir cases/demo_phase --json
# → output_guard.status=ok · ratio=0.7143

python scripts/build_case_delivery_bundle.py --case-dir cases/sampleco/2026-0001 --json
# → output_guard.status=warning · ratio=0.0696 · schema_flags present

python scripts/run_case_e2e_validation.py --case-dir cases/sampleco/2026-0001 --json
# → ok=true · output_guard.status=warning
```

### scope out

- 不更改 `clean_phase_demo` 去重规则
- 不改变主脚本 exit code 语义（仍由 `ok` / `qa_status` 控制）
- 不自动 fail E2E；默认 warning + 人工判断
- 不实现 SKU 路由或动态阈值表

### Reviewer — Step 0 设计对齐摘要

- `ratio = row_counts.ok / row_counts.intake`；默认阈值 `< 0.5` → `status="warning"`，否则 `"ok"`。
- sidecar 挂在 bundle（`case_delivery_bundle`）与 E2E JSON 上，不改主链 `ok` / exit code。
- sampleco：ratio ≈ 0.0696（8/115）→ `warning` + `schema_flags=["multi_row_export","schema_ambiguous"]`。
- demo_phase：ratio ≈ 0.7143（5/7）→ `ok`，无 `schema_flags`。

### Reviewer — Step 1 unittest

```bash
python -m unittest tests.test_output_guard tests.test_case_delivery_bundle -v
```

- **结果**：10 tests，**全部 pass**（exit 0）。
- **ratio / schema_flags 相关用例**（节选）：`test_demo_phase_ratio_ok`、`test_sampleco_ratio_warning`、`test_apply_output_guard_schema_flags`、`test_bundle_attaches_output_guard_sampleco`。

### Reviewer — Step 2 demo_phase E2E

```bash
python scripts/run_case_e2e_validation.py --case-dir cases/demo_phase --json
```

| 字段 | 值 |
|------|-----|
| `overall_ok` | `true` |
| `output_guard.ratio` | `0.7143` |
| `output_guard.status` | `"ok"` |
| `output_guard.schema_flags` | 不存在（符合预期） |

**检查点**：主链仍绿；ratio > 0.5；未误带 `multi_row_export` / `schema_ambiguous`。

### Reviewer — Step 3 sampleco E2E

```bash
python scripts/run_case_e2e_validation.py --case-dir cases/sampleco/2026-0001 --json
```

| 字段 | 值 |
|------|-----|
| `overall_ok` | `true` |
| `output_guard.ratio` | `0.0696` |
| `output_guard.status` | `"warning"` |
| `output_guard.schema_flags` | `["multi_row_export", "schema_ambiguous"]` |

**检查点**：主链 `ok=true`（exit 0）；`warning` 亮黄灯；ratio ≈ 8/115；`schema_flags` 含两项标签。

---

## C_REPORT

**verdict**: `accepted`

**demo_phase_summary**: demo_phase E2E 主链 `overall_ok=true`，`output_guard.status=ok`、ratio=0.7143，无 schema_flags——护栏仅观测、不误伤绿色案例。

**sampleco_summary**: sampleco 主链仍 `overall_ok=true`，但 `output_guard.status=warning`、ratio≈0.07，并透传 `multi_row_export` + `schema_ambiguous`，符合「低 ratio + schema 歧义 → 需人工审视」设计。

**recommendations**:

- 行为与 B_REPORT 契约、AcceptanceCriteria 一致；unittest + 双案 E2E 复跑全绿。
- 可选后续：`docs/MVP_CASE_E2E_DoD_v0.1.md` §4 可补一行「`output_guard` 为 warning-only 侧车，不升格 E2E fail」；`docs/MVP_DEMO_WALKTHROUGH_v0.1.md` 已较完整，demo 引用可优先 walkthrough。
- 阈值 0.5 本票固定常量，不在本票调整。

**scope out（Reviewer）**:

- 本票未改代码，仅验证与建议。
- 不改变 ratio 阈值（只建议，不强改）。
- 不扩 scope 至 signoff 自动写入（交给未来票或 Wave）。

**orchestrator_note**: GUARD-RATIO 与 GUARD-SCHEMA 组合后，Wave 4B guard 子链（schema 探针 + output ratio sidecar）可视为 **ready for demo 文档引用**；E2E 主链语义未变，sampleco 类案例由结构化 `output_guard` 承担黄灯职责。

---

## D_REPORT

<!-- Scribe 填 -->
