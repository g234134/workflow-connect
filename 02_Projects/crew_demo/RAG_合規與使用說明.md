# RAG 資料夾與「爬網／搜尋」合規須知（一般說明，非法律意見）

本專案提供的 **`rag_ingest_local.py` 只做一件事**：讀取你放在 **`D:\rag檔案庫`**（或 `.env` 的 `RAG_ROOT`）裡的 **本機檔案**，建立向量索引。**不會**自動對外連線爬網、不會批次下載別人網站。

---

## 一、為什麼要先談「反爬／合法性」？

自動「爬取／大量抓取」公開網頁，仍可能牽涉：

| 面向 | 你需要先想清楚的重點 |
|------|----------------------|
| **網站規則** | `robots.txt`、網站《使用條款》是否禁止自動抓取、是否禁止商用／大量抓取。 |
| **著作權** | 全文複製、重新發布、訓練用途，與「個人研究／合理使用」範圍不同；不要假設「看得到就能任意存」。 |
| **個資與隱私** | 若內容含他人個資，保存與再利用可能受個資法規範。 |
| **技術反制** | 驗證碼、登入牆、IP 封鎖、速率限制 —— 繞過可能從「技術問題」變成「合規／刑事風險」的爭議點（依管轄法律與事實認定而異）。 |
| **服務條款** | 很多網站明文禁止用自動化工具抓內容；違反條款可能導致帳號封鎖或民事爭議。 |

**以上不能取代律師意見**；若你做商用、對外提供服務、或抓取量大，建議諮詢專業法律顧問。

---

## 二、較安全的資料取得方式（由保守到需自行評估）

1. **只使用你已合法擁有的檔案**  
   自己寫的、已購買授權的 PDF、公司內部允許使用的文件、**你自己另存**的網頁（瀏覽器「另存 HTML／列印 PDF」）放置於 `PDF` / `網頁` / `文字` 分類資料夾。
2. **官方 API／授權資料源**  
   例如新聞社、政府開放資料、付費資料授權。
3. **搜尋聚合 API（付費／有 ToS）**  
   例如 Tavily、Firecrawl 等 —— 仍要閱讀其條款與允許用途；通常比「自己寫爬蟲硬抓」好管理。
4. **避免**  
   對有登入／付費牆／明確禁止自動化的網站做繞過抓取。

---

## 三、本專案腳本的分工

| 腳本 | 做什麼 | 會不會對外爬網？ |
|------|--------|------------------|
| `rag_ingest_local.py` | 讀 **本機** pdf / txt / md / html，chunk，用 **Ollama 嵌入**，寫入 **Chroma** | **否** |
| `rag_search_local.py` | 對已建立的索引做語意檢索 | **否**（只查本機索引） |
| `main.py` + `ENABLE_TOOLS` | 若開 Tavily／Firecrawl，那是 **API 供應商**去抓／搜 —— 依其條款與你的帳戶 | **是（經第三方 API）** |

---

## 四、建議目錄（你已建立）

`D:\rag檔案庫`  

- `PDF` — PDF  
- `網頁` — 建議放 **你已合法取得的** `.html` / 或先轉成 `.md/.txt`  
- `文字` — `.txt` / `.md`

腳本會 **遞迴掃描** `RAG_ROOT` 底下這些副檔名（索引目錄 `.chroma_index` 會自動略過相近規則）。

---

## 五、第一次使用（本機入庫 + 檢索）

1. 確認 Ollama 已跑，且已 `ollama pull nomic-embed-text`（或你在 `.env` 指定的嵌入模型）。  
2. 把檔案放进 `D:\rag檔案庫`。  
3. 入庫：

```powershell
cd D:\我的專案\crew_demo
& D:\虛擬環境\venv檔案\Scripts\Activate.ps1
python .\rag_ingest_local.py
```

4. 檢索測試：

```powershell
python .\rag_search_local.py "你的問題"
```

向量庫預設在：`D:\rag檔案庫\.chroma_index`（可用環境變數 `CHROMA_PERSIST_DIR` 改）。

---

## 六、與 CrewAI 結合（下一步）

目前入庫與 `main.py` 仍是 **分開的**。若要「研究員先查 RAG 再寫稿」，需要再加 **自訂 Tool** 呼叫 `rag_search_local` 的查詢邏輯；你若要做，我可以依你現在的 `main.py` 直接接上去。

---

## 七、需要「網站內容」時建議怎麼做？（`rag_fetch_urls.py`）

本專案**不做整站爬蟲**；改為你維護一份 **允許清單** `D:\rag檔案庫\urls_allowlist.txt`（一行一個 `https://...`），再執行：

```powershell
cd D:\我的專案\crew_demo
& D:\虛擬環境\venv檔案\Scripts\Activate.ps1
python .\rag_fetch_urls.py
```

- **建議路徑（預設 `auto`）**：若 `.env` 有 `FIRECRAWL_API_KEY`，會用 **Firecrawl** 轉成乾淨 Markdown 存到 `D:\rag檔案庫\網頁\`（或已存在的 `網頁` 資料夾）。  
- **沒有 Firecrawl 時**：不要硬爬；可改填 key，或僅在確認授權後用 `python rag_fetch_urls.py --mode direct --i-know-direct-risk`（會讀 `robots.txt` 的 `User-Agent` 判斷，**不通過就跳過**；存成 HTML 供之後入庫）。

**仍然要遵守**：條款、著作權、與你使用目的。清單範本見 `D:\rag檔案庫\urls_allowlist.example.txt`（可複製改名為 `urls_allowlist.txt` 再編輯）。

抓下來之後再跑 `python rag_ingest_local.py` 建索引。

---

## 八、蒐集 GitHub 資料（建議路徑）

1. **首選：官方 API**（`rag_fetch_github.py`）  
   讀 `D:\rag檔案庫\github_repos.txt`（每行 `owner/repo` 或 `https://github.com/owner/repo`），用 **GET /repos/{owner}/{repo}/readme** 取 README 文字，**不**用瀏覽器硬爬 `github.com` 的 HTML。  
   在 `.env` 裡建議填 **`GITHUB_TOKEN`**（PAT），可顯著提高每小時可呼叫次數；仍須遵守 [GitHub 條款](https://docs.github.com/en/site-policy) 與各 repo 的 **LICENSE**。

2. **要整份原始碼時：`git clone`（本機）**  
   開源專案常見做法；授權以 repo 內 `LICENSE` 為準。Clone 後把要給 RAG 的檔案（如 `docs/*.md`）放进 `D:\rag檔案庫\文字` 或子目錄，再 `python rag_ingest_local.py`。

3. **不建議**  
   用一般「網頁爬蟲」掃 `github.com` 大量頁面，容易觸及反爬、ToS 與速率限制；**API / git** 才是穩定介面。

4. **更大量研究用**（非本專案已內建）  
   [GH Archive](https://www.gharchive.org/)、BigQuery 公開資料集等，屬另一天地，需再規劃儲存與法遵。
