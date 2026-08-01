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

- overall_status: accepted_with_gaps
- current_owner: closed（T1）· G2–G4 opt-in 見 FP-G1-T3
- next_action: T1 已收口 · suite 對齊 DONE · **G2–G4 opt-in landed**（`FP-G1-T3` · 預設 off · 尚書省「全開」）· tip#1 仍 `P6-nightly-continue` · ≠ required CI
- last_updated: 2026-07-28T23:55+08:00 · Implementer 全開 G2–G4
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done（追蹤票 `W4-GUARD-01-T1-reviewer-close` · `accepted_with_gaps`）；G2–G4 Reviewer pending 另排
  - scribe: done

**追蹤票（2026-07-28）**：`04_Workflows/tickets/W4-GUARD-01-T1-reviewer-close_state.md` · **done_with_gaps** · T1 only。

**suite 對齊追蹤（2026-07-28 · post T1）**：`W4-REG-sandbox-client-runpath-suite-align-v1` · **DONE**。

**G2–G4（2026-07-28 · 全開）**：`FP-G1-T3-guard-schema-ratio-escalation-frame-v1` · **DONE** · opt-in · 見 `docs/w4-guard-g2-g4-escalation-frame-v1.md`。

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-06-13 | orchestrator | 起票 FRAME / B_REPORT 設計草案 |
| 2026-06-15 | implementer | 實作 W4-GUARD-01 IMPL 路徑（見下方 B_REPORT），不擴大 scope 前提下完成最小 guard |
| 2026-06-15 | implementer | Guard 切入點：`scripts/run_agent_standard_case_regression.py`；新增 `enforce_fixture_guard()` 函數、常數定義、CLI help 更新 |
| 2026-06-15 | implementer | README 更新：`docs/agent-and-non-tabular-lines-readme-v2.md` §2.3 新增 guard 行為說明 |
| 2026-06-15 | implementer | Unit tests 新增 6 個 guard 驗證（總 17 tests 全綠）|
| 2026-06-15 | implementer | CLI 驗證：預設 2 fixtures / 加 flag 4 fixtures，行為符合預期 |
| 2026-06-15 | implementer | B_REPORT / O_NOTES 填寫完成；票狀態更新為 implementer_done_pending_closure |

**結論摘要**：
- ✅ 採 **IMPL 路徑**（非 waiver）
- ✅ Guard 機制：experimental fixtures（`additional_demo`, `sandbox_client`）需顯式 `--include-extended-fixtures` flag
- ✅ Stable fixtures（`demo_phase`, `sampleco`）不受影響，正常執行
- ✅ 錯誤訊息清晰：`experimental_fixture_requires_explicit_flag` + 提示 `--include-extended-fixtures`
- ✅ 文件、測試、CLI 驗證同步更新
- ✅ Reviewer `accepted_with_gaps`（2026-07-28 · 追蹤票 T1 收口）· G2–G4 仍 deferred

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

**verdict**: `accepted_with_gaps`（T1 fixture guard）  
**ts**: 2026-07-28T20:20+08:00  
**追蹤票**: `W4-GUARD-01-T1-reviewer-close`（`done_with_gaps`）

### T1 裁決

- Stable（`demo_phase`／`sampleco`）無需 flag → **PASS**
- Experimental（`additional_demo`／`sandbox_client`）需 `--include-extended-fixtures` → **PASS**（六條 guard UT 全綠）
- G2–G4 schema／ratio／strict-guards → **仍 deferred**／`blocked_on_approval`（非本輪 blocking）

### 證據

`python -m unittest tests.test_agent_standard_case_regression -v` → 17 ran · **16 OK** · 1 FAIL（`test_run_all_allowed_extended_fixtures_experimental_run`：`sandbox_client` `final_status=blocked`／`needs_review`，期望 `stopped_at_cleaning_preview`；`guard_sanity_ok=true` → **out of T1**）。

P6 再核：`gh run list --workflow=p6-int-gate-nightly.yml --limit 3` → latest 仍 `30346954725` · 無新 success · **未**改 Phase%。

### non_claims

≠ G2–G4 升格 · ≠ Phase% apply · ≠ Round-2 GO／UNLOCK／execute · ≠ DarkOps／L1／K-2

---

## B_REPORT · IMPL 路徑實作（W4-GUARD-01 Implementer 交付）

### Guard 實作摘要

**選定切入點**：`scripts/run_agent_standard_case_regression.py`（最靠近入口層，被 CI suite 調用）

**核心 Guard 邏輯**：
- `enforce_fixture_guard(case_ref, maturity, *, include_extended_fixtures, explicit_flags)` 函數
- **Stable fixtures**（`demo_phase`, `sampleco/2026-0001`）：無需 flag，正常執行
- **Experimental fixtures**（`additional_demo`, `sandbox_client`）：
  - 未設 `--include-extended-fixtures` → 被 regression case_specs 排除（不進入運行列表）
  - 設 `--include-extended-fixtures` → guard 允許通過
  - 嘗試以錯誤 maturity 運行 → guard 返回 `block` + 清晰錯誤訊息

