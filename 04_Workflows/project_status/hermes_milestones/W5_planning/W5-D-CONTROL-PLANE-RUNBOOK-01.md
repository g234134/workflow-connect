# W5-D-CONTROL-PLANE-RUNBOOK-01 — 治理控制面開關與操作指南

> **票號**：W5-D-CONTROL-PLANE-RUNBOOK-01
> **類型**：runbook / 維運手冊
> **範圍**：W5-A / W5-D 中所有已實作或已設計的治理開關（env / config / workflow trigger）
> **硬邊界**：僅撰寫文件，不修改任何程式或 CI。未實作的開關以「預計／TODO」標註。
> **參考**：
>   - `W5-A-RUNTIME-03-LIMITED-DENY_plan.md`（kill-switch 設計、ENF-B1~B6、rollback 流程）
>   - `W5-A-RUNTIME-03-CI-DATA-PIPELINE-DESIGN-01.md`（shadow pipeline mode、SHADOW_BATCH_DIR）
>   - `W5-A-RUNTIME-03-ENF-PREVIEW_BRIEF_TASK_FOR_CURSOR.md`（Phase A preview step 行為）
>   - `W5-A-RUNTIME-PLAYBOOK.md`（dry-run 治理模式）
>   - `.github/workflows/eval-gate-ci.yml`（CI 排程與步驟）

---

## 1. 控制面總覽（目前有哪些開關）

以下列出目前 W5 治理鏈中所有重要的控制點（env var、CI config、workflow trigger），以及已設計但尚未實作的開關。

### 1.1 資料源的開關

| 開關 | 位置 | 類型 | 預設值 | 影響範圍 | 實作狀態 |
|------|------|------|--------|----------|----------|
| **SHADOW_BATCH_DIR** | `eval-gate-ci.yml` `env.SHADOW_BATCH_DIR` | CI env var | `artifacts/eval` | `fetch_latest_shadow_batch.sh` 搜尋批次檔的目錄 | ✅ 已實作 |
| **Shadow pipeline mode** | `scripts/fetch_latest_shadow_batch.sh` 自動判別 | 自動偵測 | `mode=fixture`（無批次檔時） | 決定 CI 治理鏈（dryrun / enf_preview）看見的是真實資料還是 fixture | ✅ 已實作 |
| **eval-shadow-nightly 排程** | `eval-gate-ci.yml` `on.schedule` | cron | `0 6 * * *`（UTC 06:00） | 每天自動觸發一次 nightly 治理管線 | ✅ 已實作 |
| **eval-shadow-nightly 手動觸發** | GitHub UI `workflow_dispatch` | 手動 | N/A | 可在任意時間手動啟動 nightly job | ✅ 已實作 |

**Shadow pipeline mode 詳細說明**：
- `mode=shadow`：批次檔 `shadow_batch_<datestamp>.jsonl` 存在於 `SHADOW_BATCH_DIR` → CI 讀取真實資料
- `mode=fixture`：無批次檔 → fallback 到 `tests/fixtures/eval/shadow_raw_records.jsonl`（4–6 條靜態 fixture 記錄）
- 判斷依據：`fetch_latest_shadow_batch.sh` 搜尋目錄下檔名字典序最大的 `shadow_batch_<datestamp>.jsonl`
- 日誌標記：`[SHADOW-PIPELINE] mode=shadow batch=<datestamp>` 或 `[SHADOW-PIPELINE] mode=fixture reason=<原因>`
- ⚠ 注意：fixture mode 是靜默的（無 alert）— 若預期有資料但未上傳，CI 會安靜地 fallback 到 fixture

### 1.2 治理步驟的開關

