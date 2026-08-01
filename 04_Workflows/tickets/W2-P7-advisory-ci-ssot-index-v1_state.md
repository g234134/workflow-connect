# TICKET STATE · W2-P7-advisory-ci-ssot-index-v1 · P7 advisory CI SSOT 索引

> handoff 摘要檔；Wave 2 · P7 · **doc-only** · 誠實索引 advisory CI · **不**改 workflow · **不**升格 required check。

---

## FRAME

- **Goal**: 把 P7 線 **advisory CI** 與相關 smoke 路徑集中索引，明確 **advisory · non-gate · non-prod**，解阻 Master Review B-3。
- **Scope**:
  - 新建 `docs/P7_ADVISORY_CI_INDEX.md`（SSOT 正文）
  - `04_Workflows/WORKFLOW_INDEX.md` §1.45「P7 · Advisory CI vs gate」
  - `docs/WAVE_PROGRESS_DASHBOARD.md` Wave-next 敘事 cross-ref（**不改 Phase%**）
  - FRAME 本區列出全部 P7 advisory CI workflows 與 human-env 路徑
- **NonScope**:
  - ❌ 不修改 `.github/workflows/p7-notification-smoke.yml` 或任何 CI 行為
  - ❌ 不升格 required check / branch protection
  - ❌ 不跑 GA / 不伪造 run URL · 不宣稱 Round-2 execute 完成 · 不上调 Phase%
  - ❌ 不重複 Wave 3 P8/P8.9 advisory 正文
