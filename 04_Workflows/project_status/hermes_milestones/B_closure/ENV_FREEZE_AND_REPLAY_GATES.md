# ENV_FREEZE_AND_REPLAY_GATES.md

> 用途：定義在開多條單線之前，每條線需要確認的最小環境條件、CI/CD 識別規則、以及 workspace 內的可重播記錄標準。
> 基於：A_closure replay checklist + eval_gate PIPELINE.md 經驗（CI/CD == unknown、Python 版本 == 推測）
> 關聯：B_MINIMAL_GAP_LIST.md §「環境凍結與重播 gate」
> 狀態：**workspace-only definition，未寫入任何 CI / repo / runtime 設定**

---

## 1. 多線調度前的最小環境條件

在**任何新的一條線啟動 discovery 之前**，必須在該線的 PIPELINE.md 中填入以下 5 項。任一項標 `needs-confirmation`（不是 filled）則該線不得進入 scan 階段。

### 1.1 Python 版本與 venv 路徑

| 欄位 | 必要？ | 填寫方式 | 範例 |
|------|:------:|----------|------|
| venv 絕對路徑 | **Y** | `01_Environments/python_venvs/<name>/` | `/mnt/d/大唐三省六部/01_Environments/python_venvs/gov_core_system/` |
| Python 版本（major.minor） | **Y** | `python --version` 輸出 | `Python 3.14.0` |
| pip list（必要套件） | **Y** | `pip list --format=columns` 輸出（至少 pytest） | pytest 9.0.2, numpy 2.x |

**閘門**：缺少 venv 路徑或 Python 版本且標 `needs-confirmation` → 該線**不得**進入 Step 3 Readonly Scan。

### 1.2 測試指令（固化版）

| 欄位 | 必要？ | 填寫方式 | 範例 |
|------|:------:|----------|------|
| 最小測試指令 | **Y** | `python -m pytest <test_files> -v --tb=short`（實際可執行） | `python -m pytest tests/test_eval_gate.py -v --tb=short` |
| 完整測試指令 | **Y** | 同上，包含該線所有測試檔案 | `python -m pytest tests/test_eval_gate*.py tests/test_eval_*.py -v --tb=short` |
| 執行時間（推測） | N | `time <cmd>` 輸出第一行 | `22.4s` |

**閘門**：`python -m pytest` 需在該 venv 下實際可執行。若 venv 的 pytest 不可用 → 在 PIPELINE.md 標 `blocked: venv/pytest unavailable`，寫入 blocker 欄位，**不得標 `needs-confirmation` 敷衍通過**。

### 1.3 Python 路徑確認

| 欄位 | 必要？ | 填寫方式 |
|------|:------:|----------|
| `which python` 或 venv python 路徑 | **Y** | `$(venv_path)/bin/python --version` |
| pycache 衝突標記 | N（但標註） | 若 pycache 含多個 Python 版本（3.14 + 3.10），在 ARCH.md 備註 |

### 1.4 必要 OS 層級工具

| 工具 | 檢查指令 | 若缺失 |
|------|----------|--------|
| bash | `which bash` | **極度不可能**，不列檢查 |
| git | `git --version` | 標 `blocked: git missing`，不得執行 discovery |
| python3 | `which python3` | 同 §1.3 |

### 1.5 環境變數 / 密鑰（如適用）

若該線依賴外部 API（Telegram、HuggingFace、OpenAI 等）：

| 欄位 | 必要？ | 填寫方式 |
|------|:------:|----------|
| 密鑰名稱列表 | Y（如適用） | `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `HF_TOKEN`... |
| 密鑰是否存在於 env | **Y**（確認存在性即可，**不得印出值**） | 以 `test -n "$VAR_NAME" && echo ok || echo missing` 驗證 |
| fallback 策略 | Y（如適用） | 缺少時該線哪個功能會降級或失敗 |

**紅線（不可違反）**：
- 嚴禁在 PIPELINE.md 或任何 workspace 文件印出 `.env` 內容或金鑰原文。
- 密鑰驗證走 `_smoke_test_keys.py` 或 `test -n "$KEY_NAME" && echo ok || echo missing`，不得用 `cat .env` / `print(key)`。

---

## 2. CI/CD 流程識別規則（workspace 內識別，不修改）

每條線需在 PIPELINE.md 中記錄該線真實的 CI/CD 資訊。目標不是修改 CI，而是**知道這條線是怎麼被驗證的**，以便在 replay 時能複製相同的驗證步驟。

### 2.1 CI 類型判斷流程（decision tree）

```
Q: repo root 是否有 .github/workflows/？
 ├─ Y → 平台 = GitHub Actions
 │     記錄：workflow 檔名、on trigger、job 名稱
 │
 └─ N（或不存在）→ Q: repo root 是否有 .gitlab-ci.yml？
     ├─ Y → 平台 = GitLab CI
     │     記錄：stage 列表、script 指令
     │
     └─ N → Q: repo root 是否有 Jenkinsfile？
         ├─ Y → 平台 = Jenkins
         │     記錄：pipeline 階段、agent 標籤
         │
         └─ N → Q: 原始碼中是否有 CI entry point 模組（如 eval_ci_check.py）？
             ├─ Y → 平台 = 自訂（custom script / external platform）
             │     記錄：entry point 模組路徑、exit code 慣例
             │
             └─ N → 平台 = 未知（unknown）
                   記錄：**blocked: CI platform unknown**
