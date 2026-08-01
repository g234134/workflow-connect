# W12-T2 · Sandbox E2E Checkpoint B Full Integration v1

> **角色**: Scribe / Implementer (docs-only)  
> **Wave**: Wave 12 — Sandbox e2e × W6-T6 integration  
> **建立日期**: 2026-06-16  
> **狀態**: P3 docs review ready

---

## FRAME

### Goal
將 Sandbox E2E 的 S12 (Checkpoint B) 從 orchestrator 內嵌 gate 改為與一般 run path **共用 W6-T6 integration layer**，使 sandbox 與 standard line 共用同一套 checkpoint trigger 語意與 delivery plan 產出邏輯。

### Scope
- [x] **P1**: Orchestrator 改呼叫 `hitl/checkpoint_b_integration_v1.py` (`maybe_create_checkpoint_b`)
- [x] **P2**: 更新 sandbox runbook 與 CP-B doc（sandbox consumer）
- [x] **P3**: 本 state 檔記錄整合語意、風險點、P1/P2/P3 收口計畫

### Non-scope
- 不改 `hitl/checkpoint_b_integration_v1.py` 核心邏輯（W6-T6 已定稿）
- 不改 sandbox manifest 格式（W12-T1 已定義）
- 不改 production delivery / notify 流程
- 不擴展 sandbox allowlist（仍僅 `additional_demo`）

### Key Semantics（P3 設計核心）

#### 1. S12 不再是特殊 inline gate
Sandbox e2e 的 S12 不再使用 `can_proceed_sandbox_bundle` 作為 orchestrator 內嵌判斷，而是與一般 run path **共用 W6-T6 integration layer**：

```python
# P1 前 (已棄用)
if can_proceed_sandbox_bundle(output_guard, auto_approve_delivery):
    proceed_to_bundle()

# P1 後 (現行)
result = maybe_create_checkpoint_b(
    case_dir=case_dir,
    execution_summary=execution_summary,
    output_guard=output_guard,      # warning/blocked/ok
    artifacts=artifacts,
    auto_approve=auto_approve_delivery,
)
delivery_plan = result["delivery_plan"]
proceed = _can_proceed_sandbox_bundle_after_checkpoint_b(delivery_plan)
```

#### 2. CP-B 狀態檔位置（與一般 run path 一致）

```
{outbox_root}/{case_ref}/checkpoint_B-{timestamp}.json
```

範例：`outbox/additional_demo/checkpoint_B-2026-06-16T08-30-00Z.json`

- 由 `maybe_create_checkpoint_b()` 統一寫入
- 路徑使用三層 fallback（見 `docs/checkpoint-b-integration-v1.md` §7）
- Sandbox 與一般 run 共用相同 checkpoint file schema

#### 3. Sandbox Bundle Manifest 位置（獨立於 CP-B）

```
{outbox_root}/sandbox_delivery/{case_ref}/{timestamp}_{experiment_id_prefix}/
  manifest.json
  report.json
  cleaning_stats.json
  ...
```

範例：`outbox/sandbox_delivery/additional_demo/20260616T083012Z_a1b2c3d4/manifest.json`

- **CP-B 狀態檔** 記錄 human gate 決策（approve / request_changes / hold）
- **Manifest** 記錄 sandbox delivery bundle 內容與 checkpoint_trace
- 兩者路徑分離，避免 sandbox delivery 被誤認為 checkpoint state

### Acceptance Criteria

| AC | 描述 | P1 狀態 |
|----|------|---------|
| **AC-1** | Sandbox e2e Phase-1 後呼叫 `maybe_create_checkpoint_b`，不再使用 `can_proceed_sandbox_bundle` 內嵌邏輯 | ✅ |
| **AC-2** | CP-B 檔案寫入路徑與一般 run path 一致：`{outbox_root}/{case_ref}/checkpoint_B_*.json` | ✅ |
| **AC-3** | Sandbox manifest 仍獨立於 `{outbox_root}/sandbox_delivery/{case_ref}/...`，不與 CP-B 混淆 | ✅ |
| **AC-4** | `checkpoint_b_status` 包含 `integration_layer: hitl.checkpoint_b_integration_v1`，與一般 run path 對齊 | ✅ |
| **AC-5** | 文件明確記載：S12 語意、CP-B 路徑、manifest 路徑、ok/warning/auto-approve 行為差異 | ✅（P3） |
| **AC-6** | `can_proceed_sandbox_bundle` 仍保留於 `delivery/sandbox_delivery_bundle_v1.py` 供舊 consumer，但 orchestrator 不再 import | ✅ |

