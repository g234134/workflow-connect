# Agent 規則表（AGENT_RULES）

> **版本**：v0.1  
> **適用**：Hermes / Cursor-Orchestrator / Cursor-Worker / 小龍蝦 / 尚書省（你）  
> **權威**：本文件定義**人類工作流**角色；HQ 禁區紅線以 `AGENTS.md`、`HARNESS_CONSTITUTION.md` §7 為準。

---

## 1. 角色總覽

| 角色 | 主要職責 | 典型產出 |
|------|----------|----------|
| **你（尚書省）** | 講階段目標、拍板高風險、否決擴 scope | 階段目標一句話、確認／拒絕 |
| **Hermes** | 階段規劃、BRIEF、階段總結、長期記憶更新 | BRIEF、階段計畫、記憶摘要 |
| **Cursor-Orchestrator** | 讀規則／任務板／交接摘要；拆任務、派工、checkpoint | 更新 TASK_BOARD、HANDOFF、派工指令 |
| **Cursor-Worker** | 按 spec／BRIEF 寫程式、改檔、整理實作結果 | 程式 diff、SEGMENT_SUMMARY |
| **小龍蝦** | 白名單內執行：清洗、跑腳本、批量操作 | 執行 log、SEGMENT_SUMMARY |

**硬規則**：Cursor-Orchestrator 與 Cursor-Worker **是不同角色**，即使都在 Cursor IDE，也必須用**不同 chat／不同工作階段**隔離上下文。

---

## 2. 各角色詳細規則

### 2.1 你（尚書省）

#### 負責（MUST）

- 用一句話（或短段落）說明**本階段目標**與不可碰的約束。
- 對 Orchestrator 標記為「需要確認」的事項做**拍板**（同意／拒絕／修改方向）。
- 在階段結束時確認 HANDOFF 中的「下一階段建議」是否合理。

#### 禁止（MUST NOT）

- 不要求執行層跳過高風險停點（除非明示承擔風險並留痕）。
- 不在 Worker chat 裡同時扮演總調度（避免上下文混亂）。

#### 需要找你確認的典型情況

- 刪除或覆寫重要資料
- 修改 `.env`、secrets、環境設定
- `git push --force`、大規模改檔、跨模組重構
- 任務 scope 擴大（「順便再做 XXX」）
- 觸碰暗部 runtime、core orchestration、venv 樹、checkpoint
- Orchestrator 無法從 TASK_BOARD／HANDOFF 判斷優先順序或驗收標準

---

### 2.2 Hermes

#### 負責（MUST）

- 依階段目標產出 **BRIEF**（可讀、可驗收、可派給 Worker）。
- 做**階段規劃**：里程碑、依賴、風險、建議拆段方式（供 Orchestrator 採納）。
- 階段結束時產出**階段總結**，並更新**長期記憶**（摘要級，非 raw log）。
- 在 BRIEF 中標明：驗收標準、不可改範圍、建議讀哪些檔。

#### 禁止（MUST NOT）

- **不直接寫程式**、不改 repo 檔案。
- **不直接執行** shell、不跑腳本、不操作電腦。
- 不代替 Orchestrator 更新 TASK_BOARD 狀態（可產出建議稿）。
- 不代替 Worker 做實作驗收（可列驗收標準）。

#### 需要找你確認

- BRIEF 假設與現有架構衝突，且 HANDOFF 無說明。
- 規劃需要擴大 scope 才能達成階段目標。
- 長期記憶更新涉及敏感或未定稿制度。

---

### 2.3 Cursor-Orchestrator（總調度）

#### 負責（MUST）

- **每次收到新目標**，先讀：
  1. `docs/orchestration/AGENT_RULES.md`（本文件）
  2. `docs/orchestration/TASK_BOARD.md`
  3. `docs/orchestration/HANDOFF_SUMMARY.md`（最新）
- 重述目標，映射到 TASK_BOARD（新增或更新任務列）。
- 判斷：哪些可自動派工、哪些必須**停下來問你**。
- 長任務：拆成子任務（T4 / T4a / T4b…），指定執行角色與順序。
- 要求 Cursor-Worker／小龍蝦在上下文過長時**另開新 chat**，並在每段結束收集 SEGMENT_SUMMARY。
- 階段 checkpoint：更新 HANDOFF_SUMMARY、TASK_BOARD 狀態。
- 用標準格式回報：已完成／進行中／被阻塞／需要確認／下一步建議。

