# W1-P75-POLICY-DENY-MVP-v1 — Policy Deny Path Doc + Minimal Runtime Probe

> handoff 摘要檔 · Wave 1 · P7.5 upstream · MVP doc + trace fields

---

## FRAME

- Goal: 補 P7.5 policy deny 上游可審計鏈（YAML → layer merge → `phi_demo` 探針 → trace 欄位）；Reviewer 可不跑 staging 即判斷 deny fail-closed。
- Scope:
  - `docs/p75-policy-deny-path-mvp-v1.md`：deny `reason_code` 枚舉 · layer merge · golden/`phi_demo` 對照 · trace 欄位 · verify_commands
  - `routing/intake_gate_policy_bridge_v1.py`：`P75_POLICY_DENY_REASON_CODES` · `derive_p75_policy_trace()`
  - `routing/intake_gate_layer_v1.py`：gate result 附加 `p75_policy_decision` · `deny_reason`
  - `tests/test_intake_gate_policy_integration_v1.py`：4 deny golden snapshot · `phi_demo` trace 對齊
  - `tests/test_intake_gate_policy_bridge_v1.py`：`derive_p75_policy_trace` unit tests
  - `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` §7.6 cross-ref
- NonScope:
  - 不重做 P75-G3 loader/evaluator
  - 不做 G-1–G-5 resume-loop runtime（Wave 2）
  - 不宣稱 prod-ready / full gate / staging POST
  - 不改 Phase% · W-MASTER · Dashboard
- AllowedPaths:
  - `docs/p75-policy-deny-path-mvp-v1.md`
  - `routing/intake_gate_policy_bridge_v1.py`
  - `routing/intake_gate_layer_v1.py`
  - `tests/test_intake_gate_policy_integration_v1.py`
  - `tests/test_intake_gate_policy_bridge_v1.py`
  - `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md`
- BlockedPaths:
  - `ENGINEERING_CONTRACT.md` · `HARNESS_CONSTITUTION.md` · `AGENTS.md`
  - `.github/workflows/**` · `config/**` · `runtime/checkpoints/**` · `.env`
  - `04_Workflows/00_Agent_Work_Progress.md` · `project_status/master_status.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md` · `W-MASTER-wave-plan_state.md`
- Dependencies:
  - `P75-G3-intake-gate-policy-allowlist-denylist-v1`（implemented）
  - `MC-SMOKE-multi-case-smoke-runner-v1` · `tests/golden/intake_gate_policy/deny_*.json`
  - downstream: `W1-P75-TRACE-UPSTREAM-v1`
- AcceptanceCriteria:
  - AC-1：deny path doc 列 ≥4 deny golden fixture 與 `reason_code`
  - AC-2：doc 明示 `phi_demo` → gate `reject` → downstream smoke fail-closed
  - AC-3：trace doc 列 ≥3 `trace_fields`（含 `intake.gate_decision` 或等價）
  - AC-4：non-claims 含 MVP ≠ full gate ≠ prod deny SLA
  - AC-5：gate result 含 `p75_policy_decision` · `deny_reason`；unittest 覆蓋 deny golden + phi_demo

---

## STATE

- overall_status: done
- implementation_status: done
- lifecycle_phase: O
- current_owner: scribe
- next_action: 無（Reviewer `accepted` · Scribe 收口完成）
- last_updated: 2026-06-26 · scribe
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files:
  - `docs/p75-policy-deny-path-mvp-v1.md`（新建）
  - `routing/intake_gate_policy_bridge_v1.py`
  - `routing/intake_gate_layer_v1.py`
  - `tests/test_intake_gate_policy_integration_v1.py`
  - `tests/test_intake_gate_policy_bridge_v1.py`
  - `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md`
- artifacts:
  - `docs/p75-policy-deny-path-mvp-v1.md`
  - matrix §7.6 Policy deny upstream
- verification:
  - `python -m unittest tests.test_intake_gate_policy_bridge_v1 tests.test_intake_gate_policy_integration_v1 -v` → **11 tests OK**
  - `rg "reason_code|phi_demo|policy deny" docs/p75-policy-deny-path-mvp-v1.md` → matches doc sections
