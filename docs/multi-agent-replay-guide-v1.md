# Multi-Agent Replay Guide v1

> **§0 上游 contract**：Phase 4 contract SSOT → [`docs/phase4-multi-agent-collaboration-contract-v1.md`](phase4-multi-agent-collaboration-contract-v1.md)（验收入口 §7、replay 假设）；本 guide 为事后分析操作层。

> **版本**：v1.0  
> **適用**：分析已完成 Multi-Chat 票（Orchestrator / Implementer / Reviewer / Scribe 協作歷史）  
> **日期**：2026-06-10  
> **上游文件**：`docs/multi-agent-collaboration-spec-v1.md` · `docs/multi-agent-handoff-runbook-v1.md`

---

## §1 目的

本指南定義如何「replay」一張已完成的 Multi-Chat 票——即透過閱讀 state 檔、spec、code/tests、index，理解：

1. **What happened**：這張票做了什麼、產出什麼
2. **How it happened**：四角色如何協作、何時 loop back、關鍵決策點
3. **What to learn**：成功模式、失敗陷阱、後續票建議
4. **How to audit**：驗證結果、確認無遺漏、追蹤 gaps

本指南用於：
- **事後分析**：Wave 結束後回顧
- **知識傳遞**：新成員理解歷史票
- **問題排查**：當前票遇到困難時參考歷史解法
- **審計驗收**：確認票確實完成、無懸空依賴

---

## §2 如何選一張已完成票做 Replay

### 2.1 選票原則

| 目的 | 選票建議 | 範例 |
|------|----------|------|
| 理解標準流程 | 一次通過（`accepted`）的票 | W3-TL-T1（Catalog） |
| 理解 gaps 處理 | `accepted_with_gaps` 的票 | W4-T2（Runner） |
| 理解 loop back | `needs_changes` 後重跑的票 | （需查找） |
| 理解複雜協作 | 跨多領域的大票 | W4-T1（glue） |
| 理解文檔收口 | Scribe 有豐富 D_REPORT 的票 | W4-T3-A（CLI path） |

### 2.2 選票檢查清單

- [ ] 票 state 檔存在且 `overall_status: done`
- [ ] 四 REPORT 區塊齊全（B_REPORT / C_REPORT / D_REPORT / O_NOTES）
- [ ] 有明確的 VerificationCommands 與結果
- [ ] 相關 spec / code / tests 仍存在於 repo

---

## §3 從哪裡看：資料來源與閱讀順序

### 3.1 資料來源總覽

| 來源 | 路徑（相對戰車根） | 內容 | 閱讀順序 |
|------|-------------------|------|----------|
| **state** | `04_Workflows/tickets/<ticket_id>_state.md` | FRAME + STATE + 四 REPORT | **第 1** |
| **spec** | `docs/*-spec-v1.md` / `docs/*-guide-v1.md` | 人讀規格 | 第 2 |
| **code/tests** | FRAME.AllowedPaths 所列 | 實作與驗證 | 第 3 |
| **WORKFLOW_INDEX** | `04_Workflows/WORKFLOW_INDEX.md` | 工作流入口 | 第 4 |
| **WAVE_PROGRESS_DASHBOARD** | `docs/WAVE_PROGRESS_DASHBOARD.md` | Wave 完成度 | 第 5 |

### 3.2 推薦閱讀順序

```
Step 1: 讀 state 檔（FRAME → STATE → O_NOTES → B_REPORT → C_REPORT → D_REPORT）
    ↓
Step 2: 讀 spec 文件（docs_updates 所列，或 FRAME 相關 spec）
    ↓
Step 3: 讀 code / tests（B_REPORT.changed_files，對照 AC 檢查）
    ↓
Step 4: 跑 VerificationCommands（確認結果與 B_REPORT 一致）
    ↓
Step 5: 讀 WORKFLOW_INDEX / DASHBOARD（理解票在 Wave 中的位置）
    ↓
Step 6: 寫 Replay 筆記（見 §5）
```

### 3.3 State 檔閱讀指南

| 區塊 | 重點看什麼 | 檢查點 |
|------|-----------|--------|
| **FRAME** | Goal/Scope/NonScope/AllowedPaths/BlockedPaths/AC | 邊界是否清晰？AC 是否可驗收？ |
| **STATE** | `status_by_role` 時間線 | 是否經過 loop back？多久完成？ |
| **O_NOTES** | Run Log 時間戳 | 各角色實際執行日期、是否有重跑 |
| **B_REPORT** | changed_files / verification | 是否與 AC 對齊？驗證證據是否充分？ |
| **C_REPORT** | conclusion / checks_summary / suggestions | gaps 是什麼？風險評估？ |
| **D_REPORT** | docs_updates / progress_entry | Scribe 如何收口？Progress 條目是否落地？ |

---

## §4 用一張具體票做 Replay（W4-T2 範例）

