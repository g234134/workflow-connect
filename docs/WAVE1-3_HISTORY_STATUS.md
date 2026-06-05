# Wave 1–3 歷史狀態總結（官方導讀）

> **工單**：W1-3-HISTORY-SUMMARY-01  
> **成文日期**：2026-05-31  
> **性質**：doc-only 歷史封存；**不**改寫當年驗收結論、**不**定義現行必做重做項  
> **權威來源（只讀）**：`04_Workflows/00_Agent_Work_Progress.md` · `04_Workflows/project_status/master_status.md` · `gov_core_system/output/phase5-8_roadmap.md` · `gov_core_system/output/wave2_soak_validation_report.md` · `gov_core_system/output/wave3_retry_policy_report.md` · `workflow_v2/20_pilot/W2-3_*`（治理 gate 線）

---

## 1. Overview

**Wave 1**（2026-05-19 封板）聚焦 **Observability V2 · Monitoring + Alert v1**：建立 monitoring schema／ingest、六條 `/monitoring/*` API、dashboard 與 budget／alert evaluator 閉環，定調為 **dev-ready**，**非 production-ready**。

**Wave 2** 分兩條並行線：**（A）Structured Errors**（`structured_errors[]`／`error_schema_version=v1`、Gate 0 PASS）與 **（B）成本／usage 實測**（Chat C 寫回，**partial**，樣本極低）；另在 **workflow_v2** 落地 **W2-3 minimal governance gate**（ART-GOV-RISK + 只讀 gate 原型，**無 CI enforcement**）。

**Wave 3**（2026-05-19 文件封板）交付 **Error Handling & Auto-Recovery v1**：error taxonomy、Retry Policy v1（exponential backoff + jitter + transient 判斷，Gate 0 PASS）、enriched DLQ、`GET /monitoring/dlq`、窄域 auto-recovery；總判定 **dev-ready · partial**，預設 runtime 旗標 **off**，須 staging soak 後才可討論 production-ready。

以下三節依 Wave 展開；§5 說明在現行 **workflow_v2／Wave 4／Wave 5** 架構下，這些成果被視為何種 **reference level**（歷史已驗證設計，非現網預設能力）。

---

## 2. Wave 1 摘要

| 維度 | 內容 |
|------|------|
| **主題** | `gov_core_system` Observability V2 · Monitoring + Alert v1 |
| **封板日期** | 2026-05-19 |
| **封板等級** | **dev-ready**（開發／聯調／受控驗收環境基線凍結） |
| **未宣稱** | production-ready；gov_core 全系統 Completed；SLO／多環境閾值治理；Langfuse usage／成本全覆蓋 |

### 主要成果

- **Schema／Migration**：`005_monitoring.sql`、`006_monitoring_v1_align.sql`、`004_dlq.sql` 已套用；五表（`task_runs`、`step_runs`、`daily_cost_summary`、`budget_rules`、`alert_events`）齊備。
- **Ingest**：traces／steps 可同步（曾驗證 `traces_synced=2`、`steps_synced=14`）。
- **API／Dashboard**：`/healthz` 與六個 `/monitoring/*` 入口、dashboard 聯合驗收 HTTP 200。
- **Alert + Budget v1**：`budget_rules` 三規則雙閾值；evaluator 讀 rules、寫 `alert_events`（**API 不 inline evaluate**）；overview 含 `kpis.budget`。
- **v1 閾值基準**（seed = 正式基準，調整須新工單）：`daily_cost_usd` 40/50 · `error_rate_15m` 0.10/0.15 · `dlq_backlog` 5/10。
- **驗收證據**：`output/wave1_monitoring_acceptance.ps1` exit 0；Chat A/B/HQ Reviewer 聯合驗收寫回。

### 下游銜接（當年定位）

- 為 **Phase 3／Phase 5** 提供可觀測真底座。
- 為 **Phase 3.5／Phase 7** 成本、usage、歸因治理提供前置里程碑。
- HQ 判定：**可安全進入 Wave 2**（不等於 Wave 2 已交付）。

### 已知限制（Wave 1 當年明寫）

- Langfuse **usage／成本欄位覆蓋**未就緒 → 後續治理工單。
- **`daily_cost_usd` 雙資料源**：evaluator 用 `daily_cost_summary`；overview `kpis.budget` 用 `task_runs` 當日 SUM — **本輪不統一**，僅記錄差異（決策 B）。
- 生產封板、閾值調參須 **另開 wave／工單**。

---

## 3. Wave 2 摘要

