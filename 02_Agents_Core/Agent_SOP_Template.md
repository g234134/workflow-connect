# Agent_SOP_Template — 兵部標準兵裝 SOP

> **能用就用，嚴禁重複撰寫；不能用，再造新的。**
> 任何新 Agent 在開工前**必須**先讀這份；下方列出的「標準兵裝」皆已落地，請直接 import，不要重發明。

---

## 0. 強制檢查清單（落地前自問）

- [ ] 路徑用 `gov_paths.py`，**不寫死磁碟字串**
- [ ] 繼承 / 內含 `Base_Agent`（取得 `run_id`、五態狀態、C3 JSONL）
- [ ] 去重透過 `Chariot_Registry`（SQLite），**不再**新增 hashes.txt
- [ ] `Status.json` 採**局部回寫**（一個 Agent 一個鍵）
- [ ] Telegram 採**批次 + 終戰報**，禁止每筆推播
- [ ] 失敗→**C3_Logs/<AgentName>/failed_events.jsonl** + 跳過，禁止熔斷終止
- [ ] 大檔／高耗時操作走**波次 (wave)** + 檢查點

---

## 1. 標準兵裝（直接 import）

| 用途 | 位置 | 重要 API |
| --- | --- | --- |
| 路徑解析 / 密鑰 | `gov_paths.py` | `get_tang_gov_root()` · `resolve_agent_output_path(root, dept, sub)` · `get_artifact_path(key)` · `get_secret(name, default)` |
| Run/狀態/日誌 | `Base_Agent.py` | `Base_Agent(dest_root=, department=, agent_name=)` · `agent.run_id` · `agent.set_status(s, reason=)` · `agent.log_event(event=, **fields)` |
| 內容指紋 / 多 Agent 去重 | `Chariot_Registry.py` | `Chariot_Registry()` · `.has(sha)` · `.add(sha, agent=, source_path=, clean_status=, extension=, original_type=)` · `.add_event(...)` · `.count()` |
| 編碼還原 | `Recovery_Agent.ENCODING_FALLBACKS` · `Code_Cleaner_Throttled_Agent._decode_full(raw)` | 全鏈解碼，回 `(text, encoding)` |
| JSON / JSONC / JSON5 修復 | `GroqHybridRecovery_Agent` | `_try_json5` · `_try_parse_json_text` · `_try_kit_line_json` · `_extract_json_from_llm` |
| Groq 雲修（節流） | `Code_Cleaner_Throttled_Agent` | `_groq_json_repair(text, name)` · `_groq_recover_decode_fail(raw, name, lang)` · `GROQ_DELAY_SEC` |
| Telegram 推播 | `Code_Cleaner_Throttled_Agent._telegram_alert(text)` | 自動帶 UA 與 chat_id；失敗靜默 |
| 上行指令長輪詢 | `Telegram_Listener_Agent` / `_telegram_listener.py` | `--mode loop|once` |

> 缺什麼**先**翻表上對應的兵裝，找不到再開新檔。

---

## 2. 三大強制設計模式

### 2.1 SQLite 指紋去重（取代任何 hashes.txt）

```python
from Chariot_Registry import Chariot_Registry

reg = Chariot_Registry()                # 預設 04_Workflows/Chariot_Registry.db
if reg.has(sha):                        # 多 Agent 併行安全（WAL）
    return  # 已處理過，跳過
reg.add(sha, agent=self.AGENT_NAME, source_path=fp,
        clean_status="ok", extension=ext, original_type=otype)
```

舊 `hashes.txt` 已遷移；新 Agent **禁止**再寫文字檔指紋。

### 2.2 Status.json 局部回寫（一個 Agent 一個鍵）

```python
def _patch_status(self, block: Dict[str, Any]) -> None:
    sp = os.path.join(resolve_agent_output_path(self.dest_root, "04_Workflows"), "Status.json")
    data = {}
    if os.path.isfile(sp):
        try:
            with open(sp, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data[self.STATUS_KEY] = block            # 例：'warning_repair' / 'code_cleaner_throttle'
    data["updated_at"] = _utc_iso()
    with open(sp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

- 一個 Agent 對應**一個**頂層鍵；**禁止**整檔覆寫他人區塊。
- 每 N 筆（建議 100）或每完成一個 wave 觸發一次，避免高頻 IO。
- listener (`PID 21492`) 只認檔案異動 → 自然偵測到。

### 2.3 Telegram 批次 + 終戰報（禁止逐筆）

```python
TELEGRAM_FAILURE_BATCH = int(get_secret("THROTTLE_TELEGRAM_FAIL_BATCH", "") or "50")

