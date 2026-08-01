# W5-A-RUNTIME-01-DRYRUN Brief — Wave 5-A 第一條 runtime 線（read-only dry-run CLI）

> **源頭**：W5-A 軸計畫啟動，但要求第一條 runtime 線必須是 read-only dry-run，不寫任何 CI/pipeline state。  
> **風險**：極低 — 只讀既不寫既有檔案，僅新增 CLI + 新報表目錄，不影響任何 CI 行為。  
> **目標**：在 repo 中新增一個 dry-run CLI，讀取現有 eval-shadow-nightly / gate verdict artefact，產出 per-record 比較報表 + 摘要。  
> **關聯方案**：`W5-A-RUNTIME-01-DRYRUN_plan.md`（完整設計稿，含治理規則細節與後續擴展）。  

---

## 任務說明

這張票是 Wave 5-A 的第一條 runtime 線，但它的所有工作都必須是 **read-only** — 不修改任何現有檔案內容，不寫入任何 CI / pipeline 決策狀態。實作內容是新增一個可執行的 dry-run CLI（Python module + entrypoint），讀取現有 eval-shadow-nightly 產出的 artefact（shadow_eval_results、shadow_ibridge_records、gate verdict、eval_export JSONL 等），用一套簡化治理規則推算每條記錄的「理想 verdict bucket」，與實際 gate verdict 對照，產出新 JSONL per-record 報表 + markdown 摘要報表。所有輸出寫入新建立的 `observability/dryrun/` 目錄。完成後團隊可以手動執行這個 CLI 來驗證治理邏輯在真實資料下的行為，再決定是否在 RUNTIME-02 開始寫入 CI。

---

## 允許操作

- 在 `tools/dryrun/` 或等價位置新增 Python module（package + entrypoint），實現 dry-run CLI
- 在 `observability/dryrun/` 或 `artifacts/dryrun/` 下新增 dry-run 報表目錄（含 per-record JSONL + summary markdown）
- 在 `observability/dryrun/README.md` 或 `docs/` 下新增 dry-run 線的說明文檔（用途、限制、免責聲明、後續擴展）
- 在 `tests/` 下新增 dry-run CLI 的基本測試（至少 unit test 確認 CLI 產出預期格式）
- 用 `find` / `ls` 確認實際 artefact 路徑後，使用 CLI 參數化指定輸入路徑

## 禁止操作

- **嚴禁**修改任何 `.github/workflows/` 下的 CI workflow 檔案
- **嚴禁**修改任何現有程式碼邏輯（eval_exporter、ibridge_exporter、eval_stats、gate_checklist 等）
- **嚴禁**修改或刪除任何既有 JSONL / md / yml 檔案內容（只讀取）
- **嚴禁**修改任何測試斷言或 fixture 資料
- **嚴禁**寫入 prod-equivalent 狀態（gate verdict、PR status、CI check、pipeline trigger）
- **嚴禁**依賴外部 API 或 production 資料庫（只讀本地 artefact）

---

## 實作步驟 Checklist

1. **路徑盤點**：用 `find` 定位現有 shadow_eval_results、shadow_ibridge_records、eval_export JSONL、gate verdict 等 artefact 的實際路徑與格式
2. **設計 CLI 介面**：定義 `--input-dir` / `--output-dir` / `--min-score` / `--verbose` 等 CLI 參數，支援指定多個輸入來源
3. **實作治理規則引擎**：按 plan.md §4.1 的五條規則（gate_ok_score_high / gate_ok_score_low / gate_fail_deny / gate_fail_needs_review / edge_unknown）計算每條記錄的 `ideal_verdict`
4. **實作輸出模組**：產出 per-record JSONL（task_id、actual_verdict、ideal_verdict、verdict_match、dryrun_rule、metrics snapshot） + markdown 摘要（統計、差異清單、免責聲明）
5. **實作 CLI entrypoint**：讓 CLI 可被 `python -m tools.dryrun` 或直接執行
6. **新增測試**：至少一組 unit test（可用 mock 輸入或 fixture 級資料）確認 CLI 在黑箱模式下產出預期格式
7. **本機乾跑驗證**：用真實 artefact 跑一次 dry-run，確認報表產出且格式正確；`git diff --stat` 確認只新增了授權檔案
8. **文檔說明**：在 `observability/dryrun/README.md` 中說明 CLI 用法、輸入/輸出格式、免責條款、後續擴展

