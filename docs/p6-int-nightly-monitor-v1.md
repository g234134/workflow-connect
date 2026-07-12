# P6 INT Gate Nightly Monitor v1

> **Ticket**: `WF-P6-INT-NIGHTLY-MONITOR`  
> **Workflow**: `.github/workflows/p6-int-gate-nightly.yml`  
> **Governance ref**: `governance_decision_p6_int_gate_2026-06-27` · Human Gate Batch-2（2026-07-10）  
> **Status**: **WINDOW OPEN · GREEN CLOCK** — DAY0 RED（不計）· DAY1 GREEN `29159219832` · **DAY2 GREEN** `29186698130` · **2/7** · uplift 满窗后再裁（B2）

---

## Purpose

Collect evidence from Track B nightly runs (`artifacts/p6-int-gate/nightly.json` / GHA artifact `p6-int-gate-nightly-*`) to support governance Phase uplift **83% → 91%**.

---

## Preconditions (met)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| CI workflows landed | **Done** | `p6-int-gate-nightly.yml` · `p6-int-gate-pr-optional.yml` |
| Interim uplift 72→83 | **Done** | `workflow_line_status_2026-06-27.yaml` · `WAVE_PROGRESS_DASHBOARD.md` · 2026-06-27 governance |
| Local Tier-A baseline | **PASS** | `_wave7_regression_gate.py --tier A` · 112/112 · exit 0 |
| First GA nightly attempt | **DONE · RED**（不計綠日） | run_id=`29157182114` · `ModuleNotFoundError: core` · 已由資產 landing 修復 |
| First GA nightly **success** | **DONE · GREEN** | run_id=`29159219832` · Tier-A **112/112** · exit 0 · **綠日鐘起算日** |

---

## 7-day run log

| UTC date | GHA run_id | Workflow | Tier | JSON `ok` | Exit | Verdict | Artifact |
|----------|------------|----------|------|-----------|------|---------|----------|
| 2026-07-11 | 29157182114 | p6-int-gate-nightly | A | n/a | 1 | **RED** · missing `core`（**不計**綠日） | uploaded (gate failed early) |
| 2026-07-11 | 29159219832 | p6-int-gate-nightly | A | true | 0 | **GREEN · DAY1** · 112/112 | `p6-int-gate-nightly-*` |
| 2026-07-12 | 29186698130 | p6-int-gate-nightly | A | true | 0 | **GREEN · DAY2** · 112/112 · schedule | `p6-int-gate-nightly-29186698130` |
| — | — | — | A | — | — | **pending DAY3** | — |
| — | — | — | A | — | — | **pending** | — |
| — | — | — | A | — | — | **pending** | — |
| — | — | — | A | — | — | **pending** | — |

**Consecutive green days**: 2 / 7  
**Window declared**: 2026-07-11（裁決 OPEN）  
**Green-day clock**: **已启动** · 起算 UTC 日 = **2026-07-11**（首成功 `29159219832`）  
**Earliest final uplift eligible**: 再連續 **5** 個後續綠日（滿 7/7）  
**Uplift policy（2026-07-11 B2）**: 满 7/7 后尚書省 **到时再裁** 是否 83→91 · 本页绿表 ≠ 已 uplift  
**Follow-up**：維持 cron／必要時 `workflow_dispatch` 補日 · 勿宣稱 83→91

---

## Collection commands (post-merge)

```powershell
# Trigger first run manually
gh workflow run "P6 INT gate nightly" --field tier=A

# List recent runs
gh run list --workflow=p6-int-gate-nightly.yml --limit 10

# Download artifact from a run
gh run download <run_id> -n p6-int-gate-nightly-<run_id>
```

---

## Final uplift gate (83→91)

Per `governance_decision_p6_int_gate_2026-06-27`:

- [ ] 7 consecutive UTC days with nightly job **success**
- [ ] Each day artifact JSON: `"ok": true`, `"tier": "A"`, `"failed_tests": []`
- [ ] Monitor doc updated with run_id table
- [ ] Governance chat updates Dashboard + YAML `current_phase_pct: 91`（**仅**在 Batch-2 再签 uplift 后）
- [ ] Remove `nightly_7d_stability_monitor_pending` · `phase_pct_final_uplift_91_pending`
- [ ] Batch-2 re-signoff 留痕（Progress 末尾 · 批文/裁决 ID）

---

*WF-P6-INT-NIGHTLY-MONITOR · evidence doc · not final until 7/7 green + re-signoff*
