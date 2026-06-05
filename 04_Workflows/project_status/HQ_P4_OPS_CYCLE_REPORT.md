# HQ-P4-OPS-CYCLE — 交付報告

> **票號**：`HQ-P4-OPS-CYCLE`  
> **執行**：大唐副官（Phase 4）  
> **日期**：2026-05-19  
> **依據**：`HQ_PHASE1_FINALIZATION_ORDER.md` §六；`AGENTS.md` §封存協議

---

## 摘要

建立**營運週期制度**：副官可依票號維護 **戰報（validate／render／append）→ 封存清單（minimal／full）→ 回顧稿（四類模板）** 的完整記錄鏈，與 Phase 3 任務路由銜接。

---

## 交付物

| 路徑 | 說明 |
|------|------|
| `04_Workflows/OPS_CYCLE.md` | 人讀制度（三階段流程、欄位契約） |
| `04_Workflows/ops_cycle_schema.json` | 機器讀 schema（戰報欄位、9 步封存、4 類回顧） |
| `02_Agents_Core/ops_cycle.py` | `validate_battle_report()`／`append_battle_report()`／`validate_archive()` 等 |
| `04_Workflows/_ops_cycle.py` | 副官 CLI（子命令） |
| `04_Workflows/test_ops_cycle.py` | 單元測試 |
| `04_Workflows/project_status/reviews/` | 回顧稿目錄 |
| `04_Workflows/Master_Map.json` | `version` **2.63**；artifacts／runners 登錄 |
| `AGENTS.md` | §初始化校準第 9 步；§封存協議戰報 CLI 銜接 |

---

## 驗收命令

```powershell
cd D:\大唐三省六部
python .\04_Workflows\test_ops_cycle.py
python .\04_Workflows\_ops_cycle.py validate-archive --mode minimal --pretty
python .\04_Workflows\_ops_cycle.py paths --pretty
```

**預期**：

- 測試全 PASS  
- `validate-archive --mode minimal` → `ready_for_archive: true`（自動檢查通過；含 manual 步驟提示）  
- `paths` 回傳 progress／master_status／schema 等絕對路徑

---

## 裁決待項（非本票範圍）

- 與 Governance Agent 自動寫回 `master_status.md` 對接（見 Progress G1 下一步）  
- `HQ-P2-RULES-FINALIZE` 升格定稿令  
- 全量封存時 war_status／指紋仍須人工執行既有 runner（`_register_fingerprints.py`）
