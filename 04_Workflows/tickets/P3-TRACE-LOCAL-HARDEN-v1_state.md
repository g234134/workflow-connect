# TICKET STATE · P3-TRACE-LOCAL-HARDEN-v1 · 本地 trace CLI／jsonl 契約 hardening

> Wave A／near-100 下一薄刀 · 2026-07-15 · Multi-Chat O→B same_chat  
> 對齊：`plans/multi-phase-near-100-p1-p6-execution-plan.md` §P3 #1 · `docs/observability.md` · WAVE-B-P1-TRACE-QUERY-CLI

---

## FRAME
<!-- Orchestrator 填：2026-07-15 凍結 -->

- Goal: 交付一入口本地 harden CLI：對 fixture JSONL 做 gov-trace-v2 契約校驗 + `trace_query` smoke，回傳結構化 `ok` dict（≠ prod Langfuse／PG 升格）。
- Scope:
  - MUST：`scripts/run_p3_trace_local_harden_v1.py`（校驗 + query smoke + `non_claims`）
  - MUST：`tests/test_p3_trace_local_harden_v1.py`
  - MUST：`docs/p3-trace-local-harden-v1.md`
  - MAY：`docs/observability.md` §7 加一行本票入口 cross-ref（不改契約正文）
  - MAY：複用既有 `observability.trace_schema.validate_trace_event`／`trace_query.query_traces`（唯讀呼叫，不重寫 core）
- NonScope:
  - ≠ 真接 Langfuse／改暗部 observability
  - ≠ Langfuse↔PG 對齊實作（仍見 `FP-G3-T3` deferred）
  - ≠ 改 `.github/workflows/**`／mandatory CI
  - ≠ Dashboard Phase% apply／假寫趴數
  - ≠ H2–H5／P9 prod／DarkOps 解禁
  - ≠ 改寫 `runtime/task_traces.jsonl` live 檔（僅 fixture／顯式 `--file`）
- AllowedPaths:
  - `scripts/run_p3_trace_local_harden_v1.py`
  - `tests/test_p3_trace_local_harden_v1.py`
  - `docs/p3-trace-local-harden-v1.md`
  - `docs/observability.md`（MAY · §7 一行 cross-ref only）
  - `04_Workflows/tickets/P3-TRACE-LOCAL-HARDEN-v1_state.md`（本票 B／C／D_REPORT；FRAME／STATE 僅 O）
  - `artifacts/p3_trace/**`（可選 `--write`）
- BlockedPaths:
  - 憲法 §7 類型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-ORCH-DESTRUCT／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
  - 暗部 `core/**`、他人 core、`.env`、venv 樹
  - `.github/workflows/**` · branch protection · mandatory CI 無批文
  - Dashboard Phase% 數字格 · `_phase_pct_apply.py --authorize`
  - 治理母本全文改寫（`HARNESS_CONSTITUTION.md`／`ENGINEERING_CONTRACT.md`）
  - `00_Agent_Work_Progress.md`／`master_status.md`／`handoff.md`（Scribe／Governance）
  - 其他票 FRAME／STATE（除本票報告區）
- Dependencies:
  - WAVE-B-P1-TRACE-QUERY-CLI（done）· `observability/trace_query.py` · `observability/trace_schema.py`
  - fixture：`tests/fixtures/trace/sample_traces.jsonl`（只讀）
  - Langfuse／PG：`docs/langfuse-pg-alignment-deferred-index-v1.md`（deferred · 本票不實作）
- relay_mode: same_chat
- phase_targets: [P3]
- baseline_pct: 82
- proposed_delta_pct: +1～+3
- evidence_gate: L-local · unittest + CLI `ok: true`
- apply_phase_pct: false
- ticket_class: code/thin
- evidence_tier: L-local
- non_claims:
  - ≠ prod Langfuse 升格／真接
  - ≠ Langfuse↔PG 全對齊完成
  - ≠ mandatory CI／Phase% apply
  - ≠ 改 live `runtime/checkpoints` 或暗部根
- AcceptanceCriteria:
  - AC-1: `python scripts/run_p3_trace_local_harden_v1.py --format text` → `ok: True` · checks 全 pass
  - AC-2: 輸出含 `schema_version=p3_trace_local_harden_v1` · `non_claims` 含 ≠ Langfuse／≠ PG align／≠ Phase% apply
  - AC-3: `python -m unittest tests.test_p3_trace_local_harden_v1 -v` 全綠
  - AC-4: 故意壞 JSONL（測試內 tempfile）→ `ok: false` 且 message 可辨
  - AC-5: 未改 `.github/workflows/**` · `apply_phase_pct=false` · 未碰暗部 core

---

## STATE

- overall_status: done
- current_owner: scribe
- next_action: 無（本票封存完成；Phase% 待另開 W-PROG）
- last_updated: 2026-07-15 · D（C accepted · Scribe 收口 STATE→done）
- ops_checklist: 無
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
    票先前不存在；near-100 P3 #1 無批文可寫。P2-INDEX-OBS 另線；本票專本地 harden，
    不切換他票。Langfuse-PG 仍 deferred（Wave C）。B 已交付 CLI／docs／tests；AC 證據見 B_REPORT。
    C accepted；D 依尚書省當次授權一併 STATE→done + Progress append。