- behavior_notes:
  - **Spec（B）**：deny path doc 定義 4 PM-D3 `reason_code`、layer merge 規則、`phi_demo`/`deny_*.json` 對照表、6 trace 欄位、verify_commands、non-claims。
  - `derive_p75_policy_trace()` 純 mapping（`policy_deny` / `policy_review` / `policy_pass` + `deny_reason`）；無外部呼叫。
  - `evaluate_intake_gate()` 成功路徑附加 trace 欄位；happy path `demo_phase` 仍 `policy_pass` / `deny_reason=null`。
- deferred_items:
  - MC-SMOKE summary `gate_status` 欄位（留 W1-P75-TRACE-UPSTREAM-v1）
  - G-1–G-5 resume-loop runtime（Wave 2）

---

## C_REPORT

- conclusion: accepted
- reviewer_date: 2026-06-26
- verdict: accepted
- implementation_summary:
  - **Bridge**（`routing/intake_gate_policy_bridge_v1.py`）：`P75_POLICY_DENY_REASON_CODES` frozenset；`derive_p75_policy_trace(bridge)` → `{p75_policy_decision, deny_reason}`。
  - **Layer**（`routing/intake_gate_layer_v1.py`）：gate result dict 合併 trace 欄位。
  - **Tests**：4 deny golden snapshot；`phi_demo` intake 等價 deny trace；bridge trace unit tests。
  - **Doc/Matrix**：`docs/p75-policy-deny-path-mvp-v1.md`；matrix §7.6 PD-1–PD-3。
- public_interface:
  - `derive_p75_policy_trace(bridge)` — observability helper
  - Gate result keys: `p75_policy_decision` (`policy_deny`|`policy_review`|`policy_pass`), `deny_reason` (str|null)
- blocking_issues: 无
- checks_summary: AC-1–AC-5 全 PASS；Reviewer 獨立複跑 11 unittest OK
- risk_level: low
- suggestions: 无

### Reviewer 收口摘要（Wave Master · 2026-06-26）

- **policy deny MVP 已 landing**：doc SSOT + bridge 純 mapping + matrix §7.6 PD-1–PD-3 cross-ref 已就緒。
- **trace 欄位已實裝**：`p75_policy_decision` · `deny_reason` · `intake.gate_decision`（doc 列 6 欄 · gate layer 合併）。
- **邊界**：**非 prod-ready** · **非 full gate** · MC-SMOKE CLI 全跑 defer `W1-P75-TRACE-UPSTREAM-v1`（outbox 副作用 · 邏輯由 unittest + doc verify_command 覆蓋 · 非 blocking）。

---

## D_REPORT

- scribe_date: 2026-06-26
- verdict_echo: Reviewer `accepted` · Scribe 收口 · `overall_status: done`
- test_results:
  - `tests.test_intake_gate_policy_bridge_v1`：**5 tests OK**（含 `test_derive_p75_policy_trace_*`）
  - `tests.test_intake_gate_policy_integration_v1`：**6 tests OK**（含 4 golden deny + phi_demo trace）
  - **合計 11 tests OK**（2026-06-26 implementer pass · Reviewer 獨立複跑確認）
- known_boundaries:
  - MC-SMOKE `phi_demo` CLI 全跑未在本輪執行（耗時 · outbox 副作用）；邏輯由 unittest + doc verify_command 覆蓋。
  - `p75_policy_decision` 僅 policy 層語意；v2-only reject 可能為 `policy_deny` 但 `deny_reason` 來自 non-PM-D3 code（如 `unsupported_task_type`）。
- docs_updates:
  - `docs/p75-policy-deny-path-mvp-v1.md`（SSOT · 本輪無新增 doc 變更）
  - matrix §7.6
- non_claims_echo: **MVP** · **非 prod-ready** · **非 full gate** · MC-SMOKE CLI defer TRACE 票 · G-1–G-5 resume runtime 歸 Wave 2
- progress_entry: 見 `04_Workflows/00_Agent_Work_Progress.md` — **2026-06-26 · W1-P75-POLICY-DENY-MVP-v1 · Scribe 收口**
- followup_suggestions: `W1-P75-TRACE-UPSTREAM-v1` 消費 deny trace 欄位；Wave 2 G-1–G-5 resume runtime。