Wave 2 在歷史文檔中有 **三條線**，完成度不同；讀者勿將「Wave 2 Gate 0 PASS」與「Wave 2 整線 dev-ready」混為一談。

### 3.1 線 A — Structured Errors（**Gate 0 PASS** ✅ 2026-05-19）

| 項目 | 狀態 |
|------|------|
| **主題** | HTTP API 結構化錯誤契約；legacy `errors[]` 與 `structured_errors[]` 並存 |
| **旗標** | `GOV_CORE_STRUCTURED_ERRORS=true`（staging 驗證用；production soak 當年未完成） |
| **Schema** | `error_schema_version=v1`；必填欄位 `code`、`message`、`node`、`retryable` |
| **模組路徑** | `finalize_errors_for_api()` ← `run_ask_flow` → `execute_workflow()` |
| **Unified 形狀** | `StructuredError.to_unified_dict()` 產出 Langfuse／觀測別名欄位；JSON Schema 見 `shared/schemas/error_schema.json` |
| **Gate 0** | `tests.test_errors` 5/5 PASS |
| **Soak** | `tests/integration/test_wave2_soak_api.py`（TestClient + mock workflow）3/3 PASS — 見 `output/wave2_soak_validation_report.md` |

**Soak 契約要點**：

- Flag **on** 且 workflow 有 errors：HTTP 200 同時含 `structured_errors[]`（v1）與未變更的 legacy `errors[]`。
- Flag **off**：`structured_errors` 缺席或 `[]`，legacy 不變。
- 成功且 `errors` 為空：**不回傳** `structured_errors` 鍵（契約設計）。

**當年限制**：本輪為 **TestClient + mock**，非真機 uvicorn soak；未連 DB／Qdrant／OpenAI。建議下一步為 staging ≥24h production soak（見 `phase3_rollout_plan.md`）。

**未收斂項（當年文件明寫，非 Wave 2 soak 範圍）**：`budget_hooks.budget_status_payload` → UnifiedErrorEnvelope 映射尚未完成（見 `integration_phase3_report.md`）。

### 3.2 線 B — 成本／usage 實測（**partial** · 低樣本）

| 項目 | 內容 |
|------|------|
| **判定** | **partial** — 成本／usage **不可用於決策** |
| **樣本** | `task_runs` 2 筆；Langfuse n≈50；**~0%** 具 `total_cost_usd > 0` |
| **覆蓋率語意** | 欄位多為 **0** 填充；有意義成本觀測 **~0%–10%** |
| **Langfuse** | 50/50 缺 `usage`；治理 metadata 大量缺失 |
| **雙資料源延續** | 同日 DCS **$0（task_count=2）** 與 **$55（task_count=0，smoke 殘留）** 並存 |
| **Phase 3.5** | partial — 底座 dev-ready（Wave 1）、**資料未就緒** |
| **Phase 7** | partial — 優先靶區已列，**未達決策級** |

**Chat D 成本實驗（附屬）**：`core/cost_experiment.py` + benchmark 腳本可合成 ~80% 降本估算（**n=20 模擬**）；**不可**與 live PG 同口径比較；預設 **OFF**。

**Chat C 本輪**：Phase 語言 + 實測寫回完成；**≠** Wave 2 整線 dev-ready。

### 3.3 線 C — workflow_v2 · W2-3 Minimal Governance Gate（read-only · 文件層）

> 命名注意：此 **W2-3** 屬 **workflow_v2 治理試點**，與 gov_core Phase 8 Rollout「Wave 2 Structured Errors」為不同 namespace，但同屬 Wave 2 時代交付。

| 項目 | 內容 |
|------|------|
| **主題** | **ART-GOV-RISK**（G8-6）機讀契約 + 最小治理 gate 原型 |
| **契約** | `workflow_v2/10_governance/G8_artifact_contract/60_gov_risk.md` v0.1 DONE |
| **設計** | `workflow_v2/20_pilot/W2-3_minimal_gate_design.md`（v0.1 · 设计 only） |
| **原型腳本** | `workflow_v2/tools/wf_gov_gate.ps1`（**只讀**；stdout only） |
| **試點案卷** | `workflow_v2/20_pilot/W2-3_case/art_gov_risk.json`（`status: signed`；`fallback_used: true`） |
| **Gate 觸發** | `GATE-RISK-EXIT`（硬）、`GATE-REL-ENTRY`（軟）、`GATE-STOP-WORK`（硬，欄位定義存在） |
| **Verdict 語意** | `allow` / `require-human-override` / `deny`（退出碼 0/1/2） |

