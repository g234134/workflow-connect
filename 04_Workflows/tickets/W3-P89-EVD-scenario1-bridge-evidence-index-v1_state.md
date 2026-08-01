# W3-P89-EVD-scenario1-bridge-evidence-index-v1 — Ticket State

> handoff 摘要檔；Wave 3 · P8/P8.9 Evidence Index · **doc-only**  
> **Goal**：P8 / P8.9 / Wave-next 统一 **L-local / CI-advisory / GA-remote** 三层证据语言 · 消除各票重复定义

---

## FRAME

### Goal（一行）

将散落在各票 / Progress / Dashboard 的 P8/P8.9/P8.5 bridge 证据整理为 **三层 Evidence Index SSOT**，使下游 runbook / GA spec **引用本 Index**，不再自创 tier 名称。

### Scope

- 新建 **`docs/p8_p89_evidence_index_v1.md`**（§1 三层定义 · §2 分层表 · §5 Phase% 门坎 · §2.3 GA-remote 记录模板）
- 收录 Scenario1 本机 **14/14 · 7/7**（**L-local**）· `bridge-smoke.yml` **CI-advisory landing** · Scenario2 **GA-remote pending/blocked**
- cross-ref：`WH-P85-CI-LAND-v1` · `WH-P85-SMOKE-B-advisory-v1` · `WH-P85-SMOKE-B-scenario2-ops-run-v1` · MP-SMOKE · P8.9-REGRESSION · Dashboard §Wave-next · `wave-next-code-inspector-v1` §3.2–3.3

### Non-Goals

- **不** dispatch GitHub Actions · **不**产生 run URL / run_id · **不**宣稱 Scenario1/2 **GA pass**
- **不**修改 `.github/workflows/**` · 现有 runbook · WORKFLOW_INDEX · Dashboard **Phase% 数字**
- **不**重写 `W-MASTER-wave-plan_state.md` / Phase Summary / `master_status`
- **不**将 advisory CI 升格 required check · **不**宣稱 prod-ready / INT Tier-A
- 本輪 **仅提供** 如何记录 GA 证据的语言（§2.3 模板）· **不**变更 Dashboard Phase% · 仅定义未来上调 Phase% 时应看的证据标准（Index §5）

### AllowedPaths

- `docs/p8_p89_evidence_index_v1.md`（必建）
- `04_Workflows/tickets/W3-P89-EVD-scenario1-bridge-evidence-index-v1_state.md`（本檔）

### BlockedPaths

- `.github/workflows/**`
- `docs/phase8_5-bridge-smoke-runbook-v1.md`（Wave 4 精修域）
- `docs/WAVE_PROGRESS_DASHBOARD.md`（Phase% · SSOT 票 `W3-P89-SSOT-*` 域）
- `04_Workflows/WORKFLOW_INDEX.md`（`W3-P8-ADV-*` 域）
- 任何 `*.py` · 暗部 `core/**`

### Acceptance Criteria

- [ ] **AC-1（Index 存在）**：`docs/p8_p89_evidence_index_v1.md` 存在 · 含 **≥3** tier（**L-local** · **CI-advisory** · **GA-remote**）· 每层 **≥1** 具名例子（命令 / workflow / job 名）
- [ ] **AC-2（Reviewer 认可）**：Reviewer D_REPORT verdict **`accepted`** 或 **`accepted_with_gaps`** · 明示「Evidence Index 已被 Reviewer 认可」· 对照 inspector §3.3 无 over-claim
- [ ] **AC-3（下游引用约束）**：FRAME / Index §6 写明 — **Wave 4 runbook / GA spec**（含 `W4-P85-S2-GA-RUNBOOK-v1` · `W4-P9-CI-*` · `W4-P85-P9-EVIDENCE-SSOT-v1`）**必须 cross-ref 本 Index** · **不得自创 tier 名称**（仅允许 `L-local` · `CI-advisory` · `GA-remote`）
- [ ] **AC-4（Scenario1 本机）**：Index 列明 **L-local** 命令 · `test_minimal_orchestration_bridge` **14/14** · `test_app_api_orchestration_bridge` **7/7** · 引用 runbook / WH-P85 票
- [ ] **AC-5（CI-advisory 标签）**：`bridge-smoke.yml` 条目标 **non prod gate / non required check / continue-on-error** · **landing ≠ GA pass**
- [ ] **AC-6（GA-remote 诚实）**：Tier **GA-remote** 写 **pending human / blocked** · 指向 `WH-P85-SMOKE-B-scenario2-ops-run-v1` · **无 URL 占位符造假** · 含 §2.3 记录模板
- [ ] **AC-7（Phase% 纪律）**：Non-goals + Index §5 明示 — 本 Wave **不上调 Phase%** · Index 仅定义未来上调门坎

### Dependencies

- 上游：`WH-P85-CI-LAND-v1` · `WD-P85-T3` closure · MP-SMOKE · P8.9-REGRESSION · Dashboard §Wave-next（06-25）
- 下游：`W3-P89-SSOT-*` · `W3-P8-ADV-*` · `W3-P8-BRG-*` · Wave 4 `W4-P85-S2-GA-RUNBOOK-v1` · `W4-P85-P9-EVIDENCE-SSOT-v1`
- `blocks_if_missing`：无（本机 tier 自洽）

### Observability

- `verify_commands`：`grep -E "L-local|CI-advisory|GA-remote" docs/p8_p89_evidence_index_v1.md` · 人工对照 WH-REV「不可说」表
- `evidence_artifacts`：Index 正文 · 本票 B_REPORT
- `trace_fields`：`evidence_tier` · `evidence_kind`（见 Index §1）
- `success_signals`：三层表与 W-ORCH Wave 3 · Progress 2026-06-22–24 bridge 叙述一致
- `failure_signals`：Index 写 GA pass 而无 URL · 或 advisory 未标 non-required

