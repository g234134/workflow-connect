# Context Entry Contract（H 線 · v0.1）

> **權威實作**：`core/context_entry.py` → `build_rooted_context`  
> **底層組裝**：`context/context_builder.py` → `build_context`（禁止在入口繞過）  
> **制度模型**：`context/context_model.md`、`context/memory_routing_rules.md`

---

## 1. 目的

將「分層上下文」從部分路徑的可選調用，升級為**新入口強制遵守的上下文入口合同**，避免未來 pipeline 在程式入口手寫 `root_context` / `working_context` / `long_term_memory`，繞開 N 線裁剪與 token 預算。

---

## 2. 唯一入口函數

| 項目 | 約定 |
|------|------|
| 模組 | `core/context_entry.py` |
| 函數 | `build_rooted_context(task_input, *, mode="ask_pipeline") -> dict` |
| 內部 | 僅委派 `context.build_context`；不在此檔重寫裁剪／檢索邏輯 |

### 2.1 輸入

- `task_input`：與 `build_context` 相同語義（`task_id`、`goal`/`query`、`work_order_id` 等均可選）。
- 若缺少 `task_id` 或 `work_order_id`，入口函數**自動生成**（前綴 `task-` / `wo-` + 短 UUID）。
- `mode`：寫入 `metadata.source` / `metadata.entry_mode`，供 trace／metrics 區分管道（如 `ask_pipeline`、`k1_pipeline`）。

### 2.2 輸出（入口合同層）

除保留 `build_context` 的 `ok`、`message`、`result`、`metadata` 外，**提升**以下欄位至頂層，供圖節點與觀測直接消費：

| 欄位 | 說明 |
|------|------|
| `root_context` | 制度／禁則層（來自 `result`） |
| `subtree_context` | P0.5 子樹層（`list[dict]`）；v0.1 由入口 mock／`task_input` 覆寫，對齊 A-2 最小欄位 |
| `working_context` | 本輪任務／對話／工具結果 |
| `long_term_memory` | semantic + structured 檢索摘要 |
| `token_usage` | 含 `root` / `working` / `memory` / `total` / **`total_tokens`**（與 `total` 同值） |
| `task_input` | 補齊 ID 後的規範化輸入 |
| `metadata.entry` | 固定 `"context_entry"` |
| `metadata.source` | 與 `mode` 一致 |
| `metadata.deny` | v0.1 最小 deny 閘結果（Sprint 1 A'-2）；見 §2.4 |
| `metadata.trim` | P0.5 子樹裁剪稽核（Sprint 2 R-2）；見 §2.5 |
| `metadata.navigation_map` | Sprint 2 R-1 nav auto v0.1；見 §2.5 |
| `metadata.navigation_map_version` | 固定 `"v0.1"`（nav auto 世代標記） |

`result` 內仍含 `assembled_text` 等，與 v0.1 `build_context` 向後相容；`result.subtree_context` 與頂層同值（入口層組裝，非 `context_builder` 核心）；`result.navigation_map` 與 `metadata.navigation_map` 同值。

### 2.5 `navigation_map`（v0.1 · Sprint 2 R-1）

| 項目 | 約定 |
|------|------|
| 位置 | `metadata.navigation_map` 與 `result.navigation_map`（同值） |
| 產生 | `task_input` 無 `navigation_map` 時，由 A-4 §8 模板 + `subtree_context` 自動生成；有部分輸入時**僅補缺**，不覆蓋使用者已給鍵 |
| 覆寫 | `task_input.navigation_map`；`active_path`／`nodes` 內已存在鍵視為使用者指定 |
| 必填鍵（頂層） | `version`、`nav_map_ref`、`active_path`、`nodes`、`subtree_to_node`、`source` |
| `active_path` | 有序 `node_id` 列表；最小路徑為 `root` → 活躍 subtree 節點 |
| `nodes` | `node_id` → 節點 dict（含 `type`、`entry_refs`；subtree 含 `subtree_id`） |
| `subtree_to_node` | `subtree_id` → `node_id`（關聯 A-2 子樹） |
| 非目標 | 全自動 nav tree、獨立 nav map 檔案產出、與 builder `root_context.navigation` 強制一致 lint |

