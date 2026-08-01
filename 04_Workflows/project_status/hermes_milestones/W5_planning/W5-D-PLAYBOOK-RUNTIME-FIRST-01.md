# W5-D-PLAYBOOK-RUNTIME-FIRST-01 — runtime-first pattern（萃取自 W5-A）

> **條目類型**：治理 / PLAYBOOK / 可重複套用的 workflow pattern
> **源頭**：W5-A-RUNTIME-01/02/03（dryrun → logging → ENF-PREVIEW → limited blocking）
> **版本**：v0.1（2026-05-31，萃取自 W5-A 三條 runtime 線的實戰經驗）
> **用途**：將「先觀察，再介入」的 runtime-first 梯子抽象為可套用的 pattern，
>   讓未來任何治理變更（新增 rule / 調整 threshold / 啟用 enforcement）可循此梯子前進，
>   不需從零設計。

---

## 1) Pattern 名稱

**`RUNTIME-FIRST` — read → log → preview → block 梯子**

短名：runtime-first / dry-then-deny / observe-then-enforce

> 這是治理/PLAYBOOK 層的 pattern，不是票號。未來任何 repo / workflow 要導入
> 新治理規則或調整 enforcement 強度，引用此 pattern 名稱即可。

---

## 2) 一句話定義

**在讓任何治理規則實際影響 pipeline 決策之前，先讓它在「只看、不動」的模式下
跑完一個完整週期，累積觀測資料，再依據資料決定是否提升到下一個層級。**

---

## 3) 背景：為什麼要先 dryrun / preview，再談 blocking

從 W5-A 的實戰中觀察到三個核心原因：

### 3.1 規則在紙面上合理，在資料上未必

治理規則（例如「score < 0.875 就 warn」）在設計時看起來合理，但真實資料的分佈
往往與預期不同。W5-A POLICY-MINING-01 顯示：threshold 0.875 從未被真實記錄觸及，
因為所有既有記錄的 score 都高於 0.875。如果直接上 blocking，會讓一個未經資料
驗證的 threshold 控制 pipeline 行為。

### 3.2 CI 環境不是本地環境

dry-run 在本地讀 artefact 成功，不代表它在 CI runner（ephemeral VM、不同的
路徑與權限）中也能執行。RUNTIME-02 logging-first 的目標之一，就是確認治理 CLI
在 CI 環境中可以正常運作並產出可索引的 log。

### 3.3 團隊對治理視覺化需要建立共識

當 CI log 開始出現 `[DRYRUN-LOG]` 和 `[GOV-ENF-PREVIEW]` 時，團隊會自然形成
「這些信號是觀察用的，不是已 enforce 的」認知。如果直接上 blocking，團隊可能
誤解 log 中的訊號含義，錯失真正該注意的信號。

---

## 4) 梯子結構（L0–L3）

```
L0: DRYRUN   → 純本地報表，不碰 CI，不寫 log，不影響 verdict
L1: LOGGING  → CI 內印 log，但仍不碰 verdict，continue-on-error: true
L2: PREVIEW  → CI 中模擬 enforcement（would_block 計數），但不實際 fail
L3: BLOCKING → 實際 fail pipeline，須有 kill-switch + rollback 機制
```

### 4.1 L0 — DRYRUN（Read-only observability）

**目標**：讓治理規則在完全隔離的環境中讀取 artefact 並產出 per-record 報表，
       確認規則邏輯可以運作並理解其在真實資料上的觸發情況。

**行為**：
- CLI 讀取 artefact（shadow_eval_results、ibridge records 等）
- 產出 per-record JSONL（含 actual_verdict / ideal_verdict / verdict_match）
- 產出 summary markdown（含 match ratio、rule 觸發統計、差異清單）
- 不修改任何 CI YAML、不寫入任何 pipeline 狀態

**範例（W5-A）**：`python -m tools.dryrun --input-dir artifacts/eval/ --output-dir observability/dryrun/`
→ 產出 `observability/dryrun/YYYYMMDDTHHMMSSZ_per_record.jsonl` + `_summary.md`

