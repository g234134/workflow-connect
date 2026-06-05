# Phase 8.6a — Minimal Bridge API Endpoint MVP (v0.1)

> **工單編號語意**：本檔的 **「Phase 8.6a Minimal Bridge API Endpoint」** 為 HTTP 接線工單。  
> **依賴**：`PHASE8_6_MINIMAL_ORCHESTRATION_BRIDGE_MVP_v0.1.md`（`run_minimal_orchestration_bridge`）；**不修改** bridge 商務邏輯。

---

## 1. 目標

在 `app_api.py` 新增最小 `POST` 端點，將巢狀 JSON 請求轉交 `run_minimal_orchestration_bridge()`，並**直接**回傳 bridge 結果 dict。

**非目標**：重構 `app_api.py`、改既有 endpoint、`/healthz` 路由表、全域 500 handler、DB、`WORKFLOW_INDEX`、Playwright、UI、auth overhaul。

---

## 2. 檔案落點

| 路徑 | 動作 | 職責 |
|------|------|------|
| `gov_core_system/app_api.py` | **修改** | `POST /api/orchestration/bridge` |
| `gov_core_system/tests/test_app_api_orchestration_bridge.py` | **新增** | API 單測 |
| `04_Workflows/PHASE8_6A_MINIMAL_BRIDGE_API_ENDPOINT_MVP_v0.1.md` | **新增** | 本規格 |

---

## 3. 端點

| 項目 | 值 |
|------|-----|
| Method / Path | `POST /api/orchestration/bridge` |
| Request model | `OrchestrationBridgeApiBody`（`intake: object` → handler 內 `IntakeGateRequest.model_validate`；`browser: BrowserBridgeSection \| null`） |
| Handler | `api_orchestration_bridge` |

### 3.1 請求 body（無外層 envelope）

```json
{
  "intake": {
    "explicit_task_type": "chariot.factory",
    "description": "wave 清洗"
  },
  "browser": {
    "plan": { "plan_id": "x", "steps": [] },
    "force_browser": false
  }
}
```

### 3.2 回應 body

完整 bridge dict（`schema_version`、`flow`、`intake`、`phase6_5_pre_state`、`browser`、`stages`），**不多包**一層。

---

## 4. HTTP 語意

| 情境 | HTTP |
|------|------|
| FastAPI / Pydantic 驗證失敗（含非法 `intake`） | **422** `{"detail": [...]}` |
| Bridge 正常執行（含 reject/defer、`ok: false`） | **200** |
| Handler 未預期例外 | **500** `{ok, message, error_type}`（**無** traceback） |

API handler 內以 `IntakeGateRequest.model_validate` 驗證 `intake`（回 **422** 使用 `jsonable_encoder`，不修改全域 validation handler）；空 `intake` 不進 bridge。

---

## 5. 驗收

```text
cd <gov_core_system 根>
python -m unittest tests.test_app_api_orchestration_bridge -v
python -m unittest tests.test_minimal_orchestration_bridge tests.test_intake_decider tests.test_browser_runner -v
```

建議回歸：`tests.test_monitoring_api`、`tests.test_dlq_api`（皆使用 `TestClient(app_api.app)`）。

---

## 6. 下一波

- `WORKFLOW_INDEX.md` 登錄
- `/healthz` routes 列表（需尚書省授權改既有輸出）
- Admin token / idempotency（若產品化需要）