---

## B_REPORT

- changed_files:
  - `scripts/run_p3_trace_local_harden_v1.py`（新建）
  - `tests/test_p3_trace_local_harden_v1.py`（新建）
  - `docs/p3-trace-local-harden-v1.md`（新建）
  - `docs/observability.md`（MAY · §7 一行 cross-ref + unittest 一行）
  - `04_Workflows/tickets/P3-TRACE-LOCAL-HARDEN-v1_state.md`（本票 STATE／B_REPORT）
- artifacts:
  - 可選 `artifacts/p3_trace/harden.latest.json`（`--write`；本輪未強制寫）
- verification:
  - `python scripts/run_p3_trace_local_harden_v1.py --format text` → **ok: True** · schema_fixture（7 events）· query_by_trace_id（3）· query_by_task_id（2）· `apply_phase_pct: False`
  - `python -m unittest tests.test_p3_trace_local_harden_v1 -v` → **Ran 7 · OK**（含壞 JSONL／缺必填鍵 → ok:false）
- behavior_notes:
  - 複用 `validate_trace_event` + `query_traces`；不重寫 observability core、不接 Langfuse／PG
  - `source_file` 優先 repo-relative posix
  - proposed P3 +1～+3 · **未** apply
- deferred_items:
  - `P3-LANGFUSE-PG-ALIGN-FRAME-v1`／實作（Wave C · 須批文）
  - live `runtime/task_traces.jsonl` 營運覆蓋（非本票）

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: >
    重跑 AC-1～AC-4 全過：CLI `--format text` → ok:True · schema_version=p3_trace_local_harden_v1 ·
    三 checks pass（schema_fixture 7 events／query_by_trace_id 3／query_by_task_id 2）·
    non_claims 含 ≠ Langfuse／≠ PG align／≠ Phase% apply · apply_phase_pct=False；
    unittest Ran 7 OK（含壞 JSONL／缺必填鍵 → ok:false）；
    產物落在 AllowedPaths（CLI／tests／docs 本票 + observability §7 MAY）；
    未改暗部 core；本票未觸 `.github/workflows/**`（工作區既有 workflow 髒檔≠本票 diff）；
    FRAME.apply_phase_pct=false 未抬 Phase%。Rule 3／8／11 滿足。
- risk_level: low
- suggestions: >
    （1）Scribe／O 收口敘事僅認領 observability §7 本票 cross-ref＋unittest 一行；
    同檔 §9 P2-INDEX-OBS footnote 屬另線，勿寫進本票 D_REPORT。
    （2）建議下一無批文薄刀：P2-INDEX-OBS 收口／footnote 對齊，或 WAVE-C
    `P3-LANGFUSE-PG-ALIGN-FRAME-v1`（須批文前僅 FRAME）。
    （3）O 請將 STATE → scribe · current_owner=scribe · next_action=D 收口。
- next_action_hint: scribe
- reviewed_at: 2026-07-15 · C

---


## D_REPORT

- scribe_date: 2026-07-15 · Scribe（D）
- verdict_echo: Reviewer `accepted` · risk=low · blocking 無 · AC-1～AC-5 對照 C_REPORT 通過
- docs_updates:
  - 已交付（B；本輪不重寫）：`docs/p3-trace-local-harden-v1.md`
  - 已交付（B MAY；本輪不重寫）：`docs/observability.md` §7 本票入口 cross-ref + unittest 一行
  - **敘事邊界**：本票 D_REPORT／Progress **僅**認領上述本票產物；**不**把工作區另線腳註／他票 dirty 寫入本條
- progress_entry: >-
    見 `04_Workflows/00_Agent_Work_Progress.md` 末尾 —
    **2026-07-15 · P3-TRACE-LOCAL-HARDEN-v1 · done**
- followup_suggestions:
  - 下一無批文薄刀：Wave B sandbox execute／RAG E2E 擇一；或 Wave C `P3-LANGFUSE-PG-ALIGN-FRAME-v1`（須批文前僅 FRAME）
  - Phase%：proposed P3 +1～+3 僅敘事 · **待另開 W-PROG** 方可 apply
  - 勿碰：`_phase_pct_apply --authorize` · Dashboard 數字格 · Langfuse 真接／PG 對齊實作 · mandatory CI
- Phase 影響:
  - 影響 Phase: P3
  - baseline: 82
  - proposed_delta: +1～+3
  - 實際上調: 否／待 W-PROG
  - apply_phase_pct: false（未 authorize）
- non_claims:
  - ≠ Langfuse 真接／prod 升格
  - ≠ Langfuse↔PG 全對齊完成
  - ≠ Phase% uplift／Dashboard 數字格寫入
  - ≠ mandatory CI／`.github/workflows/**` 本票改動
  - ≠ 改 live `runtime/task_traces.jsonl`／暗部 core
