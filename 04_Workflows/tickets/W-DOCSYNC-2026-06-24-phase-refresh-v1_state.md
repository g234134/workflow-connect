# W-DOCSYNC-2026-06-24-phase-refresh-v1 — Ticket State

> handoff 摘要檔；**06-24 跨 Phase 文档同步索引票**（doc-only · 本票不直接改目标文件）。  
> 目的：把 Owner 06-24 checklist 落成可追踪 TODO，供后续分批派工。  
> 来源：06-24 变更同步 checklist 代理（只读稽核 · 2026-06-24）

---

## META

| 欄位 | 值 |
|------|-----|
| **Phase** | **Global**（跨 P7 / P8.5 / P9 · doc-sync 索引） |
| **Lane** | Phase% SSOT · master_status · wrapup / runbook 文案对齐 |
| **Owner** | **Orchestrator**（与 `docs/WAVE_PROGRESS_DASHBOARD.md` · `W-PROG-phase-progress-refresh-2026-06` 同一 maintainer 链） |
| **Ticket type** | index · doc-sync backlog |
| **Parent context** | 06-22～06-24 P7 staging execute · P8.5 ops-run blocked · P9 sandbox payment happy-path |

---

## FRAME

### Goal（一行目的）

建立 **06-24 待同步项目** 的可追踪索引，按 P7 / P8.5 / P9 / Global summary 分组，供 Orchestrator 后续开子票或 Scribe batch 逐一收敛；**本票不修改** Dashboard / Progress / master_status / 其他票正文。

### Non-goals

- ❌ 本票不直接修改 D_REPORT 所列任何目标文件
- ❌ 不跑 Phase% 重算脚本（留给子票 / `W-PROG` follow-up）
- ❌ 不改 Python / tests / CI workflow
- ❌ 不自行新增 `master_status` 里程碑（须 Scribe 子票 + Owner 裁定）

### AllowedPaths

- `04_Workflows/tickets/W-DOCSYNC-2026-06-24-phase-refresh-v1_state.md`（本票）

### BlockedPaths

