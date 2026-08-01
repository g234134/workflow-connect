# W1-P75-INTAKE-CLI-MVP-v1 — Intake CLI Completeness Doc + Minimal Upstream Wiring

> handoff 摘要檔 · Wave 1 · P7.5 upstream · doc + 最小 `--run-p75-gate` 接線  
> **Schema SSOT**：`docs/ticket-schema-master-v1.md` · `W5-T2` · playbook §3.2

---

## FRAME
<!-- Orchestrator 2026-07-09 凍結 · 施工前勿改 -->

- Goal: 補 intake CLI **完整度**缺口：人類接案（`new_cleaning_case`）與 P7.5 gate（`run_intake_gate_cli` / layer merge）之間的 **canonical 上游路徑** doc + 最小可驗收接線，使 MP-SMOKE step 1 與人工接案敘事一致。
- Scope:
  - **MUST**：`docs/p75-intake-cli-upstream-mvp-v1.md` — case 建立 → gate 的 ≥3 步 canonical 命令（含 flags）· 與 `check_case_eligibility` / P75-G2 outbox 邊界表 · W-MVP-W3 邊界 · non-claims
  - **MUST**：最小 runtime MVP — `scripts/new_cleaning_case.py` 的 `--run-p75-gate`（或等價）呼叫 P75 `evaluate_intake_gate` **preview**，stdout 打印 `gate_status`（=`decision`）+ `reason_codes`（**不**強制寫 eligibility_result.json · **不**接 prod dispatch · **不**寫 outbox）
  - **MUST**：對應 unittest（`tests/test_new_cleaning_case.py` 至少 1 條 `--run-p75-gate` 路徑）可本地綠
  - **MAY**：`04_Workflows/WORKFLOW_INDEX.md` 在 P75-G2 區塊加 **一句** P7.5 intake upstream 入口（指向本 doc；可併 `W1-P75-UPSTREAM-ENTRY-INDEX-v1`）
  - **MAY**：cross-ref 既有 `docs/tabular-intake-tool-path-v1.md` · `W-MVP-W3-INTAKE-CLI` · `P75-G2`
- NonScope:
  - **不**建 Local UI · **不**改 `dispatch_executor` · **不**觸發清洗／bundle
  - **不**宣稱 intake CLI 已覆蓋 W4 dispatch／Checkpoint A 全鏈
  - **不**做 notify transport（P75-G4／Wave 2–3）
  - **不**改 Phase% · Dashboard · `W-MASTER-wave-plan_state.md`
  - **不**維護 Master CP 模板／commands（Wave 5 SSOT）
  - **不**重做 P75-G2 gate layer／outbox runtime（只消費 preview）
- AllowedPaths:
  - `docs/p75-intake-cli-upstream-mvp-v1.md`
  - `scripts/new_cleaning_case.py`
  - `tests/test_new_cleaning_case.py`
  - `04_Workflows/WORKFLOW_INDEX.md`（僅一句 P7.5 intake upstream 入口 · MAY）
  - `04_Workflows/tickets/W1-P75-INTAKE-CLI-MVP-v1_state.md`（僅 **B_REPORT** 區塊 · Implementer）
- BlockedPaths:
  - 憲法 §7 禁區類型（env／venv／runtime checkpoints／暗部破壞性維運等）— 引用 `HARNESS_CONSTITUTION.md` §7
  - `ENGINEERING_CONTRACT.md` · `HARNESS_CONSTITUTION.md` · `AGENTS.md` · `.cursor/rules/**`
  - `routing/intake_gate_layer_v1.py` · `scripts/run_intake_gate_cli.py` · `dispatch_executor.py`（本票不改 gate／dispatch 本體）
  - `.github/workflows/**` · `core/**`
  - `docs/WAVE_PROGRESS_DASHBOARD.md` · `04_Workflows/00_Agent_Work_Progress.md` · `project_status/master_status.md`（Scribe 末尾追加除外）
  - 本票 **FRAME／STATE／C_REPORT／D_REPORT**（Implementer 禁改）
  - 他人票 `*_state.md` FRAME／STATE
- Dependencies:
  - 只讀：`W-MVP-W3-INTAKE-CLI_state.md` · `P75-G2-intake-gate-layer-and-outbox-record-v1_state.md`
  - 只讀：`scripts/run_intake_gate_cli.py` · `docs/tabular-intake-tool-path-v1.md`
  - downstream：`W1-P75-TRACE-UPSTREAM-v1` · MP-SMOKE step 1 · `W1-P75-UPSTREAM-ENTRY-INDEX-v1`
  - **無** human／infra／security 前置（`human_only_prereqs: []`）
