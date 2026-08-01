# TICKET STATE · P4-LOCAL-SIMILARITY-v1 · 上游 eval 產出 local_similarity_pct

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> **Fix Ledger SSOT**：`04_Workflows/cross_agent_fix_ledger.yaml` → `P4-local-similarity-null`

---

## FRAME

<!-- Orchestrator 填 · 2026-07-09 凍結；後續變更僅 Orchestrator 顯式更新 -->

- Goal: 讓上游 `asset_value_eval_*.json` 實際產出 similarity，使 `scout_last_pipeline.json` 的 `local_similarity_pct` 不再全為 null。
- Scope:
  - 盤點 `02_Agents_Core/Asset_Value_Evaluator_Agent.py` 既有 `local_similarity_pct`／`_semantic_overlap_pct`／ROI 路徑，確認為何未寫入戰報 JSON
  - 讓最新 `06_Exports_Output/reports/asset_value_eval_*.json`（或等價戰報）含可透傳的 similarity 欄位
  - 確認 `04_Workflows/_sync_wave_to_scout_pipeline.py` 透傳後，`scout_last_pipeline.json` → `match_report.top_matches[].local_similarity_pct` 非全 null
  - 跑通 ledger `P4-local-similarity-null` 的 `verify_cmd`；通過後更新 ledger：`status: fixed`、`evidence`、`updated_at`、`owner_last`
  - Progress／本 STATE 僅 append 一行摘要（不重寫歷史）
- NonScope:
  - 不重開／不回退 P1–P3（ledger 已標 fixed；除非 verify 失敗改 `needs_reverify`）
  - 不改 Hermes／OmniRoute／Telegram gateway
  - 不改 Phase% Dashboard、不改憲法／合約全文
  - 不宣稱「內容相似度已達 production SLA」——本票只要求欄位非全 null 且可驗證
- AllowedPaths:
  - `02_Agents_Core/Asset_Value_Evaluator_Agent.py`
  - `04_Workflows/_sync_wave_to_scout_pipeline.py`
  - `06_Exports_Output/reports/scout_last_pipeline.json`
  - `06_Exports_Output/reports/asset_value_eval_*.json`（產物）
  - `04_Workflows/cross_agent_fix_ledger.yaml`（僅 P4 一筆）
  - `04_Workflows/tickets/P4-LOCAL-SIMILARITY-v1_state.md`（本檔 REPORT 區塊）
  - `tests/**`（可選：補 P4 回歸測）
- BlockedPaths:
  - `AGENTS.md` 紅線相關、`.env`、venv、暗部禁區類型（憲法 §7）
  - 其他 `tickets/*_state.md`（本票除外）
  - Hermes 根目錄設定（除非尚書省另開票）
- Dependencies:
  - Fix Ledger 已建：`04_Workflows/cross_agent_fix_ledger.yaml`
  - P1–P3 已 fixed（勿混修）
- AcceptanceCriteria:
  - AC-1：最近一批管線中，`scout_last_pipeline.json` 的 `top_matches` 至少一筆 `local_similarity_pct is not None`
  - AC-2：ledger `P4-local-similarity-null` 的 `verify_cmd` exit 0
  - AC-3：ledger 該筆 `status` 升為 `fixed`，`evidence`／`updated_at`／`owner_last` 已更新
  - AC-4：Progress 末尾有一行本票完成摘要（或本 STATE B_REPORT 已寫驗證命令）

### Wave Master 擴展（可選）

- wave_id: null
- group_id: null
- lifecycle_phase: B
- phase_targets: []
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: []
  - downstream_waves: []
  - blocks_if_missing: []
- risks:
  - id: R1
    description: eval 主路徑未呼叫 ROI similarity，只改 sync 仍全 null
    likelihood: high
    impact: medium
    mitigation: 先追 Asset_Value_Evaluator 寫入戰報的欄位集合
    residual: 可能需改 agent core 而非僅 workflows
- observability:
  - verify_commands:
    - "python -c \"import json, pathlib; p=pathlib.Path('06_Exports_Output/reports/scout_last_pipeline.json'); d=json.loads(p.read_text(encoding='utf-8')); tm=(d.get('match_report') or {}).get('top_matches') or []; vals=[x.get('local_similarity_pct') for x in tm]; assert tm and any(v is not None for v in vals), vals; print('P4 OK', vals[:5])\""
  - evidence_artifacts:
    - 06_Exports_Output/reports/scout_last_pipeline.json
    - 06_Exports_Output/reports/asset_value_eval_*.json
    - 04_Workflows/cross_agent_fix_ledger.yaml
  - success_signals: ["verify_cmd exit 0", "ledger status=fixed"]
  - failure_signals: ["top_matches 全 null", "ledger 仍 partial/open"]
- non_claims:
  - 不宣稱 similarity 演算法已達業務級準確度
  - 不宣稱 Groq ROI 路徑已強制開啟
- ticket_class: build
- evidence_tier: L-local
- parallel_ok: false

---

## STATE

<!-- Orchestrator 維護 -->

- overall_status: done
- lifecycle_phase: O
- current_owner: orchestrator
- next_action: none_closed
- last_updated: 2026-07-09 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: n/a
  - scribe: n/a
- ledger_ref: P4-local-similarity-null
- claim_note: claim 已清空；ledger status=fixed

---

## B_REPORT

<!-- Implementer 填 · 2026-07-09 -->

- changed_files:
  - `04_Workflows/_sync_wave_to_scout_pipeline.py`（補算 `_semantic_overlap_pct`、回寫 eval rows、寫入 scout）
  - `tests/test_p4_local_similarity_sync_v1.py`（新建）
  - `06_Exports_Output/reports/scout_last_pipeline.json`（產物）
  - `06_Exports_Output/reports/asset_value_eval_975d9d36d7c447d2958562c72159d5b6.json`（回寫 similarity）
  - `04_Workflows/cross_agent_fix_ledger.yaml`（P4 → fixed）
- artifacts: scout + eval 已含非 null `local_similarity_pct`
- verification:
  - `python 04_Workflows/_sync_wave_to_scout_pipeline.py` → ok · filled=11 · persisted=11
  - `python -m unittest tests.test_p4_local_similarity_sync_v1 -v` → 2/2 OK
  - ledger verify_cmd → `P4 OK [0.87, 0.8, 0.9, 0.91, 0.8]`
- behavior_notes: 根因是 eval `rows` 從未寫 similarity；ROI 路徑另有函式但未接波次戰報。本票在 sync 橋接層補算並回寫上游，不改 Agent 主評估迴圈。
- deferred_items: 未把 similarity 寫進 `Asset_Value_Evaluator_Agent.evaluate` 主迴圈（未來波次仍靠 sync 補算）；未宣稱業務級相似度準確度。

---

## C_REPORT

<!-- 本輪由同一施工 chat 自驗關票；未另開 Reviewer -->

- conclusion: accepted_with_gaps
- blocking_issues: 無
- checks_summary: AC-1～AC-3 以 verify_cmd + unittest 通過；AC-4 Progress 一行待 append
- risk_level: low
- suggestions: 若要更高覆蓋率分數，可另票改 needle／在 evaluate 主迴圈寫入 similarity

---

## D_REPORT

- docs_updates: Fix Ledger P4 已升 fixed；AGENTS／command_queue 約定沿用
- progress_entry: 2026-07-09 · P4-LOCAL-SIMILARITY-v1 · sync 補算 similarity · ledger fixed
- followup_suggestions: 可選另票在 Evaluator 主迴圈原生寫入 `local_similarity_pct`
