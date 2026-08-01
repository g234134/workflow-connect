# A5 — Context Entry Runbook（Sprint 0 · 操作手冊）

| 項目 | 值 |
|------|-----|
| **票號** | A-5 |
| **版本** | v0.1 |
| **狀態** | 治理層 runbook（整合 A0–A4；不取代執行期合同） |
| **權威邊界** | 執行期以 `context/context_entry_contract.md` + `core/context_entry.py` 為準 |
| **上游** | `A0_context_entry_overview.md`、`A1_root_context_spec.md`、`A2_subtree_context_spec.md`、`30_ignore_deny_rules.md`、`40_navigation_map_template.md` |
| **下游** | A-6（隊列回寫）；B/C/D/E 線（Sprint 0 後）；deny 擴面票（subtree gate / Z-* action，另開） |

---

## 1. 目的與範圍

### 1.1 本 runbook 是什麼

本檔是 **給人類與後續代理看的操作手冊**：把 A 線已完成的治理規格（root／subtree／ignore-deny／navigation）收斂成「誰在什麼情境下該做什麼」，並與戰車根 **H 線**（`build_rooted_context`）對賬。

- **是**：接戰必讀順序、組裝語意、驗收自檢、風險與未實作邊界。  
- **不是**：程式 API 參考、合同全文複製、Phase 10.5 路由表改寫。

### 1.2 Context Entry 在整體 workflow 中的角色

| 層 | 職責 | 產物 |
|----|------|------|
| **執行期（H 線）** | 新入口**唯一**組裝上下文；輸出三層 + `token_usage` | `core/context_entry.py`、`context/context_entry_contract.md` |
| **治理期（A 線 · Sprint 0）** | 規定各層載什麼、誰可改、deny／ignore、導航與派工 | `workflow_upgrade/01_context-entry/` |
| **下游 ask 圖（Phase 10.5）** | selector → retrieve → answer；消費 H 線 payload | `skills/skills_contract.md` §10.5（**只讀**） |

**一句話**：Context Entry 是 **所有 ask-like／長任務編排的上游上下文閘**；沒有合法入口組裝，下游 RAG 與回答節點不應自行發明 `root_context`／`working_context`／`long_term_memory`。

### 1.3 本 runbook 適用誰

| 角色 | 何時使用本檔 |
|------|----------------|
| **尚書省／HQ Coordinator** | 派 A 線票、審 runbook 與隊列對帳 |
| **新 chat 副官（接戰）** | 確認必讀檔、nav map 節點、禁區類型 |
| **施工 worker** | 改入口或驗收 H 線前，對照 §4–§8 |
| **實作 agent（另開票）** | 將治理片段映射進 builder 時，以 §9 缺口為邊界 |

### 1.4 範圍外（本 runbook 不涵蓋）

- 改 `core/`、`context/context_builder.py`、hooks、connector、dashboard（須單開實作票）。  
- 撰寫 B/C/D/E 線正文。  
- 自動產出 navigation map 檔案（**v0.1 未實作**，見 §9）。頂層 `subtree_context`：**v0.1 已實作（mock）**，見 §5.2／§9。

---

## 2. 必讀檔案清單

### 2.1 接任一張 Context Entry 相關票（通用）

| 順序 | 邏輯路徑 | 讀什麼 |
|------|----------|--------|
| 1 | `workflow_upgrade/90_run_queue.md` | 票號、Status、Depends on、Output File |
| 2 | `workflow_upgrade/01_context-entry/A0_context_entry_overview.md` | A 線總覽、權威位階、與 H 線對應 |
| 3 | `workflow_upgrade/00_master_plan.md` | Sprint 0 邊界、F/A 分工、Phase 10.5 關聯 |
| 4 | `AGENTS.md` | 接戰九步、紅線、**一致上下文入口**（禁止手拼三層） |
| 5 | `context/context_entry_contract.md` | 唯一入口、輸出形狀、禁止繞過、場景 S1–S3 |
| 6 | `core/context_entry.py` | `build_rooted_context` 簽名、`_ENTRY_MODES`、提升欄位（**只讀**，除非實作票） |
| 7 | `context/context_model.md` | 三層定義、裁剪優先級 P0–P7、memory 雙庫語意 |

### 2.2 按情境加讀（A0–A4）

| 情境 | 加讀 |
|------|------|
| 定義／維護 root | `A1_root_context_spec.md` |
| 子樹掛載、接力 | `A2_subtree_context_spec.md` |
| 裁剪 vs 禁止寫入 | `30_ignore_deny_rules.md` |
| 接戰導航、隊列對帳 | `40_navigation_map_template.md` |
| 本輪施工與驗收 | **本檔** `50_context_entry_runbook.md` |

### 2.3 涉 ask 全鏈時（只讀）

| 路徑 | 用途 |
|------|------|
| `skills/skills_contract.md` §10.5 | 圖路由 `health → selector → …`；**不改寫** |
| `context/context_entry_contract.md` §8 | S1–S3 與 selector 分工 |
| `04_Workflows/HARNESS_CONSTITUTION.md` §7 | 禁區**類型**（不抄實例路徑） |

### 2.4 權威位階（衝突時）

尚書省指令 ＞ 憲法 ＞ 工程合約（含附錄 D）＞ `context_entry_contract.md` ＞ **workflow_upgrade A 線 spec（含本 runbook）** ＞ 模組 `brief.md`。

---

## 3. 常見場景

### 3.1 場景 A — 新任務接戰（Boot）

**誰**：新開 chat 的大唐副官或 HQ worker。  
**情境**：尚書省口令「接戰」或派 `90_run_queue` 某一 A 線票。

| 步驟 | 動作 |
|------|------|
| 1 | 完成 `AGENTS.md` 初始化校準（憲法／合約／Conditions／Progress 等）。 |
| 2 | 查 `90_run_queue.md`：確認票號、`Line`、`Status`；若施工則改 `DOING`。 |
| 3 | 依 §5.1 走 **Navigation Map**：先 `root` 節點 `entry_refs`，再活躍 `subtree`（如 `line.a.context-entry`）。 |
| 4 | 閱讀任務卡 Output File 與 A1–A4 中與本票相關章節。 |
| 5 | **若本輪會調 LLM／跑 ask**：心智模型上應經 `build_rooted_context`；文檔票可不實際呼叫。 |
| 6 | 在 Progress **末尾**記阻塞／下一步；勿改寫 Conditions／Progress 既有段。 |

**成功標誌**：能說清角色、可碰範圍、禁區類型、本票 Output；未手拼三層 context。

### 3.2 場景 B — 長任務續戰（跨 chat／跨步）

**誰**：同一 `task_id` 或隊列上連續票的 agent。  
**情境**：LangGraph 多步、Sprint 0 多張 A 線票接力。

| 步驟 | 動作 |
|------|------|
| 1 | 從 `handoff_digest`（subtree 治理欄位）或 Progress 末尾讀上一輪要點。 |
| 2 | **每輪**若組裝 prompt：重新呼叫 `build_rooted_context`（`mode` 見 §4.2）；**不假設** session 仍記得 root。 |
| 3 | 刷新 `working_context`（本輪 query、tool 結果）；`long_term_memory` 隨檢索更新。 |
| 4 | root 制度摘要僅在 Governance 變更時更新；單票結論寫 working／戰報，**不寫入 root**。 |
| 5 | 活躍 subtree ≤2（A-2 §7）；其餘標 `inactive`。 |

