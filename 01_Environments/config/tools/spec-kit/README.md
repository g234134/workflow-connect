# tools / spec-kit

## 用途（吏部 · 規格治理）

本目錄為 **Spec-Kit / specify CLI** 的總部專用工具環境掛載位。施工前規格、契約與模板應在此獨立 Python 環境（`.venv` 或 `uvx`）中執行，**不可**共用暗部 `gov_core_system` 的 `Scripts\` 或 `Lib\`。

## 禁則

**不得放暗部 venv 相關檔案**（禁止將暗部 `requirements.txt` 複製覆蓋至此、禁止 `pip install` 進 `python_venvs\gov_core_system`）。

## 未來可能放置的內容

- `.venv\` 或 `uv.lock`：總部專用工具環境（Phase 8 建立）
- `INSTALL.md`：`specify --help` 與 spec 專案初始化 dry run
- `templates\`：spec 專案模板（若官方提供）
