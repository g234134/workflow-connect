# B_MINIMAL_GAP_LIST.md

> 用途：里程碑 B 的「還差哪些才能判定 DONE」的最小缺口清單。
> 基於：A_closure pack、B-1 報告、ENV_FREEZE_AND_REPLAY_GATES.md、CROSS_FILE_DEBT_HANDLING_SOP.md
> 更新：2026-05-30（本日新增 §2 — 環境凍結與重播 gate 缺口）

---

## §1 跨檔案 debt 處理（CROSS_FILE_DEBT_HANDLING_SOP.md）

| 缺口項 | 描述 | 處理狀態 | 剩餘工作 |
|--------|------|:--------:|----------|
| SOP 定義 | 跨檔案 debt 的拆票、lane 對齊、freeze 規則已在 SOP 中定義 | ✅ Done | — |
| 實例驗證 | D-005（`_total_context_tokens` 重複）已在 §6 做了完整演練 | ✅ Done（workspace 內）| ❌ 尚未在 eval_exporter 的 discovery/scan 中真實驗證 |
| 實例真實執行 | 依 SOP 跑完三張票（B-TKT-001/002/003）的 runtime + review + doc-sync | ❌ TODO | 需要進入 eval_exporter 的 fix_round 階段，且需人工確認 merge |
| DEBT_LOG 關聯欄位 | DEBT_LOG.md 需增加「關聯票據」欄位（在 eval_gate 和 eval_exporter 各一份） | ❌ TODO | 需修改 eval_gate DEBT_LOG.md 中 D-005 的「狀態」為 planned，加關聯欄位；eval_exporter DEBT_LOG.md 也需同步（目前該檔為空）|

**截止截至此缺口**：❌ 尚未完全閉環（剩下真實執行 + DEBT_LOG 同步）。

---

## §2 環境凍結與重播 gate（ENV_FREEZE_AND_REPLAY_GATES.md）

> 補充於 2026-05-30（基於 B-2/B-3 任務）

### 2.1 已在 workspace 內定義的項目

| 項目 | 文件位置 | 狀態 |
|------|----------|:----:|
| 多線調度前的最小環境條件（Python/venv/測試/OS/密鑰）| ENV_FREEZE_AND_REPLAY_GATES.md §1 | ✅ Done |
| CI/CD 識別 decision tree（4 種平台 + unknown） | ENV_FREEZE_AND_REPLAY_GATES.md §2 | ✅ Done |
| Workspace 重播記錄標準（run ID / config snapshot / 依賴清單 / outcome block） | ENV_FREEZE_AND_REPLAY_GATES.md §3 | ✅ Done |
| 人工 vs 自動化檢查點分配表 | ENV_FREEZE_AND_REPLAY_GATES.md §4 | ✅ Done |
| 開新線前必過的 7 個閘門（G-ENV-1~4, G-REPLAY-1~3） | ENV_FREEZE_AND_REPLAY_GATES.md §5 | ✅ Done |
| 與 A_closure replay checklist 的對應表 | ENV_FREEZE_AND_REPLAY_GATES.md 附錄 A | ✅ Done |

**結論**：環境凍結與重播 gate 的**定義**層面已在 workspace 內完成，屬於「可以在 workspace 內先完成的缺口」。

### 2.2 仍為缺口的項目（❌ 尚未閉環）

| 缺口 | 原因 | 依賴 |
|------|------|------|
| G-ENV-1 / G-ENV-2（venv + pytest 實際填入）| 取決於第二模組（eval_exporter）的 discovery 階段是否已執行。目前 eval_exporter 處於 bootstrap 階段，PIPELINE.md 全部 unknown | B-1 discovery 完成 |
| G-ENV-3（CI/CD 分類）| 影響範圍超出 workspace：需人工協助確認大唐三省六部 repo 的 CI 平台，或由 Hermes 在 discovery 時執行 §2.1 decision tree | discovery CI scan |
| 閘門檢查自動化 | 目前 7 個閘門均為手動檢核（`echo YES/NO`），無自動化腳本 | milestone C/D scope |
| run note config snapshot 自動生成 | 目前依賴人工填寫 outcome block 與 config snapshot | milestone C/D scope |
| `B-TKT` 票據系統 | 本 SOP 假設有 `B-TKT-XXX` 編號系統，但目前僅作為 workspace 內的標記草案，無正式 ticketing | control plane 整合（W4-X）|

### 2.3 標記

```
這一節屬於「可以在 workspace 內先完成的缺口」：
- 定義層面 ✅ 已完成（ENV_FREEZE_AND_REPLAY_GATES.md 與 CROSS_FILE_DEBT_HANDLING_SOP.md 均已寫入）
- 執行層面 ❌ 尚未驗證（未對 eval_exporter 執行 discovery，無法填入 PIPELINE.md 實際值）
- 自動化層面 ❌ 未啟動（閘門檢查與 config snapshot 自動化屬於後續 milestone）
```

---

## §3 總缺口摘要（截至 2026-05-30）

| 缺口 | 類型 | 優先級 | 關聯文件 |
|------|:----:|:------:|----------|
| eval_exporter discovery 未執行 → PIPELINE.md 為空 | **execution** | P0 | B-1 report |
| DEBT_LOG 跨線同步未做（D-005 關聯欄位） | **documentation** | P1 | CROSS_FILE_DEBT_HANDLING_SOP.md §4 |
| D-005 三張 ticket 未真實執行 | **execution** | P1 | CROSS_FILE_DEBT_HANDLING_SOP.md §6 |
| CI/CD 平台 ID 未知（repo 無 `.github/` 佈局）| **discovery** | P1 | ENV_FREEZE_AND_REPLAY_GATES.md §2 |
| G-ENV 閘門未自動化 | **automation** | P2 | ENV_FREEZE_AND_REPLAY_GATES.md §5 |
| B-TKT 票據系統未整合到 control plane | **integration** | P2 | CROSS_FILE_DEBT_HANDLING_SOP.md §2 |
| Python 版本確認（3.14 vs 3.10 pycache 衝突） | **discovery** | P2 | ENV_FREEZE_AND_REPLAY_GATES.md §1 |

### 級別說明

| 級別 | 定義 |
|:----:|------|
| P0 | 無此項 B 無法判定 DONE |
| P1 | 有此項但不足以阻擋 B 判定（有 workaround 或不影響判定）|
| P2 | Nice-to-have，B 可先判定 DONE 後補 |
