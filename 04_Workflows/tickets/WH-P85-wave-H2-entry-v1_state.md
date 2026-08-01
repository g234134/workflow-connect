# WH-P85-wave-H2-entry-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> **P8.5 wave-H+2 入口票 · doc-only** — 承接 CI-LAND / SMOKE-B 收口，盤點現狀與下一批票；**不改 code / tests / workflows**。

---

## FRAME

### 背景（Wave-H / H+1 已交付）

P8.5 線在 Wave-D→G 已建立 **minimal orchestration bridge** smoke 主鏈（runbook · Master_Map runners · 14/14 核心 unittest · 7/7 HTTP API unittest），Wave-G 落地 **Smoke A** advisory CI job（`p85-bridge-smoke-a`），Wave-H 追加 **Smoke B** advisory CI job（`p85-bridge-smoke-b`）並更新 runbook §0.3；**WH-P85-CI-LAND-v1** 整理版控落地 checklist，**WH-P85-SMOKE-B-advisory-v1** 於 Wave-H+1 完成 **Scenario 1 本機 smoke validated**（**非遠端 GA pass** — 无 Scenario 1 run_id/URL）— 兩模組均未 skip · A **14/14** · B **7/7** · Reviewer **`accepted`** · 性質 **advisory / non-blocking / 非 required check** · Smoke C 仍 manual · **`bridge-smoke.yml` 已 landing `origin/main`**（2026-06-24 · push 票 `99bf1f590`）。

上游票索引（唯讀盤點）：`WD-P85-T1`（browser fixture smoke）· `WD-P85-T2`（runbook + WORKFLOW_INDEX §1.4 收口）· `WD-P85-T3`（測試計數 14 對齊）· `WD-P85-T4`（第一負例 fixture · optional 第二負例未做）· `WH-P85-SMOKE-B-advisory-v1` · `WH-P85-CI-LAND-v1`。

### 目標

- 盤點 P8.5 線 **已完成** 資產（CI workflow · runbook · smoke 首跑 · advisory 語意）。
- 列出 **已知缺口**（非 blocking）與 **建議下一批 3–5 張候選票**。
- 為 wave-H+2 後續 Implementer / Reviewer / Scribe 提供單一入口 handoff。

### 非目標

- **不**修改任何 code / tests / workflows / docs / 其它票 / Progress。
- **不**在本票執行 `git push`、Actions 首跑或 branch protection 設定。
- **不**將 advisory jobs 升格為 required check；**不**新增 Smoke C CI。

---

## STATE

- **overall_status**: `done_with_gaps`
- **current_owner**: none
- **next_action**: Scenario2 GA 已 recorded · wave-H+2 最小收口完成 · optional bridge hardening／Smoke C／T4 第二負例另票 · **勿**標 Phase closure
- **last_updated**: 2026-07-13 · Scribe（H1 證據解鎖裁決）
- **notes**: wave-H+1 已全关；wave-H+2：**ops-run done** · Scenario2 PASS `29157178993` · entry／closure **done_with_gaps** · bridge stub／Smoke C 仍 gap
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-23 開 WH-P85-wave-H2-entry-v1 · B_REPORT 三段盤點
  - **Implementer (B)**: n/a — entry doc-only；子票依優先序
  - **Reviewer (C)**: done — entry `accepted_with_gaps`（2026-06-23）
  - **Scribe (D)**: done — 2026-07-13 H2 rollup／INDEX／QUEUE 解鎖

### 解鎖裁決（2026-07-13）

| 條件 | 證據 | 結論 |
|------|------|------|
| Scenario2 GA run URL + id | `29157178993` · https://github.com/g234134/workflow-connect/actions/runs/29157178993 | ✅ |
| 兩 Scenario2 job success · S1 skipped | `gh run view` jobs | ✅ |
| EVD-GR-P85-S2 | `docs/p8_p89_evidence_index_v1.md` · `recorded` | ✅ |
| ops-run overall_status | `WH-P85-SMOKE-B-scenario2-ops-run-v1` → `done` | ✅ |