def maybe_batch_alert(...):
    if failures_since_last >= TELEGRAM_FAILURE_BATCH:
        _telegram_alert(_compose_digest("批次"))
        failures_since_last = 0

# 結束時統一發一次「終戰報」，含：
#   - run_id、scanned/repaired/failed
#   - 失敗 bucket 分析（為什麼失敗：編碼／結構／超大／API）
#   - 索引異動摘要（registry.count() 前後差）
```

---

## 3. 失敗處理與容錯

- **絕對禁止**因 API 連敗或單檔錯誤而 `sys.exit` / `raise`。
- 失敗檔案：
  1. `clean_status='failed'` 寫回該檔（若有持久化記錄）
  2. 一行 NDJSON 寫到 `03_RAG_Database/C3_Logs/<AgentName>/failed_events.jsonl`
  3. SQLite `add(sha, clean_status='failed', ...)`
  4. 累計到 `Status.json[<key>].total_failed_count` 與 `failure_buckets`
- 連續失敗只**觀測**（如 `groq_fail_streak`），不熔斷。

---

## 4. 雲端節流原則（Groq / 任何外部 API）

- **本地優先**：解碼鏈 → `json/json5` → 啟發式 → 才考慮上雲。
- **白名單**：副檔在 `{.py, .php, .json, .jsonc, .json5, .yml, .yaml, .toml}` 才允許 Groq；其他類型一律本地處理或標 `failed`。
- **節流間隔**：`GROQ_DELAY_SEC`（預設 0.35s），在環境變數調整。
- **批次規模**：每呼叫一次累計到 `groq_attempts_total / groq_success_total`，寫進 `Status.json`。

---

## 5. 波次與檢查點（長跑作業）

- 每 **500 件**為一波（可調 `WAVE_DEFAULT`）。
- 每完成一波：
  - 寫狀態檔（`.<agent>_state.json`）
  - 局部回寫 `Status.json`
  - SQLite 已即時寫，不需另外 flush
- 中斷可重入：以 `Chariot_Registry.has(sha)` 自然續跑。

---

## 6. 新 Agent 骨架（最小可用版）

```python
# My_Agent.py
from Base_Agent import AgentStatus, Base_Agent
from Chariot_Registry import Chariot_Registry
from Code_Cleaner_Throttled_Agent import _telegram_alert
from gov_paths import get_tang_gov_root, resolve_agent_output_path

class My_Agent:
    AGENT_NAME = "My_Agent"
    DEPARTMENT = "兵部"
    STATUS_KEY = "my_agent"           # Status.json 內的專屬鍵

    def __init__(self):
        self.dest_root = get_tang_gov_root()
        self.agent = Base_Agent(dest_root=self.dest_root,
                                department=self.DEPARTMENT,
                                agent_name=self.AGENT_NAME)
        self.registry = Chariot_Registry()
        self.c3_dir = ...  # C3_Logs/<AGENT_NAME>

    def run(self):
        self.agent.set_status(AgentStatus.Running.value, reason="start")
        # ... wave loop with registry dedup + _patch_status + batch alert ...
        self.agent.set_status(AgentStatus.Success.value, reason="done")
        _telegram_alert("[My_Agent] 終戰報 ...")
```

---

## 7. 命名與目錄

- Agent 檔：`02_Agents_Core/<Name>_Agent.py`，類別名 `<Name>_Agent`。
- 失敗日誌：`03_RAG_Database/C3_Logs/<Name>_Agent/failed_events.jsonl`。
- 產出：`05_Temp_Cache/<sub>` 或 `06_Exports_Output/<sub>`，子目錄須先在 `Master_Map.sub_directories` 註冊。
- 狀態鍵：`Status.json` 內小寫 + 底線（如 `code_cleaner_throttle`、`warning_repair`）。

---

## 8. 違規清單（PR 直接退）

1. 寫死 `D:\` 或 `C:\` 路徑
2. 自建 `*.txt` 雜湊去重
3. 整檔覆寫 `Status.json`（清掉他人區塊）
4. 對 Groq / 外部 API 連敗熔斷終止整個 run
5. 逐筆 Telegram 推播
6. 不寫 `failed_events.jsonl` 就 swallow exception
7. 跳過 `Base_Agent`，自己造 run_id / log

---

**結論**：先翻 §1 兵裝表 → 套 §2 三模式 → 走 §6 骨架。  
寫之前問一句：「這件事是不是已有兵裝？」是 → 直接 import；否 → 先補進兵裝表，再寫。
