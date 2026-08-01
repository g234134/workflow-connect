# W1-P75-UPSTREAM-ENTRY-INDEX-v1 — P7.5 Upstream Entry Index (doc-only)

> handoff 摘要檔 · Wave 1 · P7.5 upstream · doc-only 入口索引  
> **Schema SSOT**：`docs/ticket-schema-master-v1.md` · `W5-T2` · playbook §3.2

---

## FRAME
<!-- Orchestrator 2026-07-09 凍結 · 施工前勿改 -->

- Goal: Planner / Orchestrator 從單頁索引判斷 P7.5 **上游**讀哪幾份 doc/CLI，不混淆 W-MASTER 全 Wave 規劃與 Wave 5 cross-wave rollup（W5-T5）；補 W1-T3 縮減遺留的可發現性。
- Scope:
  - **MUST**：新建 `docs/p75-upstream-entry-index-v1.md` — ≥5 行入口表（gate CLI · policy YAML · intake CLI · deny path doc · trace doc · MP-SMOKE step 1）
  - **MUST**：`04_Workflows/WORKFLOW_INDEX.md` §1.6 追加 **P7.5 upstream entry** 一句（與 W-ORCH entry 並列 · **不**替代 W5-T5）
  - **MUST**：cross-ref `W1-P75-*` 四票 output · `P75-G*` 票 ID · Dashboard P7.5 列（只引用 · 不改 Phase%）
  - **MUST**：AC-2 邊界句 —「全 Wave playbook rollup → W5-T5；本 index 僅 P7.5 上游」
  - **MUST**：non-claims 引用 W-ORCH global non-claims（不複製 Phase%）
- NonScope:
  - **不**建全 Wave 1–5 rollup INDEX（**W5-T5**）
  - **不**合并 W-MASTER 與 W-ORCH 為單檔
  - **不**跑 dispatch 真掃描 · **不**含 Multi-Chat commands/schema 模板（**W5-T1/T2**）
  - **不**改 code／tests／gate runtime · **不**改 Phase% · Dashboard · `W-MASTER-wave-plan_state.md`
  - **不**重寫 deny／CLI／trace 正文（只索引既有產物）
