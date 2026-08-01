# 總檔案紀錄 — 導航

> **用途**：D 槽專案盤點（Wave 1–5）與後續修復任務的文件根。  
> **狀態**：Wave 分析完成；任務中心 **8/8 done**（2026-07-08）。  
> **整合**：見 [CONSOLIDATION_ANALYSIS.md](./CONSOLIDATION_ANALYSIS.md)（**方案 A**／**B′**／**B3** 已做；方案 C 不做）。

---

## 兩套系統（勿混用編號）

| 系統 | 目錄 | 性質 | 編號 |
|------|------|------|------|
| **Wave 報告** | `_archive/Wave1` … `Wave5` | 發現什麼問題（歷史分析） | `W{wave}_T{n}_*.md` |
| **任務中心** | `tasks/` | 如何修復（執行紀錄） | `T{phase}.{seq}_*.md` |
| **框架** | `_framework/` | 永久參考（方法／計畫） | — |

同一問題常成對出現：**Wave 記發現 → Task 記修復**（例如 W3 問題彙整 ↔ T1.1～T2.2）。以任務總覽的「問題 ID 對照」為準，不必維護兩份敘事。

### 與 `04_Workflows/tickets/` 的區別

| | `總檔案紀錄` Wave W1–W5 | `04_Workflows/tickets/` |
|--|-------------------------|-------------------------|
| 範圍 | D 槽目錄／配置盤點 | 戰車開發票據（Wave 1–12+ 等） |
| 編號 | 本目錄內 Wave／Task | 另一套 ticket 體系 |
| **禁止** | 用本目錄 W 編號去對 `tickets/` 同名票 | 反之亦然 |

---

## 快速入口

| 想找… | 去哪 |
|-------|------|
| 本目錄怎麼讀 | 本 README |
| 分析框架／Wave 計畫 | [`_framework/MASTER_PLAN.md`](./_framework/MASTER_PLAN.md) |
| 修復任務進度 | [`tasks/INDEX.md`](./tasks/INDEX.md) |
| 任務規則 | [`tasks/RULES.md`](./tasks/RULES.md) |
| Wave 最終總報告 | [`_archive/Wave5-跨專案/W5_T2_最終總報告.md`](./_archive/Wave5-跨專案/W5_T2_最終總報告.md) |
| Wave 6 D 槽整合 | [`_archive/Wave6-D槽整合/W6_T3_整合執行報告.md`](./_archive/Wave6-D槽整合/W6_T3_整合執行報告.md) |
| 整合方案與病灶 | [`CONSOLIDATION_ANALYSIS.md`](./CONSOLIDATION_ANALYSIS.md) |

---

## 目錄一覽（B′ 後）

```
總檔案紀錄/
├── README.md                    ← 你在這裡
├── CONSOLIDATION_ANALYSIS.md
├── _framework/                  ← 永久
├── _archive/                    ← Wave 1–5 歷史
│   ├── Wave1-大唐三省六部/
│   ├── Wave2-OmniRoute/         ← W2_T1 僅摘要；FULL dump 本機
│   ├── Wave3-AI_HUB/
│   ├── Wave4-系統媒體/
│   ├── Wave5-跨專案/
│   └── Wave6-D槽整合/           ← 2026-07-25 D 槽根目錄整合
└── tasks/                       ← 原「任務發布中心」（done；B3：`INDEX`／`RULES`）
```

### W2_T1 體積說明

- 日常閱讀：[`_archive/Wave2-OmniRoute/W2_T1_目錄結構.md`](./_archive/Wave2-OmniRoute/W2_T1_目錄結構.md)（摘要，少於 200 行）
- 完整原始樹：同目錄 `W2_T1_目錄結構_FULL.md`（約 1.2MB；根 `.gitignore` 已忽略 `*_FULL.md`）

---

## 生命週期

| 層級 | 處置 |
|------|------|
| `_framework/` | 保留、可修路徑／計畫 |
| `_archive/` | Wave 歷史歸檔（B′ 已執行；不刪） |
| `tasks/` | 修復任務紀錄；總覽為 SSOT |
| 精簡 `INDEX`／`RULES` 檔名 | **B3 已做**（2026-07-12） |
| 刪除 Wave／合併進 Task | **方案 C 不做** |
