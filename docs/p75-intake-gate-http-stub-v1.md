# P7.5 Intake Gate HTTP Stub v1

> **票**：`P75-G7-intake-gate-http-stub-v1`  
> **性質**：本地 **loopback HTTP stub** · `POST /api/intake/gate` 包裝既有 `evaluate_intake_gate`  
> **對齊**：`docs/intake-gate-contract-v1.md` · 計劃 `full-line-to-100-wave-plan-2026-07-13.md` §2.1（→90% HTTP）  
> **實作**：`routing/intake_gate_http_stub_v1.py` · `scripts/run_intake_gate_http_stub_v1.py`

---

## §0 non_claims

| 禁止宣稱 | 說明 |
|----------|------|
| 本 stub **≠** 生產／暗部 `app_api` 已上線 | 僅戰車根 loopback；不改暗部根 |
| 本 stub **≠** Operator Web UI | UI 延後 Wave 4 |
| 本 stub **≠** P7.5 Phase closure | 僅 HTTP 入口增量 |
| 預設 **≠** 寫 outbox | 預設 `mode=preview`；`run` 須明示 |
| 本 stub **≠** 外網暴露 | host 僅允許 `127.0.0.1`／`localhost`／`::1` |

---

## §1 Goal

1. 提供與 80% 計劃 Non-Goal 對齊的 **90% 本地 HTTP 面**：`POST /api/intake/gate`  
2. 請求／回應穩定 `dict`；gate 本體仍走 `routing/intake_gate_layer_v1.evaluate_intake_gate`  
3. CLI：`--once`（預設，不綁埠）與 `--serve`（loopback）  
4. `GET /health` 可探活  

---

## §2 Request

```json
{
  "task_type": "tabular.cleaning.mvp",
  "case_dir": "cases/demo_phase",
  "mode": "preview",
  "policy_path": null,
  "outbox_root": null,
  "enable_notifications": false,
  "include_extended_fixtures": false,
  "no_v1_fallback": false,
  "flags": {}
}
```

| 欄位 | 必填 | 預設 | 說明 |
|------|------|------|------|
| `task_type` | 是 | — | W2 routing catalog |
| `case_dir` | 是 | — | repo-relative 或絕對（由 layer 解析） |
| `mode` | 否 | `preview` | `preview`｜`run` |
| `enable_notifications` | 否 | false | 僅 `mode=run` 時可發 `intake.gate_decision` |

---

## §3 Response

```json
{
  "ok": true,
  "schema_version": "intake_gate_http_stub_v1",
  "message": "gate evaluated",
  "http": {
    "status": 200,
    "path": "/api/intake/gate",
    "stub": true,
    "service": "intake_gate_http_stub_v1",
    "mode": "preview"
  },
  "gate": { "ok": true, "decision": "…", "schema_version": "intake_gate_result_v1" },
  "notification": null,
  "contract_ref": "docs/p75-intake-gate-http-stub-v1.md"
}
```

| HTTP status | 條件 |
|-------------|------|
| 200 | gate `ok=true` |
| 400 | 缺欄／非法 JSON／非法 mode |
| 422 | gate `ok=false`（規則／policy 失敗） |
| 404 | 未知 path |

---

## §4 CLI

```text
# One-shot（不綁埠）
python scripts/run_intake_gate_http_stub_v1.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode preview --format json

# Loopback server
python scripts/run_intake_gate_http_stub_v1.py --serve --host 127.0.0.1 --port 8765
# POST http://127.0.0.1:8765/api/intake/gate
```

---

## §5 Wave 4 UI 對照（placeholder）

| UI 欄位（計劃 Wave 0） | 本 stub 來源 |
|------------------------|--------------|
| `gate.decision` | `gate.decision` |
| `operator_actions[]` | **未實作**（Wave 4） |

---

## §6 驗證

```text
python -m unittest tests.test_intake_gate_http_stub_v1 -v
python scripts/run_intake_gate_http_stub_v1.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --mode preview
```
