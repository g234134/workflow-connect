# M-GOV-L1 — Shadow Selector / Advisory 設計稿

> **票別**：`M-GOV-L1`（Sprint 6 · 治理文檔）  
> **狀態**：**設計稿 only** — 未實作、無 env flag、無 prod API 變更  
> **權威對齊**：`50_context_entry_runbook.md` §6.8.4 · `AGENTS.md` Monitoring Graph 治理模式 · `00_master_plan.md` §4.12  
> **硬限制**：本稿**不**改 selector／answer／主 ask graph 程式；shadow／advisory 欄位**不**進預設 prod API envelope。

---

## 1. 定位（L1 vs L0 vs L2）

| 級別 | 本稿涵蓋 | 對 production decision |
|------|----------|-------------------------|
| **L0** | 參照（已交付） | **零影響** — 只讀 observability sidecar |
| **L1** | **本稿主體** | **零影響** — shadow 對照 + advisory 供離線／人工審計 |
| **L2** | 僅引用 §6.8.5 | **直接影響** — 須另開 `M-GOV-L2` 票；**不在本稿範圍** |

**L1 一句話**：在 ask 主路徑**已做出** production selector 決策之後，**平行**計算「若依 monitoring graph 啟發式會怎麼選」，寫入內部 sidecar／trace；**不**覆寫 `use_rag`、retrieve、answer 或任何 user-facing 輸出。

**Shadow vs Advisory（均屬 L1）**

| 子模式 | 語意 | 允許 | 禁止 |
|--------|------|------|------|
| **Shadow** | 記錄 hypothetical decision 與 production 對照 | 寫內部 sidecar、eval 匯出、dev trace | 改寫 production selector 輸入／輸出 |
| **Advisory** | 暴露建議值供人工／離線對賬 | metadata／eval 欄位 `advisory_*` | 自動採納、寫入 answer 文本、進預設 prod envelope |

---

## 2. 資料流（設計 · 未實作）

現況（L0）sidecar 寫入點（唯讀參照）：

```
context_entry → enrich (O-2 executor) → _monitoring_executor_result
                                      → _monitoring_graph_result (GOV_MONITORING_GRAPH_ENABLED=1)
         → selector (production use_rag) → retrieve → answer
         → ibridge_v0.monitoring_graph (L0 whitelist only)
```

**L1 建議插入點（待實作票裁定）**

| 選項 | 位置 | 優點 | 風險 |
|------|------|------|------|
| **A（首選）** | selector **之後**、retrieve **之前** | production `use_rag` 已確定；shadow 純對照 | 需讀 graph + production selector 快照 |
| **B** | enrich 內、graph finalize **之後** | 與 executor／graph 同區塊 | 易誤觸 production 分支；須嚴格 sidecar 隔離 |

**裁決（設計稿）**：預設 **選項 A** — shadow 節點**只讀** `_monitoring_graph_result` 與 `ask_selector`（或等價 production 決策快照），**只寫** `_monitoring_shadow_decision`（內部鍵，見 §3）。

---

## 3. 欄位契約（建議）

### 3.1 內部 sidecar（init／final state · 不公開）

根物件建議鍵名：**`_monitoring_shadow_decision`**（init／final 內部）；離線 eval／trace 匯出可扁平化為 **`monitoring_shadow_decision`**（**仍不**進預設 prod API envelope）。

```json
{
  "ok": true,
  "shadow_level": "L1-shadow",
  "shadow_use_rag": false,
  "shadow_route": "monitoring_heuristic_v0",
  "shadow_rule_id": "SHADOW-MON-RAG-1",
  "production_use_rag": true,
  "production_selector_rule_id": "SELECTOR-KB-1",
  "diff": {
    "use_rag_match": false,
    "route_match": null
  },
  "inputs": {
    "graph_ok": true,
    "graph_version": "v0.2-langgraph-min",
    "top_recommendation_kind": "warn",
    "top_recommendation_severity": "warn"
  },
  "reasons": ["graph_recommendation_suggests_skip_rag"],
  "trace_id": "<correlation>",
  "computed_at_ms": 0
}
```

