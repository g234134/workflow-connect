# TICKET STATE · P5-HEALTH-BUNDLE-CLI-v1 · health+metrics+stub 一入口

> Wave A · 2026-07-15 · handoff 摘要；跨 chat 以本檔為準

---

## FRAME

- Goal: 交付 health + metrics scrape + grafana stub 的一入口 CLI，回傳結構化 `ok` dict。
- Scope:
  - MUST：`scripts/run_p5_health_bundle_cli_v1.py`
  - MUST：`tests/test_p5_health_bundle_cli_v1.py`
  - MUST：`docs/p5-health-bundle-cli-v1.md`
  - MAY：複用既有 toolchain health／metrics／stub 模組
- NonScope: ≠ 真 Grafana；≠ PG soak；≠ 改暗部 monitoring core；≠ Phase% apply
- AllowedPaths:
  - `scripts/run_p5_health_bundle_cli_v1.py`
  - `tests/test_p5_health_bundle_cli_v1.py`
  - `docs/p5-health-bundle-cli-v1.md`
  - `04_Workflows/tickets/P5-HEALTH-BUNDLE-CLI-v1_state.md`
  - `artifacts/p5_health/**`（可選 write）
- BlockedPaths:
  - 暗部破壞性維運、venv、.env、runtime checkpoints
  - Dashboard Phase% 數字格
  - 未授權改他人 core
- Dependencies: `P5-metrics-grafana-stub-v1`（已 accepted）· toolchain health dashboard
- relay_mode: same_chat
- phase_targets: P5
- baseline_pct: 72
- proposed_delta_pct: +3～+5
- apply_phase_pct: false
- AcceptanceCriteria:
  - AC-1: CLI `ok: true`（本地 demo_phase）
  - AC-2: `sections` 含 health／metrics／grafana_stub
  - AC-3: `python -m unittest tests.test_p5_health_bundle_cli_v1 -v` 全綠
  - AC-4: non_claims 明示 ≠ live Grafana／PG soak

---

## STATE

- overall_status: done
- current_owner: ops
- next_action: 無（本票封存）；PG soak 另票授權 · **勿**混關
- last_updated: 2026-07-15 · scribe（same_chat D）
- status_by_role:
  - orchestrator: done — Wave A 授權開票
  - implementer: done
  - reviewer: done — accepted
  - scribe: done — D_REPORT + Progress append

---

## B_REPORT

- changed_files:
  - `scripts/run_p5_health_bundle_cli_v1.py`（新建）
  - `tests/test_p5_health_bundle_cli_v1.py`（新建）
  - `docs/p5-health-bundle-cli-v1.md`（新建）
  - `04_Workflows/tickets/P5-HEALTH-BUNDLE-CLI-v1_state.md`（新建）
- artifacts:
  - 可選 `artifacts/p5_health/health_bundle.latest.json`（`--write`）
- verification:
  - `python scripts/run_p5_health_bundle_cli_v1.py --format text` → **ok: True** · health.ok · metrics.scrape_ok · stub.ok
  - `python -m unittest tests.test_p5_health_bundle_cli_v1 tests.test_p5_metrics_grafana_stub_v1 -v` → **OK**
  - non_claims 含 ≠ live Grafana／PG soak
- behavior_notes:
  - 編排既有 `build_toolchain_health`／`export_std_case_metrics`／`build_grafana_stub`；不新開 HTTP server
  - proposed P5 +3～+5 · **未** apply
- deferred_items:
  - `P5-PG-SOAK-AUTHORIZED-v1`（須授權）

---

## C_REPORT

- conclusion: accepted
- blocking_issues: 無
- checks_summary:
  - AC-1：CLI `ok: true`（demo_phase）· Reviewer 重跑綠
  - AC-2：`sections` 含 health／metrics／grafana_stub · 通過
  - AC-3：`unittest tests.test_p5_health_bundle_cli_v1`（+ stub 同捆）→ Ran 8 · OK
  - AC-4：non_claims ≠ live Grafana／PG soak · 通過
  - 邊界：AllowedPaths 內；未改暗部 monitoring core；`apply_phase_pct=false`
- risk_level: low
- suggestions:
  - deferred `P5-PG-SOAK-AUTHORIZED-v1` 須另授權；勿與本票混關
  - proposed P5 +3～+5 · 實際上調=否／待 W-PROG

---

## D_REPORT

- docs_updates: 無（`docs/p5-health-bundle-cli-v1.md` 已交付）
- progress_entry: 見 Progress 末尾「2026-07-15 · Wave A Scribe 四票封存」合併條
- followup_suggestions:
  - deferred `P5-PG-SOAK-AUTHORIZED-v1` 須另授權
  - proposed P5 +3～+5 · 實際上調=否／待 W-PROG
- Phase 影響:
  - 影響 Phase：P5
  - baseline：72
  - proposed_delta：+3～+5
  - 實際上調：否
  - non_claims：≠ live Grafana · ≠ PG soak · ≠ Phase% apply · ≠ 暗部 monitoring core
- Reviewer：accepted · risk=low · C blocking=無
