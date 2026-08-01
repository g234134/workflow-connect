# W5-D-SMOKE-FIXTURE-PROVENANCE — Smoke Fixture 溯源缺口 · 方案卡

> **票號**：W5-D-SMOKE-FIXTURE-PROVENANCE-PLAN-01（只讀方案卡）
> **源頭**：W5-D-FIXTURE-PROVENANCE closure 發現 smoke 類 fixture 可能存在相同的 line_index 偏移問題
> **範圍**：僅 smoke 類 eval/shadow fixture 的溯源資訊 cleanup 策略設計
> **不處理**：更改程式邏輯、重寫測試、批量改寫整組 fixture 結構
> **先決**：W5-D-FIXTURE-PROVENANCE 方案卡（完整調查 + 風險評估方法）— 本卡為其 smoke 衍生版

---

## (1) 背景摘要

**問題本質**：smoke 類 eval/shadow fixture 中 `source_ref.line_index` 可能沿用匯出檔自身行號，而非對應原始輸入檔案（ibridge / shadow_raw）中的行號。這與 W5-D-FIXTURE-PROVENANCE 在 `eval_export_sample.jsonl` 中發現的完全同一類問題，只是 fixture 類型不同。

**為什麼會有這個問題**：smoke eval fixture 通常是從 eval_export_sample 或近似 source 手動 copy + 調整而來。在 copy 過程中，line_index 從 ibridge 的原始行號變成了 copy 目的檔自己的行號（或根本沒有更新），導致 traceability 中斷。

---

## (2) 候選 smoke fixture 盤點

以下為推測路徑（基於專案命名慣例，非讀取真實 repo）：

| 候選對象 | 推測類型 | 推測問題 | 與 eval 版的關係 |
|---------|---------|---------|-----------------|
| `tests/fixtures/eval/smoke_eval_results.jsonl` | 主要 smoke eval fixture | line_index 可能是 export 輸出檔行號而非原始 ibridge 行號 | 與 `eval_export_sample.jsonl` 同時被 W5-D-FIXTURE-PROVENANCE 提及為「同問題」 |
| `artifacts/eval/smoke_eval_results.latest.jsonl` 或 `artifacts/eval/smoke_shadow_eval_results.latest.jsonl` | shadow 類 smoke artifact | line_index 可能偏移 + schema 轉換（像 shadow_eval_results.latest 一樣） | 對應 W5-D-FIXTURE-PROVENANCE 的 `shadow_eval_results.latest.jsonl` |
| `tests/fixtures/eval/smoke_<variant>.jsonl` 系列 | 小型 smoke 子 fixture | 可能同樣有 line_index 語義不清的問題 | 可能只參考主 fixture，不一定有獨立 source 對應 |
| `observability/smoke_eval_schema.md`（若存在）或 `observability/eval_export_schema.md` | schema 文檔 | 缺少針對 smoke fixture 的 line_index 語義說明 | 前次已在 eval_export_schema.md 補了通用說明 |

**範圍裁決**：建議將 scope 鎖定在最核心的兩組檔案：
- **主要 smoke fixture**（`tests/fixtures/eval/smoke_eval_results.jsonl` 或等價路徑）
- **shadow smoke artifact**（`artifacts/eval/smoke_eval_results.latest.jsonl` 或等價路徑）
- **schema 文檔**（`observability/eval_export_schema.md` 或 `smoke_eval_schema.md`）

不列入：小型 smoke 子 fixture（需要另外評估是否真的需要修正）、CI config 檔案、eval exporter 程式中對 smoke 的處理邏輯。

---

## (3) 預期問題類型（5–10 行說明）

1. **line_index 仍是「匯出檔行號」而非「原始輸入行號」** — 與 eval 版完全相同的問題型別。smoke fixture 中的 line_index 寫的是 fixture JSONL 自身 1-based 行號，而非 ibridge_records 或 shadow_raw 中對應記錄的行號。
2. **沒有清楚說明是哪一層的 source** — 讀者無法判斷這個 line_index 指向的是 ibridge_records（中間格式）、shadow_raw_records（shadow 原始）、還是只是 fixture 自身（視覺標記）。
3. **fixture 本身是手動示意，但讀起來像真實溯源** — 因為 smoke fixture 的結構與真實 exporter 輸出完全相同（schema_version、source_ref、metrics），line_index 的存在讓讀者以為它真的是從 exporter 執行產生的。但實際上是手動或半自動產生的。
4. **shadow smoke artifact 可能有 schema 轉換後的偏離** — 與 shadow_eval_results.latest.jsonl 類似的問題：shadow_raw 中有 `case_name`（而非 `task_id`）的記錄，經 ibridge_exporter 轉換後 `task_id` 被重新分配，導致即使 line_index 原始行號正確，也無法 1:1 追溯到 shadow_raw。
5. **smoke 特有風險**：smoke 測試通常比完整 eval 測試更輕量，可能完全沒有 line_index 相關的斷言。因此修正的風險接近於零，但也意味著如果 fixture 本身建立時就不嚴謹，修正後的本質仍然是「示意」。

---

## (4) 實作策略

### 建議選項：精確修正 + 文檔補充（選項 B + C 混用）

與 W5-D-FIXTURE-PROVENANCE-01 採用相同手法：

1. **比對確認**：對照 smoke fixture 與對應原始輸入檔案（ibridge_records / shadow_raw），確認哪幾條記錄的 line_index 需要調整。
   - 如果 smoke fixture 基於 ibridge_records，則 line_index 應指向 ibridge_records 的行號
   - 如果 smoke fixture 基於 shadow_raw，則 line_index 應指向 shadow_raw 的行號
