# W5-A-RUNTIME-03-ENF-PREVIEW Brief — 給 Cursor 的 RUNTIME-03 Phase A 實作任務卡（Enforcement Preview step）

> **源頭**：W5-A-RUNTIME-03-LIMITED-DENY_plan.md（完整設計方案，含 Enforceability Ladder §2、Rollout 策略 §3）  \
> **前置政策分析**：W5-A-RUNTIME-03-POLICY-MINING-01.md（從 dry-run 報表挖掘 ENF-RULE 候選）  \
> **風險**：低 — Phase A 為純預覽（`continue-on-error: true` + `exit 0`），不改 gate verdict / pipeline 結果。  \
> **目標**：在現有 `eval-shadow-nightly` job 中新增一個「Enforcement Preview」step，基於 ENF-RULE-1（L2 候選）計算 `would_block` / `would_warn`，以 `[GOV-ENF-PREVIEW]` 前綴印到 CI log，僅觀察不 fail。  \
> **前置依賴**：RUNTIME-02 logging-only step（`[DRYRUN-LOG]`）已在 eval-shadow-nightly 中正常運作；dry-run CLI 可正常讀取 artefact。  \
> **關聯方案**：`W5-A-RUNTIME-03-LIMITED-DENY_plan.md`（§3.1 Phase A）、`W5-A-RUNTIME-03-POLICY-MINING-01.md`（§3.1 C-01 強 L2 候選規則）。

---

## 任務說明

這張票是 RUNTIME-03 的第一個實作步驟（Phase A：Enforcement Preview）。它站在 RUNTIME-01（乾跑 CLI）和 RUNTIME-02（logging-only step）之上，但加入一個新的視角：**如果這些規則要開始擋 pipeline，會擋到誰？**。實作內容是：在 `eval-shadow-nightly` job 中新增一個名為 "Enforcement Preview" 的 step，基於 POLICY-MINING 報告識別的 ENF-RULE 候選（L2 層級），計算 `would_block_count` / `would_warn_count`，以獨立的 `[GOV-ENF-PREVIEW]` 前綴印到 CI log，但**永遠 exit 0 且 `continue-on-error: true`**，完全不改變 gate verdict 或 pipeline 結果。這只是預覽階段，團隊會觀察 N 次 nightly 後再決定是否進入 Phase B（實際 blocking）。既有 RUNTIME-02 的 `[DRYRUN-LOG]` step 不受影響，繼續照跑。

---

## 允許操作

- 在 `.github/workflows/eval-gate-ci.yml` 的 `eval-shadow-nightly` job 中新增一個名為 "Enforcement Preview"（或 "gov-enf-preview"）的 step / job，設 `continue-on-error: true`。
- 新增一個最小 wrapper（如 `tools/enf_preview_wrapper.py`），功能為：
  - 讀取既有 dry-run artefact（per-record JSONL）或直接調用 dry-run CLI 產生最新資料。
  - 對照 ENF-RULE 候選（見下方 ENF-RULE-1），計算 `would_block_count`（L2 候選觸發數）和 `would_warn_count`（L1 觀察數）。
  - 將結果以 `[GOV-ENF-PREVIEW]` 前綴印到 stdout。
  - 任何異常情況（artefact 不存在、CLI crash）印出 `[GOV-ENF-PREVIEW] [WARN]` 後 `exit 0`。
- 使用 `[GOV-ENF-PREVIEW]` 作為唯一的 log 前綴（與 `[DRYRUN-LOG]` 明確區分，不可混用）。
- 可選：在 wrapper 中加入 `--verbose` 模式，印出每條 would-block 記錄的 task_id 與觸發原因（但預設為 summary-only）。
- 新增簡短的文檔說明（更新 `observability/dryrun/README.md` 或新增 `observability/enf-preview/README.md`），說明 preview step 的用途、log 格式、與 Phase B 的關係。

## 禁止操作

- **嚴禁**讓 preview step 以任何原因 `exit 1` — 即使 ENF rules 標記了 100 條 would-block 記錄，step 也必須 `exit 0`。
- **嚴禁**以 preview 結果改變 gate verdict、PR status、pipeline 成敗判定、或任何 CI check 狀態。
- **嚴禁**修改或刪除既有 RUNTIME-02 的 logging-only step、其 `[DRYRUN-LOG]` 格式、或 `tools/dryrun_ci_wrapper.py`。
- **嚴禁**修改 `tools/dryrun/*` 的核心規則引擎或 per-record JSONL 輸出格式。
- **嚴禁**將任何 would-block / would-warn 資料寫入外部資料庫、CI check API、或 production dashboard。
- **嚴禁**在 Phase A 的 wrapper 中預先寫入 Phase B 的行為邏輯（如 `if would_block_count > 0: exit 1`）即使以註解形式存在。

---

