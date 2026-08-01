# W5-A-RUNTIME-02-LOGGING-FIRST Brief — 給 Cursor 的 RUNTIME-02 實作任務卡（logging-only CI step）

> **源頭**：W5-A-RUNTIME-02-LOGGING-FIRST_plan.md（完整設計方案）  \
> **風險**：低 — 所有變更都是「加 log、不加權」，step 設 `continue-on-error: true`，不影響 pipeline 結果。  \
> **目標**：在一條現有的 nightly CI workflow 中新增一個 logging-only step，調用既有 dry-run CLI，把治理統計摘要印到 CI log（`[DRYRUN-LOG]` 前綴），並可選附加一個 CI artefact。  \
> **前置依賴**：W5-A-RUNTIME-01-DRYRUN 已落地（dry-run CLI + 報表格式 + README），AC-DRY-1~6 全部通過。  \
> **關聯方案**：`W5-A-RUNTIME-02-LOGGING-FIRST_plan.md`（完整設計稿，含邊界 L1–L6、風險分析、與 PLAYBOOK 的對應）。

---

## 任務說明

這張票是 W5-A-RUNTIME-02-LOGGING-FIRST 的實作票。它站在 W5-A-RUNTIME-01-DRYRUN（現有 read-only dry-run CLI）的肩膀上，把治理訊號從「本地檔案」推進到「CI log + 可選 artefact」。實作內容是：在一條既有的 nightly CI workflow 中新增一個 logging step，調用既有 dry-run CLI 讀取該次 CI run 的 eval/shadow/gate artefact，將治理統計摘要（總記錄數、match_ratio、unknown 佔比、mismatch 數量）以 `[DRYRUN-LOG]` 前綴印到 CI log，並可選上傳 summary JSON 為附加 artefact。**所有變更都是「加 log、不加權」** — step 永遠設 `continue-on-error: true`，不改變 gate verdict、exit code、pipeline 結果、或任何既有 artefact 內容。

---

## 允許操作

- 在 `.github/workflows/` 中找到與 eval/shadow/gate 直接相關的 nightly CI workflow（抽象名稱為 `k2-shadow-nightly-CI`，請用 `find` / `ls` 確認實際檔名與 job 結構），在該 workflow 的適當位置新增一個 logging step / job。
- 在該 CI step 中設 `continue-on-error: true`（或 GitHub Actions 的等價機制），確保 step 失敗不影響 pipeline 結果。
- 在 repo 中新增少量輔助程式（例如 `tools/dryrun_ci_wrapper.py` 或等價檔案），用來在 CI 環境中調用 dry-run CLI、收集 stdout、格式化摘要與異常處理。
- 在 CI log 中以 `[DRYRUN-LOG]` 前綴印出簡短統計（總數、match_ratio、unknown、mismatch、ideal_verdict 各 bucket 分佈），首行印出免責文字。
- 可選：新增一個 CI artefact（如 `dryrun_summary.json` 或等價），上傳到 CI 內建的 artifact storage（如 `actions/upload-artifact`），放至新路徑（如 `observability/dryrun-ci/`）下。
- 新增簡短的文檔說明（如 `observability/dryrun/README.md` 的追加段落，或新增 `observability/dryrun-ci/README.md`），說明 logging step 的用途、免責、與 RUNTIME-01 的關係。

## 禁止操作

- **嚴禁**修改現有 gate verdict 邏輯或 exit code（包括 eval_gate、eval_ci_check、gate_checklist 等任何既有 gate 相關檔案）。
- **嚴禁**把 dry-run logging step 的 exit code 連接到 workflow 成功/失敗條件，即使 dry-run 報表顯示大量 mismatch。
- **嚴禁**修改任何既有 JSONL / md / yml artefact 檔案內容（只讀取，不覆寫）。
- **嚴禁**修改任何既有測試、測試斷言、或 fixture 資料。
- **嚴禁**修改 RUNTIME-01 的 dry-run CLI 本身（`tools/dryrun/**`）、其報表格式、或 README 原文。
- **嚴禁**將任何 summary / verdict 寫入外部資料庫、CI check API、或 production dashboard。

---

## 實作步驟 Checklist

1. **路徑盤點**：在 repo 中用 `find` / `ls` 定位現有與 eval/shadow/gate 對應的 nightly CI workflow（`.github/workflows/**`），選定一條目標 workflow，並在回報中簡述選擇理由（建議選擇 nightly 而非 per-commit 的工作流，降低初期風險）。

2. **CI step 插入**：在目標 workflow 的適當位置（shadow_eval_results 產出之後、gate 步驟之前或之後均可，但不得 interfere 原有流程），新增一個 logging step，job 名稱為 `dryrun-logging`（或等價），step 名稱為 `Dry-run governance logging (observability only)`，設 `continue-on-error: true`。

3. **實作 wrapper（可選）**：若直接 `python -m tools.dryrun` 在 CI log 中不足以產出精簡摘要，可新增 `tools/dryrun_ci_wrapper.py`（或內聯 step 腳本），功能為：
   - 調用 dry-run CLI 讀取 CI 環境中的 artefact。
   - 從 CLI stdout 或從其產出的 summary 中，擷取總數、match_ratio、unknown、mismatch 等統計欄位。
   - 處理異常情況（artefact 不存在、CLI crash）：印出 `[DRYRUN-LOG] [WARN]` 後正常結束。

