# WH-P9-CI-payment-sandbox-smoke-v1 — Ticket State

> handoff 摘要檔；P9 **sandbox payment happy-path advisory CI** 施工票 · non-blocking。  
> 目的：新增 advisory CI workflow 跑 `WC-DEMO-1` sandbox payment happy-path（DRAFT→PAID）；**≠ required check · ≠ INT · ≠ prod**。

---

## META

| 欄位 | 值 |
|------|-----|
| **Phase** | P9 |
| **Lane** | Wave-G · advisory CI |
| **Parent wave** | Wave-P9 · payment sandbox follow-up |
| **Owner** | orchestrator |
| **Ticket type** | CI implement · advisory smoke |

---

## FRAME

### Goal（一行目的）

设计 **advisory · non-blocking** CI job：在 CI 环境跑 `WC-DEMO-1` sandbox payment happy-path（DRAFT→PAID），供回归观测；**≠ required check · ≠ INT Tier-A**。

### 核心 checklist

- [x] FRAME 定义 workflow 名 `p9-payment-sandbox-smoke`、trigger（schedule · workflow_dispatch · PR paths filter）。
- [x] `continue-on-error: true` · 文档明示 **non-blocking · ≠ merge gate**。
- [x] Job 步骤：checkout → Python setup → runner `--execute --use-hitl-fixtures --include-payment` → optional unittest。
- [x] CI env：`GOV_PAYMENT_SANDBOX_ENABLED=1` 仅 job 内 · 禁止读真实 API key。
- [x] paths filter：`run_wc_m2_e2e_walkthrough.py` · `order_ledger/payment_adapter.py` · `run_order_intake.py` · payment tests · runbook §4+。
- [x] 交叉引用：`p9-wc-m2-fixture-execute.yml` 模式 · alignment matrix CI 行 · WC-M3 non-goals。
- [x] 已创建 `.github/workflows/p9-payment-sandbox-smoke.yml`。
- [x] WORKFLOW_INDEX / overview 一句索引（Scribe · 2026-07-13）。

### Non-goals

- ❌ 不升格为 required / merge-blocking check（无尚书省批文）。
- ❌ 不把 CI green 宣称为 INT Tier-A · prod 金流 · manual HITL 验收。
- ❌ 本票不修改现有 `p9-wc-m2-fixture-execute.yml` 行为（可并列 advisory job）。

### GA-remote Ops Instructions（GOV-GA-P9-PAY-01）

> **Governance Batch 1 授权**：`GOV-GA-P9-PAY-01` · sandbox-only · prod payment provider **仍 blocked** · single-run · observation-only · non-gate。  
> **执行者**：**human Ops only** — AI / 自动化 **禁止** dispatch 或预填 run URL。

#### 进入 Actions 路径

1. GitHub → 本 repo → **Actions** 标签页。
2. 左侧 workflow 列表选择 **P9 payment sandbox smoke (advisory)**。
3. 右侧点击 **Run workflow**。

#### Workflow 名称 / branch / 参数

| 项 | 值 |
|----|-----|
| **Workflow 显示名** | **P9 payment sandbox smoke (advisory)** |
| **Workflow 文件** | `.github/workflows/p9-payment-sandbox-smoke.yml` |
| **Use workflow from** | **`main`**（或含 workflow yml 之 branch） |
| **Input: run_unittest** | 默认 **`true`**（可选；不影响 sandbox-only 性质） |
| **环境** | job 内 `GOV_PAYMENT_SANDBOX_ENABLED=1` · mock adapter · `artifacts/e2e/WC-DEMO-1/` |

**sandbox-only 说明**：本 GA **仅**跑 WC-DEMO-1 sandbox payment happy-path（DRAFT→PAID）；**不**触 prod ledger · **不**触真实 payment provider · **≠** INT Tier-A · **≠** manual HITL 验收。

#### 成功 / 失败观测指标