| 欄位 | 型別 | 說明 |
|------|------|------|
| `ok` | bool | shadow 計算是否成功（**不**代表 production 成功） |
| `shadow_use_rag` | bool \| null | graph 啟發式下的 hypothetical RAG 決策 |
| `shadow_route` | string | shadow 策略識別（**非** production `subagent_route`） |
| `shadow_rule_id` | string | shadow 規則 id（對照 production `selector_rule_id`） |
| `production_use_rag` | bool | **快照** production 值；shadow **不得**改寫來源 |
| `diff.use_rag_match` | bool \| null | `shadow_use_rag === production_use_rag`；graph 不可用時 `null` |
| `diff.route_match` | bool \| null | 可選；subagent／answer mode 對照 |
| `reasons` | string[] | shadow 推導理由（debug／eval） |
| `inputs` | object | 精簡 graph 摘要引用；**禁止**嵌入完整 `service_summary` |

**失敗／skip 形狀（fail-open）**

```json
{
  "ok": false,
  "shadow_level": "L1-shadow",
  "shadow_use_rag": null,
  "reason": "graph_unavailable",
  "production_use_rag": true,
  "diff": { "use_rag_match": null }
}
```

### 3.2 Advisory 子欄位（仍屬 L1 · 內部／eval only）

建議與 shadow 同物件或嵌套 `advisory`：

| 欄位 | 型別 | 說明 |
|------|------|------|
| `advisory_use_rag` | bool \| null | 供人工 review 的建議值；**語意上不等於** production policy |
| `advisory_confidence` | string | 可選：`low`／`medium`／`high`（啟發式，非機率校準） |
| `advisory_note` | string | 短句說明；**禁止**進 user-facing answer |

**命名空間**：`advisory_*` 與 L2 未來之 `slo_verdict`／`slo_breach` **分離**（見 runbook §6.8.7）。

### 3.3 公開 envelope（ibridge／HTTP）— **L1 仍不擴張**

| 環境 | L0 現況 | L1 設計稿 |
|------|---------|-----------|
| prod 預設 API | `ibridge_v0.monitoring_graph`（whitelist） | **維持 L0**；**不**新增 shadow／advisory 鍵 |
| dev／eval 匯出 | 可選 `expose_ibridge` | 僅經**明示** eval 匯出器或離線 trace dump；非本 Sprint 交付 |

**禁止**：在 `strip_ask_pipeline_internal_keys` 白名單外，將 `_monitoring_shadow_decision` 或 `monitoring_shadow_decision` 洩漏至預設 prod response。

### 3.4 與現有 ibridge 欄位對照

現有 production 決策已暴露於 `ibridge_v0.selector_decision.use_rag`（L0）。L1 shadow **不**替換該欄位；離線 eval 以 `production_use_rag` 快照 + `shadow_use_rag` 做 join。

---

## 4. Shadow 推導邏輯（啟發式 · 待實作票細化）

**原則**：shadow 規則集**獨立**於 production selector；僅**讀** graph 公開摘要與內部 `_monitoring_graph_result` 之 whitelist 子集。

**暫定規則骨架（非 production policy）**

| 條件（示意） | shadow_use_rag | shadow_rule_id |
|--------------|----------------|----------------|
| graph `ok=false` 或缺失 | `null` | `SHADOW-SKIP-NO-GRAPH` |
| `top_recommendation.severity` ≥ warn 且 kind 暗示 ops 優先 | `false` | `SHADOW-MON-SKIP-RAG-1` |
| 其餘 | 對齊 production 快照 | `SHADOW-MIRROR-PROD` |

**重要**：`recommendation`／`top_recommendation` 為 **L0 啟發式**；shadow 僅記錄「若採納該啟發式會怎麼選」，**不得**標為 `policy`／`slo_pass`／`gate`（runbook §6.8.7）。

---

## 5. Trace / Observability 設計

### 5.1 關聯鍵

| 鍵 | 來源 | 用途 |
|----|------|------|
| `trace_id` | ibridge／col task record | shadow 事件與 ask 請求 join |
| `task_id` | task_input | 管線內關聯 |
| `routing_rule_id` | `_subagent_route` | monitoring 路由稽核 |
| `graph_version` | `_monitoring_graph_result.analysis` | 版本對照 |