4. **CI log 輸出**：確保 logging step 的輸出符合以下格式：
   ```
   [DRYRUN-LOG] ⚠ DRY-RUN — 不影響任何 CI/pipeline 決策
   [DRYRUN-LOG] Total records: <N> | Match: <P>% | Unknown: <P>% | Mismatch: <N> (<P>%)
   [DRYRUN-LOG] Ideal breakdown: allow=<N> warn=<N> deny=<N> needs_review=<N> unknown=<N>
   [DRYRUN-LOG] ⚠ Differences found: <N> records where gate_verdict ≠ ideal_verdict
   ```
   每行前綴 `[DRYRUN-LOG]` 不可省略。首行固定為免責文字。

5. **（可選）CI artefact**：將 dry-run summary（JSON 格式）上傳為 CI artefact，放在 `observability/dryrun-ci/` 路徑下，檔名含 CI run ID（例如 `<run-id>_summary.json`），不覆蓋既有 artefact。

6. **驗證測試**：至少觸發一次 CI（或提供等價的本機模擬方法，例如用 repo 內 fixture 級資料模擬 CI 環境），確認：
   - logging step 在正常情況下印出預期格式的 log 行。
   - logging step 在異常情況下（artefact 不存在、CLI crash）印出 `[DRYRUN-LOG] [WARN]` 且不改 pipeline 結果。
   - `git diff --stat` 確認只新增或修改了允許的檔案。

7. **文檔**：在 `observability/dryrun/README.md` 或 `observability/dryrun-ci/README.md` 中補充 RUNTIME-02 logging step 的說明，包含用途、CI log 格式、免責文字、與 RUNTIME-01 的關係。

8. **自檢**：檢查既有檔案變更清單，確認無越線（未修改 gate 邏輯、未改既有 artefact、未改既有測試）。

---

## 驗收條件（AC-L 系列）

- **AC-L-1**：在選定的 nightly CI workflow 中存在一個明確的 logging step / job，名稱帶有 `dryrun` 或 `governance logging` 等可識別關鍵字，且設定了 `continue-on-error: true`（或等價機制）。

- **AC-L-2**：logging step 在正常運行時，CI log 中出現以 `[DRYRUN-LOG]` 開頭的摘要行，至少包含總記錄數、match_ratio、unknown 佔比、mismatch 數量四個欄位。

- **AC-L-3**：無論 logging step 成功或失敗（包含 artefact 不存在、CLI crash 等異常情況），整個 workflow 的 gate verdict / exit code 不變，pipeline 最終結果不因本 step 而改變。

- **AC-L-4**：新實作過程中未修改任何既有 artefact（JSONL / md / yml）、gate 邏輯程式碼、測試斷言、或 fixture 資料。`git diff --stat` 確認僅新增或修改了 CI workflow YAML、wrapper 腳本、文檔。

- **AC-L-5**：如有新增 CI artefact（如 `dryrun_summary.json`），其路徑與檔名清楚記錄在回報中，且不與既有 artefact 路徑衝突。

- **AC-L-6**：log 首行為明確的免責文字（如 `⚠ DRY-RUN — 不影響任何 CI/pipeline 決策`）；若有新增 artefact，其內容也包含相同免責。

- **AC-L-7**：異常情況下 logging step 印出 `[DRYRUN-LOG] [WARN]` 訊息後正常結束（exit 0），不觸發告警或人工重跑。

---

## 回報格式框架

```markdown
## Execution Report — W5-A-RUNTIME-02-LOGGING-FIRST

### 目標 CI workflow 與 logging step
- 選擇的 workflow 檔案：<路徑 + 選擇理由>
- 新增的 job/step 名稱：<名稱>
- continue-on-error 設定：<確認>

### 修改/新增檔案清單
- .github/workflows/<目標>.yml（新增 logging step）
- tools/dryrun_ci_wrapper.py（可選 wrapper）
- observability/dryrun-ci/README.md（可選文檔）
- observability/dryrun-ci/<run-id>_summary.json（可選 artefact — 若已執行 CI）

### CI 執行摘要
<黏貼 CI run URL 或本地模擬命令與輸出>
<範例 log 行：>
[DRYRUN-LOG] ⚠ DRY-RUN — 不影響任何 CI/pipeline 決策
[DRYRUN-LOG] Total records: 847 | Match: 91.3% | Unknown: 1.2% | Mismatch: 63 (7.5%)

### Artefact 說明（若適用）
- 上傳的 artefact 檔案：<檔名>
- 內容欄位：<簡述 JSON 欄位>
- 路徑：<路徑>

### AC-L 自檢
- [AC-L-1] logging step 存在 + continue-on-error: <OK/FAIL>
- [AC-L-2] [DRYRUN-LOG] log 行包含必要欄位：<OK/FAIL>
- [AC-L-3] pipeline 結果不受影響：<OK/FAIL>
- [AC-L-4] 未改既有 gate/artefact/tests（git diff --stat）：<OK/FAIL>
- [AC-L-5] 新 artefact 路徑無衝突（若適用）：<OK/FAIL/N/A>
- [AC-L-6] 免責文字在 log 首行：<OK/FAIL>
- [AC-L-7] 異常情況下輸出 [WARN] 且 exit 0：<OK/FAIL>

### 已知限制 / 未來建議
- 目前只掛在 nightly workflow，尚未接 PR workflow
- 若發現規則 match_ratio 偏低，建議在 RUNTIME-03 之前做一次 rule tuning
- artefact 保留策略尚未定義（由後續 DOCSYNC 票處理）
```
