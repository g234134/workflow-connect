# AI Workflow 偵錯與健檢服務 — Product Spec v1

> **票號**：C1-P1 · Product Definition v1  
> **狀態**：初稿（對外說明用；非合約、非 SLA）  
> **能力基線**：Wave A 治理／eval gate + Wave B 可觀測性／KB index（B-Final 已完成）  
> **技術權威**：`docs/WAVE_B_EXECUTION_PLAN.md` · `docs/observability.md` · `docs/SKILL_CATALOG_OVERVIEW.md` · `docs/ROUTING_POLICY_GUIDE.md`  
> **後續詳化**：C1-P2（執行步驟、戰報模板、tool_id 對照）

---

## 1. 服務介紹（用戶視角）

### 1.1 這是什麼

**AI Workflow 偵錯與健檢服務**協助團隊釐清「AI 工作流為什麼偶爾答錯、變慢、或需要人工複審」，並產出**可重跑、可交接**的結構化健檢報告。

服務聚焦三件事：

| 面向 | 客戶得到的價值 |
|------|----------------|
| **品質訊號（Gate）** | 從既有請求紀錄匯出 eval 結果，彙總 `needs_review` 比例、常見標籤與 confidence 等級（high/low/n/a）／樣本數 N |
| **追溯能力（Trace）** | 以 `trace_id`／`task_id`／`session_id` 追查 **gov-trace-v2** 事件鏈，對齊失敗或需複審的個案 |
| **知識層就緒（Index）** | 對指定程式庫子樹做離線 KB index bootstrap，驗證 manifest RAG smoke，回報 `ready`／`stale`／`missing` |

最終交付一份**工作流健康總覽**（Gate + Index + Trace join），讓 PM／工程負責人能在同一頁判斷：是資料索引問題、管線品質問題，還是基礎設施／超時類風險。

### 1.2 適合誰

- 已上線或 staging 的 **LangGraph／Agent／RAG ask 管線**，有基本日誌或 trace 輸出
- 需要**第三方視角**做離線健檢，而非長期代維運的團隊
- 希望把「人工 copy-paste trace id 追查」收斂成**標準化 CLI 產物**的團隊

### 1.3 服務性質（重要聲明）

- 本規格描述**技術服務內容**；不含報價、合約條款、收款流程。
- 現階段能力為 **dev／staging 等級的調查與彙總**（見 `docs/observability.md`：*investigation alerts · not production SLA*）。
- 我們**不承諾**修復客戶程式、也不保證消除所有 `needs_review` 個案；交付的是**診斷證據與可執行建議**，修復由客戶或後續工程票承接。

---

## 2. 客戶需提供的輸入（Input Requirements）

### 2.1 必備（Minimum）

| 輸入 | 說明 | 格式／備註 |
|------|------|-----------|
| **工作流樣本紀錄** | 一段時間內的 ask／agent 執行紀錄 | `ibridge` 或相容 JSONL；可經 `obs.eval.export` 轉為 `eval_export/v1` |
| **Trace 日誌（建議）** | 與樣本時間窗重疊的 trace 事件 | **gov-trace-v2** JSONL（例如 `runtime/task_traces.jsonl` 或客戶等價匯出） |
| **調查目標** | 本次健檢要回答的問題 | 例如：「為何 infra_risk 標籤升高？」「Index 是否覆蓋 in-scope 路徑？」 |
| **程式庫存取** | 若含 KB index 健檢 | 客戶授權之 repo 子樹（路徑清單或 scope JSON）；**非**全庫即時同步 |

### 2.2 建議提供（加速診斷）

| 輸入 | 用途 |
|------|------|
| `case_id`／案卷對照 | 對齊 `index_status` 與 eval 列（見 pilot `W2-1` 範本） |
| `trace_id`／`task_id` 已知問題單 | 直接進入 `obs.trace.query` 深查 |
| CI／nightly eval export 檔 | 與既有 `eval-gate-ci` artifact 對齊，減少重跑 |
| 環境說明 | dev／staging／prod-shadow；**不含**金鑰原文 |

### 2.3 客戶不需提供