- D_REPORT 所列全部目标路径（由子票承接）
- `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `.cursor/rules/**`
- 暗部 `core/**` · `.github/workflows/**`

### Acceptance Criteria（索引票关票口径）

- **AC-1**：D_REPORT 含完整待同步表（19 项）与四类 action 建议
- **AC-2**：Orchestrator 已按类拆分子票建议或 batch 顺序（可在 D_REPORT follow-up 或 STATE notes）
- **AC-3**：子票全部关票或明确 defer 后，本票可标 `done_with_gaps`

---

## STATE

- **overall_status**: `frame_ready`
- **current_owner**: orchestrator
- **next_action**: 按 D_REPORT 待同步表分批派工，更新 P7/P8.5/P9/Global summary 文案与票索引。
- **last_updated**: 2026-06-24 · doc-sync 索引票代理
- **wave**: Global · 06-24 phase refresh doc-sync index
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-24 建索引 FRAME + B/D_REPORT
  - **Implementer (B)**: n/a — 由子票承接
  - **Reviewer (C)**: pending — 子票 batch 完成后 spot-check
  - **Scribe (D)**: pending — `master_status` / Progress rollup 子票
- **notes**:
  - 待同步项 **19** 条 · 来源 06-24 checklist 只读稽核
  - 建议 batch 顺序见 chat 输出与 D_REPORT §follow-up

---

## B_REPORT (Orchestrator · index landing)

- **written_date**: 2026-06-24
- **purpose**: 把 **06-24 之后** 的实质进度变更（P7 local staging slot GO · P8.5 本机 smoke validated / remote GA pending · P9 sandbox payment happy-path）同步到 **Dashboard / master_status / WORKFLOW_INDEX / 各 Phase wrapup / runbook**，消除读者只看 SSOT 时的进度误判。

### 类别压缩摘要（3–5 类）

| 类别 | 待同步焦点（1–2 行） |
|------|---------------------|
| **Global summary** | Dashboard · WORKFLOW_INDEX §1.7 · Progress 06-23 rollup · W-PROG · `master_status` 仍停 06-23 或更早口径；P7 staging 40% · P8.5「Smoke A/B GA」· 缺 06-24 里程碑。 |
| **P7** | roadmap / policy / rollout bootstrap / wrapup / staging-integration 索引仍写 execute **pending** 或票 **`frame_ready`**，与 06-24 local slot S1–S4 **GO** 及设计票 **`validated`** 冲突。 |
| **P8.5** | WORKFLOW_INDEX §1.4 · W-PROG · H+2 closure C_REPORT · bridge runbook §0.3 仍用 GA pass 语汇，与 06-24 ops-run **blocked**（workflow 未 landing · 无 run_id/URL）不符。 |
| **P9** | sandbox happy-path 已在 Progress/票 STATE 落地，但 Dashboard 仍笼统 prod gap；WC-M3 scope 票索引 · alignment 表 · WC-T7 runbook · overview 仍 pre-execute 口径。 |

### 验证

- Doc-only 索引；无代码变更
- 对照来源：06-24 checklist 代理输出 + 各票 `overall_status` spot-check

---

## C_REPORT (Reviewer)

- **verdict**: `not_yet_reviewed`
- **review_date**: —
- **core**: 索引表与 06-24 票 STATE / Progress 战报一致；子票 batch 完成后复核 D_REPORT 清零项。
- **gaps**: 尚未派工；目标文件均未改。

---

## D_REPORT (Scribe · 待同步 backlog)

> **用法**：Orchestrator 按小节开子票；每关一张子票在本表对应行标 `[x]` 或移入 follow-up closed 列表。

### P7（5 项）

| # | 檔案 | 大致位置 | 不一致點（一句話） | 建議 action 類型 |
|---|------|----------|-------------------|------------------|
| 1 | `04_Workflows/tickets/WH-P7-PROD-roadmap-v1_state.md` | STATE `next_action` · B_REPORT §2 Wave-P7-5 · §6 Execution 索引 | execution 三票仍 **`frame_ready`**、Wave-P7-5 仍 **`implementer_done_pending_run`**；next_action 仍指向待执行 staging 链 | 改票状态索引 · 改文字口径 |
| 2 | `04_Workflows/tickets/WH-P7-NOTIF-PROD-policy-v1_state.md` | STATE `next_action` · 下游票表（~L234） | 仍写「staging execute 完成后更新」；execute 票仍标 **`frame_ready`**（实际 **`validated`**） | 改文字口径 · 补 run_id cross-ref |
| 3 | `04_Workflows/tickets/WH-P7-PROD-prod-rollout-governance-bootstrap-v1_state.md` | STATE `next_action` · FRAME checklist · C_REPORT gaps | 仍写「**待 staging execute 證據**」；checklist 首项未勾（local slot GO 已存在） | 改文字口径 · 引用 local slot 证据 |
| 4 | `04_Workflows/tickets/WH-P7-PROD-phase1-wrapup-v1_state.md` | FRAME Dependencies（~L43–44）· §3 缺口表 · §5 · STATE `next_action` | Dependencies 仍 **`implementer_done_pending_review`**；§3 写 HMAC receiver **not_implemented**；§5 staging 仍 **`implementer_done_pending_run`** | 改文字口径 · 改票状态索引 |
| 5 | `04_Workflows/tickets/WH-P7-PROD-staging-integration-v1_state.md` | B_REPORT 下游票索引（~L269–279） | 票 overall 已 **`validated`**，但索引表仍 **`implementer_done_pending_run` / `frame_ready`** | 改票状态索引 |

**建议 action 类型（P7）**：`改文字口径` · `改票状态索引` · `补 run_id cross-ref` · `引用 local slot 证据`

**为何值得开一轮**：roadmap / policy / wrapup 多处仍写 staging execute pending，Dashboard 子线仍 staging 40% · 0/3 closed，会低估 P7；wrapup 已建议 Phase% 72–75% 重算。

---

### P8.5（3 项）

| # | 檔案 | 大致位置 | 不一致點（一句話） | 建議 action 類型 |
|---|------|----------|-------------------|------------------|
| 1 | `04_Workflows/WORKFLOW_INDEX.md` | §1.4「最近一次通过纪录」L104 | 仍写 **GA Scenario 1 (pass)**，未标 **本机 smoke · remote GA pending push** | 改文字口径 |
| 2 | `04_Workflows/tickets/WH-P85-wave-H2-closure-scribe-v1_state.md` | C_REPORT `core` 行（~L74） | 写「**Scenario2 GA 已實證**」，与 ops-run 票 **`blocked`**（workflow 未 landing）矛盾 | 改文字口径 |
| 3 | `docs/phase8_5-bridge-smoke-runbook-v1.md` | §0.3 小节标题「Scenario 1 vs Scenario 2 (GA)」 | 标题语意易被读成「已在 GA 跑过」，未与 **remote pending CI-LAND push** 并列 | 改文字口径 · 标註 remote pending |

**建议 action 类型（P8.5）**：`改文字口径` · `标註 remote pending`

**为何值得开一轮**：WORKFLOW_INDEX §1.4 与 W-PROG 仍用「Smoke A/B GA / Scenario 1 (pass)」，与 06-24 advisory 修正（本机 smoke validated · 无 run_id/URL · workflow 未 landing）不符；H+2 closure 误写 Scenario2 已实证。

> **注**：Global summary 中 Dashboard · WORKFLOW_INDEX §1.7 · W-PROG 的 P8.5 GA 语汇另见 **Global summary** 小节；可与本类合并为 **P8.5 GA 语汇 sweep** 子票。

---

### P9（6 项）

| # | 檔案 | 大致位置 | 不一致點（一句話） | 建議 action 類型 |
|---|------|----------|-------------------|------------------|
| 1 | `docs/WAVE_PROGRESS_DASHBOARD.md` | P9 证据摘要 · 06-23 跃升说明 | 仍写「**prod 金流仍 gap / 未闭环**」，未区分 sandbox happy-path 已 **`done_with_gaps`** | 改文字口径 |
| 2 | `docs/wave_c/WC_M3_payment_closure_scope_v1.md` | §6 下游 impl/execute 票索引 | 三张 execution 票仍 **`frame_ready`**（实际已交付 / `done_with_gaps`） | 改票状态索引 |
| 3 | `04_Workflows/tickets/WH-P9-M2-INT-alignment-v1_state.md` | D_REPORT execution 票表（~L318–325） | 表内仍 **`frame_ready`**；虽有 06-24 superseded 注但主表未改 | 改票状态索引 |
| 4 | `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md` | §4 order 示例注（~L162） | 仍写「**仅到 DRAFT**、支付留待 WC-M3」；与 06-24 sandbox DRAFT→PAID 演练不符 | 改文字口径 · 补 cross-ref |
| 5 | `docs/wave_c/WC_M2_INT_HITL_alignment_matrix_v1.md` | §2 决策约束 checklist（~L46） | 仍写 fixture execute 默认仅到 **DRAFT**；未反映 happy-path execute 已可审计重跑 | 改文字口径 |
| 6 | `docs/wave_c/overview.md` | M2 达成 / 快速验证段 | 未索引 **WC-M3 sandbox payment happy-path**（06-24 Progress 已有战报） | 补 cross-ref |

**建议 action 类型（P9）**：`改文字口径` · `改票状态索引` · `补 cross-ref`

**为何值得开一轮**：sandbox happy-path 已在 Progress/票 STATE 落地，但 WC-M3 scope · alignment · WC-T7 runbook · overview 仍 pre-execute；须区分 **sandbox done_with_gaps** vs **prod blocked**。

> **已有 follow-up 票**：`WH-P9-WC-T7-runbook-payment-section-v1`（frame_ready）可覆盖 #4 部分 scope。

---

### Global summary（5 项）

| # | 檔案 | 大致位置 | 不一致點（一句話） | 建議 action 類型 |
|---|------|----------|-------------------|------------------|
| 1 | `docs/WAVE_PROGRESS_DASHBOARD.md` | Phase 完成度表 P7 列 · 子线 P7 staging · 06-23 刷新脚注 | 仍写 staging 三票 `design_accepted`、staging **40%**、「staging 未演練」；与 06-24 local slot execute **GO**（`20260623T165252Z`）不符 | 改文字口径 · Phase% 重算 |
| 2 | `04_Workflows/00_Agent_Work_Progress.md` | 2026-06-23 Phase% rollup 段（约 L3395–3426） | P7 staging 仍 **0/3 closed · 40%**；下方已有 06-24 战报但未 supersede 该汇总表 | 补 06-24 重算条 · 补 cross-ref |
| 3 | `04_Workflows/project_status/master_status.md` | 全文（最新条目仍停 2026-05） | 缺 **P7 staging 首轮 smoke**、**P9 sandbox payment happy-path** 里程碑 | 补 milestone 段 |
| 4 | `04_Workflows/WORKFLOW_INDEX.md` | §1.7 Phase% SSOT | 日期仍 **06-23**；P8.5 写「**Smoke A/B GA**」；P7 staging **40%** | 改文字口径 |
| 5 | `04_Workflows/tickets/W-PROG-phase-progress-refresh-2026-06_state.md` | 06-23 跟进表 P8.5 理由列 | 仍写「**Smoke A/B GA**」；无 06-24 follow-up 节 | 改文字口径 · 补 06-24 节 |

**建议 action 类型（Global summary）**：`改文字口径` · `Phase% 重算` · `补 milestone 段` · `补 cross-ref` · `补 06-24 节`

**为何值得开一轮**：四份全局摘要未吸收 06-24 三线交付；读者若只看 SSOT 会以为 staging 未演练、P8.5 已在 Actions GA、P9 仍无 payment 证据。建议 Owner 裁定后开 **06-24 Phase% refresh**（含 `master_status` append）。

---

### 建议子票 / batch 顺序（Orchestrator follow-up）

| 顺序 | 建议子票 / batch | 覆盖 D_REPORT 项 |
|------|------------------|------------------|
| 1 | **P8.5 GA 语汇 sweep** | P8.5 #1–3 + Global #4（§1.7）+ Global #5（W-PROG P8.5 行）+ 已部分修正的 Dashboard P8.5 段复核 |
| 2 | **P7 staging doc-sync + Phase% 重算** | P7 #1–5 + Global #1（Dashboard P7/staging）+ Global #2（Progress rollup） |
| 3 | **P9 sandbox 收编 doc-sync** | P9 #1–6（可并 `WH-P9-WC-T7-runbook-payment-section-v1`） |
| 4 | **Global Phase% refresh · master_status** | Global #3 · Global #1–2 收尾 · `W-PROG` 06-24 节 · 跑 `_progress_recalc_p7_p85_p9.py` |

### progress_entry（建议 · 子票完成后 append）

06-24 doc-sync 索引票 `W-DOCSYNC-2026-06-24-phase-refresh-v1` 建 FRAME；待同步 19 项分 P7/P8.5/P9/Global 四批派工；Dashboard / master_status / wrapup 口径对齐 06-24 staging GO · P8.5 remote pending · P9 sandbox happy-path。
