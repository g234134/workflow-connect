# 90_run_queue — 企業化補強層任務隊列

> **權威**：任務狀態與維度對賬以本檔為準；總藍圖見同目錄 `00_master_plan.md`（若尚未建立，以本檔 **done** 區塊為 2026-05 戰役對賬基線）。  
> **更新規則**：員工 chat 完工後由主代理或收兵 chat **僅改狀態與 `result_summary`**，不刪除歷史 done 行。  
> **最後對賬**：2026-05-24（Wave 3 K-2 合流治理 Chat C → rollout 策略落盘）

---

## 欄位說明

| 欄位 | 必填 | 說明 |
|------|------|------|
| `id` | 是 | 任務線代號（如 `K-1`、`I-bridge-v0`、`P+-eval-gate-v0`） |
| `lane` | 是 | H / I / J / K / L（編排線）；P+ 觀測評估歸 **P**（與 M/N/O 同層，本隊列用 `P+` id 前綴） |
| `title` | 是 | 一句話標題 |
| `status` | 是 | `todo` \| `in_progress` \| `done` \| `blocked` |
| `primary_dimensions` | 是 | 主提升維度，逗號分隔 `D1`–`D5` |
| `secondary_dimensions` | 否 | 次提升維度 |
| `expected_metric_shift` | 是 | 預期可觀測／治理指標變化（對賬用，非驗收命令） |
| `result_summary` | done 時建議填 | 不超過 2 行：核心交付物 + 最小驗收語意 |

**維度速查**：D1 可靠性 · D2 上下文 · D3 多代理編排 · D4 可觀測／評估 · D5 治理／邊界

---

## 任務條目模板（新增時複製）

```yaml
- id: <TASK_ID>
  lane: <H|I|J|K|L|P>
  title: <short title>
  status: todo
  primary_dimensions: [D1, D4]
  secondary_dimensions: [D2]
  expected_metric_shift: >
    <what should move on handoff_count / retry_count / trace_completeness / ...>
  result_summary: null
```

---

## Lane 全局視圖（2026-05-24）

| lane | 本輪 done | todo / in_progress | 主責維度 |
|------|-----------|-------------------|----------|
| **K** | K-1, K-2, K2-ask-shadow-merge | K2-rollout-governance（planned） | D1, D3, D4, D5 |
| **I** | I-bridge-v0, I-bridge-v1, I-bridge-v0-H-migrate, I-ask-skills-wire, J-answer-skill-wire, J-selector-context-governance | — | D1, D2, D4, D5 |
| **P+** | P+-eval-gate-v0, P+-eval-gate-export-ci, P+-eval-ci-wire | — | D1–D4 |
| **H** | H-context-entry-v0.1, I-bridge-v0-H-migrate, H-historical-migrate | — | D2, D5 |
| **J** | J-skills-seed-v0.1, I-ask-skills-wire, J-tool-executor-bridge, J-answer-skill-wire, J-selector-context-governance, J-tool-executor-llm-ask-skill | — | D1, D3, D4 |

---

## Done — 2026-05 企業化補強戰役（能力層躍遷）

> 本節 6 條為本輪從 **TODO 隊列結清** 的完成線；詳細實作見各模組 `*.md` / `tests/`，此處僅保留對賬維度。

| id | lane | title | status | primary_dimensions | secondary_dimensions | expected_metric_shift |
|----|------|-------|--------|--------------------|----------------------|------------------------|
| K-1 | K | minimal langgraph e2e (planner→executor→reviewer) | done | D1,D3,D4 | D2 | 為多代理圖建立可重試、可觀測、可 handoff 的最小閉環；讓 handoff_count / retry_count / trace_completeness 可在隔離環境驗證 |
| I-bridge-v0 | I | ask path minimal bridge | done | D1,D2,D4 | D5 | 在不改預設 /api/ask 行為下，為真實 ask 路徑增加 context / retry / trace 掛接能力 |
| I-bridge-v1 | I | /api/ask dev-only ibridge expose | done | D4,D5 | D1 | 通過 double gate 暴露 ibridge_record，方便 dev 級觀測與評估，而不污染生產契約 |
| P+-eval-gate-v0 | P+ | rule-based eval_gate | done | D1,D2,D3,D4 |  | 為每次 run 提供 pass/needs_review + tags，能自動標記 high_retry / context_heavy / many_handoffs / infra_risk / observability_gap |
| H-context-entry-v0.1 | H | unified context entry | done | D2,D5 | D1 | 規定新入口必須走 build_rooted_context，禁止手拼三層 context；強化上下文治理與邊界一致性 |
| J-skills-seed-v0.1 | J | metrics-aware skills seed | done | D1,D3,D4 | D5 | 為 skill 提供統一 run_metrics_aware_skill 外殼，自動掛 retry / metrics / external_call_count / span，降低後續新 skill 的治理與觀測成本 |