---

## STATE

```yaml
overall_status: done
current_owner: closed
last_updated: 2026-07-28T23:55+08:00
auth: 尚書省「全開」
next_action: closed · P1+P2 docs+P3 done · tip#1 仍 P6 WATCH
```

---

## B_REPORT（Implementer P1 + Scribe P3）

### P1 實作摘要（已完成）

#### changed_files
- `scripts/run_agent_standard_case_experiment.py`
- `tests/test_agent_standard_case_experiment.py`（sandbox e2e integration_layer 斷言）
- `04_Workflows/tickets/W12-T2-sandbox-e2e-checkpoint-b-full-integration-v1_state.md`（新建）

#### behavior_notes
- `_execute_sandbox_e2e_run` Phase-1 完成後呼叫 `_resolve_checkpoint_b_after_run`（含 `outbox_root_override` pass-through）。
- 新增 `_can_proceed_sandbox_bundle_after_checkpoint_b`：依 integration layer 的 `status` / `delivery_plan_action` / `would_trigger` 決定是否進 Phase-2 bundle。
- `checkpoint_b_status` 對齊一般 run path（`integration_layer`、`status`、`would_trigger`、`integration`）；另保留 `sandbox_bundle_gate` 追蹤 gate reason。
- CP-B 檔案寫入 `{outbox_root}/{case_ref}/...`；sandbox manifest 仍走 `{outbox_root}/sandbox_delivery/{case_ref}/...`。
- `can_proceed_sandbox_bundle` 仍保留於 `delivery/sandbox_delivery_bundle_v1.py`；orchestrator 主流程不再 import／呼叫。

#### verification
```text
python -m unittest tests.test_checkpoint_b_integration_v1 -v  → OK (11 tests)
python -m unittest tests.test_agent_standard_case_experiment -v → OK (26 tests)
```

### P2 測試補齊摘要（本輪完成）

#### changed_files
- `tests/test_agent_standard_case_experiment.py`（新增 4 個 sandbox e2e checkpoint B 測試）

#### added_tests
| 測試名稱 | 鎖定行為 |
|---------|----------|
| `test_sandbox_e2e_checkpoint_b_skipped_ok_path_completes_bundle` | Sandbox E2E ok path：checkpoint B skipped（`ok_no_human_gate`），bundle 完成，無 CP-B 檔案 |
| `test_run_mode_checkpoint_b_stops_without_auto_approve_delivery` | Run mode（非 sandbox）：experimental fixture 停於 checkpoint B，`export.delivery_bundle` 未執行 |
| `test_sandbox_e2e_checkpoint_b_status_integration_layer_structure` | 驗證 `checkpoint_b_status` integration layer 結構完整（`integration_layer`、`integration` sub-dict、`delivery_plan_action`、`sandbox_bundle_gate`）|
| `test_sandbox_e2e_warning_writes_checkpoint_b_and_blocks_bundle` | **W12-T2-sandbox-e2e-warning-blocked-regression-v1**：warning path 寫入 CP-B、final_status=`sandbox_e2e_blocked_at_checkpoint_b`、bundle 被擋、無 sandbox manifest |

#### verification
```text
python -m unittest tests.test_agent_standard_case_experiment -v → OK (33 tests, +4 total from base 29)
```

### P3 文件補充（本輪）

- 本 state 檔 FRAME 區：Goal/Scope/Non-scope/AC 完整定義
- 本 state 檔 Key Semantics：CP-B 路徑與 manifest 路徑分離語意
- 本 state 檔 Risk Analysis：ok/warning/auto-approve 行為差異

### P2 Documentation（2026-07-28 · 全開收口）

#### changed_files
- `docs/tabular-controlled-end-to-end-delivery-sandbox-v1.md` §4 S12 → W6-T6 `maybe_create_checkpoint_b`
- `docs/checkpoint-b-integration-v1.md` §9–§10 sandbox consumer

#### verification（全開再核）
```text
python -m unittest \
  tests.test_agent_standard_case_experiment.TestAgentStandardCaseExperiment.test_sandbox_e2e_checkpoint_b_status_integration_layer_structure \
  tests.test_agent_standard_case_experiment.TestAgentStandardCaseExperiment.test_sandbox_e2e_warning_writes_checkpoint_b_and_blocks_bundle \
  -v → OK
```

#### Phased Plan 勾選
- [x] P1 Implementation
- [x] P2 Documentation Update
- [x] P3 State Consolidation

---

## Risk Analysis（P3 設計重點）

