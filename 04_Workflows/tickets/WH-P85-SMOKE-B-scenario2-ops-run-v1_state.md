# WH-P85-SMOKE-B-scenario2-ops-run-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> **P8.5 Scenario 2 GA 實跑 / Progress 紀錄票** — 給 ops / oncall 用；補 `WH-P85-SMOKE-B-scenario2-v1` AC-1 / AC-3 實證缺口（Reviewer C_REPORT nit）。

---

## FRAME

### Background

| 項 | 狀態 |
|----|------|
| **Scenario 2 設計 / workflow / tests** | **`validated`** — `WH-P85-SMOKE-B-scenario2-v1` · Strategy A · `workflow_dispatch` input **`scenario=scenario2`** · 6/6 workflow config tests OK |
| **Scenario 1 本機 smoke** | **validated**（非遠端 GA pass）— Wave-H+1 · A **14/14** · B **7/7** · 本機 unittest/smoke · **`bridge-smoke.yml` 已 landing `origin/main`**（2026-06-24 · push 票 `99bf1f590`）· 無 Scenario 1 GA run_id/URL · Progress 已 append（`WH-P85-CI-LAND-v1` / `WH-P85-SMOKE-B-advisory-v1`） |
| **Scenario 2 GA 實跑 log** | **未收錄** — Reviewer **`accepted_with_nits`**：AC-1 empirical 半開 · AC-3 Progress 條目待 ops |
| **上游 SSOT** | runbook §0.3 Scenario 2 表 · `bridge-smoke.yml` Scenario 2 jobs · `WH-P85-CI-LAND-v1` B_REPORT §5 Progress 模板 |

**缺口一句話**：deps-gate skip 分支已在設計與靜態審查層 **`validated`**，但 AC 要求至少一次 **GA 實跑 log** + Progress 末尾 **Scenario 2 條目**；本票僅執行與記錄，不改 wiring。

### Goal

**一句話**：在 GitHub Actions 手動跑一次 **`scenario=scenario2`**，確認 Scenario 2 jobs 依設計 skip（design notice + deps-gate notice · exit 0 · non-blocking），並將 run URL / run id / notice 摘要 **append 至** `04_Workflows/00_Agent_Work_Progress.md` **P8.5 段末尾**（對照 CI-LAND 模板）。

具體交付：

1. **GA 實跑**：Actions → **P85 Bridge Smoke CI (advisory)** → **Run workflow** → **`scenario = scenario2`** → workflow run **completed**。
2. **log 驗收**：兩 Scenario 2 job 成功（綠勾或 advisory 語意下 completed）· log 含 design-skip notice + 各 job deps-gate skip notice · step **exit 0** · **不阻 merge**。
3. **Progress append**：依下方 **Progress 模板** 追加一條；回填本票 B_REPORT（證據摘要）· STATE → **`done`**。
4. **cross-ref**：可選更新 `WH-P85-SMOKE-B-scenario2-v1` STATE notes（GA log 已收錄）— 非本票必須。

### Non-goals

- **不**修改 `.github/workflows/bridge-smoke.yml` · tests · runbook · 其它票（除本票 STATE / B_REPORT 回填）。
- **不**將 Scenario 2 或 advisory jobs 升格為 branch protection **required** check。
- **不**在本 skeleton 輪次 append Progress（實際 append 留給執行本票的 ops / Scribe）。
- **不**重跑 Scenario 1 或改 Scenario 1 happy path 行為。
- **不**新增 Smoke C CI 或 live curl 自動化。

### GA-remote Ops Instructions（GOV-GA-P85-S2-01）

> **Governance Batch 1 授权**：`GOV-GA-P85-S2-01` · tier=`GA-remote` · single-run · observation-only · non-gate · 回填 EVD-GR-P85-S2。  
> **执行者**：**human Ops only** — AI / 自动化 **禁止** dispatch 或预填 run URL。

#### 进入 Actions 路径

1. GitHub → 本 repo → **Actions** 标签页。
2. 左侧 workflow 列表选择 **P85 Bridge Smoke CI (advisory)**。
3. 右侧点击 **Run workflow**。

#### Workflow 名称 / branch / 参数

| 项 | 值 |
|----|-----|
| **Workflow 显示名** | **P85 Bridge Smoke CI (advisory)** |
| **Workflow 文件** | `.github/workflows/bridge-smoke.yml` |
| **Use workflow from** | **`main`**（或含 Scenario 2 wiring 之 branch） |
| **Input: scenario** | **`scenario2`**（**勿**选 `default`） |
| **tier 标签** | `GA-remote`（Governance 授权 · **非** required check） |

