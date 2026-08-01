# WH-P85-CI-LAND-bridge-smoke-push-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> **P8.5 CI-LAND push 票** — 已將 `.github/workflows/bridge-smoke.yml` landing 至 `origin/main`（commit `99bf1f590`）；**GA dispatch 不在本票 scope**。

---

## META

| 欄位 | 值 |
|------|-----|
| **Phase** | P8.5 · Wave-H bridge CI |
| **類型** | CI-LAND（workflow push · 非 logic 變更） |
| **lane** | P8.5 advisory CI · 與 **`WH-P85-CI-LAND-v1`** 同線 |
| **owner** | orchestrator / human（具 repo push 權限）— 參考 **`WH-P85-CI-LAND-v1`** STATE |
| **upstream SSOT** | **`WH-P85-CI-LAND-v1`** B_REPORT 首跑 checklist · 本機 `bridge-smoke.yml`（含 Scenario 2 jobs） |

---

## FRAME

### Goal

**一句話**：在具權限環境中 **commit + push** `.github/workflows/bridge-smoke.yml` 至 **`main`**，使 GitHub Actions 出現 **P85 Bridge Smoke CI (advisory)** workflow，並確認 **`Run workflow`** 與 **`scenario`** 下拉（`default` / `scenario2`）可用。

### Scope

- **最小集**：`.github/workflows/bridge-smoke.yml` → `git add` → commit → `git push origin main`
- **可選 companion**（依 **`WH-P85-CI-LAND-v1`** 首跑 checklist · **不阻塞**本票 AC）：`docs/phase8_5-bridge-smoke-runbook-v1.md` · 相關 `WH-P85-*_state.md` · Progress 條目

### Non-goals

- **不**修改 `bridge-smoke.yml` job steps / env / triggers（logic frozen）
- **不**修改任何 Python、tests、`app_api.py`
- **不**在本 skeleton 輪次 commit / push / 跑 GA
- **不**將 advisory jobs 升格為 branch protection **required** check
- **不**在本票執行 Scenario 1/2 dispatch（留給下游 ops-run 票）

### allowed_paths（執行票）

- `.github/workflows/bridge-smoke.yml`（**add + commit + push only** · 零 logic diff）
- `04_Workflows/tickets/WH-P85-CI-LAND-bridge-smoke-push-v1_state.md`（本檔 B/C/D 回填）
- 可選：`docs/phase8_5-bridge-smoke-runbook-v1.md` · `04_Workflows/00_Agent_Work_Progress.md` · 其它 P8.5 票（companion commit）

### blocked_paths

- 任何 `*.py` · `gov_core_system/**`
- `bridge-smoke.yml` **logic diff**（禁止改 job / trigger / env）
- 其它 `.github/workflows/**`（本票 scope 外）

### acceptance_criteria

- **AC-1**：`bridge-smoke.yml` 已 on **`origin/main`**（`git show origin/main:.github/workflows/bridge-smoke.yml` 存在）
- **AC-2**：Actions UI 左側可見 **P85 Bridge Smoke CI (advisory)** · **Run workflow** 按鈕存在
- **AC-3**：`workflow_dispatch` input **`scenario`** 下拉含 **`default`** · **`scenario2`**
- **AC-4**：本票 B_REPORT 含 push 證據（commit hash · push 時間 · Actions UI 確認摘要）· **overall_status → `done`**
- **AC-5**：零 workflow logic diff · 零 Python diff

---

## STATE