```

### 2.2 必須記錄的 CI/CD 資訊

| 欄位 | 範例 | 來源 |
|------|------|------|
| CI 平台 | GitHub Actions / GitLab CI / Jenkins / custom / **unknown** | §2.1 |
| 觸發條件 | push to main / PR / schedule | workflow 檔 |
| 檢查階段列表 | lint → type → test → deploy | workflow 檔 |
| 測試指令（CI 版） | `python -m pytest tests/ -v` | workflow 檔 / 推測 |
| 建置 artifact（如適用） | dist/*.whl | workflow 檔 |
| CI 身份驗證（如適用） | GITHUB_TOKEN / gitlab-ci-token | workflow 檔 |

### 2.3 當 CI 為 **unknown** 時的處理

這不是 block，但需在 PIPELINE.md 明確記錄：

```
CI status: unknown
影響範圍：
- apply 後的回歸測試只能依賴 local unittest（§1.2）
- replay gate 需把「人工確認 CI 結果」標為強制檢查點
- 該線標記 deferred: needs-ci-audit
```

---

## 3. Workspace 內重播記錄標準

要讓一條線在未來可以安全地重播（replay），workspace 的 run notes 必須包含以下 4 類資訊。

### 3.1 Run ID

每條 run note 的檔名格式：
```
YYYY-MM-DD_<module>_<step>.md
```

其中 `<step>` 從 bootstrap → discovery → scan → fix_round → review → apply_plan → apply_result（7 步）。run_id 隱含在檔名中（日期時間 + step），不需要額外 UUID。

**唯一性規則**：同一天同一 module 同一 step 不得出現兩份。若需重做（redo），舊檔保留，新檔加後綴 `_v2`、`_v3`。

### 3.2 Config Snapshot

每份 run note 必須包含一個 config snapshot section。最低：

```
## Config Snapshot

- venv: /path/to/venv
- python: 3.x.y
- pytest: x.y.z
- module version: (git SHA or module version)
- dependency files: (requirements.txt / pyproject.toml 路徑，如果存在)
```

config snapshot **不得**在正文中重複記錄（如果連續 step 的 env 不變，可寫 `same as bootstrap run`）。

### 3.3 依賴清單

在 discovery run note 中記錄該線的完整 import 依賴樹：

```
## Import Dependencies

stdlib:
  - typing
  - functools
  - logging

third-party:
  - pydantic (>= 2.0)
  - requests (>= 2.31)

repo-internal:
  - observability.eval_gate (consumer: evaluate_task_record)
```

### 3.4 Run Outcome（關鍵結構化結果）

每個 run note 的末尾必須包含一個 outcome block，格式：

```
## Outcome