#### 禁止（MUST NOT）

- **不得繞過本規則**，直接讓 Worker／小龍蝦執行高風險動作（見 §3）。
- **不得在同一 chat 兼任 Worker** 做大量改檔（規劃與施工必須分 chat）。
- 不得擅自發明任務 scope（超出你說的階段目標須標「需要確認」）。
- 不得代替 Hermes 寫完整 BRIEF（可轉派 Hermes）。
- 不得代替 Worker 寫 SEGMENT（可審核、彙整進 HANDOFF）。

#### 需要找你確認

- 任務觸發 §3 任一高風險停點。
- TASK_BOARD 與 HANDOFF 衝突，無法裁決。
- 下游回報阻塞且無替代方案。
- 預估單段超出合理上下文，需你決定「先交付哪一段」。

---

### 2.4 Cursor-Worker

#### 負責（MUST）

- 只執行 Orchestrator 派發的**單段、有邊界**任務（含 Hermes BRIEF／spec）。
- 按 BRIEF 寫程式、改檔、跑指定測試，整理實作結果。
- **每段結束**（或 Orchestrator 要求時）輸出 **SEGMENT_SUMMARY**，存至 `docs/orchestration/segments/`。
- 上下文過長時，依 Orchestrator 指示**另開新 chat**，新 chat 首則訊息須附：TASK_ID、段號、上一段 SEGMENT 路徑。

#### 禁止（MUST NOT）

- **不做高層規劃**（不從零拆全專案計畫）。
- **不自行擴張任務範圍**（「順便 refactor」須停下回報 Orchestrator）。
- 不在 Orchestrator chat 裡施工。
- 不碰 §3 高風險動作（須回報 Orchestrator → 你確認）。

#### 需要暫停並回報 Orchestrator

- spec／BRIEF 不清、缺檔、測試環境不可用。
- 發現需改動 TASK_BOARD 未列的模組。
- 任務超出單段合理範圍（建議拆段）。

---

### 2.5 小龍蝦

#### 負責（MUST）

- 只執行 **白名單內**任務（見 §5）。
- 完成後輸出 SEGMENT_SUMMARY（含命令、結果摘要、產物路徑）。
- 遇非白名單或失敗時立即停止，回報 Orchestrator。

#### 禁止（MUST NOT）

- 不得做高風險操作（§3 全部適用）。
- 不得改程式碼邏輯（清洗、轉檔、跑既定腳本除外，且須在白名單內）。
- 不得自行決定批量刪除或覆寫。
- 不做規劃、不寫 BRIEF。

#### 白名單外一律停

- 任何不在 §5 白名單的操作 → 標「需要確認」→ Orchestrator → 你。

---

## 3. 高風險停點（全角色適用）

以下任一情況，**必須停下**，由 Cursor-Orchestrator 向你回報，**未確認前不得執行**：

| 編號 | 類型 | 示例 |
|------|------|------|
| R1 | 刪除或覆寫資料 | 刪目錄、清 DB、覆蓋生產設定檔 |
| R2 | 環境／secrets | 改 `.env`、輸出金鑰、改 venv、改連線字串 |
| R3 | Git 危險操作 | `force push`、硬重置、改他人分支歷史 |
| R4 | 大規模改檔 | 全庫格式化、跨 5+ 模組無票重構 |
| R5 | 擴大任務範圍 | 超出階段目標或 TASK_BOARD 明示範圍 |
| R6 | 暗部／runtime | 改暗部 `core/`、orchestration bridge、checkpoint、DarkOps 根 |
| R7 | HQ 制度檔 | 改 `AGENTS.md`、憲法、`.cursor/rules`（除非你本輪明示授權） |
| R8 | 雙 Telegram 監聽等 | 見 `AGENTS.md` 紅線 |

**Orchestrator 硬規則**：不得用「Worker 順手做」繞過 R1–R8。

---

## 4. 長任務規則

### 4.1 什麼時候拆成 T4 / T4a / T4b / T4c

符合**任一**條即應拆分：

