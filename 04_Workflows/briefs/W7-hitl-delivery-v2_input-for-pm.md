# W7+ HITL / Delivery / Notify 體驗 — PM Input Brief

> **文件定位**：給 PM / 產品團隊的輸入文件，基於 W6 落地現況，協助設計下一輪體驗。
> **版本**：v0.1 · 2026-06-16
> **作者**：Product-facing Engineer

---

## TL;DR

W6 已經完成了「人工審批 → 系統續跑」的基礎骨架，以及通知事件流的本地 stub。現在需要 PM 決定：**下階段體驗要做到什麼程度？** 本文件列出 3 個建議優先回答的問題，協助規劃 W7+ 的體驗路線圖。

---

## 一、Current Capabilities（現在能做什麼）

### 1. Checkpoint A — 進入點人工確認

**使用情境**：系統解析客戶需求後、正式執行前，需要人工確認理解正確。

**現在的體驗**：
- CLI 會停在 Checkpoint A，產生一個 JSON 檔案到 `outbox/`
- 操作者用 `run_hitl_checkpoint_cli --apply-decision approve` 核准
- 核准後用同一個 orchestrator CLI 加 `--resume-checkpoint <path>` 續跑後續步驟

**限制**：
- 只能一個一個 resume，沒有 queue 概念
- 核准/拒絕的動作是同步 CLI，沒有 async 通知

### 2. Checkpoint B — 交付前最終確認

**使用情境**：資料清理/處理完成後、打包交付給客戶前，需要人工確認輸出品質。

**現在的體驗**：
- 類似 Checkpoint A，產生 checkpoint JSON 等待核准
- 核准後續跑 delivery/export 步驟

**限制**：
- 沒有「批次核准多個 case」的能力
- 沒有交付預覽（preview bundle content）

### 3. 通知事件流（Notification Gateway Stub）

**使用情境**：當 workflow 到達特定節點時，讓 downstream 系統知道發生了什麼。

**現在的體驗**：
- 系統會寫入 local file / JSONL audit log
- 支援的事件：checkpoint 等待人工、checkpoint 核准、run 完成、delivery bundle 就緒
- 預設關閉，用 `--enable-notifications` 開啟

**限制**：
- 僅限本機檔案，沒有 webhook / email / Slack
- 沒有重試機制、沒有 delivery guarantee
- 沒有 dashboard 可以看所有等待人工的項目

### 4. Resume Loop — 續跑機制

**使用情境**：核准後，實驗線可以從中斷點續跑，不用從頭重來。

**現在的體驗**：
- Checkpoint A 核准後 → 續跑 cleaning/gate 步驟
- Checkpoint B 核准後 → 續跑 delivery/export 步驟
- 會檢查 case_ref/task_type 匹配，防止誤操作

**限制**：
- resume 指令是顯式的 `--resume-checkpoint <path>`，沒有「自動找最新核准的」
- 沒有 resume history / 版本控制

---

## 二、User Pain We Still Haven't Solved（還沒解的痛點）

### 1. PM / 客戶現在還是看 raw outbox

- 沒有一個統一的「待辦事項 dashboard」讓 PM 看到：
  - 現在有多少 case 卡在 Checkpoint A / B 等待人工？
  - 哪些已經核准但還沒 resume？
  - 哪些 resume 了但 delivery 還沒完成？

- 現在必須手動 `ls outbox/` 看 JSON 檔案，或用 `grep` 搜尋

### 2. 沒有正式的 webhook 可靠性

- 現在的通知是「best-effort」寫 local file：
  - 如果 disk full，通知就丟了
  - 沒有 retry、沒有 DLQ（dead letter queue）
  - downstream 系統無法「訂閱」事件流

- 客戶如果需要「當某個 case 完成時自動觸發下游流程」，現在沒有可靠的解法

### 3. Human approval UI 只有 CLI

- 現在的操作者必須：
  1. 看到通知（或發現卡住）
  2. SSH 進機器或本機開 terminal
  3. 跑 `run_hitl_checkpoint_cli --apply-decision ...`
  4. 再跑 `run_agent_standard_case_experiment --resume-checkpoint ...`

- 沒有 web UI / console 可以：
  - 一鍵核准（或一鍵拒絕）
  - 看 checkpoint 的 context（客戶需求原文、解析結果）
  - 看 bundle 預覽再決定是否交付

### 4. 沒有 multi-case queue / batch 操作

- 如果今天有 50 個 case 都卡在 Checkpoint A，操作者要執行 50 次 CLI 指令
- 沒有「選取多個 case → batch approve」的能力
- 沒有 case priority / 排程概念

### 5. 通知管道單一

- 現在只有 local file，沒有：
  - Email 通知「你有 3 個 case 等待審批」
  - Slack DM 或 channel 通知
  - Webhook 給客戶的下游系統

### 6. 沒有審批紀錄 / audit trail UI

- 雖然有 JSONL audit log，但：
  - 沒有搜尋介面
  - 沒有「誰在什麼時候核准了什麼」的視覺化
  - 沒有匯出報表功能

---

## 三、Concrete "Next Questions" for PM（需要 PM 決定的方向）

### Q1: Human Approval UI 要長什麼樣子？

**選項 A: 最小路線 — 改善 CLI 體驗**
- 加一個 `--resume-latest-approved` flag，自動找最新核准的 checkpoint
- 加一個 `list_pending_checkpoints` 命令，顯示所有等待人工的項目
- 保持 CLI only，不開發 web UI

**選項 B: 中間路線 — Local Web Console**
- 開發一個輕量的 local web UI（類似現有 Local UI 的延伸）
- 可以瀏覽等待審批的 checkpoint、看 context、點按鈕核准
- 一鍵 resume（整合 approve + resume 成一步）