### 2.4 Deny gates（v0.1 · Sprint 1 A'-2 · deny engine v1 · Sprint 3 R-3a–c）

| 項目 | 約定 |
|------|------|
| 位置 | `build_rooted_context` 內：**Gate-1** 呼叫 `build_context` 前；**Gate-2** 組裝後；**Gate-3** P0.5 trim／nav 後對 active subtree 聯集掃描 |
| 引擎 | `context/deny_rules.py` — `GateRunner` + `CONTENT_RULE_TABLE` / `ACTION_RULE_TABLE` |
| 規則表版本 | `RULE_TABLE_VERSION` = `deny-rules-v0.3-r3def`（寫入 `metadata.deny.observability.rule_table_version`） |
| 命中時 | `ok: false`；`message` 含 `context denied (<gate>): <deny_types>`；三層清空；`metadata.deny.denied` == `true` |
| `metadata.deny` 鍵 | `denied`、`gate`（`pre_injection` \| `post_assembly` \| `subtree`）、`phase`（`P0` \| `P1` \| `P0.5`）、`deny_types`（類型代號列表）、`detail` |
| `metadata.deny.subtree` | **subtree gate 命中或 union 審計**：`active_subtree_ids`、`deny_union`（`forbidden_content_types`／`forbidden_action_types`／`scope_constraints`） |
| `metadata.deny.action_audit` | Z-* action 骨架命中時：`[{ deny_type, z_type, skeleton, detail }]`（**非**運行時授權器） |
| `metadata.deny.observability` | `deny_total_count`、`deny_types_hist`、`phase_hist`（pre/post/**subtree**）、`events[]`；預設啟用，`GOV_CONTEXT_DENY_OBSERVABILITY=0` 可關 |
| 未命中 | `metadata.deny.denied` == `false`；`deny_types` == `[]`；happy path 仍附 cleared observability |
| 已支援類型（最小集） | **Content 7/7**（A-3 §5.1 表行，不含 post 衍生）：含 `full_cli_trace`；**post 衍生**：`rag_hit_with_secrets`。**Action 4/8**（§5.2）：含 `unauthorized_z_env_edit`、`unauthorized_z_runtime_cp`（骨架） |
| 非目標 | Z-* **運行時授權器**（制度停工線）；A-3 其餘 action（Telegram／hashes／dark_ops 等）見 `30_ignore_deny_rules.md` §7 |

### 2.3 `subtree_context`（v0.1 · Sprint 1 A'-1）

| 項目 | 約定 |
|------|------|
| 形狀 | `list[dict]`，建議 0～2 棵 `active: true`（A-2 §7） |
| 必填鍵（每棵） | `subtree_id`、`mount_type`、`scope_label`、`active`、`entry_refs` |
| 預設 | 無 `task_input.subtrees`／`subtree_id` 時，mock 一棵 `line.a.context-entry` |
| 覆寫 | `task_input.subtrees[]`，或 `subtree_id`／`subtree_mount_type`／`subtree_scope_label`／`subtree_entry_refs`／`subtree_active` |
| 非目標 | nav map **檔案**自動產出；deny 合併／子樹聯集見 §2.4（僅入口最小閘） |

### 2.5 `metadata.trim`（P0.5 · Sprint 2 R-2）

| 項目 | 約定 |
|------|------|
| 位置 | `build_rooted_context` 成功路徑；**deny 命中時不寫入**（deny ＞ trimming） |
| 觸發 | `subtree_context` 組裝後、寫入 `result` 前 |
| 不裁剪 | `root_context`／`hard_rules`；不改 `subtree_id` 等身份鍵 |
| `version` | `p0.5-v0.1` |
| `applied` | 本輪是否有任一 trim 決策 |
| `trims[]` | `{ subtree_id, trimmed_entries, reason, detail? }` |
| `reason` 示例 | `active_subtree_cap`、`entry_refs_cap`、`runbook_digest_cap`、`handoff_digest_cap`、`subtree_token_budget` |
| `token_estimate` | `{ before, after, budget }`（heuristic：`len(text)//4`） |
| 預設上限 | 活躍子樹 ≤2；每棵 `entry_refs` ≤3；子樹層合計 heuristic ≤8000 tokens |

---

## 3. 哪些入口必須使用

以下類型**新建**時必須呼叫 `build_rooted_context`，不得直接 `build_context` 後再手拼三層，更不得在入口複製 `_load_root_context` 等 builder 私有邏輯：

| 入口類型 | 說明 | 建議 `mode` |
|----------|------|-------------|
| 對外 API / CLI ask 類 | 用戶問答、檢索增強生成 | `ask_pipeline` |
| LangGraph / 多 Agent 長任務 | K-1 及後續編排圖首節點 | `k1_pipeline` |
| 新 HTTP 路由 handler（規劃中） | app 層僅轉發，上下文在 core 入口組裝 | `api_entry` |
| 長任務 / 批次編排 | 跨步驟共用 root，按輪次刷新 working | `long_task` |

### 3.1 既有路徑（v0.1）

| 路徑 | v0.1 狀態 |
|------|-----------|
| `core/langgraph_flow_k1.py` | **已對齊** `build_rooted_context`（示範） |
| `gov_core_system` ask I-bridge-v0 | **已對齊** `build_rooted_context(..., mode="ask_pipeline")`（I-bridge-v0-H-migrate） |
| `gov_core_system` ask 預設路徑（非 ibridge） | **已對齊** `build_rooted_context(..., mode="ask_pipeline")`（H-historical-migrate）；`run_ask_with_hline_context` |
| 歷史生產路徑 | 不要求本票一次性替換；遷移須單開工單 |

**預設 ask 回退（暫時）**：僅 dev/test 可設 `GOV_CORE_ASK_HLINE_CONTEXT_FALLBACK=1`；H 線 import／組裝失敗時跳過 context 注入（生產預設關閉）。

---

## 4. 禁止繞過（Hard Rules）

1. **禁止**在 pipeline 入口、API handler、LangGraph 首節點內手寫或 `json.dumps` 拼接 `root_context` / `working_context` / `long_term_memory` 三層結構。  
2. **禁止**為繞過 token 預算而跳過 `build_context`（含複製 builder 內 mock 檢索函數）。  
3. **禁止**修改 `build_context` 簽名以適配新入口；擴展走 `task_input` 鍵或 `metadata` 掛載。  
4. **允許**在 `build_rooted_context` 返回後，向 `task_input` 或 `working_context.task_input` **追加**工單欄位（不得替換整層 root）。  
5. **允許**下游節點只讀 `context_payload["result"]` 舊形狀；新程式應優先讀頂層三層 + `token_usage`。

違反時：Code Review / Work Report 標記 **H-line bypass**；須在 Progress 末尾留痕並補對齊。

---

## 5. 與工程合約、接戰守則的關係

- `04_Workflows/ENGINEERING_CONTRACT.md` 附錄 D（H 線）  
- `AGENTS.md`「一致上下文入口」小節  

衝突位階：尚書省指令 ＞ 憲法 ＞ 工程合約 ＞ 本合同 ＞ 模組 `brief.md`。

---

## 6. 驗收（本模組）

```bash
python -m unittest tests.test_context_entry -v
python -m unittest tests.test_ask_selector_and_answer -v
```

可選：K-1 煙測仍通過 `python -m unittest tests.test_langgraph_flow_k1 -v`（入口已對齊）。

---

## 7. 非目標（v0.1）

- 不改 `context_builder.py` 核心裁剪／mock 檢索。  
- 不替換 `app_api` HTTP 路由行為。  
- 不要求一次遷移所有歷史 `build_context` 呼叫點。  
- `subtree_context` P0.5 裁剪為 **heuristic v0.1**（見 §2.5）；非 tiktoken 精算。  
- deny：**deny engine v1**（§2.4 · `GateRunner` 三閘 + 規則表）；非 `context_builder` 政策引擎；A-3 全表 coverage 仍部分 TODO（action 4/8）。  
- `navigation_map`：**僅** 最小 JSON 結構（§2.5），不寫入 repo 內 nav 實例檔。

---

## 8. Ask RAG selector 與无 context 场景

### 8.0 切換狀態（H-historical-migrate · 2026-05-25）

| 項目 | 狀態 |
|------|------|
| **預設 ask**（`ibridge_v0=False`） | **已切換** — `run_ask_with_hline_context` → `build_rooted_context(..., mode="ask_pipeline")` → `_context_entry_payload` |
| **opt-in ibridge** | **已切換**（I-bridge-v0-H-migrate）— 同上 + `agent_run_trace` / `ibridge_record` |
| **生產 H-line bypass** | **已清零** — 僅 dev/test 可設 `GOV_CORE_ASK_HLINE_CONTEXT_FALLBACK=1` |
| **HTTP `/api/ask` 契約** | 不變 — 回應仍不含 `ibridge_record`（除非 dev 雙閘門） |

H 線 context 與 ask RAG selector 分工：

| 層 | 職責 |
|----|------|
| **H 線** `build_rooted_context` | 組裝 `root_context` / `working_context` / `long_term_memory`；提供 KB 信號（`context_refs`、semantic memory） |
| **Ask selector** `decide_use_rag` | 讀 query + H-line payload，決定是否執行 `retrieve_node` |

### 8.1 场景预期（S1–S3）

| 场景 | Context | Selector | 回答侧 |
|------|---------|----------|--------|
| **S1** 知识库问题 | 有 `context_refs` / semantic memory | `use_rag=true` (ASK-R4/R5) | `skill_answer_for_ask` + RAG |
| **S2** 问候 / 无检索 | 可无 H-line payload | `use_rag=false` (ASK-R2/R3) | 跳过 retrieve；`perform_direct_answer` + answer skill |
| **S3** Retrieve 失败 | 任意 | 已选 RAG | retrieve 失败后 `direct_fallback`；answer 带 `retrieve_fallback` / `retrieve_error_type` |

### 8.2 回归测试

- `tests/test_context_entry.py` — H 線入口合同
- `tests/test_ask_selector_and_answer.py` — selector 单元 + ask 流程 S1–S3（與 `test_context_entry` 分開跑，避免 `core` 包遮蔽）
- `gov_core_system/tests/test_ask_pipeline_default_context.py` — 預設 ask H 注入 + fallback env
- `tests/test_skills_ask_wire.py` — answer/retrieve skill 单元
- `gov_core_system/tests/test_ask_skills_wire_e2e.py` — 含 `selector_node` 的 E2E

### 8.3 H-line fallback 与 selector

`GOV_CORE_ASK_HLINE_CONTEXT_FALLBACK=1`（dev/test）时 H 线失败可不注入 context；selector 仍运行，短问候走 ASK-R2 跳过 RAG。无 context 的长知识问题走 ASK-R5/R6 使用 RAG。

### 8.4 Answer metrics 与 eval 视野

answer 步经 `skill_answer_for_ask` 写入与 retrieve 相同的 M-line 字段（`external_call_count`、`retry_count`、`call_site`）。  
`eval_exporter` / `eval_ci_check` 消费 `ibridge_record` 时，answer 步 metrics 与 selector 决策（`selector_decision`、`retrieve_fallback`）一并进入 eval / CI 分析视野（详见 `observability/eval_pipeline.md` §6.5）。

---