**當年明寫限制（v0.1）**：

- **無 CI enforcement**、**無** runtime／prod 流量整合。
- **不讀** WR 正文 fallback（僅 JSON artifact + 票面授權鏈）。
- **未實現** `GATE-STOP-WORK` **獨立 CLI 入口**（欄位檢查在設計表 S1–S3，但無 standalone stop-work 命令）。
- `W2-3_case` 無 `*_case.md` 時須 `-ImpState` 參數。
- `fallback_used: true` 預設 → **`require-human-override`**（除非 `-AllowFallback` + 票面授權）。
- **非目標**：完整 release gate、deny engine runtime、L1+ monitoring 決策。

**與 Structured Errors 的關係**：治理 gate 消費 **ART-GOV-RISK** 與 IMP 狀態；Structured Errors 消費 **HTTP/workflow 錯誤契約**。兩者在 Wave 3 透過 **error taxonomy**（`taxonomy_from_structured_error()`）對齊，但 gate 本身 **不** 解析 API `structured_errors[]`。

---

## 4. Wave 3 摘要

| 維度 | 內容 |
|------|------|
| **主題** | Error Handling & Auto-Recovery v1 |
| **封板日期** | 2026-05-19 |
| **總判定** | **dev-ready · partial** — 程式與測試基線在庫；**預設旗標 off**；staging soak 未完成 |
| **基準線聲明** | 供 Wave 4+ 修訂之文件基準；**非** production 已啟用之運維策略 |

### 三層架構（當年定義）

| 層次 | 交付 | 主要模組 |
|------|------|----------|
| **觀測** | `error_category`／`error_code`／`non_retryable` 寫入 monitoring metadata；`GET /monitoring/dlq` | `error_taxonomy` · `monitoring_ingest` |
| **策略** | Flag-gated exponential backoff；失敗入 DLQ | `retry_policy` · `retry_invoke` · `dlq` |
| **自動／人工邊界** | retry 耗盡後至多 **1** 次 immediate re-invoke；其餘 DLQ 待人工 | `auto_recovery` |

### Retry Policy v1（Gate 0 PASS ✅）

- **公式**：`delay = min(base * 2^(attempt-1), max_delay_ms)` + 可選 full jitter。
- **可重試**：transient 例外、`GovCoreError(retryable=True)`、未落 fail-fast 集。
- **Fail-fast**：`SCHEMA_VALIDATION_FAILED`、`BUSINESS_VALIDATION_FAILED`、`MALFORMED_JSON`、`EMPTY_PAYLOAD`、`HUMAN_REJECTED` 等。
- **驗證**：`tests/test_retry_policy.py` Gate 0 PASS；全 suite 135 ran，134 PASS，1 skipped（見 `output/wave3_retry_policy_report.md`）。

### DLQ + Monitoring + Auto-Recovery

- **DLQ 原因**：`non_retryable`（首次不可重試）／`max_retries_exhausted`（重試 + 可選 auto-recovery 仍失敗）。
- **審計欄位**：`trace_id`、`pipeline`、`mode`、`department`、`error_category`、`error_message`、`retryable`、`attempt`／`max_attempts`。
- **人工重試 API**：`POST /api/dlq/retry/{task_id}`（404 契約已驗；200／409 需真機 DLQ 列）。
- **不進 DLQ**：`WorkflowInterrupted`（人工中斷）。
- **Auto-recovery**：僅窄域 `system_error` + transient；**排除** `validation_error`、`config_error`、`HUMAN_REJECTED`。
- **Wave 1 告警聯動**：`dlq_backlog` warning 5／critical 10。

### 環境旗標（預設皆 **off**）

| 旗標 | 預設 | 說明 |
|------|------|------|
| `GOV_CORE_RETRY_POLICY_ENABLED` | false | invoke 重試 |
| `GOV_CORE_DLQ_ENABLED` | false | DLQ 持久化 |
| `GOV_CORE_AUTO_RECOVERY_ENABLED` | false | 額外 1 次恢復 |
| `GOV_CORE_DLQ_AUTO_RETRY_ENABLED` | false | **Wave 4a** 背景排程（非 Wave 3 本輪） |

### 處理梯度（當年 Playbook 定調）

```text
invoke → retryable? → backoff retry → auto-recovery（可選，≤1 次）
                              ↓ 仍失敗
                         DLQ 待人工 → GET /monitoring/dlq → POST /api/dlq/retry/{task_id}
                              ↓
                    HUMAN_REJECTED / interrupt → 人工批准閘（不進 DLQ 或須 resume）
```