## ENF-RULE 候選（Phase A 應實作的規則）

以下規則來自 POLICY-MINING-01 的分析結果。Phase A 應將它們實作為 enforcement preview 的計算邏輯。注意：這些是**候選**，不是已批准的 L2 enforcement。Preview step 僅計算和記錄，不實際 block。

### ENF-RULE-1（強 L2 候選 — 來自 C-01）

**條件**：
```
IF dryrun_rule == "gate_fail_deny"
   AND metrics.error_type IS NOT NULL
   AND tags CONTAINS 風險標記（如 "infra_risk"、"security:critical" 或等價）
THEN → would_block_count += 1
```

**來源**：POLICY-MINING-01 §3.1 C-01。範例記錄為 `t-infra`（timeout + infra_risk → deny）。這是目前唯一的強 L2 候選，條件為 binary（timeout + infra_risk tag → 明確的 infra failure），FP 率觀察為 0%。

**L2 判定門檻**：`score ≥ 0.7`（或等價的 `trace_completeness_score` 閾值，可在 wrapper 中設為常量）。

### ENF-RULE-2（L1 觀察 — 來自 C-03）

**條件**：
```
IF dryrun_rule == "gate_fail_needs_review"
   AND tags CONTAINS "high_retry"
   AND metrics.retry_count >= 2
THEN → would_warn_count += 1
```

**來源**：POLICY-MINING-01 §3.1 C-03。範例記錄為 `shadow-retry` 與 `t-retry`。這屬於 L1（Advisory），不進 blocking 計數，僅為提供總覽視圖。

### 通用規則機制

- 所有不匹配 ENF-RULE-1 或 ENF-RULE-2 的記錄自動歸入 `would_noop`（即不受 enforcement 影響）。
- `edge_unknown` 的記錄（若出現）也歸入 `would_noop`，確保 preview step 不因資料不全而誤判。
- 規則以 Python 常數定義在 wrapper 的頂層，註解說明來源與邏輯。
- 規則表達式應該是 readable if/elif/else 鏈，不是 regex 或動態載入（保持透明可審計）。

### 未來擴展

目前的 Rule-1 與 Rule-2 是基於現有資料的最小集。Phase A 運作後，若新的 L2 候選從後續 POLICY-SELECTION 票產出，可直接擴展 wrapper 中的規則列表（新增一個 `elif` 分支即可）。

---

## 實作步驟 Checklist

1. **路徑與狀態確認**：在 repo 中定位 `eval-shadow-nightly` job 與其 RUNTIME-02 logging step，確認 dry-run CLI 在 CI 環境中可呼叫、artefact 路徑可讀、既有 `[DRYRUN-LOG]` 正常輸出。

2. **設計 wrapper CLI**：新增 `tools/enf_preview_wrapper.py`（或等價路徑），支援以下 CLI 參數：
   - `--input`：dry-run per-record JSONL 路徑（或 `--input-dir` 若需從 artefact 目錄掃描）
   - `--output`：可選的 artefact 輸出路徑（若需要寫入 JSON summary）
   - `--min-score`：L2 判定的最低 score 閾值（預設 0.7 或與 RUNTIME-01 的 `min-score` 一致）
   - `--verbose`：可選，印出每條 would-block 記錄的 task_id

3. **實作規則邏輯**：在 wrapper 中實作 ENF-RULE-1 和 ENF-RULE-2 的判定邏輯（見上方 §ENF-RULE）。規則應為可讀的 if/elif 鏈，底部有 else → would_noop 的 fallthrough。

4. **CI step 插入**：在 `eval-shadow-nightly` job 中新增一個 step：
   - 名稱："Enforcement Preview (Phase A)"
   - 位置：接在既有 logging-only step（`[DRYRUN-LOG]`）**之後**。
   - 條件：`continue-on-error: true`
   - 腳本：`python -m tools.enf_preview_wrapper --input <dryrun_per_record_path>`
   - **不**修改既有 step 的 `[DRYRUN-LOG]` 輸出。

5. **Log 格式驗證**：確保 step 輸出符合以下格式：
   ```
   [GOV-ENF-PREVIEW] ⚠ PREVIEW — 非實際 enforcement，不影響 pipeline 結果
   [GOV-ENF-PREVIEW] event=summary total=847 would_block=3 would_warn=12 would_noop=832
   [GOV-ENF-PREVIEW] event=detail rule=ENF-RULE-1 would_block=3 min_score=0.7
   [GOV-ENF-PREVIEW] event=detail rule=ENF-RULE-2 would_warn=12
   [GOV-ENF-PREVIEW] event=complete status=ok exit_policy=preview_only
   ```
   （`event=preview` 行為在 RUNTIME-03 plan §3.1 中定義為 `[GOV-ENF-PREVIEW]`。上述 key=value 格式為建議，可微調但須保留前綴與關鍵欄位。）

