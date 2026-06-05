# 任務路由制度（Phase 3）

> **票號**：`HQ-P3-TASK-ROUTING`  
> **角色**：副官依任務類型自動分配 worker／cabin 之權威制度（可移植層 + 機器讀表）。  
> **對照**：組織拓撲見 `DEPARTMENT_MAP.md`；Phase 門檻見 `HARNESS_CONSTITUTION.md` §5；實例路徑見 `INSTANCE_ANCHOR_TANG.md`。

---

## 1. 文件定位

| 項目 | 說明 |
|------|------|
| **人讀** | 本檔（路由原則、任務類型語意、副官流程） |
| **機器讀** | `04_Workflows/task_routing_table.json`（權威路由表） |
| **執行** | `02_Agents_Core/task_routing.py` → `route_task()` 回傳 `dict` |
| **CLI** | `Master_Map.json` → `runners.route_task_py` |

**權威位階**（不變）：尚書省當次指令 ＞ 憲法 ＞ 合約 ＞ Progress 當期敘述 ＞ 本表。

---

## 2. 副官路由流程

接戰完成 §初始化校準後，尚書省下達任務前或同時，副官須：

1. **解析任務**：取得 `task_type`（建議）或任務描述／標籤。
2. **呼叫路由**：`python .\04_Workflows\_route_task.py --type <task_type>` 或 `--text "<描述>"`。
3. **解讀結果**：讀取 `worker`、`cabin`、`assignable`、`runners`；若 `assignable` 為 false，依 `block_reason` 停工或回報尚書省。
4. **派工**：將任務卡指向對應 HQ worker；若需執行 runner，僅使用回傳之**邏輯名**（見 `Master_Map.json` → `runners`），禁止自創路徑。

```text
尚書省指令 → 副官 route_task() → { worker, cabin, runners, assignable }
                ↓ assignable=false → 阻塞寫入 Progress（待確認六行）
                ↓ assignable=true  → 對應 worker／艙執行
```

---

## 3. 任務類型（`task_type`）

命名空間：`{域}.{職責}`，全小寫、點號分隔。

### 3.1 HQ 域

| task_type | worker | cabin | 說明 |
|-----------|--------|-------|------|
| `hq.coordination` | HQ-Coordinator | — | 規劃、任務卡、驗收定義；不直接改 code |
| `hq.governance` | HQ-Governance-Worker | — | 黑板、三件套、地圖、AGENTS（授權時） |
| `hq.tooling` | HQ-Tooling-Worker | — | config 下 tools／mcp／services |
| `hq.qa` | QA-Reviewer | — | 唯讀驗證、W4 盲測協助 |

### 3.2 Chariot 域（戰車 runner／雙艙）

| task_type | worker | cabin | 說明 |
|-----------|--------|-------|------|
| `chariot.smoke` | HQ-Governance-Worker | — | 三鑰／擴充盲測（`04_Workflows` runner） |
| `chariot.factory` | HQ-Governance-Worker | `gov_main` | Wave、精煉、指紋、Warpath |
| `chariot.scout` | HQ-Governance-Worker | `gov_agency` | 偵察、Playwright、agency 任務 |
| `chariot.telegram` | HQ-Governance-Worker | `gov_main` | Telegram 監聽啟停 |

### 3.3 Dark 域（暗部四 Agent · 統包艙）

| task_type | worker | cabin | dark_agent | 說明 |
|-----------|--------|-------|------------|------|
| `dark.infra` | DarkOps-Worker | `gov_core_system` | Infra | Postgres／Qdrant／健康檢查 |
| `dark.data` | DarkOps-Worker | `gov_core_system` | Data | ingest／verify／pipeline_meta |
| `dark.rag` | DarkOps-Worker | `gov_core_system` | RAG | 檢索與 LLM 組裝 |
| `dark.orchestration` | DarkOps-Worker | `gov_core_system` | Governance | LangGraph／checkpoint |
| `dark.governance` | DarkOps-Worker | `gov_core_system` | Governance | master_status／handoff |
| `dark.smoke` | DarkOps-Worker | `gov_core_system` | Governance | Gov Core 最小 smoke |

### 3.4 Monitoring subagent（H 線 · **非** HQ `task_type`）

Sprint 4 **O-2** 的 monitoring subagent **不**在本表新增 `hq.monitoring` 或 `chariot.monitoring` 列。原因：