#### 成功 / 失败观测指标

| 观测项 | 成功信号 | 失败信号 |
|--------|----------|----------|
| **Workflow run** | 状态 **completed**（advisory · 不阻 merge） | run **failure** 或 step exit **1** |
| **Jobs** | **仅** `p85-bridge-smoke-a-scenario2` · `p85-bridge-smoke-b-scenario2` · Scenario 1 jobs **不跑** | Scenario 1 jobs 意外执行 |
| **Log / notice** | 各 job 含 design-skip notice + deps-gate skip notice · step **exit 0** | `::warning … unexpected` · 无预期 notice |
| **exit code** | 各 smoke step **0** | 任一步 **≠ 0** → **勿**回填 pass |

#### 复制 run_url / run_id

- **run_url**：Actions run 页面浏览器地址栏完整 URL（例 `https://github.com/<org>/<repo>/actions/runs/<run_id>`）。
- **run_id**：URL 末段数字，或 UI「Run #」后的 numeric id。
- 回填：本 FRAME 下方占位栏位 · B_REPORT `ga_run` · Progress append（FRAME Progress 模板）。

#### GA-remote 证据占位（Ops 回填）

```yaml
ga_remote_run_url: https://github.com/g234134/workflow-connect/actions/runs/29157178993
ga_remote_run_id: "29157178993"
```

#### non-claims（本 runbook 重申）

- GA pass **≠** required CI **≠** prod-ready **≠** Phase closure **≠** P7 Round-2 GO。
- 本 runbook **仅** human Ops 观测用；**不代表** gate 升级 · advisory `continue-on-error: true` 不变 · Scenario 2 skip **by design** 非 CI bug。

---

### Human dispatch steps（唯一解阻入口）

> **前置已满足**：`bridge-smoke.yml` **已 landing `origin/main`**（commit `99bf1f590`）· workflow **active** · **advisory** · `continue-on-error: true` · **非 required check** · `workflow_dispatch` **含 `scenario2`**。  
> **当前状态（2026-07-11+）**：**Scenario2 GA-remote recorded** · run_id=`29157178993` · 本票 `overall_status=done`。下表保留为 **重跑／新人对照** checklist（≠「尚未跑」）。

| Step | 动作 | 完成信号 |
|------|------|----------|
| **1** | GitHub → Repo → **Actions** → 左栏选 **P85 Bridge Smoke CI (advisory)** → 右栏 **Run workflow** | UI 出现新 run |
| **2** | **Use workflow from**：**`main`** · **scenario** 下拉选 **`scenario2`**（**勿**选 `default`）→ **Run workflow** | dispatch 已提交 |
| **3** | 等待 workflow run **completed**（advisory · 不阻 merge） | run URL + run id 可复制 |
| **4** | 验收 log：**仅** `p85-bridge-smoke-a-scenario2` · `p85-bridge-smoke-b-scenario2` · Scenario 1 jobs **不跑** · 各 job 含 design-skip notice + deps-gate skip notice · step **exit 0** | 两 job **success** |
| **5** | 于 `04_Workflows/00_Agent_Work_Progress.md` **末尾 append**（FRAME「Progress 模板」· **最小栏位不可缺**） | AC-3 ✅ |
| **6** | 回填本票 B_REPORT **`ga_run`** / **`job_results`** / **`progress_append`** | 证据栏齐 |
| **7** | 本票 **STATE.overall_status → `done`** · B_REPORT **status: done** | AC-1–AC-4 ✅ |

**可选 CLI**（同等权限）：`gh workflow run bridge-smoke.yml --ref main -f scenario=scenario2`

**异常**：step exit **1** 或 unexpected warning → **勿** append Progress 为 pass · STATE 维持 **`blocked`** · 开 Implementer follow-up。

**禁止宣稱**：无 run URL 不得说 Scenario2 GA pass · 本机 bash 探针 **≠ GA 证据** · recorded PASS **≠** required CI／Phase closure／prod browser。

---

## Evidence Schema
<!-- W4-P85-S2-GA-RUNBOOK-v1 · 欄位定義 SSOT · 2026-07-13 -->

