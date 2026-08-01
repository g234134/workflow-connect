# WH-P85-CI-LAND-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-H · P8.5 bridge CI · 工作區落地 / 首跑準備（doc-only · 不 push）

---

## FRAME

- **summary**: 將 Wave-G（Smoke A）與 Wave-H（Smoke B）已交付、但**尚未入版控**的 advisory CI 資產整理到 **可 commit / 可 push / 可 `workflow_dispatch`** 狀態；產出首跑操作說明（**Scenario 1 — happy path** · **Scenario 2 — skip or advisory fail** · 與 runbook §0.3 同名）。**本票不改 workflow logic、不改 Python。** Doc 索引 sweep 見下游 **`WH-P85-CI-LAND-doc-sync-v1`**。

- **scope**:
  - 盤點並對齊待提交檔案：`.github/workflows/bridge-smoke.yml`（雙 job A+B）· `docs/phase8_5-bridge-smoke-runbook-v1.md`（§0.3）· `04_Workflows/00_Agent_Work_Progress.md`（Wave-G/H 條目）· `04_Workflows/tickets/WH-P85-SMOKE-B-advisory-v1_state.md`（上游 Implementer 票）
  - 建立本票 `WH-P85-CI-LAND-v1_state.md` 與 **首跑 checklist**（git 步驟 · Actions 入口 · job 觀察 · Progress 記錄模板）
  - 工作區檔案內容與 runbook / 上游票 **語意一致**（允許 1–2 句 wording 對齊）

- **non_goals**:
  - **不**修改 `bridge-smoke.yml` job steps / env / triggers（logic frozen）
  - **不**修改任何 bridge Python、tests、`app_api.py`
  - **不**新增 Smoke C CI workflow
  - **不**將 advisory jobs 升為 branch protection **required** check
  - **不**在本輪 `git push`（僅整理到可提交狀態）

- **allowed_paths**:
  - `04_Workflows/tickets/WH-P85-CI-LAND-v1_state.md`（本檔 · 必建）
  - `docs/phase8_5-bridge-smoke-runbook-v1.md`（可選 · 1–2 句對齊）
  - `04_Workflows/00_Agent_Work_Progress.md`（可選 · 末尾 append / 短表對齊）

- **blocked_paths**:
  - `.github/workflows/bridge-smoke.yml`（logic · 本票只盤點不 diff）
  - 任何 `*.py` · `gov_core_system/**`
  - 其它 `.github/workflows/**`
  - 其它 `04_Workflows/tickets/**`（含 `WH-P85-SMOKE-B-advisory-v1_state.md` 內容）

- **acceptance_criteria**:
  - **AC-1**：本票 FRAME / STATE / B_REPORT 齊全；首跑 checklist 可照做
  - **AC-2**：待提交清單與 `git status` 一致（workflow + runbook + Progress + 上游票 + 本票）
  - **AC-3**：checklist 標明 GitHub Actions 顯示名稱、兩個 job id、Scenario 1/2 Progress 記錄格式
  - **AC-4**：runbook §0.3 與 workflow header 註解一致（14/14 · 7/7 · advisory · Smoke C manual）
  - **AC-5**：零 Python diff · 零 workflow logic diff

---

## STATE

- **overall_status**: done
- **current_owner**: orchestrator / human（push + 首跑）
- **next_action**: 依 B_REPORT「首跑 checklist」執行 `git add` / commit / push → Actions `workflow_dispatch` → 依 Scenario 記錄 Progress
- **last_updated**: 2026-06-22 · implementer
- **notes**: 承接 WH-P85-SMOKE-B-advisory-v1；closure 前最後一哩 — 版控落地
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-22 開 WH-P85-CI-LAND-v1
  - **Implementer (B)**: done — 2026-06-22 票檔 + checklist + 可選 Progress/runbook 對齊
  - **Reviewer (C)**: pending — 首跑後對照 Scenario 記錄
  - **Scribe (D)**: pending — push 後 append Progress 首跑結果

---

