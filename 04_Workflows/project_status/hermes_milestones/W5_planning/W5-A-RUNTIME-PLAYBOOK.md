# W5-A-RUNTIME-PLAYBOOK — Read-Only Dry-Run Runtime 治理模式

> **條目類型**：治理 / PLAYBOOK / 可重複套用的 workflow pattern
> **源頭**：W5-A-RUNTIME-01-DRYRUN（plan + brief + Cursor 實作）
> **版本**：v0.1（2026-05-31，基於首次實戰抽象）
> **用途**：定義「read-only dry-run runtime 線」的標準結構、邊界、AC，讓未來類似工作可以直接套用這個 pattern，不需從零設計。
> **參考文件**：
>   - `W5-A-RUNTIME-01-DRYRUN_plan.md`（完整設計稿，含治理規則細節與後續擴展）
>   - `W5-A-RUNTIME-01-DRYRUN_BRIEF_TASK_FOR_CURSOR.md`（具體實作 brief）
>   - `W5_TICKET_TEMPLATES.md`（Wave 5 常見票模板）

---

## 1) 條目名稱（Pattern Name）

**`W5-A-RUNTIME-01-DRYRUN` — read-only runtime-first pattern**

**短名**：dry-run runtime 線 / read-only observability-first runtime

> 這是治理/PLAYBOOK 層的 pattern，不是 runtime 票號。未來任何 repo / workflow 要導入類似 dry-run 時，引用此 pattern 名稱即可。

---

## 2) 適用場景（When to use）

符合以下任一條件時，**必須先走一條 read-only dry-run runtime 線**，不得跳過直接進入 logging/deny runtime：

1. **治理規則尚未 ready** — 新的規則或 rulebook 仍在調整階段（threshold、bucket、edge case），尚未穩定到可以直接寫入 CI / gate 邏輯。dry-run 可以在安全環境中先觀察規則在真實資料上的行為。
2. **既有 artefact 管線存在但無系統性觀察視圖** — shadow eval / gate / export 等資料已經在跑，但從未以「per-record 對照 + summary 統計」的方式產出結構化報表。dry-run 填補這個觀測空白，讓團隊首次拿到 baseline。
3. **風險偏好是「先觀察，再介入」** — 團隊主張：在任何自動 deny / override / rollback 機制啟動之前，必須先有最少一輪的 read-only 觀察，確認治理規則在真實規模下的行為（match ratio、false positive rate、edge case 佔比）。
4. **跨 repo 或跨 workflow 移植時** — 把某個流程的治理邏輯搬到另一個 repo 時，先在新的 repo 做 dry-run 對照，確認 artefact schema 相容且規則能正確觸發，再決定是否移入正式 CI。
5. **規則調整後需回測 baseline** — 當 rule threshold 或 bucket 定義變更時，dry-run 可以對照新舊規則的 verdict 分布，快速評估變動的影響面。

**不適用**：已確認規則 ready 且 CI 流程已有完善的 error budget / rollout plan / rollback 機制時，可以直接從 logging-first runtime 起步。

---

## 3) 標準輸入 / 輸出（Inputs / Outputs）

### 3.1 標準輸入 — 抽象 artefact 類型

| 抽象名稱 | 內容說明 | 在 RUNTIME-01 的具體對應 |
|---------|---------|--------------------------|
| `shadow_eval_results.latest` | Nightly shadow eval 的 per-record 輸出：gate_result、metrics、tags 等 | `artifacts/eval/shadow_eval_results.latest.jsonl` 或 `nightly-*` |
| `shadow_ibridge_records.latest` | Shadow 原始記錄：task_id、trace_id、content 等 | `artifacts/eval/shadow_ibridge_records.latest.jsonl` |
| `eval_export.latest` | Eval export 輸出：gate_result、source_ref、schema_version | `artifacts/eval/eval_*.jsonl`（最新 snapshot） |
| `eval_stats.snapshot` | 批次級統計：counts、ratios、tag_counts | `artifacts/eval/eval_stats.json` 或等價 |
| `gate_verdict_summary` | Gate 決策摘要：實際的上層 verdict（block / warn / allow） | `artifacts/eval/gate_verdict_summary.jsonl` 或 checklist |

> **抽象原則**：以上五類是「一組 artefact 管線」的通用抽象。新專案在套用時，走一遍 `find` / `ls` 確認實際路徑與格式，然後把抽象路徑對映到實際檔案即可。不需要糾結名稱完全一致。

### 3.2 標準輸出 — 三類交付物