| 開關 | 位置 | 類型 | 預設值 | 影響範圍 | 實作狀態 |
|------|------|------|--------|----------|----------|
| **DRYRUN-LOG step** | `eval-gate-ci.yml` `eval-shadow-nightly` job | CI step + `continue-on-error: true` | 總是啟用 | 觀察性 logging：`[DRYRUN-LOG]` 印 per-record 摘要，不影響 verdict | ✅ 已實作（Phase A） |
| **GOV-ENF-PREVIEW step** | `eval-gate-ci.yml` `eval-shadow-nightly` job | CI step + `continue-on-error: true` | 總是啟用 | Enforcement preview：印 would_block / would_warn 計數，永遠 exit 0 | ✅ 已實作（Phase A） |
| **eval-shadow-smoke (PR path)** | `eval-gate-ci.yml` `on.push` | CI trigger | 僅 fixture（3 條記錄） | PR 觸發的輕量 smoke test | ✅ 已實作 |

### 1.3 已設計但尚未實作的開關（TODO）

| 開關 | 設計來源 | 類型（預計） | 預設值（預計） | 影響範圍 | 實作狀態 |
|------|----------|-------------|----------------|----------|----------|
| **GOV_ENFORCE_ENABLED** | `W5-A-RUNTIME-03-LIMITED-DENY_plan.md` §4.2 | CI env var | `0`（off） | 切換 Phase A（preview-only）↔ Phase B（actual blocking） | ⏳ **TODO** — 定義於設計文件，尚未在 CI 中實作 |
| **ENF_RULE_1_BLOCKING_ENABLED** | W5-D-CI-GAP-CHECKLIST G8 contingency | CI env var（預計） | `0`（off） | 僅控制 ENF-RULE-1 是否實際 deny (per-rule kill-switch) | ⏳ **TODO** — 僅在 G8 contingency 條件中提及，尚未設計實作細節 |
| **Blocking scope whitelist** | `W5-A-RUNTIME-03-LIMITED-DENY_plan.md` §3.2 | CI step condition（預計） | `eval-shadow-nightly` only | 限制 blocking 生效的 workflow / job / branch | ⏳ **TODO** — 設計已定義 scope 原則，未實作 |

### 1.4 開關間的相互影響

```
SHADOW_BATCH_DIR ─→ Shadow pipeline mode ─→ DRYRUN-LOG 的資料來源
                                              GOV-ENF-PREVIEW 的資料來源
                                                     │
                                                     ▼
                                        [TODO] GOV_ENFORCE_ENABLED
                                             ├ 0 (default) → preview only, exit 0
                                             └ 1 → L2 rules actually block pipeline
```

- 資料源開關（SHADOW_BATCH_DIR / pipeline mode）影響所有 downstream 步驟的輸入
- 治理步驟開關（continue-on-error）控制是否影響 pipeline 結果
- blocking 開關（GOV_ENFORCE_ENABLED, TODO）控制是否退出 preview 模式進入實際 deny

---

## 2. 常態操作模式

### 2.1 Normal Mode（預設 — 純觀察，不 blocking）

**適用場景**：日常運作。所有治理步驟僅觀察、記錄，不影響 pipeline 成敗。

**開關狀態**：

| 開關 | 值 | 說明 |
|------|-----|------|
| `SHADOW_BATCH_DIR` | `artifacts/eval` | 不變 |
| Shadow pipeline mode | 取決於是否有批次檔 | 若有真實批次，mode=shadow；否則 mode=fixture |
| `continue-on-error` | `true` on all GOV steps | 永遠安全 |
| `GOV_ENFORCE_ENABLED` | TODO: `0` (off) | 無 blocking，設計預設值 |
| `ENF_RULE_1_BLOCKING_ENABLED` | TODO: `0` (off) | 無 per-rule blocking |

**預期行為**：
1. nightly UTC 06:00 或手動觸發 `eval-shadow-nightly` job
2. fetch 步驟嘗試取得最新批次檔 → mode=shadow 或 mode=fixture
3. `[DRYRUN-LOG]` step：印 per-record 治理摘要（總數、match 率、unknown 佔比）
4. `[GOV-ENF-PREVIEW]` step：印 would_block / would_warn / would_noop 計數
5. 兩 step 皆 `exit 0` + `continue-on-error: true` → pipeline 永遠綠色