### 3.3 場景 C — Debug／調查（上下文相關）

**誰**：排查 ask 未走 RAG、token 爆掉、疑似 H-line bypass 的 agent。  
**情境**：selector 行為異常、assembled 含敏感類內容、unittest 失敗。

| 步驟 | 動作 |
|------|------|
| 1 | 確認入口是否為 `build_rooted_context`（非手拼三層、非跳過 `build_context`）。 |
| 2 | 檢查回傳：`ok`、`message`、`metadata.entry`=`context_entry`、`token_usage`、`trimming_applied`（在 `result`／metadata 內）。 |
| 3 | 對照合同 §8.1：**S1** 應有 KB 信號；**S2** 可無 payload；**S3** retrieve 失敗仍有 answer fallback。 |
| 4 | 用 §6 deny 清單掃描 tool 輸出／handoff 是否含禁止**類型**。 |
| 5 | 跑 §8 驗收命令；失敗則標阻塞，**不得**宣稱 H 線已修復。 |
| 6 | 觸及憲法 §7 硬禁區 → 停工，Progress 末尾留痕。 |

### 3.4 場景 D — 僅文檔／規格施工（Sprint 0 常態）

**誰**：A-0～A-5 類 worker。  
**情境**：只改 `workflow_upgrade/`，不動 production code。

- 以 nav map + 隊列定位必讀檔即可開工。  
- 驗收以 §8.1 檔案與章節自檢為主，**不強制**跑 unittest（除非尚書省要求對賬 H 線）。

### 3.5 場景 O-2 — monitoring subagent（`signal_only` · Sprint 4）

**誰**：排查 ask 是否應附帶監控 KPI 側車、或 ibridge 回傳中 `monitoring_executor` 異常的 agent。  
**情境**：使用者 goal／query 含 monitoring／overview／dashboard-summary 等；**不**走 HQ `_route_task.py` 派工。

| 步驟 | 動作 |
|------|------|
| 1 | `build_rooted_context(..., mode="ask_pipeline")`（禁止手拼三層）。 |
| 2 | **C-1**：`attach_subagent_route_to_context` → 檢查 `metadata.subagent_route`：`target_agent_id`、`rule_id`（`ROUTE-MON-1`）、`signal_only=true`。 |
| 3 | **O-2a**：`enrich_init_with_context_entry` → 若為 monitoring 路由，預寫 `_monitoring_executor_result`（只讀 `monitoring_service`；失敗則 stub）。 |
| 4 | **下游不變**：selector → retrieve? → answer；monitoring **不**改 `use_rag` 或圖邊。 |
| 5 | **O-2b（ibridge）**：公開欄位 `ibridge_v0.subagent_route` + `ibridge_v0.monitoring_executor`（內部 `_monitoring_executor_result` 已剝離）。 |

**時序（文字）**：

```text
task_input → build_rooted_context → C-1 subagent_route (signal_only)
  → O-2a maybe_run_monitoring_executor (pre-graph, read-only)
  → LangGraph ask (selector / retrieve / answer 不變)
  → ibridge_v0 摘要 subagent_route + monitoring_executor
```

**非 monitoring 路由**：`monitoring_executor.executed=false`、`noop=true`；勿解讀為 monitoring API 故障。

---

## 4. 執行流程（接戰 → build_rooted_context → ask_pipeline → 驗收）

### 4.1 總覽（文字流程）

```
尚書省指令 / 任務卡
  → [治理] 90_run_queue + nav map（§7）+ A0–A4 必讀
  → [治理] 確認無 H-line bypass 設計
  → [執行] build_rooted_context(task_input, mode=...)
  → [執行] build_context 內部：root → working → memory → trim（ignore）
  → [下游] ask：selector(decide_use_rag) → [retrieve] → answer
  → [驗收] unittest + 欄位斷言 + Work Report
  → [治理] 隊列 DONE / Progress 末尾戰報
```

### 4.2 步驟 1 — 接戰與派工（治理）

| # | 誰 | 做什麼 |
|---|-----|--------|
| 1 | Coordinator | 在 `90_run_queue.md` 指派票號、標 `DOING`。 |
| 2 | Worker | 依 §2、§7 讀 root + 活躍 subtree 的 `entry_refs`。 |
| 3 | Worker | 宣告可碰／不可碰（對齊 A-2 `scope_constraints` 與任務卡）。 |
| 4 | 全員 | 確認本輪若動入口，已有實作票授權；Sprint 0 文檔票 **禁止** 改 `core/`。 |

### 4.3 步驟 2 — 組裝 task_input（執行期）

| # | 誰 | 做什麼 |
|---|-----|--------|
| 1 | 入口程式 | 構造 `task_input` dict：`goal` 或 `query`、`task_id`、`work_order_id`（可省略，入口自動補）。 |
| 2 | 入口程式 | 選 `mode`：`ask_pipeline`（預設 ask）、`k1_pipeline`、`k2_pipeline`、`api_entry`、`long_task`。 |
| 3 | 入口程式 | **禁止** 在 task_input 內預填完整三層 context 取代 builder。 |
| 4 | 治理審查 | GateRunner **pre_injection** 已自動執行；Reviewer 仍須對照 §6 人工複核高風險注入。 |

### 4.4 步驟 3 — build_rooted_context（執行期）

| # | 誰 | 做什麼 |
|---|-----|--------|
| 1 | 入口 | 呼叫 `build_rooted_context(task_input, mode=...)`（戰車根 `core/context_entry.py`）。 |
| 2 | 入口 | 讀取頂層：`ok`、`message`、`root_context`、`working_context`、`long_term_memory`、`token_usage`、`task_input`、`metadata`。 |
| 3 | 入口 | 確認 `metadata.entry` == `"context_entry"`，`metadata.source` 與 mode 一致。 |
| 4 | 入口 | 若 `ok` 為 false：依 Rule 9 回傳 message，**不得**假裝三層已就緒。 |
| 5 | 允許 | 返回後向 `task_input` 或 `working_context` **追加**欄位；**禁止**替換整層 `root_context`。 |

**暗部執行注意**：unittest／煙測在戰車根 venv 執行；路徑索引見 `Master_Map.json` → `runners`，本檔不寫死磁碟路徑。

### 4.5 步驟 4 — 進入 ask_pipeline（下游）

| # | 誰 | 做什麼 |
|---|-----|--------|
| 1 | Ask 編排 | 將 H 線 payload 交給 selector（`decide_use_rag`）：讀 query + `context_refs`／semantic memory。 |
| 2 | Selector | **S1**：有 KB 信號 → `use_rag=true` → retrieve → answer。 |
| 3 | Selector | **S2**：問候／無檢索需求 → `use_rag=false` → 直接 answer。 |
| 4 | Selector | **S3**：已選 RAG 但 retrieve 失敗 → direct_fallback，answer 帶 fallback 欄位。 |
| 5 | 全員 | **不改** `skills/skills_contract.md` §10.5 路由表；僅確保上游欄位不違反 §6 deny。 |

