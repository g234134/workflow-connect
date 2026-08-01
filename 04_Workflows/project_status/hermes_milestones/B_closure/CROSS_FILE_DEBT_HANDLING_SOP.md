# CROSS_FILE_DEBT_HANDLING_SOP.md

> 用途：當技術債跨多個檔案或多條單線時，如何拆票、獨立驗收、對齊 control plane lane，避免一次大改導致難以回滾。
> 基於：DEBT_LOG.md 中的 D-005（`_total_context_tokens` 重複實作，跨 eval_gate ↔ eval_exporter）和 D-008（`KNOWN_GATE_TAGS` 硬編碼，跨 eval_stats）
> 關聯：B_MINIMAL_GAP_LIST.md §「跨檔案 debt 處理」
> 狀態：**workspace-only SOP，未寫入任何 repo / CI / control plane**

---

## 1. 什麼是「跨檔案技術債」

定義：一次修復需修改 **2 個以上檔案**，且不屬於標準化 refactoring（如單檔 rename）。

### 常見類型

| 類型 | 例子 | 危險度 |
|------|------|:------:|
| **重複實作** | D-005：`eval_gate._total_context_tokens` vs `eval_exporter._context_tokens_total` — 邏輯相同但各自實作 | ★★☆ |
| **硬編碼常數同步** | D-008：`eval_stats.KNOWN_GATE_TAGS` 需手動匹配 `eval_gate._RULES` | ★★★ |
| **介面耦合變更** | 更改 `evaluate_task_record` 回傳 schema → 所有消費者（exporter, ci_check, flow）都需更新 | ★★★ |
| **跨模組常數提取** | 共享閾值（CONTEXT_HEAVY_THRESHOLD）散落多處 | ★☆☆ |
| **循環依賴** | A import B, B import A | ★★★ |

**危險度標籤**用於決定本 SOP 的策略選擇（§2）。

---

## 2. 四步處理流程

### Step A：識別與分類（在 scan 階段完成）

| 動作 | 產出 |
|------|------|
| 在 scan run note 中標記該 debt 是否跨檔案 | 跨檔案 debt 的檔案列表 |
| 判定危險度（★數） | ★ ratings |
| 識別所有者（哪些 lane 會受影響） | 影響範圍列表（runtime / review / doc-sync / gate） |

**範例（基於 D-005）**：

```
D-005 跨檔案判定：
- 檔案：eval_gate.py(62–70) ↔ eval_exporter.py(35–43)
- 危險度：★★☆（純抽取，無語意變更風險）
- 受影響 lane：runtime（需重新安裝套件）、review（需審 shared utility）
- 消費者：無（`_total_context_tokens` 為 private helper，非 public API）
```

### Step B：拆票（ticket decomposition）

**核心規則**：一張票 = 一個可獨立驗收的變更，不能要求一次 PR 改 3 個檔案。

#### 拆票策略（依危險度）

| 危險度 | 拆票策略 | 最少票數 |
|:------:|----------|:--------:|
| ★☆☆ | 單票直接改 | 1 票（單次 patch 改多檔 + 一次測試）|
| ★★☆ | 3 票：prep → apply → cleanup | 3 票 |
| ★★★ | 4 票：freeze → prep → apply → cleanup | 4 票 |

**3 票模板**（以 D-005 為例）：

```
Ticket 1（prep）：建立 shared utility 模組
  lane: runtime → 在 workspace 建立 `observability/_shared_tokens.py`
  內容：抽取 `_total_context_tokens` → `total_context_tokens`（public）
  驗收：importable，回傳值一致（比對 eval_gate 與 eval_exporter 的原始輸出）

Ticket 2（apply）：eval_gate 改用共享版本
  lane: runtime → 將 eval_gate.py 的 private function 改為 import shared
  驗收：eval_gate unittest 全數 PASS

Ticket 3（apply）：eval_exporter 改用共享版本
  lane: runtime → 將 eval_exporter.py 的 private function 改為 import shared
  驗收：eval_exporter unittest 全數 PASS
```

**4 票模板**（以 D-008 為例）：