1. **Per-record 比較 JSONL**（`observability/dryrun/<timestamp>_per_record.jsonl`）
   - 每條記錄至少含：`task_id`、`timestamp`、`dryrun_rule`、`actual_verdict`、`ideal_verdict`、`verdict_match`、`metrics snapshot`、`source_ref`
   - 欄位名稱應與下游（RUNTIME-02+）的 log schema 保持相容

2. **摘要對照 markdown**（`observability/dryrun/<timestamp>_summary.md`）
   - 總記錄數 / verdict_match 數量與比例
   - 按 dryrun_rule 分組的統計（各 rule 觸發了多少條、match 率）
   - 差異記錄清單（actual ≠ ideal 的記錄清單）
   - 治理風險標記（例如「X 條記錄 actual=allow 但理想應該 deny」）
   - 免責聲明（⚠ DRY-RUN — 不影響任何 CI/pipeline 決策）

3. **CLI stdout（可選，但建議保留）**
   - 固定首行：「⚠ DRY-RUN — 不影響任何 CI/pipeline 決策」
   - 結束時：簡短統計（總數、match 率、unknown 佔比）
   - 不能是空的或純終端格式（必須可被 script 擷取）

---

## 4) 邊界（Boundaries）

這是 dry-run pattern 的核心約束。**任何 dry-run 票違反以下任一條，就不是 pure dry-run，應視為越界**：

| # | 邊界 | 說明 | 違反實例 |
|---|------|------|---------|
| B1 | **僅新增檔案** | 所有交付都是全新檔案（CLI module、output dir、test、README）。不修改任何既有程式的邏輯行。 | 修改既有 `eval_exporter.py` 加入 dry-run 模式 |
| B2 | **不修改 CI workflow** | 不編輯 `.github/workflows/` 或等價的 CI 配置。dry-run CLI 是手動執行或獨立 cron，不嵌入任何產線 CI job。 | 在 CI YAML 中追加 dry-run step |
| B3 | **不修改既有 artefact** | 不寫入、覆蓋、刪除任何既有的 JSONL / md / yml 內容。所有輸出寫到新建立的路徑（如 `observability/dryrun/`）。 | 在原始 `eval_export.jsonl` 上追加 dry-run 欄位 |
| B4 | **不寫入 prod-equivalent 狀態** | 不寫入 gate verdict、PR 狀態、CI check、pipeline trigger、database。輸出僅為本地檔案。 | dry-run CLI 上傳 verdict 到 CI check API |
| B5 | **不改變既有測試或 fixture** | 不修改既有測試斷言、不修改 fixture JSONL。唯獨可以新增測試檔案來驗證 dry-run CLI 本身。 | 修改 `test_eval_exporter.py` 以配合 dry-run |
| B6 | **CLI 首行 + 報表頭部須有 DRY-RUN 免責** | 任何運行路徑都要讓使用者明確知道這是觀察用，不是正式 gate。 | CLI 無任何 DRY-RUN 文字 |
| B7 | **不修改既有 plan / BRIEF 原文** | 第一條 dry-run 線的 PLAYBOOK 條目可以引用既有文件，但不可改寫它們的原文。 | 改寫 `W5-A-RUNTIME-01-DRYRUN_plan.md` 的 scope 定義 |

---

## 5) 治理規則模式（Governance Pattern）

### 5.1 五 bucket 近似模型

dry-run CLI 使用一組簡化治理規則（約 5 條規則），將每條記錄分類到五個 bucket 之一：

| Bucket | 語意 | 觸發條件（範例） | 備註 |
|--------|------|-----------------|------|
| `allow` | 完全沒問題 | gate_result=ok、score≥threshold、無 semgrep | 最低風險 |
| `warn` | 有輕微問題但 gate 仍放行 | gate_result=ok、score<threshold 或 semgrep>0 | 需要注意但不阻塞 |
| `deny` | 明確應阻擋 | gate_result=fail、有 semgrep 或其他明確失敗信號 | 高風險 |
| `needs_review` | 無法自動判定 | gate_result=fail 但非 semgrep（需人工判斷） | 中等風險 |
| `unknown` | 資料不足以判定 | 規則無法匹配（missing metrics、unexpected 欄位） | 系統性邊界 |

### 5.2 設計原則

- **近似，非精確**：這些規則是真實 rulebook（如 G10）的近似推導，在 README、報表、CLI 首行三處都有免責聲明，明確標示「非正式 enforcement 標準」。
- **per-record 對照**：每條記錄同時包含 `actual_verdict`（真實 gate 怎麼判）和 `ideal_verdict`（dry-run 規則認為應該怎麼判），**verdict_match** 欄位直接標示是否一致。這是決定性的治理差異分析工具。
- **edge_unknown 出口**：任何無法匹配的記錄都落到 `unknown` bucket，不會被默默忽略。summary 中統計 unknown 佔比，作為規則覆蓋率的客觀量化指標。
- **可調 threshold**：支援 `--min-score-threshold` 或等價 CLI 參數調整規則邊界，但不在這個階段啟用 deny 或任何 side effect。
- **與正式 gate 隔離**：規則實作在全新 module（如 `tools/dryrun/`），不與既有 gate engine 共用程式碼。未來要正式化時，可以從這裡複製規則邏輯到正式 engine，但不會發生「無意間改到 gate 行為」的風險。