### 5.2 結構化 log 事件（建議 · 實作票定義）

| 事件名 | 時機 | 最小 payload |
|--------|------|----------------|
| `monitoring_shadow_start` | shadow 節點進入 | `trace_id`, `graph_ok` |
| `monitoring_shadow_decision` | 計算完成 | `shadow_use_rag`, `production_use_rag`, `diff.use_rag_match`, `shadow_rule_id` |
| `monitoring_shadow_skip` | graph 不可用 | `reason` |
| `monitoring_shadow_fail` | 例外 | `reason`（**不** raise 至主路徑） |

### 5.3 匯出與 dashboard

- **離線 eval**：NDJSON／Parquet 匯出 `monitoring_shadow_decision` + `ibridge_v0.selector_decision` 對照表。  
- **指標（升格 L1 前監控）**：`shadow_eval_total`、`use_rag_mismatch_rate`、`shadow_ok_rate`（對齊 §6.8.4 門檻：`ok` ≥99%、樣本 ≥500）。  
- **與 K-2 shadow**：`test_k2_ask_shadow` 模式可參考；是否共用 `ibridge_exporter` 見 runbook §6.8.10（**未決**）。

---

## 6. Fail-open 原則

| 情境 | 主 ask 路徑 | Shadow sidecar |
|------|-------------|----------------|
| graph 未跑（flag OFF） | 不變 | `ok=false`, `reason=graph_disabled`, `diff.use_rag_match=null` |
| graph `ok=false` | 不變（L0 已規定） | `shadow_use_rag=null`；**不** fallback 改 production |
| adapter stub（無 graph） | 不變 | skip shadow；不寫或寫 skip 事件 |
| shadow 節點例外 | **不變** | 捕獲 → `ok=false` + log；**禁止** propagate |
| L1 flag 關閉（未來） | 不變 | 不寫 shadow sidecar；回到 L0 |

**裁決**：shadow **永遠** fail-open；任何 shadow／advisory 失敗**不得**阻斷、降級或 reroute 請求（與 L2 相反，見 §6.8.5）。

---

## 7. 環境與升格門檻（引用 · 不另立標準）

實作前須滿足 runbook **§6.8.4** 全部條件（累加 L0）：

- L0 連續 **14 日** staging／prod 開 graph **無 P0**  
- monitoring 路由樣本 **≥500**  
- graph `ok` 率 **≥99%**  
- 必要 artefacts：① 本設計稿定稿 + 實作 diff；② §8 測試骨架落地；③ shadow trace 匯出；④ 風險評估；⑤ §6.8.8 回歸全綠  
- **尚書省 L1 批文** + 實作票（env flag 名由**該票**定義；Sprint 6 **不**新增 flag）

環境矩陣見 §6.8.6：prod shadow **僅**尚書省批准後。

### 7.1 升格門檻達成度（尚書省／監控填寫 · 非本票實作範圍）

> **用途**：未來審查是否可開 **L1 實作票**（動碼）時填寫。下列欄位**不**代表現況已滿足；預設皆未達標。

| # | 門檻（runbook §6.8.4） | 現在狀態 | 證據／備註 |
|---|------------------------|----------|------------|
| G1 | L0 在 staging／prod 連續 **14 日** 開 graph **無 P0** | `TODO: 尚書省填寫` | 起算日、環境、P0 定義 |
| G2 | monitoring 路由樣本 **≥500** | `TODO: 由監控／metrics 填入樣本數` | 路由 `rule_id` 篩選條件 |
| G3 | graph `ok` 率 **≥99%** | `TODO: 由 metrics 報告填寫` | 分母＝graph 嘗試次數 |
| G4 | artefact ① 設計稿定稿 + 實作 diff | `TODO: 實作票開工後填` | 本稿＝設計；diff＝實作票 |
| G5 | artefact ② `test_monitoring_graph_shadow_*` 全綠 | `TODO: 實作票驗收後填` | §8 骨架 |
| G6 | artefact ③ shadow trace／eval 匯出可重現 | `TODO: 實作票驗收後填` | §12.4 |
| G7 | artefact ④ 風險評估（誤導／外洩） | `TODO: 尚書省或治理填` | 獨立附檔 |
| G8 | artefact ⑤ §6.8.8 L0 回歸全綠 | `TODO: 由 CI／runner 填` | runbook §6.8.9 命令 |
| G9 | **尚書省 L1 批文** | `TODO: 尚書省填寫` | 批文編號／日期 |
| G10 | L1 env flag 名稱與環境矩陣（§6.8.6） | `TODO: 實作票定義後填` | placeholder：`GOV_MONITORING_SHADOW_*` |

