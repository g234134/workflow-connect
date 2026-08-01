# WH-P9-WC-T7-runbook-payment-section-v1 — Ticket State

> handoff 摘要檔；P9 **WC-T7 runbook §4+ payment 正文** doc 票 · sandbox-only。  
> 目的：将 alignment matrix §4+ 与 happy-path 命令升格为 runbook 可复制正文；**仍非 prod gate**。

---

## META

| 欄位 | 值 |
|------|-----|
| **Phase** | P9 |
| **Lane** | WC-T7 runbook · Wave-C 文档 |
| **Parent wave** | Wave-P9 · payment sandbox follow-up |
| **Owner** | orchestrator |
| **Ticket type** | doc · runbook section |

---

## FRAME

### Goal（一行目的）

更新 `WC_T7_e2e_walkthrough_runbook.md` **§4+ payment 节正文**（transition · sandbox pay · lookup inspect · non-claims），与 `WC_M3_payment_closure_scope_v1` 及 alignment matrix §4.2 对齐。

### 核心 checklist

- [x] runbook 新增或扩展 **§4+ Payment（sandbox）**：可复制 CLI（transition / `GOV_PAYMENT_SANDBOX_ENABLED=1 pay` / lookup inspect）。
- [x] 交叉引用：`WC_M3_payment_closure_scope_v1.md` · `WC_M2_INT_HITL_alignment_matrix_v1.md` §4+ 行。
- [x] 明示 non-claims：sandbox only · **≠ prod 金流** · **≠ INT Tier-A** · **≠ required CI**。
- [x] 说明与 runner step 6 关系：manual 可按 runbook 逐步；fixture execute 由 runner 票内建（cross-ref `WH-P9-M2-runner-step6-payment-v1`）。
- [x] doc regression UT（`test_runbook_contains_sandbox_payment_section`）。
- [x] runbook 版本号 bump v0.3 → v0.4 · changelog 一句。

### Non-goals

- ❌ 不改 runner / tests / CI workflow 正文（runner 票 · CI 票另做）。
- ❌ 不把 runbook payment 节宣称为 prod gate 或 INT Tier-A 验收依据。
- ❌ 不启用真实 provider 或 prod ledger 路径说明（prod 另票 · 需批文）。

### AllowedPaths

- `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md`
- `tests/test_run_wc_m2_e2e_walkthrough.py`（doc regression · 裁决）
- `docs/wave_c/overview.md`（一句 cross-ref · Scribe）
- `04_Workflows/tickets/WH-P9-WC-T7-runbook-payment-section-v1_state.md`

### Acceptance Criteria

- **AC-1**：§4+ 含完整 sandbox payment 命令链 · 与 happy-path execute 证据一致。
- **AC-2**：non-claims 明示 · cross-ref WC-M3 + alignment matrix。
- **AC-3**：doc UT 绿或 Scribe 记录 UT gap · 无 secret 示例。

---

## STATE

- **overall_status**: `done_with_gaps`
- **current_owner**: reviewer
- **next_action**: Scribe Progress append · prod provider / INT / required CI 另票
- **last_updated**: 2026-06-24 · Wave-next-1 驗收落檔代理
- **wave**: Wave-P9 · WC-T7 runbook payment section
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-24 开 follow-up FRAME
  - **Implementer (B)**: done — 2026-06-24 §4+ 正文 + cross-ref + v0.4 bump
  - **Reviewer (C)**: done — 2026-06-24 · `accepted_with_gaps`
  - **Scribe (D)**: pending — Progress append
- **notes**:
  - runbook §4+ 正文已对齐 happy-path execute B_REPORT 命令链
  - runbook 已给出 **完整 DRAFT→PAID** sandbox 链（逐步 CLI + runner `--include-payment` 一键）
  - 遗留 gaps：**prod provider · INT Tier-A · required CI**（runner step 6 已内建 · 见 `WH-P9-M2-runner-step6-payment-v1`）

---

## B_REPORT (Implementer)

- **status**: done
- **written_date**: 2026-06-24
- **purpose**: WC-T7 runbook §4+ sandbox payment 可复制正文 · 对齐 WC-M3 scope 与 happy-path 演练命令。
- **deliverables**:
  1. `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md` v0.3→v0.4：新增 **§4+. Payment（sandbox DRAFT→PAID）** 含 4+.1–4+.4 子节。
  2. 命令链：runner `--include-payment` 一键 DRAFT→PAID（推荐）· 或逐步 CLI（transition → `GOV_PAYMENT_SANDBOX_ENABLED=1 pay` → lookup）。
  3. 文件头 cross-ref：`WC_M3_payment_closure_scope_v1.md` · alignment matrix §4+ · happy-path execute 票 · runner step6 票（`--include-payment` 已内建）。
  4. 附录表 A 补 §4+ 三行（transition · pay_sandbox · lookup audit）；§5 unittest 补 payment 模块。
  5. doc regression：`tests/test_run_wc_m2_e2e_walkthrough.py::test_runbook_contains_sandbox_payment_section`。
- **non_claims**: 本节仍 **≠ prod 金流** · **≠ INT Tier-A** · **≠ required CI** · fixture execute **默认仍止于 DRAFT**（加 `--include-payment` 可内建 step 6 至 PAID · sandbox-only）。
- **verification**: `python -m unittest tests.test_run_wc_m2_e2e_walkthrough.TestRunWcM2E2eWalkthrough.test_runbook_contains_sandbox_payment_section -v`

---

## C_REPORT (Reviewer)

- **verdict**: `accepted_with_gaps`
- **review_date**: 2026-06-24
- **core**: WC-T7 runbook §4+ 具备 sandbox DRAFT→PAID 可复制运维正文；命令与 happy-path execute 证据一致；non-claims 明示。
- **gaps**: **prod provider / prod ledger** · **INT Tier-A** · **required CI**（runner step 6-payment 已在 `WH-P9-M2-runner-step6-payment-v1` 实作；runbook §4+ 已同步 `--include-payment` 与重跑清理说明）。
- **evidence_checked**:
  - runbook §4+.2 命令链 ↔ `WH-P9-PROD-payment-happy-path-execute-v1` B_REPORT steps 2–4
  - WC-M3 §4.2 · alignment matrix §4+ 行 cross-ref 一致
  - doc UT 覆盖 §4+ 标题与关键 CLI 片段

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-06-24
- **depends_on**:
  - `WH-P9-PROD-payment-closure-bootstrap-v1`
  - `WH-P9-PROD-payment-happy-path-execute-v1`（命令 SSOT 证据）
  - `WH-P9-M2-INT-alignment-v1`（alignment matrix §4+）
  - `WC-T7` · `WC-T6-T7-v2`（runbook 基线）
- **unlocks**（预计升级 · 本票不修改他票）:
  - `WH-P9-PROD-payment-sandbox-adapter-v1` — runbook gap 关闭 · 可升 `accepted`
  - `WH-P9-PROD-payment-happy-path-execute-v1` — runbook gap 关闭
  - `WH-P9-PROD-payment-closure-bootstrap-v1` — doc 索引 completeness 提升
