# TICKET STATE · FP-G2-T1-index-job-scheduler-hook-v1 · Index job hook skeleton



> Full-Phase G2 · P2 · **build** · skeleton CLI（dry-run）· 不破壞 seed INV  

> 對齊：`W-MASTER-full-phase-plan_state.md#G2` · `LANE-A` A-G2-T1  

> 母票：`FP-G2-index-job_state.md`



---



## FRAME

<!-- Orchestrator 填：2026-07-10 凍結 · 待下輪 Implementer -->



- Goal: 補「规模化排程」缺口的 **最小可驗收增量**：index job 觸發 hook **設計 doc** + **skeleton CLI**（預設 dry-run／plan-only），回傳穩定 `dict`，**不**寫生產 index、**不**破壞 ingest_verify seed INV。

- Scope:

  - MUST：`docs/phase2-index-job-hook-v1.md` — 觸發模型、解阻條件（infra/PM）、與 WA-T1／gap-audit 交叉引用、MVP vs stretch

  - MUST：`scripts/run_index_job_hook_v1.py` — `--dry-run`（預設）· `--format json` · 回傳 `ok`/`message`/`planned_jobs[]`（或等價鍵）

  - MUST：`tests/test_index_job_hook_v1.py` — ≥3 斷言 skeleton 行為（dry-run · 不觸發寫入 · dict 形狀）

  - MUST：本票 B_REPORT／驗證命令

  - MAY：`WORKFLOW_INDEX.md` §1.24 一句交叉引用本 hook doc

- NonScope:

  - 生產 cron／scheduler 部署 · 全庫 re-ingest · 重寫 `core/repo_index_job`／`data_pipeline`

  - GraphRAG 全量 · E2E LLM synthesis · smoke_corpus 擴檔（T5）

  - 宣稱 P2 closure／Phase% 上調 · 改 `.github/workflows/**`

  - 暗部禁區 · 金鑰 · human-blocked 線

- AllowedPaths:

  - `docs/phase2-index-job-hook-v1.md`

  - `scripts/run_index_job_hook_v1.py`

  - `tests/test_index_job_hook_v1.py`

  - `04_Workflows/WORKFLOW_INDEX.md`（僅 §1.24 一句 MAY）

  - `04_Workflows/tickets/FP-G2-T1-index-job-scheduler-hook-v1_state.md`

- BlockedPaths:

  - `core/**` · 暗部 · `.github/workflows/**` · Dashboard Phase% 數字

  - 治理母本 · `00_Agent_Work_Progress.md`（僅 Scribe 末尾）· 憲法 §7 類型

  - 其他票 FRAME／STATE（除本票）

- Dependencies:

  - 上游：WA-T1 · 建議讀 `FP-G2-T2` gap-audit（∥ 可並行；若 T2 已 done 則引用）

  - 下游：T5（串行本票策略）· 未来规模化排程 infra 票

- AcceptanceCriteria:

  - AC-1：`python scripts/run_index_job_hook_v1.py --dry-run --format json` → 穩定 JSON／dict（含 `ok` · `message` · `planned_jobs`）

  - AC-2：預設 dry-run · 不寫生產 index／不改 seed corpus（B_REPORT 明示）

  - AC-3：`python -m unittest tests.test_index_job_hook_v1 -v` ≥3 tests PASS

  - AC-4：doc 列解阻條件（infra／PM）與 non_claims（skeleton ≠ 已排程生產 job）

  - AC-5：路徑經相對／地圖慣例 · 無硬編本機絕對路徑



### Wave Master 擴展



- wave_id: null

- group_id: G2

- lifecycle_phase: B

- phase_targets: [P2]

- estimated_cycles: 1

- mvp_allowed: true

- human_only_prereqs: []

- infra_only_prereqs: ["生产 cron／规模化排程部署（本票不交付）"]

- security_only_prereqs: []

- dependencies_detail:

  - upstream_tickets: [WA-T1-phase2-knowledge-indexing-contract-v1, FP-G2-T2-phase2-index-contract-gap-audit-v1]

  - downstream_waves: [FP-G2-T5-smoke-corpus-expansion-v1]

  - blocks_if_missing: []

