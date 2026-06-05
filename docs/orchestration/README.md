# 多 Agent 總調度 — 使用說明

> **落點**：`docs/orchestration/`  
> **版本**：v0.1（文件驅動 MVP）  
> **你只需記住**：新階段開一個 **Cursor-Orchestrator** chat，貼 `ORCHESTRATOR_PROMPT.md` 全文，再說這階段要做什麼。

---

## 1. 這套系統是什麼

這是一套**純 markdown** 的多 Agent 協作骨架，讓你：

1. **只講階段目標**（不碰細部執行）
2. **Cursor-Orchestrator** 讀規則表、任務板、交接摘要後拆任務、派工、控 checkpoint
3. **Hermes** 做階段規劃與 BRIEF（不寫程式）
4. **Cursor-Worker** 按 spec 改檔（不擴 scope）
5. **小龍蝦** 跑白名單內腳本／批量操作

**不是**：暗部 Python orchestration、LangGraph runtime、資料庫後端。那些在 `core/`、`agents/` 另域，本目錄不碰。

- **T2 試跑（2026-06-02）**：已驗證 Orchestrator 拆段 → Worker 新 chat → SEGMENT 回報流程。

### T2 試跑成果與後續用途

- **證明了什麼**：在 Orchestrator 與 Worker 分屬不同 chat 的前提下，Orchestrator 可拆段派工、Worker 依 BRIEF 改檔並產出 SEGMENT，整條回報鏈路可落地。
- **未來如何複用**：引入新角色、新文件或新工作流前，可先設計改動極小的試跑任務（類似 T2／T3），驗證派工與 SEGMENT 流程正常，再擴大 scope。
- **範例參考**：[`segments/T2a__seg1__2026-06-02.md`](./segments/T2a__seg1__2026-06-02.md)

---

## 2. 文件地圖（先看哪一份）

| 文件 | 誰改 | 什麼時候用 |
|------|------|------------|
| [`AGENT_RULES.md`](./AGENT_RULES.md) | 你（偶爾修規則） | 定義五角色職責、禁區、長任務拆段、高風險停點 |
| [`TASK_BOARD.md`](./TASK_BOARD.md) | **Cursor-Orchestrator** 為主 | **活任務板**；每階段開工／收工都對齊這裡 |
| [`TASK_BOARD_TEMPLATE.md`](./TASK_BOARD_TEMPLATE.md) | 參考用 | 新增任務時複製欄位格式 |
| [`HANDOFF_SUMMARY.md`](./HANDOFF_SUMMARY.md) | **Cursor-Orchestrator** | **最新階段交接**；新 Orchestrator chat 必讀 |
| [`HANDOFF_SUMMARY_TEMPLATE.md`](./HANDOFF_SUMMARY_TEMPLATE.md) | 參考用 | 階段結束時複製填寫 |
| [`SEGMENT_EXEC_SUMMARY_TEMPLATE.md`](./SEGMENT_EXEC_SUMMARY_TEMPLATE.md) | Worker／小龍蝦 | 長任務**每一段**結束的回報格式 |
| [`segments/`](./segments/) | Worker／小龍蝦 | 各段 SEGMENT 實例存放目錄 |
| [`ORCHESTRATOR_PROMPT.md`](./ORCHESTRATOR_PROMPT.md) | 你 | **貼進新 Orchestrator chat** 的系統提示詞 |

**與 HQ 既有制度的關係**（只引用、不重複）：

- 禁區紅線 → `AGENTS.md`、`HARNESS_CONSTITUTION.md` §7
- Cursor 派工細節 → `.cursor/agents/DISPATCH_GUIDE.md`
- 官方戰報 append → `04_Workflows/00_Agent_Work_Progress.md`（可選同步，不取代本目錄 HANDOFF）

---

## 3. 第一次上線 — 最短 5 步

### 步驟 1：改活任務板

打開 [`TASK_BOARD.md`](./TASK_BOARD.md)，把示例任務改成你**本階段真正要做的事**（至少一條主任務 + 負責角色 + 狀態）。

### 步驟 2：確認交接摘要

打開 [`HANDOFF_SUMMARY.md`](./HANDOFF_SUMMARY.md)。若是第一次用，保留「尚無上一階段」占位即可；若有上一階段，請 Orchestrator 先更新再開工。

### 步驟 3：開 Cursor-Orchestrator chat

1. 在 Cursor **新建一個 chat**（專用總調度，不要和 Worker 混用）
2. 複製 [`ORCHESTRATOR_PROMPT.md`](./ORCHESTRATOR_PROMPT.md) **全文**貼入第一則訊息
3. 接著用下面「開場白模板」說你的階段目標

### 步驟 4：等 Orchestrator 派工

Orchestrator 會：

