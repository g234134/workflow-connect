# W5-D-W4-FIX-A-IMPLEMENTATION-01 — W4-A Gate Checklist 清理（實作票模板）

> **用途**：這份模板是給實作者（Cursor／開發者）開工用的任務卡。  
> **源頭**：`W5-D-W4-FIX-A_plan.md`（方案卡）→ 第 (4) 節 7 步高層實作 + 第 (6) 節任務卡骨架。  
> **範圍**：僅 W4-A 相關文檔與 case markdown；**不改**程式碼、CI、其他 Wave、run_records 正文。  
> **Lane 推定**：`doc-sync`（僅文檔整理，不動 runtime）。

---

## 1) 基本資訊

| 欄位 | 值 |
|------|-----|
| **任務名稱** | W5-D-W4-FIX-A-IMPLEMENTATION-01 |
| **任務說明** | 修正 W4-A gate checklist 的命名不一致、證據路徑錯誤、欄位衝突、缺失實例，使其可完整重建 rollout 決策 |
| **主標的文件** | `workflow_v2/20_pilot/W3-A_case/W4-A_gate_checklist.md` |
| **輔助文件** | `workflow_v2/20_pilot/W3-A/W4-A_rollout_runbook.md` |
| **次要範圍** | `workflow_v2/20_pilot/W3-A_case/` 下的新 example 檔案 |
| **非範圍** | 任何 `.ps1`/`.py`/CI YAML/`00_master_plan.md`/`90_run_queue.md`/`99_latest_status.md`/`CHK-W4` Memory/`08_art_rel_exec.json` |

### 允許的操作類型

- 修改 markdown 中的欄位名、證據路徑、註釋
- 在 `W3-A_case/` 下新增 `_example` 後綴的標竿範本
- 在 checklist 文首新增 schema 版本對照表
- 在 checklist 各節標註 deprecated／N/A 標記
- 調整 runbook §2 路徑圖與 §7 範例中的 step 命名

### 不允許的操作

- 改動任何 script（`wf_k2_rollout_run.ps1`、`wf_k2_rollout_canary_sim.py`）
- 改動任何 CI workflow（`.github/workflows/`）
- 改動 JSON artifact（`07_art_rel_dec.json`、`08_art_rel_exec.json`）
- 改動歷史 run_records 正文（`shadow_run_01.md`、`canary_run_01.md`、`rollout_trace.jsonl`、`shadow_state.json` 等）
- 改動 `00`/`90`/`99` 全域文檔
- 改動 CHK-W4 或任何 W5-* Ticket Memory
- 改動檔名或目錄結構
- 新增 gate 或改變檢查項目數量

---

## 2) 前提與不變條件

### 實作前須成立

- [x] `run_records/2026-05-29_110959/`（早期 schema，含 `shadow_run.md`、`canary_run.md`、同目錄下的 `rollout_trace.jsonl`）
- [x] `run_records/2026-05-29_111042/`（正式 schema，含 `shadow_run_01.md`、`canary_run_01.md`、`shadow_state.json`、`rollout_trace.jsonl`、`eval/` 子目錄）
- [x] `W4-A_gate_checklist.md`、`W4-A_rollout_runbook.md`（主 runbook 與案卷索引）均已存在
- [x] `07_art_rel_dec.json`、`08_art_rel_exec.json`、`canary_env.md` 均已存在
- [x] `canary_cohort_state.json` 位於 `runs/w4a-int-20260529-pilot/` 下（非案卷根）
- [x] `override_record.json` **不存在**（無 override run 被執行過）
- [x] CHK-W4 已判定 `OK_WITH_KNOWN_GAPS`，GAP-1~4 已記錄

### 不得改動的事項（不變條件）

