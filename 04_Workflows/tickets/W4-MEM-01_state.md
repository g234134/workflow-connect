# TICKET STATE · W4-MEM-01 · Wave 4 Lane A · 轻量 case 记忆索引补齐

> handoff 摘要档；承接 `W-MVP-W4A-MEMO-LOOKUP` FRAME 未填字段。  
> **SSOT 计划**：`docs/wave4-lane-a-execution-plan-v0.1.md` · **spec**：`docs/case-history-lookup-spec-v0.1.md`

---

## FRAME

- Goal: 补齐只读 case 记忆索引，可查历史 case、清洗 profile、已用规则、交付模板与 enriched `known_limits`。
- Scope:
  - 扩展 `scripts/cases_index_lib.py` 索引字段
  - `scripts/build_cases_index.py` · `scripts/lookup_case_history.py`（`--verbose`）
  - `cases/index.json` refresh
  - `docs/case-history-lookup-spec-v0.1.md`
  - `tests/test_lookup_case_history.py` · `tests/test_build_cases_index.py`
- NonScope:
  - 无向量 RAG / agent memory
  - 不改 gate / cleaning / bundle / E2E exit 语义
  - 不自动发现全 `cases/` 树
- AllowedPaths:
  - `scripts/cases_index_lib.py` · `scripts/build_cases_index.py` · `scripts/lookup_case_history.py`
  - `cases/index.json`
  - `docs/case-history-lookup-spec-v0.1.md` · `docs/wave4-lane-a-execution-plan-v0.1.md`
  - `tests/test_lookup_case_history.py` · `tests/test_build_cases_index.py`
  - `04_Workflows/tickets/W4-MEM-01_state.md`
- BlockedPaths:
  - `core/*` · `notebooks/csv_cleaning/clean_phase_demo.py`
  - `AGENTS.md` · `.cursor/rules/*`
- Dependencies:
  - `W-MVP-W4A-MEMO-ORCH` · `W-MVP-W4A-MEMO-LOOKUP`（骨架）
  - `cases/demo_phase/**` · `cases/sampleco/2026-0001/**`
- AcceptanceCriteria:
  - index 含 `cleaning_profile` / `cleaning_rules_applied` / `delivery_template_ref` / `schema_notes` / `qa_status` / `accepted_ratio`
  - sampleco `known_limits` 含 `multi_row_export`（或 schema note 等价）与 `low_accepted_ratio`
  - lookup `--verbose` 返回规则与模板字段
  - unittest 全绿

---

## STATE

- overall_status: in_progress
- current_owner: implementer
- next_action: Reviewer 对照 AC；Scribe 可选引用 spec 更新 walkthrough
- last_updated: 2026-06-13 · implementer
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

### changed_files

- `scripts/cases_index_lib.py` — enriched index build + lookup `--verbose`
- `scripts/lookup_case_history.py` — `--verbose` flag
- `cases/index.json` — refreshed entries
- `docs/case-history-lookup-spec-v0.1.md` — 新建
- `docs/wave4-lane-a-execution-plan-v0.1.md` — 新建
- `tests/test_lookup_case_history.py` — 扩展断言
- `tests/test_build_cases_index.py` — 新建
- `04_Workflows/tickets/W4-MEM-01_state.md` — 本档

### verification

```bash
python scripts/build_cases_index.py --json
python scripts/lookup_case_history.py --client-ref sampleco --verbose
python -m unittest tests.test_lookup_case_history tests.test_build_cases_index -v
```

### deferred_items

- 自动 glob 登记 `cases/<client>/<id>/`（见 execution plan T4）
- `schema_fingerprint` 字段（ORCH FRAME 可选）
- Progress 末尾 Wave 4 partial → done（Scribe / W4-MEM-02）

---

## C_REPORT

<!-- Reviewer pending · 2026-06-14 多 lane 收口：implementer done + unittest 10/10 OK（2026-06-14 smoke）；待对照 FRAME AC 关票。不得自行升格 overall_status → done。 -->

---

## D_REPORT

<!-- Scribe 填 -->
