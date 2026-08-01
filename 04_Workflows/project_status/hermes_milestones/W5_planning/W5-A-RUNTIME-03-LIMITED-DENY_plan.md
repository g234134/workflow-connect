# W5-A-RUNTIME-03-LIMITED-DENY — Wave 5-A 第三條 runtime 線（limited deny design）

> **票號**：W5-A-RUNTIME-03-LIMITED-DENY-PLAN-01（設計方案卡）
> **位置**：W5-A 軸的第三條 runtime 線 — **在嚴格範圍內允許規則影響 gate verdict / pipeline 成敗**
> **範圍**：定義 enforceability ladder（Level 0/1/2）、兩階段 rollout（preview → limited blocking）、kill-switch 與 rollback 機制；不在此 plan 中決定具體哪些 rule 要 deny
> **不處理**：具體 rule selection / policy mining（後續獨立票）、重寫乾跑規則引擎、全域生效的 enforcement
> **先決**：
>   - W5-A-RUNTIME-01-DRYRUN 已落地（乾跑 CLI + 報表 + PLAYBOOK）
>   - W5-A-RUNTIME-02-LOGGING-FIRST 已落地（CI logging step + [DRYRUN-LOG] + artefact）
>   - AC-DRY-1~6 及 AC-L-1~7 全部通過
>   - 有至少 N 個 cycle（nightly run）的 RUNTIME-02 log 資料可作為 false positive 校準依據
> **參考**：
>   - `W5-A-RUNTIME-PLAYBOOK.md`（乾跑治理模式條目，含邊界與 AC-DRY）
>   - `W5-A-RUNTIME-02-LOGGING-FIRST_plan.md`（logging-first 完整設計，含 L1–L6 邊界）
>   - `W5-A-RUNTIME-01-DRYRUN_plan.md`（乾跑設計稿，含治理規則 §4）

---

## (1) 目的與定位

### 1.1 RUNTIME-03 在三階段中的位置

```
RUNTIME-01 (乾跑)      RUNTIME-02 (logging)      RUNTIME-03 (limited deny)
┌──────────────┐       ┌──────────────┐          ┌──────────────┐
│ 只讀 artefact│  ──→  │ CI 內印 log  │  ──→     │ 限域 deny    │
│ 產本地報表   │       │ + 附加 JSON  │          │ + override   │
│ 不碰 CI      │       │ 不碰 verdict │          │ + rollback   │
└──────────────┘       └──────────────┘          └──────────────┘
  DRYRUN_AUDIT_ONLY       LOG_ONLY                  LIMITED_ENFORCE
  (v0.1 done)             (v0.1 done)               （本票）
```

每一層的安全擔保演化：

| 階段 | 對 CI 的影響 | 對 gate verdict 的影響 | 可回復性 |
|------|-------------|----------------------|---------|
| RUNTIME-01 (乾跑) | 無 — 完全不碰 CI YAML | 無 — 只產本地報表 | 刪除報表檔即可 |
| RUNTIME-02 (logging) | 輕微 — 新增 logging step，但 `continue-on-error: true` | 無 — log 只讀、不改 verdict | 關掉 CI step 即可 |
| RUNTIME-03 (limited deny) | 有限 — 特定 workflow/branch 的 step 可 fail pipeline | 有 — 對屬於 Level 2 的規則啟用真正 deny | 需要 kill-switch + rollback 機制 |

### 1.2 為什麼需要有限 deny，而不是直接全量 deny

RUNTIME-03 設計的核心問題是三個：

**Q1：哪些情境值得被「真正擋掉」？**
不是所有治理規則都適合自動 deny。有些規則是主觀的（needs_review）、有些是閾值可調的（warn on low score）、有些則是硬性的（semgrep > 0 且 gate_result = fail）。RUNTIME-03 需要一個分類法（enforceability ladder）來決定哪些情境可以被自動阻擋，哪些仍需人工判斷。