- AllowedPaths:
  - `docs/p75-upstream-entry-index-v1.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（僅 §1.6 追加 P7.5 upstream entry 一句／短段）
  - `04_Workflows/tickets/W1-P75-UPSTREAM-ENTRY-INDEX-v1_state.md`（僅 **B_REPORT** 區塊 · Implementer）
- BlockedPaths:
  - 憲法 §7 禁區類型（env／venv／runtime checkpoints／暗部破壞性維運等）— 引用 `HARNESS_CONSTITUTION.md` §7
  - `ENGINEERING_CONTRACT.md` · `HARNESS_CONSTITUTION.md` · `AGENTS.md` · `.cursor/rules/**`
  - `routing/**` · `scripts/**` · `tests/**` · `core/**`
  - `.github/workflows/**`
  - `docs/WAVE_PROGRESS_DASHBOARD.md` · `04_Workflows/00_Agent_Work_Progress.md` · `project_status/master_status.md`（Scribe 末尾追加除外）
  - 本票 **FRAME／STATE／C_REPORT／D_REPORT**（Implementer 禁改）
  - 他人票 `*_state.md` FRAME／STATE · `W-MASTER-wave-plan_state.md`
- Dependencies:
  - upstream（done）：`W1-P75-POLICY-DENY-MVP-v1` · `W1-P75-INTAKE-CLI-MVP-v1` · `W1-P75-TRACE-UPSTREAM-v1`
  - 並列 SSOT（非阻塞）：`W5-T5-cross-wave-playbook-index-v1`
  - 只讀：`W-ORCH-wave-next-control-plane-v1_state.md` §全局 non-claims
  - **無** human／infra／security 前置
- AcceptanceCriteria:
  - AC-1：index 含 P7.5 上游 **≥5** 入口行（CLI/doc 各至少 2）
  - AC-2：明確寫「全 Wave playbook rollup → W5-T5；本 index 僅 P7.5 上游」
  - AC-3：WORKFLOW_INDEX §1.6 可達本 index + W1-P75-TRACE doc
  - AC-4：non-claims 引用 W-ORCH global non-claims（不複製 Phase%）
  - AC-5：`rg "p75-upstream-entry|run_intake_gate_cli" docs/p75-upstream-entry-index-v1.md 04_Workflows/WORKFLOW_INDEX.md` 有命中

### Wave Master 擴展

- wave_id: W1
- group_id: G7
- lifecycle_phase: B
- phase_targets: [P7.5]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [W1-P75-POLICY-DENY-MVP-v1, W1-P75-INTAKE-CLI-MVP-v1, W1-P75-TRACE-UPSTREAM-v1]
  - downstream_waves: [W5-T5, W5-T3, Wave2]
  - blocks_if_missing: []
- risks:
  - id: RSK-W1-P75-IDX-01
    description: 與 W5-T5 重疊
    likelihood: low
    impact: medium
    mitigation: NonScope + AC-2 明示邊界
    residual: accept
  - id: RSK-W1-P75-IDX-02
    description: 與原 W1-T3 雙 CP 敘事混淆
    likelihood: low
    impact: medium
    mitigation: 本票僅 P7.5 upstream · 雙 CP 見 W5-T5
    residual: accept
- observability:
  - verify_commands:
    - `rg "p75-upstream-entry|run_intake_gate_cli" docs/p75-upstream-entry-index-v1.md 04_Workflows/WORKFLOW_INDEX.md`
    - `rg "W5-T5|僅 P7.5" docs/p75-upstream-entry-index-v1.md`
  - evidence_artifacts: [docs/p75-upstream-entry-index-v1.md, WORKFLOW_INDEX.md §1.6]
  - trace_fields: [wave_id, entry_type]
  - success_signals: [新 Orchestrator 無口述即可列出 P7.5 上游五入口]
  - failure_signals: [index 含 commands/schema 主施工（應 defer W5）]
- non_claims: >-
  P7.5 upstream only · 非 W5 rollup · 非 lane 自動編排 · 非 Phase% 上調 ·
  引用 W-ORCH global non-claims（local≠prod · advisory≠required · 無 run URL≠GA）
- ticket_class: doc/spec
- evidence_tier: L-local
- parallel_ok: false

---

## STATE

- overall_status: done
- implementation_status: closed · C_accepted · D_scribe_done · orch_closed
- lifecycle_phase: closed
- current_owner: orchestrator
- next_action: 無（本票收口完成）· Downstream 見 D_REPORT followup（W5-T5／Wave2／W5-T3）
- last_updated: 2026-07-09 · Orchestrator（讀 D_REPORT → 標 done）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  B→C→D 齊：C_REPORT `accepted`（AC-1–AC-5 PASS · risk=low）·
  D_REPORT + Progress 末尾已 append · O 獨立重跑 AC-5／W5-T5 邊界 rg 綠 ·
  index 實體存在。本票僅 §1.6 增量歸因（C 非阻塞建議已記）。
  未改 code／tests／Phase%／Dashboard／FRAME。標 overall_status=done。

---

## B_REPORT

- changed_files:
  - `docs/p75-upstream-entry-index-v1.md`（新建 · 入口表 ≥5 行 · W5-T5 邊界 · ticket map · non-claims 引用 W-ORCH）
  - `04_Workflows/WORKFLOW_INDEX.md`（§1.6 追加 P7.5 upstream entry 一句 · 指向本 index + TRACE doc）
  - `04_Workflows/tickets/W1-P75-UPSTREAM-ENTRY-INDEX-v1_state.md`（本 B_REPORT）
- artifacts:
  - `docs/p75-upstream-entry-index-v1.md`
- verification:
  - `rg "p75-upstream-entry|run_intake_gate_cli" docs/p75-upstream-entry-index-v1.md 04_Workflows/WORKFLOW_INDEX.md` → 命中 index 表列 + §1.6 入口句 + P75-G2 CLI 既有行
  - `rg "W5-T5|僅 P7.5" docs/p75-upstream-entry-index-v1.md` → AC-2 邊界句命中
  - `rg "P7.5 upstream entry" 04_Workflows/WORKFLOW_INDEX.md` → §1.6 可達
  - 紙面 AC-1：入口表 7 行（cli×3 · doc×4）≥5 · CLI/doc 各 ≥2
  - 紙面 AC-4：Non-claims 節引用 W-ORCH global non-claims · 未複製 Phase% 表
- behavior_notes:
  - doc-only；未改 routing／scripts／tests
  - Dashboard 僅列為只讀入口行 · 未改 Phase%
- deferred_items:
  - W5-T5 全 Wave rollup（明示 out of scope）
  - Scribe Progress 末尾（Reviewer accepted 後）

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary: >
  已讀 FRAME／STATE／B_REPORT；spot-check `docs/p75-upstream-entry-index-v1.md` 與
  `WORKFLOW_INDEX.md` §1.6；獨立重跑 AC-5／observability rg 全綠；索引路徑實體存在性抽查全 True。
  AC-1：入口表 7 行（cli×3 · doc×4）≥5，且含 gate CLI／policy YAML／intake CLI／deny／trace／MP-SMOKE step 1／Dashboard 只讀列 — PASS。
  AC-2：Boundary 表 +「全 Wave playbook rollup → W5-T5；本 index 僅 P7.5 上游」一句 — PASS。
  AC-3：§1.6「P7.5 upstream entry」指向本 index + TRACE doc，並標僅上游／W5-T5 — PASS。
  AC-4：Non-claims 引用 W-ORCH §全局 non-claims，未複製 Phase% 表；明示不調 % — PASS。
  AC-5：`rg "p75-upstream-entry|run_intake_gate_cli"` 於 index + WORKFLOW_INDEX 命中 — PASS。
  邊界（Rule 3/8）：B 主張變更僅 AllowedPaths（新 index + §1.6 一句 + B_REPORT）；未改 code／tests／routing／Dashboard／Phase%／deny·CLI·trace 正文。
  模擬接戰 traversal：§1.6 → index Boundary → Entry table → Ticket map → Suggested read order 可無口述走完。
  四流派最低覆蓋：Context/Source/Incremental/Debugging（L-local rg + 紙面 AC）滿足；Rule 11 證據可重跑。
- risk_level: low
- suggestions: >
  工作樹中 `WORKFLOW_INDEX.md` 相對 HEAD 另有大量既有未提交 diff（非本票 B_REPORT 主張範圍）。
  收口／commit 時請只歸因本票 §1.6「P7.5 upstream entry」一句，勿把整檔 rewrite 算進本票。
  可選：Scribe 於 Progress 註明「本票僅 §1.6 增量」。

---

## D_REPORT

- docs_updates:
  - `docs/p75-intake-cli-upstream-mvp-v1.md` — Cross-references 追加 entry index
  - `docs/p75-policy-deny-path-mvp-v1.md` — Cross-references 追加 entry index
  - `docs/p75-intake-gate-control-plane-trace-v1.md` — Changelog + Downstream consumers 指向 entry index
  - `04_Workflows/00_Agent_Work_Progress.md` — 末尾追加本票收口戰報（**僅** §1.6 增量歸因）
  - （B 已交付 · 本輪未改）`docs/p75-upstream-entry-index-v1.md` · `WORKFLOW_INDEX.md` §1.6「P7.5 upstream entry」一句
- progress_entry: >
  2026-07-09 · W1-P75-UPSTREAM-ENTRY-INDEX-v1 · Scribe 收口 · C_REPORT `accepted` ·
  交付 `docs/p75-upstream-entry-index-v1.md`（7 入口）+ WORKFLOW_INDEX §1.6 一句（本票僅該增量）·
  上游三 doc 反向 xref · 非 W5-T5 · 非 Phase%。
- followup_suggestions:
  - Orchestrator 讀 D_REPORT → 標 `overall_status: done`（Scribe 不改 STATE）
  - Downstream：`W5-T5` 全 Wave rollup · Wave 2 G-1–G-5 resume runtime · W5-T3 observer 只消費 TRACE 欄位
  - Commit 歸因：勿把 `WORKFLOW_INDEX.md` 工作樹其他未提交 diff 算進本票（C 非阻塞建議）
