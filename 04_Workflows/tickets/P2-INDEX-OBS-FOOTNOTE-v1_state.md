# TICKET STATE · P2-INDEX-OBS-FOOTNOTE-v1 · Index obs 腳註（薄）

> Wave B 可並行薄票 · 2026-07-15 · Multi-Chat O→B same_chat  
> 對齊：`GAP-OBS-INDEX` · contract §6.4 · P1 R4 INDEX 敘事 **explicit defer**

---

## FRAME

- Goal: 以薄 doc／腳註對齊 `run_id`↔`agent_runs`（contract §6.4）與 Wave B `index_cases` 命名空間邊界，關閉 GAP-OBS-INDEX 的**敘事／腳註**缺口（≠ 真接线实现）。
- Scope:
  - MUST：新建 `docs/phase2-index-obs-footnote-v1.md`（non_claims · 命名空間對照 · 驗收命令）
  - MUST：在 gap-audit `GAP-OBS-INDEX`、contract §6.4、`docs/observability.md`、hook doc §7 各加**最小**交叉引用腳註
  - MUST：薄測 `tests/test_phase2_index_obs_footnote_v1.py`；既有 `tests.test_phase2_knowledge_indexing_contract_v1` 仍綠
  - MAY：腳註提及 P1 R4 INDEX 全文輕修仍 **explicit defer**（本票不改 INDEX）
- NonScope:
  - 不改 `04_Workflows/WORKFLOW_INDEX.md` 全文（對齊 P1-GOV R4 defer）
  - 不實現 `run_id`↔`agent_runs` 真接线；不改 `core/data_pipeline.py`／他人 core
  - 不寫 Dashboard Phase%；`apply_phase_pct=false`
  - 不碰 H2–H5／P9 prod／DarkOps／Z-* 禁區類型
  - 不開 P3-TRACE／sandbox execute／RAG E2E
- AllowedPaths:
  - `docs/phase2-index-obs-footnote-v1.md`
  - `docs/phase2-index-contract-gap-audit-v1.md`
  - `docs/phase2-knowledge-indexing-contract-v1.md`
  - `docs/observability.md`
  - `docs/phase2-index-job-hook-v1.md`
  - `tests/test_phase2_index_obs_footnote_v1.py`
  - `04_Workflows/tickets/P2-INDEX-OBS-FOOTNOTE-v1_state.md`
- BlockedPaths:
  - `04_Workflows/WORKFLOW_INDEX.md`（R4 defer）
  - `docs/WAVE_PROGRESS_DASHBOARD.md` Phase% 數字格
  - `core/**`、暗部 root、`.env`／venv／`runtime/checkpoints/**`
  - `HARNESS_CONSTITUTION.md`、`ENGINEERING_CONTRACT.md` 正文
  - `.github/workflows/**`、H2–H5／P9 prod 路徑
  - 憲法 §7：Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-ORCH-DESTRUCT／Z-DARK-OPS／Z-HQ-LIQUIDATION
- Dependencies:
  - 上游：WA-T1 contract · FP-G2-T2 gap-audit（GAP-OBS-INDEX）· P1-GOV R4 defer
  - 並行：可與 `P2-HOOK-LOCAL-SANDBOX-EXECUTE-v1` 並行；不依賴 write
- relay_mode: same_chat
- ticket_class: doc/spec
- evidence_tier: L-local
- parallel_ok: true
- estimated_cycles: 1
- mvp_allowed: true
- phase_targets: [P2]
- baseline_pct: 66
- proposed_delta_pct: +1～+2
- apply_phase_pct: false
- evidence_gate: footnote doc + thin unittest + contract unittest 仍綠
- non_claims:
  - 本票腳註 ≠ `run_id`↔`agent_runs` 已接线
  - Wave B `index_cases`／`kb_index_status` ≠ 全库 index 排程 SSOT
  - 本票 ≠ P2 closure／Phase% 上調
  - 本票 ≠ WORKFLOW_INDEX 全文修訂（R4 仍 defer）
- AcceptanceCriteria:
  - AC-1: `docs/phase2-index-obs-footnote-v1.md` 存在，含 `GAP-OBS-INDEX`、`run_id`、`agent_runs`、`index_cases`、non_claims
  - AC-2: `rg "phase2-index-obs-footnote-v1|GAP-OBS-INDEX" docs/phase2-index-contract-gap-audit-v1.md docs/phase2-knowledge-indexing-contract-v1.md docs/observability.md docs/phase2-index-job-hook-v1.md` 均有交叉引用
  - AC-3: `python -m unittest tests.test_phase2_index_obs_footnote_v1 tests.test_phase2_knowledge_indexing_contract_v1 -v` → OK
  - AC-4: 未改 `WORKFLOW_INDEX.md`；`apply_phase_pct=false`；未寫 Dashboard %
  - AC-5: 文檔無本機絕對路徑／金鑰原文

---

## STATE

- overall_status: done
- current_owner: ops
- next_action: 無（本票已封存）；下一可派見 D_REPORT followup
- last_updated: 2026-07-15 · scribe（D 收口）
- ops_checklist: 無
- status_by_role:
  - orchestrator: done — FRAME 凍結
  - implementer: done — B_REPORT 已填
  - reviewer: done — C_REPORT accepted
  - scribe: done — D_REPORT + Progress 末尾

---

