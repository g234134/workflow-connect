# P1 治理殘項核銷清單 v1

> **Ticket**: `P1-GOV-RESIDUAL-CHECKOFF-v1`  
> **Date**: 2026-07-15 · Wave A  
> **Phase%**: proposed Δ only · `apply_phase_pct=false`（≠ 本票寫 Dashboard）  
> **Evidence runner**: `python 04_Workflows/_ops_cycle.py checklist --mode full --pretty`

---

## Purpose

核銷 P1（治理層 · Gauge **90%**）→ ~100% 前的殘項：每項標 **done**／**explicit defer**，並附可重跑證據。  
**non_claims**：≠ Phase closure · ≠ 自動 uplift · ≠ DarkOps 解禁 · ≠ K-2 prod rollout。

---

## Residual checkoff table

| ID | 殘項 | Verdict | Evidence / note |
|----|------|---------|-----------------|
| R1 | Phase 1 定稿令（W0–W5 正式權威） | **done** | `04_Workflows/project_status/HQ_PHASE1_FINALIZATION_ORDER.md` · 2026-05-19 Done |
| R2 | 接戰自檢一鍵綠（archive + Wave1 readiness） | **done** | 2026-07-15：`_ops_cycle.py checklist --mode full` → `ok: true` · `archive_ok=True` · `wave1_ok=True`（smoke_keys／routing／eval_gate／darkops_blocked_expected 均 pass） |
| R3 | Onboarding／接戰入口可跟 | **done** | `AGENTS.md` Tier1 `_boot_context.py` · `docs/GOVERNANCE_ONBOARDING_v1.md` 指向同一 checklist |
| R4 | WORKFLOW_INDEX ↔ runbooks 假陰性 | **done** | 2026-07-15：票 `P1-INDEX-R4-FALSE-NEG-DOC-v1` · SSOT `docs/p1-index-r4-false-neg-doc-v1.md` · INDEX §2／§2.1 去掉「待 RAG v0.1」假陰性並指向 §1.2 + GraphRAG thin；unittest `tests.test_p1_index_r4_false_neg_doc_v1` |
| R5 | K-2／遠端 rollout 納入 P1 100% | **explicit defer** | 近-100 計畫：K-2 **不**納入本衝刺；見 `docs/k2_deployment_governance.md` |
| R6 | Cursor rules／Phase2 規則升格 | **explicit defer** | 定稿令 §五：`HQ-P2-RULES-FINALIZE` 另軸；≠ 本票 |

---

## Ops checklist evidence (2026-07-15)

```text
python 04_Workflows/_ops_cycle.py checklist --mode full --pretty
# → ok: true
# → archive_checklist.ok: true
# → wave1_readiness.ok: true
# → darkops_route_gate: assignable=False blocked=True (expected)
# → smoke_keys: OpenAI/Groq/Telegram [OK]（無金鑰原文）
```

---

## Phase% proposal (not applied)

| Field | Value |
|-------|-------|
| phase_targets | P1 |
| baseline_pct | 90 |
| proposed_delta_pct | +3 ～ +5 |
| evidence_gate | R1–R3 done + checklist full green |
| apply_phase_pct | **false** |

上調僅能由後續 **W-PROG** 票 + `_phase_pct_apply.py apply --authorize` 執行。

---

## Suggested next

1. ~~若要清 R4 INDEX 敘事 → 開薄 doc 票~~ → **已交** `P1-INDEX-R4-FALSE-NEG-DOC-v1`（2026-07-15）  
2. W-PROG：彙總 Wave A + R4 證據後再裁 P1 Δ  
3. **勿**把 R5／R6 標 done

---

*P1-GOV-RESIDUAL-CHECKOFF-v1 · checkoff doc · Wave A*