**Q2：怎麼避免一開始就 over-enforce？**
分階段 rollout — Phase A 只做 enforcement preview（模擬阻擋但不實際 fail），在觀察到足夠週期的 false positive 率後，才進入 Phase B 的實際 blocking。Phase B 初始僅限於特定的 workflow（nightly、非 production 路徑），待穩定後再擴展。

**Q3：一旦出現誤判，如何回滾？**
每次 deny 決策必須留下完整 trace（rule id、inputs、score、timestamp），讓 reviewer 可以回溯、辨識 false positive、並決定是否調整 rule 或觸發 kill-switch。kill-switch 必須是一鍵可關閉的（環境變數或 CI variable），並且在 rollout 初期就準備好，而不是出了問題才補。

### 1.3 一句話定位

> RUNTIME-03 讓「已經在 dry-run + logging 中被反覆驗證過的規則」在嚴格範圍內實際生效，但保留下一次 CI run 即可關閉的 kill-switch。

---

## (2) 可被 enforce 的條款類型（Enforceability Ladder）

RUNTIME-03 引入一個三級分類法，用來判斷治理規則（bucket + rule 組合）是否適合自動 enforce。

### 2.1 三級分類

| 等級 | 名稱 | 行為 | 範例 | 是否可 enforce | 備註 |
|------|------|------|------|---------------|------|
| **L0** | Observability-only | 僅適合 dry-run / log 觀察，不建議用於任何形式的自動決策 | `needs_review` bucket、主觀評分、閾值接近邊界的 `warn` | ❌ 永不 | 這類判定需要人工 context 判斷，自動 deny 的 false positive 率過高 |
| **L1** | Advisory | 可以觸發 warning / review 信號，但**不 direct fail** pipeline | `gate_ok_score_low`（actual=allow 但 ideal=warn）、`gate_fail_needs_review`（fail 但非 semgrep） | ⚠️ 可 advisory，不直接 fail | pipeline 可設一個「review recommended」的非 blocking 標示，不改變 exit code |
| **L2** | Enforceable | 符合條件的記錄可以直接讓 pipeline fail | `ideal_verdict == deny` 且 rule 標記為硬約束（semgrep > 0、gate_result = fail、score 遠低於 threshold） | ✅ 可 enforce | 這類規則的 false positive 率在 dry-run/log 階段應當已收斂到接近 0 |

### 2.2 L2（Enforceable）的具體條件

一條 rule 要升級到 L2，須同時滿足以下條件：

1. **規則判定是 binary 的** — 沒有灰色地帶（例如 `semgrep_count > 0` 是明確的 yes/no，不是 "maybe problematic"）。
2. **在 RUNTIME-01 和 RUNTIME-02 中已觀察 ≥N 個週期** — 最少經過 N 次 nightly CI 的 dry-run + log 驗證（N 的具體值由後續 policy mining 票決定）。
3. **false positive 率低於可接受閾值** — 在觀察期間，dry-run rule 標記為 deny（或等價強判定）但最終人工確認不應 deny 的比率低於 X%（具體值由 policy mining 票決定）。
4. **有明確的 action 對應** — pipeline 可以採取的 action 是確定的（fail the step），不需要進行主觀權衡。

### 2.3 不屬於 L2 的情境（明確排除）

以下情境不應進入 L2 enforcement，無論其在 L0/L1 的觀察表現如何：

- `needs_review` bucket — 這是設計給人工判斷的。即使它在 dry-run 中被 100% 觸發，也應保持為 L1 advisory 或保持 log-only。
- `unknown` bucket — 資料不足以判定。若 unknown 佔比高，應先改善資料來源或擴展規則，而不是直接 deny。
- `allow` bucket — 這是正常狀態。如果 allow 被判定為不正確，應是 gate 邏輯有 bug，而不是靠 deny 來補償。
- 任何涉及 rollout 階段決策的規則（cohort 大小、promote 條件）— 這些屬於 rollout control，不在本 plan 的 enforce 範圍內。

---