## B_REPORT

- changed_files:
  - `docs/phase2-index-obs-footnote-v1.md`（新建）
  - `docs/phase2-index-contract-gap-audit-v1.md`（GAP-OBS-INDEX 列 → 腳註已交付）
  - `docs/phase2-knowledge-indexing-contract-v1.md`（§6.4 腳註）
  - `docs/observability.md`（§9.3 後 `index_cases` 分欄腳註）
  - `docs/phase2-index-job-hook-v1.md`（§7 交叉引用）
  - `tests/test_phase2_index_obs_footnote_v1.py`（新建薄測）
  - `04_Workflows/tickets/P2-INDEX-OBS-FOOTNOTE-v1_state.md`（FRAME／STATE／B_REPORT）
- artifacts:
  - Index obs 腳註 SSOT：`docs/phase2-index-obs-footnote-v1.md`
- verification:
  - `python -m unittest tests.test_phase2_index_obs_footnote_v1 tests.test_phase2_knowledge_indexing_contract_v1 -v` → **OK** · **21** tests · 0.127s
  - 未改 `WORKFLOW_INDEX.md`／Dashboard Phase%（對齊 R4 defer · `apply_phase_pct=false`）
  - 無金鑰原文；腳註測含禁本機絕對路徑斷言
- behavior_notes:
  - 關閉 **GAP-OBS-INDEX** 的**敘事／可導航**缺口；真接线仍 deferred
  - Wave B `index_cases` 與 contract §6.4 分欄，避免誤讀為全庫排程 SSOT
  - 未切換 P3：Index 線未滿檔、本票先前不存在，依指令優先實作 P2
  - proposed P2 +1～+2 · **未** apply
- deferred_items:
  - `run_id`↔`agent_runs` 真接线（另授權票）
  - WORKFLOW_INDEX R4 輕修（尚書省明示後另票）
  - W-PROG apply Phase%

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary:
  - AC-1 **PASS**：`docs/phase2-index-obs-footnote-v1.md` 存在；含 `GAP-OBS-INDEX`／`run_id`／`agent_runs`／`index_cases`／`non_claims`
  - AC-2 **PASS**：四檔均含 `phase2-index-obs-footnote-v1` 與／或 `GAP-OBS-INDEX` 交叉引用（gap-audit／contract §6.4／observability §9／hook §7）
  - AC-3 **PASS**：Reviewer 重跑 `python -m unittest tests.test_phase2_index_obs_footnote_v1 tests.test_phase2_knowledge_indexing_contract_v1 -v` → **OK · 21 tests · 0.129s**
  - AC-4 **PASS**：本票 `changed_files` 未含 INDEX／Dashboard；`rg` 兩檔無本票號；FRAME／腳註 `apply_phase_pct=false`（工作樹 INDEX／Dashboard 他票脏改 ≠ 本票 touch）
  - AC-5 **PASS**：腳註無本機絕對路徑／金鑰；薄測含 drive-letter 禁斷言
  - 邊界：AllowedPaths 內；未碰 core／§7 禁區；敘事腳註 ≠ 真接线；proposed Δ 未灌水
- risk_level: low
- suggestions:
  - 非阻塞：薄測 `test_workflow_index_not_required…` 僅 assert INDEX 存在；後續可選加「本票號不得出現於 INDEX」負向斷言（R4 defer 硬化）
  - Phase%：proposed +1～+2 僅敘事；**禁止**本票／Scribe 寫 Dashboard 數字格；待 W-PROG
  - 建議下一票：`P3-TRACE-LOCAL-HARDEN-v1`（若 Wave B Index 薄線已收口）或計劃 Wave 2 下一刀（sandbox execute／RAG E2E 擇一，勿捆綁接线）
- handoff: **請 Scribe（D）收口** — 寫 D_REPORT + Progress 末尾；Phase 影響欄必填「實際上調=否／待 W-PROG」；non_claims 重申 ≠ 接线／≠ P2 closure

---

## D_REPORT

- docs_updates: 無新增 docs（B 已交付 `docs/phase2-index-obs-footnote-v1.md` + 四檔交叉引用；本輪僅 STATE／本區塊／Progress 末尾）
- progress_entry: 見 `04_Workflows/00_Agent_Work_Progress.md` 末尾「2026-07-15 · P2-INDEX-OBS-FOOTNOTE-v1 · done」
- followup_suggestions:
  - proposed P2 +1～+2 · **實際上調=否／待 W-PROG**；**禁止** `_phase_pct_apply --authorize`／改 Dashboard 數字格
  - 下一可派（須尚書省）：`P3-TRACE-LOCAL-HARDEN-v1` 或 Wave B 下一刀（sandbox execute／RAG E2E 擇一；勿捆綁接线）
  - C 非阻塞建議：薄測可選加「本票號不得出現於 INDEX」負向斷言（R4 defer 硬化）— 另票
- Phase 影響:
  - 影響 Phase：P2
  - baseline：66
  - proposed_delta：+1～+2
  - 實際上調：否／待 W-PROG
  - non_claims：≠ `run_id`↔`agent_runs` 接线 · ≠ P2 closure · ≠ Phase% uplift · ≠ WORKFLOW_INDEX 全文修（R4 defer）· ≠ 全库 index 排程 SSOT
- Reviewer：accepted · risk=low · C blocking=無
