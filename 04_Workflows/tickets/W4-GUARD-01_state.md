# TICKET STATE · W4-GUARD-01 · Wave 4 Lane A · 真样本护栏升格草案

> **状态**：design draft · **不施工 gate 升格**（待尚書省 / Orchestrator 裁定阈值）  
> **前置**：`W-MVP-W4B-GUARD-SCHEMA`（accepted）· `W-MVP-W4B-GUARD-RATIO`（accepted · warning-only）  
> **计划 SSOT**：`docs/wave4-lane-a-execution-plan-v0.1.md` §票 2 · §设计分歧 TODO

---

## FRAME

- Goal: 定义 schema mismatch、低 `accepted_ratio`、`pass_with_warnings` 不可信三类情形何时升格 `review_needed` 或 delivery `blocked`，并指定接入点。
- Scope:
  - 本票 **doc + ticket state + contract 草案**
  - sampleco / demo_phase 对照表
  - 建议接入：`case_eligibility.py` · `output_guard.py` · 可选 `qa_delivery_guard.py` sidecar
  - skeleton test 或 spec unittest（不强制改 gate 行为）
- NonScope:
  - 不改 `clean_phase_demo` 算法
  - 不默认 fail E2E（须 `--strict-guards` opt-in 才改 exit，TODO）
  - 不 prod 远程服务
  - **不**在本票硬编码最终阈值（见 TODO T1–T3）
- AllowedPaths:
  - `docs/wave4-lane-a-execution-plan-v0.1.md`
  - `04_Workflows/tickets/W4-GUARD-01_state.md`
  - `tests/test_qa_delivery_guard_draft_v1.py`（skeleton · 可选）
- BlockedPaths:
  - `notebooks/csv_cleaning/clean_phase_demo.py`
  - `core/*`
- Dependencies:
  - W4-MEM-01（index 可见 `known_limits`）
  - W-MVP-W4B-GUARD-SCHEMA · W-MVP-W4B-GUARD-RATIO
- AcceptanceCriteria:
  - AC1 三条触发条件文档化
  - AC2 接入点矩阵（gate vs bundle vs new sidecar）
  - AC3 sampleco 现行 vs 提案对照
  - AC4 TODO T1–T3 显式列出，无静默升格

---

## STATE

- overall_status: draft
- current_owner: orchestrator
- next_action: 尚書省裁定 T1–T3 后开 **W4-GUARD-01-IMPL** Implementer 票
- last_updated: 2026-06-13 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: n/a
  - reviewer: n/a
  - scribe: pending

---

## B_REPORT（设计草案）

### 三条触发（提案 · 未实施）

| ID | 条件 | 现行 | 提案（待批） |
|----|------|------|--------------|
| G1 | CLEAN-BASIC header 缺 Phase/名稱 | gate `schema` → `review_needed` | 维持 |
| G2 | `phase_like` + `multi_row_export` + `schema_ambiguous` | notes only · gate `accepted` | **选项 B**：gate `review_needed` 或 bundle 前置 block（T1） |
| G3 | `accepted_ratio < 0.5` | `output_guard.status=warning` | sidecar 维持；**若** G2 成立且 ratio `< 0.1` → delivery `blocked`（T2） |
| G4 | `qa_status=pass_with_warnings` + G3 | E2E 仍 `ok=true` | CP-B / signoff 须人工勾选；可选 `--strict-guards` fail E2E（T3） |

### sampleco/2026-0001 对照

| 信号 | 现行值 |
|------|--------|
| gate | `accepted` |
| schema.notes | `multi_row_export`, `schema_ambiguous` |
| accepted_ratio | ≈ 0.0696 (8/115) |
| output_guard | `warning` |
| qa_status | `pass_with_warnings` |
| E2E overall_ok | `true` |

**提案意图**：对外 demo 时须同时展示 lookup `known_limits` + output_guard warning；升格 gate 行为需单独 IMPL 票。

### 建议接入点

1. **P2 gate** — G1 已部分存在；G2 升格须改 `case_eligibility.py` 整体 eligibility 合成逻辑。  
2. **P4 bundle** — `output_guard` 已挂载；可增 `qa_delivery_guard.recommendation=block_delivery`（只写 JSON，不改 exit）。  
3. **E2E** — 透传 guards；`--strict-guards` 时 `warning` → exit 1（TODO）。

### deferred_items（→ W4-GUARD-01-IMPL）

- 实现 G2/G3/G4 升格与 opt-in CLI
- 阈值常量 / SKU 表外置 config
- DoD §4 增补 strict mode 说明
- CI 接入（非 MVP）

---

## C_REPORT

<!-- Reviewer 填 -->

---

## D_REPORT

<!-- Scribe 填 -->