- 讀 `AGENT_RULES` / `TASK_BOARD` / `HANDOFF_SUMMARY`
- 告訴你哪些可自動做、哪些要你拍板
- 派 Hermes 寫 BRIEF、派 Worker 改檔、派小龍蝦跑腳本
- **長任務**會拆成 T4a / T4b…，並要求 Worker **另開新 chat**

### 步驟 5：執行層回寫 + 階段收工

- **Cursor-Worker / 小龍蝦** 每段結束 → 依模板寫 SEGMENT，存到 `segments/`
- **Cursor-Orchestrator** 階段結束 → 更新 `HANDOFF_SUMMARY.md` 與 `TASK_BOARD.md` 狀態
- 你要拍板時，Orchestrator 會用標準格式問你，不會偷偷讓執行層做高風險事

---

## 4. 你以後每次開新階段 — 跟 Orchestrator 怎麼說

複製改寫即可：

```text
【階段目標】
（一句話，例如：完成 XXX 模組 v0.1，含測試與文件）

【約束】
- 不可改：（列禁區或檔案）
- 必須對齊：（列 spec / runbook）

【優先順序】
P0：…
P1：…

【請先】
讀 docs/orchestration/AGENT_RULES.md、TASK_BOARD.md、HANDOFF_SUMMARY.md，
重述理解、更新任務板、列出需我確認的項目，再派工。
```

---

## 5. Worker / 小龍蝦做完後 — 結果寫哪

| 產出類型 | 寫入位置 |
|----------|----------|
| 單段執行回報 | 複製 [`SEGMENT_EXEC_SUMMARY_TEMPLATE.md`](./SEGMENT_EXEC_SUMMARY_TEMPLATE.md) → 存成 `segments/{TASK_ID}__seg{N}__{日期}.md` |
| 任務板狀態 | Orchestrator 更新 [`TASK_BOARD.md`](./TASK_BOARD.md) |
| 階段總交接 | Orchestrator 更新 [`HANDOFF_SUMMARY.md`](./HANDOFF_SUMMARY.md) |
| Hermes BRIEF | 建議 `docs/orchestration/briefs/{TASK_ID}_brief.md`（本輪未建模板，可自訂） |

**SEGMENT 命名範例**：`segments/T4b__seg2__2026-06-02.md`

---

## 6. 長任務拆段 — 誰決定、誰寫摘要

| 決策 | 負責人 |
|------|--------|
| 要不要拆 T4 → T4a/b/c | **Cursor-Orchestrator**（依 AGENT_RULES §4） |
| Worker 要不要另開新 chat | **Cursor-Orchestrator** 下指令 |
| 每段 SEGMENT_SUMMARY | **該段執行者**（Cursor-Worker 或 小龍蝦）撰寫 |
| 階段總 HANDOFF | **Cursor-Orchestrator** 彙整 |

---

## 7. 三個 chat 怎麼分（必遵守）

```
你 ──拍板──► Cursor-Orchestrator chat（總調度）
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    Hermes      Cursor-Worker   小龍蝦
   （規劃 chat）  （施工 chat）  （執行 chat）
```

- **Orchestrator chat**：只規劃、派工、更新 TASK_BOARD / HANDOFF，**不自己大改程式**
- **Worker chat**：只施工，**不做高層規劃**，段末交 SEGMENT
- **不可**在同一 chat 又當 Orchestrator 又當 Worker

---

## 8. 高風險時你會被叫來拍板

完整清單見 [`AGENT_RULES.md`](./AGENT_RULES.md) §3。常見包括：刪資料、改 `.env`、force push、大規模改檔、擴 scope、碰暗部 runtime／core orchestration。

Orchestrator **不得**繞過規則讓 Worker／小龍蝦直接做上述動作。

---

## 9. 常見問題

**Q：TASK_BOARD 和 04_Workflows Progress 有什麼差？**  
A：TASK_BOARD 是**本工作流**的活任務板，給 Orchestrator 讀；Progress 是 HQ 官方戰報。重要里程碑可兩邊都留痕，但 HANDOFF 以本目錄為準。

**Q：可以只有 Orchestrator 一個 chat 嗎？**  
A：短任務可以 Orchestrator 只讀不改；**只要涉及改檔施工，必須另開 Worker chat**。

**Q：小龍蝦是什麼？**  
A：你環境裡負責**白名單內**腳本／清洗／批量的執行者（可能是另一個 Agent 或自動化工具），規則見 AGENT_RULES §2.5。

---

## 10. 快速檢查清單（開工前 30 秒）

- [ ] `TASK_BOARD.md` 已反映本階段任務
- [ ] `HANDOFF_SUMMARY.md` 已更新或確認無上一階段
- [ ] 新開 **Orchestrator** chat，已貼 `ORCHESTRATOR_PROMPT.md`
- [ ] 已用「階段目標」開場白
- [ ] Worker／小龍蝦 chat 尚未混在 Orchestrator 同一視窗

---

*維護：規則變更改 `AGENT_RULES.md`；格式變更改對應 `*_TEMPLATE.md`，並同步 README 本檔。*
