# W5-A-RUNTIME-01-DRYRUN — Wave 5-A 第一條 runtime 線（read-only dry-run 設計）

> **票號**：W5-A-RUNTIME-01-DRYRUN-PLAN-01（只讀方案卡）
> **位置**：W5-A 軸的第一條 runtime 線 — **但不寫任何 CI / pipeline state**
> **範圍**：只讀現有 artefact + 產出觀察型報表（新 JSONL / markdown），不修改任何既有檔案
> **不處理**：CI workflow 變更、既有程式碼修改、gate verdict 寫入、任何 prod-equivalent 狀態變更
> **先決**：W4-A-PILOT-RELEASE-STREAM-v0.1（既有底盤）、Wave 4-A gate checklist / rollout trace 等既有 artefact

---

## (1) 目的與範圍

### 1.1 為什麼需要這條 dry-run 線

W5-A 的最終目標是在 prod CI 中嵌入真正的 K-2 rollout（shadow → canary → promote）。但直接從「規劃」跳到「寫入 prod CI」風險太高 — 因為 Wave 4-A 的治理邏輯（gate verdict、checklist、rollout 條件等）從未被放在「一晚多筆 shadow eval 資料」的真實場景下系統性驗證過。

**W5-A-RUNTIME-01-DRYRUN 的角色**：在安全、read-only 的環境中，驗證 Wave 4-A 設計在真實資料規模下的行為。具體來說：

- **讀取**：現有 eval-shadow-nightly 產出的 shadow_eval_results、shadow_ibridge_records、gate verdict、eval_stats summary 等 artefact。
- **分析**：對每一條記錄，用簡化治理規則推算出「理想 verdict bucket」（allow / warn / deny / needs_review），與目前 gate 的「實際 verdict」對照，產出差異報告。
- **產出**：新建立的可觀察報表 artefact（在 `observability/` 或 `artifacts/` 下新子目錄），純觀察，不驅動任何 pipeline 步驟。

**不是做**：本票不修改任何現有 CI / gate 行為。不寫入 prod 狀態。不改變任何既有 artefact 內容。

### 1.2 範圍邊界

| 維度 | 範圍內 | 範圍外 |
|------|--------|--------|
| 資料讀取 | shadow_eval_results、shadow_ibridge_records、eval_export JSONL、eval_stats snapshots、gate verdict 等 artefact（只讀） | ibridge_records.jsonl 原始 fixture、production database 或 logging 系統 |
| 資料寫入 | 新建立的 dry-run 報表 JSONL / markdown（如 `observability/dryrun/` 下） | 任何既有 JSONL / md / CI 檔案；任何 git commit 到 CI 設定 |
| 治理邏輯 | 簡化治理規則（基於 W4-A gate checklist / G10 rulebook 推導） | 完整的 deny engine runtime（G10-2 T3） |
| 後續升級 | 本票產出的報表格式可被 RUNTIME-02 直接消費 | RUNTIME-02 的「寫入 CI logging / metrics」行為 |

---

## (2) 輸入 / 輸出設計

### 2.1 輸入 artefact 列表

| 抽象名稱 | 內容說明 | 用途 |
|---------|---------|------|
| `shadow_eval_results.latest.jsonl` | Nightly shadow eval 的輸出：每條記錄包含 gate_result、metrics、semgrep_count、tags 等 | 作為「實際 verdict」的來源 |
| `shadow_ibridge_records.latest.jsonl` | Shadow ibridge 原始記錄（task_id、trace_id、case_name、content 等） | 作為記錄的原始內容參考 |
| `eval_export.jsonl`（最新 snapshot） | Eval export 輸出：gate_result、source_ref、schema_version | 補充 verdict 資訊 |
| `eval_stats.json` 或等價 snapshot | Stats 統計：counts / ratios / tag_counts / suggest_ci_thresholds | 作為批次級對照 |
| `gate_verdict_summary.jsonl` 或等價 | Gate 決策摘要：實際的上層 verdict（block / warn / allow） | 作為「理想 verdict」的對照對象 |

> **註**：以上名稱均為抽象描述。Cursor 在實作時需用 `find` / `ls` 確認實際路徑與檔名。dry-run CLI 應支援參數化指定輸入路徑。

### 2.2 輸出 artefact 形式

dry-run CLI 產出兩種報表：

**A. Per-record 比較 JSONL**（`observability/dryrun/<timestamp>_per_record.jsonl`）

每條記錄至少含：