> **用途**：human／Scribe 回填與 Reviewer 抽查的欄位契約。值填入 B_REPORT／下方 YAML；**禁止**預填虛構 URL。

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `ga_run.url` | str | ✅ | Actions run 完整 URL |
| `ga_run.run_id` | str | ✅ | URL 末段數字／Run # |
| `ga_run.scenario` | str | ✅ | 必須為 `scenario2` |
| `ga_run.branch` | str | ✅ | 通常 `main` |
| `ga_run.completed` | bool | ✅ | workflow run completed |
| `job_results.a_scenario2` | enum | ✅ | `success`／`failed`／`skipped` |
| `job_results.b_scenario2` | enum | ✅ | 同上 |
| `job_results.scenario1_ran` | bool | ✅ | 必須為 `false` |
| `job_results.notices.design_skip` | bool | ✅ | design-skip notice 可見 |
| `job_results.notices.deps_gate` | bool | ✅ | deps-gate skip notice 可見 |
| `progress_append` | bool | ✅ | Progress 末尾已 append |
| `evidence_tier` | str | ✅ | `GA-remote` |

**已回填快照（2026-07-11 H3 · 勿改造）**

```yaml
ga_run:
  url: https://github.com/g234134/workflow-connect/actions/runs/29157178993
  run_id: "29157178993"
  scenario: scenario2
  branch: main
  completed: true
job_results:
  a_scenario2: success
  b_scenario2: success
  scenario1_ran: false
  notices:
    design_skip: true
    deps_gate: true
progress_append: true
evidence_tier: GA-remote
```

Cross-ref runbook：`docs/phase8_5-bridge-smoke-runbook-v1.md` §0.3 · 票 `W4-P85-S2-GA-RUNBOOK-v1`。

---

### 操作流程（ops checklist · 详版）

#### 0. 前置

| 項 | 值 |
|----|-----|
| **權限** | repo **Actions: Read and write**（或等價：可 `workflow_dispatch`） |
| **Branch** | 含 Scenario 2 wiring 的 branch（通常 **`main`** · 以遠端已 merge 為準） |
| **Workflow 顯示名** | **P85 Bridge Smoke CI (advisory)** |
| **Workflow 檔** | `.github/workflows/bridge-smoke.yml` |

#### 1. 觸發 Scenario 2 dispatch

1. 打開 GitHub → Repo → **Actions**。
2. 左側選 **P85 Bridge Smoke CI (advisory)**。
3. 右側 **Run workflow**：
   - **Use workflow from**：選含 Scenario 2 的 branch（例 **`main`**）。
   - **scenario** 下拉：選 **`scenario2`**（**不要**選 `default`）。
4. 點 **Run workflow** · 記下 **workflow run URL** 與 **run id**（Actions UI 或 URL 末段數字）。

#### 2. 等待並驗收 run

| 檢查項 | 預期 |
|--------|------|
| **Workflow 狀態** | Run **completed**（advisory · 不阻 merge） |
| **跑的 jobs** | **僅** `p85-bridge-smoke-a-scenario2` · `p85-bridge-smoke-b-scenario2` |
| **Scenario 1 jobs** | **不跑**（`p85-bridge-smoke-a` / `p85-bridge-smoke-b` 應 skipped 或未出現） |
| **Job 結果** | 兩 Scenario 2 job **success**（綠勾）· `continue-on-error: true` 語意不變 |

**逐 job log 必見（copy 摘要用）**：

| Job | 必見 notice（順序可略異） |
|-----|---------------------------|
| **A Scenario 2** | ① `::notice title=Bridge Smoke Scenario 2::… Smoke A deps gate probe` · ② `::notice title=Bridge Smoke Skipped::… venv not built` |
| **B Scenario 2** | ① `::notice title=Bridge Smoke Scenario 2::… Smoke B deps gate probe` · ② `::notice title=Bridge Smoke B skipped::reason=gov_core_system directory missing` |

**Step exit code**：各 smoke step **0** · **無** `Bridge Smoke A/B passed` · **無** unittest 執行 · **無** artifact upload（skip 路徑）。

**異常**：若見 `::warning … unexpected` 或 step exit **1** → **不要** append Progress 為 pass；記錄 run URL · 本票 STATE **`blocked`** · 開 follow-up 給 Implementer。

#### 3. 證據留存（建議）

- 保存 **workflow run URL**（Progress 必填）。
- 可選：各 Scenario 2 job log 中兩行 notice 的 **screenshot** 或 **copy-paste 片段**（貼 B_REPORT · 不必上傳 artifact）。
- 可選：記 `GITHUB_RUN_ID` / dispatch 時間（UTC 或本地 · 與 Progress 日期一致即可）。

#### 4. Progress append

於 `04_Workflows/00_Agent_Work_Progress.md` **末尾 append**（**不改寫**歷史 Wave-D / Wave-H+1 段落）— 使用下方模板。

### Progress 模板（append 用 · 複製後填值）

