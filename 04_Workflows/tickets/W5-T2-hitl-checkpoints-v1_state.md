# W5-T2 · hitl-checkpoints-v1 · State

> **Ticket**: W5-T2-DESIGN — HITL Checkpoints v1 Design  
> **Role**: Architect  
> **Status**: Design Complete — Ready for Review  
> **Date**: 2026-06-10

---

## 1. Task Summary

為「Agent 主導流程、只保留極少人工確認」設計 HITL checkpoints v1：

- **Checkpoint A**: Intake Confirmation（接案確認）
- **Checkpoint B**: Delivery Confirmation（交付確認）

本票僅設計，不寫程式。

---

## 2. Acceptance Criteria

| AC | 內容 | 狀態 | 證據 |
|----|------|------|------|
| AC-1 | Checkpoint A 完整設計 | ✅ | `docs/hitl-checkpoints-v1.md` §3 |
| AC-2 | Checkpoint B 完整設計 | ✅ | `docs/hitl-checkpoints-v1.md` §4 |
| AC-3 | State / Outbox / Trace 記錄設計 | ✅ | `docs/hitl-checkpoints-v1.md` §5 |
| AC-4 | Resume 策略設計 | ✅ | `docs/hitl-checkpoints-v1.md` §3.5, §4.5 |
| AC-5 | 為何僅 1–2 checkpoints 說明 | ✅ | `docs/hitl-checkpoints-v1.md` §6 |
| AC-6 | v1 NonScope 明確列出 | ✅ | `docs/hitl-checkpoints-v1.md` §7 |
| AC-7 | 與現有 Wave 1–5 系統關係圖 | ✅ | `docs/hitl-checkpoints-v1.md` §9 |
| AC-8 | 設計文件已寫入 `docs/` | ✅ | `docs/hitl-checkpoints-v1.md` 存在 |

---

## 3. Checkpoint 摘要

### Checkpoint A: Intake Confirmation

| 項目 | 內容 |
|------|------|
| **觸發時機** | `evaluate_intake_decision()` 返回 `needs_review`，或 `risk_level=medium`，或未知 fixture |
| **Agent 輸出** | intake_decision, suggested_route, case_summary, gate_preview |
| **Human 選項** | `approve` / `reject` / `revise_plan` |
| **預設行為** | timeout → `approve`（auto-approve） |
| **Resume 點** | `selector`（approved）/ `gate`（revised）/ 終止（rejected） |

### Checkpoint B: Delivery Confirmation

| 項目 | 內容 |
|------|------|
| **觸發時機** | Cleaning + Bundle 完成，且 `output_guard.status` 為 `ok`/`warning`，或有 force/warning 條件 |
| **Agent 輸出** | execution_summary, cleaning_results, artifacts, output_guard, delivery_draft |
| **Human 選項** | `approve_delivery` / `request_changes` / `hold` |
| **預設行為** | timeout → `hold` |
| **Resume 點** | `delivery`（approved）/ `cleaning`/`bundle`（changes）/ `on_hold`（hold） |

---

## 4. Resume 策略摘要

| Checkpoint | Resume From | 行為 |
|------------|-------------|------|
| A | `selector` | 使用 checkpoint 中的 `planned_tools`，跳過 intake_decision_rules 重算 |
| A | `gate` | 從 eligibility validation 重新開始（人為 revise 選擇不同 path） |
| B | `delivery` | 僅更新 status / notify，不重新執行任何 tool |
| B | `cleaning` | 重新執行 cleaning step，保留 gate/bundle 結果 |
| B | `bundle` | 重新執行 bundle step，保留 cleaning 結果 |

**Resume Context 結構**:
```json
{
  "checkpoint_id": "A|B",
  "case_ref": "...",
  "original_decision": { ... },
  "human_decision": { "action": "...", "by": "...", "at": "..." },
  "resume_from": "selector|gate|cleaning|bundle|delivery",
  "artifacts": { ... }
}
```

---

## 5. State / NonScope 摘要

### State 儲存設計

| 類型 | 路徑 | Schema |
|------|------|--------|
| Checkpoint state | `outbox/<case_ref>/checkpoint_<id>_<timestamp>.json` | `hitl_checkpoint_v1` |
| Checkpoint events | `outbox/checkpoint_events.jsonl` | Append-only |
| Case status | `cases/index.json` | 欄位 `hitl_status`, `checkpoint_pending` |

### v1 NonScope（明確不做）

| 類別 | 項目 | 原因 |
|------|------|------|
| 通知 | Slack / Email / Telegram approval | 需 async/webhook 基礎建設，W5-T3+ 再議 |
| Workflow Engine | Durable workflow / 24hr+ checkpoint / 分散式儲存 | v1 使用檔案-based state + CLI resume |
| 彈性 | 任意步驟暫停 / Dynamic checkpoint / Pause API | 僅固定 2 個 checkpoints，簡化設計 |
| 簽核 | 多人簽核 / 角色區分 / 簽核流配置 | v1 僅單一 operator decision |
| 其他 | 修改既有 scripts/Local UI、Langfuse/PG 寫入、非 Tabular 家族、checkpoint 統計 | 保持設計票範圍最小 |

---

## 6. Work Report

### 變更檔案

| 檔案 | 類型 | 說明 |
|------|------|------|
| `docs/hitl-checkpoints-v1.md` | 新增 | 主要設計文件 |
| `04_Workflows/tickets/W5-T2-hitl-checkpoints-v1_state.md` | 新增 | 本狀態票 |

### Skeleton（無程式碼）

- 本票僅設計，無 skeleton code
- 預留 future implementation 的 CLI 介面設計於 §8

### Placeholder

- Resume CLI 設計（`scripts/resume_from_checkpoint.py`）僅為概念預覽，非實作

### 阻塞

- 無

### 下一步

1. Reviewer review 本設計文件
2. 若設計通過，開實作票（W5-T2-IMPL 或其他編號）
3. 實作票內容：
   - `routing/hitl_checkpoint.py` — Checkpoint state manager
   - `scripts/resume_from_checkpoint.py` — Resume CLI
   - `tools/hitl_checkpoint_hooks.py` — Integration with existing Wave 1–5 tools
   - Unit tests

---

## 7. 文件工單自檢：見 APP-DOC

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| 可移植正文零本機絕對路徑 | ✅ | 全用 `outbox/<case_ref>/` 相對路徑 |
| 地圖涵蓋任務卡約定範圍 | ✅ | 涵蓋 Wave 1–5 既有系統 |
| Cabin 僅角色／用途 | ✅ | 無 venv 路徑 |
| 禁區僅類型 | ✅ | 無 DarkOps/runtime/.env 觸及 |
| Pipeline 制度在可移植層 | ✅ | Outbox / State 設計通用 |
| 對齊 W0、未與 Conditions/Progress/AGENTS 衝突 | ✅ | 參照既有 spec，無衝突 |
| 未在 Phase 1 偷寫 `.cursor/rules`、未自標定稿版號 | ✅ | 僅 `docs/` 設計文件 |

---

## 8. 四流派檢核

| 流派 | 滿足 | 說明 |
|------|------|------|
| Context-Driven | ✅ | 已讀 Wave 1–5 全文件 |
| Source-Driven | ✅ | 已列並讀取所有引用文件 |
| Incremental | ✅ | 設計票範圍明確，無擴張 |
| Debugging | ✅ | 設計含 trace / resume / state 除錯機制 |

---

*W5-T2-hitl-checkpoints-v1_state.md · 2026-06-10 · Design Complete*