6. **異常處理驗證**：手動觸發一次（或提供等價模擬），確認在下列情境下 step `exit 0` 且 pipeline 不變紅：
   - 正常執行（artefact 存在、規則正常跑）
   - artefact 不存在（印 `[GOV-ENF-PREVIEW] [WARN] event=skip reason=input_not_found` 後 exit 0）
   - wrapper 內 Python exception（印 `[GOV-ENF-PREVIEW] [WARN] event=error` 後 exit 0）

7. **git diff 自檢**：確認只新增了 `tools/enf_preview_wrapper.py`、修改了 `.github/workflows/eval-gate-ci.yml`（僅新增 step）、更新了文檔。未修改 `tools/dryrun/*`、`tools/dryrun_ci_wrapper.py`、gate 邏輯或其他既有檔案。

8. **文檔**：在 `observability/dryrun/README.md` 或新建 `observability/enf-preview/README.md` 中說明 preview step 的角色、log 格式、ENF-RULE 候選清單、與 Phase B 的關係。強調這只是 Phase A 預覽。

---

## 驗收條件（AC-PREV 系列）

- **AC-PREV-1**：`eval-shadow-nightly` job 中存在一個名為 "Enforcement Preview"（或 "gov-enf-preview"）的新 step，且設定了 `continue-on-error: true`。

- **AC-PREV-2**：該 step 正常運行時輸出以 `[GOV-ENF-PREVIEW]` 開頭的 log 行，至少包含 `event=summary` 行（含 `total`、`would_block`、`would_warn`、`would_noop` 四個欄位）和 `event=complete` 行（含 `status`、`exit_policy`）。

- **AC-PREV-3**：無論 preview step 的計算結果如何（would_block 為 0 或 >0），整體 workflow 的 gate verdict / exit code 不變，pipeline 結果不受影響。

- **AC-PREV-4**：既有 RUNTIME-02 的 `[DRYRUN-LOG]` logging step 保持不變，仍正常執行並輸出原有格式。

- **AC-PREV-5**：在任何異常情況下（artefact 不存在、wrapper crash），preview step 印出 `[GOV-ENF-PREVIEW] [WARN]` 後 `exit 0`，不破壞 pipeline。

- **AC-PREV-6**：未修改 `tools/dryrun/*`、`tools/dryrun_ci_wrapper.py`、或任何 gate 邏輯檔案。`git diff --stat` 確認僅新增/修改了 wrapper、CI YAML、文檔。

- **AC-PREV-7**：ENF-RULE-1（L2 候選）和 ENF-RULE-2（L1 觀察）已在 wrapper 中以可讀的 if/elif/else 鏈實作，頂層有註解說明來源。無隱藏的 exit 1 邏輯。

---

## 回報格式框架

```markdown
## Execution Report — W5-A-RUNTIME-03-ENF-PREVIEW

### 目標 CI workflow 與 preview step
- Workflow：<.github/workflows/ 路徑>
- Job：eval-shadow-nightly
- 新增 step 名稱：<step 名稱>
- continue-on-error：<確認>

### 修改/新增檔案清單
- .github/workflows/<目標>.yml（新增 Enforcement Preview step）
- tools/enf_preview_wrapper.py（wrapper 實作）
- observability/enf-preview/README.md（可選文檔）

### CI 執行摘要（[GOV-ENF-PREVIEW] 範例）
<黏貼 CI log 中的 2–3 行，例如：>
[GOV-ENF-PREVIEW] ⚠ PREVIEW — 非實際 enforcement，不影響 pipeline 結果
[GOV-ENF-PREVIEW] event=summary total=847 would_block=3 would_warn=12 would_noop=832
[GOV-ENF-PREVIEW] event=complete status=ok exit_policy=preview_only

### AC-PREV 自檢
- [AC-PREV-1] step 存在 + continue-on-error：<OK/FAIL>
- [AC-PREV-2] [GOV-ENF-PREVIEW] log 行含必要欄位：<OK/FAIL>
- [AC-PREV-3] pipeline 結果不受影響：<OK/FAIL>
- [AC-PREV-4] 既有 [DRYRUN-LOG] 不變：<OK/FAIL>
- [AC-PREV-5] 異常處理 exit 0：<OK/FAIL>
- [AC-PREV-6] 未改 dryrun/* / gate 邏輯（git diff --stat）：<OK/FAIL>
- [AC-PREV-7] ENF-RULE-1/2 已實作且可讀：<OK/FAIL>

### 已知限制 / 未來建議
- 目前僅掛在 nightly workflow，尚未接入 PR workflow
- 僅實作了 2 條 ENF-RULE（ENF-RULE-1 L2 候選 + ENF-RULE-2 L1 觀察）；新規則待後續 POLICY-SELECTION 票擴展
- Phase B（實際 blocking）不在本票範圍內
```
