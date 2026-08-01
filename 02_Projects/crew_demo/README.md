# crew_demo

啟用 venv → 改 .env 切供應商 → python main.py → 看 output.txt

**Canonical 路徑**：`D:\大唐三省六部\02_Projects\crew_demo`

## 不想每次手打指令（推薦）

1. 用 Cursor **開資料夾**：`D:\大唐三省六部\02_Projects\crew_demo`
2. `Ctrl+Shift+B`（或選單 **Terminal → Run Task…**）→ 選 **「CrewAI：本機 Ollama 執行」**
3. 結果在 `output.txt`；若要開檔可再 Run Task → **「CrewAI：僅開啟 output.txt」**

或直接雙擊／在檔總管對 `run_crew.ps1` 右鍵「使用 PowerShell 執行」（若被政策擋，先在 PowerShell 執行過一次即可）。

## 啟用 venv（手動版，與上列二選一即可）

```powershell
. D:\大唐三省六部\04_Workflows\Enter-Agency.ps1
cd D:\大唐三省六部\02_Projects\crew_demo
```

## 切換模型

`.env` 改 `LLM_PROVIDER`：
- `ollama` 本機，不需 key
- `groq` 需要 `GROQ_API_KEY`
- `nvidia` 需要 `NVIDIA_NIM_API_KEY`
- `huggingface` 需要 `HUGGINGFACE_API_KEY`

執行：

```powershell
python .\main.py
```

換主題：

```powershell
$env:TOPIC = '量子電腦'; python .\main.py
```

## 啟用工具

`.env` 設 `ENABLE_TOOLS=true`，並填 `TAVILY_API_KEY` 或 `FIRECRAWL_API_KEY`（有填的才會啟用）。