**選項 C: 完整路線 — Multi-tenant Dashboard**
- 開發支援多使用者的 web dashboard
- 支援 batch approve、priority queue、audit trail 視覺化
- 需要 authentication / authorization

**建議優先回答**：這影響 W7 的 scope 大小，以及是否需要引入前端資源。

---

### Q2: 要不要支援多 checkpoint queue？

**選項 A: 單一序列（現在的設計）**
- 一個 case 只有一個 active checkpoint（A 或 B）
- 操作者一次處理一個，resume 後才能進入下一個
- 實作簡單，但無法處理大量並發

**選項 B: 多 case queue（batch processing）**
- 支援多個 case 同時卡在 checkpoint，操作者可以 batch 核准
- 系統自動依序 resume（或平行 resume，取決於 resource）
- 需要 queue 管理、狀態追蹤、可能的 priority 機制

**選項 C: 分離式 workflow engine**
- checkpoint 核准後，把 resume 任務丟進 background queue（如 Celery / RQ）
- 操作者只管核准，系統自動處理後續
- 最大彈性，但架構複雜度大增

**建議優先回答**：這影響 W7 是否需要引入 queue / scheduler 元件。

---

### Q3: Notify 的 SLA / 重試 / 保證程度？

**選項 A: 維持 Best-effort（現在的設計）**
- 通知發送是「盡力而為」，失敗不影響主流程
- 適合 internal sandbox，不適合 production client-facing

**選項 B: At-least-once delivery（基本保證）**
- 加入 retry 機制（指數退避、最多 3 次）
- 失敗時進入 DLQ，可操作者手動重發
- 需要 persistent queue（如 Redis / SQS）

**選項 C: Exactly-once + audit guarantee**
- 嚴格的冪等性保證（idempotency key + deduplication）
- 完整的 audit trail：誰發了什麼、什麼時候、成功/失敗
- SLA 承諾（如 99.9% delivery within 30s）

**子問題**：
- 需要哪些通知通道？（Webhook / Email / Slack / Telegram）
- 優先順序？（Webhook > Email > Slack？）

**建議優先回答**：這影響 W7 是否需要引入 external queue、retry logic、以及合約承諾。

---

### Q4（Bonus）: Delivery / Summary 體驗的完整程度？

**背景**：W7-T3 有 controlled delivery notify experiment，產生 client summary JSON，但還沒決定怎麼用。

**選項 A: 僅 log 記錄**
- 產生 summary JSON 但不主動通知客戶
- 操作者手動查閱後決定是否用其他方式通知

**選項 B: 半自動 — 人工觸發發送**
- summary 準備好後，通知操作者「可以發送了」
- 操作者一鍵觸發 email / webhook

**選項 C: 全自動 — 條件觸發**
- 符合條件時（如 auto_approve + 無 warning）自動發送
- 需要定義「什麼情況可以自動發、什麼情況必須人工審批」

---

## 四、Non-Goals（W7 這輪不打算碰的）

為了讓討論聚焦，以下項目**明確列為 W7 Non-Goals**：

### 1. Multi-tenant / 多組織隔離
- W7 假設單一組織、單一 workspace
- 不處理「客戶 A 不能看到客戶 B 的 checkpoint」

### 2. 全通道通知平台（通用 notification service）
- 不支援任意第三方 webhook 註冊
- 不支援「客戶自己設定 callback URL」
- 僅支援固定的、internal 的下游系統

### 3. 手機 App / Mobile Push
- 僅限 desktop web / CLI
- 不包括 mobile-optimized UI

### 4. 即時協作（多人同時審批）
- 不處理「兩個人同時核准同一個 checkpoint」的 race condition
- 假設單一操作者模式（或 external 解決協調）

### 5. 自動 decision / AI 輔助審批
- 不引入 ML model 預測「這個 checkpoint 應該被核准」
- 保持人工決策為唯一來源

### 6. 生產環境的 production delivery
- W7 仍屬 internal sandbox / 實驗線
- 不直接影響 production case delivery 流程

---

## 五、Reference（給 PM 的技術背景補充）

| 概念 | 簡單解釋 | 現在狀態 |
|------|----------|----------|
| **Checkpoint A** | Intake 確認：需求理解正確嗎？ | ✅ 有 CLI 核准 + resume |
| **Checkpoint B** | Delivery 確認：輸出品質 OK 嗎？ | ✅ 有 CLI 核准 + resume |
| **Notification Gateway** | 事件通知機制 | ✅ Local file stub |
| **Resume Loop** | 核准後自動續跑 | ✅ 單 case 序列 |
| **Controlled Notify** | 產生 client summary | ✅ Sandbox experiment |
| **Webhook** | HTTP callback 通知下游 | ❌ Not yet |
| **Batch Approval** | 一次核准多個 case | ❌ Not yet |
| **Audit Dashboard** | 視覺化審批紀錄 | ❌ Not yet |

---

## 六、建議的 PM 決策順序

1. **先回答 Q1（UI 形式）**：這決定團隊需要多少前端資源
2. **再回答 Q2（Queue 需求）**：這決定後端架構複雜度
3. **最後回答 Q3（Notify SLA）**：這決定是否需要 external infrastructure

---

## 附錄：W6 相關票索引（給工程師參考）

| Ticket | 內容 | 狀態 |
|--------|------|------|
| W6-T5 | Checkpoint A 整合 | ✅ done |
| W6-T6 | Checkpoint B 整合 | ✅ done |
| W6-T10 | Notification Gateway Stub | ✅ P2+P3 done |
| W6-T11 | Resume Orchestrator Loop | ✅ P3 done |
| W7-T3 | Controlled Delivery Notify | ✅ done |

---

*End of Brief — 等待 PM 回饋與決策*