| 維度 | HQ `route_task`（本檔 §3.1–3.3） | H 線 monitoring subagent（C-1 + O-2） |
|------|----------------------------------|----------------------------------------|
| **用途** | 尚書省派工 → HQ 五角色／DarkOps cabin | ask 流程內 **signal_only** 側車（`metadata.subagent_route.signal_only=true`） |
| **觸發** | `--type` 或 `--text` 關鍵字 | `build_rooted_context` 後之 context 信號（tags／goal／query 等） |
| **執行者** | `HQ-*-Worker`／`DarkOps-Worker` | `subagents/monitoring_executor.py`（只讀 service + stub fallback） |
| **與 `dark.infra`** | Postgres／Qdrant／docker **維運派工** | **不**等同；monitoring 不替 Infra 解禁或改 compose |

**制度結論**：

- 人類／Infra 維運 monitoring API、schema、驗收腳本 → 仍用 `dark.infra`（或尚書省明示之 Dark 票）；`assignable` 仍受 DarkOps 閘門約束。
- ask 內「順帶查 overview／dashboard-summary」→ 走 H 線 runbook（`50_context_entry_runbook.md` §3.5），**勿**用 `_route_task.py --type` 假裝已啟動 subagent executor。
- 若未來需要 **HQ 協調用**標籤（例如隊列票 `O-2c` 文檔收口），可另開票新增 `hq.coordination` 關鍵字或備註欄，**不得**標成 executor 實作或 `assignable` 默認 true。

**交叉索引**：`AGENTS.md` · Monitoring Subagent；`subagents/context_routing.py` · `subagents/monitoring_executor.py`。

---

## 4. Phase 門檻與 `assignable`

| 閘門 | 現況（路由表 `phase_gates`） | 行為 |
|------|------------------------------|------|
| **DarkOps-Worker** | `blocked`（憲法 §5.2 第一階段預設） | 路由仍回傳正確 `worker`／`cabin`／`dark_agent`，但 `assignable=false`，`block_reason` 說明須另開票解禁 |

**裁決**：Phase 1 定稿令已發布；Dark 域路由用於**預分配與交接**，不代表暗部已解禁施工。

---

## 5. 匹配規則

| 優先 | 方法 | 說明 |
|------|------|------|
| 1 | **explicit** | `--type` 與路由表 `task_type` 完全一致 |
| 2 | **keyword** | `--text` 對各路由 `keywords` 計分，取最高 |
| 3 | **default** | 無匹配 → `hq.coordination` |

關鍵字匹配不區分大小寫；中英文皆可。尚書省若明示 `task_type`，**以 explicit 為準**，關鍵字僅作 fallback。

---

## 6. 與三件套分工

| 主題 | 憲法／合約／地圖 | 本制度 |
|------|------------------|--------|
| 五角色職責 | `DEPARTMENT_MAP.md` §5 | 引用；不重複全表 |
| Cabin 角色 | `DEPARTMENT_MAP.md` §6 | `cabin` 鍵對齊地圖 `cabins` |
| 暗部四 Agent 順序 | 合約 §7.5、地圖 §7 | `dark_agent` 欄位 |
| runner 邏輯名 | `Master_Map.json` | 路由表僅列鍵名，不複製路徑 |
| 禁區／Blocked | 憲法 §5.2 | `phase_gates` + `assignable` |

---

## 7. 回傳 `dict` 契約（摘要）

`route_task()` 必含：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `ok` | bool | 是否成功解析（含 default） |
| `assignable` | bool | 當前 Phase 是否可派工 |
| `task_type` | str | 解析後類型 |
| `worker` | str | HQ 五角色或 DarkOps |
| `cabin` | str \| null | `gov_main`／`gov_agency`／`gov_core_system` |
| `domain` | str | `HQ`／`Chariot`／`Dark` |
| `dark_agent` | str \| null | Infra／Data／RAG／Governance |
| `runners` | list[str] | 建議 runner 邏輯名 |
| `enter_runner` | str \| null | 進艙 runner 鍵（若有） |
| `match_method` | str | `explicit`／`keyword`／`default` |
| `blocked` | bool | 同 `not assignable` |
| `block_reason` | str \| null | 阻塞說明 |
| `message` | str | 人讀一句摘要 |

---

## 8. 維護

- 新增任務類型：先更新本檔 §3，再改 `task_routing_table.json`，最後跑 `test_task_routing.py`。
- 解禁 DarkOps：尚書省裁決後改 `phase_gates.dark_ops_worker` 為 `active`，並於 Progress 留痕。
- 版本：`routing_schema_version` 目前 **v1**；破壞性變更須升版並寫入 Progress。

**存檔**：`04_Workflows/TASK_ROUTING.md` · `04_Workflows/task_routing_table.json`