1. **不改歷史結果**：不修改任何舊 run 的 trace、state、run markdown。schema 差異只在 checklist 標註，不在舊檔案上補欄位。
2. **不改 JSON artifact 的值**：`rollback_path_valid: false` 保持原值，僅在 checklist 加語義註釋。
3. **不改檔名與目錄結構**：所有 checklist 路徑修正採「修正 checklist 內的證據路徑字串」策略，而非移動檔案。
4. **不改 gate 邏輯**：D 門 4 項禁區保持人工 checkbox 形式，不加入自動化檢查。
5. **不改 CHK-W4 判定**：本票只能對齊文檔敘述，不能改 `OK_WITH_KNOWN_GAPS` 的結論等級或 gap 清單。
6. **注意 90_run_queue.md 的格式汙染**：已知 `90` 因累積 patch 操作有行號前綴汙染。實作中若需手動對照 `90` 的 W4-A 行，請使用 workspace 內的清洗版（如果存在），不要直接貼 `90` 原文。

---

## 3) 具體步驟（實作 checklist）

實作者依序完成以下步驟。每個步驟都標註了「目標檔案」與「變更類型（命名 / 路徑 / 註釋 / 新增）」以便事後回報。

### Step 1 — 對齊 runbook 與 checklist 的 step 命名語義

| 項 | 內容 |
|---|------|
| **目標文件** | `W3-A/W4-A_rollout_runbook.md`（主 runbook） |
| **變更類型** | 命名 |
| **做什麼** | 將 runbook §2 端到端路徑圖中的 step 名和 §7 範例中的 `step=shadow`/`step=canary` 改為與實際 trace 一致的細粒度名。 |
| **參考** | 111042 trace 實際 step 序列：`k2_shadow_unittest` → `ibridge_exporter_shadow` → `eval_ci_check_shadow` → `internal_canary`。§3 門控描述（細粒度）與 §2 路徑圖（也可能用粗粒度）需一併確認是否都有對齊。 |

### Step 2 — 修正 checklist 證據路徑

| 項 | 內容 |
|---|------|
| **目標文件** | `W3-A_case/W4-A_gate_checklist.md` |
| **變更類型** | 路徑 |
| **做什麼** | 逐項修正 A1/A5/A6/B8/C1 的證據欄位：將 `runs/` 前綴改為 `run_records/<run_id>/`，將模糊描述改為具體相對路徑。 |
| **已知需改的項** | A1 證據（`runs/…` → `run_records/<run_id>/eval/…`）、A5 證據（「案卷 runs 目錄」→ `run_records/<run_id>/shadow_run_01.md`）、C1 證據（暗示案卷根 → `runs/w4a-int-20260529-pilot/canary_cohort_state.json` 或加註路徑偏移說明）。 |

### Step 3 — 標記 rollback_path_valid 衝突

| 項 | 內容 |
|---|------|
| **目標文件** | `W3-A_case/W4-A_gate_checklist.md`（B6 項） |
| **變更類型** | 註釋 / 補充說明 |
| **做什麼** | 在 B6 項旁加一行註釋：說明 `08_art_rel_exec.json` 中的 `rollback_path_valid: false` 可能是因為該欄位語義指「生產回退路徑已驗證」，而當前 internal canary 階段的回退（cohort→0）在等價意義上滿足條件。不改 artifact 值。 |
| **參考** | `08_art_rel_exec.json` 的 `not_in_scope` 已經說明了範圍限制。註釋應引用該字段作為 context。 |

### Step 4 — 標記缺失證據與 override 佔位

| 項 | 內容 |
|---|------|
| **目標文件** | `W3-A_case/W4-A_gate_checklist.md`（C2/C3 項） |
| **變更類型** | 標記 / 註釋 |
| **做什麼** | 在 C2（override 角色）、C3（override reason）的證欄中標記 `N/A — 目前無 override 實例`。不建立假的 `override_record.json`，不做超過「標記」以外的動作。 |
| **補充** | 對於 `canary_cohort_state.json` 路徑偏移（Step 2 已處理），可在 C1 證據欄中同時註明「當前位於 `runs/w4a-int-20260529-pilot/`」。 |

### Step 5 — 在 checklist 文首新增 schema 版本對照表

