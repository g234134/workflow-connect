# D 槽總調度分析主計畫

## 任務目標
全面分析 D 槽所有專案的功能性與檔案完整性，記錄問題但不修改程式碼。

## 分析範圍邊界

| 範圍 | 包含 | 邊界 |
|------|------|------|
| **專案代碼** | Python、JavaScript、TypeScript、Shell、Config | 不修改任何原始碼 |
| **檔案完整性** | 語法正確性、檔案完整度、引用依賴 | 不刪除/移動檔案 |
| **結構化資料** | JSON、YAML、TOML、TXT、MD | 不重構目錄結構 |
| **媒體/備份** | 遊戲庫、下載、備份目錄 | 僅記錄問題 |

## 分析方法

1. **結構掃描** → 列出目錄樹與檔案清單
2. **語法驗證** → Python(py_compile)、JavaScript(Node)、JSON/Shell
3. **完整性檢查** → 對照 import/require 是否存在、檔案是否截斷
4. **問題記錄** → 每項問題附 [嚴重度] + [檔案路徑] + [描述]

## Wave 調度計畫 (5 Waves × 3-5 Tickets)

```
WAVE 1: 大唐三省六部 (3 tickets)
  ├─ T1: 目錄掃描 + 檔案清單 + 結構分析
  ├─ T2: Python/JS 語法檢查 + import 完整性
  └─ T3: 問題彙整報告 → 代碼檢查員審查

WAVE 2: 總大腦加免費token (OmniRoute) (4 tickets)
  ├─ T1: 目錄掃描 + 結構分析
  ├─ T2: Python 語法 + import 完整性
  ├─ T3: JS/Config 語法 + 完整性
  └─ T4: 問題彙整報告 → 代碼檢查員審查

WAVE 3: AI_HUB + 小型專案 (4 tickets)
  ├─ T1: AI_HUB 完整分析
  ├─ T2: 我的專案 + 虛擬環境 + rag檔案庫
  ├─ T3: OmniRoute compression 功能性測試
  └─ T4: 問題彙整報告 → 代碼檢查員審查

WAVE 4: 系統/媒體/備份目錄 (4 tickets)
  ├─ T1: 遊戲庫 + 鉍戲庫 結構掃描
  ├─ T2: Hermes/hermes-workspace/ollama 結構
  ├─ T3: 666LAG_Backup/tank_downloads/invalid 檢查
  └─ T4: 問題彙整報告 → 代碼檢查員審查

WAVE 5: 跨專案整合 + 最終報告 (3 tickets)
  ├─ T1: 跨專案依賴分析 + 重複檔案檢測
  ├─ T2: 全部問題分類統計
  └─ T3: 最終總報告產出
```

## 問題分級標準

| 等級 | 標籤 | 說明 |
|------|------|------|
| 🔴 **CRITICAL** | `critical` | 檔案損毀、語法錯誤、不可執行 |
| 🟠 **MAJOR** | `major` | import 缺失、引用斷鏈、配置錯誤 |
| 🟡 **MINOR** | `minor` | 類型提示遺漏、格式問題、未使用變數 |
| 🔵 **INFO** | `info` | 重複檔案、命名不一致、可以改進 |

## 產出文件結構

> **實際路徑**（repo 相對）：`04_Workflows/總檔案紀錄/`  
> （舊稿曾寫 `D:\總檔案紀錄\`，已廢止；勿再使用該絕對路徑。）  
> **B′（2026-07-12）**：Wave 歷史進 `_archive/`；任務根改名 `tasks/`（原「任務發布中心」）。

```
04_Workflows/總檔案紀錄/
├── README.md                 # 導航（兩套系統關係）
├── CONSOLIDATION_ANALYSIS.md # 整合分析（方案 A/B/C）
├── _framework/               # 主框架與計畫（永久參考）
│   └── MASTER_PLAN.md
├── _archive/                 # Wave 歷史歸檔
│   ├── Wave1-大唐三省六部/
│   │   ├── W1_T1_目錄結構.md
│   │   ├── W1_T2_語法檢查.md
│   │   └── W1_T3_問題報告.md
│   ├── Wave2-OmniRoute/
│   │   ├── W2_T1_目錄結構.md       # 摘要版
│   │   ├── W2_T1_目錄結構_FULL.md  # 原始 dump（gitignore）
│   │   ├── W2_T2_Python檢查.md
│   │   ├── W2_T3_Config檢查.md
│   │   └── W2_T4_問題報告.md
│   ├── Wave3-AI_HUB/
│   ├── Wave4-系統媒體/
│   └── Wave5-跨專案/
│       └── W5_T2_最終總報告.md
└── tasks/                    # 修復任務（執行紀錄；8/8 done）
    ├── RULES.md              # 規範（舊名 00_規則與使用說明.md）
    └── INDEX.md              # 看板（舊名 01_任務總覽.md）
```