```markdown
## YYYY-MM-DD · P8.5 · Scenario 2 GA 實跑 · WH-P85-SMOKE-B-scenario2-ops-run-v1

**角色**：ops / Scribe · **票**：WH-P85-SMOKE-B-scenario2-ops-run-v1 · **上游**：WH-P85-SMOKE-B-scenario2-v1（validated）

| 項 | 值 |
|----|-----|
| Workflow | **P85 Bridge Smoke CI (advisory)** · `.github/workflows/bridge-smoke.yml` |
| Trigger | `workflow_dispatch` · **scenario = scenario2** · branch `<branch>` |
| Run | **completed** · run_id=`<run_id>` · URL `<workflow_run_url>` |

| Job id | 結果 | skip / notice 摘要 |
|--------|------|-------------------|
| `p85-bridge-smoke-a-scenario2` | success · step exit **0** | design-skip notice ✅ · deps-gate `Bridge Smoke Skipped` ✅ · `skip_reason=gov_core_system directory missing` |
| `p85-bridge-smoke-b-scenario2` | success · step exit **0** | design-skip notice ✅ · `Bridge Smoke B skipped::reason=gov_core_system directory missing` ✅ |

**性質**：兩 job **`continue-on-error: true`** · **advisory / non-blocking / 非 required check** · skip **by design**（非 CI bug）。

**一句話**：Scenario 2 deps-gate skip 探針 GA 實跑與 `WH-P85-SMOKE-B-scenario2-v1` 預期一致 · 補 AC-1 / AC-3 實證。
```

**單行摘要（可併入表上或戰報）**：

`YYYY-MM-DD · P8.5 · Scenario 2 GA 實跑 · run_id=<run_id> · design-skip notice + deps-gate notice 皆如預期 · exit 0 · non-blocking · 票 WH-P85-SMOKE-B-scenario2-ops-run-v1`

**Progress 最小欄位（不可缺）**：**日期** · **wave/線**（P8.5） · **票號**（本票 + 上游 scenario2 票） · **run_id / run URL** · **兩 Scenario 2 job 狀態** · **design-skip + deps-gate notice 是否如預期** · **non-blocking 註明** · **一句話結論**。

### allowed_paths（執行票）

- `04_Workflows/00_Agent_Work_Progress.md`（**末尾 append only** · Scenario 2 條目）
- `04_Workflows/tickets/WH-P85-SMOKE-B-scenario2-ops-run-v1_state.md`（本檔 B_REPORT / STATE）
- `04_Workflows/tickets/WH-P85-SMOKE-B-scenario2-v1_state.md`（**可選** · STATE notes 一行 cross-ref）

### blocked_paths

- `.github/workflows/bridge-smoke.yml`
- `docs/phase8_5-bridge-smoke-runbook-v1.md`
- 所有 `*.py` · `gov_core_system/**`
- 其它 `04_Workflows/tickets/**`（除上列可選 cross-ref）
- Progress **歷史段改寫**（僅 append）

### acceptance_criteria（本票完成條件）

- **AC-1**：至少一次 GA **`scenario=scenario2`** dispatch · run **completed** · 證據含 **run URL** + **run id**。
- **AC-2**：兩 job `p85-bridge-smoke-a-scenario2` / `p85-bridge-smoke-b-scenario2` log 含 **design-skip notice** + **deps-gate skip notice** · step **exit 0** · Scenario 1 jobs **未跑**。
- **AC-3**：Progress 末尾已 append Scenario 2 條目（符合上方模板 · 最小欄位齊全）。
- **AC-4**：本票 B_REPORT 含 run 摘要 + AC checklist · **overall_status: done**。
- **AC-5**：零 workflow / test / runbook diff（本票 scope 外檔案無變更）。

### 上游 cross-ref

| 票 / 資產 | 關係 |
|-----------|------|
| **`WH-P85-SMOKE-B-scenario2-v1`** | 設計 / wiring **`validated`** · 本票補 GA log + Progress |
| **`WH-P85-CI-LAND-v1`** | B_REPORT §5 Scenario 1/2 Progress 模板 · 首跑 checklist 格式 |
| **`WH-P85-SMOKE-B-advisory-v1`** | Scenario 1 **本機 smoke validated**（非遠端 GA pass）· AC-3 gap 來源 |
| **`docs/phase8_5-bridge-smoke-runbook-v1.md` §0.3** | Scenario 2 表 · 預期 log 文案 SSOT |

---

## STATE

