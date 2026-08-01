# TICKET STATE · W1-T3 · Eval／Trace／WF 觀測閉環 CI Artifact

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 1 - Governance & Observability

---

## FRAME

- Title: Eval／Trace／WF 觀測閉環 CI Artifact
- Goal: nightly／PR 可產出 Gate + Index + Trace 一頁總覽與 flagged triage 附錄，供治理決策消費。
- Scope:
  - 擴充 .github/workflows/eval-gate-ci.yml：上傳 wf_status_summary + eval_trace_correlate triage-md artifact
  - 固定 fixture 路徑與 GOV_EVAL_EXPORT_KB_INDEX_STATUS=1 側車驗證
  - 文檔：docs/observability.md 新增 §9 CI 觀測產物索引
  - 不改 eval gate 閾值邏輯
- NonScope:
  - Grafana／Slack 通知
  - Langfuse 統一查詢 API
  - prod selector 接線
- AllowedPaths:
  - .github/workflows/eval-gate-ci.yml
  - docs/observability.md
  - artifacts/eval/**
  - artifacts/wf/**
- BlockedPaths:
  - core/ask_rag_selector.py
  - config/routing_policy.yaml
  - AGENTS.md
- Dependencies:
  - Wave B 模組（eval_exporter、eval_report、wf_status_summary、eval_trace_correlate）
  - tests/fixtures/eval/、tests/fixtures/trace/
- Risks:
  - fixture 過小導致 needs_review 比例不穩定 → 文檔標 investigation-only
  - kb_index_status 缺失時 export 降級為 n/a 分桶
- Observability:
  - logs: CI step 輸出 needs_review 比例、樣本 N
  - metrics: eval_ci_check pass/fail
  - traces: correlate join 率（flagged 列 trace_found 比例）
- OutputArtifacts:
  - 更新 eval-gate-ci.yml
  - artifacts/eval/、artifacts/wf/ CI 上傳樣本
  - docs/observability.md §9
- AcceptanceCriteria:
  - PR workflow 綠；artifact 含 eval_report、wf_status_summary、triage-md
  - python -m unittest tests.test_wf_status_summary tests.test_eval_trace_correlate -v 全綠
  - artifact 內 ok 欄位可機器解析
- VerificationCommands:
  - `python -m unittest tests.test_wf_status_summary tests.test_eval_trace_correlate -v`
    - 預期：全綠
  - `GitHub Actions eval-gate-ci workflow`
    - 預期：綠；artifact 可下載

---

## STATE

- overall_status: done
- implementation_status: landed_ci_green
- current_owner: none
- next_action: 無（C_REPORT 已簽）；**P6 DAY3／Round-2 仍 defer／等時間**（非本票）
- last_updated: 2026-07-13 · reviewer（C_REPORT）
- status_by_role:
  - orchestrator: done
  - implementer: done — land + CI green
  - reviewer: done — C_REPORT accepted
  - scribe: done — Progress／QUEUE 本輪回填
- land_evidence:
  - auth: 尚書省明示同意 W1-T3-CI-LAND 入庫（2026-07-12）
  - commits:
    - `d6a9c373c` — modules + docs §9 + eval-gate steps
    - `bde9a8ea4` — eval_* API deps + fixtures（首推後 CI 暴露缺口）
  - local_unittest: `tests.test_wf_status_summary` + `tests.test_eval_trace_correlate` → **25 OK**；全 eval-gate suite **74 OK**
  - ci_push: run `29195842807` **success**（含 W1-T3 steps + artifact upload）
  - ci_dispatch: run `29195843133` **success**
  - branch: `main`
  - defer_unchanged:
    - P6 nightly 綠日鐘仍 **2/7** · 等 DAY3+ schedule（≠ 本票）
    - Round-2 仍 DEFER · earliest **07-18**（≠ 本票）

---
## B_REPORT

> **C 區（Orchestrator 預填）**：Implementer 施工時更新下方欄位，保留 Implementation Plan 歷史。

### Implementation Plan (initial)

- [x] 擴充 eval-gate-ci.yml 上傳 wf_status_summary artifact
- [x] 加入 eval_trace_correlate --format triage-md 產物
- [x] 固定 fixture 與 GOV_EVAL_EXPORT_KB_INDEX_STATUS=1 驗證
- [x] 撰寫 observability.md §9

### Files To Touch

- .github/workflows/eval-gate-ci.yml
- docs/observability.md
- artifacts/eval/
- artifacts/wf/

- changed_files:
  - `.github/workflows/eval-gate-ci.yml` — PR/nightly 新增 wf_status_summary、eval_trace_correlate triage-md、kb_index sidecar 步驟；unittest 加入 `test_wf_status_summary`/`test_eval_trace_correlate`；artifact 更名 `eval-gate-observability-pr|nightly`
  - `docs/observability.md` — 新增 §9 CI observability artifacts (W1-T3)；Wave A 改 §10；Related docs 改 §11；§8 交叉引用 §9
  - `04_Workflows/tickets/W1-T3_state.md` — 本輪 B_REPORT / STATE
- artifacts:
  - `artifacts/eval/eval_report.latest.{json,md}`
  - `artifacts/wf/wf_status_summary.latest.{json,md}`
  - `artifacts/eval/eval_trace_correlate.latest.{json,triage.md}`
  - `artifacts/eval/eval_export_kb_index_sidecar.latest.jsonl`
- verification:
  - `python -m unittest tests.test_wf_status_summary tests.test_eval_trace_correlate -v` → **exit 0**；25 tests OK
  - `python -m observability.eval_report tests/fixtures/eval/eval_export_sample.jsonl --out-dir artifacts/eval` → exit 0；`ok: true`
  - `python -m observability.wf_status_summary --eval tests/fixtures/eval/eval_export_sample.jsonl --index-status workflow_v2/20_pilot/W3-B/index_status_W2-1.json --trace-jsonl tests/fixtures/trace/sample_traces.jsonl --out-dir artifacts/wf` → exit 0；`ok: true`；trace_join hit_rate=0.5
  - `python -m observability.eval_trace_correlate … --format triage-md -o artifacts/eval/eval_trace_correlate.latest.triage.md` → exit 0
  - `GOV_EVAL_EXPORT_KB_INDEX_STATUS=1 python -m observability.eval_exporter tests/fixtures/eval/ibridge_records.jsonl -o artifacts/eval/eval_export_kb_index_sidecar.latest.jsonl --case-index-map tests/fixtures/eval/case_index_map_W2-1.json` → exit 0；`t-infra` 列 `kb_index_status=ready`
  - GitHub Actions eval-gate-ci workflow → **未在本輪觸發**（Reviewer 可手動 `workflow_dispatch` 驗 artifact 上傳）
- behavior_notes:
  - **不改** eval gate 閾值邏輯；PR job 固定 fixture，needs_review 比例僅 investigation（文檔 §9.4 已標）
  - kb_index 缺失時 export 行無 `kb_index_status` 欄（`n/a` 分桶）；CI 以 `t-infra`/`W2-1` case map 驗 sidecar 非空
  - ingest 三源（PG/Langfuse/JSONL）**不在** eval-gate-ci artifact；交叉引用 W1-T2 `artifacts/monitoring/pg_ingest_soak.latest.json`（§9.6）
  - nightly job 沿用 shadow export 或 fixture fallback；wf/triage 步驟 `continue-on-error: true`（與既有 nightly 語意一致）
- deferred_items:
  - CI workflow 手動觸發驗證（本 Implementer 環境未跑 Actions）
  - `daily_cost_summary` vs `task_runs` 統一（FRAME NonScope / W1-T2 follow-up）
  - Grafana/Slack、Langfuse 統一查詢 API、prod selector（FRAME NonScope）

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: |
    對照 FRAME AC：本機 unittest 25 OK（land 證據）· 遠端 eval-gate push `29195842807` success · dispatch `29195843133` success（含 W1-T3 artifact 步驟）。
    Scope 邊界：僅 eval-gate CI artifact + observability §9 + 觀測模組／fixtures；未改 eval gate 閾值、selector、routing_policy。
    NonScope 維持：Grafana／Slack／Langfuse 統一 API／prod selector 未碰。
    Rule-11：遠端 CI 綠 + land commits `d6a9c373c`／`bde9a8ea4` 可重跑驗證；≠ Phase% uplift。
- risk_level: low
- suggestions: 無必須 follow-up；P6 DAY3／Round-2 仍屬他票 defer，勿併入本票。

---

## D_REPORT

- docs_updates: `docs/observability.md` §9 已寫（本機）；須隨 LAND 一併入庫審 diff
- progress_entry: 2026-07-12 授權 LAND 完成 · commits d6a9c373c／bde9a8ea4 · CI 29195842807／29195843133 success · P6/Round-2 仍 defer
- followup_suggestions: 開／沿用本票執行 **W1-T3-CI-LAND**；勿與 W1-T3B（MVP mainline）混淆

### LANDING checklist（下一棒 · 須授權 commit/push）

1. `git add observability/wf_status_summary.py tests/test_wf_status_summary.py tests/test_eval_trace_correlate.py`（+ 審過的 `docs/observability.md` diff）
2. 本機再跑：`python -m unittest tests.test_wf_status_summary tests.test_eval_trace_correlate -v`（預期 25 OK）
3. 恢復 `.github/workflows/eval-gate-ci.yml` 內 W1-T3 unittest／artifact 步驟（對照本檔 B_REPORT · **僅在步驟 1 已入庫後**）
4. commit → push → `workflow_dispatch` eval-gate-ci → 確認 artifact 含 wf_status_summary／triage-md
5. Reviewer 填 C_REPORT；Scribe 回填 Progress／QUEUE

---

## O_NOTES

> **O 區**：Orchestrator 維護 run log 與戰報連結；Observe / Operate 計畫。

### Observability Plan

- CI artifact 保留策略見 workflow；needs_review 比例僅 investigation

### Rollout / Ops Notes

- CI artifact 保留策略見 workflow；needs_review 比例僅 investigation
- **2026-07-12**：遠端 eval-gate **刻意不含** W1-T3 模組引用（回綠優先）；LAND 前勿再加

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 開票 FRAME/STATE/B_REPORT 預填 | 本檔 |
| 2026-06-07 | implementer | CI artifact 接線 + observability §9；unittest 全綠；STATE→in_review | 本檔 B_REPORT |
| 2026-07-12 | implementer | 續作盤點：本機 25 OK；3 檔未追蹤；遠端回綠無 W1-T3；STATE→blocked_remote_land | Progress 末尾 · QUEUE note |
| 2026-07-12 | 尚書省 | 授權 W1-T3-CI-LAND 入庫（僅本票；P6/Round-2 仍等） | 本輪指令 |
| 2026-07-12 | implementer | land `d6a9c373c`+`bde9a8ea4` · CI green `29195842807`/`29195843133` · STATE→done | 本檔 · Progress |
| 2026-07-13 | reviewer | C_REPORT **accepted** · 對照 CI `29195842807`/`29195843133` · ≠ Phase% | 本檔 C_REPORT |