### 4.6 步驟 5 — 驗收與收兵（治理 + 執行）

| # | 誰 | 做什麼 |
|---|-----|--------|
| 1 | Worker | 執行 §8 命令與欄位檢查。 |
| 2 | Worker | Work Report 區分 skeleton／placeholder／阻塞（工程合約 Rule 7）。 |
| 3 | Worker | `90_run_queue`：`DOING` → `DONE`，更新 Notes。 |
| 4 | Worker | 依 `AGENTS.md` 封存協議 append Progress（僅末尾）。 |

---

## 5. 四層上下文：實際操作（root / subtree / working / memory）

> **v0.1 執行期**：`build_rooted_context` 頂層輸出 **root / subtree_context / working / long_term_memory** 四鍵；`subtree_context` 為 **v0.1 mock**（Sprint 1 A'-1）；P0.5 裁剪（R-2）與 **deny engine v1**（R-3a–c）已上線；**subtree deny 聯集**仍 TODO。

### 5.1 root_context（制度層 · P0）

| 動作 | 誰 | 怎麼做 |
|------|-----|--------|
| **填寫** | Governance／制度票 | 維護 A-1 類型：`identity`、`hard_rules`、`governance_digest`、`navigation`、`provenance`；用**摘要** + 邏輯名，非全文。 |
| **更新** | Governance | 觸發：憲法／合約／AGENTS 紅線變更 → bump `root_version`／`source_manifest`（A-1 §7 R1–R2）。 |
| **檢查** | 任何 agent | 接戰時確認含禁區**類型**、入口合同引用；無 `.env` 原文、無實例磁碟路徑、無單票 goal。 |
| **禁止** | Worker | 不得把本輪測試輸出、tool 原文、RAG hits 寫入 root。 |

**執行期對賬**：`build_rooted_context` 回傳的 `root_context` 目前多為 builder mock（如 `red_lines_summary`）；**不等同** A-1 全套 `hard_rules` 表已自動灌入。

### 5.2 subtree_context（子樹層 · P0.5 · 治理優先）

| 動作 | 誰 | 怎麼做 |
|------|-----|--------|
| **建立** | 線負責人／Governance | 滿足 A-2 §6（≥3 次 task、專屬 runbook、需明示部門邊界等）時，定 `subtree_id`、`mount_type`、`scope_label`。 |
| **填寫** | 線負責人 | `entry_refs`（3～7）、`runbook_digest`、`handoff_digest`、`scope_constraints`（只嚴不寬）。 |
| **更新** | 線負責人 | 票 DONE 後更新 `handoff_digest`；合併重疊子樹（A-2 §7 N5–N7）。 |
| **檢查** | 接戰 agent | 讀 nav map 中 `active_default=true` 的節點；確認 `entry_refs` 與隊列 Output File 一致（§7.3）。 |
| **執行期** | `build_rooted_context` | **v0.1 已實作**：頂層 `subtree_context`（`list[dict]`）；預設 mock `line.a.context-entry`；可經 `task_input.subtrees` 覆寫。**已實作**：P0.5 heuristic trim（R-2）。**TODO**：subtree deny 聯集、nav map 檔案自動產出。 |

### 5.3 working_context（工作層 · P1–P2、P5–P7）

| 動作 | 誰 | 怎麼做 |
|------|-----|--------|
| **填寫** | 執行 agent | 本輪 `goal`／`query`、`task_input`、tool 結果、最近對話、handoff 快照、scratch。 |
| **更新** | 執行 agent | 每輪覆寫／追加本輪欄位；跨步時由 `build_rooted_context` 重新組裝。 |
| **檢查** | Reviewer | 無 deny 類內容（§6）；超長附件應被 **ignore** 截斷而非刪禁則。 |
| **禁止** | 全員 | 不得以 working 覆寫 root／subtree 禁則類型。 |

### 5.4 long_term_memory（長期記憶 · P3–P4）

| 動作 | 誰 | 怎麼做 |
|------|-----|--------|
| **填寫** | builder／檢索層 | semantic hits + structured rows（v0.1 多為 mock）。 |
| **更新** | 檢索／ingest 票 | 依 `memory_routing_rules.md` 分流寫入；進 prompt 前再走 **GateRunner post_assembly**（§6.3）。 |
| **檢查** | Reviewer | hits 不含 `env_secret_plaintext` 等（A-3 §5.1）；低分 hit 可被 **ignore** 裁掉。 |
| **下游** | Selector | 消費 KB 信號決定 S1；無 payload 時可能走 S2。 |

### 5.5 組裝順序（治理語意 · 全層）

```
root（P0）→ subtree[]（P0.5，0～2 活躍）→ working（P1–P2）→ long_term_memory（P3–P4）
→ deny 掃描（⑤ · GateRunner `post_assembly`）→ ignore 裁剪（⑥，TRIM_PRIORITY）
```

與 A-3 §6.1 一致；步驟 ①⑤ 由 **deny engine v1** 自動化；③ subtree 聯集仍 TODO（§9.1）。

---

## 6. ignore / deny 的操作化

> 細則見 `30_ignore_deny_rules.md`；本節為 **實務檢查清單**。

### 6.1 先分清兩件事

| | Deny | Ignore |
|---|------|--------|
| **問題** | 這內容能進 prompt 嗎？ | token 夠嗎？ |
| **答案** | 命中則**絕對不行** | 可以丟，但要留痕 |
| **例子** | API key 原文、憲法全文貼進 handoff | 舊對話輪次、低分 RAG chunk |

### 6.2 組裝前（Deny 注入前閘 · 步驟 ①）

**誰**：`GateRunner` · `pre_injection`（自動）+ Reviewer（高風險複核）。

- [x] `build_rooted_context` 在 `build_context` 前執行 pre 閘（ContentRuleTable + ActionRuleTable）。  
- [x] `task_input` 含 `full_cli_trace` 特徵時 pre 閘可攔截（R-3e）。  
- [ ] 未規劃 **H-line bypass**（手拼三層、跳過 `build_context`）— 命中 `hand_assemble_*` / `hline_bypass_trim` 時 `ok: false`。  
- [x] 若任務卡限定 subtree：`GateRunner` · `subtree` 合併 `scope_constraints` 聯集（R-3d）；仍須人工複核邊界。  
- [x] Z-* action 骨架（如 `_z_env_edit`）pre 閘可 deny 並留 `action_audit`（**非**授權器）。

### 6.3 組裝後（Deny 掃描 ⑤ + Ignore 裁剪 ⑥）

**誰**：跑完 `build_rooted_context` 後的驗收者。

- [x] **GateRunner** · `post_assembly` 已掃描三層 + `assembled_text`；命中時追加 `rag_hit_with_secrets` 衍生標籤。  
- [x] **GateRunner** · `subtree`（P0.5）已掃描 active subtree + deny 聯集（R-3d）。  
- [ ] 查看 `token_usage`：`root`／`working`／`memory`／`total`／`total_tokens` 合理。  
- [ ] 查看 `metadata.deny.observability`（若啟用）：`deny_types_hist`、`phase_hist`（pre/post/subtree）。  
- [ ] 若有 `trimming_applied`：記錄被 **ignore** 裁掉的區塊（非 deny）。  
- [ ] root 禁則摘要未被裁至低於最小保留（P0；違反則標阻塞，不可用 ignore 替代）。  
- [ ] 仍超預算：**不得**用 ignore 塞入 deny 類內容；應降級或阻塞。

