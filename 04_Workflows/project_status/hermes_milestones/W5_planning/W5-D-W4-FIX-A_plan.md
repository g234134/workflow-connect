# W5-D-W4-FIX-A — W4-A Gate Checklist 命名／證據清理方案

> **票號**：W5-D-W4-FIX-A 實作方案卡  
> **源頭**：CHK-W4 §W4-A Check Record → GAP-1（trace key 不一致）+ 衍生清理  
> **範圍**：僅 W4-A gate checklist 相關文檔與案卷的命名／證據不一致  
> **不處理**：metrics/cohort 樣本（GAP-2~4）、CHK-W4 判定語義、實際 rollout 腳本  

---

## (1) 背景摘要

**W4-A Gate Checklist 的角色**：
- 定義於 `workflow_v2/20_pilot/W3-A_case/W4-A_gate_checklist.md`。
- 被 5 處參考：runbook（`W4-A_rollout_runbook.md` line 7）、`00_master_plan.md` §15.1、`99_latest_status.md`、`90_run_queue.md` W4-A 行、以及至少 5 份 W5-A Ticket Memory 的 read_set。
- 用途：每次 `-Phase full|shadow|canary` 後勾選，做為「可重複 rollout 決策」的檢查清單。
- 結構：A 門（shadow，6 項）、B 門（canary，8 項）、C 門（rollback/override，3 項）、D 禁區（4 項），外加 E 簽收行（`release_id`/`checker`/`date`/`verdict`）。

**已知不一致類型（3+1 類）**：

| 類型 | 說明 |
|------|------|
| **命名不對齊** | checklist 內的證據路徑/step name 與實際 `rollout_trace.jsonl`、filesystem 路徑不同 |
| **證據與實物衝突** | checklist 要求的欄位值（如 `rollback_path_valid=true`）與實際 artifact 內容（`false`）矛盾 |
| **缺少對應實例** | checklist 項引用不存在的檔案（`override_record.json`）或路徑與落點不同（`canary_cohort_state.json`） |
| **跨 run 命名不一致** | 早期 run（110959）的 trace/run 欄位命名與後期 run（111042）不同，checklist 未區分 |

---

## (2) 目標與邊界

### 目標
讓 W4-A 的 gate checklist 在文檔和 `run_records` 上可以完整重建一次最小 rollout 決策：  
任一 W4-A run → 對應 `W4-A_gate_checklist.md` 簽收本 → 每個 ✓ 項可索引到實際證據（檔案/欄位值）→ 可重播出「為何當次通過／被擋」的判斷過程。

### 不會做的事
- 不改實際 rollout 腳本（`wf_k2_rollout_run.ps1`、`wf_k2_rollout_canary_sim.py`）
- 不改 CI workflow（`.github/workflows/eval-gate-ci.yml`）
- 不改 CHK-W4 的 GAP-2~4 判定語義
- 不引入新 gate 或新檢查項
- 不重新執行或覆蓋歷史 run_records
- 不改 `00_master_plan.md`/`90_run_queue.md`/`99_latest_status.md`（語義變更歸 DOCSYNC 票）

---

## (3) 只讀調查結果摘要

### 發現 1：checklist 內 `step=shadow` 與 trace 實際細粒度 step 不一致

| 來源 | 用的 step 名 | 實際 trace 內容 |
|------|------------|----------------|
| checklist A6 | `step=shadow` | `k2_shadow_unittest` / `ibridge_exporter_shadow` / `eval_ci_check_shadow` |
| checklist B8 | `step=canary` | `internal_canary` |
| runbook §7 範例 | `step=shadow` / `step=canary` | 同上（不一致） |
| 早期 run (110959) trace | `step=k2_shadow` | 與後期 run (111042) 的 trace step 命名也不同 |

**影響**：A6/B8 無法直接用 `grep step=shadow rollout_trace.jsonl` 找到 — 實際 step 名是 `k2_shadow_unittest`。

### 發現 2：checklist 內的證據路徑與實際 filesystem 不對齊

| checklist 項 | 寫的路徑 | 實際路徑 |
|-------------|---------|---------|
| A1 證據 | `runs/<id>/eval/shadow_ibridge_records.latest.jsonl` | `run_records/<run_id>/eval/shadow_ibridge_records.latest.jsonl` |
| A5 證據 | `案卷 runs 目錄`（模糊） | `run_records/<run_id>/shadow_run_01.md` |
| C1 證據 | `canary_cohort_state.json`（暗示案卷根） | `runs/w4a-int-20260529-pilot/canary_cohort_state.json` |