**決策句（填完 G1–G10 後）**：`TODO: 尚書省裁決 — 是否開 L1 實作票 / 僅延長 L0 觀察 / 阻塞原因`

---

## 8. 暫定測試骨架清單

檔案前綴：`tests/test_monitoring_graph_shadow_*`（戰車根；實作票落地）

| 模組 | 類／函式（建議） | 断言要點 |
|------|------------------|----------|
| `test_monitoring_graph_shadow_contract.py` | `TestShadowDecisionShape` | `_monitoring_shadow_decision` 必填鍵、`diff.use_rag_match` 語意 |
| `test_monitoring_graph_shadow_fail_open.py` | `TestShadowFailOpen` | graph 失敗／缺失時 production `use_rag` 不變 |
| `test_monitoring_graph_shadow_no_prod_leak.py` | `TestShadowNotInPublicEnvelope` | `run_ask_pipeline_ibridge_v0` 公開 dict **無** shadow 鍵 |
| `test_monitoring_graph_shadow_diff.py` | `TestShadowProductionDiff` | match／mismatch 場景、`shadow_rule_id` 穩定 |
| `test_monitoring_graph_shadow_advisory.py` | `TestAdvisoryFieldsInternalOnly` | `advisory_use_rag` 僅內部／eval 路徑 |
| `test_monitoring_graph_shadow_trace.py` | `TestShadowTraceEvents` | log 事件含 `trace_id`、不含 `service_summary` 全文 |

**整合（升格 L1 時加跑）**

```bash
python -m unittest tests.test_context_subagent_routing tests.test_monitoring_executor tests.test_monitoring_graph tests.test_monitoring_graph_shadow_contract tests.test_monitoring_graph_shadow_fail_open -v
```

（完整清單以 runbook §6.8.9 為準。）

---

## 9. 風險與未決項

| 風險 | 緩解（設計） |
|------|----------------|
| 誤導性 shadow 建議被當 policy | 欄位命名 `shadow_*`／`advisory_*`；禁止進 prod envelope；文件標啟發式 |
| `service_summary` 外洩 | sidecar `inputs` 僅 whitelist 子集 |
| shadow 與 production 耦合 | shadow 規則獨立模組；只讀 production 快照 |
| 運維誤開 L1 | 獨立 env flag（實作票定義）；回退 → L0（§6.8.8） |

**未決**（移交實作票／§6.8.10）：

- 寫入點 A vs B 最終裁定  
- `ibridge_exporter` 與 K-2 shadow 共用與否  
- prod shadow 報備流程細節  

---

## 10. 明示不在範圍

- **L2** SLO gate／`slo_verdict` — 見 `M-GOV-L2` 錨點與 runbook §6.8.5  
- 修改 production selector／answer／主 ask LangGraph  
- 新增 Sprint 6 env flag 或 prod API 欄位  
- 自動採納 shadow／advisory 影響 retrieve 或 answer  

---

## 12. 實作方案草稿（檔案級 · 候選 · 未動碼）

> **狀態**：前置施工方案；**是否開工**取決於 §7.1 門檻 + 尚書省批文。env flag **僅 placeholder**，本 Sprint 不落地。

### 12.1 推薦寫入點：**選項 A（selector 之後 · retrieve 之前）**

**裁決（本稿）**：在 `selector_node` **末尾**呼叫純函式 `compute_monitoring_shadow_decision(state)`（不修改 `updates["_ask_use_rag"]`／`ask_selector`）。時序上等價於在 `selector_node` → `_route_after_selector` 之間插入觀測邏輯，**不**新增 LangGraph 邊（首版最小 diff）。