## (3) Rollout 策略（兩段式：先 preview 再 blocking）

RUNTIME-03 的 rollout 分為兩個階段，中間有明確的 gate 條件。

### 3.1 Phase A — Enforcement Preview（模擬，不實際 fail）

**目標**：讓團隊看到「如果 enforcement 啟用了，會擋掉多少記錄、哪些記錄」，但不實際影響 pipeline。

**實作方式**：
- 在 CI workflow（接在 RUNTIME-02 logging step 之後或與其合併）新增一個 "enforcement preview" step。
- 此 step 計算 `would_block` / `would_warn` 兩組計數，但**只印 log，不 fail**。
- 使用獨立的 log 前綴（例如 `[GOV-ENF-PREVIEW]`），與 `[DRYRUN-LOG]` 明確區分。
- 輸出範例：
  ```
  [GOV-ENF-PREVIEW] ⚠ PREVIEW — 非實際 enforcement，不影響 pipeline 結果
  [GOV-ENF-PREVIEW] L2 would_block: 3 records (task-001, task-045, task-102)
  [GOV-ENF-PREVIEW] L1 would_warn: 12 records | L0 would_noop: 832 records
  [GOV-ENF-PREVIEW] L2 false-positive candidates: 0 (filter threshold: score ≥ 0.7)
  ```

**退出條件（進入 Phase B 的前置要求）**：
- Phase A 至少運行 N 個 nightly CI 週期（具體 N 由 policy mining 票決定，建議 ≥7 次 nightly）。
- 在 Phase A 中，L2 `would_block` 的 false positive 率低於 X%（X 由政策決定，建議 ≤5%）。
- 至少有 M 條 L2 deny 記錄被人工驗證過（M 具體值由 policy mining 票決定）。
- 團隊已檢視過所有 L2 would_block 記錄，並確認沒有一條是明顯誤判。
- kill-switch 機制已在 Phase A 中驗證過至少一次（確認可以開關 enforcement）。

### 3.2 Phase B — Limited Blocking（實際 enforcement）

**目標**：在嚴格範圍內啟用實際的 enforcement，讓 Level 2 的規則可以真正 fail pipeline。

**實作方式**：
- 在 CI workflow 中原本是 enforcement preview 的 step，將 `exit 0` 改成「遇到 L2 would_block 則 exit 1（或等價的 pipeline 失敗信號）」。
- 行為變化僅限於：
  - 指定的 workflow（例如 nightly CI，暫時不包含 PR workflow）。
  - 指定的 branch（例如 `main` 或 `develop`，暫時不包含 feature branches）。
  - 僅 Level 2 條款觸發 deny。Level 1 和 Level 0 保持 preview-only / log-only。
- 保持 `[GOV-ENF-PREVIEW]` 的前綴，但將 log 行改成：
  ```
  [GOV-ENF-PREVIEW] 🚫 ENFORCED — 3 records blocked (task-001, task-045, task-102)
  [GOV-ENF-PREVIEW] ⚠ DRY-RUN — 其他所有記錄不影響 pipeline 決策
  ```

**退出條件（擴展到更多 workflow/branch）**：
- Phase B 在初始範圍內穩定運行 ≥N 個週期。
- 無任何 L2 false positive 需要緊急回滾。
- 團隊已建立 override 流程（allowlist + reason）。
- 決策擴展到更多 workflow/branch 需另行開票（可能是 RUNTIME-04 或其他後續票）。

### 3.3 這個 rollout 策略要達成的三個目標

1. **不在未充分觀察前就讓任何規則控管 gate** — 每條 L2 rule 在 Phase A 中已被反覆驗證，不是「直接打開就上」。
2. **讓 enforcement 前有可追溯的 log** — Phase A 的 preview log 可以作為未來討論「這條 rule 是否該強制執行」的證據。
3. **blocking 一開始範圍小、可控** — 僅限 nightly CI、僅限 Level 2、僅限特定 branch。即使爆炸，也只影響一條 nightly pipeline。