### 6.4 各層快速參照

| 層 | Deny 重點 | Ignore 重點 |
|----|-----------|-------------|
| root | 禁則條目不裁 | 壓縮非禁則 digest |
| subtree | 繼承 root；只追加更嚴 | 壓縮 runbook／handoff 過長 |
| working | 攔截 tool 中的秘密 | 裁舊對話、冗長 tool、scratch |
| memory | 路由拒絕禁止寫入類型 | 裁低分 hits／非關鍵 rows |

### 6.5 Policy coverage 自查（R-3f · debug）

**誰**：尚書省／H 線 Reviewer；**不改**運行期 deny 行為。

1. Python REPL 或 debug 腳本：

```python
from context.deny_rules import summarize_deny_policy, list_builtin_deny_rules

print(summarize_deny_policy())
print(list_builtin_deny_rules())
```

2. 輸出解讀：
   - `content.coverage` / `action.coverage`：對 A-3 §5 表行的實作比例（content 不含 post 衍生 `rag_hit_with_secrets`）。
   - `missing_from_a3`：spec 有、表內尚無的 id。
   - `z_action_skeletons`：已上線的 Z-* **偵測骨架**（非授權器）。
   - `registered_gates`：含 `subtree` 表示 R-3d gate 已啟用。

3. 可選 hook 日誌：`GOV_CONTEXT_DENY_POLICY_DEBUG=1` 且 `GOV_CONTEXT_ENTRY_HOOKS=1` 時，post-hook 會 log coverage 摘要（預設關閉）。

### 6.6 Work Report 怎麼寫

- 明確列出：被 **deny** 攔截的**類型代號**（非原文）；可引用 `metadata.deny.deny_types` 與 `observability`。  
- 明確列出：被 **ignore** 裁掉的**區塊語意**（如「第 1–3 輪對話」）。  
- 禁止把 **Z-* 運行時授權器** 或尚未實作的 action 規則寫成「已自動攔截」；subtree gate／`full_cli_trace`／Z-* 骨架已上線者須標 gate 名。

### 6.7 Monitoring subagent 除錯與審計（O-2 · 只讀側車）

**誰**：驗收 ibridge／預設 ask H 線、或對賬 Wave 1 monitoring KPI 是否被「誤當成」HQ 派工。

| 檢查點 | 期望 | 常見誤判 |
|--------|------|----------|
| **路由來源** | `metadata.subagent_route`（C-1）或 init `_subagent_route` | 用 `_route_task.py --type dark.infra` 不代表已跑 monitoring executor |
| **`signal_only`** | 應為 `true` | 以為已派 DarkOps／Infra worker 施工 |
| **`monitoring_executor.monitoring`** | 僅 monitoring 路由為 `true` | 一般問候（S2）應為 `false`／`noop` |
| **`executor`** | `monitoring-service-adapter`＝真讀 `core.monitoring_service` | `v0.1-stub`＋`fallback`＝adapter 失敗回退，**非**「未實作 O-2a」 |
| **`service_query`** | `get_overview`／`get_dashboard_summary` 等（見 executor 解析規則） | 與 RAG `use_rag` 無對應關係 |
| **內部鍵** | Graph init 可有 `_monitoring_executor_result`、可選 `_monitoring_graph_result`；公開 API 應已剝離 | 把 sidecar 當最終 user answer |
| **`monitoring_graph`（M-3）** | 僅 `GOV_MONITORING_GRAPH_ENABLED=1` 且 adapter 成功時出現在 `ibridge_v0` | flag OFF 時欄位不存在；**不**表示 executor 故障 |

**讀取順序（ibridge v0）**：

1. `ibridge_v0.subagent_route` → 是否 `target_agent_id=monitoring_subagent`、`rule_id=ROUTE-MON-1`。  
2. `ibridge_v0.monitoring_executor` → `executed`／`executor`／`service_summary`／`fallback`。  
3. `ibridge_v0.monitoring_graph`（可選）→ `ok`／`analysis_summary`／`recommendation_count`；僅 observability，**不**用於改 selector 或 answer。  
4. 僅 H 線、未走 ibridge 時：對 `build_rooted_context` 輸出做 `attach_subagent_route_to_context`，並在 enrich 後查 init 內 `_monitoring_executor_result`／`_monitoring_graph_result`。

**可重跑驗收（戰車根 venv）**：

```bash
python -m unittest tests.test_context_subagent_routing tests.test_monitoring_executor tests.test_monitoring_graph -v
```

暗部 ibridge 整合：`tests.test_ask_pipeline_ibridge_v0`（`gov_core_system` venv）。

**in-process 審計 log（開發／測試）**：`subagents.monitoring_executor.get_monitoring_task_log()`；測試用 `reset_monitoring_task_log()`。非生產持久化審計。

**Monitoring graph（Sprint 5 · v0.2-langgraph-min）**：`core/monitoring_graph.run_monitoring_graph` 為 in-process **LangGraph**（節點 `summarize`→`analyze`→`recommend`→`finalize`）；預設關閉（`GOV_MONITORING_GRAPH_ENABLED=0`）。公開摘要可含可選 `analysis_summary.nodes_executed`。**仍不**接入 selector／answer。

**L0 Observability 閘門（`/api/ask` · B 線 · M-3 · dev/debug）**

> **制度定位**：本閘門屬 **L0 控制器**，控制「能否在 HTTP 回應看內部 observability state」。**非**業務 contract 層；**開啟閘門 ≠ 准許業務依賴欄位 ≠ SLA 承諾**。

**合併決策（C 線 · 2026-05-25；OBS-GATE-1 · 2026-07-29）**：制度上視兩者為 **同一 L0 Observability Gate 的兩個 surface**，共用下列規則。**OBS-GATE-1 已落地**：可選伺服器 env `GOV_CORE_API_EXPOSE_OBSERVABILITY=1` 作為 **umbrella**（OR 滿足任一 surface 的伺服器半閘門）；**舊** `GOV_CORE_API_EXPOSE_MONITORING_GRAPH`／`GOV_CORE_API_EXPOSE_IBRIDGE` **仍完全相容**。每 surface **仍須**各自 query opt-in（`?expose_monitoring_graph=true`／`?expose_ibridge=true`）。**未**合併為單一 query；**仍** L0 only（≠ L1／L2）。

| Surface | 伺服器 env（預設 **0**） | 請求 query（須顯式 opt-in） | 暴露內容 | 敏感度 |
|---------|-------------------------|----------------------------|----------|--------|
| **monitoring_graph** | `GOV_CORE_API_EXPOSE_MONITORING_GRAPH=1` | `?expose_monitoring_graph=true` | 頂層 **`monitoring_graph`** 精簡摘要 | 中（whitelist 後） |
| **ibridge** | `GOV_CORE_API_EXPOSE_IBRIDGE=1` | `?expose_ibridge=true` | 頂層 **`ibridge_v0`**（含 K-1 側車全量） | 高 |
| **umbrella（OBS-GATE-1）** | `GOV_CORE_API_EXPOSE_OBSERVABILITY=1` | （仍用上列各 surface query） | 僅滿足**伺服器**半閘門；不單獨暴露鍵 | 同 surface |