| 候選 | 位置 | 優點 | 缺點 |
|------|------|------|------|
| **A（推薦）** | `langgraph_flow.selector_node` 末尾；L1 flag ON 時寫 `_monitoring_shadow_decision` | production `use_rag` 已確定；與 `retrieve_node` 解耦；易單測 | selector 節點職責變長（可抽至獨立模組緩解） |
| **A′** | 新節點 `shadow_observability_node` 插在 selector 與 retrieve 之間 | Langfuse span 獨立；職責清晰 | 改 `build_ask_graph` 邊；非 ibridge 與 ibridge 路徑都要對齊 |
| **B** | `monitoring_executor`／graph finalize 內 | 與 graph 同區塊 | **時序錯**：graph 在 enrich（selector **前**）已跑；難取 production 快照；易誤耦合 |

**不採 B 的理由**：`attach_executor_result_to_init` → `_monitoring_graph_result` 發生在 `enrich_init_with_context_entry`（`run_ask_with_ibridge_v0` 在 `execute_workflow` **之前**），而 `ask_selector` 在圖內 `selector_node` 才產生（見 `gov_core_system/core/langgraph_flow.py`）。

### 12.2 欄位與資料流（實作票對照）

```
[enrich] _monitoring_executor_result, _monitoring_graph_result  (L0, 已有)
    ↓
[selector_node] ask_selector { use_rag, selector_rule_id, ... }  → production 決策
    ↓  (L1 flag ON)
[shadow] compute_monitoring_shadow_decision:
    讀: state._monitoring_graph_result, state.ask_selector
    寫: state._monitoring_shadow_decision { shadow_*, production_*, diff, advisory_* }
    ↓
[retrieve_node | answer_node] 僅讀 _ask_use_rag（production，不讀 shadow）
    ↓
[ibridge] strip 內部鍵；公開 ibridge_v0 仍僅 L0 monitoring_graph + selector_decision
```

| 輸出欄位 | 來源 |
|----------|------|
| `production_use_rag` | `ask_selector.use_rag` **快照**（唯讀） |
| `production_selector_rule_id` | `ask_selector.selector_rule_id` |
| `shadow_use_rag`／`shadow_rule_id`／`shadow_route` | `core/monitoring_shadow_selector.py` 啟發式，輸入 whitelist：`extract_monitoring_graph_public_summary(_monitoring_graph_result)` + 可選 `recommendations[0]` |
| `advisory_use_rag`／`advisory_reason`（或 `advisory_note`） | 同上模組；語意＝人工審計建議，**≠** policy |
| `diff.use_rag_match` | `shadow_use_rag === production_use_rag`（任一為 `null` → `null`） |
| `diff.route_match` | 可選；`shadow_route` vs `_subagent_route.target_agent_id`（v1 可常 `null`） |

### 12.3 建議新增／修改檔案（實作票範圍）

| 動作 | 路徑 | 說明 |
|------|------|------|
| **NEW** | `core/monitoring_shadow_selector.py` | 契約形狀、`compute_*`、fail-open、啟發式規則表；**不** import 改 production selector |
| **MOD** | `01_Environments/python_venvs/gov_core_system/core/langgraph_flow.py` | `selector_node` 末尾 gated 呼叫；**禁止**改 `_ask_use_rag` 來源 |
| **MOD** | `gov_core_system/core/ask_pipeline_ibridge_v0.py` | `_ASK_PIPELINE_INTERNAL_STATE_KEYS` 加入 `_monitoring_shadow_decision`；**不**寫入 `public["ibridge_v0"]` |
| **MOD** | `gov_core_system/app_api.py` | 確認 strip／API payload **無** shadow 鍵（與 L0 雙閘門並列審計） |
| **NEW** | `tests/test_monitoring_graph_shadow_*.py`（戰車根） | §8 六模組 |
| **MOD** | `subagents/monitoring_executor.py` | **不**寫 shadow（僅註解指向 A）；避免 B 路徑 |
| **DOC** | 本稿 + runbook §6.8.10 | 實作票關閉後更新「寫入點已裁定」 |
| **不碰** | `core/ask_rag_selector.py` | production 規則獨立；L1 只讀 `decide_use_rag` 輸出 |
| **不碰** | `core/monitoring_graph.py` | L0 graph 語意不變 |
| **不碰** | prod API envelope／`MONITORING_GRAPH_API_PUBLIC_KEYS` | L1 不擴公開鍵 |