### Done — Wave 2（2026-05-23 結清）

| id | lane | title | status | primary_dimensions | secondary_dimensions | expected_metric_shift |
|----|------|-------|--------|--------------------|----------------------|------------------------|
| I-bridge-v0-H-migrate | H/I | migrate ibridge ask entry to H-line context_entry | done | D2,D4,D5 | D1 | opt-in ibridge ask 入口改走 build_rooted_context(mode="ask_pipeline")，collector metadata 對齊 H 線；預設 ask 仍 bypass，為 H-historical-migrate 預留空間 |
| I-ask-skills-wire | I/J | wire ask mainline to metrics-aware skills | done | D1,D3,D4 | D5 | ask 主線的 retrieve/answer 節點改走 metrics-aware skills；行為與回應結構不變，增加 retry_count / external_call_count 等可量測指標 |
| P+-eval-gate-export-ci | P+ | export eval_gate results & CI hook | done | D1,D2,D3,D4 |  | 建立 eval_export/v1 JSONL 導出 + eval_ci_check CLI，能對 ibridge_record 批次產生 pass/needs_review + tags 報表，預備接入 CI |
| P+-eval-ci-wire | P+ | wire eval_ci_check into CI pipeline | done | D1,D4 |  | shadow export → `shadow_ibridge_records.latest.jsonl`；nightly 0.60 + `infra_risk`；PR 0.72 |
| K-2 | K | deepen LangGraph orchestration (K-2 graph) | done | D1,D2,D3,D4 | D5 | 在 K-1 基礎上新增 build_k2_graph/run_k2_flow，圖內掛 H/J/P/P+，保留 K-1 並存，為後續 shadow/合流提供實驗圖 |

### Done — Wave 3 收斂（2026-05-25）

| id | lane | title | status | primary_dimensions | secondary_dimensions | expected_metric_shift |
|----|------|-------|--------|--------------------|----------------------|------------------------|
| H-historical-migrate | H | migrate default ask entry to H-line context_entry | done | D2,D5 |  | 預設 ask 經 `run_ask_with_hline_context`；生產 H-line bypass 清零；驗收+文檔封存（程式零 diff） |

### Done 條目明細（YAML · 對賬用）