## B_REPORT (Implementer)

### 待提交檔案盤點（與工作區 `git status` 對齊）

| 路徑 | 狀態 | 說明 |
|------|------|------|
| `.github/workflows/bridge-smoke.yml` | untracked | Wave-G A + Wave-H B 雙 job advisory workflow |
| `docs/phase8_5-bridge-smoke-runbook-v1.md` | untracked | §0.3 CI advisory 索引（A 14/14 · B 7/7 · C manual） |
| `04_Workflows/00_Agent_Work_Progress.md` | modified | Wave-G / Wave-H append（含 advisory 表） |
| `04_Workflows/tickets/WH-P85-SMOKE-B-advisory-v1_state.md` | untracked | 上游 Implementer 票（Smoke B） |
| `04_Workflows/tickets/WH-P85-CI-LAND-v1_state.md` | untracked | 本票 |

### 首跑 checklist（commit → push → Actions → Progress）

#### 1. Git add / commit（本機 · 本輪不 push）

```powershell
# repo root
git add .github/workflows/bridge-smoke.yml
git add docs/phase8_5-bridge-smoke-runbook-v1.md
git add 04_Workflows/00_Agent_Work_Progress.md
git add 04_Workflows/tickets/WH-P85-SMOKE-B-advisory-v1_state.md
git add 04_Workflows/tickets/WH-P85-CI-LAND-v1_state.md

git status   # 確認僅上述五檔（或預期 subset）在 staged

git commit -m "$(cat <<'EOF'
Land P8.5 bridge Smoke A+B advisory CI workflow and runbook.

Wave-G/H deliverables: non-blocking p85-bridge-smoke-a/b jobs, runbook §0.3, Progress, ticket state.
EOF
)"
```

> **PowerShell 無 HEREDOC**：改用手動 `-m "Land P8.5 bridge Smoke A+B advisory CI…"` 單行或 here-string `@'…'@`。

#### 2. Push（人類操作 · 本 Implementer 輪次不做）

```powershell
git push -u origin HEAD
```

#### 3. GitHub Actions 入口

| 項 | 值 |
|----|-----|
| **Workflow 檔** | `.github/workflows/bridge-smoke.yml` |
| **Actions UI 顯示名稱** | **P85 Bridge Smoke CI (advisory)** |
| **建議首跑方式** | Repo → **Actions** → 左側選 **P85 Bridge Smoke CI (advisory)** → **Run workflow**（`workflow_dispatch`）→ 選 target branch → Run |
| **其它觸發** | Daily cron UTC 06:00 · path-filtered `pull_request`（改 bridge 相關路徑時） |

#### 4. 必觀察 jobs

| Job id | Display name | 預期（deps OK） | Skip 信號 |
|--------|--------------|-----------------|-----------|
| **`p85-bridge-smoke-a`** | P85 Bridge Smoke A (advisory · 14/14) | unittest **14/14** · log 含 `Bridge Smoke A passed` | `::notice title=Bridge Smoke Skipped::…` 或 `Bridge Smoke … skipped` · step exit 0 |
| **`p85-bridge-smoke-b`** | P85 Bridge Smoke B (advisory · HTTP API) | unittest **7/7** · log 含 `Bridge Smoke B passed` | `::notice title=Bridge Smoke B skipped::reason=…` · step exit 0 |

**共同約束**：兩 job 皆 `continue-on-error: true` — **失敗不阻 merge**；失敗時找 `::warning title=Bridge Smoke … failed (advisory)::`。

**Artifacts（非 skip 時）**：`p85-bridge-smoke-a-<run_id>` · `p85-bridge-smoke-b-<run_id>`（各含 `bridge_smoke_*.log`）。

#### 5. Scenario 1 / Scenario 2 → Progress 記錄

首跑後於 `04_Workflows/00_Agent_Work_Progress.md` **末尾 append**（不改寫歷史段）：