---

## STATE

- **overall_status**: done
- **lifecycle_phase**: O
- **current_owner**: orchestrator
- **next_action**: 无（本票收口完成）· Wave 4 GA 后仅 **追加** Index §2.3 GA-remote 行
- **last_updated**: 2026-07-10 · Orchestrator（同輪 C→D→O 關票）
- **wave_id**: W3
- **phase_targets**: [P8, P8.9]
- **non_claims**:
  - advisory CI ≠ prod gate / required check / merge gate
  - CI landing ≠ GA pass
  - 不宣稱 Phase% 上调
  - 不宣稱任何 GA-remote 已跑
- **status_by_role**:
  - **Orchestrator (A)**: done — W-MASTER Wave 3 规划 · 2026-07-10 關票
  - **Implementer (B)**: done — 2026-06-26 Index + 本票 STATE
  - **Reviewer (C)**: done — 2026-07-10 · `accepted` · AC-1–AC-7 PASS
  - **Scribe (D)**: done — 2026-07-10 Progress / QUEUE 收口（GA-remote 物證仍待 human · 不在本 Wave）

---

## B_REPORT (Implementer)

- **changed_files**:
  - `docs/p8_p89_evidence_index_v1.md` — **新建** · 三层 SSOT · Scenario1 L-local · bridge CI-advisory · GA-remote pending/blocked · Phase% 门坎 §5 · GA 记录模板 §2.3
  - `04_Workflows/tickets/W3-P89-EVD-scenario1-bridge-evidence-index-v1_state.md` — 本檔 FRAME/STATE/B_REPORT

- **not_changed**: `.github/workflows/**` · runbook · WORKFLOW_INDEX · Dashboard Phase% · W-MASTER 正文

- **verification**:
  - Index 含 **3** tier · 每层具名例子 **≥1**
  - Scenario1：**EVD-LL-P85-A/B**（14/14 · 7/7）· **EVD-CA-P85-BRG**（landing · non-required）
  - Scenario2 GA：**EVD-GR-P85-S2** → `WH-P85-SMOKE-B-scenario2-ops-run-v1` **`blocked`** · 无 run URL
  - grep 抽樣：`L-local` · `CI-advisory` · `GA-remote` 均出现于 Index 正文

- **AC checklist（Implementer 自檢）**:
  - **AC-1 ✅**: Index 存在 · 三层 + 例子
  - **AC-2 ⏳**: 待 Reviewer
  - **AC-3 ✅**: Index §6 + 本票 AC-3 写明 Wave 4 必须引用
  - **AC-4 ✅**: §2.1 EVD-LL-P85-A/B
  - **AC-5 ✅**: §2.2 EVD-CA-P85-BRG · §3 误解表
  - **AC-6 ✅**: §2.3 · pending/blocked · 模板 · 无假 URL
  - **AC-7 ✅**: Non-goals + §5

- **gaps / honesty**:
  - **无 GA-remote 物证** — 符合 Non-goals
  - **WORKFLOW_INDEX bridge 条目尚未引用 Index** — defer `W3-P8-ADV-*` / `W3-P89-SSOT-*`
  - **OBS contract**（`W3-P89-OBS-*`）未建 — Index §4 已 cross-ref 占位

---

## C_REPORT (Reviewer)

- **conclusion**: accepted
- **verdict**: accepted
- **blocking_issues**: 無
- **risk_level**: low
- **checks_summary**: |
  **Evidence Index 已被 Reviewer 認可**（AC-2）。
  AC-1 PASS：`docs/p8_p89_evidence_index_v1.md` · 三 tier · 每層 ≥1 具名例子。
  AC-3 PASS：§6 + FRAME 寫明 Wave 4 必須 cross-ref · 不得自創 tier。
  AC-4 PASS：EVD-LL-P85-A/B · 14/14 · 7/7 · runbook/WH-P85 引用。
  AC-5 PASS：bridge-smoke · non-gate / continue-on-error · landing ≠ GA pass · non required（non-claims）。
  AC-6 PASS：GA-remote pending/blocked · 指向 ops-run · §2.3 模板 · 無假 URL。
  AC-7 PASS：Non-goals + §5 · 本 Wave 不上調 Phase%。
  inspector §3.2–3.3：無 over-claim（無 GA pass / required / prod-ready）。
- **gaps_noted**: WORKFLOW_INDEX bridge 條目引用 Index → 已 defer ADV/SSOT/BRG（AllowedPaths 不含 INDEX；誠實缺口非 blocking）
- **suggestions**: 無

---

## D_REPORT (Scribe)

- **docs_updates**:
  - 無新增正文（Index 已於 2026-06-26 落地）· 本輪僅 STATE C/D/O 收口
- **progress_entry**: |
  2026-07-10 · W3-P89-EVD done · Evidence Index Reviewer accepted · C=accepted · risk=low
- **followup_suggestions**:
  - Downstream：`W3-P89-OBS` → `W3-P89-SSOT`；Wave 4 runbook 必須引用本 Index tier
- **queue_note**: QUEUE 補列 EVD DONE（原僅在 priority/frame 出現）

---

## O_NOTES

| date | role | action |
|------|------|--------|
| 2026-06-26 | Implementer | Index + FRAME/STATE/B_REPORT |
| 2026-07-10 | orch+C+D | Reviewer accepted · Scribe · overall_status=done |
