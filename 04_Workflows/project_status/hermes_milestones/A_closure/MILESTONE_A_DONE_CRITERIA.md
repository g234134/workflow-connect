# MILESTONE_A_DONE_CRITERIA.md

> 建立日期：2026-05-30
> 定義：里程碑 A — 第一條可復用的「單線 owner 閉環」已被執行過一次，且可被複製到第二個模組。

---

## 1. 里程碑 A 的定義

里程碑 A = 在一個真實模組（eval_gate）上，完整執行一次 **Infra Hygiene Owner 閉環**，證明以下 8 項能力全部可運作：

| 能力 | 說明 |
|------|------|
| discovery | 從零找到模組原始碼位置、公開介面、依賴鏈、消費者 |
| readonly scan | 對模組執行結構化只讀衛生檢查（6 個維度） |
| suggested patch | 產出建議修正版（zero/low-risk only），不修改 repo |
| review gate | 對建議版進行結構化審查（接受/拒絕/partial） |
| apply plan | 產出詳細套用計畫（按行號、按順序），供人類或 Cursor 執行 |
| replayable run record | 所有步驟有 `90_runs/` 記錄，可重播 |
| debt/log status update | 技術債狀態流轉（open → fixed_suggested → fixed_in_repo）可追溯 |
| style/playbook feedback loop | review 發現回寫至 STYLE.md / PLAYBOOK.md，形成慣例閉環 |

## 2. 已滿足的各項（評估日期：2026-05-30）

| # | 能力 | 支撐證據 | 狀態 |
|---|------|----------|:----:|
| 1 | discovery | `90_runs/2026-05-30_discovery.md` — 定位了 eval_gate 在 `observability/eval_gate.py`，識別 5 條規則、3 個 CLI、3 個消費者 | ✅ |
| 2 | readonly scan | `90_runs/2026-05-30_scan_readonly.md` — 6 維度衛生檢查，產出 10 筆 DEBT LOG（D-001 ~ D-010），含結構分析、CLI 一致性、耦合點 | ✅ |
| 3 | suggested patch | `20_runtime/eval_gate.suggested.v1.py`（12128 bytes）— docstring + logging + 註解純加法，無語意變更 | ✅ |
| 4 | review gate | `90_runs/2026-05-30_review_v1.md` — 結構化審查，接受/保留/修改三級裁決，含審查員主觀意見（like/dislike）、下次規則 | ✅ |
| 5 | apply plan | `90_runs/2026-05-30_apply_plan_v1.md` — 8 步計畫，含靜態比對表、逐行套用順序、後驗證清單、人工確認欄位 | ✅ |
| 6 | replayable run record | 7 份 `90_runs/` 記錄：bootstrap → discovery → scan → fix_round1 → review_v1 → apply_plan_v1 → apply_result_v1 | ✅ |
| 7 | debt/log status update | DEBT_LOG.md — 完整狀態機（10 種狀態）、D-001/D-003/D-010 從 open → fixed_suggested → fixed_in_repo、統計摘要（10 total / 3 fixed / 7 open） | ✅ |
| 8 | style/playbook feedback loop | STYLE.md §9 從 proposed → confirmed（依 review 意見）；PLAYBOOK.md 新增 P-003 實例、P-006 完成信標、P-007 輕量方案、P-010 標記準則 | ✅ |

**全部 8 項能力均已證明可在一個真實模組上運作。**

## 3. 未完全滿足但不影響 A 判定的項目

以下項目存在缺口，但均屬於「流程成熟度」或「第二模組環境差異」範疇，**不影響里程碑 A 的 DONE 判定**：

| 項目 | 缺口 | 為什麼不阻擋 |
|------|------|-------------|
| **自動化重播** | 所有步驟目前為手動執行（Hermes 的 tool calls），無獨立的 `replay.sh` 或 CI pipeline | A 只要求「可回放」，不要求「自動回放」。7 份 run notes 已足夠人工重新執行。自動化是里程碑 B 的優化項 |
| **測試環境確認** | 實際的 unittest 執行依賴 `gov_core_system` venv，未在此 workspace 中驗證 venv 可用性 | apply_result_v1 已確認「依人工套用，24 項 unittest 全數通過」。測試環境問題屬於第二模組的 bootstrap 風險，非 A 的缺口 |
| **CI/CD 系統識別** | CI 平台仍 unknown（無 `.github/workflows/`、無 Makefile）。PIPELINE.md 標記 `needs-confirmation` | eval_gate 的 patch（docstring + logging）不依賴 CI 執行。CI 識別是第二模組的前置工作 |
| **Python 版本確認** | pycache 顯示 3.14 和 3.10 並存，未在 venv 下驗證 | 不影響 patch 內容（stdlib only），不影響 review/apply 流程 |
| **debt lifecycle 完全閉環** | D-001/D-003/D-010 已從 open → fixed_in_repo，但另外 7 條仍 open | A 不要求「全部 debt 修完」，只要求「整條 pipeline 走過一次關」。剩餘 debt 屬於模組常態維護 |

## 4. 為什麼 eval_gate / 當前 owner 流程足以作為 A 的樣板

1. **真實性**：eval_gate 是真實 repo 中的真實模組（`observability/eval_gate.py`），有測試（24 項 unittest）、有消費者（k2_langgraph_flow）、有 CLI（3 個入口）。
2. **端到端**：流程從 bootstrap（零知識）到 apply（patch 套入 repo，測試通過），所有階段都有對應文件。
3. **工具鏈獨立**：唯一依賴是 stdlib（`typing`、`functools`、`logging`）+ `contract.constants`，無第三方套件。第二模組如果有第三方依賴，流程不變，只需在 discovery 階段多檢查 `requirements.txt` / `pyproject.toml`。
4. **審查閘門運作**：review_v1.md 證明審查不只是 checkbox，而是真正的技術審查（有 like/dislike、有下次規則、有 STYLE/PLAYBOOK 回寫）。
5. **DRY 文件**：APPLY_PLAYBOOK.md、APPLY_CONFIRM_TEMPLATE.md、REPORT_TEMPLATE.md、TASK_INTAKE_TEMPLATE.md 都不是一次性產物 — 它們可以跨模組復用。
6. **所有 SOP 都在 patch 之前建立**：不是先做 patch 再補 SOP。discovery/scan 先產出 DEBT_LOG，fix_round 基於 debt 優先級選擇。

## 5. 判決

```
里程碑 A：可判定 DONE（2026-05-30）
證據：本目錄 + /mnt/d/hermes-workspace/infra_owner/eval_gate/
```

下一階段（里程碑 B）的起點：用本 pack 中的 `NEXT_MODULE_BOOTSTRAP_TEMPLATE.md` 複製到第二模組。