- **overall_status**: done
- **current_owner**: scribe
- **next_action**: 無 · GA 證據已回填（run_id=29157178993）· Reviewer 可抽查 Scenario2 log
- **last_updated**: 2026-07-11 · H3 Scribe（尚書省本人 dispatch + 副官代填）
- **ga_run**:
  - run_url: https://github.com/g234134/workflow-connect/actions/runs/29157178993
  - run_id: "29157178993"
  - scenario: scenario2
  - event: workflow_dispatch
  - conclusion: success
  - jobs: a-scenario2=success · b-scenario2=success · S1 A/B skipped
- **notes**:
  - ≠ required CI · ≠ prod browser · bridge 仍 in-memory stub
  - 2026-06-24 blocked 歷史保留於下方 B_REPORT 原段
- **status_by_role**:
  - **Orchestrator (A)**: done
  - **Implementer / ops (B)**: done — 尚書省本人 `gh workflow run` · 2026-07-11
  - **Reviewer (C)**: pending — 可抽查 Scenario2 job log
  - **Scribe (D)**: done — Progress + EVD-GR-P85-S2 + 本 STATE

---

## B_REPORT (Implementer / ops)

> **2026-07-11 H3**：`status=done` · run_id=`29157178993` · Scenario2 PASS。 下方保留 2026-06-24 blocked 審計段。


- **purpose**: GA 手動 dispatch `scenario=scenario2`，補 AC-1/AC-3 實證 log + Progress append；對齊 FRAME ops checklist 與 runbook §0.3。
- **status**: blocked
- **agent_round**: 2026-06-24 · P8.5 Scenario2 GA 推進代理（本 chat）· Step 0 UI/API 複檢 OK · dispatch **401** · **GA 未執行** · **未改 Progress**
- **changed_files**:
  - `04_Workflows/tickets/WH-P85-SMOKE-B-scenario2-ops-run-v1_state.md` — B_REPORT / C_REPORT / D_REPORT / STATE 收口（本輪唯一 diff）
- **not_changed**: `.github/workflows/bridge-smoke.yml` · tests · runbook · `00_Agent_Work_Progress.md` · 其它票（符合 AC-5 預期）

### Step 0 · workflow 狀態複檢（2026-06-24 · P8.5 Scenario2 GA 推進代理 · 本 chat）

| 項 | 值 |
|----|-----|
| **workflow 可見** | **是** — GitHub API `GET /repos/g234134/workflow-connect/actions/workflows/301057708` → **P85 Bridge Smoke CI (advisory)** · path `.github/workflows/bridge-smoke.yml` · state **active** |
| **`origin/main` 有檔** | **是** — `git fetch origin main` + `git ls-tree origin/main .github/workflows/` 含 `bridge-smoke.yml` |
| **`workflow_dispatch`** | **是** — 遠端 YAML 含 `scenario` choice input（`default` / `scenario2`）· Scenario 2 jobs 條件 `github.event.inputs.scenario == 'scenario2'` |
| **Run workflow（UI）** | **預期可用** — workflow **active** · dispatch input 已定義；需具 repo **Actions read/write**（本 agent 無 UI 登入 · 無 token · 無法代點） |
| **既有 runs** | **0** — `GET …/workflows/301057708/runs` → `total_count=0`（尚無 default / scenario2 / schedule / PR 觸發紀錄） |
| **dispatch 嘗試** | **401 Unauthorized** — `POST …/dispatches` · `ref=main` · `inputs.scenario=scenario2` · 無 `GITHUB_TOKEN` / `GH_TOKEN` · 無 `gh` CLI |

### GA 執行結果（2026-06-24 · P8.5 Scenario2 GA 推進代理 · 本 chat）

| 項 | 值 |
|----|-----|
| **GA 是否執行** | **否** — **Scenario2 GA 尚未跑** |
| **阻塞原因** | workflow **已 landing** · advisory CI **存在且可 `Run workflow`（UI）** · 但本 agent **無權限 dispatch**（401）· **需要具權限的 human / ops 在 Actions UI 上手動跑 `scenario=scenario2`** · 完成後回填 run_id/URL 與 job log |
| **CI-LAND 狀態** | **已完成** — workflow 已 on `origin/main` 且 API **active**（CI 已 landing，待 GA run） |
| **操作者** | Cursor agent（P8.5 Scenario2 GA 實跑代理）· 2026-06-24 |
| **本機探针（非 GA）** | Git Bash 執行 Scenario 2 job A/B bash 本體 · `GITHUB_RUN_ID=999999` · 兩 script **exit 0** · design-skip + deps-gate skip notice 語意與 runbook §0.3 一致 |

### 操作者必做（GA 實跑 · CI-LAND 已完成）

