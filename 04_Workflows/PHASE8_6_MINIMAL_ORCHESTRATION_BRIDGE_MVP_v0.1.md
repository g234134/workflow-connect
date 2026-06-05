# Phase 8.6 — Minimal Orchestration Bridge MVP (v0.1)

> **工單編號語意**：本檔的 **「Phase 8.6 Minimal Orchestration Bridge」** 為 intake → Phase 6.5 pre-state → optional browser 串接工單。  
> **不同軌**：`gov_core_system/output/phase5-8_roadmap.md` 表中 **8.6 Phase 3 回顧與 V3 規劃** 為治理路線，與本工單**無對應關係**；引用戰報或里程碑時請用完整工單名稱。

---

## 1. 目標

在暗部 `gov_core_system` 提供**可重跑、結構化 `dict`** 的最小編排橋，串接已完成的三條線：

1. **Phase 7.5** — `parse_and_decide`（intake / gate）
2. **Phase 6.5** — `phase6_5_pre_state`（已由 intake 附加）
3. **Phase 8.5** — 可選 `run_plan`（InMemory DOM；無 Playwright）

**非目標（v0.1 不做）**：`app_api.py`、`WORKFLOW_INDEX.md`、DB、`pipeline_meta`、Playwright adapter、UI、`task_routing` 自動派工、`suggest_browser_plan_from_intake`。

---

## 2. 與既有制度的關係

| 既有資產 | 關係 |
|----------|------|
| `PHASE7_5_INTAKE_GATE_MVP_PLAN_v0.1.md` | intake 請求／回應契約 |
| `PHASE8_5_BROWSER_AUTOMATION_MVP_v0.1.md` | browser `plan` 步驟契約 |
| `DATA_CONTRACT_AND_EVENT_MODEL_v0.1.md` | `phase6_5_pre_state` 權威 |
| `core/orchestrator.py` | **不同域**（ingest/query）；僅作 `dict` 形狀參考 |

---

## 3. 檔案落點

| 路徑 | 動作 | 職責 |
|------|------|------|
| `04_Workflows/PHASE8_6_MINIMAL_ORCHESTRATION_BRIDGE_MVP_v0.1.md` | **新增** | 本規格 |
| `gov_core_system/core/minimal_orchestration_bridge.py` | **新增** | `run_minimal_orchestration_bridge()` |
| `gov_core_system/core/schemas/orchestration_bridge.py` | **新增** | Pydantic 請求區段 |
| `gov_core_system/shared/schemas/orchestration_bridge_v1.json` | **新增** | 跨模組 JSON 契約 |
| `gov_core_system/tests/test_minimal_orchestration_bridge.py` | **新增** | 單元測試 |

**不修改**：`intake_decider.py`、`browser_runner.py`、`app_api.py`、`WORKFLOW_INDEX.md`。

---

## 4. 請求契約（巢狀）

```json
{
  "intake": { "description": "...", "explicit_task_type": "chariot.factory" },
  "browser": {
    "plan": { "plan_id": "...", "stop_on_error": true, "steps": [] },
    "force_browser": false
  }
}
```

| 欄位 | 必填 | 說明 |
|------|------|------|
| `intake` | 是 | Phase 7.5 `IntakeGateRequest` 欄位（見 `intake_gate_v1.json`） |
| `browser` | 否 | 省略則 browser 階段 `skipped` |
| `browser.plan` | 條件 | 含非空 `steps[]` 才可能執行 runner |
| `browser.force_browser` | 否 | 預設 `false`；`true` 時即使 `decision != accept` 仍跑 plan |

---

## 5. Browser 觸發規則

| 條件 | 行為 |
|------|------|
| 無 `browser` 區段 | `skip_reason=no_browser_section` |
| `browser.plan` 缺失或 `steps` 為空 | `skip_reason=no_plan` |
| `intake.ok == false` 且未 `force_browser` | `skip_reason=intake_failed` |
| `decision != accept` 且未 `force_browser` | `skip_reason=gate_not_accept` |
| 其餘 | 執行 `validate_plan` + `run_plan` |

---

## 6. 回應契約（`run_minimal_orchestration_bridge` → `dict`）

| 欄位 | 說明 |
|------|------|
| `ok` | 全流程：intake 驗證失敗 → `false`；defer/reject 且未跑 browser → `true`；有跑 browser → `intake.ok ∧ browser.result.ok` |
| `message` | 人讀摘要 |
| `schema_version` | `orchestration_bridge_v1` |
| `flow` | `minimal_intake_browser` |
| `intake` | 完整 Phase 7.5 輸出 |
| `phase6_5_pre_state` | 與 `intake.phase6_5_pre_state` 相同（頂層重複，方便下游） |
| `browser` | `{skipped, skip_reason, plan_id, validated, result}` |
| `stages` | `[{name:intake,...}, {name:browser,...}]` |

---

## 7. 驗收

```text
cd <gov_core_system 根>
python -m unittest tests.test_minimal_orchestration_bridge -v
python -m unittest tests.test_intake_decider tests.test_browser_runner -v
```

---

## 8. 下一波（非 MVP）

- HTTP：`POST /api/orchestration/bridge`（`app_api.py`）
- `WORKFLOW_INDEX.md` 登錄工作流
- `suggest_browser_plan_from_intake()` 啟發式 plan 生成
- 與 `task_routing` / wave runner 接線（accept 後自動派工）
- Playwright adapter（8.5b）注入 `DomAutomationPort`