```yaml
- id: K-1
  lane: K
  title: minimal langgraph e2e (planner→executor→reviewer)
  status: done
  primary_dimensions: [D1, D3, D4]
  secondary_dimensions: [D2]
  expected_metric_shift: >
    handoff_count / retry_count / trace_completeness 可先於隔離 e2e 圖驗證，
    為 ask 主線橋接提供安全樣板。
  result_summary: >
    core/langgraph_flow_k1.py 最小 StateGraph；K-1 已對齊 build_rooted_context。
    驗收：python -m unittest tests.test_langgraph_flow_k1 -v

- id: I-bridge-v0
  lane: I
  title: ask path minimal bridge
  status: done
  primary_dimensions: [D1, D2, D4]
  secondary_dimensions: [D5]
  expected_metric_shift: >
    預設關閉 ibridge 路徑；開啟時產出 ibridge_record（context/retry/trace 摘要）。
  result_summary: >
    gov_core_system/core/ask_pipeline_ibridge_v0.py；run_ask_flow(..., ibridge_v0=True)。
    驗收：暗部 venv unittest tests.test_ask_pipeline_ibridge_v0 -v

- id: I-bridge-v1
  lane: I
  title: /api/ask dev-only ibridge expose
  status: done
  primary_dimensions: [D4, D5]
  secondary_dimensions: [D1]
  expected_metric_shift: >
    僅 env+query 雙閘門同時滿足時 HTTP 響應含 ibridge_v0/ibridge_record；預設響應不變。
  result_summary: >
    gov_core_system/app_api.py 雙閘門透傳；tests/test_app_api_ibridge_expose.py 4/4。

- id: P+-eval-gate-v0
  lane: P+
  title: rule-based eval_gate
  status: done
  primary_dimensions: [D1, D2, D3, D4]
  secondary_dimensions: []
  expected_metric_shift: >
    evaluate_task_record → pass/needs_review + HIGH_RETRY 等 tags，供複查篩樣本。
  result_summary: >
    observability/eval_gate.py + eval_gate_rules.md；tests/test_eval_gate.py。

- id: H-context-entry-v0.1
  lane: H
  title: unified context entry
  status: done
  primary_dimensions: [D2, D5]
  secondary_dimensions: [D1]
  expected_metric_shift: >
    新入口統一 build_rooted_context；AGENTS/工程合約禁止手拼三層 context。
  result_summary: >
    core/context_entry.py + context/context_entry_contract.md；tests/test_context_entry.py。

- id: J-skills-seed-v0.1
  lane: J
  title: metrics-aware skills seed
  status: done
  primary_dimensions: [D1, D3, D4]
  secondary_dimensions: [D5]
  expected_metric_shift: >
    新 skill 經 run_metrics_aware_skill 自動記錄 retry/metrics/external_call/span。
  result_summary: >
    skills/skill_runner.py + example_skill_retrieve/pg_query；skills/skills_contract.md。

- id: I-bridge-v0-H-migrate
  lane: H/I
  title: migrate ibridge ask entry to H-line context_entry
  status: done
  primary_dimensions: [D2, D4, D5]
  secondary_dimensions: [D1]
  expected_metric_shift: >
    opt-in ibridge ask 入口改走 build_rooted_context(mode="ask_pipeline")；
    collector metadata 對齊 H 線；預設 ask 仍 bypass。
  result_summary: >
    ask_pipeline_ibridge_v0 改走 build_rooted_context；tests OK。
    驗收：暗部 venv unittest tests.test_ask_pipeline_ibridge_v0 -v

- id: I-ask-skills-wire
  lane: I/J
  title: wire ask mainline to metrics-aware skills
  status: done
  primary_dimensions: [D1, D3, D4]
  secondary_dimensions: [D5]
  expected_metric_shift: >
    retrieve/answer 經 metrics-aware skills；retry_count / external_call_count 可量測。
  result_summary: >
    ask 主線 retrieve/answer 掛 skill_runner；legacy 行為不變。
    驗收：暗部 venv 相關 unittest OK

- id: P+-eval-gate-export-ci
  lane: P+
  title: export eval_gate results & CI hook
  status: done
  primary_dimensions: [D1, D2, D3, D4]
  secondary_dimensions: []
  expected_metric_shift: >
    eval_export/v1 JSONL + eval_ci_check CLI；批次 pass/needs_review + tags 報表。
  result_summary: >
    observability/eval_exporter.py + eval_ci_check；JSONL schema + 21 項單測。
    驗收：python -m unittest tests.test_eval_exporter tests.test_eval_ci_check -v

- id: K-2
  lane: K
  title: deepen LangGraph orchestration (K-2 graph)
  status: done
  primary_dimensions: [D1, D2, D3, D4]
  secondary_dimensions: [D5]
  expected_metric_shift: >
    build_k2_graph/run_k2_flow 與 K-1 並存；圖內掛 H/J/P/P+，為 shadow/合流預備。
  result_summary: >
    core/langgraph_flow_k2.py；build_k2_graph() / run_k2_flow()。
    驗收：python -m unittest tests.test_langgraph_flow_k2 -v
```

### Done — Wave 3（2026-05-24 回答侧 skill 化 + selector 收敛 · Chat A/B/C 封存）

