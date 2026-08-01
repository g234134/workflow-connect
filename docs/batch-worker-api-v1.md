# Batch Worker API v1（P8 真 Worker）

> **票**：`P8-T4-worker-api-batch-v1`  
> **日期**：2026-07-13

---

## non_claims

| 本交付 **不是** | 說明 |
|-----------------|------|
| ≠ Cursor Multi-Chat 自動派工 | 不 spawn Implementer chat |
| ≠ 自動寫 `*_state.md` / Progress | `writes_ticket_state=false` |
| ≠ 遠端 production fleet | 本機／env 設定的 Worker base URL |
| ≠ 取代 `--mode mock` | mock 仍為預設回歸路徑 |

---

## 契約

| 項 | 值 |
|----|-----|
| Method / Path | `POST /api/batch/worker/run` |
| Health | `GET /healthz` |
| Env | `GOV_BATCH_WORKER_API_URL`（base URL，無尾斜線） |

請求 JSON（節錄）：`subtask_id`、`subtask`、`prompt?`、`parent_frame?`、`force_fail?`  
回應 dict：`ok`、`status`、`message`、`subtask_id`、`prompt`、`latency_ms`、`writes_ticket_state`

---

## CLI

```powershell
# 終端 A：起 Worker API
$env:PYTHONPATH = "04_Workflows"
python -m _batch_orchestrator.cli serve-worker --host 127.0.0.1 --port 8765

# 終端 B：真 HTTP 跑 batch
python -m _batch_orchestrator.cli run --manifest tests/fixtures/sample_manifest.json --mode worker_api --worker-url http://127.0.0.1:8765 --limit 2
```

---

## 驗收

```powershell
$env:PYTHONPATH = "04_Workflows"
python -m unittest tests.test_batch_worker_api -v
```