### 4.1 選票：W4-T2 · Routing Eval Runner

**選擇理由**：
- `accepted_with_gaps`（理解 gaps 處理）
- 有清晰的 B_REPORT / C_REPORT / D_REPORT
- 涉及 Runner / CLI / unittest 多種交付物
- 有 followup_suggestions（理解後續票規劃）

### 4.2 Step 1：讀 State 檔

**路徑**：`04_Workflows/tickets/W4-T2-routing-eval-runner_state.md`

**閱讀重點**：

```markdown
## FRAME
- Goal: 新增本地 routing eval runner，讀 `routing_eval_cases_v1.yaml`，...（v1 不做 LLM 判分、不讀 Langfuse、不接 CI）
- Scope: 新增 `scripts/run_routing_eval.py` ...
- NonScope: **不**改既有 router / skills / 主鏈 ...
- AC-1: `--dry-run` 對 YAML 全部 case 產生結果且不崩潰
- AC-2: Tabular `planned_tools` ⊇ `expected_tool_ids` ...
...

## STATE
- overall_status: done
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

## B_REPORT
- changed_files:
  - `scripts/run_routing_eval.py`
  - `docs/routing-eval-runner-v1.md`
  - `tests/test_routing_eval_runner.py`
- verification:
  - `python -m unittest tests.test_routing_eval_runner -v` → **12/12 OK**
  - `python scripts/run_routing_eval.py --dry-run --format json` → **4/4 aligned**, exit 0

## C_REPORT
- conclusion: **accepted_with_gaps**
- checks_summary:
  - **AC-1** ✅：... 4/4 aligned
  - **AC-2** ✅：...
  - ...
- suggestions:
  - **G1**：dry-run 尚未接入 GitHub Actions／CI；建議 **W4-T4** 掛 `--dry-run` ...
  - **G2**：`--execute` 僅 `tabular_mainline_regression` ...

## D_REPORT
- progress_entry: |
    **W4-T2 · Routing Eval Runner**（2026-06-10）— Reviewer **`accepted_with_gaps`**；
    交付 `scripts/run_routing_eval.py`、`docs/routing-eval-runner-v1.md`、...
- followup_suggestions:
  - **W4-T4**：CI 接入 ...
```

**檢查點**：
- ✅ Goal 清晰，NonScope 明確（不做 LLM judge、不接 CI）
- ✅ AC-1/AC-2 可驗收（dry-run 結果、tools 對齊）
- ✅ verification 數字清晰（12/12, 4/4）
- ⚠️ `accepted_with_gaps` — G1/G2 為非阻塞遺漏，已規劃後續票 W4-T4

### 4.3 Step 2：讀 Spec

**路徑**：`docs/routing-eval-runner-v1.md`（由 D_REPORT.docs_updates 得知）

**閱讀重點**：
- CLI 介面定義（`--dry-run`, `--case-id`, `--execute`, `--format`）
- Case 類型（Tabular vs Gov）
- 輸出 JSON schema
- 與 Wave 1–4 的關係

### 4.4 Step 3：讀 Code / Tests

**檔案**：
- `scripts/run_routing_eval.py`（B_REPORT.changed_files）
- `tests/test_routing_eval_runner.py`

**閱讀重點**：
- 對照 AC-1：是否實作 `--dry-run`？是否消費 `routing_eval_cases_v1.yaml`？
- 對照 AC-2：Tabular case 是否呼叫 `plan_tabular_route`（W4-T1 glue）？
- 對照 BlockedPaths：是否誤改 `scripts/run_case_e2e_validation.py`？
- tests：是否覆蓋 dry-run 全案、錯誤 case、execute mock？

### 4.5 Step 4：跑 VerificationCommands

```bash
# 驗證 AC-4（unittest）
python -m unittest tests.test_routing_eval_runner -v
# 預期：12/12 OK

# 驗證 AC-1（dry-run CLI）
python scripts/run_routing_eval.py --dry-run --format json
# 預期：4/4 aligned, exit 0

# 驗證 AC-5（主鏈守護）
python scripts/run_mvp_mainline_regression.py -v
# 預期：6/6 OK, exit 0
```

**檢查點**：
- ✅ 當前執行結果與 B_REPORT 一致
- ✅ 無回歸（mainline 仍 6/6）

### 4.6 Step 5：讀 Index / Dashboard

**WORKFLOW_INDEX.md §1.5**：
```markdown
- Routing Eval Guide & Cases（Wave 2 · ...）：
  - `docs/routing-eval-guide-v1.md` — 人讀指南...
- Routing Eval Runner（Wave 4 · W4-T2 · dry-run）：
  - `docs/routing-eval-runner-v1.md` — 消費 `routing_eval_cases_v1.yaml` ...
```