- **AllowedPaths**:
  - `docs/P7_ADVISORY_CI_INDEX.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（敘事 only）
  - `04_Workflows/tickets/W2-P7-advisory-ci-ssot-index-v1_state.md`
- **BlockedPaths**:
  - `.github/workflows/**`
  - `core/**` · `tests/**`（本票 doc-only）
  - branch protection / repo settings
- **Dependencies**:
  - `WH-P7-PROD-prod-rollout-governance-bootstrap-v1` G8
  - `.github/workflows/p7-notification-smoke.yml`（只讀）
  - `W-MASTER-wave-plan_state.md` Wave 2 區塊
- **AcceptanceCriteria**:
  - AC-1：WORKFLOW_INDEX ≥2 條 P7 CI/smoke 條目 · 每條 advisory 或 human-env 標籤
  - AC-2：`p7-notification-smoke` 寫清 `continue-on-error` · `127.0.0.1:8080` · ≠ merge gate
  - AC-3：bootstrap G8 與 INDEX 一致（仍 open/advisory）
  - AC-4：Dashboard 敘事 cross-ref · **無 Phase% 變更**
  - AC-5：對照 inspector §3.2 無反向敘事
  - AC-6：non-claim 段齊全

### Build spec（B）— P7 advisory CI / smoke 清單

| # | 路徑 / SSOT | 用途 | 觸發條件 | 結果類型 | 標籤 |
|---|-------------|------|----------|----------|------|
| 1 | `.github/workflows/p7-notification-smoke.yml` | 全鏈 notify unittest + localhost mock | PR paths · cron · `workflow_dispatch` | unittest exit · warning · artifact | **advisory · non-gate · non-prod** |
| 2 | `WH-P7-PROD-staging-smoke-runbook-v1_state.md` | staging S1–S4 手動 smoke | human ops env | 人工 log / execute 物证 | **human-env-only · non-gate · non-prod** |
| 3 | 三 unittest 模組（見 INDEX §3） | 本機 / CI 子集 smoke | `python -m unittest …` | pass/fail 計數 | **local_smoke · non-gate · non-prod** |
| 4 | bootstrap **G8** | required CI 升格模板 | governance 批文 | **`open`** | **governance_template · 非 workflow · 未升格** |

---

## STATE

- overall_status: done
- implementation_status: done
- current_owner: scribe
- next_action: none — Scribe 收口完成（Reviewer accepted · Master Review B-3 Resolved）
- last_updated: 2026-06-26 · scribe
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- non_claims:
  - indexed GitHub Actions workflows 均為 **advisory · non-gate · non-prod**
  - `p7-notification-smoke` **未**升格 required check（G8 仍 `open`）
  - advisory CI 索引就緒 **≠** Round-2 execute GO **≠** staging 集成完成
  - **未**上调 Dashboard Phase%

---

## B_REPORT

- **changed_files**:
  - `docs/P7_ADVISORY_CI_INDEX.md`（新建 · SSOT 正文）
  - `04_Workflows/WORKFLOW_INDEX.md`（§1.45 P7 Advisory vs gate）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（Wave-next P7 敘事 cross-ref · Phase% 不變）
  - `04_Workflows/tickets/W2-P7-advisory-ci-ssot-index-v1_state.md`（本檔）
- **索引涵蓋範圍**:
  - **1** GitHub Actions advisory workflow（`p7-notification-smoke.yml`）
  - **1** human-env-only staging smoke runbook（非 CI）
  - **3** local unittest smoke 模組（CI 子集）
  - **1** governance G8 required-CI 升格模板（`open` · default advisory）
  - cross-wave 分線表（P8/P9 指向 Wave 3 · 非 P7 正文）
- **artifacts**: `docs/P7_ADVISORY_CI_INDEX.md`
- **verification**: 見 D_REPORT（Implementer 已跑 verify_commands）
- **behavior_notes**: 僅 doc/index · **零** workflow 變更
- **deferred_items**: Wave 3 `W3-P8-ADV` P8/P8.9 advisory 索引 · G8 升格施工（Wave-P7-6 · human 批文）

---

## C_REPORT

- **index_files**:
  - **Primary SSOT**: `docs/P7_ADVISORY_CI_INDEX.md`
  - **Index entry**: `04_Workflows/WORKFLOW_INDEX.md` §1.45
  - **Dashboard cross-ref**: `docs/WAVE_PROGRESS_DASHBOARD.md` Wave-next 敘事 P7 段
  - **Ticket FRAME Build spec**: 本檔 FRAME Build spec 表
- **Scribe 收口摘要**（2026-06-26 · verdict: **accepted**）:
  - P7 advisory CI 現有**單一 SSOT index**（`docs/P7_ADVISORY_CI_INDEX.md`）；WORKFLOW_INDEX §1.45 與 Dashboard 敘事 cross-ref 已 landing。
  - 所有 indexed GitHub Actions workflows 均標 **advisory · non-gate · non-prod**；bootstrap **G8 仍 `open`**（未升格 required check）。
  - **無 Phase% 變更**；advisory CI 索引就緒 **≠ required gate ≠ Round-2 execute GO**。

---

## D_REPORT

### verify_commands 執行摘要（2026-06-26 · implementer）

| 命令 | 結果摘要 |
|------|----------|
| `rg "P7 advisory\|advisory / non-gate / non-prod" docs/P7_ADVISORY_CI_INDEX.md` | **命中** — SSOT 含 P7 advisory 敘事與 non-gate 標題 |
| `rg "continue-on-error\|127\.0\.0\.1" .github/workflows/p7-*.yml` | **命中** — job `continue-on-error: true` · mock `127.0.0.1:8080` |
| `rg "required" .github/workflows/p7-*.yml` | **命中 2 行 · 均為註解**（「not a branch protection required check」）· **無** required check 升格 |
| `rg "G8\|advisory\|required CI" …bootstrap…state.md` | **命中** — G8 = `open` · `p7-notification-smoke` 仍 advisory |
| `rg -i "advisory\|P7_ADVISORY_CI_INDEX" WORKFLOW_INDEX.md WAVE_PROGRESS_DASHBOARD.md` | **命中** — §1.45 與 Dashboard cross-ref 已 landing |

**Observability 結論**：Reviewer 可透過 **本檔 + INDEX §1.45 + grep p7-*.yml + bootstrap G8** 確認 P7 advisory CI **存在且仍 non-gate**；Round-2 blocked 狀態見 Dashboard / execute-v2 STATE。

---

## C_REPORT (Reviewer)

<!-- Reviewer 填 -->

---

## D_REPORT (Scribe)

<!-- Scribe 填 -->
