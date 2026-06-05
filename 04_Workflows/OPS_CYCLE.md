# 營運週期制度（Phase 4）

> **票號**：`HQ-P4-OPS-CYCLE`  
> **角色**：副官依專案／票號維護**戰報 → 封存 → 回顧**完整營運週期記錄。  
> **對照**：接戰／封存口令見 `AGENTS.md`；任務路由見 `TASK_ROUTING.md`；Phase 1 定稿見 `project_status/HQ_PHASE1_FINALIZATION_ORDER.md`。

---

## 1. 文件定位

| 項目 | 說明 |
|------|------|
| **人讀** | 本檔（週期原則、三階段流程、欄位契約） |
| **機器讀** | `04_Workflows/ops_cycle_schema.json`（戰報欄位、封存步驟、回顧類型） |
| **執行** | `02_Agents_Core/ops_cycle.py` |
| **CLI** | `Master_Map.json` → `runners.ops_cycle_py` |

**權威位階**（不變）：尚書省當次指令 ＞ 憲法 ＞ 合約 ＞ Progress 當期敘述 ＞ 本制度。

**與 AGENTS.md**：`§封存協議` 為**行為權威**；本制度提供**結構化欄位、驗證與 CLI**，不取代口令語義。

---

## 2. 營運週期三階段

```text
接戰（open/active）→ 作戰中寫戰報 → 封存（archive_pending → archived）→ 回顧（reviewed）
```

| 階段 | 產物 | 落點 |
|------|------|------|
| **戰報** | 單輪執行紀錄（命令、結果、阻塞、下一步） | `04_Workflows/00_Agent_Work_Progress.md` 文末 |
| **封存** | 證據 + 里程碑 + 戰報 +（全量時）war_status／指紋 | 見 §3、`AGENTS.md` §封存協議 |
| **回顧** | 迭代／階段／事件／結案反思 | `04_Workflows/project_status/reviews/` |

---

## 3. 副官流程

### 3.1 開戰後（active）

1. 取得 `ticket_id`（尚書省票號或自訂，建議 `HQ-…`）。
2. 作戰中累積證據（CLI 輸出、`ok`、指標）；**不**將金鑰寫入戰報。
3. 收兵前組裝戰報 JSON（見 §5），執行驗證：

```powershell
cd D:\大唐三省六部
python .\04_Workflows\_ops_cycle.py validate-report --json .\path\to\report.json
python .\04_Workflows\_ops_cycle.py render-report --json .\path\to\report.json
```

### 3.2 封存（archive）

依 `AGENTS.md` §封存協議順序執行。可用清單自檢：

```powershell
python .\04_Workflows\_ops_cycle.py checklist --mode full
python .\04_Workflows\_ops_cycle.py validate-archive --mode full
```

- **`minimal`**：證據 + 戰報（文檔工單、單輪修補）。
- **`full`**：含 milestone、war_status、指紋等（全量收兵）。

寫入戰報（預覽／正式）：

```powershell
python .\04_Workflows\_ops_cycle.py append-report --json .\path\to\report.json --dry-run
python .\04_Workflows\_ops_cycle.py append-report --json .\path\to\report.json
```

### 3.3 回顧（review）

階段結束或尚書省要求時，建立回顧稿：

```powershell
python .\04_Workflows\_ops_cycle.py new-review --type phase_gate --project HQ-Phase4 --ticket HQ-P4-OPS-CYCLE
```

類型：`sprint`｜`phase_gate`｜`incident`｜`project_closeout`（見 schema `review_types`）。

### 3.4 封存 Cursor Subagents 類戰報

適用票號形如 `TEST-SUB-*` 或尚書省明示走 Cursor subagent 鏈的 HQ 票（見 `.cursor/agents/DISPATCH_GUIDE.md`）。

1. **checker 外層 JSON ≠ 可 append 戰報**：`checker-reviewer` 產出含 `verdict`、`evidence`、`gaps` 等；寫入 Progress 須抽出內層 **`battle_report_json_draft`**，存成**獨立** `.json`，且根物件僅含 §5 契約欄位（勿把外層驗收包直接餵 CLI）。
2. **驗證與寫入**：

```powershell
python .\04_Workflows\_ops_cycle.py validate-report --json .\path\to\report.json
python .\04_Workflows\_ops_cycle.py render-report --json .\path\to\report.json
python .\04_Workflows\_ops_cycle.py append-report --json .\path\to\report.json --dry-run
python .\04_Workflows\_ops_cycle.py append-report --json .\path\to\report.json
```

3. **封存模式**：純文檔澄清票（如 TEST-SUB-002）可用 `checklist --mode minimal`；全量收兵仍用 `full`。
4. **未知欄位**：草稿若含 schema 外頂層鍵，`validate-report` 回傳 **`warnings`**（`unknown fields`），**不**阻斷 `ok`；缺必填欄位則 `ok: false`。
5. **隊列對齊**：`ticket_id` 建議與 `workflow_upgrade/90_run_queue.md` 之 `TEST-SUB-00X` 一致。

---

## 4. 封存步驟對照

