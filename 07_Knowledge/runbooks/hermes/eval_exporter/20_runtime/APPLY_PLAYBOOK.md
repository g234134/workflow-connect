# APPLY_PLAYBOOK.md — 從 Workspace Suggested Patch 安全導回 Repo

> 建立日期：2026-05-30 | 狀態：initial_draft
> 適用範圍：單檔、低風險、無語意變更（docstring / logging / 註解）的 suggested patch

---

## 1. 目的

當 Infra Hygiene Owner 完成以下前置工作後，本 playbook 定義如何將 workspace 內的建議版（`suggested.vN.py`）安全、可追溯地套用到真實 repo。

```
workspace 階段                          apply 階段                     repo 階段
┌──────────────┐    ┌──────────────────┐    ┌───────────────────┐
│ discovery    │    │ APPLY_PLAYBOOK   │    │ 人工 / Cursor     │
│ scan_readonly │──►│ apply_plan_vN    │──►│ 套入 repo         │
│ fix_roundN   │    │                 │    │ 跑測試 / commit   │
│ review_vN    │    │ apply_confirm    │    │ 回報 Hermes       │
└──────────────┘    └──────────────────┘    └───────────────────┘
```

---

## 2. 適用範圍（scope）與排除（non-scope）

### 適用

| 條件 | 說明 |
|------|------|
| **patch 類型** | docstring 新增、logging 補強、區塊註解、常數旁加 inline 註解 |
| **風險等級** | 零風險（無行為變更）或低風險（僅加法變更） |
| **檔案數** | 單檔（目前版本；跨檔擴充待確認） |
| **語意變更** | 無：不改變 if 條件、回傳值、輸入簽名、常數值 |
| **測試影響** | 不改變現有 test assertion |

### 不適用（需另走 PR / code review 流程）

| 條件 | 原因 |
|------|------|
| 改變 if 條件（如 `>` 改 `>=`） | 語意變更，需上游確認 |
| 新增 TypedDict 或公開型別 | 影響下游 consumer |
| 跨檔案重構（抽取共用函數） | 需同步改多檔 |
| try/except 規則迴圈包裝 | 行為變更，需測試調整 |
| 新增第三方依賴 | 需 CI/CD 確認 |

---

## 3. 前置條件

在進入 apply 流程之前，必須全部滿足：

- [ ] **有 suggested 建議版存在**：`20_runtime/<module>.suggested.v<N>.py`
- [ ] **已完成人工審查**：有 `90_runs/YYYY-MM-DD_review_v<N>.md`，且結論為「接受」
- [ ] **靜態比對已通過**：確認簽名、keys、常數、if 條件完全一致
- [ ] **已知 repo 目標路徑**：對應的真實 repo 檔案已確認（例如 `observability/eval_gate.py`）
- [ ] **apply_plan 已建立**：`90_runs/YYYY-MM-DD_apply_plan_v<N>.md`
- [ ] **若路徑或指令不確定**：該項需標 `needs-confirmation`，不得猜測

---

## 4. 角色分工

| 角色 | 負責 | 不負責 |
|------|------|--------|
| **Hermes Agent** | 產生 suggested 檔、靜態比對、apply_plan、人工審查紀錄、更新 DEBT_LOG（→ `fixed_suggested`） | 修改 repo、執行 git、跑測試 |
| **Human / Cursor** | 依照 apply_plan 將 patch 套入 repo、執行測試、commit / PR | 變更 patch 內容（只可拒絕或接受，不可 edit-in-place） |
| **Human（CI）** | 確認 CI 通過或記錄失敗原因 | 決定 patch 語意 |

**為什麼 Hermes 不改 repo？**
- 工作規則禁止直接修改真實 repo。
- 雙層隔離：Hermes 產建議 → Human/Cursor 審核套用 → 降低誤改風險。

---

## 5. 標準流程（8 步）

### Step 1 — 確認建議版與目標