---

## (4) 邊界與控制（kill-switch / rollback）

### 4.1 硬邊界（ENF-B1~B6）

| # | 邊界 | 說明 | 違反實例 |
|---|------|------|---------|
| ENF-B1 | **不直接修改 policy 本身** | RUNTIME-03 只能照既定 policy（rule + threshold）做 runtime 決策，不得在 enforcement step 中動態調整 policy。policy 變更須經獨立的 policy review 流程。 | enforcement step 內寫 `if threshold < 0.5: threshold = 0.5` 動態調低門檻 |
| ENF-B2 | **enforcement 僅作用於明列範圍** | 生效的 workflow、job、branch 必須在 ticket memory 或 config 中明確列出。禁止「全域生效」的 enforcement。 | 沒有列出 scope → 自動應用到所有 workflow |
| ENF-B3 | **每次 deny 必須留下完整 trace** | block decision 必須包含：rule id、inputs（score、metrics snapshot）、verdict、timestamp、artefact 路徑。不可只印 log 但無法回溯。 | deny 只說 `blocked 3 records` 但不知道是哪三條、為什麼 |
| ENF-B4 | **必須存在可驗證的 kill-switch** | 以環境變數（如 `GOV_ENFORCE_ENABLED=0`）或 CI variable 作為開關。kill-switch 關閉後，下一個 CI run 即完全恢復至 RUNTIME-02 等級（log-only + continue-on-error）。 | kill-switch 需要重寫 CI YAML 或 git push 才能生效 |
| ENF-B5 | **false positive → 先標記再調整，不可直接關 log** | 若某 L2 rule 出現 false positive，流程為：新增 false positive 記錄 → 檢討 rule 的 threshold / 條件 → 調整後回 Phase A 重新 preview → 確認後重回 Phase B。不可因為一次誤判就把整條 rule 從 enforcement 中移除而不留紀錄。 | 有 false positive 就直接把 rule 的 enforcement 關掉，不回 Phase A 驗證 |
| ENF-B6 | **不得在同一票混合新增 rule 與變更底層模型** | 一張 implementation 票不能同時「新增一條 L2 enforcement rule」又「大幅改動底層 eval/gate 的計分邏輯或資料來源」。兩者必須分票處理，避免混因。 | 在「新增 semgrep deny rule」的同張票中修改了 semgrep 的計分方式 |

### 4.2 kill-switch 設計原則

kill-switch 是 RUNTIME-03 最重要的安全機制。應滿足：

1. **無需 git push** — kill-switch 不應依賴 YAML 修改或 PR merge。環境變數或 CI secret 是較好的載體。
2. **下個 CI run 即生效** — 關閉 kill-switch 後，不需要重跑已完成的 CI run，但下一個 run 應完全恢復至 RUNTIME-02 行為。
3. **開關有 log 紀錄** — 每次 enforcement 啟動時印出 `[GOV-ENF-PREVIEW] ENFORCEMENT ACTIVE — kill-switch: <開關狀態>`，關閉時也類似。
4. **預設關閉** — 初始 rollout 時 kill-switch 預設為關閉（即 Phase B 不生效），直到團隊明確決定打開，並通過對應的 PR review 後才啟用。

### 4.3 rollback 流程（草案）

當 enforcement 導致 blocking 問題時，rollback 流程：

```
Step 1 — 偵測：某個 CI run 因 enforcement 而 fail，經手動確認為 false positive。
Step 2 — 切換 kill-switch：設置 GOV_ENFORCE_ENABLED=0，下一個 CI run 即恢復 log-only。
Step 3 — 記錄 false positive：在 DEBT_LOG 或等價位置記錄 rule id、inputs、timestamp。
Step 4 — 調整 rule：檢討該 rule 的 threshold / 分類（是否應降回 L1 或 L0）。
Step 5 — 回 Phase A：修改後的 rule 先以 preview 模式跑 N 次，確認 false positive 不再發生。
Step 6 — 重新開啓：經 reviewer gate 後，重新開啟 enforcement。
```