**維運檢查點（正常模式下的感興趣事項）**：
- `[SHADOW-PIPELINE] mode=fixture` 是否連續多日出現？（可能代表資料管線停滯）
- `[GOV-ENF-PREVIEW] would_block` 是否突然跳升？（可能代表 rule 或資料變異）
- `unknown` 佔比是否異常升高？（可能代表 schema 變更或新 edge case）

### 2.2 Normal Mode 操作步驟

```
操作目標：確認 nightly 治理鏈正常運作

Step 1: 登入 GitHub Actions → 找到最近一次 eval-shadow-nightly run
Step 2: 展開 [DRYRUN-LOG] step，確認有 [DRYRUN-LOG] event=summary 行
Step 3: 展開 [GOV-ENF-PREVIEW] step，確認有 [GOV-ENF-PREVIEW] event=summary 行
Step 4: 確認兩 step 皆綠色（exit 0）
Step 5: 粗略掃描 would_block 與 unknown 計數，與前次 run 對比有無異常跳升
```

---

## 3. Canary / 實驗操作模式

### 3.1 Canary Mode — 在特定 nightly 開啟 ENF blocking

**適用場景**：當需驗證某條 L2 rule 在真實資料上的 blocking 行為，但限於非關鍵路徑。
**前提條件**（參考 `W5-A-RUNTIME-03-LIMITED-DENY_plan.md` §3.2 與 G8）：
- Phase A preview 已運行 ≥N 次 nightly（建議 ≥7）
- 該 L2 rule（如 ENF-RULE-1）的 false positive 率已收斂到可接受閾值
- kill-switch 機制已在 Phase A 中驗證過至少一次正常運作

**開關狀態**（預計 — 待 GOV_ENFORCE_ENABLED 實作後方可使用）：

| 開關 | 值 | 說明 |
|------|-----|------|
| `GOV_ENFORCE_ENABLED` | `1`（on，僅限 nightly） | 啟用 L2 blocking |
| blocking scope | 限制為 `eval-shadow-nightly` job only | 不影響 PR / smoke 路徑 |
| `continue-on-error` | 保持 `true`（安全備援） | 即使 blocking step crash 仍不影響 pipeline |
| 非 L2 規則 | 維持 preview-only 行為 | 僅 L2 實際 deny |

**操作流程**（設計階段指引 — 實作後需更新為實際步驟）：

```
Step 1: 確認 canary 前的最後一次 preview run 的 would_block 為可接受範圍
Step 2: 在 GitHub repo settings 或 CI env 中設定 GOV_ENFORCE_ENABLED=1
         （此步驟需 git push 或 repo env var 變更，不是 workflow_dispatch）
Step 3: 手動觸發 eval-shadow-nightly (workflow_dispatch)
Step 4: 觀察 [GOV-ENF-PREVIEW] log 是否出現 🚫 ENFORCED 而非 ⚠ PREVIEW
Step 5: 若正常，觀察 N 次 nightly；若異常，立即 GOV_ENFORCE_ENABLED=0
Step 6: 紀錄 canary 結果（would_block 數量、false positive 與否）
```

### 3.2 手動觸發 Nightly 資料管道測試

**適用場景**：上傳新批次檔後，想立刻驗證 CI 能否正確讀取並產出治理報表。

```
Step 1: 將新批次檔命名為 shadow_batch_<YYYYMMDD>.jsonl
Step 2: 放到 SHADOW_BATCH_DIR (artifacts/eval/) 下
Step 3: 到 GitHub Actions → eval-gate-ci.yml → workflow_dispatch
Step 4: 觸發後，檢查 [SHADOW-PIPELINE] 是否印 mode=shadow 而非 mode=fixture
Step 5: 比對 [DRYRUN-LOG] event=summary 的記錄數是否與批次檔相符
```

### 3.3 Switching shadow data source (Upload new batch)

**適用場景**：取得新的 prod shadow 批次，希望 CI 下次 nightly 吃新資料。