- AcceptanceCriteria:
  - AC-1：doc 列 case 建立 → gate CLI 的 **≥3 步** canonical 命令（含 flags）
  - AC-2：最小 runtime MVP 可本地跑通 demo／sample 路徑（unittest 或 B_REPORT 命令輸出含 `gate_status`／`decision` + `reason_codes`）
  - AC-3：doc 明示與 `W-MVP-W3` 邊界（何時用 `new_cleaning_case` vs 僅 gate CLI；`--run-gate` vs `--run-p75-gate`）
  - AC-4：non-claims 含「upstream MVP ≠ E2E delivery ≠ prod intake API」
  - AC-5：`python -m unittest tests.test_new_cleaning_case -v` 全綠（含 `--run-p75-gate` 測）

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
  - upstream_tickets: [W-MVP-W3-INTAKE-CLI, P75-G2-intake-gate-layer-and-outbox-record-v1]
  - downstream_waves: [W1-P75-TRACE-UPSTREAM-v1, W1-P75-UPSTREAM-ENTRY-INDEX-v1, MP-SMOKE]
  - blocks_if_missing: []
- risks:
  - id: RSK-W1-P75-CLI-01
    description: 與 W-MVP-W3 票 scope 衝突
    likelihood: low
    impact: medium
    mitigation: 本票只補 P7.5 gate 上游 · NonScope 明示
    residual: accept
  - id: RSK-W1-P75-CLI-02
    description: gate 與 P2 eligibility 雙入口混淆
    likelihood: medium
    impact: medium
    mitigation: doc 邊界表 + 引用 tabular-intake-tool-path
    residual: accept
- observability:
  - verify_commands:
    - `python scripts/new_cleaning_case.py --help`
    - `python -m unittest tests.test_new_cleaning_case -v`
    - `rg "run_intake_gate_cli|new_cleaning_case|run-p75-gate" docs/p75-intake-cli-upstream-mvp-v1.md`
  - evidence_artifacts:
    - `docs/p75-intake-cli-upstream-mvp-v1.md`
    - B_REPORT CLI／unittest 輸出摘要
  - trace_fields: [case_dir, gate_status, reason_codes, intake.gate_decision]
  - success_signals:
    - Reviewer 無口述即可複製上游接案→gate 命令序列
    - unittest 含 `--run-p75-gate` 且綠
  - failure_signals:
    - 宣稱已接 W4 dispatch
    - 硬編磁碟絕對路徑
    - `--run-p75-gate` 寫 outbox／eligibility_result.json
- non_claims: upstream MVP · 非 UI · 非 dispatch · 非 notify transport · 非 E2E delivery · 非 prod intake API · 非 Phase% 上调
- ticket_class: build
- evidence_tier: L-local
- parallel_ok: true

---

## STATE

- overall_status: done
- lifecycle_phase: closed
- current_owner: orchestrator
- next_action: >-
  本票已關。Downstream 可開：`W1-P75-TRACE-UPSTREAM-v1` ·
  `W1-P75-UPSTREAM-ENTRY-INDEX-v1` · MP-SMOKE step 1（引用本 doc）。
- last_updated: 2026-07-09 · Orchestrator（Scribe D_REPORT + Progress 收口 → done）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- orch_notes: >-
  收口核對：C=`accepted`（AC-1–AC-5 全 PASS · risk=low · blocking 無）·
  D_REPORT 已寫 · Progress 末尾「2026-07-09 · W1-P75-INTAKE-CLI-MVP-v1 · Scribe 收口」已存在。
  標 overall_status=done。未改 B/C/D_REPORT／FRAME／code。

---

## B_REPORT

- changed_files:
  - `04_Workflows/WORKFLOW_INDEX.md`（MAY：P75-G2 區塊加一句 P7.5 intake upstream 入口）
  - 其餘 AllowedPaths（doc／`new_cleaning_case.py`／`test_new_cleaning_case.py`）本輪**無 diff** — 開票時已落地，AC 盤點通過
- artifacts:
  - `docs/p75-intake-cli-upstream-mvp-v1.md`（既有：≥3 步 canonical · 邊界表 · W-MVP-W3 · non-claims）
  - `scripts/new_cleaning_case.py`（既有：`--run-p75-gate` / `_run_p75_gate_preview` · stdout `gate_status`+`reason_codes`）
  - `tests/test_new_cleaning_case.py`（既有：`test_cli_with_run_p75_gate`）
  - WORKFLOW_INDEX P75-G2 一句指向 `docs/p75-intake-cli-upstream-mvp-v1.md`
