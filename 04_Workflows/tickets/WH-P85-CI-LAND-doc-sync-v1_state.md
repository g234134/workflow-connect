# WH-P85-CI-LAND-doc-sync-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> **P8.5 CI-LAND doc-sync 票** — 對齊 `bridge-smoke.yml` / runbook §0.3 / P8.5 票檔文字與索引；**本輪僅 FRAME + STATE 占位，不改 code / tests / docs / workflows**。

---

## FRAME

### Background

**WH-P85-CI-LAND-v1** 已於 Wave-H+1 完成 advisory CI **設計 + 本機版控**；**Scenario 1 本機 smoke validated**（A **14/14** · B **7/7**）· **遠端 GA 未執行**（`bridge-smoke.yml` **未 landing 至 `origin/main`** · 無 run_id/URL）：

| 已落地（本機 / doc） | 錨點 |
|--------|------|
| **Workflow 設計** | `.github/workflows/bridge-smoke.yml` — `P85 Bridge Smoke CI (advisory)` · jobs `p85-bridge-smoke-a`（**14/14**）· `p85-bridge-smoke-b`（**7/7**）· **remote pending CI-LAND push** |
| **Runbook** | `docs/phase8_5-bridge-smoke-runbook-v1.md` §0.3 — 雙 job 表 · skip / advisory 語意 · Smoke C manual |
| **票檔** | `WH-P85-SMOKE-B-advisory-v1` · `WH-P85-CI-LAND-v1` — C/D 收口 · Reviewer **`accepted`**（設計 + 本機 smoke） |
| **Progress** | Wave-H+1 設計收口條目 — Scenario 1 **本機 smoke validated**（非遠端 GA pass） |

**殘留 doc 漂移（非 blocking · 低優先）**：

| 漂移類型 | 範例 | 權威來源 |
|----------|------|----------|
| **歷史測試計數** | 舊 Progress / 索引仍寫「**10 tests**」 | runbook § Smoke A · `EXPECTED_TEST_COUNT=14` · **14/14** |
| **Job / workflow 名稱** | 部分票索引或模板未列 `p85-bridge-smoke-b` · Actions UI 顯示名 | `bridge-smoke.yml` `name:` · job `name:` 欄 |
| **Scenario 語意** | Scenario 2 skip 模板已寫入 CI-LAND，但 wave-H+2 子票尚未交叉引用 | `WH-P85-CI-LAND-v1` B_REPORT §5 |
| **WORKFLOW_INDEX §1.4** | 可能仍引用 stale 計數或未列 HTTP Smoke B runner | `Master_Map.json` `bridge_smoke_http` · runbook |

上游索引：`WH-P85-wave-H2-entry-v1`（建議本票優先序 #2 · doc-sync gap）· `WH-P85-CI-LAND-v1`（首跑 checklist · Scenario 模板）· `docs/phase8_5-bridge-smoke-runbook-v1.md`（§0.3 權威）。

### Goal

對 **文字 / 索引 / 票檔交叉引用** 做一次 sweep，使下列三者 **數字 · 票號 · job 名稱 · advisory 語意** 一致：

| 對齊對象 | 權威欄位 |
|----------|----------|
| **`.github/workflows/bridge-smoke.yml`** | workflow `name:` · job id `p85-bridge-smoke-a` / `p85-bridge-smoke-b` · display name · **14/14** · **7/7** · `continue-on-error: true` |
| **`docs/phase8_5-bridge-smoke-runbook-v1.md` §0.3** | 雙 job 表 · skip reason 列 · Smoke C = manual · Actions UI 名 |
| **P8.5 票檔 + 索引** | `WH-P85-*` state 檔 · `WORKFLOW_INDEX.md` §1.4（若涉 bridge smoke）· Progress **模板**（非重寫歷史段） |

**代表性一句話**：以 **`bridge-smoke.yml` + runbook §0.3 為 SSOT**， sweep P8.5 票檔與 WORKFLOW_INDEX 中仍殘留的 **10→14** 計數、job id、Actions 顯示名與 Scenario 1/2 交叉引用，使 doc 讀者無需猜哪份是權威。

**預期 deliverables（實作票細化）**：

- doc-only diff 清單（逐檔 before/after 摘要）
- 不重寫 Progress 歷史 Wave-D/E 段落（FRAME 刻意保留考古語意；僅模板 / 索引 / 票檔更新）
- 可選：在 runbook 或 WORKFLOW_INDEX 加一句「歷史 Progress 10 tests 敘述已 supersede by 14/14」交叉引用

### Non-goals

- **不**修改 `bridge-smoke.yml` job steps / env / triggers（CI **行為** frozen）。
- **不**修改任何 Python、tests、`app_api.py`。
- **不**新增 / 刪除 CI job · 不升格 required check · 不新增 Smoke C workflow。
- **不**在本 skeleton 輪次修改任何 doc / Progress / 其它票（僅建立本票 FRAME）。
- **不**執行 `git push` 或 Actions 首跑。