| ID | 標題 | 全量封存 | 最小封存 |
|----|------|:--------:|:--------:|
| `evidence` | 執行證據 | ✓ | ✓ |
| `milestone` | 里程碑 | ✓ | — |
| `battle_report` | 戰報 | ✓ | ✓ |
| `runbook_calibration` | Runbook 校正 | 視需要 | — |
| `standards_calibration` | 標準校正 | 視需要 | — |
| `forbidden_zone` | 禁區確認 | ✓ | 建議 |
| `war_status` | war_status | ✓ | — |
| `constitution_readme` | README 對齊 | ✓ | — |
| `fingerprints` | 指紋登錄 | ✓ | — |

---

## 5. 戰報欄位契約

`validate_battle_report()` / `append-report` 使用下列欄位（JSON）：

| 欄位 | 必填 | 說明 |
|------|:----:|------|
| `ticket_id` | ✓ | 票號，如 `HQ-P4-OPS-CYCLE` |
| `role` | ✓ | 執行角色，如 `大唐副官` |
| `executed` | ✓ | 執行之檔案與命令（列表或字串） |
| `results` | ✓ | 關鍵結構化結果 |
| `blockers` | ✓ | 阻塞與風險（無則寫「無」） |
| `next_steps` | ✓ | 下一步建議 |
| `status` | — | `draft`／`done`／`blocked`／`partial` |
| `metrics` | — | 任意 JSON 物件（chunks、latency 等） |
| `forbidden_zone_note` | — | 禁區／邊界接觸說明 |

渲染標題見 schema `battle_report.section_titles`。

### Subagents 工單類型（Cursor · v0.1）

| 類型 | 建議流水線 | governance-guard | 可改範圍（示例） |
|------|------------|------------------|------------------|
| `bugfix`（單檔） | （可選）`repo-researcher` → `implementation-worker` → `checker-reviewer` | **`allow`** 後施工 | 任務明示單檔，如戰車根 `subagents/context_routing.py` |
| `doc_clarification` | guard → worker（文檔）→ checker | **須** `allow`；條件鎖 runbook 章節 | 僅 `workflow_upgrade/01_context-entry/50_context_entry_runbook.md` 等明示段落；**禁止** AGENTS／`core/**`／暗部 |
| `governance_test`／跨域 proposal | **僅** `governance-guard` | 可 **`stop_work`** | 不派 worker；裁決與條文引用寫入戰報或 Progress |

與 H 線 ask `subagents/*`（monitoring 側車）**不同系統**；HQ 派工制度仍以 `TASK_ROUTING.md`／`_route_task.py` 為準，本表僅 Cursor 協作鏈。

### 戰報範例（TEST-SUB-002 · doc_clarification）

下列為可通過 `validate-report` 的**扁平**草稿（checker 內層 `battle_report_json_draft` 應長這樣；本輪**不**另建 repo 內 JSON 檔）：

```json
{
  "ticket_id": "TEST-SUB-002",
  "role": "Cursor-checker-reviewer",
  "status": "done",
  "date_local": "2026-05-25",
  "executed": [
    "governance-guard: verdict=allow；allowed_paths 鎖 50_context_entry_runbook.md §6.7",
    "implementation-worker: §6.7 新增 HTTP expose_monitoring_graph 閘門 ≠ 保證 monitoring_graph 鍵；cross-ref 管線前提",
    "checker: 23 tests OK（context_entry／相關 B 線）"
  ],
  "results": {
    "guard_verdict": "allow",
    "checker_verdict": "accepted",
    "output_file": "workflow_upgrade/01_context-entry/50_context_entry_runbook.md §6.7"
  },
  "blockers": "無",
  "next_steps": "無；本票 doc_clarification 已收口",
  "forbidden_zone_note": "未改 AGENTS、ENGINEERING_CONTRACT、.cursor/rules、core、暗部"
}
```

---

## 6. 回傳 `dict` 契約（摘要）

### `validate_battle_report(data)`

| 欄位 | 說明 |
|------|------|
| `ok` | 必填欄位齊全且 status 合法 |
| `missing_fields` | 缺欄位列表 |
| `warnings` | 非阻斷建議 |

### `validate_archive(mode)`

| 欄位 | 說明 |
|------|------|
| `ok` | 可自動檢查之步驟均通過 |
| `mode` | `minimal`／`full` |
| `steps` | 逐步 `status`：`pass`／`fail`／`manual`／`skip` |

---

## 7. 與 Phase 3 銜接

| 時機 | 動作 |
|------|------|
| 接戰校準 | 先 `TASK_ROUTING`（第 8 步），再本制度（第 9 步）讀最近戰報 |
| 派工前 | `route_task` 得 `assignable` |
| 收兵 | `validate-report` → 執行 §封存協議 → `append-report` → 必要時 `new-review` |
| Cursor Subagents 票收兵 | 抽出 `battle_report_json_draft` → §3.4；`ticket_id` 對齊 `90_run_queue` 之 `TEST-SUB-00X` |

---

## 8. 維護

- 新增回顧類型：更新本檔、`ops_cycle_schema.json`、`ops_cycle.py` 測試。
- 封存步驟變更：須與 `AGENTS.md` 同步，並升 `ops_cycle_schema_version`。
- 版本：目前 **v1**。

**存檔**：`04_Workflows/OPS_CYCLE.md` · `04_Workflows/ops_cycle_schema.json`