| 步 | 動作 |
|----|------|
| 1 | GitHub → **Actions** → **P85 Bridge Smoke CI (advisory)** → **Run workflow** |
| 2 | **Use workflow from**：含 Scenario 2 wiring 的 branch（通常 **`main`**） |
| 3 | **scenario** 下拉：選 **`scenario2`**（**勿**選 `default`） |
| 4 | Run 完成後驗收：workflow **completed** · **僅**兩 job `p85-bridge-smoke-a-scenario2` / `p85-bridge-smoke-b-scenario2` · Scenario 1 jobs **不跑** |
| 5 | 逐 job log 確認 design-skip notice + deps-gate skip notice · step **exit 0** · 無 `Bridge Smoke A/B passed` |
| 6 | **人工**於 `04_Workflows/00_Agent_Work_Progress.md` **P8.5 段末尾 append**（見下方 Progress 指引） |
| 7 | 回填下方 **ga_run** / **job_results** / **progress_append** · 將 **STATE.overall_status → `done`** |

**異常**：若見 `::warning … unexpected` 或 step exit **1** → 勿 append Progress 為 pass · STATE → **`blocked`** · 開 follow-up。

### §0 dry-run 预检（设计步 · 本代理未跑 GA）

> 在 Actions dispatch 前，操作者可本地对照 `docs/phase8_5-bridge-smoke-runbook-v1.md` §0.3 Scenario 2 表，确认 workflow 输入与 job id 无误：

| 预检项 | 预期 |
|--------|------|
| Workflow 名 | **P85 Bridge Smoke CI (advisory)** |
| dispatch input | **`scenario=scenario2`**（非 `default`） |
| 将跑的 jobs | 仅 `p85-bridge-smoke-a-scenario2` · `p85-bridge-smoke-b-scenario2` |
| Scenario 1 jobs | **不跑** / skipped |
| 每 job log（设计） | design-skip `::notice` + deps-gate skip `::notice` · step exit **0** |
| 不应出现 | `Bridge Smoke A/B passed` · unittest 执行 · artifact upload |

**本预检不构成 GA 证据**；AC-1–AC-3 仍以真实 workflow run URL + Progress append 为准。

### 操作者必填欄位（回填本 B_REPORT）

| # | 欄位 | 說明 |
|---|------|------|
| 1 | **run_url** | GitHub Actions workflow run 完整 URL |
| 2 | **run_id** | Run id（URL 末段數字或 UI 顯示） |
| 3 | **branch** | dispatch 所用 branch（例 `main`） |
| 4 | **dispatch_input** | 固定 `workflow_dispatch` + **`scenario=scenario2`** |
| 5 | **job_a_scenario2** | `p85-bridge-smoke-a-scenario2`：**success** · step exit **0** · design-skip notice ✅ · deps-gate `Bridge Smoke Skipped` ✅ |
| 6 | **job_b_scenario2** | `p85-bridge-smoke-b-scenario2`：**success** · step exit **0** · design-skip notice ✅ · `Bridge Smoke B skipped::reason=gov_core_system directory missing` ✅ |
| 7 | **progress_append** | Progress 條目日期 + 標題（append 完成後填） |

- **ga_run**:
  - **run_url**: **N/A — GA 未執行**（無 GitHub 認證 · dispatch 未觸發）
  - **run_id**: **N/A**
  - **branch**: **`main`**（workflow 已 on `origin/main` · dispatch 待具權限操作者）
  - **dispatch_input**: `workflow_dispatch` · **scenario=scenario2**（**未 dispatch**）
- **job_results**:
  - **p85-bridge-smoke-a-scenario2**: **N/A（GA 未跑）** · 本機 bash 探针 exit **0** · 預期 design-skip `Bridge Smoke Scenario 2` + deps-gate `Bridge Smoke Skipped`
  - **p85-bridge-smoke-b-scenario2**: **N/A（GA 未跑）** · 本機 bash 探针 exit **0** · 預期 design-skip + `Bridge Smoke B skipped::reason=gov_core_system directory missing`
  - **scenario1_jobs_ran**: **N/A**（預期 GA 下 **false**）
- **progress_append**: **未 append**（AC-3 待 GA pass 後依 FRAME 模板）

### Progress append 指引（操作者人工 · 本輪代理未改 Progress）

於 `04_Workflows/00_Agent_Work_Progress.md` **末尾 append**（不改寫 Wave-H+1 Scenario 1 段落）— 複製 FRAME「Progress 模板」填值，**最小欄位不可缺**：