**WAVE_PROGRESS_DASHBOARD.md**：
```markdown
## Wave 4 — Routing / Tool Layer Integration · **4/4 done**
- **W4-T2-routing-eval-runner** | done · Reviewer `accepted_with_gaps` | ...
```

**檢查點**：
- ✅ 票已列於 Wave 4 區塊
- ✅ 狀態為 done，`accepted_with_gaps` 結論一致

### 4.7 Step 6：寫 Replay 筆記（見 §5）

---

## §5 如何做事後分析（Postmortem / Audit）

### 5.1 輕量 Replay（10 分鐘）

**適用**：快速了解一張票的交付內容

| 步驟 | 動作 | 輸出 |
|------|------|------|
| 1 | 讀 state FRAME + B_REPORT | 理解目標與交付物 |
| 2 | 讀 C_REPORT conclusion + suggestions | 理解 gaps |
| 3 | 檢查 verification 數字 | 確認驗收完成 |

### 5.2 標準 Replay（30 分鐘）

**適用**：深入理解協作過程與設計決策

| 步驟 | 動作 | 輸出 |
|------|------|------|
| 1 | 讀 state 全檔（FRAME → O_NOTES） | 時間線與角色切換 |
| 2 | 讀 spec + changed_files | 設計與實作 |
| 3 | 跑 VerificationCommands | 確認當前仍通過 |
| 4 | 讀 WORKFLOW_INDEX / DASHBOARD | Wave 上下文 |
| 5 | 填寫 Replay 筆記（見 5.4） | 結構化總結 |

### 5.3 深度 Audit（1–2 小時）

**適用**：Wave 結束後正式回顧、或問題排查

| 步驟 | 動作 | 輸出 |
|------|------|------|
| 1 | 標準 Replay 全步驟 | 基礎理解 |
| 2 | 比對 FRAME.Scope vs B_REPORT.changed_files | 檢查 scope creep |
| 3 | 比對 AC vs C_REPORT.checks_summary | 檢查驗收完整度 |
| 4 | 追蹤 suggestions / followup_suggestions | 檢查 gaps 是否後續解決 |
| 5 | 檢查 Progress 末尾條目 | 檢查戰報落地 |
| 6 | 檢查後續票（如 W4-T4）是否引用本票 gaps | 檢查規劃執行度 |

### 5.4 Replay 筆記模板

```markdown
# Replay: <ticket_id>

## 1. 票概覽
- **票號**: 
- **Wave**: 
- **結論**: 
- **gaps**: 

## 2. 交付物
| 檔案 | 類型 | 說明 |
|------|------|------|
| | | |

## 3. 驗證結果
- [ ] VerificationCommands 當前執行通過
- [ ] 數字與 B_REPORT 一致

## 4. 協作觀察
- **流程**: 一次通過 / loop back _次
- **關鍵決策**: 
- **風險評估**: 

## 5. 後續追蹤
- **suggestions 解決狀態**: 
- **followup_suggestions 執行狀態**: 

## 6. 學習點
- **成功模式**: 
- **陷阱避免**: 
```

---

## §6 常見 Replay 情境

### 6.1 「我想參考歷史票做類似功能」

1. 找同類型票（如都需要 runner）：W4-T2
2. 讀 FRAME.Scope / NonScope（理解邊界如何劃分）
3. 讀 B_REPORT.changed_files（理解交付物結構）
4. 讀 C_REPORT.suggestions（理解常見 gaps）
5. 複製 template，調整 FRAME 為新需求

### 6.2 「這張票說 done 但好像有遺漏」

1. 讀 C_REPORT.suggestions（確認 gaps 是否已知）
2. 讀 D_REPORT.followup_suggestions（確認是否規劃後續票）
3. 檢查 Progress 末尾條目（確認戰報落地）
4. 檢查後續 Wave 票（確認 gaps 是否已解）

### 6.3 「我想了解 Wave 4 整體如何協作」

1. 讀 WAVE_PROGRESS_DASHBOARD.md Wave 4 區塊
2. 依序 Replay W4-T1 / W4-T2 / W4-T3-A / W4-T4
3. 關注 Dependencies（W4-T2 依賴 W4-T1 glue）
4. 關注 suggestions 的傳遞（W4-T2 G1 → W4-T4 CI 接入）

---

## §7 參考索引

| 文件 | 用途 |
|------|------|
| `04_Workflows/tickets/README.md` | 票機制總覽 |
| `docs/multi-agent-collaboration-spec-v1.md` | 角色規格 |
| `docs/multi-agent-handoff-runbook-v1.md` | Handoff 流程 |
| `04_Workflows/tickets/_templates/ticket_state.template.md` | State 檔結構 |
| `docs/WAVE_PROGRESS_DASHBOARD.md` | Wave 完成度 |
| `04_Workflows/WORKFLOW_INDEX.md` | 工作流入口 |

---

*本檔為 W5-T0 · Multi-Agent Collaboration Docs 交付物 · 2026-06-10*