| id | lane | title | status | primary_dimensions | secondary_dimensions | expected_metric_shift |
|----|------|-------|--------|--------------------|----------------------|------------------------|
| J-answer-skill-wire | J/I | wire ask answer_node to metrics-aware skill_answer_for_ask | done | D1,D3,D4 | D5 | answer 侧与 retrieve 对称：`call_site` / `external_call_count` / `retry_count` / span `execute` 可量测；eval / ibridge_record 可消费 answer 步 metrics |
| J-selector-context-governance | J/I/H | ask RAG selector + 无 context / fallback 场景收敛 | done | D1,D2,D4 | D3 | selector 决策可观测（`ask_rag_selector` span / `selector_decision`）；S1–S3 场景行为可控；问候跳过 retrieve 仍走 answer skill |
| J-tool-executor-llm-ask-skill | J | wire tool_executor llm.ask to skill_answer_for_ask | done | D1,D3,D4 | D5 | executor 层 llm.ask 纳入 M-line metrics；eval 可按 call_site 分列 tool-layer 样本 |

```yaml
- id: J-answer-skill-wire
  lane: J/I
  title: wire ask answer_node to metrics-aware skill_answer_for_ask
  status: done
  primary_dimensions: [D1, D3, D4]
  secondary_dimensions: [D5]
  expected_metric_shift: >
    answer 侧 D1/D3/D4/D5 与 retrieve 对称；M-line record.external_call_count
    含 LLM 尝试；ibridge execute span 与 skill_answer_for_ask 事件对齐。
  result_summary: >
    Chat A：langgraph_flow.answer_node 经 ask_skills_wire.run_answer_via_skill →
    skill_answer_for_ask；retry_meta 含 call_site / external_call_count。
    验证：tests/test_skills_ask_wire.py（answer 单元）；
    gov_core_system/tests/test_ask_skills_wire_e2e.py（含 execute 步 metrics）。

- id: J-selector-context-governance
  lane: J/I/H
  title: ask RAG selector + no-context / fallback scenario governance
  status: done
  primary_dimensions: [D1, D2, D4]
  secondary_dimensions: [D3]
  expected_metric_shift: >
    selector 行为可控：S1 KB→RAG、S2 问候→skip retrieve、S3 retrieve 失败→direct_fallback；
    ibridge_v0.selector_decision 与 answer_mode / retrieve_fallback 标签可审计。
  result_summary: >
    Chat B：ask_rag_selector.decide_use_rag（ASK-R1–R6）+ selector_node 图路由；
    perform_direct_answer 无 context 直答；retrieve 失败带 retrieve_error_type。
    验证：tests/test_ask_selector_and_answer.py（单元 S1–S3 + 流程集成）；
    context_entry_contract §8 场景表对齐。

- id: J-tool-executor-llm-ask-skill
  lane: J
  title: wire tool_executor llm.ask to skill_answer_for_ask
  status: done
  primary_dimensions: [D1, D3, D4]
  secondary_dimensions: [D5]
  expected_metric_shift: >
    executor 层 llm.ask 与 LangGraph answer 步共用 skill_answer_for_ask；
    call_site=tool_executor.ask_pipeline.llm.ask；eval export 可分列 tool-layer 样本。
  result_summary: >
    tool_executor_skills_bridge._execute_llm_ask → run_answer_via_skill +
    perform_direct_answer（策略 A）；output_summary.answer + skill metrics。
    验证：tests/test_tool_executor_skills_bridge.py（llm.ask metrics + retry drill）；
    tests/test_tool_executor.py（test_ask_pipeline_llm_ask_dispatch）。
    合同：skills/skills_contract.md §11；observability/eval_pipeline.md §6.5。
```

---

## Backlog — todo / in_progress（Wave 3 余项）