| 观测项 | 成功信号 | 失败信号 |
|--------|----------|----------|
| **Workflow run** | 状态 **completed**（advisory · 不阻 merge） | run **failure**（job 仍可能 `continue-on-error` 不阻 merge） |
| **Job** | `p9-payment-smoke` / `P9 payment sandbox smoke (advisory)` **success** | job **failure** · 查 log |
| **Log / summary** | e2e `ok=true` · `order_status=PAID` · step exit **0** | `::warning` · summary 断言失败 |
| **Artifact** | 可选 `p9_payment_sandbox_smoke_summary.json` | 无 summary 或断言未过 |

#### 复制 run_url / run_id

- **run_url**：Actions run 页面浏览器地址栏完整 URL。
- **run_id**：URL 末段数字，或 UI「Run #」后的 numeric id。
- 回填：本 FRAME 下方占位栏位 · B_REPORT `GitHub 首跑` · Progress **末尾 append**。

#### GA-remote 证据占位（Ops 回填）

```yaml
ga_remote_run_url: <PENDING_TO_BE_FILLED_BY_OPS>
ga_remote_run_id: <PENDING_TO_BE_FILLED_BY_OPS>
```

#### non-claims（本 runbook 重申）

- GA pass **≠** required CI **≠** prod-ready **≠** Phase closure **≠** P7 Round-2 GO。
- sandbox CI green **≠** prod 金流 **≠** 真 payment provider **≠** INT Tier-A。
- 本 runbook **仅** human Ops 观测用；**不代表** gate 升级 · advisory `continue-on-error: true` 不变。

---

### AllowedPaths

- `04_Workflows/tickets/WH-P9-CI-payment-sandbox-smoke-v1_state.md`（本票 FRAME / STATE / B/C/D）
- `.github/workflows/p9-payment-sandbox-smoke.yml`（advisory CI · 已创建）
- `04_Workflows/WORKFLOW_INDEX.md`（索引 · Scribe 待补）
- `docs/wave_c/overview.md`（一句 · Scribe 待补）
- `04_Workflows/00_Agent_Work_Progress.md`（**末尾 append only**）

### Acceptance Criteria

- **AC-1**：FRAME 含完整 job 步骤草案 · trigger · paths · env gate 说明。
- **AC-2**：non-claims 明示 advisory · non-blocking · ≠ INT · ≠ prod。
- **AC-3**：depends_on runner step 6 或等价 manual CLI 链已定义；施工前可标 frame_ready。

---

## STATE

- **overall_status**: `done_with_gaps`
- **current_owner**: none
- **next_action**: 索引 gap 已補 · 剩餘 gap=prod provider／ledger（另票）· ≠ Phase%／required CI
- **last_updated**: 2026-07-13 · Scribe 索引補洞
- **wave**: Wave-P9 · payment sandbox CI smoke
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-24 开 follow-up FRAME
  - **Implementer (B)**: done — 2026-06-24 workflow yml + 本地验证
  - **Reviewer (C)**: pending
  - **Scribe (D)**: done — 2026-07-12 run_url · 2026-07-13 INDEX／overview 一句
- **gaps**:
  - prod provider / ledger 仍 blocked（明示可另票 · ≠ 本票索引）
- **notes**:
  - workflow 已落地；本地 unittest 21/21 OK · e2e `ok=true` · `order_status=PAID`
  - 二次 GA-remote **PASS** · run_id=`29159159265`
  - 2026-07-13：`WORKFLOW_INDEX` §1.46 表列 + `docs/wave_c/overview.md` CI advisory 一句已補

---

## B_REPORT (Implementer)

- **status**: done
- **written_date**: 2026-06-24
- **purpose**: 新增 P9 sandbox payment advisory CI smoke · 仿 Wave-G non-blocking 模式。
- **delivered**:
  - **workflow yml**: `.github/workflows/p9-payment-sandbox-smoke.yml`
  - **job name**: `P9 payment sandbox smoke (advisory)` · `continue-on-error: true`
  - **triggers**: `workflow_dispatch` · `schedule`（`0 7 */2 * *` UTC）· PR paths filter（payment / runner / tests / runbook）
  - **execute command**:
    ```bash
    GOV_PAYMENT_SANDBOX_ENABLED=1 python scripts/run_wc_m2_e2e_walkthrough.py \
      --ticket WC-DEMO-1 \
      --artifacts-root artifacts/e2e \
      --execute \
      --use-hitl-fixtures \
      --include-payment \
      --json
    ```
  - **summary artifact**: `p9_payment_sandbox_smoke_summary.json`（断言 `walkthrough_ok` + `order_status=PAID`；失败仅 `::warning` · step exit 0）
  - **optional unittest**: `tests.test_run_wc_m2_e2e_walkthrough` · `tests.test_payment_sandbox_adapter`
