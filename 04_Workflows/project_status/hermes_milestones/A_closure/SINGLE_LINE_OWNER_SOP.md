# SINGLE_LINE_OWNER_SOP.md

> 供下一模組的 owner 使用。
> 本 SOP 基於 eval_gate 單線樣板的實際執行經驗提煉。
> 狀態：2026-05-30 | 版本：v1（源自 eval_gate 第一次閉環）

---

## 概述

從接到一個新模組的 owner 任務，到完成第一輪 hygiene patch 套用，共 7 步。

**總時間估計**：2–3 輪對話（視模組大小與 CLI 環境可用度）。
**核心原則**：先確認，再掃描，再建議，再審查，再套用。跳步必出錯。

---

## Step 0：確認所在目錄與模組邊界

**輸入**：模組名稱（如 `eval_gate`、`logging_adapter`）。

**動作**：
- [ ] 確認 workspace 根目錄：`/mnt/d/hermes-workspace/infra_owner/<module>/` 存在
- [ ] 若不存在，手動建立目錄結構（見 `NEXT_MODULE_BOOTSTRAP_TEMPLATE.md`）
- [ ] 確認真實 repo 的模組原始碼路徑（例如 `observability/eval_gate.py`）
- [ ] 確認是否有測試目錄、fixture、CLI 入口

**產出**：目錄結構就緒，模組邊界清楚。

**人工確認點**：模組名稱與 repo 路徑 → 請人類或尚書省確認，**不要猜測**。

---

## Step 1：Bootstrap（初始化管理包）

**動作**（參考 `NEXT_MODULE_BOOTSTRAP_TEMPLATE.md`）：
- [ ] 建立 `00_skill/SKILL_<MODULE>_HYGIENE_OWNER.md`（複製模板，填入模組名稱）
- [ ] 建立 `10_memory/ARCH.md`（全部填 unknown，後續覆蓋）
- [ ] 建立 `10_memory/STYLE.md`（填入通用慣例）
- [ ] 建立 `10_memory/DEBT_LOG.md`（空表 + 格式說明）
- [ ] 建立 `10_memory/PLAYBOOK.md`（占位模板）
- [ ] 建立 `20_runtime/PIPELINE.md`（全部標 unknown）
- [ ] 建立 `20_runtime/TASK_INTAKE_TEMPLATE.md`（複製模板）
- [ ] 建立 `20_runtime/REPORT_TEMPLATE.md`（複製模板）
- [ ] 建立 `90_runs/YYYY-MM-DD_bootstrap.md`（本次 bootstrap run note）

**產出**：管理包 9 份文件就緒。

---

## Step 2：Discovery（只讀探路）

**動作**：
- [ ] 掃描 repo 中該模組的所有 `.py` 檔案
- [ ] 識別：公開函數、常數、class、CLI 入口
- [ ] 識別：外部依賴（import 來自 site-packages 的模組）
- [ ] 識別：消費者（誰 import 這個模組）
- [ ] 識別：測試檔案與 fixture 路徑
- [ ] 識別：CI/CD 配置（檢查 `.github/`、Makefile、`pyproject.toml`）
- [ ] 更新 `ARCH.md`：填入實際目錄結構、公開介面、依賴、消費者
- [ ] 更新 `PIPELINE.md`：填入測試指令（推測，標 `needs-confirmation`）

**產出**：
- `90_runs/YYYY-MM-DD_discovery.md`（探路報告）
- `ARCH.md` 更新（從 bootstrap → 實際資訊）
- `PIPELINE.md` 更新（加入測試指令推測）

**人工確認點**：
- 如果測試環境未知，**所有測試指令必須標 `needs-confirmation`**
- 如果模組依賴第三方套件，列出給人類確認

---

## Step 3：Readonly Scan（衛生檢查）

**動作**：
- [ ] 對照 `SKILL_INFRA_HYGIENE_OWNER.md` §2 的 6 個維度執行掃描
- [ ] 合約檢查（docstring、type hint）
- [ ] 錯誤處理（bare except、例外類型）
- [ ] 型別與介面（Any 濫用、Protocol 同步）
- [ ] 日誌與可觀測性（關鍵決策點 logging）
- [ ] 測試穩定性（測試存在性、flaky 徵兆）
- [ ] 技術債（TODO/FIXME/HACK 對應 DEBT_LOG）
- [ ] 每個發現建立 DEBT_LOG 條目（D-XXX 格式）
- [ ] 評估嚴重度（P1 ~ P3）

**產出**：
- `90_runs/YYYY-MM-DD_scan_readonly.md`（掃描報告 + 問題總表）
- `DEBT_LOG.md` 填入首次發現的 debt 條目

**人工確認點**：無（掃描結果是客觀陳述，不需確認）。

---