```
來源：20_runtime/eval_gate.suggested.v1.py
目標：observability/eval_gate.py（在大唐三省六部 repo 中）
類型：docstring + logging + 區塊註解（無語意變更）
```

動作：
- [ ] 確認 suggested 檔存在且與 `review_v<N>.md` 結論一致。
- [ ] 確認 repo 目標檔路徑可讀取。
- [ ] 若有路徑假設，標 `needs-confirmation` 在 apply_plan 中。

### Step 2 — 人工 diff 審核

```
cd /mnt/d/大唐三省六部
diff <(cat observability/eval_gate.py) <(cat /mnt/d/hermes-workspace/.../eval_gate.suggested.v1.py)
```

審核重點：

| 審核項 | 通過條件 | 否決條件 |
|--------|----------|----------|
| 函式簽名 | 完全一致 | 參數順序或名稱不同 |
| 回傳 keys | `pass`、`tags`、`reasons`、`eval_gate_version` 一致 | 任何 key 新增或改名 |
| 常數值 | 所有 `Final` 值一致 | 任一常數值變動 |
| if 條件 | 完全相同（含運算子） | `>` 改 `>=` 等 |
| _RULES 順序 | 相同元組順序 | 順序變動 |
| import | 僅新增 `import logging` | 新增第三方套件 import |
| 原始邏輯行 | 未被修改 | 任何非 docstring/logging 行的變更 |

### Step 3 — 人工確認可套用

- [ ] 在 `apply_plan_v<N>.md` 的「人工確認欄位」簽署 `approved`。
- [ ] 若 `rejected`，回到 Step 1 重新檢視；若 `partial`，標明哪些部分不接受。

### Step 4 — 由有權限工具套入 repo

四種套入方式（依可用工具選一）：

| 方式 | 指令 | 風險 | 建議 |
|------|------|:----:|------|
| A. 直接覆寫 | `cp suggested.v1.py observability/eval_gate.py` | 低（若內容唯一變更） | 最單純，但需確保換行符號一致 |
| B. 手動 patch | 用 editor 逐段複製 | 最低 | 適合 docstring 段落 |
| C. git diff + patch | `git diff --no-color > patch.diff` → `git apply patch.diff` | 中（需 clean diff） | 適合 CI 環境 |
| D. Hermes patch tool | 使用 Hermes 的 `patch` tool（若日後開放） | 低 | 未來選項 |

⚠️ **若使用方式 A / C，需先確認 repo 的换行符號（CRLF vs LF）**。
原始 `eval_gate.py` 使用 `\r\n`（CRLF；由 `read_file` 輸出確認）。suggested 版為 LF。
建議套用後再執行一次 diff 確認完整度。

### Step 5 — 最小驗證

在對應的 Python 環境下執行（指令為推測，標 `needs-confirmation`）：

```bash
# 1. 檔案可載入（importable）
python -c "from observability.eval_gate import evaluate_task_record; print('OK')"

# 2. 介面未變 — 回傳 keys
python -c "
from observability.eval_gate import evaluate_task_record
r = evaluate_task_record({'success': True, 'retry_count': 0, 'handoff_count': 0})
assert set(r.keys()) == {'pass', 'tags', 'reasons', 'eval_gate_version'}, f'keys={r.keys()}'
assert r['pass'] == True
print('Interface OK')
"

# 3. CLI 入口名稱未變（eval_gate.py 無直接 CLI；驗證 exporter 可載入）
python -c "from observability.eval_exporter import main; print('exporter CLI OK')"

# 4. 無新增外部依賴
python -c "
import observability.eval_gate as g
# import logging 是 stdlib；不該有 site-packages dependency
assert 'site-packages' not in str(g.__file__), 'unexpected external dep'
print('stdlib only OK')
"

# 5. logging 不造成 import / runtime error
python -c "
import logging
logging.basicConfig(level=logging.INFO)
from observability.eval_gate import evaluate_task_record
r = evaluate_task_record({'success': True, 'retry_count': 0, 'handoff_count': 0})
print('Logging OK')
"
```