**退出條件（進 L1）**：
- AC-DRY-1~6 全部通過
- CLI 在本地成功讀取 artefact 並產出正確格式的報表
- 規則觸發 distribution 可被團隊解讀（無 unknown 佔比爆炸的情況）

### 4.2 L1 — LOGGING（CI-embedded read-only）

**目標**：將治理信號引進 CI，讓團隊在每次 CI run 的 log 中看到治理快照，
       並確認 CLI 在 CI 環境（ephemeral runner、網路路徑、依賴）中仍可正常運作。

**行為**：
- CI workflow 中新增一個 step，執行 dry-run CLI
- CLI stdout/stderr 中的 `[DRYRUN-LOG]` 行出現在 CI run log 中
- 可選上傳 summary JSON 為 CI artefact
- `continue-on-error: true`，step 失敗不影響 pipeline 結果

**範例（W5-A）**：`eval-gate-ci.yml` 的 `eval-shadow-nightly` job 新增 logging step
```yaml
- name: Dry-run governance logging
  continue-on-error: true
  run: |
    python -m tools.dryrun --input-dir ${{ env.ARTIFACTS_DIR }} --output-dir ${{ runner.temp }}/dryrun-ci/
```

**退出條件（進 L2）**：
- CI run log 中有完整 `[DRYRUN-LOG]` 摘要行
- 至少觀察過一個完整的 nightly CI 週期（累積 RUNTIME-02 的 CI artefact）
- `[DRYRUN-LOG]` 行可以被 grep/scan 自動化工具解析

### 4.3 L2 — ENFORCEMENT PREVIEW（Simulated blocking, no actual fail）

**目標**：讓團隊看到「如果 enforcement 啟用了，會擋掉多少記錄、哪些記錄」，
       但不實際影響 pipeline。Phase A 是真實 enforcement 的觀測階段。

**行為**：
- CI step 中計算 `would_block` / `would_warn` 兩組計數
- 印出 `[GOV-ENF-PREVIEW]` 行，說明 L2 would_block 有多少筆紀錄
- 不 fail CI step，不影響 pipeline 最終結果
- 可記錄哪些 rule 的 L2 會被觸發，供人工審閱

**範例（W5-A）**：`enf_preview_wrapper` 輸出：
```
[GOV-ENF-PREVIEW] ⚠ PREVIEW — 非實際 enforcement，不影響 pipeline 結果
[GOV-ENF-PREVIEW] L2 would_block: 3 records (task-001, task-045, task-102)
[GOV-ENF-PREVIEW] L1 would_warn: 12 records | L0 would_noop: 832 records
```

**退出條件（進 L3）**：
- Phase A 至少運行 N 個 nightly CI 週期（N 由 policy mining 票決定）
- L2 would_block 的 false positive 率低於可接受閾值
- 團隊人工檢視過所有 L2 would_block 記錄，確認無明顯誤判
- kill-switch 機制已驗證可正常開關

### 4.4 L3 — LIMITED BLOCKING（Actual enforcement）

**目標**：在嚴格範圍內啟用實際的 enforcement，讓符合 L2 條件的規則真正 fail pipeline。

**行為**：
- 遇到 L2 would_block 紀錄時，CI step exit 1（或等價 pipeline 失敗信號）
- 生效範圍限於明列的 workflow / job / branch（非全域）
- 每次 block 留下完整 trace（rule id、inputs、verdict、timestamp）
- kill-switch 以環境變數（如 `GOV_ENFORCE_ENABLED=0`）控制，無需 git push

**範例（W5-A）**：ENF-PREVIEW 行變為：
```
[GOV-ENF-PREVIEW] 🚫 ENFORCED — 3 records blocked (task-001, task-045, task-102)
```

**範圍限制（初始 rollout）**：
- 僅 nightly CI（非 PR workflow）
- 僅特定 branch（如 main / develop）
- 僅 Level 2 規則（binary、false positive 率接近 0）
- 擴展到更多 workflow 需另行開票

