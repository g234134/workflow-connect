# Wave 4 · P8.5 / P9 Evidence SSOT（v1）

> **Ticket**: `W4-P85-P9-EVIDENCE-SSOT-v1` · Wave 4 · **doc-only** · 2026-07-13  
> **位階**：證據索引 SSOT · **子票 B_REPORT ＞** 本檔摘要 ＞ W-ORCH 編排快照  
> **Phase%**：本檔 **不**授權改 Dashboard 數字格（見 `docs/phase-progress-impact-protocol-v1.md`）

---

## non_claims（置頂）

| 本檔 **不是** | 說明 |
|---------------|------|
| ≠ Phase closure | P8.5／P9 任一 Phase **未**結案 |
| ≠ required CI／merge gate | 兩線 workflow 均 **advisory** · `continue-on-error` |
| ≠ prod browser | bridge 仍 in-memory stub |
| ≠ prod 金流／INT Tier-A | P9 sandbox-only · provider／ledger 仍 gap |
| ≠ Round-2 GO | 與 P7 五頂無關 |

**用語**：寫 **GA-remote recorded**／**CI-advisory recorded**；**禁止**「已 GA 等於 prod-ready」類越級句。

---

## evidence_status

| 欄 | 值（2026-07-13） |
|----|------------------|
| **evidence_status** | **`complete`**（兩線皆有真實 run URL） |
| **更新方** | Scribe／本票（human AC 已於 07-11／07-12 滿足） |
| **權威值來源** | 子票 B_REPORT · 非本表臆造 |

---

## 兩線對照表

| 項 | **P8.5 Scenario2** | **P9 payment sandbox** |
|----|--------------------|------------------------|
| **Workflow 顯示名** | P85 Bridge Smoke CI (advisory) | P9 Payment Sandbox Smoke (advisory) |
| **yml** | `.github/workflows/bridge-smoke.yml` | `.github/workflows/p9-payment-sandbox-smoke.yml` |
| **ci_class** | advisory · non-blocking | advisory · sandbox-only · non-blocking |
| **Human 入口** | Actions → Run workflow → **scenario=`scenario2`**（**勿** `default`） | Actions → Run workflow（`workflow_dispatch`） |
| **CLI（可選）** | `gh workflow run bridge-smoke.yml --ref main -f scenario=scenario2` | `gh workflow run p9-payment-sandbox-smoke.yml --ref main` |
| **子票** | `WH-P85-SMOKE-B-scenario2-ops-run-v1` | `WH-P9-CI-payment-sandbox-smoke-v1` |
| **Evidence Schema** | ops-run STATE `## Evidence Schema`（`W4-P85-S2-GA-RUNBOOK-v1`） | 子票 B_REPORT `ga_run`／`ci_run` 欄（`W4-P9-CI-FIRST-RUN-SPEC` 敘事） |
| **Runbook／spec** | `docs/phase8_5-bridge-smoke-runbook-v1.md` §0.3 | 子票 FRAME + INDEX §1.x／overview 一句 |
| **recorded run_id** | `29157178993` | `29159159265` |
| **recorded run_url** | `https://github.com/g234134/workflow-connect/actions/runs/29157178993` | `https://github.com/g234134/workflow-connect/actions/runs/29159159265` |
| **結果摘要** | Scenario2 A/B success · S1 skipped · exit 0 | sandbox happy-path PASS · fixtures+unit |
| **子票 status** | `done` | `done_with_gaps` |
| **closure** | wave-H+2 `done_with_gaps`（bridge stub gaps） | INDEX／overview 已補 · ≠ prod |
| **Human AC** | ✅ 07-11 | ✅ 07-12 二次 PASS |

---

## 禁止宣稱 ↔ 可說

| 可說 | 不可說 |
|------|--------|
| Scenario2 GA-remote **recorded** · advisory | Scenario2 = prod browser／required CI／Phase closure |
| P9 sandbox CI-advisory **recorded** · local 21/21 | P9 = prod 金流／INT／merge gate |
| Smoke A 權威計數 **20/20**（runbook） | 歷史 Progress 14/14 被「改寫」為失敗 |
| W-PROG 07-13：P8.5=18% · P9=22% | 本 SSOT 存在 = 再次 uplift Phase% |

對照 Reviewer：`04_Workflows/review_checklists/wave-next-code-inspector-v1.md` · alignment `WH-REV-2026-06-P7-P8_5-P9-alignment-checklist-v1`。

---

## Cross-ref

| 檔 | 角色 |
|----|------|
| 本檔 | Wave 4 兩線證據索引 SSOT |
| `W4-P85-S2-GA-RUNBOOK-v1_state.md` | P85 checklist／Evidence Schema |
| `W4-P9-CI-FIRST-RUN-SPEC-v1`（wave-plan） | P9 首跑 spec（已關） |
| `W-ORCH-wave-next-control-plane-v1_state.md` | 編排入口（快照可舊；**以子票為準**） |
| `docs/WAVE_PROGRESS_DASHBOARD.md` | Phase% **唯一數字** SSOT（07-13） |
| `docs/phase-progress-impact-protocol-v1.md` | 提案 Δ vs 寫入 % |

---

*wave4-p85-p9-evidence-ssot-v1 · complete · ≠ Phase% write*
