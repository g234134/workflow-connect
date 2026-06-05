# HQ-P3-TASK-ROUTING — 交付報告

> **票號**：`HQ-P3-TASK-ROUTING`  
> **執行**：大唐副官（Phase 3）  
> **日期**：2026-05-19  
> **依據**：`HQ_PHASE1_FINALIZATION_ORDER.md` §六；Phase 1 定稿三件套 + W5

---

## 摘要

建立**多智能體任務路由制度**：副官可依 `task_type` 或任務描述，自動解析應派發之 **HQ worker**、**cabin**、**dark_agent** 與建議 **runners**；DarkOps 閘門維持 `blocked` 時回傳 `assignable: false`。

---

## 交付物

| 路徑 | 說明 |
|------|------|
| `04_Workflows/TASK_ROUTING.md` | 人讀制度（任務類型表、副官流程、dict 契約） |
| `04_Workflows/task_routing_table.json` | 機器讀路由表（v1，14 條路由 + default） |
| `02_Agents_Core/task_routing.py` | `route_task()` / `load_routing_table()` |
| `04_Workflows/_route_task.py` | 副官 CLI |
| `04_Workflows/test_task_routing.py` | 單元測試 |
| `04_Workflows/Master_Map.json` | `version` **2.62**；`artifacts` + `runners` 登錄 |
| `AGENTS.md` | §初始化校準第 8 步「任務路由校準」 |

---

## 驗收命令

```powershell
cd D:\大唐三省六部
python .\04_Workflows\test_task_routing.py
python .\04_Workflows\_route_task.py --type hq.governance --pretty
python .\04_Workflows\_route_task.py --type dark.infra --pretty
python .\04_Workflows\_route_task.py --text "啟動 scout 偵察" --pretty
```

**預期**：

- 測試全 PASS  
- `hq.governance` → `HQ-Governance-Worker`，`assignable: true`  
- `dark.infra` → `DarkOps-Worker` + `gov_core_system`，`assignable: false`  
- scout 描述 → `chariot.scout` + `gov_agency`

---

## 裁決待項（非本票範圍）

- 解禁 DarkOps：改 `task_routing_table.json` → `phase_gates.dark_ops_worker` 為 `active`（須尚書省另票）  
- `HQ-P4-OPS-CYCLE` 戰報／封存自動化