⚠️ **如果以上任一命令因路徑 / venv 問題失敗**，記錄到 apply_plan 的「套用後障礙」欄位，**不得猜測替代指令**。

### Step 6 — 跑最小測試（指令為推測，標 `needs-confirmation`）

```bash
# 推測指令（需在對應 venv 下執行）
python -m pytest tests/test_eval_gate.py tests/test_eval_gate_contract.py -v --tb=short
```

測試結果必須：全部 PASS 或與 apply 前一致（無 regression）。
若因測試環境不可用無法執行，標 `needs-confirmation` 在 apply_plan。

### Step 7 — 回報 Hermes

使用 `20_runtime/APPLY_CONFIRM_TEMPLATE.md` 回報結果給 Hermes。
Hermes 收到後：

- [ ] 更新 DEBT_LOG.md：相關 debt_id 從 `fixed_suggested` → `fixed_in_repo`
- [ ] 在 `90_runs/YYYY-MM-DD_fix_roundN.md` 追加一節「套用結果」
- [ ] 歸檔 `suggested.v<N>.py`（可保留或移至 archive/）

### Step 8 — 歸檔與清理

- [ ] suggested 檔保留在原位（作為歷史紀錄），或移至 `20_runtime/archive/`
- [ ] apply_plan 中的 `approved = yes` 欄位已簽署
- [ ] DEBT_LOG 統計已更新

---

## 6. 失敗與回滾策略

### 場景 A：測試失敗

| 失敗類型 | 動作 |
|----------|------|
| 測試與 apply 前狀態不一致（regression） | 回滾 repo 修改 → 在 DEBT_LOG 將 debt 標回 `fixed_suggested` → 在 apply_plan 記錄 failure |
| 測試因環境問題無法執行 | 在 apply_plan 標 `needs-confirmation`，不視為 failure，但下次套用前需先驗證環境 |
| 測試環境不存在 | 不套用；停在此步，等待環境確認 |

### 場景 B：人工否決 patch

- 在 `apply_plan` 中記錄 `approved = rejected` 及理由
- DEBT_LOG 中相關 debt_id 從 `fixed_suggested` → `rejected`
- 若部分接受：改為 `partial`，只將接受的 debt_id 標 `fixed_suggested`（等待部分版 v2）

### 場景 C：套用後發現 repo 其他問題（非本次 patch 造成）

- 不歸咎於本 patch
- 開新 DEBT_LOG 條目，記錄發現的問題
- 本 patch 仍視為 fixed

---

## 7. 套用完成後需更新的檔案

| 檔案 | 更新內容 |
|------|----------|
| `10_memory/DEBT_LOG.md` | debt_id 狀態 `fixed_suggested` → `fixed_in_repo`；統計摘要更新 |
| `90_runs/YYYY-MM-DD_fix_roundN.md` | 追加「套用結果」章節（日期、執行人、測試結果、commit 參考） |
| `90_runs/YYYY-MM-DD_apply_plan_vN.md` | 填入 `approved` 欄位、`applied_at`、測試結果摘錄 |
| `10_memory/ARCH.md` | 若套用新增了公開型別或介面變更（非本次情況），需同步 |

---

## 8. 重複使用指引

下一次要套用新的 suggested 檔時：

1. 複製本 playbook 作為範本（不需修改 playbook 本文）。
2. 建立新的 `apply_plan_v<N+1>.md`，填入該次的具體資訊。
3. 確認該次 patch 在「適用範圍」內；若超出，標註並改走 code review 流程。
4. 從 Step 1 開始。

---

## 9. 下一步

- [ ] 人類 / Cursor 閱讀本 playbook + `apply_plan_v1.md`。
- [ ] 確認所有前置條件滿足後，執行 Step 2（人工 diff 審核）。
- [ ] 審核通過後，執行 Step 4（套入 repo）。
- [ ] 套入後回報結果（使用 `APPLY_CONFIRM_TEMPLATE.md`）。