- risks:

  - id: RSK-G2-T1-01

    description: skeleton 被標 complete／生產就緒

    likelihood: M

    impact: H

    mitigation: AC 分 MVP vs stretch · non_claims · Reviewer 檢查

    residual: accept

  - id: RSK-G2-T1-02

    description: 誤改 core ingest 破壞 INV

    likelihood: L

    impact: H

    mitigation: BlockedPaths 禁 core · dry-run only

    residual: accept

- observability:

  - verify_commands:

    - "python scripts/run_index_job_hook_v1.py --dry-run --format json"

    - "python -m unittest tests.test_index_job_hook_v1 -v"

  - evidence_artifacts:

    - docs/phase2-index-job-hook-v1.md

    - scripts/run_index_job_hook_v1.py

    - tests/test_index_job_hook_v1.py

  - trace_fields: []

  - success_signals: [dry-run ok · unittest PASS · doc non_claims]

  - failure_signals: [寫入生產 index · 改 core · 無 dict]

- non_claims:

  - skeleton CLI ≠ 生产 index job 已排程

  - dry-run planned_jobs ≠ 已執行 ingest

  - 本票 ≠ P2 65%→closure · ≠ GraphRAG 主路

- ticket_class: build

- evidence_tier: L-local

- parallel_ok: true



---



## STATE



- overall_status: done

- lifecycle_phase: O

- current_owner: orchestrator

- next_action: 無 · overall_status done · 下游 T3 arrange／T4 arrange／T5 仍 blocked

- last_updated: 2026-07-10 · O/B/C/D 同輪收口

- status_by_role:

  - orchestrator: done

  - implementer: done

  - reviewer: done

  - scribe: done



---



## B_REPORT



- changed_files:

  - `docs/phase2-index-job-hook-v1.md`（新建）

  - `scripts/run_index_job_hook_v1.py`（新建）

  - `tests/test_index_job_hook_v1.py`（新建）

  - `04_Workflows/WORKFLOW_INDEX.md`（§1.24 一句 MAY）

- artifacts:

  - hook 設計 doc · dry-run skeleton CLI · 5 unittest

- verification:

  - `python scripts/run_index_job_hook_v1.py --dry-run --format json` → `ok=true` · `mode=dry_run` · `planned_jobs`×2 · `writes_index=false`

  - `python -m unittest tests.test_index_job_hook_v1 -v` → Ran 5 tests · OK

- behavior_notes:

  - 預設 dry-run／plan-only；`--execute` 回 `ok=false`／`execute_blocked`（不寫 index）

  - 未改 `core/**` · 未觸 seed corpus · 未部署 cron

  - skeleton 誠實：`skeleton=true` · non_claims 於 doc §0

- deferred_items:

  - 生產 cron／scheduler 部署（infra）

  - core ingest 接線（另票）

  - T5 smoke_corpus 擴檔（串行本票 + PM）

  - T3 E2E FRAME · T4 graphrag 状态机



---



## C_REPORT



- conclusion: accepted

- blocking_issues: 無

- checks_summary:

  - AC-1 PASS：dry-run JSON 含 `ok`／`message`／`planned_jobs`

  - AC-2 PASS：`writes_index=false` · unittest 確認無 seed 寫入側效

  - AC-3 PASS：5 tests OK（≥3）

  - AC-4 PASS：doc §0 non_claims · §3 解阻（infra／PM）

  - AC-5 PASS：相對路徑／`DOC_REL` · 無本機絕對路徑硬編

  - 邊界：未碰 `core/**` · workflows · Phase% · human-blocked

- risk_level: low

- suggestions:

  - 下游勿把 skeleton 標生產就緒；T5 仍須 PM 策略



---



## D_REPORT



- docs_updates:

  - `docs/phase2-index-job-hook-v1.md`（本票新建）

  - `04_Workflows/WORKFLOW_INDEX.md` §1.24 交叉引用

  - Progress 末尾 append（本輪）

- progress_entry: 2026-07-10 · FP-G2-T1 done · skeleton dry-run CLI + doc · Reviewer accepted · ≠ 生產 cron

- followup_suggestions:

  - arrange `FP-G2-T3`（E2E FRAME）或 `FP-G2-T4`（graphrag 状态机 doc）

  - T5 仍 blocked on T1（本票已 done）+ PM verify strategy

  - 勿無 FRAME 擴 smoke_corpus · 勿宣稱 P2 closure