---

## 5) 使用時機：什麼類型的治理變更要走這條梯子

符合以下任一條件時，**必須先走完這條梯子**，不得跳步：

| # | 情境 | 說明 |
|---|------|------|
| 1 | **新增一條治理規則** | 新規則尚未在真實資料上驗證過，必須從 L0 開始觀察觸發情況 |
| 2 | **調整治理 threshold 或 bucket 定義** | 變更後的規則可能在某些邊界觸發未預期的行為，需重新累積觀測資料 |
| 3 | **將已通過 L0/L1 的規則提升到 enforcement** | 需先有 Phase A（preview）資料，確認 false positive 率可接受 |
| 4 | **跨 repo 或跨 workflow 移植治理邏輯** | 新的環境可能有不同的 artefact schema 或 CI 設定，需從頭驗證 |
| 5 | **規則調整後的回測** | 當 threshold 或分類方式變更時，dry-run 可快速對照新舊規則的 verdict 分布 |

**可以跳步的情境**：
- 規則已在其他 repo 完成 L0→L1→L2 的完整梯子，且新 repo 的 artefact schema 完全相同 → 可從 L1 開始，但仍建議跑一次 L0 確認路徑正確
- 純粹的 log format 調整（如修改 `[DRYRUN-LOG]` 的統計行格式）→ 可在 L1 內完成，不需重走 L0

---

## 6) 反例：什麼情況不適合，或可以略過某些階段

### 6.1 不適用於純技術性 CI 改動

如果變更只是「調整 CI step 的 timeout」、「改 log level」，不涉及治理規則
邏輯或 pipeline 決策，則不需要走這條梯子。

### 6.2 明確不允許的跳步

| 跳步行為 | 為什麼不允許 |
|---------|-------------|
| 直接從 L0 上 L3（無 L1/L2） | CI 環境適配性未驗證；團隊對治理信號的認知未建立；沒有 Phase A 的 preview 資料可參考 |
| L1→L3（跳過 L2 preview） | 沒有「模擬 enforcement」的觀測階段，false positive 率無法評估 |
| 在未達退出條件的情況下進入下一層 | 例如：Phase A 只跑了 2 天就想進 Phase B；或 unknown 佔比仍高達 30% 就想升級 |

### 6.3 需要提前終止梯子的情況

若在某層發現規則邏輯有根本性問題（例如： artefact schema 與規則預期不符，
導致 80% 的記錄都落到 unknown bucket），應：
1. 停止升級，留在當前層
2. 回報問題（记录為 DEBT_LOG 或等價文件）
3. 修復規則邏輯或改善 artefact schema 後，再重新開始梯子

---

## 7) Enforceability Ladder（決定規則能否進入 L2/L3）

### 7.1 三級分類法（來自 W5-A-RUNTIME-03-LIMITED-DENY_plan.md §2）

| 等級 | 名稱 | 行為 | 範例 | 是否可 enforce |
|------|------|------|------|---------------|
| **L0** | Observability-only | 僅適合 dry-run / log，不應用於自動決策 | `needs_review` bucket、主觀評分 | ❌ 永不 |
| **L1** | Advisory | 可觸發 warning / review 信號，但**不 direct fail** | `gate_ok_score_low`（actual=allow, ideal=warn） | ⚠️ 可 advisory |
| **L2** | Enforceable | 符合條件時可直接 fail pipeline | `gate_fail_deny` + binary conditions（semgrep > 0, error_type=timeout） | ✅ 可 enforce |

### 7.2 升級到 L2 的必要條件

1. **規則判定是 binary 的** — 無灰色地帶（例如 `semgrep_count > 0`）
2. **在 L0/L1 中已觀察 ≥N 個週期** — 具體 N 由 policy mining 票決定
3. **false positive 率低於可接受閾值** — 具體值由團隊決定
4. **有明確的 action 對應** — pipeline 可以採取的 action 是確定的

### 7.3 明確排除的bucket