| id | lane | title | status | primary_dimensions | secondary_dimensions | expected_metric_shift | 備註 |
|----|------|-------|--------|--------------------|----------------------|------------------------|------|
| J-tool-executor-bridge | J | unify tool_executor.rag.retrieve with metrics-aware skills | done | D1,D3,D4 |  | 消除工具呼叫雙軌，讓所有 retriever 路徑都能記錄 retry / external_call / trace metadata | 與 I-ask-skills-wire 互補 |
| K2-ask-shadow-merge | K/I | shadow-run K-2 graph against ask mainline & design merge hook | done | D1,D3,D4 |  | shadow 比對 + merge adapter + 策略文档；合流前回归基线 | Chat A/B done |
| K2-rollout-governance | K | K-2 deployment governance & prod rollout playbook | in_progress | D1,D4,D5 | D3 | **本地** Phase 1 演練：T+0 done + 7 日 spool/nightly；**Phase 2 批文草案 done**（暫不生效）；升格待 §6.3 出門 | Chat C + local T+0 |
| K2-phase1-shadow-hook | K/I | Phase 1 prod shadow async hook (app_api + spool) | done | D1,D4 |  | `/api/ask` subprocess shadow；`GOV_K2_PROD_SHADOW` 預設 off；nightly 改 spool 輸入 | HQ-GOV-K2-P1-SHADOW-20260525 |
| K2-phase1-prod-shadow | K | Phase 1 prod shadow — **local-only gate** (T+0 + local 7d rehearsal) | in_progress | D1,D4,D5 |  | **local-only gate**：T+0 done；7 日觀測；Phase 1 出门不含 remote | HQ-GOV-K2-P1-SHADOW-20260525 |
| K2-phase1-remote-rollout | K | Phase 1 remote prod cluster shadow deploy + parity (P1) | todo | D1,D4,D5 |  | P1 工單；**非** Phase 1 gate；不阻塞 Phase 2 canary；非 canary 流量 | WAVE-CORE-P0-PHASE1-ROLLOUT-DECISION |
| K2-phase1-remote-rollout-runbook | K | Phase 1 remote rollout runbook blueprint (docs only) | done | D1,D4,D5 |  | `docs/k2_phase1_remote_rollout_runbook.md`；blueprint 不代表已實施；實作见 `K2-phase1-remote-rollout` | — |