- status: PASS / FAIL / PARTIAL / BLOCKED
- files_created: (list)
- files_modified: (list)
- blocker: (if status == BLOCKED, reason; else N/A)
- notes: (optional, 1–2 sentences)
```

---

## 4. 檢查點分配：人工 vs 未來自動化

| 檢查點 | 歸屬 | 原因 |
|--------|:----:|------|
| Python 版本與 venv 路徑確認 | **人工** | venv 路徑依賴 SSH/WSL 環境，agent 無法保證該路徑在其他 session 有效 |
| `pip list` 套件確認 | 未來可自動 | 以 `pip list --format=json` 執行即可，agent 可排 cron |
| 測試指令可執行性 | **人工** | 需實際 activate venv 並試跑。agent 可以跑，但結果波動（可能因環境時間、資源競爭）需有人判斷 |
| CI 平台識別（判斷 decision tree） | **未來可自動** | decision tree 邏輯是 deterministic，agent 可寫成 Python 腳本 |
| CI 平台為 unknown 的標記 | **人工** | 需要人類了解團隊使用的 CI 工具 |
| Run ID 唯一性 | **未來可自動** | agent 檢查檔名即可，無爭議 |
| Config snapshot 生成 | **未來可自動** | `pip list --json` + `python --version` + `git rev-parse HEAD` 可程式化 |
| Import 依賴樹生成 | **未來可自動** | `pipdeptree` 或 `modulefinder` 可自動化 |
| Outcome block 填寫 | **人工終審** | agent 可生成 draft，但 PASS/FAIL/BLOCKED 判斷在 agent 可能不準（工具成功但邏輯錯誤） |
| 密鑰存在性驗證 | **人工** | 因安全紅線，agent 不得直接讀 env 且需要安全策略判斷 |

### 適用於 all lanes（control plane）

以上檢查點不區分 lane（runtime / review / doc-sync / gate）— 它們是所有 lane 的共享前置條件。

- 若一條線的 **runtime lane** 需要執行測試 → 依 §1.2 與 §2。
- 若一條線的 **review lane** 需要回放之前的 scan → 依 §3 run note 查找。
- 若一條線的 **doc-sync lane** 需要記錄 env 變更 → 依 §1.1 更新。
- **gate lane** 可依靠§1–§3 的完成度來判斷該線是否「可重播」。

---

## 5. 定義閘門：開新線前必過

> 這些閘門是 workspace 層級的**文件閘門**，不是 CI / repo 層級的 gate。它們約束的是「是否可以從 bootstrap 進入 discovery / scan / fix」。

| 閘門 | 通過條件 | 關聯條文 |
|:----:|----------|----------|
| G-ENV-1 | PIPELINE.md 中 venv 路徑與 Python 版本已**實際填入**（非 `needs-confirmation`） | §1.1 |
| G-ENV-2 | 測試指令已**實際填入**（非推測）且已用 `--dry-run` 驗證過 | §1.2 |
| G-ENV-3 | CI/CD 平台已分類（含 `unknown` 也裝作分類完成） | §2.1–2.2 |
| G-ENV-4 | Config snapshot 模板已建立 | §3.2 |
| G-REPLAY-1 | 前序 step 的 run note 存在且 outcome 為 PASS/ PARTIAL | §3.4 |
| G-REPLAY-2 | 前序 step 的 run note 包含 config snapshot（可引用「same as bootstap」） | §3.2 |
| G-REPLAY-3 | 無兩份相同 run_id（已知一天內同一 step 未 redo） | §3.1 |

**閘門檢查方式**（均在 workspace 內手動檢核，尚未自動化）：

```
for gate in G-ENV-1 G-ENV-2 G-ENV-3 G-ENV-4 G-REPLAY-1 G-REPLAY-2 G-REPLAY-3; do
  echo "gate <gate>: YES / NO"
done
```

---

## 附錄 A：與 A_closure replay checklist 的對應

| A_closure checkpoint | B 強化 | 狀態 |
|----------------------|--------|:----:|
| 0.1 模組原始碼路徑已知 | 增加 CI/CD 平台識別 | 本次新增 |
| 1.1 SKILL 檔案存在 | 增加 env freeze gate | 本次新增 |
| 2.5 測試指令有推測 | 改為「測試指令已實際填入」 | 升級 |
| 3.1 DEBT_LOG 有條目 | 增加跨線 debt 處理 SOP（另見 CROSS_FILE_DEBT_HANDLING_SOP.md）| 本次新增 |
| 7.1 DEBT_LOG 統計已更新 | 增加 run_id 唯一性規則 + config snapshot | 本次新增 |

## 附錄 B：術語對照

| 本文件用語 | 對應 control plane 用語 | 說明 |
|-----------|-------------------------|------|
| 一條線（line）| lane（runtime / review / doc-sync / gate）| 單線 owner 走完 7 步 closed loop 即為一條 lane |
| run note | runtime lane 記錄 | `90_runs/` 下的執行記錄 |
| PIPELINE.md | runtime lane config / doc-sync lane 參考 | 模組的 CI/CD 文件 |
| config snapshot | runtime lane env freeze | 需要凍結的環境快照 |
| outcome block | gate lane 的 checkpoint | 每步結果判斷 |
