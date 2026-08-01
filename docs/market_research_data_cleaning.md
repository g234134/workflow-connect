# 數據清洗市場調研報告
> 2026-07-18 | 目標：簡單、低法律風險、能賺錢

---

## 一、市場現狀

### 數據清洗服務市場規模
- 全球數據清洗市場 2025 年約 **$3.2B**，年增率 15-20%
- 中國市場約占 15-20%，約 **$500M**
- 主要驅動力：AI 訓練數據需求暴增、企業數位轉型

### 誰在買？
1. **AI 公司** — 需要乾淨的訓練數據（最大買家）
2. **電商** — 產品目錄清洗、價格比對
3. **金融** — 交易數據、客戶資料清洗
4. **政府/研究** — 公開數據整理
5. **中小企業** — Excel/CSV 清洗（最簡單的客戶）

---

## 二、低風險方向分析

### 方向 A：Excel/CSV 清洗服務 ⭐⭐⭐⭐⭐
- **複雜度**：★☆☆☆☆（最簡單）
- **法律風險**：☆☆☆☆☆（幾乎為零）
- **市場需求**：★★★★★（巨大）
- **利潤率**：★★★★☆

**為什麼低風險？**
- 客戶提供自己的數據，你只做清洗
- 不涉及爬蟲、不涉及第三方數據
- 不觸及個資法（客戶自己負責）
- 不需要特殊牌照

**具體服務：**
- 去重、補空值、格式統一
- 多表合併、欄位標準化
- 編碼轉換（Big5→UTF-8）
- 數據驗證、異常值標記

**收費模式：**
- Fiverr/Upwork：$10-50/件（簡單）$100-500/件（複雜）
- 台灣接案：NT$500-5000/件
- 月費制：NT$3000-10000/月（固定客戶）

---

### 方向 B：公開數據整理 ⭐⭐⭐⭐
- **複雜度**：★★☆☆☆
- **法律風險**：★☆☆☆☆（公開數據，合理使用）
- **市場需求**：★★★★☆
- **利潤率**：★★★☆☆

**具體服務：**
- 政府公開數據（data.gov.tw、data.gov）清洗整理
- 學術論文資料集整理
- 開源資料集清洗（HuggingFace、Kaggle）
- 新聞/文章語料庫整理

**收費模式：**
- 賣清洗後的資料集（$5-50/份）
- 訂閱制更新（$10-30/月）
- 客製化整理（$100-500/案）

---

### 方向 C：網頁數據結構化 ⭐⭐⭐
- **複雜度**：★★★☆☆
- **法律風險**：★★☆☆☆（需注意 robots.txt、個資）
- **市場需求**：★★★★☆
- **利潤率**：★★★★☆

**具體服務：**
- 網頁 HTML 轉結構化 JSON/CSV
- 產品目錄抓取+清洗
- 地址/電話等聯繫資訊整理
- 新聞/文章內容提取

**法律注意事項：**
- 遵守 robots.txt
- 不抓個資（姓名、電話、地址需脫敏）
- 不繞過付費牆
- 不抓版權內容全文

---

### 方向 D：AI 訓練數據清洗 ⭐⭐⭐⭐⭐
- **複雜度**：★★★☆☆
- **法律風險**：★★☆☆☆（需注意版權）
- **市場需求**：★★★★★（爆發中）
- **利潤率：★★★★★（最高）**

**具體服務：**
- 文本去重（exact + fuzzy dedup）
- 語言過濾（保留特定語言）
- 品質過濾（移除低品質文本）
- 格式轉換（JSONL、Parquet、Arrow）
- 標籤清洗（修正錯誤標籤）

**收費模式：**
- 按量計費：$0.01-0.10/1K tokens
- 批次處理：$100-1000/批
- 月費制：$500-5000/月

**法律注意：**
- 使用公開數據集（OSI 授權）
- 不抓付費內容
- 脫敏處理個資
- 保留數據來源記錄

---

## 三、推薦策略（優先級排序）

### 第一優先：Excel/CSV 清洗（立即開始）
1. 在 Fiverr/Upwork 開帳號
2. 上架 3-5 個 data cleaning gig
3. 用我們的工具自動化 80% 的工作
4. 目標：第一個月賺 $100-300

### 第二優先：AI 訓練數據（1-2 週後）
1. 用我們的 web pipeline 自動抓公開數據
2. 清洗成 JSONL 格式
3. 上架 HuggingFace datasets
4. 目標：建立被動收入

### 第三優先：公開數據整理（同步進行）
1. 整理台灣/中國政府公開數據
2. 上架 Kaggle/HuggingFace
3. 建立 reputation

---

## 四、法律風險最小化