- 生產資料庫寫入權限（本服務以**只讀**匯出為主）
- `.env` 或 API 金鑰全文（驗證走客戶側 smoke 或遮罩後 metadata）
- 長期託管 infra 的 root 權限

### 2.4 前置假設

客戶管線至少具備下列之一，否則服務降級為「契約／schema 對照 + 缺口清單」：

1. 可匯出 **eval_export/v1** 相容列（含 `gate_result`、`tags`、`source_ref` 等）
2. 可匯出 **gov-trace-v2** JSONL（含 `trace_start`／`span_end`／`trace_end`）
3. （若含 Index 健檢）可指定 **index scope** 並允許離線 bootstrap

---

## 3. 服務輸出內容（Deliverables）

### 3.1 標準交付包（v1）

| 產物 | 內容摘要 | 對應工具（Gov `tool_id`） |
|------|----------|---------------------------|
| **Eval 健檢報表** | Markdown + JSON：`needs_review` 比例、top tags、樣本數 N | `obs.eval.report` |
| **WF 健康總覽** | 一頁 Gate／Index／Trace join 摘要 | `obs.wf.status_summary` |
| **Flagged 個案追查** | `needs_review`／`infra_risk` 列與 trace 摘要 join | `obs.eval.correlate`（可 `--format triage-md`） |
| **Trace 深查摘要** | 指定 id 的事件計數、延遲、錯誤類型 | `obs.trace.query` |
| **Index 狀態側車** | `case_id`、`kb_index_status`、`file_count`、`chunk_count` | `kb.index.bootstrap` + `index_status` JSON |
| **RAG smoke 結果** | manifest 對齊之 smoke 通過／失敗摘要 | `kb.index.rag_smoke` |
| **執行證據索引** | 可重跑命令清單 + 關鍵 `ok`／計數語意 | 彙整自 catalog `verify_command` |

典型 artifact 路徑（邏輯名，實例見 `Master_Map.json`）：

- `artifacts/eval/eval_report.latest.{md,json}`
- `artifacts/wf/wf_status_summary.latest.{md,json}`
- correlate／triage 附錄（Markdown 或 JSONL）

### 3.2 可選加購（視輸入與授權）

| 產物 | 條件 |
|------|------|
| Eval 分佈統計附錄 | 有足夠樣本數 N（`obs.eval.stats`） |
| CI gate 對照說明 | 客戶提供 PR／nightly eval artifact |
| Index scope 差距清單 | scope JSON 與實際 in-scope 路徑可對照 |

### 3.3 明確不屬於 v1 交付

- 自動修改客戶 repo 或 production 設定
- Grafana／HTML dashboard、Slack 自動通知（Wave C 留項）
- PG + Langfuse **統一查詢 API**（現僅支援本地 JSONL + 可選 PG 讀取，非統一 API）
- Production selector gate 接線（`kb.index.selector_gate` 現為 **skeleton／reference**）
- 對外 SLA 或「零 needs_review」保證

---

## 4. 適用場景與限制（What We Do / What We Don't Do）

### 4.1 我們做什麼

| 場景 | 服務動作 |
|------|----------|
| **品質退化調查** | 匯出 eval → 報表 → 標出高頻 tags 與 `needs_review` 列 |
| **單案追溯** | `obs.eval.correlate` 將 flagged 列 join 到 trace 摘要；必要時 `obs.trace.query` 逐事件深查 |
| **知識層就緒檢查** | 對授權子樹 bootstrap index → 更新 `index_status` → RAG smoke |
| **跨域一頁總覽** | wf status summary 回答：Gate 是否惡化、Index 是否 ready、trace join 命中率 |
| **標準化交接** | 產物對齊 Gov Tool Catalog `tool_id`，便於 C1-P2 戰報與後續工程票引用 |

### 4.2 我們不做什麼

