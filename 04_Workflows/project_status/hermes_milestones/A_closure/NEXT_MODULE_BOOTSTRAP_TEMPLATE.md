# NEXT_MODULE_BOOTSTRAP_TEMPLATE.md

> 將此模板複製到第二模組時使用。
> 複製後替換 `<MODULE>` 為真實模組名稱（如 `logging_adapter`）。

---

## 1. 前置準備（需人工確認）

| 項目 | 填入值 | 確認者 |
|------|--------|--------|
| 模組名稱 | `<MODULE>` | 尚書省 / 專案 lead |
| 真實 repo 路徑 | `observability/<MODULE>.py`（推測，需確認） | 尚書省 |
| 是否有測試檔案 | `tests/test_<MODULE>.py`（推測，需確認） | 尚書省 |
| 是否有第三方依賴 | 執行 `grep -rn "import \|from " <repo>/observability/<MODULE>.py \| grep -v "from __future__\|from typing\|import.*#.*stdlib"` | Hermes（掃描後）|
| 是否有 CLI 入口 | `grep -rn "def main\|if __name__" <repo>/observability/<MODULE>.py` | Hermes（掃描後）|
| 測試 venv 路徑 | `01_Environments/python_venvs/gov_core_system/`（推測）| 尚書省 |
| pyproject.toml 位置 | 未知（eval_gate 經驗：root 無，子目錄有多份） | 尚書省 |

---

## 2. 最小目錄結構

```
/mnt/d/hermes-workspace/infra_owner/<MODULE>/
├── 00_skill/
│   └── SKILL_<MODULE>_HYGIENE_OWNER.md    # 複製 eval_gate 版，替換模組名稱
├── 10_memory/
│   ├── ARCH.md                             # 全部填 unknown，覆蓋後更新
│   ├── STYLE.md                            # 複製 eval_gate 版（通用慣例）
│   ├── DEBT_LOG.md                         # 空表 + 格式說明（複製 eval_gate 版）
│   └── PLAYBOOK.md                         # 複製 eval_gate 版（占位模板）
├── 20_runtime/
│   ├── PIPELINE.md                         # 全部標 unknown（複製 eval_gate 版）
│   ├── TASK_INTAKE_TEMPLATE.md             # 直接複製 eval_gate 版（通用）
│   ├── REPORT_TEMPLATE.md                  # 直接複製 eval_gate 版（通用）
│   └── <MODULE>.suggested.v1.py            # 在 fix_round 後建立
└── 90_runs/
    ├── YYYY-MM-DD_bootstrap.md
    ├── YYYY-MM-DD_discovery.md
    ├── YYYY-MM-DD_scan_readonly.md
    ├── YYYY-MM-DD_fix_round1.md
    ├── YYYY-MM-DD_review_v1.md
    ├── YYYY-MM-DD_apply_plan_v1.md
    └── YYYY-MM-DD_apply_result_v1.md
```

---

## 3. 直接複製（不需修改）的文件

以下文件在 eval_gate 版中已是通用模板。到第二模組時直接複製即可，不需任何內容修改：

| 來源（eval_gate 版） | 目標（<MODULE> 版） | 備註 |
|----------------------|---------------------|------|
| `20_runtime/TASK_INTAKE_TEMPLATE.md` | `20_runtime/TASK_INTAKE_TEMPLATE.md` | 完全通用 |
| `20_runtime/REPORT_TEMPLATE.md` | `20_runtime/REPORT_TEMPLATE.md` | 完全通用 |
| `20_runtime/APPLY_PLAYBOOK.md` | `20_runtime/APPLY_PLAYBOOK.md` | 完全通用 |
| `20_runtime/APPLY_CONFIRM_TEMPLATE.md` | `20_runtime/APPLY_CONFIRM_TEMPLATE.md` | 完全通用 |

---

## 4. 需要複製但替換模組名稱的文件

| 來源 | 目標 | 修改 |
|------|------|------|
| `00_skill/SKILL_INFRA_HYGIENE_OWNER.md` | `00_skill/SKILL_<MODULE>_HYGIENE_OWNER.md` | 替換檔案內「eval_gate」為「<MODULE>」|
| `10_memory/DEBT_LOG.md` | `10_memory/DEBT_LOG.md` | 保留空表和格式說明，刪除 D-001 ~ D-010 |
| `10_memory/STYLE.md` | `10_memory/STYLE.md` | 保留通用慣例，替換 §9 的 Logging 慣例（如適用） |

---

## 5. 需要新建（空白待填）的文件

| 檔案 | 初始內容 |
|------|----------|
| `10_memory/ARCH.md` | 全部填 unknown，只留目錄結構占位 |
| `10_memory/PLAYBOOK.md` | 複製 eval_gate 版的占位模板，清空 eval_gate 特定內容 |
| `20_runtime/PIPELINE.md` | 全部標 unknown，只留標題結構 |
| `90_runs/YYYY-MM-DD_bootstrap.md` | 本日期的 bootstrap run note |

---

## 6. 風險提示（eval_gate 經驗）

| 風險 | 說明 | 緩解 |
|------|------|------|
| **測試環境不可用** | eval_gate 的 apply_result 依賴人工回報測試。如果第二模組的 venv 無法 activate，則 apply 後的驗證無法自動化 | 在 discovery/scan 階段就嘗試 `python --version` 和 `python -m pytest --version`（在推測的 venv 路徑下）。如果失敗，提前標記在 PIPELINE.md |
| **第三方依賴** | eval_gate 是 stdlib-only。如果第二模組依賴 FastAPI / numpy / pydantic，discovery 階段需多檢查 `requirements.txt` / `pyproject.toml` | 在 scan 中加入「外部依賴完整性」維度；如果依賴未安裝，在 PIPELINE.md 標明 |
| **跨檔案 debt** | eval_gate 的 D-005 和 D-008 都是跨檔案 debt，無法在單檔 fix_round 中處理 | SOP Step 4 已明確限制「僅處理單檔零風險 patch」。跨檔案 debt 標記 deferred，待第二輪 |
| **消費者介面變更風險** | 如果要改回傳結構（如 D-002 TypedDict），必須確認所有消費者相容 | 在 ARCH.md 記錄完整消費者列表；對這類 debt 設審查閘門 |

---

## 7. 確認列表（給複製者）

```
□ 確認模組名稱與 repo 路徑（不要猜）
□ 已建立目錄結構（按 §2）
□ 已複製通用模板（按 §3）
□ 已替換模組名稱文件（按 §4）
□ 已新建空白文件（按 §5）
□ 已知風險已讀取（按 §6）
□ 準備進入 SOP Step 1：Bootstrap
```