```json
{
  "task_id": "...",
  "timestamp": "ISO8601",
  "dryrun_rule": "gate_ok_score_high | gate_ok_score_low | gate_fail_semgrep | needs_review | ...",
  "actual_verdict": "allow | warn | deny | needs_review",
  "ideal_verdict": "allow | warn | deny | needs_review",
  "verdict_match": true | false,
  "metrics": { ... },
  "source_ref": { ... }
}
```

**B. 摘要對照 markdown**（`observability/dryrun/<timestamp>_summary.md`）

包含：
- 總記錄數 / verdict_match 數量與比例
- 按 dryrun_rule 分組的統計（各 rule 觸發了多少條、match 率）
- 差異記錄清單（actual ≠ ideal 的記錄，列出 task_id / timestamp / 差異原因）
- 治理風險標記（例如：「X 條記錄 actual=allow 但理想應該 deny — 可能代表 gate 規則太寬鬆」）
- **免責聲明**：清楚寫明「本報表為 read-only dry-run 產出，不代表已啟用任何 gate enforcement」

---

## (3) 不變條件與風險 guard

### 3.1 不變條件（施工與驗收共用）

| # | 條件 | 違反方式 | 防止方式 |
|---|------|---------|---------|
| I1 | 不修改任何現有 eval / export / stats / gate 程式碼邏輯 | 在已有檔案中插入 import、修改函數 | CLI 是全新檔案（module），不 patch 既有 code |
| I2 | 不更改任何既有 JSONL / md 檔案內容 | 在原始 artefact 上追加/修改行 | dry-run 只讀取 + 僅寫新目錄 |
| I3 | 不修改 CI workflow 檔案（`.github/workflows/**`） | 編輯 workflow YAML | 禁止寫入任何 `.github/` 路徑 |
| I4 | 不寫入 prod-equivalent 狀態（gate verdict、PR status、CI check） | 用 API 或檔案寫入 CI gate 決策 | 輸出僅為新 JSONL / md 報表，不與 CI 綁定 |
| I5 | 不改變既有測試或 fixture | 修改 fixture JSONL / 測試斷言 | 只讀 fixture，不寫入 fixture 目錄 |

### 3.2 風險 guard

| # | 風險 | 影響 | 緩解 |
|---|------|------|------|
| R1 | dry-run 報表中的「ideal_verdict」被團隊誤解為「已生效的 enforce 標準」 | 開發者可能以為 dry-run 的 deny 已被 gate 強制執行 | 報表頭部 + CLI 輸出首行均顯示「⚠ DRY-RUN — 不影響任何 CI/pipeline 決策」 |
| R2 | dry-run 規則太過簡化，導致大量 false positive「差異記錄」 | 報表淹沒真實差異 | 在簡化治理規則定義中補充「本規則為近似推導，不代表真實 G10 rulebook 精確度」；支援 `--min-score-threshold` 等參數調整 |
| R3 | dry-run 產出大量報表檔案，累積後消耗磁碟 | 雜亂的 artifact 目錄 | 命名規則含 timestamp；可選支援 `--output-dir` 參數；後續由 W5-A-DOCSYNC 票建立保留策略 |
| R4 | 治理規則無法完整覆蓋 edge case（如 async ibridge、partial failures） | 部分記錄的 ideal_verdict 為 `unknown` | 明確將 `unknown` 設為合法值，且在摘要中統計 `unknown` 佔比 |

---

## (4) 治理規則設計（dry-run 專用）

dry-run CLI 使用一套簡化治理規則來計算每條記錄的 `ideal_verdict`。這些規則是 W4-A gate checklist / G10 rulebook 的近似推導，**不是**正式 enforcement 邏輯。

### 4.1 規則概要

```text
規則 1（gate_ok_score_high）：
  IF gate_result == "ok" AND metrics.score >= 0.7 AND semgrep_count == 0
  → ideal_verdict = "allow"

規則 2（gate_ok_score_low）：
  IF gate_result == "ok" AND (metrics.score < 0.7 OR semgrep_count > 0)
  → ideal_verdict = "warn"     // 分數低但 gate 仍 allow，建議關注

規則 3（gate_fail_deny）：
  IF gate_result == "fail" AND semgrep_count > 0
  → ideal_verdict = "deny"     // 明確應阻擋

規則 4（gate_fail_needs_review）：
  IF gate_result == "fail" AND semgrep_count == 0
  → ideal_verdict = "needs_review"  // fail 但非 semgrep 問題，需要人工判斷

規則 5（edge_unknown）：
  IF 上述規則無法匹配（例如 missing metrics、unexpected gate_result）
  → ideal_verdict = "unknown"
```

### 4.2 規則的已知限制