> **注意（HTTP `monitoring_graph` 閘門 ≠ 有資料）**  
> 僅啟用 surface A（`GOV_CORE_API_EXPOSE_MONITORING_GRAPH=1` + `?expose_monitoring_graph=true`）**不**保證回應含頂層 `monitoring_graph` 鍵。頂層摘要仍須同時滿足 **管線前提**（下表該列）：  
> 1. `GOV_MONITORING_GRAPH_ENABLED=1`  
> 2. monitoring 路由（C-1 `ROUTE-MON-1`）  
> 3. executor **adapter 成功**（`executor=monitoring-service-adapter`；非 `v0.1-stub`／`fallback`）  
> 開啟 `expose_monitoring_graph` 可能使 B 線走 **ibridge 管線**（`ibridge_v0=true`），但無上述前提時 graph 摘要仍為空 → 回應**不含**頂層 `monitoring_graph`（非 `{}` 占位）。全量側車見 surface B（`expose_ibridge`）；兩閘門**獨立**。

**共用規則（兩 surface 均須遵守）**

| 項 | 規定 |
|----|------|
| **預設** | 伺服器 flag **OFF**；無 query opt-in → 回應**不含**對應鍵（非 `{}`） |
| **誰可開** | **dev**：工程師本地除錯；**staging**：ops／尚書省授權票；**prod**：**預設禁止**；大規模 L0 觀測須 Progress 報備 |
| **禁止環境** | prod 預設；特定客戶／租戶隔離環境（除非事故 RCA 票明示） |
| **管線前提** | 見上方**注意**；須 `GOV_MONITORING_GRAPH_ENABLED=1` + monitoring 路由（`ROUTE-MON-1`）+ adapter 成功；**僅**開 HTTP 閘門**不**保證頂層 `monitoring_graph` 鍵 |
| **剝離** | `_monitoring_graph_result`、`_monitoring_executor_result` **永不**進預設 API envelope |
| **業務邊界** | 客戶 SDK／SLA 文件**不得**引用 `monitoring_graph`／`ibridge_v0`；僅 `answer`／`retrieve`／`observability` 為主契約 |

**讀取順序（HTTP）**：`answer`／`retrieve`（主契約）→ `observability` → 可選 `monitoring_graph`（旁路 · surface A）→ 可選 `ibridge_v0`（全量側車 · surface B，**獨立**閘門）。

**範例（dev，雙閘門 + graph flag）**：

```bash
curl -s -X POST "http://127.0.0.1:8000/api/ask?expose_monitoring_graph=true" \
  -H "Content-Type: application/json" \
  -d '{"query":"Check /monitoring/overview KPI drift","top_k":3}'
```

**暗部 B 線 unittest（自帶戰車根 bootstrap，無須手設 PYTHONPATH）**：

- **Path bootstrap 單一權威**：`01_Environments/python_venvs/gov_core_system/core/repo_paths.py`（`find_repo_root`／`ensure_repo_root_on_path`）。`app_api` 啟動與 `tests/_repo_bootstrap.py` 共用同一套 marker 與 `sys.path` 插入策略（venv 根 index 0、戰車根 index 1）；勿在測試或 API 入口另寫第二套 walk。
- **測試專用 idempotency**：`app_api` B 線 suite 在 setUp 內設 `GOV_CORE_TEST_USE_INMEM_IDEM=1`（經 `tests.prepare_test_idempotency_env()`），強制 SQLite、跳過 PG，避免 import 時 dotenv 注入的 `DATABASE_URL` 觸發 ~25s 連線 timeout。**勿**寫入 `.env` 或 deploy config；prod 行為不變。

```bash
cd 01_Environments/python_venvs/gov_core_system
python -m unittest tests.test_app_api_monitoring_graph_expose tests.test_app_api_ibridge_expose tests.test_app_api_k2_prod_shadow -v
```

戰車根裸跑（同上 bootstrap，無須 `PYTHONPATH`；`unittest discover` 單次僅支援一個 `-p`，故列三檔）：

```bash
python 01_Environments/python_venvs/gov_core_system/tests/test_app_api_monitoring_graph_expose.py
python 01_Environments/python_venvs/gov_core_system/tests/test_app_api_ibridge_expose.py
python 01_Environments/python_venvs/gov_core_system/tests/test_app_api_k2_prod_shadow.py
```

Graph 失敗時 HTTP 仍 200：頂層 `monitoring_graph.ok=false` + `reason`（heuristic 建議欄位非 SLO 裁決）；`answer`／`retrieve` 與未暴露時一致。

**未實作（勿寫成已完成）**：graph 參與 selector／SLO gate（L1+）、Z-* 運行時授權、monitoring 寫入 PG／觸發 alert evaluate、HQ `hq.monitoring` 派工類型、**生產預設**暴露 `monitoring_graph`（須雙閘門）。

### 6.8 Monitoring graph 治理條款（C 線 · Sprint 5 後續 · L0／L1／L2）

> **權威**：本節定義 **L0 observability／L1 shadow-advisory／L2 SLO gate** 三級定位、升級階梯與回退；**不**改 selector 生產邏輯。實作消費 graph 驅動 selector／gate 須**另開實作票**（前綴 `M-GOV-L*`）。索引：`AGENTS.md` Monitoring Graph 治理模式、根 `00_master_plan.md` §4.12。

#### 6.8.1 裁決句（接戰必讀）

| 問題 | 答案 |
|------|------|
| **現在啟用哪一級？** | **僅 L0。** L1／L2 為未來選項，無實作、無批文。 |
| **現在能否讓 graph 參與 selector？** | **不能。** 除非滿足 §6.8.4 對應級別之**全部**門檻，且尚書省批准該級實作票。 |
| **現在 graph 是什麼？** | **L0 observability signal**：讀 executor `service_summary` 的只讀分析側車；供 debug／dashboard／離線分析。 |
| **現在能否當 SLO gate？** | **不能。** 屬 **L2**；v0.1 未產出 `slo_verdict` 契約欄位。 |
| **開 HTTP observability 閘門代表什麼？** | 僅 L0 **可見度**控制器；**≠** 業務 contract、**≠** SLA（見 §6.7 L0 Observability 閘門）。 |

#### 6.8.2 三級總覽（L0／L1／L2）

| 級別 | 名稱 | 對 ask 主路徑 | v0.1 狀態 |
|------|------|---------------|-----------|
| **L0** | Observability-only | **零影響**；sidecar／日誌／trace | **已允許**（預設 flag OFF） |
| **L1** | Shadow selector／advisory | **零用戶面影響**；可記錄「若依 graph 會怎麼決策」 | **禁止** |
| **L2** | SLO gate／hard policy | **直接影響**；可阻斷、降級、reroute | **禁止** |

**語意對照（舊三層標籤）**：L0 ≈ observability；L1 ≈ shadow + advisory；L2 ≈ gating／hard SLO。舊稿 L3 partial influence／L4 hard gate 併入 **L2 升格路徑之子階段**（見 §6.8.5）。