### 驗收證據（文件輪）

| 來源 | 結果 |
|------|------|
| `tests/test_retry_policy.py` | Gate 0 PASS |
| `tests/test_dlq_wave3.py` | enriched DLQ + taxonomy PASS |
| `tests/test_auto_recovery.py` | 8 cases PASS |
| Wave 2 soak | `structured_errors[]` 契約 PASS |

### 當年 Phase 對照

| Phase | 判定 |
|-------|------|
| Phase 3 · 錯誤觀測 slice | partial — 觀測就緒；**尚未**依 `error_category` 自動派工 |
| Phase 5（冪等 + DLQ） | dev-ready · partial |
| Phase 7（成本 + 營運） | partial — 錯誤路徑成本治理 **deferred** |

---

## 5. 在現行架構中的位置（Reference Level）

### 5.1 定位一句話

Wave 1–3 成果在 **workflow_v2／Wave 4／Wave 5** 時代被視為 **「歷史已驗證設計」（reference level）**：schema、契約、測試基線與 Playbook **可供引用**，但 **不等於** 現網預設開啟、**不等於** production SLO／SLA 承諾。

| Reference level | 含義 | 不含 |
|-----------------|------|------|
| **R0 — 契約／測試基線** | Wave 2 `structured_errors` v1、Wave 3 retry／DLQ taxonomy、Wave 1 monitoring schema | 真機 soak 通過、旗標 default-on |
| **R1 — dev-ready 能力** | Wave 1 六端點 + evaluator；Wave 3 單元／整合測試全綠 | production-ready、on-call runbook 定稿 |
| **R2 — 治理原型** | W2-3 `wf_gov_gate.ps1` + ART-GOV-RISK JSON | CI enforcement、GATE-STOP-WORK 獨立 CLI |

### 5.2 與 Wave 4 的關係

Wave 4A（ask_pipeline live，2026-05-19）為 **Wave 1–3 的實戰後驗**，結論 **強化 partial 敘事**而非升格：

- Wave 1：API 成功 **≠** PG 有列（ingest 斷層）。
- Wave 2：20 筆 live **未** 收口 PG 成本；合成基準 **不可** 與 live 同口径比較。
- Wave 3：有效批次 **未** 觸發 DLQ／retry（旗標 off）；`config_error` 邊界在 deploy 不一致時已概念驗證。

Wave 4+ 待辦（當年寫入，本文件僅轉述）：ingest 對齊、DLQ 真機 soak、`GOV_CORE_DLQ_AUTO_RETRY_ENABLED`（Wave 4a）、Interrupt resume。

### 5.3 與 Wave 5 / ENF 設計的梯度對照

Wave 3 確立的 **「錯誤 → 重試 → DLQ → 監控 → 人工決策 → Auto-Recovery」** 梯度，在 Wave 5 ENF 架構中可讀作 **能力升級階梯的歷史先例**（非一一映射，僅設計脈絡）：

| Wave 3 梯度 | 現行 W5／ENF 類似姿態（reference） |
|-------------|-------------------------------------|
| Structured error 觀測（taxonomy metadata） | Shadow 觀測：`[GOV-ENF-SHADOW-SUMMARY]`、`would_block` **不阻斷** |
| Retry / auto-recovery（窄域、flag-gated） | Preview / logging-only：`GOV_ENF_BLOCKING_CANARY=0` |
| DLQ 待人工 + `POST /api/dlq/retry` | `require-human-override`、人工抽檢 escalation criteria |
| Fail-fast（validation／config） | 未來 **limited deny**／blocking canary 候選（如 ENF-RULE-1）— **當年 Wave 3 未實作，W5 仍 shadow-only** |
| Wave 1 `dlq_backlog` 告警 | 營運面板 + nightly analyzer；**非** SLA 承諾 |

**重點**：W5-A Phase 2 明定 **shadow-only**（`GOV_ENF_BLOCKING_CANARY=0`）；Wave 3 亦明定 **旗標預設 off**。兩者共同哲學是 **先觀測、再人工裁決、最後才談阻斷** — Wave 3 Playbook 為 runtime 錯誤徑路提供了已驗證的 **參考實作**；W5 ENF 為 **CI／治理徑路** 提供了平行的 shadow 參考層。

### 5.4 workflow_v2 消費方式