---

## (5) 與既有 RUNTIME-01 / 02 / PLAYBOOK 的對應

### 5.1 規則來源

RUNTIME-03 **不重寫一套新的規則引擎**。它直接站在乾跑引擎上：

| 既有元件 | RUNTIME-03 的使用方式 | 變更 |
|---------|----------------------|------|
| 乾跑規則引擎（五 bucket + edge_unknown） | 仍由 `tools/dryrun/*` 提供 per-record 判定。RUNTIME-03 在此基礎上增加 enforcement 決策層（決定哪些 bucket/rule 組合應 fail pipeline）。 | **不變** — 不修改乾跑引擎邏輯 |
| RUNTIME-01 per-record JSONL | 提供歷史 baseline。policy mining 時可分析過去 N 次 CI 的 `ideal_verdict` 分布，決定哪些 rule 值得升級到 L2。 | **不變** — 只讀不寫 |
| RUNTIME-02 [DRYRUN-LOG] / CI artefact | 提供最近的 enforcement preview 觀察資料。Phase A 的 preview log 會與既有 [DRYRUN-LOG] 並列，但使用 [GOV-ENF-PREVIEW] 前綴區分。 | **追加** — 不修改 RUNTIME-02 既有的 log 格式或 artefact |
| `tools/dryrun_ci_wrapper.py` | Phase A 可複用 wrapper 的 CI 環境適配邏輯（路徑、權限、異常處理），但需要擴展或新增一個 enforcement 版本的 wrapper。 | **新增** — 不修改既有 wrapper（新增 `dryrun_enforcement_wrapper.py` 或等價） |

### 5.2 流程演進：從 Hermes → Cursor → 人類 gate 到加入 policy mining

```
既有節奏（RUNTIME-01 / 02）：
  Hermes（plan + brief） → Cursor（實作 + 測試） → 人類 gate → PLAYBOOK 更新

RUNTIME-03 新增一個步驟：
  Hermes（plan + brief）
    → [新增] Policy mining / rule selection（分析 RUNTIME-01/02 資料，決定哪些 rule 進 L2）
      → Cursor（實作 enforcement wrapper + CI step + kill-switch + test）
        → 人類 gate（含 kill-switch 驗證）
          → PLAYBOOK 更新（可選：新增「enforcement pattern」章節）
```

### 5.3 實作票應引用的文件段落

未來 W5-A-RUNTIME-03-IMPLEMENTATION-01 票在撰寫時，應直接引用：

- `W5-A-RUNTIME-PLAYBOOK.md §3`：輸入/輸出格式的參考規範（與 RUNTIME-01 的 artefact 相容）
- `W5-A-RUNTIME-PLAYBOOK.md §4`：底線邊界 B1–B7（RUNTIME-03 繼承這些邊界，加上 ENF-B1~B6）
- `W5-A-RUNTIME-PLAYBOOK.md §6`：前置驗收條件（AC-DRY checklist — 確保乾跑引擎仍在正確運作）
- `W5-A-RUNTIME-02-LOGGING-FIRST_plan.md §2–§3`：CI logging step 的既有設計（RUNTIME-03 的 preview step 可參考其結構與異常處理模式）
- **本 plan §2–§4**：enforceability ladder、rollout 策略、邊界與 kill-switch

---

## (6) AC-ENF-x 驗收條件

以下高層驗收條件供未來 implementation 票對齊。注意：這些是「enforcement 功能的驗收條件」，不是 policy mining 的驗收條件（policy mining 將有獨立的 AC）。

### AC-ENF-1：enforcement 僅作用於 Level 2 條款

- [ ] 實施 enforcement 的規則僅限於已被分類為 Level 2（Enforceable）的條款
- [ ] Level 0 和 Level 1 的規則保持 preview-only / log-only，不受 enforcement step 影響
- [ ] 每條 L2 rule 的選擇理由有文字記錄（例如引用 dry-run log 中的 match 率與 false positive 率）