**與 O-2 executor 的關係**：executor（O-2a）亦屬 L0／`signal_only`；graph **不得**繞過 executor 直連 monitoring API／PG（見 `core/monitoring_graph.py` 模組註解）。

#### 6.8.3 L0 — Observability-only（**現況** · M-1–M-3）

| 維度 | 規定 |
|------|------|
| **定位** | 只讀 observability signal；**不**參與 selector、answer 合成、SLO 裁決 |
| **可見度** | 開啟 `GOV_MONITORING_GRAPH_ENABLED=1` 後：`ibridge_v0.monitoring_graph`（管線內）；HTTP 須 §6.7 雙閘門才有頂層 `monitoring_graph` 或 `ibridge_v0`；init 內 `_monitoring_graph_result` **僅內部** |
| **權限** | **零**寫入 selector 輸入；**零**改 `use_rag`／retrieve／answer；recommendation **不得**驅動決策 |
| **欄位範圍** | 公開 whitelist：`ok`、`analysis_summary`、`recommendation_count`、`top_recommendation`（heuristic）、失敗 `reason`（見 §6.8.6） |
| **必要條件** | `tests.test_monitoring_executor` + `tests.test_monitoring_graph` + ibridge 整合全綠；graph 預設 **OFF** |
| **回退** | `GOV_MONITORING_GRAPH_ENABLED=0` → 不跑 graph、無公開鍵；graph 錯誤 → `ok=false`，主路徑不變；關 HTTP 閘門 → strip 頂層 observability 鍵 |
| **禁止** | 業務邏輯依賴 L0 欄位；客戶-facing SLA 引用 `monitoring_graph`／`ibridge_v0`；把 `severity: warn` 當 skip-RAG 指令 |

#### 6.8.4 L1 — Shadow selector／advisory（**未來** · 須單開 `M-GOV-L1` 票）

> **設計稿（Sprint 6 · 治理）**：`M-GOV-L1_shadow_selector_design.md` — shadow／advisory 欄位契約、trace、fail-open、測試骨架；**設計 only**，不含實作或 env flag。

**什麼叫 L1**

- Selector（或 enrich 節點）**可讀取** graph 輸出，但僅作 **shadow decision**：記錄 `shadow_use_rag`／`shadow_rule_id`（或等價）與生產 `use_rag` **對照**；**不**改實際回答路徑。  
- **Advisory 子階段**（仍屬 L1）：在 metadata 暴露 `advisory_use_rag`（或等價）供人工／離線對賬；**禁止**自動採納、**禁止**寫入 user-facing answer。

| 維度 | 規定 |
|------|------|
| **可見度** | L0 全部 + shadow／advisory 欄位（僅內部 trace、eval 匯出或 dev API；**不**進預設 prod envelope） |
| **權限** | 可**讀** graph；可**寫** shadow／advisory sidecar；**不可**覆寫生產 selector、**不可**阻斷請求 |
| **升級前提（累加 L0 全部）** | L0 連續 **14 日** staging／prod 開 graph **無 P0**；monitoring 路由樣本 **≥500**；graph `ok` 率 **≥99%** |
| **必要 artefacts** | ① shadow 對照欄位契約（單開）；② 專用 test suite（`test_monitoring_graph_shadow_*`）；③ shadow selector log／trace 匯出；④ 風險評估報告（誤導場景、資料外洩）；⑤ §6.8.8 回歸全綠 |
| **環境** | dev／staging 先行；prod shadow **僅**尚書省批准後 |
| **回退** | 關閉 L1 旗標（實作票定義）→ **立即**回到 L0；連續 shadow 異常 **≥3** 次 → 暫停升格 **30 日**；Progress **末尾** RCA |

#### 6.8.5 L2 — SLO gate／hard policy（**未來** · 須單開 `M-GOV-L2` 票）

**什麼叫 L2**

- graph 結果或正式 **`slo_verdict`** 可**直接**阻斷請求、強制 fallback、降級 retrieve 或 reroute；影響生產 `use_rag`／answer 策略。

| 維度 | 規定 |
|------|------|
| **可見度** | L1 內部欄位 + SLO 裁決欄位（命名空間與 `recommendation` **分離**）；gate 事件須可審計 |
| **權限** | 可改寫生產路徑；須 feature flag + 自動回退 hook |
| **升級前提（累加 L1 全部）** | L1 shadow／advisory 穩定 **≥21 日**；shadow 與生產不一致率 **≤5%**；誤導性 recommendation **≤2%**（人工抽樣 **200** 筆）；**policy owners** 具名；營運／客戶影響評估通過 |
| **L2 子階段（原 L3 partial）** | 僅 dev／test 或 staging，或 prod **canary ≤5%** 流量先驗證覆寫 selector；須與 K-2 canary 制度對齊（`docs/k2_deployment_governance.md`）；canary **≥28 日** 且 P0=0 方可擴面 |
| **必要 artefacts** | ① SLO 契約全文（`slo_verdict`／breach 定義）；② rollback playbook（演練 **1** 次）；③ 變更審核記錄 + 尚書省 **gating** 批文 + 治理／安全會簽；④ gate／SLO 專測全綠 |
| **環境** | prod hard gate **僅** L2 批文 + 24h on-call + 自動回退；staging **預設禁止** L2（除非明示演練票） |
| **回退（必須立即執行）** | gate 誤判率超閾、P0、用戶面異常、SLO breach 假陽性 → **立即**降回 **L1** 或 **L0**（視嚴重度）；關閉所有 L2 旗標；保留 L0 sidecar 可選直至 RCA 關閉 |

#### 6.8.6 環境矩陣（L0／L1／L2）

| 環境 | L0 observability | L1 shadow／advisory | L2 SLO gate |
|------|------------------|---------------------|-------------|
| **dev／test** | 允許（flag + 閘門） | 允許（滿足 L1 門檻後） | **預設禁止**；事故演練票除外 |
| **staging** | 允許 | 允許（L1 批文後） | **禁止**（L2 批文 + 限流除外） |
| **prod** | 允許（不改用戶答案；HTTP 閘門預設 off） | **僅**尚書省批准 | **僅** L2 批文 + canary 門檻 + on-call |

**prod 預設**：即使 `GOV_MONITORING_GRAPH_ENABLED=1`，仍屬 **L0**；不得同時開啟未定義之 L1／L2 env 旗標（旗標名由實作票定義，**禁止** worker 自創 env 上線）。

#### 6.8.7 信號治理（公開 vs 內部）

| 類別 | 欄位／位置 | 說明 |
|------|------------|------|
| **L0 可公開** | `ibridge_v0.monitoring_graph` 或頂層 `monitoring_graph` | whitelist 產出；**不得**含完整 `service_summary`、token、連線資訊 |
| **僅內部** | `_monitoring_graph_result` 全文、`analysis` 全物件、`recommendations[]` 全列表、executor 原始 KPI | 禁止進預設 API；禁止寫入 `master_status` 當「已執行政策」 |
| **L1 內部（未來）** | `shadow_use_rag`、`advisory_use_rag` 等 | 僅 trace／eval；不進客戶 SDK |
| **L2（未來）** | `slo_verdict`、`slo_breach` | 僅 L2 契約票定義；與 `recommendation` **命名空間分離** |
| **recommendation** | `kind`／`severity`／`message` | **啟發式**；**不得**標為 `policy`／`slo_pass`／`gate` |