**影響**：直接按 checklist 證據欄位找檔案會找不到或找錯。

### 發現 3：checklist B6 要求 `rollback_path_valid=true`，但實際 artifact 為 `false`

- `08_art_rel_exec.json` line 55: `"rollback_path_valid": false`
- `08_art_rel_exec.json` line 56: `"not_in_scope": "No remote prod auto rollout; no Phase 3+; no merge adapter change"`
- 當前 W4-A 的最小 v1 階段，rollback path 實際上就是「設 cohort=0」— 這在 internal canary 中是 valid 的，但 artifact 欄位值卻寫了 `false`。
- 分歧原因推測：`rollback_path_valid` 字段定義可能指「到 prod 的回退路徑已驗證」，而非「internal canary 的回退路徑已驗證」。checklist 用了不同語義尺度。

### 發現 4：`override_record.json` 不存在

- checklit C2/C3 引用 `override_record.json`，但 `W3-A_case/` 下無此檔案。
- 無任何 run 曾使用 `-Phase override` 路徑。
- 檢查簽收行 E 亦無範例填寫值（所有欄位空白）。

### 發現 5：早期與後期 run 的欄位命名不一致，checklist 未標註版本差異

- Run `2026-05-29_110959`（早期 schema）：
  - 檔名 `shadow_run.md`（而非 `shadow_run_01.md`）
  - 欄位：`k2_phase`、`unittest_exit`、`eval_ci_fixture`、`spool_indexed_lines`
  - Trace step：`k2_shadow`、`eval_ci_check_fixture`、`internal_canary`
- Run `2026-05-29_111042`（正式 schema）：
  - 檔名 `shadow_run_01.md`、`canary_run_01.md`
  - 欄位：`unittest_ok`、`export_ok`、`eval_ci_ok`
  - Trace step：`k2_shadow_unittest`、`ibridge_exporter_shadow`、`eval_ci_check_shadow`、`internal_canary`

**影響**：同一份 checklist 無法同時適用於兩個 schema 的 run（證據欄位名稱和 trace step 名不同）。

### 發現 6：checklist 有 4 項禁區（D 門），但無運行時檢查機制

- D1：禁改 prod `.github/workflows` release
- D2：禁宣稱遠端 prod Phase 3+
- D3：禁輸出 `.env`／金鑰原文
- D4：禁改 `merge_ask_and_k2`／adapter
- 這些是人工自檢項（checkbox），無對應 CI gate 或 script 檢查。本票不討論自動化。

### 發現 7：runbook §7 範例中的 step 名與 checklist 一致，但與真實 trace 不一致

- Runbook §7 成功範例寫 `step=shadow` 和 `step=canary`
- 但 runbook §3 門控描述的是實際細粒度（unittest exit 0 + `eval_ci_check` exit 0），並未說 trace 中只用 `step=shadow`
- 即 runbook 自身在 §3（設計層）和 §7（範例輸出層）之間也存在步長粒度不一致。

---

## (4) 建議的實作步驟（高層）

### 步驟 1：統一 runbook 與 checklist 的 step 命名語義

- **做什麼**：在 `W4-A_rollout_runbook.md` §2 端到端路徑圖和 §7 範例中，修正 step 名稱為 trace 實際使用的細粒度名（`k2_shadow_unittest` / `ibridge_exporter_shadow` / `eval_ci_check_shadow` 等）或明確定義一個標準化 alias。
- **影響範圍**：`W3-A/W4-A_rollout_runbook.md`、`W3-A_case/W4-A_gate_checklist.md`

### 步驟 2：修正 checklist 證據路徑為實際 filesystem 相對路徑

- **做什麼**：將 checklist 各項（A1/A5/A6/B8/C1）的證據欄位從 `runs/` 前綴更正為 `run_records/` 前綴，取消模糊表述（如「案卷 runs 目錄」），改為具體相對路徑。
- **影響範圍**：`W3-A_case/W4-A_gate_checklist.md`

### 步驟 3：解決或標記 checklist B6 `rollback_path_valid` 衝突

