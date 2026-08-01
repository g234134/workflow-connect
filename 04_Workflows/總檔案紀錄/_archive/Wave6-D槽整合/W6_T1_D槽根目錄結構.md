# WAVE 6 — T1: D 槽根目錄結構（摘要）

> 更新時間: 2026-07-25  
> 完整 tree dump: 同目錄 `W6_T1_FULL.txt`（本機保留）

---

## 整合後 D:\ 根目錄

```
D:\
├── 大唐三省六部\     # AI Workflow 治理 SSOT（~20 GB）
├── Hermes\           # Tools 衛星 — Hermes Agent runtime（~4.4 GB）
├── _infra\           # Tools 衛星 — OmniRoute API gateway port 20128（~7.5 GB）
├── 遊戲庫\             # Steam + Riot 遊戲（~37 GB）
├── SteamLibrary\     # Steam 函式庫（~3.7 GB）
└── (已清除 AI_HUB、鉍戲庫)
```

**已移除（2026-07-25 整合）**：`tmp`、`hermes-workspace`、`666LAG_Backup`、`u5927`、`鉍戲庫`

---

## 各目錄功用

| 目錄 | 大小 | 類型 | 功用 |
|------|------|------|------|
| **大唐三省六部** | ~20 GB | 治理 repo | 六部架構、LangGraph 編排、tabular MVP、總檔案紀錄 |
| **Hermes** | ~4.4 GB | Tools 衛星 | Nous Research Hermes Agent：gateway、MCP、skills、memories |
| **_infra** | ~7.5 GB | Tools 衛星 | OmniRoute Next.js API proxy（port 20128） |
| **遊戲庫** | ~37 GB | 遊戲 | Steam / Riot Games 安裝目錄 |
| **SteamLibrary** | ~3.7 GB | 遊戲 | 額外 Steam libraryfolder |
| **AI_HUB** | ~0 | 已清除 | 原 `.cache` 已刪（2026-07-25 後續確認） |

---

## 邏輯歸屬（Master_Map external_satellites）

| 衛星 | 物理路徑 | 邏輯歸屬 |
|------|----------|----------|
| hermes | `D:/Hermes` | Tools 域 |
| omniroute | `D:/_infra` | Tools 域 |

詳見 `04_Workflows/Master_Map.json` → `external_satellites`。

---

## 相關報告

- [W6_T2_大唐內部結構摘要.md](./W6_T2_大唐內部結構摘要.md)
- [W6_T3_整合執行報告.md](./W6_T3_整合執行報告.md)
- [drive_root_consolidation_plan.yaml v3](../../drive_root_consolidation_plan.yaml)