### 變更檔案

| 檔案 | 變更類型 | 說明 |
|------|----------|------|
| `scripts/run_agent_standard_case_regression.py` | 修改 | 新增 `enforce_fixture_guard()`、`EXPERIMENTAL_CASE_REFS`、`EXPERIMENTAL_MATURITY_LABELS`；更新 `--include-extended-fixtures` help 文檔 |
| `docs/agent-and-non-tabular-lines-readme-v2.md` | 修改 | 新增 §2.3 「W4-GUARD-01: Experimental Fixture Guard」段落，說明 guard 行為與使用方式 |
| `tests/test_agent_standard_case_regression.py` | 修改 | 新增 6 個 guard 驗證測試 |

### 驗證證據

**1. Unit Test（17 tests 全綠）**：
```bash
python -m unittest tests.test_agent_standard_case_regression -v
# 包含：
# - test_enforce_fixture_guard_blocks_experimental_without_flag
# - test_enforce_fixture_guard_allows_stable_fixture
# - test_enforce_fixture_guard_allows_experimental_with_flag
# - test_enforce_fixture_guard_blocks_by_maturity_label
# - test_default_regression_excludes_extended_fixtures_silently
# - test_guard_blocks_when_include_extended_fixtures_true_but_fixture_marked_experimental
```

**2. CLI 驗證**：
```bash
# 預設行為：只跑 stable fixtures（2 個）
$ python scripts/run_agent_standard_case_regression.py --run-mode preview
> passed: 2/2
> cases: demo_phase, sampleco/2026-0001

# 顯式啟用 experimental fixtures（4 個）
$ python scripts/run_agent_standard_case_regression.py --run-mode preview --include-extended-fixtures
> passed: 4/4
> cases: demo_phase, sampleco/2026-0001, additional_demo [controlled_experimental], sandbox_client [controlled_experimental]
```

### Guard 決策邏輯

```python
def enforce_fixture_guard(case_ref, maturity, *, include_extended_fixtures, explicit_flags):
    if case_ref in EXPERIMENTAL_CASE_REFS or maturity in EXPERIMENTAL_MATURITY_LABELS:
        if include_extended_fixtures:
            return {"ok": True, "action": "allow", "reason": "explicit_include_extended_fixtures"}
        return {
            "ok": False, "action": "block",
            "reason": "experimental_fixture_requires_explicit_flag",
            "required_flags": ["--include-extended-fixtures"],
            "message": "Guard blocked: case_ref='...' requires explicit opt-in. Use --include-extended-fixtures to enable."
        }
    return {"ok": True, "action": "allow", "reason": "stable_fixture"}
```

### 被 Guard 的場景與例外

| 場景 | Guard 行為 | 錯誤訊息 |
|------|------------|----------|
| Stable fixture 無 flag | ✅ 允許 | — |
| Experimental fixture 無 flag | ✅ 排除於運行列表（regression 層） | N/A（不進入） |
| Experimental fixture 有 flag | ✅ 允許 | — |
| 嘗試以錯誤 maturity 直接調用 | ❌ Block | `experimental_fixture_requires_explicit_flag` |

### 仍未覆蓋的範圍（如適用）

- `scripts/run_mvp_mainline_regression.py`：未加 guard（MVP 主鏈只跑 demo_phase，無 extended fixtures）
- `scripts/run_agent_standard_case_experiment.py`：sandbox e2e 已有獨立 `--sandbox-end-to-end` flag
- Local UI / Notebook：未於本次實作範圍（CLI guard 為主要防線）
- Non-Tabular fixtures：shadow flow，不在 tabular regression 範圍

### 設計理由說明

1. **為什麼選 regression.py 而非 experiment.py**：regression 是 CI 和新人最常使用的入口，在此設防可最大化覆蓋
2. **為什麼用排除而非 error**：避免破壞現有 stable fixture 使用流程，experimental fixtures 需要主動 opt-in
3. **maturity 標籤雙檢查**：同時檢查 `case_ref` 與 `maturity` 標籤，防禦未來新增 fixtures

---

## C_REPORT（重複錨 · 見上方正式 C_REPORT）

正式裁決見本檔第一個 `## C_REPORT` 與追蹤票 `W4-GUARD-01-T1-reviewer-close_state.md`。

---

## D_REPORT

- **docs_updates**:
  - `docs/WAVE_PROGRESS_DASHBOARD.md` — Lane A W4-GUARD-01 → **accepted_with_gaps（T1）**（僅狀態句 · 未改 Phase% Gauge）
  - `docs/agent-and-non-tabular-lines-readme-v2.md` §2.3（implementer 已交付）
- **progress_entry**: W4-GUARD-01 T1 Reviewer **accepted_with_gaps** · G2–G4 仍 deferred · tip#1 未改。

- 2026-07-28T21:15+08:00 · Implementer · suite 對齊 **DONE** · 17/17 UT · QUEUE DONE · tip#1 未改 · ≠ G2–G4／Phase%