```yaml
# 上表之機器可讀副本（派工時優先讀此塊）
- id: P+-eval-ci-wire
  lane: P+
  title: wire eval_ci_check into CI pipeline
  status: done
  primary_dimensions: [D1, D4]
  secondary_dimensions: []
  expected_metric_shift: >
    CI 上游自動質控 signal；needs_review 比例與關鍵 tags 早期預警。
  result_summary: >
    ibridge_exporter --source shadow → shadow_ibridge_records.latest.jsonl；
    eval-gate-ci.yml 增 eval-shadow-nightly（0.60 + infra_risk，cron 06:00 UTC）；
    PR job 維持 0.72；dry-run 4 樣本 gate_result 全有值，eval_ci_check ok。

- id: J-tool-executor-bridge
  lane: J
  title: unify tool_executor.rag.retrieve with metrics-aware skills
  status: done
  primary_dimensions: [D1, D3, D4]
  secondary_dimensions: []
  expected_metric_shift: >
    消除 retriever 雙軌；統一 retry / external_call / trace metadata。
  result_summary: >
    ask_pipeline handler 經 tool_executor_skills_bridge + retrieve_core 重用 skill_retrieve_for_ask；
    test_tool_executor_skills_bridge 驗證 external_call_count / retry。

- id: H-historical-migrate
  lane: H
  title: migrate default ask entry to H-line context_entry
  status: done
  primary_dimensions: [D2, D5]
  secondary_dimensions: []
  expected_metric_shift: >
    預設 ask 路徑走 build_rooted_context；清零 H-line bypass。
  result_summary: >
    run_ask_flow 預設 run_ask_with_hline_context；盤點無第二注入點；
    unittest 全綠（context_entry 9 + selector 8 + 暗部 default_context/ibridge 7）；
    eval_ci_check shadow 4 樣本 ok（needs_review 25%）；context_entry_contract §8.0 已切換。

- id: K2-ask-shadow-merge
  lane: K/I
  title: shadow-run K-2 graph against ask mainline & design merge hook
  status: done
  primary_dimensions: [D1, D3, D4]
  secondary_dimensions: []
  expected_metric_shift: >
    shadow 比對 K-2 與 ask；merge_ask_and_k2 单点 adapter；降低合流回归风险。
  result_summary: >
    Chat A：k2_ask_shadow + behavior profile；Chat B：k2_merge_adapter + k2_merge_strategy.md；
    验证：tests/test_k2_merge_adapter tests/test_k2_ask_shadow。

- id: K2-rollout-governance
  lane: K
  title: K-2 deployment governance & prod rollout playbook
  status: in_progress
  primary_dimensions: [D1, D4, D5]
  secondary_dimensions: [D3]
  expected_metric_shift: >
    定义 shadow/canary 审批链、eval_ci_check 阈值、自动回退；Phase 1 T+0 已啟用，7 日觀測進行中。
  result_summary: >
    本地 Phase 1 演練（戰車根+gov_core_system）；T+0 done；7 日觀測中；
    **local-only gate**（2026-06-05 裁決）；遠端见 `K2-phase1-remote-rollout`（P1）；Phase 2 canary 批文草案 done（docs/drafts/HQ-GOV-K2-P2-CANARY-DRAFT.md，暫不生效）；升格待 §6.3 出門；T1–T10 實作票未開。

- id: K2-phase1-prod-shadow
  lane: K
  title: Phase 1 prod shadow — local-only gate (T+0 + local 7d rehearsal)
  status: in_progress
  primary_dimensions: [D1, D4, D5]
  secondary_dimensions: []
  expected_metric_shift: >
    **local-only gate**：本地 workstation K1/K2 parity；7 日 spool + nightly eval_ci_check；满足即 Phase 1 出门；remote 不纳入本票 gate。
  result_summary: >
    T+0 done：k2_phase1_prod_shadow.env 四鍵；本地 /api/ask→spool；export 三元組 OK。
    觀測窗 2026-05-26–06-02 UTC；每日 export+gate；裁決 2026-06-05：Phase 1 gate = local shadow only。

- id: K2-phase1-remote-rollout
  lane: K
  title: Phase 1 remote prod cluster shadow deploy + parity (P1)
  status: todo
  primary_dimensions: [D1, D4, D5]
  secondary_dimensions: []
  expected_metric_shift: >
    remote prod shadow 部署与 K1/K2 parity 验证；不切换 canary 流量（属 Phase 2）。
  result_summary: null

- id: K2-phase1-shadow-hook
  lane: K
  title: Phase 1 prod shadow async hook (app_api + spool)
  status: done
  primary_dimensions: [D1, D4]
  secondary_dimensions: []
  expected_metric_shift: >
    prod /api/ask 複製流量至 K-2 shadow spool；用戶仍 100% ask 主答案。
  result_summary: >
    gov_core app_api fire-and-forget subprocess；GOV_K2_PROD_SHADOW 預設 off；
    spool artifacts/eval/k2_shadow_spool.jsonl；nightly export 改讀 spool；unittest 27+3 OK。

- id: K2-phase1-remote-rollout-runbook
  lane: K
  title: Phase 1 remote rollout runbook blueprint (docs only)
  status: done
  primary_dimensions: [D1, D4, D5]
  secondary_dimensions: []
  expected_metric_shift: >
    遠端 Phase 1 shadow 可有示意 runbook；不啟動任何遠端施工。
  result_summary: >
    docs/k2_phase1_remote_rollout_runbook.md（Blueprint only；systemd/K8s/script pseudocode 內嵌）；
    不代表已在任何環境實施；遠端 rollout 實作須另票授權；未拆獨立 deploy 檔。
```

---

## Wave B — 知識層 bootstrap（2026-06-05）

```yaml
- id: WAVE-B-P1-REPO-INDEX-GOV-SCOPE-LIVE
  lane: P
  title: 治理關鍵 subtree 真實 index 回填（W2-1 閉環）
  status: done
  primary_dimensions: [D2, D4, D5]
  secondary_dimensions: []
  expected_metric_shift: >
    W2-1 pilot index 由 sample 升級為真實 repo_index_v1 bootstrap；案卷 kb_index_status=ready；IMP-AI-READY gate allow。
  result_summary: >
    workflow_v2/kb/wave_b_gov_scope.json + repo_index_bootstrap.py；index_status_W2-1.json（file_count=190，chunk_count=1204）；
    sync/gate/RAG smoke 全綠；tests.test_kb_index_bootstrap 10/10 OK；暗部替換留 Wave C。
```

```yaml
- id: WAVE-B-P2-EVAL-TRACE-CORRELATE
  lane: P
  title: eval_export 與 gov-trace-v2 關聯追查 CLI
  status: done
  primary_dimensions: [D4]
  secondary_dimensions: [D5]
  expected_metric_shift: >
    needs_review / infra_risk 列可一鍵 join trace 摘要；減少手動 copy-paste trace_id 到 trace_query。
  result_summary: >
    observability/eval_trace_correlate.py；join trace_id>task_id>session_id；tests.test_eval_trace_correlate；
    fixture sample_traces.jsonl 增 tr-3/t-infra；nightly artifact 留 Wave C。
```