- **日期** / **wave**（P8.5） / **票號**（`WH-P85-SMOKE-B-scenario2-ops-run-v1` + 上游 `WH-P85-SMOKE-B-scenario2-v1`）
- **run_id** / **run URL**
- **trigger** = `workflow_dispatch` + **`scenario=scenario2`** + **branch**
- 兩 Scenario 2 job **status**（success · step exit **0**）
- **design-skip notice** / **deps-gate skip notice** 是否如預期（各 job 兩行 notice）
- **non-blocking** 註明（`continue-on-error: true` · 非 required check）
- **一句話結論**（與 `WH-P85-SMOKE-B-scenario2-v1` 預期一致）

**收口條件**：Progress append 完成 + 上方欄位回填後 → **STATE.overall_status: `done`** · B_REPORT **status: done** · AC-1–AC-4 全 ✅。

### AC checklist

- **AC-1 ❌**: GA **`scenario=scenario2`** dispatch **未執行** — CI-LAND 已 landing · 但本環境無 token · 無 run URL / run id
- **AC-2 ❌**: GA job log **未收錄** · 本機 bash 探针 exit 0 與 notice 語意一致（**非 GA 證據**）
- **AC-3 ❌**: Progress Scenario 2 pass 條目 **未 append**（待 GA 後）
- **AC-4 ⏳**: B_REPORT / D_REPORT 已回填 Step 0 + 阻塞證據（本 chat）· STATE **`blocked`**（待 human GA + Progress 後升 **`done`**）
- **AC-5 ✅**: 零 workflow / test / runbook / Progress diff（本輪僅本票 `_state.md`）

---

## C_REPORT (Reviewer)

- **verdict**: pending
- **review_date**: 2026-06-24
- **core**: CI-LAND **已解除**（workflow id 301057708 · active on `main` · `workflow_dispatch` + **`scenario2`** input 已確認）；**Scenario2 GA 仍 blocked** — 本 chat dispatch **401** · **0** runs · 需 human/ops UI 手動跑並回填 run URL。
- **notes**:
  - Step 0 複檢：API 確認 workflow 存在 · `workflow_dispatch` + `scenario` input · **0** prior runs。
  - B_REPORT 誠實標記 GA 未執行 · 本機 bash 探针 exit 0——**不足以**關 AC-1/AC-2 empirical。
  - 待具權限操作者 UI/`gh` dispatch `scenario=scenario2` → Progress append 後再審。
  - 若 GA pass 且兩 Scenario 2 job log 符合 FRAME（design-skip notice + deps-gate skip notice · step exit 0 · Scenario 1 jobs 未跑），verdict 傾向 **`accepted_with_gaps`**（見 gaps）。
- **gaps**:
  - **GA dispatch 缺口**：需具 **Actions read/write** 之 human/ops 於 UI 或 `gh workflow run` 觸發；本 agent 環境 **401**。
  - **bridge in-memory stub**：即便未來 GA 通過，bridge 仍非 production 持久化/outbox PG 能力。
  - **非 production browser**：Smoke C 仍 manual；Scenario 2 僅探针 `missing_dir` reason（`fastapi` / import-failed 分支未 GA 實跑）。
  - **doc vs remote**：Scenario 1 GA pass 若無 run_id/URL 留痕，ops-run GA 完成後應一併澄清 Progress 證據鏈。
- **AC_recheck**（待 GA 後）:
  - **AC-1 ⏳**: 待真實 `scenario=scenario2` dispatch + run URL + run id
  - **AC-2 ⏳**: 待兩 job GA log 驗收
  - **AC-3 ⏳**: Progress append 未做
  - **AC-4 ⏳**: B_REPORT 阻塞證據已齊；待 GA 後升 **done**
  - **AC-5 ✅**: 零 workflow / test / runbook diff（本輪 scope 外）

---

## D_REPORT (Scribe)

- **status**: blocked
- **scribe_date**: 2026-06-24
- **notes**: GA **仍 blocked** · Progress Scenario 2 pass 條目 **未 append** · **CI 已 landing** · **Scenario2 GA 未跑**（`total_count=0` runs）。

### 為何 blocked（一句話 · 本 chat 收口）

**workflow 已 landing** — Actions 可見 **P85 Bridge Smoke CI (advisory)**（id **301057708** · **active**）· `workflow_dispatch` **含 `scenario2` 參數** · `origin/main` 已含 `bridge-smoke.yml`。  
**Scenario2 GA 仍 blocked** — 本 agent 環境 **無 GitHub token / 無 `gh` CLI** · API dispatch → **401** · 尚無任何 workflow run URL。  
**解除阻塞**：需要具 **Actions read/write** 權限的 **human / ops** 在 GitHub Actions UI 手動 **Run workflow** · branch **`main`** · **`scenario=scenario2`** → 驗兩 job log → append Progress → 回填 B_REPORT → **overall_status → `done`**。  
**禁止宣稱**：無 run URL 不得說 Scenario2 GA pass · advisory · stub · 非 prod browser · 非 required CI（維持 non-claims）。