- **overall_status**: done_with_gaps
- **current_owner**: ops / human（GA dispatch）
- **next_action**: 下游 **`WH-P85-SMOKE-B-scenario2-ops-run-v1`** — Actions **`workflow_dispatch` · `scenario=scenario2`** → log 驗收 → Progress append
- **last_updated**: 2026-06-24 · P8.5 CI-LAND push 實作代理
- **notes**:
  - **`bridge-smoke.yml` 已 landing `origin/main`** — commit **`99bf1f590`** · push **`main → origin/main`** 成功
  - GitHub Actions API 確認 workflow **P85 Bridge Smoke CI (advisory)** · id **301057708** · state **active**
  - **gap**：本票 scope 只做 landing，**未執行任何 GA run**（dispatch 留給 ops-run 票）
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-24 開 WH-P85-CI-LAND-bridge-smoke-push-v1 FRAME
  - **Implementer (B)**: done — 2026-06-24 commit + push + API 驗證
  - **Reviewer (C)**: done — 2026-06-24 `accepted_with_gaps`（未跑 GA）
  - **Scribe (D)**: done — cross-ref 已更新下游 ops-run / CI-LAND-v1

---

## B_REPORT (Implementer)

### purpose

將 `.github/workflows/bridge-smoke.yml` 真正 **landing** 到 **`origin/main`**，使 **P85 Bridge Smoke CI (advisory)** 出現在 Actions UI，解除 **`WH-P85-SMOKE-B-scenario2-ops-run-v1`** 之 GA dispatch 阻塞。

### status

done_with_gaps — **push 完成** · **未跑 GA**

> 已將 `.github/workflows/bridge-smoke.yml` push 至 `origin/main`（commit hash 對應 CI-LAND 變更 · **`99bf1f590`**）；遠端可見 workflow 名稱 **P85 Bridge Smoke CI (advisory)**，支援 `workflow_dispatch` 與 `scenario` 參數；本票 **不涵蓋** 任一 GA run 的 dispatch，Scenario1/2 run 仍 pending。

### git 操作（2026-06-24 · P8.5 CI-LAND push 實作代理）

| 步 | 動作 | 結果 |
|----|------|------|
| add | `git add .github/workflows/bridge-smoke.yml` | 僅 workflow 一檔 staged |
| commit | `git commit -m "P85: land bridge-smoke advisory workflow"` | **`99bf1f590`** · 268 insertions |
| push | `git push origin main` | **`a56328229..99bf1f590 main → main`** 成功 |

> 注：push 一併帶上本地既存 2 commits（ticket close-out docs）；本票 commit **僅含** `bridge-smoke.yml`。

### Actions 驗證（2026-06-24）

| 檢查項 | 結果 |
|--------|------|
| **遠端檔** | `git show origin/main:.github/workflows/bridge-smoke.yml` ✅ |
| **GitHub API workflows 列表** | **P85 Bridge Smoke CI (advisory)** · path `.github/workflows/bridge-smoke.yml` · id **301057708** · state **active** ✅ |
| **Run workflow 按鈕** | 未以 UI 手動點擊；依 API `state=active` + workflow 含 `workflow_dispatch` 推定可用 |
| **scenario 下拉** | 本機 yml 唯讀對照：`default` / `scenario2` ✅（UI 未手動截圖） |
| **GA run** | **本票 scope 只做 landing，不做 GA dispatch** — 無 run_id / URL |

### push checklist（人類 · 具權限環境）

#### 1. 預檢

| 項 | 預期 |
|----|------|
| **本機檔** | `.github/workflows/bridge-smoke.yml` 存在 · workflow `name:` = **P85 Bridge Smoke CI (advisory)** |
| **遠端缺口** | `git show origin/main:.github/workflows/bridge-smoke.yml` **不存在**（push 前） |
| **上游 checklist** | 詳細 git 步驟見 **`WH-P85-CI-LAND-v1`** B_REPORT §首跑 checklist |

#### 2. Stage · commit

```powershell
# repo root
git add .github/workflows/bridge-smoke.yml

git status   # 確認僅預期 workflow（± 可選 companion 檔）在 staged

git commit -m "Land P8.5 bridge Smoke A+B advisory CI workflow (bridge-smoke.yml)."
```

> **最小 scope**：僅 `bridge-smoke.yml` 亦可解阻 ops-run；companion 檔依 CI-LAND-v1 五檔清單 optional。

#### 3. Push

```powershell
git push origin main
```