```
Ticket 0（freeze）：凍結現狀
  lane: runtime → git tag / branch snapshot
  產出：freeze note + snapshot label
  驗收：git tag 存在

Ticket 1（prep）：建立動態提取 path
  lane: runtime → 新增 `eval_gate.list_gate_tags()` public 函數
  驗收：函數回傳值等於 `_RULES` 的 tag 集合

Ticket 2（apply）：eval_stats 改用動態提取
  lane: runtime → `KNOWN_GATE_TAGS` 改為呼叫 `eval_gate.list_gate_tags()`
  驗收：eval_stats unittest 全數 PASS + 行為與舊版一致（fixtures 比對）

Ticket 3（cleanup）：清理舊常數
  lane: runtime → 移除 `KNOWN_GATE_TAGS`（若已無其他引用）
  驗收：搜尋全 repo 無 `KNOWN_GATE_TAGS` 引用 + 所有測試 PASS
```

### Step C：為每張票對齊 control plane lane

| Lane | 每張票必須做的事 |
|------|------------------|
| **runtime** | 產出 suggested patch（至少一檔）、執行測試、填寫 outcome block |
| **review** | Run review gate（like/dislike 各 1+）、產出 review note、更新 STYLE.md / PLAYBOOK.md 如適用 |
| **doc-sync** | 更新 ARCH.md（如果 shared utility 新增了公開介面）、更新 PIPELINE.md（如果測試指令變更）、更新 DEBT_LOG.md（狀態流轉）|
| **gate** | 確認前一個 ticket 的 outcome 為 PASS 才能啟動下一個 ticket |

**階梯規則**：

```
Ticket N (runtime) → PASS → review 通過 → doc-sync 更新 → 
  ⟹ gate 確認 Ticket N done → Ticket N+1 可以開始 (runtime lane)
```

階梯不允許跳過。如果 Ticket 1 的 review 被 reject，Ticket 2 必須等待 Ticket 1 修正並重新 review 通過。

### Step D：驗收與合併（merge 策略）

| 危險度 | 合併策略 | Rollback 方式 |
|:------:|----------|--------------|
| ★☆☆ | 單 PR merge | revert single commit |
| ★★☆ | 每個 ticket 獨立 PR merge | revert 其中一個 ticket 的 commit（其他 ticket 不受影響）|
| ★★★ | freeze branch → 在 branch 上逐一 merge tickets → PR into main | branch-level revert 或逐一 revert tickets |

---

## 3. 什麼時候必須先 freeze 再開分支

### 三條強制 freeze 條件（任一成立即觸發）

1. **變更會改變消費者行為**（如 D-002 TypedDict 回傳型別、D-004 比較運算子修正）
2. **跨多個 lane**（runtime + doc-sync + gate 都需要動作）
3. **危險度 ★★★**

### Freeze 流程

```
Step 1：確認當前 git HEAD 與未 commit 變更
  git status
  git log --oneline -3

Step 2：建立 freeze tag / branch
  git tag b-<線名>-freeze-<YYYYMMDD>
  或 git branch b-<線名>-<ticket-id>-prep

Step 3：寫 freeze note（放入 90_runs/）
  格式：
    ## Freeze Note
    - date: YYYY-MM-DD
    - tag: b-eval_exporter-freeze-20260530
    - committer: (name / Hermes)
    - reason: (觸發條件編號 + 簡要說明)
    - open_changes: (list of uncommitted files if any)

Step 4：開始在 branch 上逐一執行 tickets（從 Ticket 0 開始）
```

### 不需要 freeze 的情況（純加法變更）

- 僅新增 docstring / logging / 註解 → **不需要 freeze**
- 新增 public function（不修改既有 API）→ **不需要 freeze**
- 新增模組級常量（不影響既有 import）→ **不需要 freeze**
- D-001、D-003、D-010（純加法，已在 eval_gate 完成）→ **不需要 freeze**

---

## 4. 與現有 DEBT_LOG 狀態機的對接

當跨檔案 debt 進入本 SOP 流程時，DEBT_LOG 狀態流轉如下：

```
open（scan 發現跨檔案 debt）
  │
  ├→ planned（拆票完成，tickets 已列在 B_closure 或該線的 20_runtime/）
  │      │
  │      ├→ fixed_suggested（prep ticket 通過 review，suggested patch 就緒）
  │      │      │
  │      │      ├→ fixed_in_repo（apply ticket 完成 + unittest PASS）
  │      │      │      │
  │      │      │      └→ 所有 tickets 完成 → debt 狀態 close
  │      │      │
  │      │      └→ rejected（review reject）
  │      │
  │      └→ deferred（因優先級或資源原因延期）
```