### allowed_paths（實作票預留 · 本 skeleton 不動）

- `docs/phase8_5-bridge-smoke-runbook-v1.md`（§0.3 及必要 cross-ref）
- `04_Workflows/WORKFLOW_INDEX.md`（§1.4 bridge smoke 索引 · 若需）
- `04_Workflows/tickets/WH-P85-*_state.md`（票檔交叉引用 · 不含已 closure 票之歷史 C/D 改寫）
- `04_Workflows/tickets/WH-P85-CI-LAND-doc-sync-v1_state.md`（本檔 B/C/D 回填）
- `04_Workflows/00_Agent_Work_Progress.md`（**僅**末尾 append doc-sync 收口條目 · **不**重寫歷史段）

### blocked_paths

- `.github/workflows/bridge-smoke.yml`（logic · 零 diff）
- 任何 `*.py` · `gov_core_system/**`
- 其它 `.github/workflows/**`
- Progress 歷史 Wave-D/E/F/G 既有段落（禁止覆蓋 / 重排）

### acceptance_criteria（實作票預留 · skeleton 占位）

- **AC-1**：runbook §0.3 job 表與 `bridge-smoke.yml` **逐欄一致**（id · display name · 14/14 · 7/7 · skip 語意）。
- **AC-2**：WORKFLOW_INDEX §1.4（若 touched）引用 **14/14** + HTTP **7/7** 或指向 runbook，**無 stale 10**。
- **AC-3**：本 sweep 涉及之 P8.5 票檔索引無互相矛盾之 job 名 / 計數。
- **AC-4**：**零** workflow logic diff · **零** Python diff。
- **AC-5**：Reviewer 抽樣 3 處 cross-ref（workflow header · runbook §0.3 · 任一更新票檔）一致。

---

## STATE

- **overall_status**: validated
- **current_owner**: scribe / orchestrator
- **next_action**: 無（doc-sync 已 validated）；Scribe 可選 append Progress doc-sync 收口條目
- **last_updated**: 2026-06-23 · reviewer
- **notes**: doc sweep 完成 · 零 workflow / Python diff · Progress 歷史段未改寫 · Reviewer AC-1–AC-5 全通過
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-23 開 WH-P85-CI-LAND-doc-sync-v1 skeleton
  - **Implementer (B)**: done — 2026-06-23 doc-only sweep（runbook §0.3 · WORKFLOW_INDEX §1.4 · WH-P85 / WD-P85-T3 票檔 FRAME·B_REPORT）
  - **Reviewer (C)**: done — 2026-06-23 AC-1–AC-5 抽樣對照 · verdict **accepted**
  - **Scribe (D)**: done — 2026-06-23 D_REPORT（doc-sync 收口 · Progress append 可選）

---

## B_REPORT (Implementer)

- **status**: done
- **changed_files**:
  - `docs/phase8_5-bridge-smoke-runbook-v1.md` — §0.3 job 表加 Actions display name 欄 · Scenario 1/2 表 · 歷史 10 tests supersede 註腳
  - `04_Workflows/WORKFLOW_INDEX.md` — §1.4 Smoke A/B **14/14** + **7/7** · CI advisory 雙 job 索引 · Scenario 1/2 cross-ref · Wave-H+1 首跑紀錄 · 歷史 10 tests 註腳
  - `04_Workflows/tickets/WH-P85-CI-LAND-v1_state.md` — FRAME summary 補 Scenario 命名 · 指向 doc-sync 下游票
  - `04_Workflows/tickets/WH-P85-SMOKE-B-advisory-v1_state.md` — FRAME goal 補 job id / display name / Scenario cross-ref
  - `04_Workflows/tickets/WH-P85-SMOKE-B-scenario2-v1_state.md` — FRAME 補 runbook §0.3 Scenario 2 同名 cross-ref
  - `04_Workflows/tickets/WH-P85-wave-H2-entry-v1_state.md` — 已知缺口「Doc partial」指向本票收口
  - `04_Workflows/tickets/WD-P85-T3-bridge-index-test-count-closure-v1_state.md` — B_REPORT closure/suggestions 補 **p85-bridge-smoke-b** **7/7**
  - `04_Workflows/tickets/WH-P85-CI-LAND-doc-sync-v1_state.md` — 本檔 B_REPORT / STATE

- **sweep_summary**:

| 改動類型 | 摘要 |
|----------|------|
| **10→14 / 7/7 計數** | WORKFLOW_INDEX §1.4 明示 Smoke A **14/14** · Smoke B **7/7**；runbook §0.3 歷史註腳 supersede 舊 Progress「10 tests」 |
| **Job id / Actions 顯示名** | runbook §0.3 與 WORKFLOW_INDEX §1.4 對齊 `p85-bridge-smoke-a` · **P85 Bridge Smoke A (advisory · 14/14)** · `p85-bridge-smoke-b` · **P85 Bridge Smoke B (advisory · HTTP API)** · workflow **P85 Bridge Smoke CI (advisory)** |
| **Scenario 1 / 2 cross-ref** | runbook §0.3 新增 Scenario 表（與 CI-LAND B_REPORT §5 同名）；WORKFLOW_INDEX §1.4 指向 `WH-P85-CI-LAND-v1`；scenario2 / CI-LAND / SMOKE-B 票 FRAME 互引 |
| **WORKFLOW_INDEX 早期狀態** | 補 CI advisory 雙 job 段 · Wave-H+1 Scenario 1 **本機 smoke validated**（remote GA pending CI-LAND push）· 不再僅 Wave-E 本地 14/14 |

- **not_changed**:
  - `.github/workflows/bridge-smoke.yml`（logic · 零 diff）
  - 所有 `*.py` · tests · `00_Agent_Work_Progress.md` 歷史段
  - 票檔 `STATE.overall_status`（除本票）· 所有 `C_REPORT` / `D_REPORT`

- **verification**:
  - 唯讀對照 `bridge-smoke.yml`：`name:` = **P85 Bridge Smoke CI (advisory)** · jobs `p85-bridge-smoke-a` / `p85-bridge-smoke-b` · display names 與 runbook §0.3 表一致
  - `grep` bridge 語境：`WORKFLOW_INDEX.md` §1.4 + runbook §0.3 無 stale **10/10**（歷史 Progress 依 FRAME 保留 · 已加 supersede 註腳）
  - **零** workflow logic diff · **零** Python diff

---

## C_REPORT (Reviewer)

- **verdict**: **accepted**
- **one_liner**: 以 **`bridge-smoke.yml` + runbook §0.3 為 SSOT** 將 P8.5 CI 描述統一為 **14/14 + 7/7 + 雙 job**，Scenario 1/2 命名一致。
- **gaps**: bridge **in-memory stub** — doc 對齊不等同 production 持久化；Smoke C 仍 manual。
- **AC_recheck**:
  - **AC-1 ✅**: runbook §0.3 job 表與 `bridge-smoke.yml` 逐欄一致 — workflow **`P85 Bridge Smoke CI (advisory)`** · jobs **`p85-bridge-smoke-a`** / **`p85-bridge-smoke-b`** · display names **P85 Bridge Smoke A (advisory · 14/14)** / **P85 Bridge Smoke B (advisory · HTTP API)** · **14/14** · **7/7** · skip / `continue-on-error: true` 語意一致；Scenario 2 jobs 表與 workflow `p85-bridge-smoke-*-scenario2` 對齊。
  - **AC-2 ✅**: `WORKFLOW_INDEX.md` §1.4 明示 Smoke A **14/14** · Smoke B **7/7** · advisory 雙 job · Scenario 1/2 cross-ref；bridge 語境無 stale **10/10**（僅歷史 supersede 註腳）。
  - **AC-3 ✅**: 抽樣 `WH-P85-CI-LAND-v1` · `WH-P85-SMOKE-B-advisory-v1` · `WH-P85-SMOKE-B-scenario2-v1` · `WD-P85-T3` FRAME/B_REPORT — job id / 計數 / **advisory · non-blocking · 非 required check** 無互相矛盾。
  - **AC-4 ✅**: 零 workflow logic diff · 零 Python diff（依 B_REPORT · 唯讀對照 workflow 未變）。
  - **AC-5 ✅**: 三處 cross-ref 一致 — (1) workflow `name:` + job `name:` (2) runbook §0.3 雙 job 表 + Scenario 表 (3) `WORKFLOW_INDEX` §1.4 CI advisory 段。
- **scenario_naming**: **Scenario 1 — happy path** · **Scenario 2 — deps skip probe**（runbook §0.3）與 `WH-P85-SMOKE-B-scenario2-v1` FRAME / CI-LAND Progress 模板 **Scenario 2 — skip or advisory fail** 互補不衝突（前者為 GA dispatch 實作名 · 後者為 Progress 記錄模板）。
- **review_date**: 2026-06-23

---

## D_REPORT (Scribe)

- **status**: done
- **closure_summary**: doc-sync 已完成；P8.5 CI 文字／索引／票檔交叉引用已以 **`bridge-smoke.yml` + runbook §0.3** 為 SSOT 收口；Progress 歷史段依 FRAME 未改寫。
- **future_process**: 未來如有新 Scenario 或 job，只要以 workflow 為 SSOT 重跑同樣 doc sweep 流程即可（runbook §0.3 → WORKFLOW_INDEX §1.4 → 相關 `WH-P85-*` 票檔 FRAME/B_REPORT）。
- **suggestions**: 可選 — 日後以 tooling（例如 CI workflow parse + grep stale 計數）自動檢查 doc vs workflow 差異，降低 drift 復發；**不必**立刻開票。
- **progress_append**: 可選 — Scribe 若需 Progress 留痕，可 append 一句 doc-sync **validated** 條目；非 blocking。
- **scribe_date**: 2026-06-23