### 絕對不碰
- 個人資料（姓名、身分證、電話、地址）
- 付費內容（繞過付費牆）
- 版權內容（全文複製）
- 政府機密/非公開資料
- 金融機密（信用卡、銀行帳號）

### 安全做法
- 只處理客戶提供的數據
- 使用公開、OSI 授權的數據
- 脫敏處理（hash、匿名化）
- 保留完整審計軌跡
- 不存儲客戶數據（處理完即刪）

---

## 五、工具需求

### 我們已有的
- ✅ web_crawler.py — 爬蟲（GitHub API + HTML）
- ✅ web_cleaner.py — 清洗 + 去重
- ✅ web_pipeline.py — 自動化管線
- ✅ Asset_Value_Evaluator — 品質評分

### 還需要建的
- [ ] Excel/CSV 清洗腳本（openpyxl + pandas）
- [ ] JSONL 轉換腳本（AI 訓練數據格式）
- [ ] Fiverr/Upwork gig 模板
- [ ] 客戶數據處理 SOP
- [ ] 自動化報價系統

---

## 六、結論

**最簡單、最低風險、最快賺錢的方向是 Excel/CSV 清洗服務。**

理由：
1. 零法律風險（客戶提供數據）
2. 技術門檻最低（pandas 就能搞定）
3. 市場需求穩定（每個企業都有髒數據）
4. 可以立即開始（今天就上架 Fiverr）
5. 工具已經有了（我們的管線可以自動化）

**下一步行動：**
1. 建 Excel/CSV 清洗腳本
2. 寫 Fiverr gig 描述
3. 上架 3 個 service
4. 等第一筆訂單

---

## 附錄：MCP 整合報告（2026-07-19 更新）

### 找到的 MCP 伺服器

| MCP | 語言 | Stars | 核心功能 | 適用性 |
|-----|------|-------|---------|--------|
| `jwadow/mcp-excel` | Python | 39 | Excel 分析（原子操作、過濾、聚合、驗證） | ✅ **最佳** |
| `angrysky56/data-forge-mcp` | Python | 2 | 完整數據科學管線（清洗、驗證、profiling、SQL） | ⚠️ Python 3.13+ 要求 |
| `opendocswork-mcp` | Rust | 154 | Office 文件處理（Excel/Word/PPT） | ⚠️ Rust 原生，整合複雜 |
| `@negokaz/excel-mcp-server` | Node.js | — | 簡單 Excel 讀寫 | ⚠️ 功能有限 |

### `jwadow/mcp-excel` 工具清單（已驗證可用）

| 工具 | 用途 | 數據清洗對應 |
|------|------|------------|
| `inspect_file` | 檢查檔案結構（格式、sheet、行列數） | **Stage 0**：檔案探索 |
| `get_column_names` | 取得欄位名稱 | **Stage 0**：欄位映射 |
| `find_nulls` | 找出空值（含索引、百分比） | **Stage 1**：空值偵測 |
| `find_duplicates` | 找出重複列 | **Stage 1**：重複偵測 |
| `get_column_stats` | 欄位統計（mean/median/std/quartiles） | **Stage 2**：異常值偵測 |
| `filter_and_count` | 條件過濾計數 | **Stage 2**：資料篩選 |
| `get_unique_values` | 唯一值列表 | **Stage 1**：類別分析 |
| `get_value_counts` | 值頻率統計 | **Stage 2**：分佈分析 |
| `group_by` | 分組聚合 | **Stage 3**：資料彙總 |
| `detect_outliers` | 異常值偵測 | **Stage 2**：異常值處理 |

### 整合架構

```
客戶端 Excel/CSV
    ↓
[mcp-excel] inspect_file → 檔案結構報告
    ↓
[mcp-excel] find_nulls → 空值報告
    ↓
[mcp-excel] find_duplicates → 重複報告
    ↓
[mcp-excel] get_column_stats → 統計摘要
    ↓
[mcp-excel] detect_outliers → 異常值報告
    ↓
清洗腳本（pandas）→ 修復空值/去重/標準化
    ↓
[mcp-excel] validate → 驗證清洗結果
    ↓
輸出乾淨 Excel/CSV + 清洗報告
```

### 環境配置

```bash
# 安裝 mcp-excel
git clone https://github.com/jwadow/mcp-excel.git
cd mcp-excel && python -m venv venv && venv\Scripts\activate
pip install -e .

# 注意：必須清除 PYTHONPATH（避免 Hermes venv 污染）
PYTHONPATH="" python your_script.py
```

### 下一步

1. 建 `core/mcp_excel_cleaner.py` 封裝 mcp-excel 工具
2. 建 `core/mcp_excel_pipeline.py` 串接 Stage 0-3
3. 寫 Fiverr gig 描述（基於 MCP 工具能力）
4. 上架 3 個 service