**跨檔案 debt 的 DEBT_LOG 條目格式**（與單檔 debt 共用同一個表）：

```
| ID | 位置 | 類型 | 嚴重度 | 摘要 | 發現日期 | 預計修復 | 狀態 | 關聯票據 |
|----|------|------|:----:|------|----------|----------|:----:|----------|
| D-005 | eval_gate.py:62–70, eval_exporter.py:35–43 | WORKAROUND | P2 | `_total_context_tokens` 重複實作 | 2026-05-30 | 2026-Q2 | planned | B-TKT-001/002/003 |
```

新增「關聯票據」欄位（從 B_TKT 系統引用 ticket ID）。

---

## 5. 與 A_closure SOP 的關係

| A_closure SOP 步驟 | 跨檔案 debt 的對應調整 |
|---------------------|----------------------|
| Step 3（Readonly Scan）| 在 scan run note 中額外標記跨檔案 debt + 危險度 |
| Step 4（Fix Round）| **跨檔案 debt 不得在單檔 fix_round 中處理**。改為進入本 SOP（拆票、列 planned）|
| Step 5（Review Gate）| 每個 ticket 獨立跑 review |
| Step 6（Apply Plan）| 每個 ticket 有獨立 apply plan | 
| Step 7（Debt Status Update）| 原 debt 條目在「所有 tickets 完成」之前保持 `planned` 狀態 |

---

## 6. 實例：D-005 完整演練

目前狀態：D-005 在 eval_gate DEBT_LOG.md 中標 `open`。

### Step A：識別與分類（已在 eval_gate scan 完成）

```
D-005：
  檔案：eval_gate.py:62–70 ↔ eval_exporter.py:35–43
  危險度：★★☆（純抽取，無語意變更）
  受影響 lane：runtime, review, doc-sync
```

### Step B：拆票（本次建立）

```
B-TKT-001：prep — 在 workspace 建立 shared utility 檔
  檔案：20_runtime/_shared_tokens.py（workspace only，不進 repo）
  內容：public total_context_tokens(record) → int
  驗收條件：輸入已知 record，回傳值 = eval_gate._total_context_tokens(record) == eval_exporter._context_tokens_total(record)
  lane: runtime

B-TKT-002：apply — eval_gate 改用 shared
  檔案：eval_gate.suggested.v2.py（修改 import + 函數呼叫）
  驗收條件：eval_gate unittest PASS
  lane: runtime → review → doc-sync

B-TKT-003：apply — eval_exporter 改用 shared
  檔案：eval_exporter.suggested.v1.py（修改 import + 函數呼叫）
  驗收條件：eval_exporter unittest PASS
  lane: runtime → review → doc-sync
```

### Step C：階梯執行

```
B-TKT-001 (PASS) → B-TKT-002 review (PASS) → B-TKT-002 apply (PASS, test PASS) →
  D-005 → planned → fixed_suggested (partially) →
  B-TKT-003 review (PASS) → B-TKT-003 apply (PASS, test PASS) →
  D-005 → fixed_in_repo
```

### Step D：合併策略

★☆☆ → merge 策略為獨立 PR merge。每個 ticket 獨立 merge，任一 ticket 出問題只 revert 該 ticket 的 commit。

---

## 7. 常見陷阱

| 陷阱 | 後果 | 預防 |
|------|------|------|
| 把所有跨檔案 debt 塞進同一張票 → 一改全改 | 難以回滾，合併衝突 | 依 §2 Step B 拆成至少 3 票 |
| prep 票跳過 review → 直接寫進 repo | 共享函數命名/風格不一致，後續 tickets 基於錯誤基礎 | prep 票需經 review gate |
| 不 freeze 直接改 dangerous debt | 消費者突然出錯，無法快速恢復 | 依 §3，任一條件成立即 freeze |
| 同一張票同時跨 runtime + doc-sync | 漏更新 ARCH.md/PIPELINE.md | 每一張 ticket 的 doc-sync lane 不可省略 |
| 跨線 debt 只更新其中一條線的 DEBT_LOG | 另一條線不知此 debt 已被處理，可能重開 | 若跨兩條線（如 eval_gate ↔ eval_exporter），兩邊的 DEBT_LOG 都需更新 |
