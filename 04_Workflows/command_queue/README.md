# Command Queue — 總指揮官任務編排

> **用途**：尚書省說「安排任務」時，副官**先讀本目錄**，再決定「接著做」或「接著排」。
> **不是** Phase% SSOT · **不是** 子票 FRAME 全文 · **不取代** `tickets/*_state.md`。

---

## 權威位階（由低到高引用）

| 層級 | 路徑 | 角色 |
|------|------|------|
| **本隊列（操作索引）** | `04_Workflows/command_queue/QUEUE.yaml` | 總指揮官 · 當次取捨 |
| Wave 規劃正文 | `04_Workflows/tickets/W-MASTER-wave-plan_state.md` | Wave 1–5 已規劃票 FRAME |
| 全 Phase 任務盤 | `04_Workflows/tickets/W-MASTER-full-phase-plan_state.md` | G1–G10 任務群 |
| 戰術線 P7/P8.5/P9 | `04_Workflows/tickets/W-ORCH-wave-next-control-plane-v1_state.md` | 並行 lane |
| Phase% | `docs/WAVE_PROGRESS_DASHBOARD.md` | 完成度數字 |
| 戰報 | `04_Workflows/00_Agent_Work_Progress.md`（末尾） | 已做證據 |
| **跨端缺陷 SSOT** | `04_Workflows/cross_agent_fix_ledger.yaml` | Hermes↔Cursor 已修／待修（非聊天） |

**規則**：QUEUE 只存 **索引 + 狀態 + 下一步**；FRAME 細節仍在 W-MASTER 或子票 `*_state.md`。  
**跨端修復**：開工讀／收工寫 Fix Ledger；`fixed`+`verify_cmd` 通過不得重開；相交檔先 `claim_owner`。

---

## 口令對照

| 尚書省口令 | 副官模式 | 必跑命令 | 產出 |
|------------|----------|----------|------|
| **安排任務** / **接著安排** | `arrange` | `python 04_Workflows/_command_queue.py --mode arrange --pretty` | 更新 QUEUE · 列 ready/blocked/backlog · 建議下一批票 |
| **接著做** / **執行下一張** | `execute` | `python 04_Workflows/_command_queue.py --mode execute --pretty` | 從 `priority_next` 取 1 票 · 開 FRAME 或派 Implementer |
| **隊列狀態** | `status` | `python 04_Workflows/_command_queue.py --pretty` | 統計 + 全表摘要 |

Cursor slash：`/arrange-tasks`（見 `.cursor/commands/arrange-tasks.md`）

---

## 總指揮官 SOP（每次「安排任務」）

### 1. 接戰（Tier 1）

```powershell
python 04_Workflows/_boot_context.py --text "總指揮官安排任務" --pretty
python 04_Workflows/_command_queue.py --pretty
```

### 2. 讀取（依 `--mode`）

**arrange 模式** — 排後續、不施工：

1. `QUEUE.yaml` → `stats` · `priority_next` · `status: PLANNED|NOT_PLANNED`
2. `W-MASTER-wave-plan_state.md` → 對應 Wave 摘要表 + FRAME 段落
3. `W-MASTER-full-phase-plan_state.md` → 若 Wave 票不足，從 G1–G10 補規劃
4. Progress **末尾** → 已關票 / 新阻塞

**execute 模式** — 接著做：

1. `QUEUE.yaml` → `priority_next[0]` 或 `status: READY|DOING`
2. 子票 `*_state.md` → FRAME / STATE / 上一輪 REPORT
3. 依 `multi_chat_roles.mdc` 派 Implementer / Reviewer / Scribe

### 3. 寫回（只改本目錄 + 必要子票 STATE）

| 動作 | 寫入 |
|------|------|
| 新排一批票 | `QUEUE.yaml` 追加/更新列 · `SESSION.md` 決策紀錄 |
| 開新子票 | 複製 `tickets/_templates/ticket_state.template.md` → `tickets/<id>_state.md` |
| 改票狀態 | 子票 `STATE` + `QUEUE.yaml` 同 id 的 `status` |
| 里程碑/Phase% | **不寫**（Governance 票 · Progress 末尾） |

### 4. 回報尚書省（固定五段）

1. **全局**：17 Phase 平均 %（Dashboard SSOT）
2. **隊列統計**：ready / doing / blocked / planned / done
3. **建議下一動**：arrange 或 execute 二選一 + 票 ID
4. **阻塞**：human/infra/security 前置
5. **若已派工**：Implementer 起手口令 + state 路徑

---

## 狀態字彙

| status | 含義 | 指揮官動作 |
|--------|------|------------|
| `NOT_PLANNED` | 缺口已知、尚未寫入 W-MASTER | arrange：補 FRAME 到 W-MASTER 或 G 組 |
| `PLANNED` | W-MASTER 有 FRAME、無 `_state.md` | execute：開 `_state.md` 派 Implementer |
| `READY` | `_state.md` 就緒、無 blocking | execute：派 Implementer |
| `DOING` | Implementer 施工中或待 Review | execute：派 Reviewer 或續 B |
| `BLOCKED` | human/infra/security/merge 前置 | arrange：列解阻票；不派功能施工 |
| `DONE` | 子票 accepted/done | **歸檔**至 `QUEUE.archive.yaml`；不重開 |
| `DONE_WITH_GAPS` | AI 段結束、等人 ops（見 awaiting_ops） | 歸檔；`priority_next` 用 `mode: human` |
| `DEFERRED` | 明確延後 | 不排入 `priority_next` |

**活躍 vs 歸檔**：`QUEUE.yaml` 只留非 DONE 列 + `priority_next`／`human_ops_sequence`；關票後把該列**移入** `QUEUE.archive.yaml`。CLI `_command_queue.py --status DONE` 會合併 archive。

---

## 與既有資產的關係

| 既有 | 本隊列 |
|------|--------|
| `workflow_upgrade/90_run_queue.md` | H 線 / Sprint 專用；**不合并** |
| `W-MASTER-wave-plan_state.md` | 規劃 SSOT；QUEUE **引用** ticket id |
| `artifacts/control_plane/dispatch_plan.*` | 單次 dispatch 產物；非持久隊列 |

---

## 檔案

| 檔 | 說明 |
|----|------|
| `QUEUE.yaml` | 活躍隊列（READY／DOING／PLANNED／BLOCKED）· **總指揮官主寫** |
| `QUEUE.archive.yaml` | DONE／DONE_WITH_GAPS 歸檔 |
| `SESSION.md` | 編排決策 log（**UTF-8** append） |
| `README.md` | 本 SOP |
| `../_command_queue.py` | CLI 讀取/摘要（合併 archive） |

---

*Command Queue v1 · 2026-07-08 · HQ-Coordinator*