```
Step 1: 確認批次檔格式與既有 k2_shadow_spool schema 相容
Step 2: 命名為 shadow_batch_<YYYYMMDD>.jsonl（日期需比現有檔案大，fetch 腳本吃最新的）
Step 3: 放置到 SHADOW_BATCH_DIR（目前為 artifacts/eval/）
Step 4: 下次 nightly (UTC 06:00) 或手動觸發後，CI 會自動切換到 mode=shadow
Step 5: 確認 log 中出現 [SHADOW-PIPELINE] mode=shadow batch=<datestamp>
```

---

## 4. 異常時的處置流程

### 4.1 場景 A：大量 ENF 出現 would_block，疑似誤殺

**徵兆**：`[GOV-ENF-PREVIEW] would_block` 計數突然從平常的個位數跳到數十或數百。

```
Step 1 — 確認是否為 rule 問題：
   查看最近一次 dryrun per-record JSONL（observability/dryrun/ 下最新檔案）
   找出觸發 would_block 的記錄的共通模式（相同的 rule id? 相同的 error_type? 相同的 tag?）
   若大量記錄的觸發原因相同 → 可能是 rule threshold 或條件太寬

Step 2 — 確認是否為資料問題：
   檢查最近批次檔（shadow_batch_<latest>.jsonl）的記錄數與內容是否異常
   檢查 [SHADOW-PIPELINE] log 行：mode=shadow 還是 mode=fixture？
   若 mode=fixture 但以前是 mode=shadow → 資料管線中斷，所有資料來自 fixture
   若批次檔記錄數突然增加百倍 → 資料源可能有變化

Step 3 — 立即停止 blocking（若 blocking 已啟用 → TODO 實作後）：
   設置 GOV_ENFORCE_ENABLED=0
   下一個 CI run 即恢復為 preview-only（continue-on-error: true）
   不需要 git push 修改 YAML

Step 4 — 記錄 false positive：
   在 DEBT_LOG 或等價位置記錄：rule id、觸發條件、affected records、timestamp
   參考 ENF-B5 流程：不直接關閉 rule，而是記錄後檢討

Step 5 — 調整 rule：
   若確認是 rule 過寬 → 調整 threshold 或條件
   修改後的 rule 回到 Phase A 重新 preview（GOV_ENFORCE_ENABLED=0）
   觀察 ≥N 次 nightly 確認 FP 不再發生
   經 reviewer gate 後重新開啟 blocking
```

### 4.2 場景 B：Nightly pipeline 因 GOVERNANCE step 變紅

**前提**：當前所有 GOV step 均為 `continue-on-error: true`，正常情況下 pipeline 不應因 GOV step 變紅。若變紅，代表 wrapper crash 或 CI 基礎設施問題。

```
Step 1 — 確認是哪個 step 紅：
   展開紅色的 step，查看 error 訊息
   [DRYRUN-LOG] 紅 vs [GOV-ENF-PREVIEW] 紅？還是 fetch 步驟紅？

Step 2 — 常見原因：
   - 「artefact not found」或「FileNotFoundError」→ 資料管線路徑問題
   - Python import error → wrapper 或 dependency 變更
   - Timeout → 批次檔過大或 runner 資源不足

Step 3 — 立即處置：
   若為資料路徑問題 → 重新上傳最新批次檔，手動觸發重跑
   若為 wrapper crash → 可暫時關閉該 step（commment out），待修復後重新啟用
   若為 runner 問題 → 重新觸發 pipeline（GitHub Actions 偶發性錯誤）

Step 4 — 書面記錄：
   建立 ticket 追蹤 root cause
   若為重複性問題 → 考慮加 alert 或 monitoring
```

### 4.3 場景 C：Silent fallback（連續多日 mode=fixture 但預期應有真實資料）

**徵兆**：查看最近 N 次 nightly run log，`[SHADOW-PIPELINE] mode=fixture` 持續出現。