### 解除阻塞之前置條件

| # | 前置條件 | 負責方 | 完成信號 | 狀態 |
|---|----------|--------|----------|------|
| 1 | **`bridge-smoke.yml` landing** — on `main` | **`WH-P85-CI-LAND-bridge-smoke-push-v1`** | Actions **P85 Bridge Smoke CI (advisory)** · id 301057708 · commit `99bf1f590` | **✅ 2026-06-24 已完成（push 票）** |
| 2 | **Repo Actions 權限** — 允許 `workflow_dispatch`；操作者有 Write 或 Actions read/write | repo admin / human ops | UI 可見 **Run workflow** 按鈕 · 可選 **`scenario2`** | **⏳ 待具權限 human**（API 已證 workflow active · input 存在 · 本 agent 401） |
| 3 | **GA 真跑** — UI 或 `gh`/API + token dispatch · `scenario=scenario2` · branch=`main` | ops / oncall | run **completed** · run URL + run id | **❌ 未執行**（`total_count=0` · dispatch 401） |
| 4 | **log 驗收** — 僅 `p85-bridge-smoke-a-scenario2` / `p85-bridge-smoke-b-scenario2` · design-skip + deps-gate notice · exit 0 | ops | B_REPORT job 欄位回填 | **❌ 待 #3** |
| 5 | **Progress append** — FRAME 模板 · P8.5 段末尾 | Scribe / ops | AC-3 ✅ | **❌ 待 #3** |
| 6 | **Reviewer 收口** — C_REPORT 對照 AC-1/AC-2 | Reviewer | verdict → **`accepted_with_gaps`** | **⏳ 待 #3–#5** |

### 建議下一步（不限定執行者）

#### A. CI-LAND push 票 — `WH-P85-CI-LAND-bridge-smoke-push-v1` — **✅ 已完成（2026-06-24）**

- workflow 已 on `origin/main` · commit `99bf1f590` · Actions **P85 Bridge Smoke CI (advisory)** · id 301057708 · state **active**。
- **不再阻塞**本票；現阻塞為 **GA run 未 dispatch**（见下方 B）。

#### B. ops-run GA 真跑（本票解阻主路徑 · **当前阻塞**）

1. GitHub → **Actions** → **P85 Bridge Smoke CI (advisory)** → **Run workflow**
2. **Use workflow from**：`main`
3. **scenario**：選 **`scenario2`**（勿選 `default`）
4. Run **completed** 後驗兩 Scenario 2 job log（FRAME §2 表）
5. append Progress（FRAME Progress 模板）
6. 回填 B_REPORT `ga_run` / `job_results` / `progress_append`
7. **STATE.overall_status → `done`**

**異常路徑**：step exit 1 或 unexpected warning → 勿 append pass · STATE 維持 **`blocked`** · 開 Implementer follow-up。

### blocked → done 路徑

```
blocked
  → [CI-LAND push] workflow on main          ✅ 2026-06-24
  → [ops GA dispatch scenario2] run URL + id  ← **當前阻塞**（需 human/token · 本 chat 401）
  → [log 驗收] AC-1/AC-2
  → [Progress append] AC-3
  → [B_REPORT 回填] AC-4
  → overall_status: done
  → [C_REPORT] accepted_with_gaps（bridge stub · 非 prod browser · Scenario2 僅 missing_dir）
```

### 阻塞上游

| 票 id | 關係 |
|-------|------|
| **`WH-P85-CI-LAND-bridge-smoke-push-v1`** | **resolved** — workflow landing 已完成 |
| **`WH-P85-CI-LAND-v1`** | checklist SSOT · 首跑 git 步驟模板 |

### 下游（GA 完成後）

| 票 id | 關係 |
|-------|------|
| **`WH-P85-SMOKE-B-scenario2-v1`** | 可選 STATE notes：AC-1 empirical closed |
| **`WH-P85-wave-H2-closure-scribe-v1`** | wave-H+2 批次收口 |
| **`WH-P85-bridge-run-record-jsonl-v1`** · **`WH-P85-bridge-fixture-dom-port-v1`** | bridge non-stub · 可並行 |

### progress_append

- **未 append**（AC-3 待 GA pass 後依 FRAME 模板）