---

## 驗收條件

- **AC1**：存在可被 `python -m tools.dryrun <input_artefact_path>` 呼叫的 dry-run CLI，在本地成功讀取現有 artefact 並產出報表
- **AC2**：per-record JSONL 報表中每條記錄至少包含 `task_id`、`actual_verdict`、`ideal_verdict`、`verdict_match`、`dryrun_rule` 欄位；摘要 markdown 至少包含總記錄數、match 比例、差異清單
- **AC3**：簡化治理規則已實作（至少覆蓋 gate_ok_score_high、gate_ok_score_low、gate_fail_deny、gate_fail_needs_review、edge_unknown 五種場景）
- **AC4**：不修改任何既有程式碼檔案、CI workflow、既有 artefact、測試斷言；`git diff --stat` 確認僅新增檔案
- **AC5**：新增的 dry-run CLI 有至少一組 unit test 通過（測試可用 mock 輸入，不依賴真實 artefact）
- **AC6**：每份 dry-run 報表頭部或 CLI 輸出首行有清晰免責聲明（⚠ DRY-RUN — 不影響任何 CI/pipeline 決策）

---

## 回報格式框架

```markdown
## Execution Report — W5-A-RUNTIME-01-DRYRUN

### 新增/修改檔案清單
- tools/dryrun/__init__.py（CLI module）
- tools/dryrun/core.py（治理規則引擎 + 輸入解析）
- tools/dryrun/output.py（報表輸出模組）
- tools/dryrun/__main__.py（entrypoint）
- observability/dryrun/README.md（文檔說明）
- tests/test_dryrun_basic.py（單元測試）
- observability/dryrun/<timestamp>_per_record.jsonl（乾跑輸出 — 如已執行）
- observability/dryrun/<timestamp>_summary.md（乾跑輸出 — 如已執行）

### 乾跑結果摘要
python -m tools.dryrun --input-dir artifacts/eval/ --output-dir observability/dryrun/
<黏貼 CLI stdout，包含記錄總數 / match 率 / 差異統計 / 免責聲明文字>

### 報表示例（3–5 條記錄）
| task_id | actual_verdict | ideal_verdict | match | dryrun_rule |
|---------|---------------|--------------|-------|-------------|
| t-xxx   | allow         | allow         | ✅    | gate_ok_score_high |
| t-yyy   | allow         | warn          | ❌    | gate_ok_score_low  |
| t-zzz   | fail          | deny          | ✅    | gate_fail_deny     |

### 測試結果
python -m unittest tests.test_dryrun_basic
<黏貼 OK 輸出>

### 自檢勾選
- [AC1] CLI 可呼叫且產出報表：<OK/FAIL>
- [AC2] 報表包含 required 欄位：<OK/FAIL>
- [AC3] 五種治理規則已實作：<OK/FAIL>
- [AC4] 僅新增檔案（git diff --stat）：<OK/FAIL>
- [AC5] 測試通過：<OK/FAIL>
- [AC6] 免責聲明清楚：<OK/FAIL>

### 已知限制
- 治理規則為近似推導，不完整對應 G10 rulebook（具體偏離見 plan.md §4.2）
- 目前僅覆蓋 <實際覆蓋的 artefact 列表>，未涵蓋所有 artefact 類型
- 尚未接到任何 CI / pipeline 整合（本票為純 read-only dry-run）
```
