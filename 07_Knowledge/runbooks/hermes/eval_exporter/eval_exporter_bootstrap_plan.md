# eval_exporter Bootstrap Plan

> 基於 A_closure NEXT_MODULE_BOOTSTRAP_TEMPLATE.md
> 建立：2026-05-30 | 狀態：plan（未執行）

---

## 模組資訊

| 項目 | 值 | 確認狀態 |
|------|-----|:--------:|
| 模組名稱 | `eval_exporter` | ✅ 已選定 |
| 真實 repo 路徑 | `observability/eval_exporter.py`（推測，基於 eval_gate 同目錄） | ⚠️ **待 discovery 確認** |
| 推測行數 | ~278 行 | ⚠️ 推測（eval_gate ARCH.md 記錄為 278 行） |
| 是否有測試檔案 | `tests/test_eval_exporter.py`（推測） | ⚠️ **待 discovery 確認** |
| 推測測試行數 | ~111 行 | ⚠️ 推測（eval_gate discovery.md 記錄） |
| 消費者 | eval_gate → eval_exporter → JSONL（推測） | ⚠️ **待 discovery 確認** |
| 測試 venv 路徑 | `01_Environments/python_venvs/gov_core_system/`（推測） | ⚠️ **待 discovery 確認** |

---

## 確認列表

```
□ 目錄骨架已建立（00_skill / 10_memory / 20_runtime / 90_runs）          → ✅ 完成
□ SKILL 檔案已建立（SKILL_EVAL_EXPORTER_HYGIENE_OWNER.md）               → ✅ 完成
□ 記憶檔案已建立（ARCH / STYLE / DEBT_LOG / PLAYBOOK）                   → ✅ 完成
□ 運行時模板已複製（TASK_INTAKE / REPORT / APPLY_PLAYBOOK / APPLY_CONFIRM） → ✅ 完成
□ PIPELINE.md 已建立（佔位）                                              → ✅ 完成
□ bootstrap run note 已建立                                              → ⬜ 待建立
□ 任務說明文件已建立（bootstrap_plan / discovery_task / scan_task）       → ✅ 完成
□ 空白 run note 模板已建立                                                → ⬜ 待建立
```

---

## 下一步

1. 設置好 90_runs/ 下的 bootstrap run note（`YYYY-MM-DD_eval_exporter_bootstrap.md`）
2. 準備好 discovery / scan 的空白 run note 模板
3. 以上完成後即可啟動 SOP Step 2（Discovery）

---

## 依賴

- 本計畫不需要任何 repo 修改
- 所有文件位於 `/mnt/d/hermes-workspace/infra_owner/eval_exporter/`
- 首次 discovery 時需獨佔 `read_file` 權限掃描真實 repo 原始碼