#### 6.8.8 回退條款（flag off／degrade／誤判）

| 觸發 | 系統行為 | 操作者動作 |
|------|----------|------------|
| **`GOV_MONITORING_GRAPH_ENABLED=0`** | 不呼叫 graph；無 `monitoring_graph` 公開鍵 | 預設安全態 |
| **HTTP 閘門關閉** | strip 頂層 `monitoring_graph`／`ibridge_v0` | L0 可見度歸零；管線 sidecar 行為不變 |
| **graph 執行錯誤** | `ok=false` + `reason`；selector／answer **不變** | 查 executor adapter |
| **adapter fallback（stub）** | v0.1 **不跑** graph | 見 §6.7 `v0.1-stub` |
| **L1 異常** | 關 L1 旗標 → **L0** | Progress 末尾 RCA |
| **L2 異常** | 關 L2 旗標 → **L1 或 L0** | 觸發 rollback playbook；連續誤判 **≥3** → 暫停升格 **30 日** |

**快速回退口令（運維）**：prod 上 L1／L2 相關旗標 → `0`；grep 確認無 selector 分支讀取 `_monitoring_graph_result` 做生產決策；重跑 §6.7 驗收命令。

#### 6.8.9 驗證與文件清單（升格前自檢）

| 檢查項 | L1 shadow／advisory | L2 SLO gate |
|--------|---------------------|-------------|
| 戰車根 unittest | + `test_monitoring_graph_shadow_*` | + gate／SLO 專測 |
| ibridge 整合 | + shadow 欄位斷言 | + 阻斷演練 |
| 文件 | shadow 契約 + 風險報告 | SLO 契約 + rollback playbook |
| 制度 | 尚書省 L1 批文 | 尚書省 L2 gating 批文 + 會簽 |
| 指標 | §6.8.4 L1 欄 | §6.8.5 L2 欄 |

**可重跑（L0 最低）**：

```bash
python -m unittest tests.test_context_subagent_routing tests.test_monitoring_executor tests.test_monitoring_graph -v
```

#### 6.8.10 已知未決策項

| 項 | 狀態 |
|----|------|
| L1 shadow 欄位契約與 trace 設計 | **設計稿** · `M-GOV-L1_shadow_selector_design.md`（Sprint 6；**未實作**） |
| L1 shadow 寫入點（selector 後 vs enrich 內）最終裁定 | **設計稿傾向 A** · 實作票待定 |
| L2 SLO gate／`slo_verdict` | **錨點 only** · `M-GOV-L2` + §6.8.5；**禁止、未實作、未排期** |
| `slo_verdict` 與 Infra alert evaluate 分工 | **未開票** · `M-GOV-L2` 實作票 |
| 合併 HTTP 閘門為 `GOV_CORE_API_EXPOSE_OBSERVABILITY` | **已決（OBS-GATE-1 · 2026-07-29）** · umbrella env OR 舊雙閘門；query 仍分 surface · L0 only |
| prod 大規模開 L0 是否需尚書省報備 | **建議** off 為常態；大規模 observability 可報備 |
| 與 K-2 shadow 共用匯出（`ibridge_exporter`） | **未決** |
| **哪一版才考慮 L1 shadow** | **未排期**；預設 v0.2 LangGraph 仍 **L0**；L1 最早在 M-GOV-L1 票 + §6.8.4 門檻滿足後 |

---

## 7. Navigation Map Template 的操作化

> 模板見 `40_navigation_map_template.md`；本節說明**如何維護**，不在此複製全文表格。

### 7.1 何時更新 nav map

| 觸發 | 誰 | 動作 |
|------|-----|------|
| 新開 A/B/C/D/E 子線 | F 線／線負責人 | 在 §7 空白表複製一行 `subtree`，填 `node_id` 對齊 A-2 `subtree_id` |
| 隊列新票、Output File 變更 | 施工 worker | 將新路徑**末尾追加**到該 subtree 的 `entry_refs`（A-4 §6.3） |
| 票 DONE | worker | 更新 `notes`／`handoff_digest`；**不刪**歷史節點 |
| Master plan 依賴變更 | F 線 | 檢查 `master_plan_anchor` 與 §5.1 依賴圖一致 |

### 7.2 維護步驟（單次）

1. 打開 `40_navigation_map_template.md` §7 空白表或 §8 示例（Sprint 0 可先用示例表擴展）。  
2. 確認 `root` 節點唯一；`subtree` 的 `parent_node_id` 通常為 `root`。  
3. 填 `entry_refs`：順序為 **接戰必讀 → 本線規格 → 合同 → 驗收**；3～7 條。  
4. 填 `queue_ids` 與 `90_run_queue.md` 對賬（A-4 §6.2）。  
5. 若 `entry_refs` 與隊列 Output 衝突：**以隊列為準追加**，不覆蓋前段必讀順序。  
6. 實例檔若過大：拆 `nav_map_<scope>.md`（另開票）；更新 `nav_map_ref` 邏輯名。

### 7.3 與接戰流程的銜接

- 口令「接戰」、無具體票 → 僅載入 **`root`** 節點（A-4 §5.2）。  
- `A-*` 票 → **`root` + `line.a.*` subtree**（示例：`line.a.context-entry`）。  
- 讀檔順序 = root.`entry_refs` → subtree.`entry_refs` → 本輪 working（任務卡 query）。

### 7.4 與 builder 的邊界

- Nav map **不會**被 `build_rooted_context` 自動生成。  
- `root_context.navigation` 在程式內可能僅 mock 少量邏輯名；nav map 可規劃為**超集**，實作對齊另開票。

---

## 8. 驗收與自檢

### 8.1 文檔票（A 線 Sprint 0）

| 檢查項 | 通過標準 |
|--------|----------|
| 檔案存在 | `50_context_entry_runbook.md` 含 §1–§10 |
| 引用一致 | 與 A0–A4、合同、A0 §4 無衝突宣稱 |
| 不假裝實作 | §9 明列 subtree deny 聯集／Z-*／未覆蓋 rule 缺口 |
| 隊列 | A-5 行 `DONE`，Notes 一句話 |

### 8.2 執行期／入口票（H 線）

**必跑（合同 §6）**：

```bash
python -m unittest tests.test_context_entry -v
```

**涉 ask 全鏈時加跑**：

```bash
python -m unittest tests.test_ask_selector_and_answer -v
```

**可選**：`tests.test_langgraph_flow_k1`（K-1 入口已對齊時）。

### 8.3 欄位斷言（`build_rooted_context` 成功時）

| 欄位 | 期望 |
|------|------|
| `ok` | `true`（除非測試預期失敗） |
| `metadata.entry` | `"context_entry"` |
| `metadata.source` / `entry_mode` | 與傳入 `mode` 一致（非法 mode 回退 `ask_pipeline`） |
| `task_input.task_id` / `work_order_id` | 非空（可為自動生成） |
| `root_context` / `working_context` / `long_term_memory` | dict，非手拼空殼冒充 |
| `token_usage` | 含 `root`、`working`、`memory`、`total`、`total_tokens` |
| `result` | 含 `assembled_text` 等向後相容欄位 |

