# TICKET STATE · WB-T4 · agent-lines-ci-and-metrics-dashboard-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- Goal: 在 W10-T1/T2、W11-T3、W12-T2 之上新增 toolchain health dashboard CLI，一鍵輸出 JSON + Markdown summary；Phase 6 contract 附录 optional smoke matrix。
- Scope:
  - `scripts/run_toolchain_health_dashboard.py`（新增）
  - `docs/toolchain-health-dashboard-v1.md`（新增）
  - `tests/test_toolchain_health_dashboard_v1.py`（≥8 tests）
  - `docs/phase6-int-regression-gate-contract-v1.md` 附录 A only
  - 交叉引用 `docs/agent-lines-ci-suite-v1.md` · `docs/agent-lines-metrics-and-monitoring-v1.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md` · `04_Workflows/WORKFLOW_INDEX.md`
- NonScope:
  - 不改 `.github/workflows/eval-gate-ci.yml` / `core-agent-smoke.yml`
  - 不改 `run_agent_lines_ci_suite.py` 核心行為
  - 不引入 Prometheus / Grafana
  - 不把 dashboard 升格 PR required check
  - 即时告警推送
- AllowedPaths:
  - `scripts/run_toolchain_health_dashboard.py`
  - `docs/toolchain-health-dashboard-v1.md`
  - `tests/test_toolchain_health_dashboard_v1.py`
  - `docs/agent-lines-metrics-and-monitoring-v1.md`（§ 交叉引用）
  - `docs/agent-lines-ci-suite-v1.md`（§ 交叉引用）
  - `docs/phase6-int-regression-gate-contract-v1.md`（附录 only）
  - `tests/test_phase6_int_regression_gate_contract_v1.py`
  - `04_Workflows/tickets/WB-T4-agent-lines-ci-and-metrics-dashboard-v1_state.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md` · `04_Workflows/WORKFLOW_INDEX.md`
- BlockedPaths:
  - `.github/workflows/eval-gate-ci.yml` · `.github/workflows/core-agent-smoke.yml`
  - `scripts/run_agent_lines_ci_suite.py`（核心邏輯）
  - `scripts/analyze_agent_lines_metrics.py`（schema）
- Dependencies: W10-T1 · W10-T2 · W11-T3 · W12-T2 · WB-T1 · WA-T3 P3.5 · WA-T6 · `observability/wf_status_summary.py`
- AcceptanceCriteria:
  - AC-1: `--format json` → `toolchain_health_v1`
  - AC-2: sections agent_ci · metrics_summary · monthly_report_head · fixture_maturity_tiers · catalog_health
  - AC-3: `--dry-run` 只讀 outbox
  - AC-4: Markdown → `artifacts/toolchain/toolchain_health.latest.md`
  - AC-5: unittest ≥8 全綠
  - AC-6: P5 70%→85% · P6 84%→90% in Dashboard
  - AC-7: Phase 6 附录 optional smoke matrix
  - AC-8: optional class · blocks_mainline=false
  - AC-9: wf_status 缺檔不崩潰
  - AC-10: minimum example ok:true · sections_populated≥3

---

## STATE

- overall_status: done
- current_owner: orchestrator
- next_action: 無（票面已收口；Toolchain Wave B closure complete）
- last_updated: 2026-06-11 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files:
  - `scripts/run_toolchain_health_dashboard.py`（新增）
  - `docs/toolchain-health-dashboard-v1.md`（新增）
  - `tests/test_toolchain_health_dashboard_v1.py`（新增）
  - `docs/phase6-int-regression-gate-contract-v1.md`（附录 A）
  - `tests/test_phase6_int_regression_gate_contract_v1.py`（附录斷言）
  - `docs/agent-lines-ci-suite-v1.md` §7
  - `docs/agent-lines-metrics-and-monitoring-v1.md` §13
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `04_Workflows/tickets/WB-T4-agent-lines-ci-and-metrics-dashboard-v1_state.md`
- artifacts:
  - `artifacts/toolchain/toolchain_health.latest.json`（CLI 執行時寫入）
  - `artifacts/toolchain/toolchain_health.latest.md`
- verification:
  - `python -m unittest tests.test_toolchain_health_dashboard_v1 -v`
  - `python -m unittest tests.test_phase6_int_regression_gate_contract_v1 -v`
  - `python scripts/run_toolchain_health_dashboard.py --format json --dry-run`
- behavior_notes:
  - 預設 `--dry-run`；`maybe_run_agent_ci_suite` 僅在 `--no-dry-run` 時可選呼叫
  - 缺 outbox 區塊標 `degraded`；`aggregated_health_score` 為啟發式非 SLA
  - `catalog_health` 消費 WB-T1 雙 catalog JSON（tool count + stale revision）
- deferred_items:
  - P3.5 表新增 `OG-TOOLCHAIN-HEALTH` 行（非本票 AllowedPaths；可選 follow-up）

---

## C_REPORT

- conclusion: **accepted_with_gaps**
- blocking_issues: **无**
- checks_summary:
  - **FRAME**：未被 Implementer 改动；optional gate、NonScope（不改 CI / 非 PR required）遵守。
  - **B_REPORT 证据**：`tests.test_toolchain_health_dashboard_v1` + `tests.test_phase6_int_regression_gate_contract_v1` 含于汇总 **108/108 OK**；`python scripts/run_toolchain_health_dashboard.py --format json --dry-run` → `ok: true`, `schema_version=toolchain_health_v1`, `gate_class=optional`, `blocks_mainline=false`, `sections_populated=5`。
  - **AC 对照**：五核心 section（agent_ci · metrics_summary · monthly_report_head · fixture_maturity_tiers · catalog_health）+ wf_status 缺档不崩溃；Markdown 输出路径；P6 附录 A optional smoke matrix；`catalog_health` 消费 WB-T1 双 catalog JSON。
  - **Rule 3**：未改 `eval-gate-ci.yml` / `run_agent_lines_ci_suite.py` 核心逻辑。
- risk_level: **low**
- suggestions:
  - **缺但可接受**：FRAME AC-6 写 P6 **84%→90%**，Dashboard/WB-T7 口径 **84%→88%** → Phase% 以 Dashboard SSOT 为准（WB-T8 deferred 已记录）。
  - **缺但可接受**：P3.5 表增 `OG-TOOLCHAIN-HEALTH` 非本票 scope。
  - **缺但可接受**：B_REPORT verification 未逐条贴 unittest 计数（Reviewer 复跑已补证）。
  - 无 blocking；可交 Scribe。

---

## D_REPORT

- docs_updates:
  - P6 Phase% 以 Dashboard **84%→88%** 为准（非 FRAME AC-6 的 90%）；WC-PRE-01 未改 Phase% 数字
  - Dashboard Toolchain 分栏 P5/P6 状态列已对齐 `done · accepted_with_gaps`（WC-PRE-01）
- progress_entry: WB-T4 交付 `toolchain_health_v1` 离线健康摘要与 optional gate（dashboard unittest 含于 Wave B 汇总 108/108 OK）；未改 CI / 非 PR required。
- followup_suggestions:
  - **WC-PRE-06**：P3.5 表增 `OG-TOOLCHAIN-HEALTH`（需 governance 批文）
  - **WB-T4 deferred**：`audit_sections_found` / `audit_gaps_count` dashboard hook（WB-T5 交叉）
