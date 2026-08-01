# W12-T1 · Tabular Controlled End-to-End Delivery Sandbox v1

> **角色**: Orchestrator + Implementer  
> **類型**: Implementation  
> **Wave**: Wave 12 — Sandbox E2E Controlled Delivery  
> **建立日期**: 2026-06-10  
> **狀態**: implementer done · Reviewer pending

---

## FRAME

### Goal
為 `additional_demo` sandbox fixture 新增受控真實交付線：allowlist 限定、`--sandbox-end-to-end` 真跑到 bundle，產物僅落 `outbox/sandbox_delivery/`；不觸發 production notify / contract。

### Scope
- [x] `docs/tabular-controlled-end-to-end-delivery-sandbox-v1.md`
- [x] `delivery/sandbox_delivery_bundle_v1.py`
- [x] `scripts/run_agent_standard_case_experiment.py` — `end_to_end_sandbox` profile · `--sandbox-end-to-end`
- [x] `scripts/run_agent_audit_quickview.py` — `sandbox_delivery` 區塊
- [x] `tests/test_sandbox_delivery_bundle_v1.py` · `tests/test_agent_standard_case_experiment.py` 擴充
- [x] `04_Workflows/WORKFLOW_INDEX.md` · `docs/WAVE_PROGRESS_DASHBOARD.md`

### NonScope
- 不改 demo_phase / sampleco run_path 與 bundle path
- 不改 production delivery / notify 腳本
- 不將 additional_demo 升格為 production fixture

### BlockedPaths（未修改）
- `scripts/build_case_delivery_bundle.py`
- `notebooks/csv_cleaning/case_delivery_bundle.py`
- `delivery/controlled_notify_experiment_v1.py`

---

## STATE

```yaml
overall_status: implementer_done
current_owner: reviewer
last_updated: 2026-06-10

status_by_role:
  orchestrator: done
  implementer: done
  reviewer: pending
  scribe: pending
```

---

## B_REPORT（Implementer）

### sandbox e2e run_path 摘要（additional_demo）

| 步驟 | 真跑 | HITL |
|------|------|------|
| S3 Decision | ✅ | — |
| S4 CP-A | ✅ | 預設 would_pause；`--auto-approve-intake` 跳過 |
| S5–S6 Plan/Preview | ✅ | — |
| S7 Gate | ✅ | — |
| S8 Cleaning | ✅ | — |
| S9 Outbox | ✅ | — |
| S11 Guard | ✅ live | — |
| S12 CP-B | ✅ sandbox gate | guard warning 需 `--auto-approve-delivery` |
| S10 Bundle | ✅（gate 通過後） | — |
| S10b Sandbox manifest | ✅ | — |
| S13–S15 | ❌ | 不跑 |

### changed_files
- `delivery/sandbox_delivery_bundle_v1.py`（新）
- `docs/tabular-controlled-end-to-end-delivery-sandbox-v1.md`（新）
- `scripts/run_agent_standard_case_experiment.py`
- `scripts/run_agent_audit_quickview.py`
- `tests/test_sandbox_delivery_bundle_v1.py`（新）
- `tests/test_agent_standard_case_experiment.py`
- `04_Workflows/WORKFLOW_INDEX.md`
- `docs/WAVE_PROGRESS_DASHBOARD.md`
- `04_Workflows/tickets/W12-T1-tabular-controlled-end-to-end-delivery-sandbox-v1_state.md`（本檔）

### verification
```bash
python -m unittest tests.test_sandbox_delivery_bundle_v1 tests.test_agent_standard_case_experiment -v
```

### anchor_unchanged
- demo_phase: `stop_at=bundle` · 無 `--sandbox-end-to-end` 行為不變
- sampleco: `stop_at=checkpoint_b` · 不變
- additional_demo 預設（無 flag）: `stop_at=checkpoint_b` · W11-T1 不變

---

## C_REPORT (Reviewer)

- conclusion: **accepted_with_gaps**
- blocking_issues: 無
- checks_summary:
  - **AC allowlist ✅**: `test_allowlist_only_additional_demo` · `test_sandbox_end_to_end_blocked_for_demo_phase` · `test_sandbox_end_to_end_blocked_for_sandbox_client` 通過
  - **AC sandbox bundle ✅**: `test_write_sandbox_bundle_creates_manifest` · `test_find_latest_sandbox_bundle` · gate/`--auto-approve-delivery` 路徑通過
  - **AC anchor 不變 ✅**: demo_phase/sampleco/additional_demo 預設 run path 測試仍綠（experiment suite）
  - **BlockedPaths ✅**: `controlled_notify_experiment_v1.py` · production bundle scripts 未改（B_REPORT BlockedPaths 對照）
  - **unittest ✅**: `python -m unittest tests.test_sandbox_delivery_bundle_v1 tests.test_agent_standard_case_experiment -v` → 全綠（含 W12 sandbox e2e CLI flag test）
  - **quickview 交叉 ✅**: W10-T3 audit quickview 已聚合 `sandbox_delivery` 區塊
- risk_level: medium
- suggestions:
  - deferred：S13–S15（delivery approval CLI / notify）不在 sandbox e2e 範圍 — 與 W8-T3 orchestrator `--resume-from-checkpoint` 整合另開票
  - deferred：sandbox 產物僅 `outbox/sandbox_delivery/` — production notify/contract 仍禁止；CI nightly sandbox e2e 排程留 W12-T2
  - risk note：`risk_level: medium` 因 sandbox 真跑到 bundle（雖 allowlist 限定）— Orchestrator 更新 Dashboard 時應標「sandbox only」