### 5.3 差異分析的實戰價值

per-record 對照報表的核心產出是**差異清單** — 那些 `actual ≠ ideal` 的記錄。這些記錄的典型分析路徑：

- actual=allow 但 ideal=deny → 現有 gate 可能太寬鬆（false negative）
- actual=deny 但 ideal=allow → 現有 gate 可能太嚴格（false positive）
- actual=warn 但 ideal=needs_review → 需要人工確認的灰色地帶
- `unknown` 佔比過高 → 規則覆蓋率不足，需要擴展規則

這些差異分析是 RUNTIME-02（logging-first runtime）的 rule tuning 依據，也是 RUNTIME-03（limited deny）的 override 設計參考。

---

## 6) 驗收條件（Standard AC — AC-DRY 系列）

任何遵循此 PLAYBOOK 的 dry-run runtime 票，應以以下 6 條為驗收標準。這些 AC 跨 repo / 跨 workflow 通用，僅 artifact 名稱需按實際專案調整。

### AC-DRY-1：可呼叫的 dry-run 入口

- [ ] 存在可被 `python -m <module>` 或腳本直接執行的 CLI 入口
- [ ] 在本地成功讀取現有 artefact 並產出報表
- [ ] CLI 支援參數化指定輸入/輸出路徑（如 `--input-dir` / `--output-dir`）

### AC-DRY-2：per-record 報表 + summary 報表資訊齊全

- [ ] Per-record JSONL 每條記錄至少含：`task_id`、`actual_verdict`、`ideal_verdict`、`verdict_match`、`dryrun_rule`
- [ ] Summary markdown 至少含：總記錄數、match 比例、按 rule 分組統計、差異清單
- [ ] JSONL 和 markdown 路徑均在新建的輸出目錄下，不與既有 artefact 混雜

### AC-DRY-3：規則覆蓋所有關鍵 bucket，並有 edge_unknown 出口

- [ ] 簡化治理規則已實作，至少覆蓋 allow / warn / deny / needs_review 四種判定
- [ ] 存在 `unknown` 或等價的 edge case 出口（規則無法匹配時不崩潰）
- [ ] Summary 報表中統計 `unknown` 佔比

### AC-DRY-4：僅新增檔案，未改既有程式碼 / CI / artefact / 測試

- [ ] `git diff --stat`（或等價 diff 指令）確認僅新增檔案，無既有檔案修改
- [ ] 確認 `.github/workflows/`（或等價 CI 配置路徑）未被寫入
- [ ] 確認所有既有 artefact（JSONL / md / yml）未被覆寫或追加

### AC-DRY-5：測試通過（至少一組 unit）

- [ ] 至少一組 unit test 通過（可用 mock 輸入或 fixture 級資料）
- [ ] 測試不依賴真實 artefact 路徑存在
- [ ] 測試確認 CLI 在黑箱模式下產出預期格式

### AC-DRY-6：免責聲明明確

- [ ] CLI stdout 首行為「⚠ DRY-RUN — 不影響任何 CI/pipeline 決策」
- [ ] 每份 summary markdown 報表頭部有相同的免責文字
- [ ] README（若新增）明確說明「本 dry-run CLI 為觀察用，非正式 gate enforcement」

---

## 7) 如何沿用這個 pattern 到其他 repo / workflow（How to apply）

### 7.1 五步沿用流程

當新的專案 / repo / workflow 需要導入 read-only dry-run runtime 線時：