```
Step 1 — 確認是資料未上傳還是 fetch 腳本有問題：
   手動登入 CI runner 或本機，執行 scripts/fetch_latest_shadow_batch.sh
   看 log 是否提示「no_batch_found」或「permission_denied」或其他錯誤

Step 2 — 若是資料未上傳：
   追問負責人（誰最近上傳了批次檔？）
   確認 prod shadow 管線仍在產出資料
   手動上傳最新批次檔到 SHADOW_BATCH_DIR

Step 3 — 若是 fetch 腳本問題：
   檢查 SHADOW_BATCH_DIR 路徑是否正確
   檢查批次檔命名格式是否符合 shadow_batch_<YYYYMMDD>.jsonl

Step 4 — 確認恢復：
   手動觸發一次 eval-shadow-nightly (workflow_dispatch)
   檢查 [SHADOW-PIPELINE] mode=shadow 恢復正常
```

### 4.4 場景 D：Fatal — blocking 誤擋生產流量（Phase B 啟用後，TODO）

**此開關尚未實作。以下為設計階段的處置流程（參考 `W5-A-RUNTIME-03-LIMITED-DENY_plan.md` §4.3）。**

```
Step 1 — 偵測：某個 CI run 因 enforcement 而 fail，經手動確認為 false positive
Step 2 — 切換 kill-switch：設置 GOV_ENFORCE_ENABLED=0，下個 CI run 恢復 log-only
Step 3 — 記錄 false positive：在 DEBT_LOG 記錄 rule id、inputs、timestamp
Step 4 — 調整 rule：檢討 threshold / 分類（是否應降回 L1 或 L0）
Step 5 — 回 Phase A：修改後的 rule 先以 preview 模式跑 N 次，確認 FP 不再發生
Step 6 — 重新開啟：經 reviewer gate 後，重新開啟 enforcement
```

---

## 5. 快速參考卡（Quick Reference）

### 5.1 開關一覽表（摘要）

```
開關                          位置                         預設值      可動態改？
───────────────────────────── ─────────────────────────── ────────── ─────────
SHADOW_BATCH_DIR               CI env (eval-gate-ci.yml)    artifacts/eval  需 git push
Shadow pipeline mode           auto by fetch script         fixture fallback 自動
eval-shadow-nightly cron        on.schedule                  0 6 * * *     需 git push
workflow_dispatch              GitHub UI                    N/A           可（手動）
continue-on-error (GOV steps)  CI step config               true          需 git push
───────────────────────────── ─────────────────────────── ────────── ─────────
GOV_ENFORCE_ENABLED (TODO)     CI env var (未實作)         0 (off)       預計無需 git push
ENF_RULE_1_BLOCKING (TODO)     CI env var (未實作)         0 (off)       預計無需 git push
```

### 5.2 常見 CI log marker 索引

```
功能                             Log Marker                        在哪個 step
──────────────────────────────  ────────────────────────────────── ────────────────────
資料管線模式（real vs fixture）    [SHADOW-PIPELINE]                  Fetch step
治理乾跑摘要（per-record 統計）     [DRYRUN-LOG] event=summary          DRYRUN-LOG step
Enforcement preview（模擬 deny）  [GOV-ENF-PREVIEW] event=summary      GOV-ENF-PREVIEW step
Enforcement blocking（實際 deny） [GOV-ENF-PREVIEW] 🚫 ENFORCED        GOV-ENF-PREVIEW step (Phase B)
異常跳過（artefact 不存在時）      [GOV-ENF-PREVIEW] [WARN] event=skip  GOV-ENF-PREVIEW step
```

### 5.3 應急決策樹

```
Nightly CI 出現異常 GOV log？
├─ pipeline 變紅？
│  └─ ⚠ 目前所有 GOV step 為 continue-on-error: true，理論上不應變紅
│     → 檢查是否為 fetch 或 infra 層級錯誤（disc I/O、timeout、runner 崩潰）
│     → 參見 §4.2 場景 B
├─ would_block 突然暴增？
│  ├─ blocking 啟用中？ → GOV_ENFORCE_ENABLED=0（第一個動作！）
│  └─ blocking 未啟用 → 先確認 rule 問題還是資料問題（§4.1 Step 1-2）
└─ mode=fixture 連續出現？
   └─ 檢查資料管線來源（§4.3）
```