| 限制 | 說明 |
|------|------|
| **非 7×24 代維運** | 不提供持續託管、on-call 或 incident 承諾 |
| **非 production SLA** | 告警與指標為 **investigation-only**（見 `docs/observability.md`） |
| **不全庫即時索引** | 僅**離線、scoped** bootstrap；全庫增量、多 tenant 產品化屬 Wave C 以後 |
| **不改寫客戶決策邏輯** | 不預設接入 `ask_rag_selector` prod gate；Routing Policy v1 僅描述編排，**尚未**驅動生產路由 |
| **不保證根因唯一** | 交付證據與假設清單；多因並存時標註需客戶確認的項目 |
| **不處理商業流程** | 報價、合約、NDA、收款不在本規格範圍 |

### 4.3 能力邊界對照（誠實基線）

以下能力**已存在**於 Wave B（可納入服務），其餘為路線圖：

| 能力 | v1 服務 | 備註 |
|------|---------|------|
| eval export／report | ✅ | CI artifact 可對照 |
| trace query（JSONL） | ✅ | 需客戶提供或接線匯出 |
| eval–trace correlate | ✅ | 預設僅 flagged 列 |
| wf status summary | ✅ | trace 檔缺失時 soft degrade |
| kb index bootstrap + smoke | ✅ | 需 scope 授權；試點級非全庫 |
| routing policy 編排 | ✅（描述層） | `config/routing_policy.yaml` 可調 route，**不自動執行** |
| selector gate prod 接線 | ❌ | skeleton only |
| 統一 Langfuse／PG query API | ❌ | Wave C |
| 視覺化 dashboard | ❌ | Wave C |

---

## 5. 粗略流程概覽（High-Level Execution Steps）

> **對外文件**：此處保留 v1 high-level 骨架，供客戶理解服務流程。  
> **對內執行細節**：參見 `docs/WAVE_C_EXECUTION_PLAN.md` — 含完整 Step 0–4、tool_id/route_id 對照、CLI 範例與人工判讀點。

```mermaid
flowchart LR
    A[Step 0 接案與輸入盤點] --> B[Step 1 工具選擇]
    B --> C[Step 2 執行 Wave B 工具]
    C --> D[Step 3 彙整戰報草稿]
    D --> E[Step 4 Internal Review]
    E --> F[交付與交接]
```

> **執行分工**：Step 2 各 CLI 目前為**人工執行**（可重跑、有 unittest 驗證）；自動化 pipeline 為 Wave C 後續票。

### Step 0 — 接案與輸入盤點

- 確認調查目標、時間窗、環境（dev／staging／shadow）。
- 檢查必備輸入是否滿足 §2.1；缺項則在交付包中標 **degraded scope**。
- 對齊 Gov catalog：`python -m skills.gov_tool_registry validate`（內部自檢，非客戶必跑）。

### Step 1 — Eval 健檢（Gate）

- 路由參考：`wave_b.eval_report`（`obs.eval.export` → `obs.eval.report`）。
- 產出 `eval_report.latest.{md,json}`：N、`needs_review` 比例、top tags。
- 若客戶有 CI artifact，註明與 `eval-gate-ci` 的對照關係。

### Step 2 — Trace 對齊與追查

- 對 flagged 列執行 `obs.eval.correlate`（join 優先序：`trace_id` > `task_id` > `session_id`）。
- 必要時 `obs.trace.query` 深查；triage 格式用於值班速覽。
- 記錄 **trace join 命中率**（與 wf summary §3 一致）。

### Step 3 — Index 健檢（可選）

- 路由參考：`wave_b.kb_index_bootstrap`（`kb.index.bootstrap` → `kb.index.rag_smoke`）。
- 更新／讀取 `index_status`：`kb_index_status`、`file_count`、`chunk_count`。
- 僅在客戶授權 scope 內執行；不宣稱全庫覆蓋。

### Step 4 — 綜合總覽

- 執行 `obs.wf.status_summary`，組裝 Gate + Index + Trace join 一頁摘要。
- 產出 **Reviewer shortcuts**（可重跑命令區塊，見 `artifacts/wf/wf_status_summary.latest.md` 範例）。

### Step 5 — 交付與交接

- 交付 §3.1 標準包 + 缺口／假設清單。
- 建議項分級：**立即**（blocking 品質）、**短期**（index stale）、**路線圖**（Wave C 能力）。
- 交接至 C1-P2 戰報模板或客戶內部 ticket（引用 `tool_id`，非暱稱）。

