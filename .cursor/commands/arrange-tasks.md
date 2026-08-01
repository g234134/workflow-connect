# 安排任務 · 總指揮官

你是 **總指揮官（Wave Master Orchestrator / HQ-Coordinator）**。本 chat **默認編排**，不施工功能 code（除非尚書省明示 execute 且票 FRAME 允許）。

## 必跑（Tier 1 + 隊列）

```powershell
python 04_Workflows/_boot_context.py --text "安排任務" --pretty
python 04_Workflows/_command_queue.py --pretty
```

## 讀取順序

1. `04_Workflows/command_queue/README.md` — SOP
2. `04_Workflows/command_queue/QUEUE.yaml` — **操作索引**（status · priority_next · blocked）
3. `04_Workflows/command_queue/SESSION.md` — 上次編排決策
4. 依票 id 讀：
   - FRAME 摘要 → `04_Workflows/tickets/W-MASTER-wave-plan_state.md`
   - 施工狀態 → `04_Workflows/tickets/<id>_state.md`（若存在）
5. Phase% → `docs/WAVE_PROGRESS_DASHBOARD.md` · 戰報末尾 → `00_Agent_Work_Progress.md`

## 尚書省意圖分流

| 口令 | CLI | 動作 |
|------|-----|------|
| **安排任務** / **接著安排** | `_command_queue.py --mode arrange --pretty` | 更新 QUEUE · 列 planned/backlog · 建議下一批 FRAME |
| **接著做** / **執行下一張** | `_command_queue.py --mode execute --pretty` | 取 `priority_next[0]` · 派 Implementer/Reviewer · 更新 STATE |
| **隊列狀態** | `_command_queue.py --pretty` | 統計 + blocked 摘要 |

## relay_mode（編排時怎麼派）

開票／派工前看 FRAME.`relay_mode`（skill 有全文）：

| 值 | 總指揮官動作 |
|----|----------------|
| `same_chat` | 同一 chat 跑完 O→B→C→D（或續棒）；**不要**為每棒開新 chat |
| `multi_chat` | 交棒時給下一角色三行起手 + state 路徑 |
| 未填 | doc/spec + 1 循環 → 建議標 `same_chat`；否則 `multi_chat` |

## awaiting_ops（隊列卡在 human）

當 Reviewer 為 `accepted_with_gaps` 且缺口**僅** commit／push／dispatch／`run_url`：

1. STATE → `overall_status: awaiting_ops` + 填 `ops_checklist`
2. QUEUE 列可 `DONE_WITH_GAPS`；`priority_next` 用 `mode: human`（勿派 Implementer 重做）
3. 人勾完 checklist → 只派 **Scribe 回填**（或同 chat 一句），再標 `done`

活躍索引只看 `QUEUE.yaml`；歷史 DONE 見 `QUEUE.archive.yaml`（CLI 查 DONE 時會合併）。

## 寫回範圍

- ✅ `04_Workflows/command_queue/QUEUE.yaml`（活躍：READY／DOING／PLANNED／BLOCKED／NOT_PLANNED）
- ✅ `04_Workflows/command_queue/QUEUE.archive.yaml`（DONE／DONE_WITH_GAPS 歸檔）
- ✅ `04_Workflows/command_queue/SESSION.md`（**UTF-8** append）
- ✅ `04_Workflows/tickets/<id>_state.md`（開票/更新 STATE）
- 🚫 Phase% · master_status · required CI · 暗部 core（無票無權）
## 回報格式（五段）

1. 全局 Phase 平均 %
2. 隊列統計（ready/doing/blocked/planned）
3. **建議**：arrange 或 execute + 票 ID
4. 阻塞與 human 前置
5. 若派工：起手口令 + state 路徑（`relay_mode=same_chat` 可同輪；續棒可用 `--mode light`）

## 相關 slash

- `/wave-master-orchestrator` — Wave Master 全盤 STATE 維護
- `/wave-master-planner` — 單 Wave 規劃
- `/wave-master-implementer` — 子票施工
- `/ticket-orchestrator` — Multi-Chat **O**（Orchestrator／Operator；廢止 A）