2. **修正 line_index**：用安全的 JSON 編輯工具（python json.load/dump 或 jq）對少量記錄做 line_index 數值調整。
3. **可選修正 shadow smoke artifact**：如果 artifact 的 line_index 也偏移，做 minimal 對齊修正。修正後在文檔註明「因 schema 轉換僅到 ibridge 中間格式」。
4. **文檔補充**：在相關 schema/markdown 中強化 line_index 語義，特別說明 smoke fixture 的 line_index 是手動修正的（非 exporter runtime 產生的）。
5. **測試確認**：跑 smoke 相關測試（如 `test_smoke_eval` / `test_smoke_gate`），確保全部通過且輸出與修正前完全一致。

### 不考慮的選項

- **重新產生 fixture**（選項 D）：對 smoke fixture 來說太過重，且可能改變記錄順序 → 影響已有的 smoke 測試假設。
- **僅補文檔不改 fixture**（選項 C 純版）：讀者只看 fixture JSON 仍會被誤導，改善效果有限。
- **批量重寫**：與本票「小 cleanup」定位不合。

---

## (5) 風險評估

| # | 風險 | 影響 | 緩解方式 |
|---|------|------|---------|
| R1 | smoke fixture 的原始 source 不明確（不確定是 ibridge 還是 shadow_raw） | 無法精確修正 | 先讀 smoke 測試中的 fixture 引用，推斷原始 source；若仍不明確，在文檔註明「無法完全追溯」 |
| R2 | shadow smoke artifact 的 schema 轉換使 line_index 無法 1:1 對應 | 修正後仍只能到中間格式 | 與 eval 版同樣處理：在文檔註明「僅保證到 ibridge 中間格式」 |
| R3 | smoke 測試可能意外依賴 fixture 的 line_index（可能性低） | 修正後測試失敗 | 在實作步驟中明確要求跑完整測試套件確認 |
| R4 | 有多個 smoke fixture 導致 scope creep | 超出小 cleanup 範圍 | 在做法中明確只鎖定 1–2 個主要 smoke fixture |

**總體風險評級：低** — 與 W5-D-FIXTURE-PROVENANCE 同級。

---

## (6) 驗收要點

| # | 驗收條件 | 如何驗證 |
|---|---------|---------|
| A1 | 至少一條 smoke fixture 記錄可以精準追到對應原始輸入檔案的行號 | 比對修復後的 line_index 與 ibridge_records / shadow_raw 行號 |
| A2 | 所有相關 smoke 測試全部通過，且輸出與修正前一致 | 執行完整測試套件，diff 確認無意外變更 |
| A3 | schema/markdown 中對 smoke line_index 的語義有明確說明 | 讀 schema 檔案找到新增或強化的 paragraph |
| A4 | 修改僅限授權檔案（smoke fixture / shadow artifact / schema 文檔） | `git diff --stat` / 檔案 diff 確認 |
| A5 | 所有 JSON/JSONL 維持格式合法 | `python -m json.tool` 或 `jq .` 驗證語法 |

---

## (7) 與 W5-D-FIXTURE-PROVENANCE 的關係

| 維度 | W5-D-FIXTURE-PROVENANCE（已做） | W5-D-SMOKE-FIXTURE-PROVENANCE（本票） |
|------|--------------------------------|--------------------------------------|
| **對象** | `eval_export_sample.jsonl` + `shadow_eval_results.latest.jsonl` | `smoke_eval_results.jsonl` + shadow smoke artifact |
| **問題** | line_index = export file line number | 同左（line_index = smoke export file line number 或未更新） |
| **方法** | 精確修正 2 條 line_index + 補 schema 說明 | 同左模式，比例相當或更少（如果 smoke fixture 更小） |
| **文檔更新** | `eval_export_schema.md` §source_ref.line_index | `eval_export_schema.md` 或 `smoke_eval_schema.md`（如果獨立） |
| **難度** | 極低（改 2 個數字） | 同級（預期改 1–6 個數字） |
| **獨立性** | 已完成 | 可獨立進行，無阻塞 |

---

## 附錄 A — 預期檔案對照速查

| 檔案（推測路徑） | 角色 | 預期問題 | 建議處理方式 |
|-----------------|------|---------|------------|
| `tests/fixtures/eval/smoke_eval_results.jsonl` | 主要 smoke eval fixture | line_index 為匯出檔行號 | 精確修正 1–6 條 line_index |
| `artifacts/eval/smoke_eval_results.latest.jsonl` | shadow smoke eval artifact | line_index 偏移 + 可能 schema 轉換 | minimal 對齊修正，註明中間格式限制 |
| `observability/eval_export_schema.md`（§source_ref.line_index） | schema 文檔 | 缺少 smoke 特定說明 | 補充一小段 smoke 用例語義（可重用 eval 版表述） |
| `observability/smoke_eval_schema.md`（若存在） | 專屬 schema | 可能完全沒寫 line_index 語義 | 新增 line_index 語義與限制段落 |

> **註**：以上路徑為推測命名，實作時請用 `find` / `ls` 確認實際路徑。

## 附錄 B — 真實風險評估

```
高風險情況（不存在）         目前實際情況（低風險）
─ ─ ─ ─ ─ ─ ─ ─              ─ ─ ─ ─ ─ ─ ─ ─
smoke 測試依賴 line_index    ✓ 無測試斷言 line_index（推測，需確認）
原始資料行號變更              ✓ fixture 穩定不變
影響 smoke gate 判決邏輯      ✓ line_index 不參與 gate 決策
阻礙 CI 運行                  ✓ 不影響任何 CI job
```
