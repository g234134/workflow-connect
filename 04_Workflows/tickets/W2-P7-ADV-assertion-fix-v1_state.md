# TICKET STATE · W2-P7-ADV-assertion-fix-v1 · P7 advisory CI AssertionError 修復

> handoff 摘要檔；跨 chat 交棒以本檔為準。  
> **依據**：二次 GA `29159219044` · 51 ran / **11 fail** · 資產已齊（非缺檔）· 尚書省「另票」授權  
> **Schema**：`docs/ticket-schema-master-v1.md`

---

## FRAME

- Goal: 修復 P7 advisory CI（`p7-notification-smoke.yml`）遠端 unittest **11 條 AssertionError**，使 job 達 functional pass（仍維持 advisory · non-gate）。
- Scope:
  - 根因定位：job-level env（`GOV_NOTIFICATION_*_ENABLED=1`）是否污染「gate off」測試；或 production code／test 契約漂移
  - 最小修復：workflow env 隔離 **或** 測試／runtime 對齊（擇一最小可驗收路徑）
  - 本機重跑三模組全綠後，建議 Ops 再 `workflow_dispatch` 驗證（本票可不代跑 GA）
- NonScope:
  - **不**升格 required CI／branch protection
  - **不**解阻 Round-2 staging（五頂／H4 DEFER 維持）
  - **不**改 Phase% · DarkOps core · 憲法／合約母本
  - **不**修 P6／P9（已 PASS）
- AllowedPaths:
  - `.github/workflows/p7-notification-smoke.yml`（僅 env／step 隔離 · 不改 continue-on-error／non-gate）
  - `tests/test_orchestrator_dispatch_full_smoke_v1.py`
  - `tests/test_orchestrator_notifications.py`
  - `tests/test_notification_webhook_dispatch_v1.py`
  - `delivery/notification_*.py`（僅若證實 runtime bug；優先不擴）
  - `scripts/run_agent_standard_case_experiment.py`（僅若測試依賴）
  - `04_Workflows/tickets/W2-P7-ADV-assertion-fix-v1_state.md`（B_REPORT）
- BlockedPaths:
  - 憲法 §7 禁區類型（env 金鑰原文、venv、runtime/checkpoints）
  - `HARNESS_CONSTITUTION.md` · `ENGINEERING_CONTRACT.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md` Phase%
  - Round-2／staging／prod webhook 路徑
  - 他人 core／暗部根（無授權）
  - 其他票 FRAME／STATE（本票 STATE 僅 Orchestrator）
- Dependencies:
  - upstream：資產 landing（tests 已上遠端）· GA run `29159219044`
  - 參考：`docs/P7_ADVISORY_CI_INDEX.md` · `W2-P7-advisory-ci-ssot-index-v1`
- AcceptanceCriteria:
  - **AC-1**: 本機 `python -m unittest tests.test_orchestrator_dispatch_full_smoke_v1 tests.test_orchestrator_notifications tests.test_notification_webhook_dispatch_v1 -v` → **0 failures**（在模擬 CI job env 下亦須通過，或明確改 workflow 使 step env 不污染）
  - **AC-2**: 若改 workflow：仍 `continue-on-error: true` · sandbox localhost mock · **禁止** staging/prod tier
  - **AC-3**: B_REPORT 列 changed_files + 失敗根因一句 + 驗證命令輸出語意
  - **AC-4**: non_claims：修綠 ≠ Round-2 GO ≠ required CI ≠ Phase%
  - **AC-5**（MAY）: Ops 重跑 advisory 得 job success · 回填 run_url（可 Scribe）

### Wave Master 擴展

- wave_id: W2
- group_id: G7
- lifecycle_phase: O
- phase_targets: [P7]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [W2-P7-advisory-ci-ssot-index-v1, WD-P7-T3-orchestrator-dispatch-full-smoke-v1]
  - downstream_waves: []
  - blocks_if_missing: []
- risks:
  - id: R1 · description: job env 與「gate off」測試衝突 · likelihood: high · impact: medium · mitigation: 測前 unset／step-scoped env · residual: low
- observability:
  - verify_commands:
    - `python -m unittest tests.test_orchestrator_dispatch_full_smoke_v1 tests.test_orchestrator_notifications tests.test_notification_webhook_dispatch_v1 -v`
  - evidence_artifacts: [p7_notification_smoke.log · GA run_url]
  - success_signals: [failures=0 · job success]
  - failure_signals: [AssertionError · failures>0]
- non_claims:
  - advisory 綠 ≠ Round-2 GO
  - ≠ required CI / merge gate
  - ≠ Phase% uplift
  - ≠ staging/prod webhook
- ticket_class: build
- evidence_tier: CI-advisory
- parallel_ok: true