- **IMP 生命周期**：W2-3 gate 原型可供 W3-C／W4 案卷 **只讀** 驗證 `GATE-RISK-EXIT`；**不** 取代 Cursor `governance-guard` 或 HQ 派工。
- **錯誤契約**：新 ticket 若涉 retry／DLQ，應引用 Wave 3 taxonomy + Wave 2 `structured_errors` v1，**而非** 重新發明欄位名。
- **監控底座**：Wave 1 六端點仍為 monitoring 整合的 **schema 參考**；成本／雙資料源問題 **仍 open**（Wave 2 partial 延續）。

---

## 6. Limitations & Open Questions

以下 **僅轉述** 當年文件明寫限制與「未來可能補做」項；**不** 新增承諾或工單。

### Wave 1

- production-ready **未宣稱**；生產封板須另開 wave／工單。
- Langfuse usage／成本欄位覆蓋 **未完成**。
- `daily_cost_usd` **雙資料源未統一**（evaluator vs overview）。
- 閾值調整須新工單，禁止無留痕漂移。

### Wave 2

- Structured Errors：**非真機 soak**；staging ≥24h soak **未完成**。
- Budget → UnifiedErrorEnvelope 映射 **尚未完成**（integration phase3 當年留痕）。
- 成本線：**Chat A/B 正式交付物未完全入檔**；`kpis.cost` 區塊 **未現**。
- Langfuse 樣本 **100%** 缺 usage。
- W2-3 gate：**無 CI**、**無 GATE-STOP-WORK 獨立入口**、**不讀 WR fallback 正文**。
- `W2-3_case.md` IMP 迁移日志 **留待后续票**。

### Wave 3

- 所有 runtime 旗標 **預設 off**；DLQ 200／409 真機待失敗種子。
- **staging soak 與 production 漸進開旗標未完成**。
- 錯誤路徑 **cost／usage** 與 DLQ 聯動 **deferred**（Wave 2 建議延續）。
- **未納入**：DLQ 背景 auto-retry（Wave 4a）、DLQ UI／批量操作、依 `error_category` 自動路由 worker、`llm_error` 專用 fallback 模型。
- Production 全開 retry + auto-recovery 須 **staging soak + 尚書省裁決**。

### 跨 Wave（Wave 4A 後驗加強）

- Monitoring ingest：**「API 成功 ≠ PG 有列」** 斷層已暴露。
- Deploy／熱進程與契約常數不一致可致全批 **`config_error`** 假失敗。
- 雙資料源 DCS smoke **$55** vs task_runs **$0** **延續**。

---

## 7. Non-goals

本文件 **刻意不做** 以下事項：

1. **不改寫歷史結論** — dev-ready／partial／Gate 0 PASS 等判定以 Progress／master_status 為準。
2. **不定義現系統必須重做什麼** — 是否重跑 soak、是否開旗標、是否統一雙資料源，留待當下 wave 工單與尚書省裁決。
3. **不涉及實作票** — 不提供 patch、不開新 milestone 編號；僅提供設計脈絡與 reference level。
4. **不宣稱 production-ready** — Wave 1–3 任何子項均 **不能** 因本總結而被解讀為現網 SLA／on-call 就緒。
5. **不混淆 namespace** — gov_core Phase 8 Rollout Wave 1–3 與 workflow_v2 的 W2-1／W2-3／W3-A 票號 **各自獨立**；本文件 §3.3 已標註 W2-3 治理線。

---

## 附錄 — 關鍵證據索引

| 主題 | 路徑 |
|------|------|
| Wave 1 封板戰報 | `04_Workflows/00_Agent_Work_Progress.md` →「Wave 1 封板戰報」 |
| Wave 2 成本 partial | 同上 →「Wave 2 – 成本 / usage 實測小結」 |
| Wave 2 Structured Errors soak | `gov_core_system/output/wave2_soak_validation_report.md` |
| Wave 3 Playbook | `04_Workflows/00_Agent_Work_Progress.md` →「Wave 3 – Error Handling & Auto-Recovery v1」 |
| Wave 3 Retry Gate 0 | `gov_core_system/output/wave3_retry_policy_report.md` |
| Phase 5–8 路線圖 Wave 段 | `gov_core_system/output/phase5-8_roadmap.md` |
| W2-3 治理 gate | `workflow_v2/20_pilot/W2-3_minimal_gate_design.md` · `W2-3_case/README.md` |
| 里程碑索引 | `04_Workflows/project_status/master_status.md`（2026-05-19 Wave 1–3 條目） |
| W5 ENF shadow 現行姿態 | `docs/W5-A-RUNTIME-03-ENF-SHADOW-OPERATIONS-GUIDE.md` |

---

*W1-3-HISTORY-SUMMARY-01 — doc-only — 2026-05-31*