#### 4. Actions UI 驗收

| 檢查項 | 預期 |
|--------|------|
| **Workflow 列表** | 左側出現 **P85 Bridge Smoke CI (advisory)** |
| **Run workflow** | 按鈕可點 · `workflow_dispatch` 可用 |
| **scenario 下拉** | 含 **`default`** · **`scenario2`** |
| **Job ids（唯讀對照）** | `p85-bridge-smoke-a` / `p85-bridge-smoke-b` · Scenario 2：`p85-bridge-smoke-a-scenario2` / `p85-bridge-smoke-b-scenario2` |

**本票不要求**在本步 dispatch 或跑 GA；Scenario 2 實跑留 **`WH-P85-SMOKE-B-scenario2-ops-run-v1`**。

### changed_files（本輪）

- `.github/workflows/bridge-smoke.yml` — **新建 on `origin/main`**（commit `99bf1f590`）
- `04_Workflows/tickets/WH-P85-CI-LAND-bridge-smoke-push-v1_state.md` — B/C/STATE 回填

### not_changed

- 所有 `*.py` · tests · runbook · workflow logic
- 其它 `.github/workflows/**`

### verification

- `git show origin/main:.github/workflows/bridge-smoke.yml` — 存在 ✅
- GitHub API `GET .../actions/workflows` — **P85 Bridge Smoke CI (advisory)**  listed ✅
- **未執行** GA dispatch（scope 外）

### AC checklist

- **AC-1 ✅**: `bridge-smoke.yml` on `origin/main`（commit `99bf1f590`）
- **AC-2 ✅**: Actions workflow 可見（API id 301057708 · state active）
- **AC-3 ✅**: yml 含 `scenario` choice `default`/`scenario2`（UI 未手動截圖 · API 無 inputs 端點）
- **AC-4 ✅**: B_REPORT push 證據已填 · STATE **`done_with_gaps`**
- **AC-5 ✅**: 零 workflow logic diff · 零 Python diff

---

## C_REPORT (Reviewer)

- **verdict**: accepted_with_gaps
- **review_date**: 2026-06-24
- **core**: push 成功 · workflow active on remote · AC-1–AC-5 滿足（AC-4 以 `done_with_gaps` 收口）。
- **notes**: GitHub API 確認 **P85 Bridge Smoke CI (advisory)** 存在；Run workflow / scenario 下拉未以 UI 手動截圖，但 yml 與 API state 一致。
- **gaps**:
  - **gap：尚未執行任何 Scenario1/Scenario2 GA run；Progress 無 run_id/URL 留痕** — dispatch 留 **`WH-P85-SMOKE-B-scenario2-ops-run-v1`**
  - **Run workflow UI 未手動點擊驗證** — 僅 API + yml 對照

---

## D_REPORT (Scribe)

- **status**: done
- **scribe_date**: 2026-06-24
- **notes**: push 完成 · **`WH-P85-SMOKE-B-scenario2-ops-run-v1`** workflow landing 前置已解除 · 阻塞降縮為 GA dispatch + log 驗收。

### depends_on

| 票 / 資產 | 關係 |
|-----------|------|
| **`WH-P85-CI-LAND-v1`** | 首跑 checklist SSOT · git 步驟 · Actions 名稱 · Scenario 模板 |

### downstream

| 票 / 資產 | 關係 |
|-----------|------|
| **`WH-P85-SMOKE-B-scenario2-ops-run-v1`** | **解阻票** — push 完成後可 GA dispatch `scenario=scenario2` |
| **`docs/WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md`** | 可選更新 — toolchain 索引補 P85 advisory workflow landing 狀態 |

### unblock 路徑（摘要）

```
frame_ready
  → [本票] commit + push bridge-smoke.yml → main
  → [Actions UI] P85 Bridge Smoke CI (advisory) 可見
  → [WH-P85-SMOKE-B-scenario2-ops-run-v1] GA dispatch scenario2
  → Progress append → ops-run done
```