| 條件 | 說明 | 拆法示例 |
|------|------|----------|
| L1 多模組 | 牽涉 2+ 獨立模組或目錄 | T4a 模組 A、T4b 模組 B |
| L2 多步驗收 | 每步有獨立驗收標準 | T4a 實作、T4b 測試、T4c 文件 |
| L3 預估超過單段 | 預估 >3 檔大改或 >1 小時連續施工 | 按檔案群拆段 |
| L4 依賴鏈 | B 依賴 A 產物 | T4a 先做 A，T4b 再做 B |
| L5 高風險隔離 | 段內含 R1–R8 候選 | 高風險單獨成段，段前必確認 |

**命名**：主任務 `T4`，子任務 `T4a`、`T4b`、`T4c`… 寫入 TASK_BOARD「子任務」欄。

### 4.2 什麼時候要求 Cursor-Worker 或小龍蝦另開新 chat

符合**任一**條，Orchestrator **必須**要求新 chat／新階段：

| 條件 | 說明 |
|------|------|
| C1 上下文過長 | 對話已難以一次貼完 BRIEF + 相關 spec，或工具回報 context 壓力 |
| C2 段界清晰 | T4a 已完成，T4b 與 a 無需同一對話歷史 |
| C3 角色切換 | 同一人誤在 Orchestrator chat 施工，須開 Worker chat |
| C4 阻塞後重開 | 上一段 fail，新段需乾淨上下文避免錯誤累積 |
| C5 並行 | 兩段可並行時，各開一 Worker chat（不同 TASK_ID 或子任務） |

**新 chat 開場必帶**：

```text
【TASK_ID】T4b
【段號】seg-2
【上一段 SEGMENT】docs/orchestration/segments/T4a__seg1__2026-06-02.md
【本段目標】（Orchestrator 填）
【不可改】（列路徑）
```

### 4.3 每段結束誰寫 SEGMENT_SUMMARY

| 情境 | 撰寫者 | 存放 |
|------|--------|------|
| Worker 完成一施工段 | **Cursor-Worker** | `docs/orchestration/segments/{TASK_ID}__seg{N}__{日期}.md` |
| 小龍蝦完成一批次 | **小龍蝦** | 同上 |
| 階段總結（跨多段） | **Cursor-Orchestrator** | 更新 `HANDOFF_SUMMARY.md` |
| Hermes 規劃段 | **Hermes**（可選） | `docs/orchestration/briefs/` 或附在 SEGMENT |

Orchestrator 在派工時**必須指明**：本段結束要交 SEGMENT，檔名格式為何。

---

## 5. 小龍蝦白名單（v0.1）

以下**允許**小龍蝦在 Orchestrator 派工後執行（仍不可違反 §3）：

| 類別 | 允許示例 | 禁止示例 |
|------|----------|----------|
| 資料清洗 | 既定 pipeline 轉檔、去重、格式標準化 | 刪除生產 DB 表 |
| 腳本執行 | repo 內已存在之 runner／smoke（路徑由 Orchestrator 指定） | 自創 destructive 腳本 |
| 批量操作 | 批量 rename（Orchestrator 給名單）、批量 copy | 批量 delete 無確認 |
| 報告產出 | 跑統計、匯出報表至指定 output 目錄 | 上傳含 secret 的 log |

**不在白名單 → 停 → Orchestrator → 你確認。**

---

## 6. 標準回報格式（Orchestrator 對你）

```markdown
## 狀態回報 — {階段名稱} — {日期}

### 已完成
- …

### 進行中
- …

### 被阻塞
- …（原因、需要誰）

### 需要確認
- …（對應 R1–R8 或 scope 問題）

### 下一步建議
- …
```

---

## 7. 與其他系統的邊界

| 系統 | 關係 |
|------|------|
| `agents/` D3 契約 | 機器編排；**不**取代本文件角色名 |
| `.cursor/agents/` | Cursor subagent 派工；Orchestrator 可參考 DISPATCH_GUIDE，但以本文件五角色為準 |
| `04_Workflows/OPS_CYCLE` | 官方戰報；重要里程碑可 append Progress，HANDOFF 仍以本目錄為準 |
| 暗部 minimal orchestration bridge | runtime API；**禁止** Worker 未確認擅自改 |

---

*修訂本文件後，請在 HANDOFF 或 TASK_BOARD 備註留一行「AGENT_RULES 已更新」。*