**裁決**：H1 證據夠 → **解鎖** wave-H2 entry／closure 收口。**仍 ≠** Phase closure／required CI／prod browser。

---

## B_REPORT (Orchestrator · 現狀盤點)

### 1. 已完成

| 類別 | 交付物 | 證據／錨點 |
|------|--------|------------|
| **CI workflow** | `.github/workflows/bridge-smoke.yml` — **P85 Bridge Smoke CI (advisory)** | 雙 job：`p85-bridge-smoke-a`（14/14）· `p85-bridge-smoke-b`（7/7）· `continue-on-error: true` · cron / `workflow_dispatch` / path-filtered PR |
| **Runbook** | `docs/phase8_5-bridge-smoke-runbook-v1.md` | §0.3 CI advisory 索引 · Smoke A/B/C 手動路徑 · Master_Map runners · 測試計數 checklist |
| **Smoke 首跑** | **Scenario 1 本機 smoke validated**（Wave-H+1 · **非遠端 GA pass**） | Progress 2026-06-22 條目 · `WH-P85-SMOKE-B-advisory-v1` C/D_REPORT · 本機 **14/14 + 7/7** · **无 run_id/URL** |
| **Advisory 語意** | non-blocking · 非 required check | workflow `continue-on-error` · skip → `::notice` + exit 0 · fail → `::warning` · 不阻 merge |
| **Bridge 測試底盤** | 核心 + HTTP API unittest | 本機 validated：**14/14** + **7/7** · `EXPECTED_TEST_COUNT=14` · runbook 權威計數 · **遠端 GA log 未收錄** |
| **索引／制度** | WORKFLOW_INDEX §1.4 · Master_Map `bridge_smoke_unittest` / `bridge_smoke_http` | WD-P85-T2/T3 收口 · Progress Wave-D→H+1 段 |

**一句話（P8.5 線現在已完成的核心東西）**：  
P8.5 已交付 **minimal orchestration bridge 雙路徑 smoke**（核心 **14/14** + HTTP API **7/7**）、**runbook §0.3** 與 **advisory CI 雙 job 版控落地**（`bridge-smoke.yml` **已 on `main`**）· **Scenario 1 本機 smoke validated**（**非遠端 GA pass**）· **Scenario 2 GA 待 ops-run human dispatch**，語意為 **non-blocking / 非 required check**，Smoke C 仍 manual。

### 2. 已知缺口（非 blocking）

| 缺口 | 說明 | 嚴重度 |
|------|------|--------|
| **Scenario 2 未實測** | **`WH-P85-SMOKE-B-scenario2-v1` validated**（wiring）· **GA 實跑** `29157178993` **PASS**（2026-07-11）· Progress／INDEX 2026-07-13 收口 | **已解除 H+2 blocking** · 仍 ≠ required CI |
| **Smoke C 仍 manual** | live curl / uvicorn 無 CI job；runbook §0.3 明示 **Not in CI** | 預期 · 非 regression |
| **Bridge 仍 in-memory stub** | 業務 bridge 非 production 持久化；outbox jsonl 側車為可接受 stub 副作用（WD-P85-T1 裁決） | 架構性 · 非本 wave blocking |
| **可選第二負例 fixture** | WD-P85-T4 最小交付已完成一則；第二負例 fixture **未做**（Wave-E optional gap） | 低 · 可選 |
| **Doc 仍 partial** | 歷史 Progress 仍保留「10 tests」敘述（FRAME 刻意不重寫）；索引／runbook Scenario cross-ref 由 **`WH-P85-CI-LAND-doc-sync-v1`** 收口 | 低 · **doc-sync 進行中** |
| **Telemetry 粒度** | CI 僅 log artifact + `::notice`/`::warning`；無結構化 metrics hook / dashboard 聚合 | 低 · 觀測增強 |
| **Smoke B deps 假設** | CI 需 checkout 含 `gov_core_system` + pip + `fastapi`；本地無 venv 時僅 skip 不 fail | 預期 · 已文件化 |

### 3. 建議下一批票（候選 · 3–5 張）