- **local verification**:
  - `python -m unittest tests.test_run_wc_m2_e2e_walkthrough tests.test_payment_sandbox_adapter -v` → **21/21 OK**
  - 上述 e2e 命令（清 `artifacts/e2e/WC-DEMO-1` 后）→ **`ok=true` · `order_status=PAID` · exit 0**
- **GitHub 首跑（二次 PASS · 2026-07-11）**:
  - run_url: `https://github.com/g234134/workflow-connect/actions/runs/29159159265`
  - run_id: `29159159265`
  - conclusion: **success**
  - 首跑失敗紀錄：`29157179910`（fixtures missing · 已由資產 landing 修復）
- **non-claims**:
  - **sandbox-only** · mock adapter · `artifacts/e2e/WC-DEMO-1/`
  - **advisory / non-blocking** · **≠ required check** · **≠ merge gate**
  - **≠ prod 金流** · **≠ 真 payment provider / prod ledger**
  - **≠ INT Tier-A** · **≠ manual HITL 验收**
  - 未改 branch protection · 未改 Phase% · 未改 `p9-wc-m2-fixture-execute.yml`
- **ready for human first dispatch**:
  - workflow yml · 票 STATE/B_REPORT · Progress 末尾增量已对齐；**本地验证完成**（21/21 unittest · e2e `ok=true` · `order_status=PAID`）
  - **human 动作**：merge/push 含 yml 的变更至 `main` → Actions **workflow_dispatch** 手动首跑 → 用真实 run URL 回填 `<RUN_URL>`（**无 URL 不得宣稱 CI 首跑 pass**）
  - **仍 gap**（不阻塞 dispatch）：Scribe 补 `WORKFLOW_INDEX.md` / `docs/wave_c/overview.md` 一句索引 · Reviewer C_REPORT pending

---

## C_REPORT (Reviewer)

- **verdict**: `not_yet_reviewed`
- **review_date**: —
- **core**: P9 sandbox payment 具备 advisory CI 回归观测路径；≠ required · ≠ INT · ≠ prod。
- **AC review**（Implementer 自评 · 待 C 确认）:
  - **AC-1** ✅ workflow yml 含完整 job 步骤 · trigger · paths · env gate
  - **AC-2** ✅ non-claims 明示 advisory · non-blocking · ≠ INT · ≠ prod
  - **AC-3** ✅ depends_on runner `--include-payment` step 6 已可用；本地 e2e PAID 证据
- **gaps**: WORKFLOW_INDEX / overview 索引已補（2026-07-13）；prod provider 仍另票。

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-07-12
- **ga_remote_backfill**:
  - run_id=`29159159265` · PASS · sandbox fixtures + happy-path + unit
  - non_claims：≠ prod provider · ≠ required CI · ≠ Phase%
- **depends_on**:
  - `WH-P9-PROD-payment-happy-path-execute-v1`（happy-path 命令 SSOT）
  - `WH-P9-M2-runner-step6-payment-v1`（runner `--include-payment` step 6 已交付）
  - `WH-P9-PROD-payment-sandbox-adapter-v1`
  - `p9-wc-m2-fixture-execute`（Wave-G 模式参考）
- **scribe_todo**:
  - [x] 首跑／二次 `run_url` 回填 B_REPORT / Progress / checklist
  - [x] `WORKFLOW_INDEX.md` 加 `p9-payment-sandbox-smoke` 一句索引（2026-07-13 §1.46）
  - [x] `docs/wave_c/overview.md` advisory CI 一句（2026-07-13）