---

## 6. 未來擴展建議

以下為 Phase 3 及之後可能需要的更細粒度控制開關，目前尚未設計或實作。

| 建議開關 | 用途 | 建議實作時機 |
|----------|------|-------------|
| **`GOV_L1_ENFORCE_ENABLED`** | 獨立控制 L1 規則（advisory）是否進 warning | 當 Phase B blocking 穩定後，需要微調 L1/L2 行為時 |
| **`GOV_SCOPE_WORKFLOW`** | 控制 blocking 生效的 workflow（逗號分隔列表） | 當 blocking 擴展到 PR＋nightly＋release 多條路徑時 |
| **`GOV_SCOPE_BRANCH`** | 控制影響的 branch regex | 同上，細化 scope 控制 |
| **`ENF_<RULE_NAME>_ENABLED`** | per-rule kill-switch，可獨立開關每條 L2 rule | 當 L2 rule 數量 > 3 時 |
| **`SHADOW_BATCH_FALLBACK_WARN`** | 控制 fixture fallback 時是否發 alert（預設 false → true） | 當資料管線穩定運轉後，fixture 應視為異常 |
| **`GOV_DEBUG_MODE`** | 印更詳細的 per-record 判定過程（供 debug） | 當 rule 行為難以從 summary log 推斷時 |
| **`GOV_DRYRUN_SAMPLE`** | 在 blocking 模式下僅對部分記錄執行 dry-run（取樣） | 當資料量變大且 blocking 穩定後 |

### 開關設計原則（建議沿用 ENF-B4）

- **優先使用 CI env var**，而非 workflow YAML 條件（可動態修改，無需 git push）
- **預設關閉**（opt-in），避免未經討論的 blocking 影響生產
- **每次 run 印開關狀態** — `[GOV-ENF-PREVIEW] ENFORCEMENT: ACTIVE (GOV_ENFORCE_ENABLED=1, scope=nightly)`
- **per-rule > 全域** — 若同一個 workflow 中有多條 L2 規則，應支援逐條獨立控制

---

## 附錄 A — 文件對應關係

| 文件 | 與本 runbook 的關係 |
|------|---------------------|
| `W5-A-RUNTIME-03-LIMITED-DENY_plan.md` | kill-switch、ENF-B1~B6、rollback 流程的設計來源。本 runbook §1.3 直接引用其設計 |
| `W5-A-RUNTIME-03-ENF-PREVIEW_BRIEF_TASK_FOR_CURSOR.md` | Phase A preview step 的行為定義。本 runbook §1.2 引用其 continue-on-error 設計 |
| `W5-A-RUNTIME-03-CI-DATA-PIPELINE-DESIGN-01.md` | shadow pipeline mode 的設計來源。本 runbook §1.1 引用 fetch-fallback 機制 |
| `W5-A-RUNTIME-03-CI-DATA-PIPELINE-IMPL-01.md`（設計內嵌） | SHADOW_BATCH_DIR、fetch 腳本、mode=shadow/mode=fixture 的實作細節 |
| `W5-D-CI-GAP-CHECKLIST-01.md` | G8（ENF-RULE-1 尚未 blocking）的確認。本 runbook §1.3 的 TODO 來源之一 |
| `W5-A-RUNTIME-PLAYBOOK.md` | dry-run 治理模式的邊界與 AC 定義。本 runbook 不修改 PLAYBOOK，僅在 §1.4 描述開關間關係 |

---

## 附錄 B — 版本歷史

| 版本 | 日期 | 作者 | 變更說明 |
|------|------|------|---------|
| v0.1 | 2026-05-31 | W5-D-CONTROL-PLANE-RUNBOOK-01 | 首版 runbook。盤點所有已知開關（6 已實作 + 3 TODO），定義 4 種異常場景的處置流程 |