## Step 4：Fix Round（產出建議修正版）

**範圍**：從 DEBT_LOG 中選出 ≤ 5 條零風險或低風險的 debt。

**零風險認定標準**：
| 條件 | 說明 |
|------|------|
| patch 類型 | 僅 docstring、logging、註解（純加法）|
| 語意變更 | 無（不改變 if 條件、回傳值、常數、簽名）|
| 檔案數 | 單檔（跨檔需另案處理）|
| 測試影響 | 不改變 test assertion |

**動作**：
- [ ] 複製原始碼檔案至 `20_runtime/<module>.suggested.v1.py`
- [ ] 在建議版中修正選定的 debt
- [ ] 執行靜態比對（簽名、keys、常數、if 條件、_RULES 順序）→ 全部 PASS
- [ ] 更新 `DEBT_LOG.md`：對應 debt_id 從 `open` → `fixed_suggested`

**產出**：
- `20_runtime/<module>.suggested.v1.py`（建議修正版）
- `90_runs/YYYY-MM-DD_fix_round1.md`
- `DEBT_LOG.md` 狀態更新

**人工確認點**：無（建議版不改 repo，只在 workspace）。

---

## Step 5：Review Gate（結構化審查）

**動作**：
- [ ] 審查建議版的 docstring 風格（是否與現有風格一致）
- [ ] 審查建議版的 logging 風格（等級分配是否合理）
- [ ] 記錄「喜歡的點」和「不喜歡的點」
- [ ] 裁決：接受 / 拒絕 / partial
- [ ] 如果接受 → 更新 STYLE.md（確認慣例）、更新 PLAYBOOK.md（補充經驗）

**產出**：
- `90_runs/YYYY-MM-DD_review_v1.md`（審查結論）
- `STYLE.md` 更新（如有慣例確認）
- `PLAYBOOK.md` 更新（如有補充條目）

**人工確認點**：
- STYLE.md 的慣例變更（從 proposed → confirmed）需人類知悉
- PLAYBOOK.md 新增條目需人類知悉
- 如果裁決是 reject / partial，需人類確認是否符合預期

---

## Step 6：Apply Plan + 套用

**動作**（參考 `APPLY_PLAYBOOK.md`）：
- [ ] 建立 `90_runs/YYYY-MM-DD_apply_plan_v1.md`（逐行套用順序、後驗證清單）
- [ ] 人工或 Cursor 依計畫套入 repo
- [ ] 執行靜態驗證（5 項：importable / 介面 / keys / logging / 依賴）
- [ ] 執行測試（如有環境可用）
- [ ] 填寫 `APPLY_CONFIRM_TEMPLATE.md` 回報

**產出**：
- `90_runs/YYYY-MM-DD_apply_plan_v1.md`
- `90_runs/YYYY-MM-DD_apply_result_v1.md`（或等同的確認紀錄）
- `DEBT_LOG.md`：`fixed_suggested` → `fixed_in_repo`（3 條左右）

**人工確認點**：
- **套入 repo 前**：人類必須審核 diff 並簽署 `approved`
- **套入後回報**：人類回報測試結果、障礙、git 狀態
- **下標 fixed_in_repo 前**：確認 4 個閘門（審查接受 + 套入 + 靜態驗證 PASS + 測試 PASS）

---

## Step 7：Debt Status Update + 關閉

**動作**：
- [ ] 確認 DEBT_LOG.md 統計摘要已更新
- [ ] 確認所有 debt 狀態流轉已記錄（含日期與原因）
- [ ] 確認 STYLE.md / PLAYBOOK.md / ARCH.md 的本輪變更已保存
- [ ] 寫一條簡短戰報（3–5 句），摘要本輪做了什麼、哪些 debt 已關、哪些仍 open

**產出**：DEBT_LOG.md 統計完成，所有檔案一致。

**人工確認點**：無（所有變更已在 workspace 內完成）。

---

## 注意事項（來自 eval_gate 實戰經驗）

1. **不要跳過 discovery 直接做 scan** — 不知道模組路徑、依賴、消費者，scan 缺維度。
2. **不要在 fix_round 處理跨檔案的 debt** — D-005（_total_context_tokens 重複）和 D-008（KNOWN_GATE_TAGS 硬編碼）都是跨檔案的。把它們標記為 deferred，不混入單檔 round。
3. **不要修改行為** — review gate 的底線是「不接受行為變更的 suggested patch」。if 條件改變、try/except 包裝、TypedDict 新增 — 這些需要另走 code review。
4. **APPLY_PLAYBOOK.md 本身不修改** — 每次複製、建立新的 apply_plan_vN.md，不改 playbook 本文。
5. **apply 階段需要人類參與** — Hermes 不改 repo。APPLY_PLAYBOOK.md §4 的角色分工不可違反。