- 不考量 tag 層級 rule（例如 `security:critical` 自動 deny）— 如後續需要可在 RUNTIME-02 擴展
- 不考量累計趨勢（例如「3 天內連續 warn → escalate」）
- `allow` 不等於「可以 promote」，僅代表該條記錄在 dry-run 層級無明顯問題
- 規則不涉入 rollout 階段的 cohort 決策

---

## (5) 後續擴展 slot

| 後續票 | 預期行為 | 與本票的關係 |
|--------|---------|-------------|
| **W5-A-RUNTIME-02**（Logging-first runtime） | 在單一 prod-equivalent CI workflow 中加入只寫 logging / metrics 的輕量 runtime。仍不啟用 gate deny，但開始在 CI 中產出可索引的 metrics 記錄。 | 可使用 RUNTIME-01 的治理規則 + 報表格式作為 log output schema；RUNTIME-01 的報表可作為 RUNTIME-02 上線前的 baseline |
| **W5-A-RUNTIME-03**（Limited gate deny） | 在有限 scope（如特定 tag / 特定 threshold）下啟用真正的 gate deny，並引入 override（allowlist + reason）/ rollback（觸發即 cohort→0）機制。 | RUNTIME-01/02 的實踐經驗可作為 RUNTIME-03 的 rule tuning 與 override 設計參考 |
| **W5-A-COHORT-DESIGN** | 多 cohort 階梯策略表 + traffic routing 文檔 | 獨立票，與 RUNTIME-01 無直接依賴 |
| **W5-A-DOCSYNC-01** | K-2 rollout 擴面的 doc-sync 票：保留策略、artefact 管理 SOP | RUNTIME-01 產出的報表管理（保留/清理策略）由本票定義 |

> **重要**：後續擴展票**不在**本票 W5-A-RUNTIME-01-DRYRUN 的 scope 內。本票只做讀取 + 新報表輸出。RUNTIME-02 須另行開票，經尚書省 gate 後方可開始。

---

## (6) 交付形式

本票的 runtime 交付物：

| 交付物 | 說明 | 位置（抽象） |
|--------|------|-------------|
| **dry-run CLI（Python module + entrypoint）** | 可被 `python -m tools.dryrun` 或 `python tools/dryrun.py` 呼叫的 CLI，支援 `--input-dir` / `--output-dir` / `--min-score` 等參數 | `tools/dryrun/` 或 `observability/dryrun/` 下新 module |
| **Per-record 比較報表（JSONL）** | 前述 2.2-A 格式 | `observability/dryrun/<timestamp>_per_record.jsonl` |
| **摘要報表（markdown）** | 前述 2.2-B 格式 | `observability/dryrun/<timestamp>_summary.md` |
| **基本測試覆蓋** | 至少一組 unit test 確認 CLI 在黑箱模式下產出預期格式 | `tests/test_dryrun_*` |
| **文檔說明** | 在 `observability/dryrun/README.md` 或 `docs/` 下說明 dry-run 線的用途、限制、後續擴展 | `observability/dryrun/README.md` |

---

## 附錄 A — 檔案路徑慣例（抽象）

| 抽象路徑 | 角色 | 讀/寫 |
|---------|------|-------|
| `artifacts/eval/shadow_eval_results.latest.jsonl` | Shadow eval 輸出（實際可能為 `nightly-*` 或 `latest`） | 只讀 |
| `artifacts/eval/shadow_ibridge_records.latest.jsonl` | Shadow ibridge 輸出 | 只讀 |
| `artifacts/eval/eval_*` | Eval export / stats 系列 | 只讀 |
| `observability/dryrun/` | 新建立的 dry-run 報表目錄 | 寫（新建） |
| `tests/` | 測試目錄 | 新增測試檔案 |
| `tools/dryrun/` 或等價 | dry-run CLI 原始碼 | 新增 module |
| `docs/` 或 `observability/` | 文檔說明 | 新增說明檔案 |
| `.github/workflows/**` | CI workflow — **禁止觸碰** | 不讀不寫 |

## 附錄 B — 真實風險評估

```text
高風險情況（不存在）         目前實際情況（極低風險）
─ ─ ─ ─ ─ ─ ─ ─              ─ ─ ─ ─ ─ ─ ─ ─
dry-run 修改既有 CI 行為    ✓ 只讀 artefact，不碰 CI workflow
dry-run 寫入 gate verdict   ✓ 輸出僅為新檔案，不連接到 CI gate
dry-run 影響 production     ✓ 完全隔離在 observability/dryrun/ 下
dry-run 規則取代 G10        ✓ 明確標示「近似推導，非正式 rulebook」
dry-run 消耗大量資源        ✓ 只處理現有 artefact，無重計算或 API call
```