---

## 決策備註（主代理留痕）

- **2026-05-23**：倉庫原先無 `90_run_queue.md`；本檔為**首版落盤**，直接將本輪 6 線標為 `done`（代碼與測試已存在於戰車根／暗部，見各 `result_summary`）。  
- **2026-05-23（Wave 2）**：`I-bridge-v0-H-migrate`、`I-ask-skills-wire`、`P+-eval-gate-export-ci`、`K-2` 自 Backlog 結清 → Done；Wave 3 Backlog 落盤 4 線。  
- **2026-05-24（Wave 3 · Chat A/B/C）**：`J-answer-skill-wire`、`J-selector-context-governance` 結清 → Done；问答 pipeline **问 + 检索 + 答** 三段均在 metrics-aware 治理骨架下。Chat C 仅文档／队列封存，无代码变更。  
- **2026-05-24（K-2 合流治理 · Chat C）**：`K2-ask-shadow-merge` 結清 → Done（Chat A/B 交付）；新增 `K2-rollout-governance` **planned**（策略文档 `docs/k2_deployment_governance.md` 已落盘，prod rollout 未启动）。  
- **2026-05-24（J-tool-executor-llm-ask-skill）**：executor 层 `llm.ask` 接 `skill_answer_for_ask` + `perform_direct_answer`；`skills_contract` §11、`eval_pipeline` §6.5、`00_master_plan` §4.9 已写回。  
- **2026-05-24（P+-eval-ci-wire）**：`P+-eval-ci-wire` 結清 → Done；shadow export + nightly `eval_ci_check`（0.60 + `infra_risk`）；PR 維持 0.72。  
- **2026-05-25（H-historical-migrate）**：預設 ask H 線 context **done**；程式零 diff；驗收+`context_entry_contract` §8.0／隊列／Progress 封存。
- **Wave 3 余项建议优先序**：`K2-rollout-governance` 7 日 Phase 1 觀測與週報（`K2-phase1-prod-shadow` **done**；`K2-phase1-shadow-hook` **done**）。
- **2026-05-25（K2-phase1-shadow-hook）**：Wave 1 async shadow hook 結清 → Done；Phase 仍 0 直至 T+0 開 `GOV_K2_PROD_SHADOW=1`。
- **2026-05-26（K2-phase1-prod-shadow · T+0）**：Phase 0→1 **本地** prod shadow 演練啟用；遠端 prod **不**自動 rollout（另票）。
- **範圍裁決（尚書省 · 2026-05-26）**：本地 Phase 1 演練；`K2-phase1-prod-shadow` T+0 done、7 日觀測 in_progress。
- **範圍裁決（尚書省 · 2026-06-05 · Option A）**：Phase 1 gate = local shadow only；remote → `K2-phase1-remote-rollout`（P1 · todo），不阻塞 Phase 2 canary。
- **2026-05-25（K2-phase1-remote-rollout-runbook）**：遠端 rollout **runbook 藍圖** 結清 → Done（`docs/k2_phase1_remote_rollout_runbook.md`）；實作票见 `K2-phase1-remote-rollout`。
- **2026-06-05（WAVE-CORE-P0-PHASE1-ROLLOUT-DECISION · Option A）**：Phase 1 gate = **local shadow only**（`K2-phase1-prod-shadow` 标 **local-only gate**）；remote prod rollout 另票 **`K2-phase1-remote-rollout`（P1 · todo）**，**不阻塞** Phase 2 canary；见 `00_master_plan.md` §4.8、`04_Workflows/00_Agent_Work_Progress.md` 战报。
- **2026-06-05（WAVE-B-P1-REPO-INDEX-GOV-SCOPE-LIVE）**：Wave B repo index bootstrap **done**；治理 subtree 真實 index → sync → gate → manifest RAG smoke 全鏈跑通；見 `workflow_v2/20_pilot/W3-B/W3-B_index_pipeline_runbook.md` 附錄 A。
