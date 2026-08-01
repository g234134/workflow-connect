# P6 INT Gate Nightly Monitor v1

> **Ticket**: `WF-P6-INT-NIGHTLY-MONITOR`  
> **Workflow**: `.github/workflows/p6-int-gate-nightly.yml`  
> **Governance ref**: `governance_decision_p6_int_gate_2026-06-27` · Human Gate Batch-2（2026-07-10）  
> **Status**：WINDOW OPEN · GREEN CLOCK · **≥7/7 已滿** · uplift **91 applied** · 超額綠日續收（tip#1）· **≠** 自動再 uplift · **≠** Round-2 GO

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

## 7-day run log（核心窗）

| UTC date | GHA run_id | Workflow | Tier | JSON `ok` | Exit | Verdict | Artifact |
|----------|------------|----------|------|-----------|------|---------|----------|
| 2026-07-11 | 29157182114 | p6-int-gate-nightly | A | n/a | 1 | **RED** · missing `core`（**不計**綠日） | uploaded (gate failed early) |
| 2026-07-11 | 29159219832 | p6-int-gate-nightly | A | true | 0 | **GREEN · DAY1** · 112/112 | `p6-int-gate-nightly-*` |
| 2026-07-12 | 29186698130 | p6-int-gate-nightly | A | true | 0 | **GREEN · DAY2** · schedule | `p6-int-gate-nightly-29186698130` |
| 2026-07-13 | 29242215006 | p6-int-gate-nightly | A | true | 0 | **GREEN · DAY3** · schedule | `p6-int-gate-nightly-29242215006` |
| 2026-07-14 | 29320080998 | p6-int-gate-nightly | A | true | 0 | **GREEN · DAY4** · schedule | `p6-int-gate-nightly-29320080998` |
| 2026-07-15 | 29403223522 | p6-int-gate-nightly | A | true | 0 | **GREEN · DAY5** · schedule | `p6-int-gate-nightly-29403223522` |
| 2026-07-16 | 29486053016 | p6-int-gate-nightly | A | true | 0 | **GREEN · DAY6** · schedule | `p6-int-gate-nightly-*` |
| 2026-07-17 | 29568619424 | p6-int-gate-nightly | A | true | 0 | **GREEN · DAY7** · **7/7 滿窗** | `p6-int-gate-nightly-*` |

**Consecutive green days（核心窗）**: **7 / 7**（DAY7 = `29568619424` · 2026-07-28 Wave5 sidecar `gh run list` 回填）  
**Window declared**: 2026-07-11（裁決 OPEN）  
**Green-day clock**: **已启动** · 起算 UTC 日 = **2026-07-11**（首成功 `29159219832`）  
**Earliest final uplift eligible**: **已達**（≥7/7）· **仍須**尚書省 B2 再签  
**Uplift policy（2026-07-11 B2）**: 满 7/7 后尚書省 **到时再裁** 是否 83→91 · 本页绿表 ≠ 已 uplift  
**Follow-up**：超額綠日續收（觀測穩定性）· **禁止**未再签上调 Phase% · 勿宣稱 83→91

---

## 超額綠日（7/7 後 · 續收 · 非 uplift 條件加碼）

> 來源：`gh run list --workflow=p6-int-gate-nightly.yml`（2026-07-28）· workflow **success** · schedule

| UTC date | GHA run_id | Verdict |
|----------|------------|---------|
| 2026-07-18 | 29637960949 | GREEN · post-7 |
| 2026-07-19 | 29680857459 | GREEN · post-7 |
| 2026-07-20 | 29732981838 | GREEN · post-7 |
| 2026-07-21 | 29818063221 | GREEN · post-7 |
| 2026-07-22 | 29907694459 | GREEN · post-7 |
| 2026-07-23 | 29994889258 | GREEN · post-7 |
| 2026-07-24 | 30081898808 | GREEN · post-7 |
| 2026-07-25 | 30151945487 | GREEN · post-7 |
| 2026-07-26 | 30195901807 | GREEN · post-7 |
| 2026-07-27 | 30258570894 | GREEN · post-7 |
| 2026-07-28 | 30346954725 | GREEN · post-7 · 最近一筆 |

### Append · 2026-07-28 · tip#1 盯梢（p6-log-utc-0728）

> 口令預設 `執行計畫`／`P6_WATCH` · **≠** 新 uplift · **≠** Phase% 假閉環

| 項 | 現況 |
|----|------|
| `gh run list`（limit 5） | 最新 UTC **2026-07-28** · `30346954725` · **success**（09:31:38Z） |
| UTC 07-28 schedule | **已出現** · success · 已 Progress 留痕 |
| Dashboard P6 | **91%**（已 authorize · 本盯梢 **不再**開 uplift） |
| QUEUE tip#1 | `P6-nightly-continue`（維持 · 未改 tip） |
| 可選旁線 | Tabular 回歸／新 case · 須口令 `TABULAR_SIDELINE` · **≠** 改 Phase%／war_status |
| 總覽 | `docs/governance/wave5_next_stage_post_defer_p6_v1.md` |

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

- [x] 7 consecutive UTC days with nightly job **success**
- [ ] Each day artifact JSON: `"ok": true`, `"tier": "A"`, `"failed_tests": []`（抽樣核驗可另開；本表以 GHA job success 為綠日鐘）
- [x] Monitor doc updated with run_id table（含 DAY6–7 + 超額）
- [x] Governance Dashboard P6 **91%**（`W-PROG-p6-uplift-83-to-91-2026-07-28` · authorize apply · 口令 `DEFER + P6_SIGN`）
- [x] Batch-2／裁決包再簽留痕（Progress `03:58` 收尾 · 裁決包 APPROVE）
- [ ] 超額綠日持續觀測（post-uplift · tip#1 · **≠** 再 uplift 除非新裁決包）

**Track B 裁決包（2026-07-28）**：`docs/governance/p6_uplift_decision_pack_83_to_91_v1.md`  
→ **已** APPROVE＋authorize · Dashboard **91%** · 後續＝超額綠日盯梢（見上表 Append）。

---

*WF-P6-INT-NIGHTLY-MONITOR · evidence doc · 7/7 met · uplift 91 applied · excess-green watch continues*