- **做什麼**：檢查 `08_art_rel_exec.json` 中 `rollback_path_valid: false` 是因欄位語義不同（prod vs internal canary）還是單純填錯。若語義不同，在 checklist B6 補充註釋說明當前 internal canary 階段的等價驗收條件（cohort→0 即可視為 rollback_path_valid）；若確為填錯，在 `08_art_rel_exec.json` 旁附勘誤說明（不改內容）。
- **影響範圍**：`W3-A_case/W4-A_gate_checklist.md`、可選 `08_art_rel_exec.json` 旁勘誤 note

### 步驟 4：為不存在的檔案建立證據佔位或標準化簽收模板

- **做什麼**：
  - 對於 `override_record.json`（不存在）：在 checklist C2/C3 旁標註「override 路徑尚未被實際跑過，本例為 N/A」，或建立一個最小模板文件放在 `W3-A_case/` 下。
  - 對於 `canary_cohort_state.json`（路徑偏移）：確認 checklist C1 證據路徑應為 `runs/w4a-int-20260529-pilot/canary_cohort_state.json` 或將該文件移動/鏈接到案卷根。
- **影響範圍**：`W3-A_case/W4-A_gate_checklist.md`，可選 `W3-A_case/` 下的模板或 link

### 步驟 5：在 checklist 中標註 schema 版本差異

- **做什麼**：在 checklist 文首或 A 門附註說明早期 run（schema v0.0 = 110959 式）與正式 run（schema v0.1 = 111042 式）對應哪些 check 項的證據路徑/欄位名有差異；指明當前 run_records 中哪些 run 屬於哪個 schema。
- **影響範圍**：`W3-A_case/W4-A_gate_checklist.md`、`W3-A_case/run_records/` 下可選 README

### 步驟 6：建立一次完整的 post-hoc 簽收範例

- **做什麼**：選一套 run（推薦 `2026-05-29_111042`），按改正後的 checklist 走一遍，填寫 E 簽收行（`release_id`、`checker`、`date`、`verdict`），並將填寫結果存為 `W3-A_case/W4-A_gate_checklist_completed_2026-05-29_111042.md` 作為範本。
- **影響範圍**：`W3-A_case/` 下新增 completed 範本

### 步驟 7：更新所有參考 W4-A_gate_checklist.md 的 Ticket Memory 路徑（可選）

- **做什麼**：確認 CHK-W4 及 W5-A-* Ticket Memory 中對 `W4-A_gate_checklist.md` 的引用是否穩定（路徑不變則不需要改）。如果 path 沒變，本步可跳過。
- **影響範圍**：`40_ticket_memory/` 下若有路徑變更才需要動

---

## (5) 風險與驗收要點

### 風險

| # | 風險 | 影響 | 緩解方式 |
|---|------|------|---------|
| R1 | 改 checklist 的證據路徑或 step 名後，舊 run_records（110959 schema）對不上新命名 | 歷史 run 無法用新版 checklist 復盤 | 步驟 5 標註 schema 差異；保留舊 schema 的對照表 |
| R2 | `rollback_path_valid` 的語義重新定義可能引發與相鄰文檔（如 `k2_deployment_governance.md`）的矛盾 | 跨文檔不一致 | 步驟 3 強調只加註釋不改值；必須先確認相鄰文檔的定義 |
| R3 | 建立 completed 範本（步驟 6）可能被誤解為「W4-A gate 已經正式簽過一次」 | audit trail 混亂 | 範本檔名加 `_example` 或存放在子目錄，明確標註 `# EXAMPLE ONLY` |
| R4 | D 門（禁區）無法自動驗證，純人工自檢 | 實質上無 enforcement | 本票不處理；在驗收要點中列為已知限制 |
| R5 | 步驟 7 更新 Ticket Memory 引用時若路徑不變但名稱微調，可能導致依賴 `W4-A_gate_checklist.md` 的 cron/CI 失效 | 外部引用斷裂 | 所有變更僅限於 checklist 的內容和證據描述，不改檔名和路徑 |

### 驗收要點