### Evidence seed（二次 GA）

```yaml
ga_run:
  run_id: "29159219044"
  run_url: "https://github.com/g234134/workflow-connect/actions/runs/29159219044"
  ran: 51
  failures: 11
  failure_class: AssertionError
  note: "assets present · not ModuleNotFound · job fail under continue-on-error"
```

**已知 FAIL 簇**（orchestrator／notifications 為主；webhook DLQ／HMAC／retry 多數 ok）：

- `test_orchestrator_dispatch_full_smoke_v1`: AC-2/3/4/5 多條（env gate / webhook fail-open）
- `test_orchestrator_notifications`: enable／disable／CLI／env gate／fail-open

---

## STATE

- overall_status: done
- lifecycle_phase: O
- current_owner: none
- next_action: 無（AC-5 已回填 · 遠端 job PASS）
- last_updated: 2026-07-12 · Ops+Scribe AC-5 回填
- ops_checklist: 無
- diagnosis_seed: >-
    根因：遠端缺 cleaning CLI → exit 2 誤讀；次因 job-level env。
    修復後遠端 `29171873118` job PASS · Ran 51 · OK。
- status_by_role:
  - orchestrator: done — FRAME 凍結 · 關票 done
  - implementer: done — 三檔已 commit `3dd2a9c68` + push
  - reviewer: done — accepted（AC-5 遠端 PASS 關閉 gap）
  - scribe: done — AC-5 run_url 回填

---

## B_REPORT

- changed_files:
  - `scripts/run_agent_standard_case_experiment.py` — 缺 `notebooks/csv_cleaning/clean_phase_demo.py`（或 `GOV_P7_SMOKE_STUB_TOOLS=1`）時 stub `execute_tabular_tool`；`additional_demo` clean 補 `--profile-id phase_demo_v1`
  - `.github/workflows/p7-notification-smoke.yml` — 移除 job-level `GOV_NOTIFICATION_*`（避免污染 gate-off／disable 測試）；維持 `continue-on-error: true` · sandbox localhost mock · 非 required
  - `tests/test_orchestrator_notifications.py` — disable／CLI-only 測試顯式清 `GOV_NOTIFICATION_*`
- artifacts: 無
- verification:
  - `python -m unittest tests.test_orchestrator_dispatch_full_smoke_v1 tests.test_orchestrator_notifications tests.test_notification_webhook_dispatch_v1 -v` → **Ran 51 · OK**（本機實 CLI）
  - 同上 + `GOV_P7_SMOKE_STUB_TOOLS=1` + 模擬 CI job-level `GOV_NOTIFICATION_*=1` → **Ran 51 · OK**
- behavior_notes:
  - **失敗根因（一句）**：CI 缺 cleaning／eligibility／bundle CLI（`clean_phase_demo.py` 等未入遠端）；Python「找不到檔」exit **2**，被誤讀成 gate AssertionError——**非**單純 job-env 污染（env 為次因，已隔離）。
  - stub ≠ 宣稱真實 cleaning GA pass；僅讓 P7 notification 鏈在缺資產時可跑通 advisory smoke。
  - deferred 建議（需 O 擴 AllowedPaths／另票）：force-add `notebooks/csv_cleaning/**` + `scripts/check_case_eligibility.py` + `scripts/build_case_delivery_bundle.py` 後可關 stub 默認路徑。
- deferred_items:
  - 落地真實 cleaning CLI 資產至遠端（本票 AllowedPaths 未含 notebooks／缺檔 scripts）
- non_claims: 修綠 ≠ Round-2 GO ≠ required CI ≠ Phase% ≠ staging/prod webhook

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 无
- checks_summary: |
    AC-1–4 PASS（本機）；AC-5 PASS：遠端 run_id=29171873118 · job success · Ran 51 · OK
    commit=3dd2a9c68 · URL https://github.com/g234134/workflow-connect/actions/runs/29171873118
- risk_level: low
- gaps: 無（AC-5 已關）
- suggestions: >-
    勿把 advisory job PASS 當 Round-2 GO 或 required CI 升格。

---

## D_REPORT

- docs_updated:
  - `docs/P7_ADVISORY_CI_INDEX.md` — AC-5 run_url／job PASS 回填
  - `04_Workflows/command_queue/QUEUE.yaml` — P7-advisory 解阻；priority_next 改 P6
  - `04_Workflows/00_Agent_Work_Progress.md` — 末尾 append
- progress_appended: true
- notes: >-
    wave_id=W2 · overall_status=done · AC-5 PASS run_id=29171873118 ·
    ≠ Round-2 GO ≠ required CI ≠ Phase% ≠ stub=真實 cleaning GA
