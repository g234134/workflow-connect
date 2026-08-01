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

- overall_status: accepted_with_gaps
- overall_status_rationale: FRAME AC 全满足（index enriched 字段 · sampleco known_limits · lookup `--verbose` · unittest 10/10）；deferred（glob 自动登记 · `schema_fingerprint` · temp-dir index refresh UT）与 FRAME NonScope / B_REPORT deferred_items 一致，**不阻塞** v0.1 关票。
- current_owner: orchestrator
- next_action: closed · W4-MEM-01 accepted_with_gaps；可选 follow-up **W4-MEM-02**（glob 自动登记 + temp-dir index refresh UT + schema_fingerprint）
- last_updated: 2026-06-14 · orchestrator + scribe
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

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

- conclusion: accepted_with_gaps
- blocking_issues: 无（FRAME AC 全满足；无 AllowedPaths 越界；无须返工 code）
- checks_summary: |
  - AC-1（index enriched 字段）：PASS — `cases/index.json` 含 `cleaning_profile` / `cleaning_rules_applied` / `delivery_template_ref` / `schema_notes` / `qa_status` / `accepted_ratio`。
  - AC-2（sampleco known_limits）：PASS — `multi_row_export`（schema_notes 等價） + `low_accepted_ratio`；`accepted_ratio=0.0696` < 0.1。
  - AC-3（lookup --verbose）：PASS — `test_verbose_includes_rules_and_template`；Reviewer 复跑 `python scripts/lookup_case_history.py --client-ref sampleco --verbose` 含 rules + template + qa 字段。
  - AC-4（unittest 全绿）：PASS — `python -m unittest tests.test_lookup_case_history tests.test_build_cases_index -v` → **10/10 OK**（2026-06-14）。
  - Boundary：PASS — 变更限于 AllowedPaths；未觸 `core/*` · `clean_phase_demo.py` · 制度檔。
  - Spec 對齊：PASS — `docs/case-history-lookup-spec-v0.1.md` 與 CLI/字段表一致；deferred（glob 自動登記、schema_fingerprint）與 FRAME NonScope 一致。
- risk_level: low
- suggestions: |
  1. Orchestrator 更新 STATE：`reviewer: done` · `overall_status` → done 或 accepted_with_gaps。
  2. Scribe 在 Progress / Dashboard 補上 W4-MEM-01 Reviewer 關票條目。
  3. 可選 follow-up 票：W4-MEM-02（glob 自動登記 + temp-dir index refresh UT + schema_fingerprint）。
- reviewed_by: reviewer
- reviewed_at: 2026-06-14

---

## D_REPORT

- docs_updates:
  - `docs/WAVE_PROGRESS_DASHBOARD.md` — Lane A 分票收口表 · 最小接案 MVP Wave 4 分栏 W4-MEM-01 → **accepted_with_gaps**；下一步索引移除 Reviewer 關票项
  - `04_Workflows/00_Agent_Work_Progress.md` — 2026-06-14 W4-MEM-01 Reviewer 关票条目（append）
- progress_entry: W4-MEM-01 关票：只读 case 记忆索引 enriched 字段与 lookup `--verbose` 已验证（10/10 UT）；glob 自动登记 · schema_fingerprint deferred → W4-MEM-02。
- followup_suggestions:
  - **W4-MEM-02**：glob 自动登记 `cases/<client>/<id>/` · temp-dir index refresh UT · `schema_fingerprint` 字段
  - Progress Wave 4 partial → done 收口（可与 W4-MEM-02 Scribe 合并）