- verification: # evidence_tier=L-local
  - `python scripts/new_cleaning_case.py --help` → exit 0；可見 `--run-gate | --run-p75-gate` 與 `--p75-task-type`
  - `python -m unittest tests.test_new_cleaning_case -v` → Ran 3 tests · OK（含 `test_cli_with_run_p75_gate`）
  - `rg "run_intake_gate_cli|new_cleaning_case|run-p75-gate" docs/p75-intake-cli-upstream-mvp-v1.md` → exit 0；命中 canonical 命令與邊界表
- behavior_notes:
  - AC-1–AC-5 自檢：既有 doc+runtime+unittest 已滿足；本輪僅補 MAY 索引一句
  - `--run-p75-gate` = `evaluate_intake_gate(..., mode="preview")`；不寫 outbox／eligibility_result.json；與 `--run-gate`（P2 eligibility）互斥
  - 未改 FRAME／STATE／C_REPORT／D_REPORT；未碰 BlockedPaths
- deferred_items: 無

---

## C_REPORT

- conclusion: accepted
- reviewer_date: 2026-07-09
- blocking_issues: 無
- checks_summary: |
    Reviewer 獨立重跑（2026-07-09 · evidence_tier=L-local；不盲信既有草稿）。
    已讀：FRAME／STATE／B_REPORT · doc · `new_cleaning_case.py`（`_run_p75_gate_preview`）·
    `test_cli_with_run_p75_gate` · WORKFLOW_INDEX P75-G2 L229 一句。
    AC-1 PASS：doc §Canonical 三步（create · `--run-p75-gate` · `run_intake_gate_cli`）均含 flags。
    AC-2 PASS：`_run_p75_gate_preview` 固定 `mode="preview"`；stdout `gate_status`(=decision)+`reason_codes`；
    help 明示 no outbox；與 `--run-gate` 互斥組。
    AC-3 PASS：邊界表 + W-MVP-W3 節明示 `--run-gate` vs `--run-p75-gate` 與何時用何 CLI。
    AC-4 PASS：Non-claims 含 upstream MVP ≠ E2E delivery ≠ prod intake API（另 ≠ dispatch／outbox／notify）。
    AC-5 PASS：獨立 `python -m unittest tests.test_new_cleaning_case -v` → Ran 3 · OK（含 p75）。
    Scope：AllowedPaths 內；未改 gate／dispatch 本體；non_claims／NonScope 未越界。
    Rule 11：三條 verify_commands 本輪 exit 0 可重跑。
    獨立 verify：
    - `python scripts/new_cleaning_case.py --help` → exit 0；`--run-gate | --run-p75-gate` · `--p75-task-type`
    - `python -m unittest tests.test_new_cleaning_case -v` → 3/3 OK
    - `rg "run_intake_gate_cli|new_cleaning_case|run-p75-gate" docs/p75-intake-cli-upstream-mvp-v1.md` → exit 0
- risk_level: low
- suggestions: |
    非阻塞：`WORKFLOW_INDEX.md` 工作樹可能另有他票 diff；commit 時只歸因本票 MAY 那一行。
    非阻塞：doc step 1／2 部分重疊（step 2 已含 create）；可接受，因 step 3 補齊 full gate CLI。

---

## D_REPORT

- scribe_date: 2026-07-09
- verdict_echo: Reviewer `accepted` · risk=low · blocking 無 · AC-1–AC-5 獨立重跑全 PASS
- docs_updates:
  - `docs/p75-intake-cli-upstream-mvp-v1.md` — 本票 SSOT（≥3 步 canonical · 邊界表 · W-MVP-W3 · non-claims）；本輪無正文改動
  - `04_Workflows/WORKFLOW_INDEX.md` — P75-G2 區塊已有一句 P7.5 intake upstream 入口（Implementer MAY）；本輪不重寫
  - `docs/tabular-intake-tool-path-v1.md` — §4 補反向交叉引用至本票 SSOT（術語／路徑對齊）
- progress_entry: >-
  見 `04_Workflows/00_Agent_Work_Progress.md` 末尾 —
  **2026-07-09 · W1-P75-INTAKE-CLI-MVP-v1 · Scribe 收口**
- followup_suggestions:
  - Orchestrator：讀本 D_REPORT → `overall_status: done` · `scribe: done`
  - Downstream：`W1-P75-TRACE-UPSTREAM-v1` · `W1-P75-UPSTREAM-ENTRY-INDEX-v1` · MP-SMOKE step 1 可引用本 doc
  - Commit 時僅歸因本票 MAY 之 WORKFLOW_INDEX 那一行（C_REPORT 非阻塞建議）
- non_claims_echo: >-
  upstream MVP ≠ E2E delivery ≠ W4 dispatch ≠ prod intake API ≠ outbox ≠ notify ·
  **非** Phase% 上調 · **非** Dashboard／W-MASTER 變更