### Risk-1: `ok` path 行為差異

| Path | `output_guard.status=ok` + `auto_approve=False` | Result |
|------|-----------------------------------------------|--------|
| 一般 run path | Skip checkpoint；`delivery_plan.action=ok_no_human_gate` | 直接 delivery |
| Sandbox e2e | Skip checkpoint；`_can_proceed_sandbox_bundle_after_checkpoint_b` 判斷 | 進入 sandbox bundle |

**關鍵差異**：一般 run path 的 `ok` 直接進 delivery；sandbox e2e 的 `ok` 仍需通過 `_can_proceed_sandbox_bundle_after_checkpoint_b` 確認進 bundle。

### Risk-2: `warning` path 必經 CP-B

| `output_guard.status` | Checkpoint B 建立 | Sandbox Bundle 進行 |
|----------------------|-------------------|---------------------|
| `warning` | ✅ `awaiting_human` | 需 human approve |
| `blocked` | ✅ `awaiting_human` | 需 human approve |
| `ok` + `auto_approve=True` | ❌ skipped | 直接 bundle |
| `ok` + `auto_approve=False` | ❌ skipped | 直接 bundle |

**行為一致性**：與 W6-T6 integration layer 完全一致（見 `docs/checkpoint-b-integration-v1.md` §3）。

### Risk-3: 路徑解析混淆

| 檔案類型 | 路徑範例 | 解析方式 |
|----------|----------|----------|
| CP-B state | `outbox/additional_demo/checkpoint_B-2026-06-16T08-30-00Z.json` | 三層 fallback（repo-relative → outbox-relative → absolute）|
| Manifest | `outbox/sandbox_delivery/additional_demo/20260616T083012Z_xxx/manifest.json` | 直接拼接 |

**實作提醒**：
- CP-B 路徑由 `maybe_create_checkpoint_b` 回傳 `checkpoint_path`，使用三層 fallback 語意
- Manifest 路徑由 orchestrator 直接組合，不依賴 integration layer

---

## Phased Plan（P1/P2/P3）

### P1 · Implementation（已完成 2026-06-16）
- [x] Orchestrator 改接 `maybe_create_checkpoint_b`
- [x] 新增 `_can_proceed_sandbox_bundle_after_checkpoint_b`
- [x] 更新 test assertions
- [x] Verification: 11/11 + 26/26 tests OK

### P2 · Documentation Update（2026-07-28 · 全開 · 完成）
- [x] 更新 `docs/tabular-controlled-end-to-end-delivery-sandbox-v1.md` §4：S12 使用 W6-T6 integration layer
- [x] 更新 `docs/checkpoint-b-integration-v1.md` §9–§10：sandbox consumer usage
- [ ] 更新 `docs/agent-run-standard-case-orchestrator-v1.md` §2（可選 gap · 非阻擋）

### P3 · State Consolidation（本輪完成）
- [x] 本 state 檔 FRAME 完整定義
- [x] 本 state 檔 Risk Analysis 三項風險
- [x] 本 state 檔 AC-1～AC-6 驗收條件
- [x] 本 state 檔 P1/P2/P3 收口計畫

---

## O_NOTES

| 日期 | 角色 | 內容 |
|------|------|------|
| 2026-06-16 | Implementer | P1 接線完成 — sandbox e2e Phase-1 後改 W6-T6 integration layer 決定 CP-B 寫檔與 bundle gate；integration 建立 checkpoint 時 `final_status=sandbox_e2e_blocked_at_checkpoint_b` |
| 2026-06-16 | Scribe | P3 文件收口 — FRAME/AC/Risk/Phased Plan 完整記錄，為 P1/P2 正式 close 做準備 |
| 2026-06-16 | Implementer (B-F2) | P2 測試補齊完成 — 新增 4 個 sandbox e2e checkpoint B 測試，驗證 ok path / stopped path / integration layer 結構 / **warning blocked path**；33/33 tests OK |
| 2026-07-28 | Implementer（全開） | P2 docs 收口 + STATE=`done` · sandbox runbook／CP-B doc §10 · 再核 sandbox e2e 測試 OK · ≠ Phase%／Round-2 |

---

## Cross References

- W6-T6 integration layer: `docs/checkpoint-b-integration-v1.md`
- Orchestrator: `docs/agent-run-standard-case-orchestrator-v1.md`
- Sandbox runbook: `docs/tabular-controlled-end-to-end-delivery-sandbox-v1.md`
- W12-T1 sandbox delivery: `docs/tabular-controlled-end-to-end-delivery-sandbox-v1.md`