**wave-H+2 GA 完成條件（Orchestrator 裁決）**：

| 條件 | 說明 |
|------|------|
| **Scenario2 ops-run GA** | `WH-P85-SMOKE-B-scenario2-ops-run-v1`：`workflow_dispatch` + `scenario=scenario2` · 兩 Scenario 2 job log 含 design-skip + deps-gate notice · Progress append |
| **Bridge 能力水位** | 維持 **unittest + advisory CI**（14/14 + 7/7）；**不**宣稱 production browser / 持久化 bridge |
| **entry 收口** | 上述 GA 完成後 entry 可升 **`done_with_gaps`**；bridge hardening / Smoke C 矩陣為 optional follow-up |

| 優先 | Ticket id | 一句話 |
|------|-----------|--------|
| 1 | **WH-P85-SMOKE-B-scenario2-ops-run-v1** | **`done`**：GA **`scenario=scenario2`** · run_id=`29157178993` · PASS |
| 2 | ~~**WH-P85-SMOKE-B-scenario2-v1**~~ | **done** · validated |
| 3 | ~~**WH-P85-CI-LAND-doc-sync-v1**~~ | **done** · validated |
| 3 | **WH-P85-bridge-ci-hardening-v1** | CI 強化：artifact 保留策略、job summary、path filter 審查、可選 scheduled 失敗 notify（仍 advisory） |
| 4 | **WH-P85-SMOKE-C-manual-matrix-v1** | doc-only：Smoke C live curl 手動矩陣 + 預期 JSON 鍵表，不新增 CI job |
| 5 | **WH-P85-T4-second-negative-fixture-v1** | optional：補 WD-P85-T4 第二負例 browser plan fixture + unittest（不改 bridge 核心語意） |

> **Orchestrator 裁決提示**：P8.5 主線 **可封箱**（Progress Wave-H+1 後續建議）；wave-H+2 若繼續推進，建議 **優先 1→2**（Scenario 2 實證 + doc sync），**3–5 依尚書省優先序選開**。

### GA 完成條件（wave-H+2 scope）

| 子票 | 角色 | GA / 收口條件 |
|------|------|---------------|
| `WH-P85-SMOKE-B-scenario2-ops-run-v1` | **blocking for H+2 close** → **已滿足** | 人工 Actions `scenario=scenario2` · Progress append · STATE → `done` · run=`29157178993` |
| `WH-P85-SMOKE-B-scenario2-v1` | design | **validated** · wiring only |
| bridge hardening / Smoke C | optional | 不阻 H+2 最小收口 |

---

## C_REPORT (Reviewer)

- **review_date**: 2026-06-23
- **verdict**: **`accepted_with_gaps`**
- **conclusion**: 盤點與 wave-H+1 交付一致；Scenario 2 設計 **validated** · ops-run 待 GA 不夸大為 done；**bridge in-memory stub** 限制已索引。
- **core**: wave-H+2 入口盤點 SSOT；ops-run GA 為 H+2 最小 blocking；bridge non-stub 票已建檔待 impl。
- **gaps**: ops-run GA · Smoke C manual · bridge stub · 可選 T4 第二負例仍 open。

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-07-13
- **closure**: wave-H+2 entry → **`done_with_gaps`**（Scenario2 GA recorded · bridge stub／Smoke C 仍 gap）
- **next**: optional `WH-P85-bridge-ci-hardening-v1` · `WH-P85-SMOKE-C-manual-matrix-v1` · `WH-P85-T4-second-negative-fixture-v1` · **≠** Phase closure

**Execution 入口票（收口後）**

| 票 id | 狀態 | 優先 |
|-------|------|------|
| `WH-P85-SMOKE-B-scenario2-ops-run-v1` | **`done`** | GA PASS `29157178993` |
| `WH-P85-bridge-run-record-jsonl-v1` | `frame_ready` | optional |
| `WH-P85-bridge-fixture-dom-port-v1` | `frame_ready` | optional |
| `WH-P85-wave-H2-closure-scribe-v1` | **`done_with_gaps`** | 2026-07-13 解鎖收口 |