**Env placeholder（實作票定義，本稿不新增常數）**：例如 `GOV_MONITORING_SHADOW_SELECTOR_ENABLED=1` 且建議 **與** `GOV_MONITORING_GRAPH_ENABLED=1` **與** adapter 成功 **與** monitoring 路由 **四重**與運算；關閉 → 完全不寫 `_monitoring_shadow_decision`（回到 L0）。

### 12.4 Trace／eval 整合（設計）

| 通道 | L0 | L1 shadow |
|------|-----|-----------|
| Langfuse／`log_event` | `ask_rag_selector_decision`、graph 無獨立 shadow 事件 | `monitoring_shadow_start`／`monitoring_shadow_decision`／`monitoring_shadow_skip`／`monitoring_shadow_fail`；payload 含 `shadow_level: "L1-shadow"` |
| `MetricsCollector.log_step` | selector metadata | 同上事件名 + `diff.use_rag_match` |
| 離線 eval | `ibridge_v0.selector_decision` + `monitoring_graph` | 匯出 `monitoring_shadow_decision`（扁平）join `trace_id`；**不**經預設 `/api/ask` |
| 與 K-2 | `core/k2_ask_shadow.py` 可比對 `selector_use_rag` | **未決**是否共用 exporter（§6.8.10） |

**區分 L0／L1 trace**：L0 請求可無 `monitoring_shadow_*` 事件；L1 請求必有 `shadow_level` 且**不得**出現在 `strip_ask_pipeline_internal_keys` 之外的 HTTP body。

---

## 13. L1 實作票範圍／步驟／風險（候選工單 · 未開工）

**票名（候選）**：`M-GOV-L1-IMPL` — Shadow selector／advisory **實作**（依賴：§7.1 全綠 + 尚書省批文）

| 階段 | 步驟 | 退出準則 |
|------|------|----------|
| **0 門檻** | 填 §7.1 G1–G10；L0 soak 報告 | 尚書省「可動碼」 |
| **1 核心** | `monitoring_shadow_selector.py` + `test_*_contract`／`fail_open` | shadow 形狀穩定；production 不變 |
| **2 接線** | `selector_node` gated 寫入；flag placeholder 接線 | 整合測試：match／mismatch |
| **3 防洩** | ibridge strip + `test_*_no_prod_leak` + app_api 回歸 | 公開 dict 無 shadow 鍵 |
| **4 觀測** | trace 事件 + 離線 NDJSON 匯出（dev） | 事件含 `trace_id`；無 `service_summary` 全文 |
| **5 soak** | staging 開 L1；監控 `shadow_ok_rate`、mismatch 率 | 異常 → 關 flag 回 L0（§6.8.8） |

**風險（實作票 RACI）**

| 風險 | 等級 | 緩解 |
|------|------|------|
| 運維誤以 `advisory_use_rag` 當 policy | 高 | 命名空間 + 禁止 prod envelope + 文件 |
| shadow 與 production 規則漂移 | 中 | 獨立模組 + 版本欄 `shadow_route` |
| selector 節點例外連帶 | 中 | shadow try/except 隔離；fail-open 表 §6 |
| 樣本不足升格 | 中 | §7.1 G2–G3 硬門檻 |
| 與 L2 混淆 | 高 | **禁止** `slo_verdict`；L2 另票 |

**明確不在 M-GOV-L1-IMPL**：L2 gate、改 `decide_use_rag`、prod API 新鍵、自動採納 shadow。

---

## 14. 修訂紀錄

| 日期 | 變更 |
|------|------|
| 2026-05-25 | Sprint 6 初稿：L1 shadow／advisory 設計稿（治理票；零程式碼） |
| 2026-05-25 | 前置實作票附件：§12 檔案級方案、§13 工單步驟、§7.1 門檻占位 |