| # | 驗收條件 | 如何驗證 |
|---|---------|---------|
| A1 | W4-A gate 名稱（shadow section A / canary section B / rollback section C）在 runbook、checklist、CHK-W4 三處一致 | 對比 `W4-A_rollout_runbook.md` §2／§7 → `W4-A_gate_checklist.md` → `CHK-W4-WAVE4-CLOSURE.memory.md` §W4-A Check Record |
| A2 | 任選一個 W4-A run（如 111042）可用 checklist 逐項對應到實際證據（trace 行、state JSON、run markdown） | 手走一遍 A1~B8，每個 ✓ 項的文件路徑和欄位值都可讀取 |
| A3 | checklist 的證據路徑均為 `run_records/` 前綴，無 `runs/` 假路徑 | `grep -n 'runs/' W4-A_gate_checklist.md` 回傳 0 |
| A4 | `rollback_path_valid` 衝突在 checklist 上已標記原因或等價條件 | 讀 B6 項的附加行，可理解為何 `08_art_rel_exec.json` 有 `false` 而 checklist 仍允許通過 |
| A5 | 不存在的證據（`override_record.json`）在 checklist 上有明確的 N/A／範本標記 | 讀 C2/C3 項旁有註釋，非留空白 |
| A6 | checklist 文首有 schema 版本對照表，清楚標明早期 run 的欄位/step 差異 | 讀文首前 10 行 |

---

## (6) 給未來實作票的任務卡骨架

```
票名：W4-A-FIX-01 — Gate checklist 命名與證據清理
前置：W5-D-W4-FIX-A 方案卡（本文件）
Lane：doc-sync（僅文檔整理，不改 runtime）

要改的檔案（僅以下）：
  - workflow_v2/20_pilot/W3-A_case/W4-A_gate_checklist.md（主標的）
  - workflow_v2/20_pilot/W3-A/W4-A_rollout_runbook.md（§2/§3/§7 step 名校正）

允許的操作：
  - 修改 markdown 內容（命名、路徑、註釋）
  - 在 W3-A_case/ 下新增 _example 範本（不含 run_records/ 內）
  - 新增 schema 版本對照表到 checklist 文首

禁止事項：
  - 不改 CI、tools、config JSON、run_records 正文
  - 不改 00/90/99 語義
  - 不改檔名或目錄結構
  - 不改 08_art_rel_exec.json 內容

回報要求：
  - diff 範圍：只限 checklist + runbook 的 markdown 行
  - 須附：A1~B8 各項在 111042 run 上的實測對應結果（檔案路徑 + 欄位值）
  - 不存在的證據（override_record.json）須在 C2/C3 旁有 N/A 標記
  - 附 schema 版本對照表

風險提醒：
  - 留意 R1：110959 schema 的 trace step 命名（k2_shadow）與 111042 不同，需在對照表中同時覆蓋
  - 留意 R2：rollback_path_valid 僅加註釋，不改值
  - 留意 R3：範本檔名含 _example，文內首行 # EXAMPLE ONLY
```

---

## 附錄 A — 調查中發現的檔案路徑對照速查

| 文件 | 路徑 |
|------|------|
| 主 runbook | `workflow_v2/20_pilot/W3-A/W4-A_rollout_runbook.md` |
| 案卷索引 runbook | `workflow_v2/20_pilot/W3-A_case/W4-A_rollout_runbook.md` |
| Gate checklist | `workflow_v2/20_pilot/W3-A_case/W4-A_gate_checklist.md` |
| ART-REL-DEC | `workflow_v2/20_pilot/W3-A_case/07_art_rel_dec.json` |
| ART-REL-EXEC | `workflow_v2/20_pilot/W3-A_case/08_art_rel_exec.json` |
| Canary cohort state | `workflow_v2/20_pilot/W3-A_case/runs/w4a-int-20260529-pilot/canary_cohort_state.json` |
| Canary env 指針 | `workflow_v2/20_pilot/W3-A_case/canary_env.md` |
| 正式 run（111042） | `workflow_v2/20_pilot/W3-A_case/run_records/2026-05-29_111042/` |
| 正式 run trace | `workflow_v2/20_pilot/W3-A_case/run_records/2026-05-29_111042/rollout_trace.jsonl` |
| 早期 run（110959） | `workflow_v2/20_pilot/W3-A_case/run_records/2026-05-29_110959/` |
| CHK-W4 memory | `workflow_v2/40_ticket_memory/CHK-W4-WAVE4-CLOSURE.memory.md` |
| W5-A 父票 memory | `workflow_v2/40_ticket_memory/W5-A-K2-ROLLOUT-EXPANSION.memory.md` |