| Scenario | 條件 | Progress 記什麼 |
|----------|------|-----------------|
| **Scenario 1 — happy path** | 兩 job 均未 skip · A **14/14** · B **7/7** · workflow run **completed**（job 可 green 或 yellow advisory） | 標題例：`## YYYY-MM-DD · Wave-H · P8.5 bridge CI 首跑 · Scenario 1 (pass)` · 列 **workflow run URL** · job 結果表（A 14/14 · B 7/7）· 註明 **non-blocking / 非 required** |
| **Scenario 2 — skip 或 advisory fail** | 任一 job **skipped**（deps gate）或 unittest **failed** 但 workflow 仍 completed | 標題例：`… Scenario 2 (skip or advisory fail)` · 列 run URL · 逐 job：`skipped` + `skip_reason` **或** `failed` + `::warning` 摘要 · 註明 **不阻 merge** · 若 skip：記「待 deps 路徑複驗」；若 fail：記「對照本地 venv 14/14 + 7/7 是否仍 OK」 |

**Progress 條目最小欄位**：日期 · 票 `WH-P85-CI-LAND-v1` · Actions 顯示名 · run id/URL · 兩 job 狀態 · Scenario 編號 · 下一步（例：Reviewer 收口 / 無需 action）。

### changed_files（本票 Implementer）

- `04_Workflows/tickets/WH-P85-CI-LAND-v1_state.md` — 新建（FRAME + 首跑 checklist）
- `04_Workflows/00_Agent_Work_Progress.md` — 末尾 append CI-LAND 條目；advisory CI 短表補 `p85-bridge-smoke-b`（若實施）
- `docs/phase8_5-bridge-smoke-runbook-v1.md` — §0.3 補 Actions UI 顯示名一句（若實施）

### not_changed

- `.github/workflows/bridge-smoke.yml`（logic · 零 diff）
- 所有 `*.py`
- 其它 workflow 檔
- `WH-P85-SMOKE-B-advisory-v1_state.md` 內文

### verification

- `git status --short` 五檔狀態與上表一致
- workflow `name:` = `P85 Bridge Smoke CI (advisory)` · jobs = `p85-bridge-smoke-a` / `p85-bridge-smoke-b`（唯讀對照）
- runbook §0.3 job 表與 workflow 註解一致
- **未執行** push / 遠端 Actions 首跑（留待 Scenario 1/2 人類步驟）

### AC checklist

- **AC-1 ✅**: 本票 FRAME / STATE / B_REPORT + checklist
- **AC-2 ✅**: 待提交清單 = git status 盤點
- **AC-3 ✅**: Actions 名 · 兩 job · Scenario Progress 模板
- **AC-4 ✅**: runbook §0.3 ↔ workflow header 一致
- **AC-5 ✅**: 零 Python · 零 workflow logic diff

---

## C_REPORT (Reviewer)

- **verdict**: pending
- **notes**: 待首跑 push 後依 Scenario 1/2 對照 AC

---

## D_REPORT (Scribe)

- **status**: pending
- **notes**: push + 首跑 Progress append 後收口
- **scenario_2_cross_ref**: deps-gate skip 探針已由 **`WH-P85-SMOKE-B-scenario2-v1`** 交付（Strategy A · `workflow_dispatch` **scenario=scenario2**）· 操作與預期 log 見 runbook **§0.3** Scenario 2 表 · Reviewer **`validated`**（2026-06-23）
- **ops_run_unblock_cross_ref**: **`WH-P85-SMOKE-B-scenario2-ops-run-v1`** 解阻需 **`WH-P85-CI-LAND-bridge-smoke-push-v1`**（`bridge-smoke.yml` commit + push 至 `main`）· CI-LAND push 具體由 **`WH-P85-CI-LAND-bridge-smoke-push-v1`** 負責 · **2026-06-24 更新**：CI-LAND 推送已由 **`WH-P85-CI-LAND-bridge-smoke-push-v1`** 完成（commit `99bf1f590` · workflow id 301057708 active）· ops-run 解阻只剩 **GA dispatch + log 驗收 + Progress append**