**失敗形狀**：`ok: false` + 非空 `message`（如 `task_input must be a dict`）。

### 8.4 Phase 10.5 / S1–S3 對賬

| 場景 | 檢查 |
|------|------|
| S1 | 有 semantic／`context_refs` 時 selector 倾向 RAG |
| S2 | 問候可無 H payload；deny 仍適用後續 tool |
| S3 | retrieve 失敗有 fallback 欄位，且無 deny 污染 |

### 8.5 治理自檢（Runbook 使用者）

- [ ] 四流派最低覆蓋：Context（§2 已讀）、Source（列檔）、Incremental（最小改）、Debugging（§8 命令）。  
- [ ] Work Report 七節齊全或標「無」。  
- [ ] 無 H-line bypass、無未授權改 `core/`。

---

## 9. 風險與限制（v0.1 必讀）

### 9.1 執行期狀態（deny engine v1 · Sprint 3 收口）

| 項目 | 現狀 | 影響 |
|------|------|------|
| **deny engine v1** | **已實作**（R-3a–c） | `context/deny_rules.py` 規則表 + `GateRunner` 雙閘；`tests.test_context_entry` 26/26 OK |
| 頂層 `subtree_context` | **已實作**（mock／`task_input` 覆寫） | 仍非 nav map 檔案自動產出 |
| P0.5 subtree 裁剪 | **已實作**（R-2 · `metadata.trim`） | heuristic，非 tiktoken 精算 |
| **subtree deny 聯集**（步驟③） | **已實作**（R-3d） | `GATE_PIPELINE.subtree` enabled；`metadata.deny.subtree` |
| **A-3 coverage** | content **7/7** 表行 · action **4/8** | 缺 Telegram／hashes／dark_ops 等；Z-* 僅骨架 |
| Nav map 自動產檔 | **無** | 僅 JSON `metadata.navigation_map`（R-1） |
| 憲法 Z-* 運行時拒絕器 | **未實作** | 違規靠制度 + 停工；非 regex 可替代 |

### 9.2 Mock 與合同差距

- `root_context` 多為 builder **mock**（如 `red_lines_summary`），**不等同** A-1 完整 `governance_digest`。  
- `long_term_memory` 的 semantic／structured 為 **mock 檢索**，字段形狀對齊真連，內容非生產 KB。  
- **TRIM_PRIORITY** 僅覆蓋 **ignore** 語意；deny 由 **GateRunner** 處理，兩者不可混用。

### 9.3 歷史路徑與遷移

- 並非所有歷史呼叫點已改為 `build_rooted_context`；遷移須**單開工單**（合同 §3.1）。  
- `GOV_CORE_ASK_HLINE_CONTEXT_FALLBACK=1` 僅 dev/test；生產預設關閉。  
- 勿與 `_workflow_upgrade/`（底線）歷史隊列混用；本輪以 `workflow_upgrade/` 為準。

### 9.4 權限與禁區

- Worker **不得**改 root 制度 digest；**不得**放寬 deny。  
- 觸及 DarkOps、checkpoint、`.env` 等 → 依憲法停工。  
- 雙 Telegram 監聽、主艙重套件等 → deny 行為類（A-3 §5.2）。

### 9.5 Monitoring subagent（Sprint 4 · O-2 制度邊界）

| 項目 | 現狀 | 影響 |
|------|------|------|
| **C-1 路由** | **已實作** · `context_routing_v0.1` · 一律 `signal_only` | 不分配 HQ worker；不改 selector |
| **O-2a executor** | **已實作** · 只讀 adapter + stub fallback | 不寫 DB；不跑 ingest／scheduler |
| **O-2b ibridge 掛載** | **已實作** · 預圖 enrichment + 公開摘要欄位 | 不改 Phase 10.5 圖邊 |
| **HQ `task_routing_table`** | **刻意無** `hq.monitoring` | 維運票仍走 `dark.infra` 等；見 `TASK_ROUTING.md` §3.4 |
| **LangGraph monitoring 圖** | **未實作** | 需單開編排票；本 runbook 不描述節點表 |
| **持久化 executor 審計** | **未實作**（僅 in-memory log） | 生產審計仍靠 trace／`task_runs`／monitoring API |

---

## 10. 未來工作（後續線別 · 不新增 A 線票號）

> 下列為 **TODO 總結**，供 A-6、B/C/D/E 或實作票參考；**不在此開新 A-x 票**。

### 10.1 A 線收尾（隊列既有）

| 項 | 負責 | 內容 |
|----|------|------|
| A-6 | `90_run_queue.md` | 回寫 A 線全票 Status／Notes；Sprint 0 A 出口對賬 |
| Nav 實例檔 | 尚書省裁決 | 是否必要 `nav_map_line_a.md` 等，目錄與命名 |

### 10.2 實作票（建議單開，非 Sprint 0）

| 項 | 內容 |
|----|------|
| Subtree deny 進階 | 啟用 `subtree` gate、root ∪ subtree `forbidden_*` 聯集 |
| Deny coverage 擴面 | `full_cli_trace`；Z-* / Telegram / hashes 等 action 規則（O 線對賬） |
| Root 富化 | mock root → 對齊 A-1 `hard_rules` 類型表（可配置 digest） |
| Nav 對齊 | builder `navigation` 與 nav map 節點自動一致性檢查（unittest 或 lint） |
| 歷史遷移 | 殘留 `build_context` 直接呼叫點 → H 線 |

### 10.3 B / C / D / E 線（Sprint 0 後 · placeholder）

| 線 | 方向 |
|----|------|
| **B** | 編排／handoff 與 context 交接欄位對齊 |
| **C** | `token_usage`、`trimming_applied`、eval 視野（合同 §8.4） |
| **D** | Skills 與 §10.5 消費欄位契約 |
| **E** | 外部通道注入 working 時的 deny 閘 |

### 10.4 與 Phase 10.5 的持續對賬

- 每次改 selector／retrieve 契約時，回讀本 runbook §4.5、§8.4。  
- A 線**不改** `skills/skills_contract.md` 路由表；僅更新上游欄位說明（若尚書省授權）。

---

## 變更紀錄

| 日期 | 變更 |
|------|------|
| 2026-05-25 | A-5 初版：整合 A0–A4；場景／四層／deny-ignore／nav／驗收／風險／未來工作 |
| 2026-05-25 | Sprint 3 R-3 收口：§6／§9 對齊 deny engine v1；移除「deny 未實作」過時說法 |
| 2026-05-25 | Sprint R-3d–f：subtree gate v1、`full_cli_trace`、Z-* 骨架、policy coverage 自查 |
| 2026-05-25 | Sprint 5 C 線治理：§6.7 L0 Observability 閘門 + §6.8 L0／L1／L2 三級條款（升級／回退） |
| 2026-05-25 | Sprint 6 M-GOV-L1／L2 治理票：§6.8.4 L1 設計稿索引；§6.8.10 L1 契約／L2 錨點對帳 |