| 項 | 內容 |
|---|------|
| **目標文件** | `W3-A_case/W4-A_gate_checklist.md`（文首，標題行之後） |
| **變更類型** | 新增（對照表） |
| **做什麼** | 在 checklist 文首新增一段「Schema 版本對照」，列出 early schema（110959）與正式 schema（111042）的欄位名對應、trace step 名對應、檔名對應。 |
| **對照表應包含** | |
| | 1. **Run ID**：`2026-05-29_110959` vs `2026-05-29_111042`（及後續正式 run） |
| | 2. **Shadow 檔案名**：`shadow_run.md` vs `shadow_run_01.md` |
| | 3. **Trace step 名**：`k2_shadow` / `eval_ci_check_fixture` vs `k2_shadow_unittest` / `ibridge_exporter_shadow` / `eval_ci_check_shadow` |
| | 4. **Canary step 名**：`internal_canary`（兩者相同） |
| | 5. **Shadow 欄位名**：`unittest_exit`/`eval_ci_fixture`/`spool_indexed_lines` vs `unittest_ok`/`export_ok`/`eval_ci_ok` |
| | 6. **影響的 checklist 項**：110959 僅能覆蓋 A1~A2（細粒度不足），111042 可覆蓋 A1~A6 |

### Step 6 — 建立 post-hoc 簽收範例

| 項 | 內容 |
|---|------|
| **目標文件** | `W3-A_case/W4-A_gate_checklist_completed_111042_example.md`（新增） |
| **變更類型** | 新增 |
| **做什麼** | 以 run `2026-05-29_111042` 為對象，按修正後的 checklist 走一遍，填寫 E 簽收行，存為 `_example` 檔案。內文**首行**必須標 `# EXAMPLE ONLY`，全檔明確不得被當成正式簽收。 |
| **簽收行填寫建議** | `release_id` = `w4a-p2-canary-2026-05-29`（取自 `07_art_rel_dec.json`）；`checker` = `CHK-W4 (post-hoc)`；`date` = 實作當日；`verdict` = `pass`（根據 CHK-W4 判定）；每項 ✓ 可在其後方加 `(111042)` 或實證路徑。 |
| **注意** | 此為**後設回溯填寫**，不是正式的即時簽收。新舊 run 都要能用。 |

### Step 7 — 驗收巡檢（全量檢查）

| 項 | 內容 |
|---|------|
| **目標文件** | 所有修改過的檔案 |
| **變更類型** | 檢查（無改動） |
| **做什麼** | 走一遍下方的驗收條件（§5），在回報模板（§6）中逐條記錄結果。確保 Step 1~6 的變更無遺漏、無衝突。 |

---

## 4) 風險與注意事項

### 實作端須留意清單

| # | 風險 | 注意事項 |
|---|------|---------|
| **R1** | **舊 schema run（110959）對不上新命名** | Step 1 改 runbook step 名時，110959 trace 的 `k2_shadow` 與 111042 的 `k2_shadow_unittest` 不同。Step 5 的對照表必須同時覆蓋兩種 schema。**不可為了讓舊 run 符合新命名而去改舊 trace 內容**。 |
| **R2** | **rollback_path_valid 語義擴散** | 只改 checklist（Step 3）。不要因為 checklist 改了，就去改 `08_art_rel_exec.json` 的值或 `k2_deployment_governance.md` 的定義。如發現相鄰文檔也有此字段，在回報中記錄發現，不擅自修改。 |
| **R3** | **example 範本被誤認為正式簽收** | 檔名必須包含 `_example`，內文首行必須是 `# EXAMPLE ONLY — post-hoc retroactive fill, not a live gate sign-off`。管理層不應以此作為「W4-A 已正式簽收」的證據。 |
| **R4** | **D 門不處理** | 4 項禁區是人工自檢項。本票不加入自動化、不改 D 門內容。驗收時只需確認 D 門的 checkbox 保持原樣。 |
| **R5** | **路徑沒變但引用文檔期待內容不同** | Checklist 文首新增 schema 對照表後，`00_master_plan.md` / `99_latest_status.md` 對 `W4-A_gate_checklist.md` 的引用仍有效（路徑不變）。不需要更新這些引用。 |
| **R6** | **跨 run 的 canary_run_01.md 與 canary_run.md 檔案名不同** | Step 5 對照表已覆蓋。實作時若想將 `canary_run.md` 重命名為 `canary_run_01.md` 以保持一致 → **不可以**（違反不變條件 §2-3 不改檔名）。 |
| **R7** | **90_run_queue.md 的 format pollution** | 90 文件因累積 patch 有行號前綴汙染。若需參考 90 中 W4-A 行來確認 gate checklist 引用敘述，請在 workspace 的清洗版中查閱，不要直接複製 90 汙染內容。 |