- `needs_review` — 永遠不進 L2，設計給人工判斷
- `unknown` — 先改善資料來源，不直接 block
- `allow` — 正常狀態，不需要 block

---

## 8) 與既有 W5 文件的關係

| 文件 | 關係 |
|------|------|
| `W5-A-RUNTIME-PLAYBOOK.md` | L0 的詳細定義，含 B1–B7 邊界、AC-DRY-1~6、五 bucket 規則 |
| `W5-A-RUNTIME-02-LOGGING-FIRST_plan.md` | L1 的詳細定義，含 L1–L6 邊界、CI step 設計、異常處理 |
| `W5-A-RUNTIME-03-LIMITED-DENY_plan.md` | L2/L3 的詳細定義，含 enforceability ladder、Phase A/B rollout、kill-switch |
| `W5-A-RUNTIME-03-CI-DATA-PIPELINE-DESIGN-01.md` | 資料流的 L0 前置設計（確保 L0 有真實資料可讀） |
| `W5-A-RUNTIME-03-POLICY-MINING-01.md` | 從 L0 觀測資料中萃取 L2 candidate 的方法論 |

本條目是上層抽象：將 L0/L1/L2/L3 整合為一個完整梯子，供未來直接引用。

---

## 9) 如何沿用到其他 repo / workflow

### 9.1 沿用流程

```
Step 1 — Artefact 盤點
    確認新 repo 中是否有 equivalent 的 artefact（shadow eval results、ibridge records、eval export）
    將抽象路徑映射到實際檔案位置

Step 2 — 選擇起始層級
    若新 repo 從未跑過治理觀測 → 從 L0 開始
    若 L0 已在另一 repo 驗證且 schema 完全相同 → 可考慮從 L1 開始（但建議跑一次 L0 確認）

Step 3 — 產出 plan + brief
    參考本條目結構 + W5-A-RUNTIME-0X_plan.md 格式

Step 4 — 實作（Hermes → Cursor / 其他人）
    遵守對應層級的邊界（B1–B7 為底線，加上 L1–L6 或 ENF-B1~B6）

Step 5 — 人類 gate → 回寫 PLAYBOOK
    確認對應層級的 AC 全部通過
    若有新發現（edge case、邊界調整），更新本條目（v0.2、v0.3...）
```

### 9.2 常見調整項

| 調整項 | 說明 |
|-------|------|
| Artefact 路徑 | 不同 repo 的 `artifacts/`、`observability/` 目錄結構可能不同 |
| JSON 欄位名稱 | `gate_result` / `verdict` / `metrics` 的名稱可能因 repo 而異 |
| CI 語法 | GitHub Actions、GitLab CI、Jenkins 的 step 語法不同 |
| Bucket 數量 | 若新 repo 只需 3 bucket，可在 plan 中調整，但 edge_unknown 出口建議保留 |

---

## 附錄 A — 版本歷史

| 版本 | 日期 | 作者 | 變更說明 |
|------|------|------|---------|
| v0.1 | 2026-05-31 | W5-D | 萃取自 W5-A RUNTIME-01/02/03 三條 runtime 線的實戰經驗，產出首版 runtime-first pattern 條目 |

---

## 附錄 B — 三行摘要（供快速引用）

1. **一句話定義**：在讓任何治理規則實際影響 pipeline 之前，先讓它在只讀模式下跑完一個完整週期，累積觀測資料，再依據資料決定是否提升到 enforcement 層級。
2. **梯子主要階段**：L0 DRYRUN（純本地報表）→ L1 LOGGING（CI 內印 log，不碰 verdict）→ L2 PREVIEW（模擬 blocking，不實際 fail）→ L3 BLOCKING（實際 enforcement，需 kill-switch）。
3. **最重要的「不要跳步」提醒**：永遠不要在沒有 Phase A（L2 preview）觀測資料的情況下直接進入 Phase B（L3 blocking）—— false positive 率是無法在事後弥补的，必須在事前透過 preview 確認。