### 內部編排備註（不寫入客戶合約）

- **B-F1** Skill Catalog 定義工具清單；**B-F3** Routing Policy 定義 route 順序。
- **B-F2** Multi-Chat 四角色（Implementer／Reviewer／Scribe／Orchestrator）可作為**內部交付協作**方式，非客戶必知介面。
- Policy 驗證：`python -m core.routing_policy_loader validate`（內部）。

---

## 6. 相關文件索引

| 文件 | 用途 | 讀者 |
|------|------|------|
| `docs/WAVE_B_EXECUTION_PLAN.md` | Wave B 各票交付與可重跑命令 | 內部執行者 |
| `docs/WAVE_C_EXECUTION_PLAN.md` | **本服務對內執行 runbook**：Step 0–4、tool_id/route_id 對照、CLI 範例 | **內部執行者（主要）** |
| `docs/observability.md` | Trace schema、trace query、wf summary | 技術整合者 |
| `docs/SKILL_CATALOG_OVERVIEW.md` | Gov `tool_id` 權威清單（11 tools） | 內部執行者、下游開發 |
| `docs/ROUTING_POLICY_GUIDE.md` | `route_id` 與編排語意；Policy v1 為描述層（非自動執行） | 內部執行者 |
| `observability/eval_export.md` | eval export／correlate 契約 | 技術整合者 |
| `workflow_v2/20_pilot/W3-B_kb_contract.md` | Index 狀態與 gate 語意 | 技術整合者 |

> **索引說明**：
> - **對外 Product Spec**（本檔）聚焦「客戶能得到什麼」與「需要提供什麼」
> - **對內 Execution Plan**（WAVE_C_EXECUTION_PLAN.md）聚焦「如何一步步執行」與「人工判讀點」
> - **Wave B 計畫**（WAVE_B_EXECUTION_PLAN.md）為各工具開發交付紀錄，Execution Plan 引用其 CLI 範例

---

## 7. 版本與後續

| 項目 | 說明 | 狀態 |
|------|------|------|
| **本檔版本** | Product Spec v1 · C1-P1 | 已接受（accepted_with_gaps） |
| **C1-P2** | 執行 runbook、戰報模板、`tool_id`／`route_id` 對照表 | **本檔** — 見 `docs/WAVE_C_EXECUTION_PLAN.md` |
| **C1-P3（建議）** | 定價與交付邊界（最小／標準／含 Index 分級） | 待排程 |
| **Wave C** | 視覺化 dashboard、nightly correlate artifact、prod selector 接線 | **未**納入 v1 承諾 |

### 路線圖錨點

```
C1-P1 Product Spec（對外）
    │
    ▼
C1-P2 Execution Plan ← 本文檔新增「對內執行細節」
    │
    ├──► Wave C1 自動化（一鍵 pipeline）
    ├──► Wave C1 CI 整合（nightly eval → report → summary）
    ├──► Wave C2 Dashboard（Grafana/HTML）
    └──► Wave C2 Prod Selector 接線（kb.index.selector_gate skeleton → prod）
```

### 文件關係總覽

| 層級 | 文件 | 讀者 | 更新頻率 |
|------|------|------|---------|
| 對外產品 | `docs/PRODUCT_AI_WORKFLOW_DIAGNOSTIC.md` | 客戶、PM | 每版 Product Spec |
| 對內執行 | `docs/WAVE_C_EXECUTION_PLAN.md` | Implementer、分析師 | 每案執行參考 |
| 工具權威 | `docs/SKILL_CATALOG_OVERVIEW.md` | 開發者、執行者 | 每 Wave 交付 |
| 開發紀錄 | `docs/WAVE_B_EXECUTION_PLAN.md` | 開發者 | Wave B 交付時 |
| 編排配置 | `docs/ROUTING_POLICY_GUIDE.md` | 開發者、執行者 | Policy 版本迭代 |

---

*文件版本：v1.0-draft · 2026-06-07 · C1-P1 Product Definition*