### 通用原則

- **遇到無法對齊的歷史資料 → 加註說明，不強行改舊記錄。**
- **遇到跨文檔語義衝突（如 `rollback_path_valid` 在其他地方也有定義）→ 僅在本票範圍內記錄衝突，不擅自修復相鄰文檔。**
- **所有新增的 example/註解都必須清楚標明不是正式簽收。**

---

## 5) 驗收條件

實作者完成 Step 1~6 後，逐項檢查並填入結果。第 A 欄為勾選，第 B 欄為簡短說明。

| # | 驗收條件 | 如何驗證 | 實測結果 |
|---|---------|---------|---------|
| AC1 | W4-A gate 名稱（section A shadow / section B canary / section C rollback+override）在 runbook、checklist、CHK-W4 三處一致 | 對比 `W4-A_rollout_runbook.md` §2/§7 → `W4-A_gate_checklist.md` → `CHK-W4-WAVE4-CLOSURE.memory.md` §W4-A Check Record | |
| AC2 | 對正式 run（111042）可逐項走完 A1~B8，每個 ✓ 項的證據路徑和欄位值都可對應到實際檔案 | 手走一遍 A1~B8，記錄每個 |  |
| AC3 | 對早期 run（110959）至少可覆蓋 A1~A3，其餘項標註 schema 限制 | 比對 110959 的 trace/run markdown 欄位名與 checklist 證據欄是否匹配 |  |
| AC4 | `grep -n 'runs/' W4-A_gate_checklist.md` 回傳 0（無殘留 `runs/` 假路徑） | 在 WSL 上執行該 grep 命令 |  |
| AC5 | `rollback_path_valid` 衝突已在 B6 項有明確標記（原因或等價條件） | 讀 B6 項的附加行，可理解為何 artifact 有 `false` 而 checklist 仍允許通過 |  |
| AC6 | 不存在的證據（`override_record.json`）在 C2/C3 項有明確的 N/A 標記 | 讀 C2/C3 項旁有 `N/A` 或等同標記，非留空白 |  |
| AC7 | checklist 文首（標題後）有 schema 版本對照表，清楚標明 early（110959）vs formal（111042）的欄位差異 | 讀文首前 10~20 行，確認對照表存在 |  |
| AC8 | `_example` 範本檔的首行為 `# EXAMPLE ONLY`，檔名含 `_example` 後綴 | 檢查 `W3-A_case/W4-A_gate_checklist_completed_111042_example.md` 是否存在且符合規範 |  |
| AC9 | 所有修改僅限於授權文件（checklist + runbook），未觸及腳本/CI/JSON/run_records/00/90/99 | `git diff --stat`（在實作前後）或手動比對修改檔案清單 |  |

---

## 6) 回報格式模板

實作者完成後，按以下框架填寫回報。貼在實作票的 comment 或 Workspace 戰報中。

