# TICKET STATE · W5-T3-evidence-ingestion-observer-v1 · Cross-Wave Evidence Observer

> Master CP · Wave 5 · 證據匯入 spec + 只讀 observer CLI 骨架  
> Schema SSOT：`docs/ticket-schema-master-v1.md` · `W5-T2`  
> **注意**：舊檔 `W5-T3_state.md` 為 Memory+1 歷史票 · **本檔**為 QUEUE / W-MASTER 所指 observer 票。

---

## FRAME

- Goal: Wave 1–4 施工產生的 smoke JSON · B_REPORT verification · run URL 可被統一只讀查詢；觀測層可回答「本 Wave 有哪些可重跑證據、缺哪些 human 占位符」。
- Scope:
  - `docs/wave-evidence-ingestion-spec-v1.md`（≥4 證據類型 · trace_fields · human-only 分界）
  - `scripts/observe_wave_evidence_v1.py`（只讀 skeleton · `--wave` / `--ticket-id` · json|text）
  - `tests/test_observe_wave_evidence_v1.py`（ephemeral fixture）
  - `docs/WAVE_PROGRESS_DASHBOARD.md` §Multi-phase smoke 索引句（**不改 Phase%**）
- NonScope:
  - 不實作 full metrics / Grafana · 不改 smoke runners · 不 ingest secret
  - 不閉合 P10 runtime · 不將 P10.5 蒸餾 skeleton 宣稱 prod
  - 不偽造 GA run URL 為 verified
- AllowedPaths:
  - `docs/wave-evidence-ingestion-spec-v1.md`
  - `scripts/observe_wave_evidence_v1.py`
  - `tests/test_observe_wave_evidence_v1.py`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（敘事 only）
  - `04_Workflows/tickets/W5-T3-evidence-ingestion-observer-v1_state.md`
- BlockedPaths:
  - `.github/workflows/**`
  - `core/**`（非本票）
  - Dashboard Phase% 數字格
  - 憲法 §7 禁區類型（env / venv / checkpoints）
- Dependencies:
  - W5-T1 / W5-T2 / W5-T5（已 done）
  - W1-P75-TRACE（trace 欄位只消費）
  - playbook §4.3 · MP/MC smoke 產物格式（只讀）
- AcceptanceCriteria:
  - AC-1：spec 覆蓋 ≥4 種證據類型 + trace_fields 表
  - AC-2：`observe_wave_evidence_v1.py --wave W1 --format json` 回穩定 dict（含 `ok` · `gaps`）
  - AC-3：demo 路徑可列 `evidence_summary` 或 honest `gaps`（無檔不 crash）
  - AC-4：spec 明確 human-only vs AI 可驗證分界；CLI 不把 run URL 標 verified

### Wave Master 擴展

- wave_id: W5
- group_id: G3
- lifecycle_phase: B
- phase_targets: [P10, P10.5]
- estimated_cycles: 2
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [W5-T1-multi-chat-commands-v1, W5-T2-wave-master-ticket-template-v1, W5-T5-cross-wave-playbook-index-v1, W1-P75-TRACE-UPSTREAM-v1]
  - downstream_waves: [W5-T4 rollup inspector cross-ref]
  - blocks_if_missing: []
- risks:
  - id: RSK-W5-T3-01
    description: Wave 票未齊時 gaps 誤報
    likelihood: M
    impact: L
    mitigation: --wave 過濾 + spec 註明 planning gaps 預期
    residual: accept
  - id: RSK-W5-T3-02
    description: 路徑硬編碼違反 Rule 6
    likelihood: M
    impact: H
    mitigation: 相對路徑 + --repo-root · 禁絕對路徑常數
    residual: accept
  - id: RSK-W5-T3-03
    description: skeleton 被誤標 production observability
    likelihood: M
    impact: M
    mitigation: spec + CLI skeleton/non_claims
    residual: accept
- observability:
  - verify_commands:
    - "python scripts/observe_wave_evidence_v1.py --wave W5 --format json"
    - "python -m unittest tests.test_observe_wave_evidence_v1 -v"
  - evidence_artifacts:
    - docs/wave-evidence-ingestion-spec-v1.md
    - observe_wave_evidence_v1.py stdout JSON
  - trace_fields: [run_id, ticket_id, evidence_type, gap_reason, ga_run.url]
  - success_signals: [CLI ok=true 且 gaps honest]
  - failure_signals: [靜默忽略空 verification · 偽造 run URL verified]
- non_claims:
  - 非 production metrics backend
  - 非自動關閉 human-blocked 票
  - 不替代 Reviewer over-claim 判定
  - 非 P10/P10.5 runtime 閉環
- ticket_class: build
- evidence_tier: L-local
- parallel_ok: true

---

## STATE

- overall_status: done
- implementation_status: closed · C_accepted · D_scribe_done · orch_closed
- lifecycle_phase: O
- current_owner: orchestrator
- next_action: 无（本票收口完成）· Downstream 见 W5-T4（本輪已並行交付）
- last_updated: 2026-07-09 · Orchestrator（同輪 B→C→D→O）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  同輪開票關票。unittest 4/4 · CLI ok=true。舊 W5-T3_state.md（Memory+1）未改。

---

## B_REPORT

- changed_files:
  - `docs/wave-evidence-ingestion-spec-v1.md`
  - `scripts/observe_wave_evidence_v1.py`
  - `tests/test_observe_wave_evidence_v1.py`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（§Multi-phase smoke 索引句 · Phase% 不變）
  - `04_Workflows/tickets/W5-T3-evidence-ingestion-observer-v1_state.md`
- artifacts:
  - evidence ingestion spec v1
  - read-only observer CLI skeleton（json/text）
  - unittest 4 cases（ephemeral tmp）
- verification:
  - `python scripts/observe_wave_evidence_v1.py --wave W5 --format json` → `ok=true` · 含 `tickets` · `evidence_summary` · `gaps`
  - `python scripts/observe_wave_evidence_v1.py --wave W1 --format json` → `ok=true` · honest gaps（artifact_missing 等）
  - `python -m unittest tests.test_observe_wave_evidence_v1 -v` → **4/4 OK**
- behavior_notes: |
  skeleton=true；缺證據 → gaps 而非 crash；ga_run.url 永遠 verified=false（human-only）。
  empty verification 標記含 `<!-- pending -->`。
- deferred_items: 無（unittest 已納入 MVP · 非 stretch defer）

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: |
  AC-1 PASS（≥4 證據類型 + trace_fields）· AC-2 PASS（穩定 dict ok/gaps）·
  AC-3 PASS（無檔 honest gaps）· AC-4 PASS（human-only 分界 · 不標 verified）。
  AllowedPaths 內 · skeleton 已標 · risk=low。
- risk_level: low
- suggestions: 無

---

## D_REPORT

- docs_updates:
  - wave-evidence-ingestion-spec-v1.md · Dashboard observer 索引句
- progress_entry: |
  2026-07-09 · W5-T3 done · evidence observer spec+CLI skeleton · unittest 4/4 · C=accepted
- followup_suggestions:
  - W5-T4 已消費 trace_fields（本輪並行）
  - 未來可選：擴更多 smoke 邏輯路徑探針（另票）

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-07-09 | orch+B+C+D | 同輪開票關票 |