```
Step 1 — Mapping：走一遍既有 artefact 盤點
    在新 repo 中執行 find/ls 確認以下五類 artefact 的實際路徑與格式：
      ① shadow eval results（或等價的 per-record gate 結果）
      ② shadow/raw records（或等價的原始記錄）
      ③ export / snapshot results（或等價的結構化輸出）
      ④ stats / summary（或等價的批次級統計）
      ⑤ gate verdict / checklist（或等價的決策摘要）
    將抽象名稱映射到實際檔案路徑與 JSON 欄位結構。
    重點確認：新 repo 的 artefact 是否已有足夠完整的健欄位來推導 verdict bucket。

Step 2 — 簡化規則推導：
    根據新 repo 的既有 rulebook / checklist，推導出 4–5 條簡化規則，
    近似對映到 allow / warn / deny / needs_review / unknown 五 bucket。
    保留 edge_unknown 出口。

Step 3 — 產出 plan + BRIEF：
    按照這個 PLAYBOOK 條目的結構，產出 plan.md（邊界、輸出格式、治理規則）
    和 BRIEF.md（具體實作步驟、允許/禁止操作、回報格式）。
    參考既有 `W5-A-RUNTIME-01-DRYRUN_plan.md` 與 BRIEF 作為格式範本。

Step 4 — 交給實作（Hermes → Cursor）：
    plan + brief 產出後，交給 Cursor（或其他實作 agent）執行。
    實作僅在 repo 內新增檔案（CLI module + output dir + test + README）。
    完成後執行 `git diff --stat` 確認僅新增。

Step 5 — 人類 gate → 回寫 PLAYBOOK：
    人類審查（gate）：確認 AC-DRY-1~6 全部通過。
    若發現本次實戰中有新的 edge case、邊界調整、或規則改進，
    更新這個 PLAYBOOK 條目（v0.2、v0.3...）。
```

### 7.2 觀察到的實戰節奏

```
Hermes（planning / 本 PLAYBOOK 條目）
   → 人類確認 plan + brief
     → Cursor（實作 + 測試）
       → 人類 gate（AC-DRY checklist）
         → 回寫 PLAYBOOK（若有新發現）
```

這個循環的關鍵點：

- **plan + brief 階段由人類/Hermes 負責**，確保治理意圖被準確文件化 — 不對邊界有任何模糊空間。
- **實作階段交給 Cursor**，因為這是純機械性的「讀 artefact → 寫新報表」，不需要人類糾結工具選擇或格式細節。
- **人類 gate** 是安全閥 — 確認 AC-DRY-4（僅新增檔案）和 AC-DRY-6（免責聲明）是最後防線。
- **回寫 PLAYBOOK** 是治理迭代閉環 — 每次實戰的新發現都要寫回此條目，讓 pattern 隨使用而成熟。

### 7.3 跨 repo 常用的調整項

| 調整項 | 說明 |
|-------|------|
| Artefact 路徑映射 | 不同 repo 的 `artifacts/`、`observability/` 或 `output/` 目錄結構可能不同，需要在 plan 階段明確定義 mapping |
| JSON 欄位名稱 | 不同 repo 的 gate_result / verdict / metrics 欄位名稱可能不同。CLI 應支援「per-record 的欄位提取 mapping」，可寫在 plan 中或實作為 config |
| Bucket 定義 | 若新 repo 需要 3 bucket 或 7 bucket，可以在 plan 階段調整，但主結構（含 edge_unknown）建議保留 |
| CLI 名稱與所在 package | 建議統一命名為 `dryrun`，但 package 層級可調整（如 `tools/dryrun/`、`observability/dryrun/`、`scripts/dryrun/`） |
| 免責文字語言 | 若團隊以非英文溝通，免責文字應以團隊語言撰寫 |

---

## 附錄 A — 與既有 W5 文件的關係

| 文件 | 關係 | 注意 |
|------|------|------|
| `W5-A-RUNTIME-01-DRYRUN_plan.md` | 本 PLAYBOOK 條目的**源頭設計稿**，有具體的治理規則細節與後續擴展 slot | 本條目不取代 plan.md，而是將其抽象化為可套用的 pattern |
| `W5-A-RUNTIME-01-DRYRUN_BRIEF_TASK_FOR_CURSOR.md` | 本 PLAYBOOK 條目的**實作驗證範例**，BRIEF 的格式與 AC 可直接複用 | 未來新 repo 的 BRIEF 可參考其回報格式框架 |
| `W5_TICKET_TEMPLATES.md` | 提供 runtime 票的 Memory 模板 | 本 PLAYBOOK 是高一層的「治理/PLAYBOOK 條目」，與 ticket template 互補：template 定義**一張票的格式**，PLAYBOOK 定義**一個 pattern 的結構與邊界** |
| `W5_AXES_AND_THEMES.md` | 定義 W5-A 軸的整體目標 | 本 PLAYBOOK 條目作為 W5-A 軸的「治理模式」文件補充 |
| `W5_OVERVIEW.md` | Wave 5 高層目標 | 本 PLAYBOOK 條目服務於 W5 的「強化 observability」和「鋪路 deny engine」兩大方向 |

---

## 附錄 B — 版本歷史

| 版本 | 日期 | 作者 | 變更說明 |
|------|------|------|---------|
| v0.1 | 2026-05-31 | W5-A-PLAYBOOK | 基於 W5-A-RUNTIME-01-DRYRUN 實戰抽象，產出首版治理/PLAYBOOK 條目 |