```markdown
### 實作回報 — W5-D-W4-FIX-A-IMPLEMENTATION-01

**實作日期**：YYYY-MM-DD
**實作者**：<role>

#### 修改檔案清單

| 檔案 | 變更類型 | 說明 |
|------|---------|------|
| `W3-A/W4-A_rollout_runbook.md` | 命名 | §2 路徑圖 + §7 範例 step 名對齊 |
| `W3-A_case/W4-A_gate_checklist.md` | 多項 | 路徑修正（A1/A5/A6/B8/C1）+ B6 註釋 + C2/C3 N/A + 文首 schema 對照表 |
| `W3-A_case/W4-A_gate_checklist_completed_111042_example.md` | 新增 | 111042 run 的 post-hoc 簽收範例 |

#### Step 命名前後對照

| 來源 | 前 | 後 |
|------|----|----|
| runbook §7 `step=shadow` | `step=shadow` | <填改後的名> |
| runbook §7 `step=canary` | `step=canary` | <填改後的名> |
| checklist A6 | `step=shadow` | <填改後名或 alias> |
| checklist B8 | `step=canary` | <填改後名或 alias> |

#### 111042 run 走查結果（從 checklist 到證據檔案）

| 項 | 證據路徑（修正後） | 欄位值是否符合？ | 備註 |
|----|------------------|----------------|------|
| A1 | `run_records/2026-05-29_111042/eval/shadow_ibridge_records.latest.jsonl` | 是 | 檔案存在 |
| A2 | `run_records/2026-05-29_111042/shadow_state.json` → `"ok": true` | 是 | |
| A3 | 從 A1 證據判斷 `infra_risk` 未觸發 | 是（由 eval 訊息） | 或加註「手動確認」 |
| A4 | 無須證據（runbook §3 保證） | — | 已引用 runbook |
| A5 | `run_records/2026-05-29_111042/shadow_run_01.md` | 是 | |
| A6 | `run_records/2026-05-29_111042/rollout_trace.jsonl` → `step=…` | <是/否> | |
| B1 | `run_records/2026-05-29_111042/shadow_state.json` → `"ok": true` | 是 | |
| B2 | `07_art_rel_dec.json` → `traffic_percent: 5` | 是 | |
| B3 | `07_art_rel_dec.json` → `decision: approve` | 是 | |
| B4 | `08_art_rel_exec.json` → `published_at` 存在 | 是 | |
| B5 | `canary_env.md` → 與 DEC `target_audience_or_env` 一致 | 是 | 均為 `staging-internal` |
| B6 | 已標記語義註釋（artifact 為 `false`） | — | 見 Step 3 |
| B7 | `08_art_rel_exec.json` → `not_in_scope` | 是 | |
| B8 | `rollout_trace.jsonl` → `step=…` | — | 同 A6 處理方式 |

#### 驗收條件檢查

| # | 通過？ | 備註 |
|---|-------|------|
| AC1 | [ ] | |
| AC2 | [ ] | |
| AC3 | [ ] | |
| AC4 | [ ] | `grep` 結果：<0 或 >0> |
| AC5 | [ ] | |
| AC6 | [ ] | |
| AC7 | [ ] | |
| AC8 | [ ] | |
| AC9 | [ ] | |

#### 已知殘留

- 列舉驗收條件中未完全通過的項及原因
- 列出執行中發現但本次不處理的跨文檔衝突
- 列出實作中遇到的「rollback_path_valid 在其他文件也有定義」之類的發現
```

---

## Extra Notes for Implementer

### 如何選擇 example run
**唯一推薦**：`2026-05-29_111042`。原因：
- 它是 schema v0.1 的正式結構，有完整的 `shadow_run_01.md` / `canary_run_01.md` / `shadow_state.json` / `rollout_trace.jsonl` / `eval/` 子目錄。
- 它經過了 `-Phase full`（shadow + canary），可覆蓋 A1~B8 全部檢查項。
- 它是 CHK-W4 檢查時參考的主要 run。

不建議用 `110959`（schema v0.0，欄位名不同、無 `eval/` 子目錄）或 `111011`（僅 rollback）作為 example run。

### 如何處理早期 run schema（110959）
- **不修改** 110959 下的任何檔案。
- Schema 對照表（Step 5）已經列出了欄位名差異。
- 實作完成後，當驗收 AC3 時，拿 110959 跑一次 partial 驗證即可（只能過 A1~A3 部分項，其餘標 `N/A (schema v0.0)`）。

### 關於 90_run_queue.md 的汙染
已知 `90_run_queue.md` 因累積 patch 操作，每行前面都有重複的行號前綴（如 `228|228|228|W4-A-K2-…`）。本票不修改 `90`，但如果需要對照 `90` 中 W4-A 的 Notes 與 checklist 的關係，建議用 workspace 內的清洗版（`/mnt/d/hermes-workspace/milestones/CHK-W4/90_run_queue.cleaned.v1.md`）。

### 關於 D 門的處理
D 門 4 項禁區在本票中不做任何修改（保持原文的 checkbox `- [ ]` 形式）。驗收時只需確認 D 門未被誤改。

### 回報中的 diff 要求
回報不需要貼「完整 diff 全文」，但需要：
- 修改檔案清單（檔名 + 變更類型）
- Step 命名前後對照摘要（表格形式）
- 111042 走查結果（表格形式，每一項都能追到實際證據檔案）
- 驗收條件勾選結果