### AC-ENF-2：生效範圍明確列出且初始 rollout 限縮

- [ ] enforcement 的生效範圍（workflow / job / branch）在 ticket memory 或 config 中明確列出
- [ ] 初始 rollout 僅限於非關鍵路徑（nightly CI、非 production release、非 PR workflow）
- [ ] 任何擴展到更多 workflow 都須經獨立票 + 人類 gate

### AC-ENF-3：每次 deny 留下完整 trace

- [ ] 每次 block decision 的 log 包含：rule id、verdict、score（或等價計量）、artefact 路徑引用
- [ ] 被 deny 的記錄（或其 ID）可以從 log 回溯到原始的 per-record JSONL 或 CI artefact

### AC-ENF-4：kill-switch 存在且可驗證

- [ ] kill-switch 以環境變數（或等價機制）實作，無需 git push 即可生效
- [ ] kill-switch 關閉後，下一個 CI run 完全恢復至 RUNTIME-02 行為（log-only + continue-on-error）
- [ ] kill-switch 已在測試中至少成功驗證一次（開 → enforcement 生效 → 關 → enforcement 停止）

### AC-ENF-5：不破壞既有 DRY（RUNTIME-01）與 LOG（RUNTIME-02）

- [ ] RUNTIME-03 不修改 `tools/dryrun/*` 的任何程式碼或輸出格式
- [ ] RUNTIME-02 的 `[DRYRUN-LOG]` log 行保持不變，不受 enforcement step 影響
- [ ] `git diff --stat` 確認 RUNTIME-03 僅新增（或修改 CI YAML / wrapper），未改既有乾跑或 logging 元件

### AC-ENF-6：Phase A（preview）有足夠的觀察期證據

- [ ] Phase A 的 `[GOV-ENF-PREVIEW]` log 行已被記錄至少 N 次 nightly CI run（N 由後續 policy mining 票決定）
- [ ] Phase A 的 L2 would_block 記錄中無（或極低）已確認的 false positive
- [ ] Phase A 期間有團隊成員人工檢視過 L2 would_block 記錄的樣本

### AC-ENF-7：override 流程已定義（可選但建議）

- [ ] 存在 allowlist 機制（可讓特定 task_id 或特定 record 跳過 enforcement），須記錄 reason
- [ ] override 的使用有 log 紀錄（誰、什麼時候、為什麼 override）

---

## 附錄 A — 與既有文件的對應

| 文件 | 關係 | 注意 |
|------|------|------|
| `W5-A-RUNTIME-PLAYBOOK.md` | RUNTIME-03 繼承其邊界 B1–B7，並在其基礎上追加 ENF-B1~B6。PLYABOOK 的 AC-DRY 是前置依賴。 | 不修改原文。 |
| `W5-A-RUNTIME-02-LOGGING-FIRST_plan.md` | RUNTIME-03 的 Phase A preview step 可參考 RUNTIME-02 的 CI step 結構與異常處理模式。 | 不修改原文。 |
| `W5-A-RUNTIME-01-DRYRUN_plan.md` | 乾跑規則引擎（五 bucket）是 RUNTIME-03 enforcement 決策的基礎。 | 不修改原文。 |
| `W5_OVERVIEW.md` | RUNTIME-03 完成後更新進度小節。 | 本 plan 不更新 overview。 |
| `W5-A-RUNTIME-POLICY-MINING`（未來票） | 決定具體哪些 rule 升級到 L2，獨立票，與本 plan 正交。 | 本 plan 不預先決定 rule 清單。 |

---

## 附錄 B — 版本歷史

| 版本 | 日期 | 作者 | 變更說明 |
|------|------|------|---------|
| v0.1 | 2026-05-31 | W5-A-PLANNING | 首版 RUNTIME-03-LIMITED-DENY 設計方案卡。定義 enforceability ladder、兩段 rollout、kill-switch 機制、AC-ENF-1~7。 |
