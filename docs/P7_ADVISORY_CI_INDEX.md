# P7 · Advisory CI SSOT Index (v1)

> **Ticket**: `W2-P7-advisory-ci-ssot-index-v1` · **Wave 2** · **doc-only**  
> **Authority**: P7 線 GitHub Actions advisory CI 與相關 smoke 路徑的**誠實索引**；**不**改 workflow 行為 · **不**升格 branch protection。

---

## Non-claims（必讀）

| 聲明 | 狀態 |
|------|------|
| 本索引所列 **GitHub Actions workflow** 均為 **advisory · non-gate · non-prod** | **是** |
| `p7-notification-smoke` 已升格 **required check / merge gate** | **否**（bootstrap **G8** 仍 `open`） |
| advisory CI 綠燈 = P7 **Round-2 execute GO** | **否**（Round-2 仍 **`blocked`** · 五顶 human 前置） |
| advisory CI = **staging S1–S4 物证** 或 **客户 staging endpoint** 就緒 | **否**（CI 僅 `127.0.0.1:8080` localhost mock · sandbox-only） |
| advisory CI = **prod 閉環** / prod-ready | **否** |
| 本索引就緒 = Phase% 上調 | **否**（Dashboard Phase% **未變**） |

**分線**：P8 / P8.9 advisory CI（`bridge-smoke.yml` 等）歸 **Wave 3** `W3-P8-ADV-advisory-ci-ssot-index-v1`；**本檔僅 P7**。

---

## 索引摘要

| 類型 | 數量 | 說明 |
|------|------|------|
| **GitHub Actions · advisory CI** | **1** | `p7-notification-smoke.yml` |
| **Human-env-only smoke** | **1** | staging S1–S4 手動 runbook（**非 CI**） |
| **Local unittest smoke 模組** | **3** | advisory CI 內跑 · 亦可本機單跑 |
| **Governance · required CI 升格模板** | **1** | bootstrap **G8**（**仍 default advisory · open**） |

---

## 1. GitHub Actions · advisory CI

| 欄位 | 值 |
|------|-----|
| **檔案路徑** | `.github/workflows/p7-notification-smoke.yml` |
| **Actions 顯示名** | P7 notification smoke (advisory) |
| **Job id** | `p7-notification-smoke` |
| **用途** | P7 orchestrator 通知全鏈 **unittest smoke**：emit → gateway → dispatch → **localhost webhook mock**（`:8080`） |
| **ci_class** | `advisory` |
| **blocking** | **non-gate** · job `continue-on-error: true` · **≠ branch protection required check** |
| **環境** | **sandbox-only** · `GOV_NOTIFICATION_WEBHOOK_URL=http://127.0.0.1:8080/webhook` · **禁止** `TIER=staging/prod` |
| **觸發條件** | `pull_request`（path filter：workflow 自身 · `delivery/notification_*.py` · handlers YAML · experiment script · 三 unittest 模組 · `cases/**`）· `schedule` cron `0 4 * * *`（UTC 每日 advisory）· `workflow_dispatch` |
| **結果類型** | unittest exit code（**失敗不阻 merge**）· `::warning` on failure · artifact `p7-notification-smoke-<run_id>`（`p7_notification_smoke.log` · 14 天） |
| **預設 env 缺口** | CI **預設無** retry / HMAC prod env（見 `WH-P7-sandbox-line-wrapup-v1`） |
| **upstream 票** | `WD-P7-T3-orchestrator-dispatch-full-smoke-v1` AC-7 · Wave-G |
| **required 升格 SSOT** | `WH-P7-PROD-prod-rollout-governance-bootstrap-v1` **G8**（`open`） |

**advisory / non-gate / non-prod**：本 workflow **僅** observability 回歸；**不**參與 merge 裁決 · **不**替代 staging execute-v2 物证。

### Advisory GA-remote Ops Instructions（GOV-GA-P7-ADV-01）

> **Governance Batch 1 授权**：`GOV-GA-P7-ADV-01` · advisory GA · **non-merge-gate** · single-run · observation-only。  
> **执行者**：**human Ops only** — AI / 自动化 **禁止** dispatch 或预填 run URL。  
> **性质**：本次 GA **仅** observability 观测；**不会**升格为 branch protection required check · bootstrap **G8** 仍 **`open`**。

#### 进入 Actions 路径

1. GitHub → 本 repo → **Actions** 标签页。
2. 左侧 workflow 列表选择 **P7 notification smoke (advisory)**。
3. 右侧点击 **Run workflow**。

#### Workflow 名称 / branch / 参数

| 项 | 值 |
|----|-----|
| **Workflow 显示名** | **P7 notification smoke (advisory)** |
| **Workflow 文件** | `.github/workflows/p7-notification-smoke.yml` |
| **Use workflow from** | **`main`**（或含 workflow yml 之 branch） |
| **workflow_dispatch inputs** | 无额外必填 input（直接 **Run workflow**） |
| **环境** | sandbox-only · `GOV_NOTIFICATION_WEBHOOK_URL=http://127.0.0.1:8080/webhook` · **禁止** `TIER=staging/prod` |

#### 成功 / 失败观测指标

| 观测项 | 成功信号 | 失败信号 |
|--------|----------|----------|
| **Workflow run** | 状态 **completed**（advisory · 不阻 merge） | run **failure**（job 仍 `continue-on-error: true` · **不阻 merge**） |
| **Job** | `p7-notification-smoke` **success** | job **failure** · 查 log |
| **Log / unittest** | 三 smoke 模组 unittest pass · step exit **0** | unittest fail · `::warning` on failure |
| **Artifact** | 可选 `p7-notification-smoke-<run_id>`（`p7_notification_smoke.log`） | 无 artifact 或 log 异常 |

#### 复制 run_url / run_id

- **run_url**：Actions run 页面浏览器地址栏完整 URL。
- **run_id**：URL 末段数字，或 UI「Run #」后的 numeric id。
- 回填：本节下方占位栏位 · `WH-P7-sandbox-line-wrapup-v1` / Progress **末尾 append**（Scribe）。

#### GA-remote 证据占位（Ops 回填）

```yaml
ga_remote_run_url: "https://github.com/g234134/workflow-connect/actions/runs/29171873118"
ga_remote_run_id: "29171873118"
ga_remote_event: workflow_dispatch
ga_remote_recorded_at: "2026-07-12"
ga_remote_run_conclusion: success
ga_remote_job_conclusion: success   # unittest Ran 51 · OK（post assertion-fix）
ga_remote_summary: "Ran 51 · OK · commit 3dd2a9c68 · W2-P7-ADV-assertion-fix-v1 AC-5 PASS"
ga_remote_baseline_fail_run_id: "29159219044"  # pre-fix · 51/11 AssertionError
```

#### Assertion-fix 狀態（`W2-P7-ADV-assertion-fix-v1` · 2026-07-12）

| 項 | 狀態 |
|----|------|
| 本機三模組 | **Ran 51 · OK**（含 stub + 模擬 job-level `GOV_NOTIFICATION_*=1`） |
| 修復摘要 | 缺 cleaning CLI 時 stub；移除 job-level `GOV_NOTIFICATION_*`；disable 測試顯式清 env |
| 遠端 re-dispatch | **PASS** · run_id=`29171873118` · job success · Ran 51 · OK |
| ticket overall | **done** |

#### non-claims（本 runbook 重申）

- GA pass **≠** required CI **≠** prod-ready **≠** Phase closure **≠** P7 Round-2 GO。
- advisory CI 绿灯 **≠** staging S1–S4 物证 **≠** Round-2 execute 解阻 · bootstrap **G8** 仍 **`open`**。
- stub **≠** 真實 cleaning CLI 已入遠端／真實 cleaning GA。
- 本 runbook **仅** human Ops 观测用；**不代表** gate 升级 · `continue-on-error: true` 不变。

---

## 2. Human-env-only · staging smoke（非 CI）

| 欄位 | 值 |
|------|-----|
| **SSOT** | `04_Workflows/tickets/WH-P7-PROD-staging-smoke-runbook-v1_state.md` B_REPORT（S1–S4 正文） |
| **用途** | staging tier **人工 env** 上 S1–S4 shadow/enforce 演練 · URL / HMAC / retry / DLQ gate |
| **ci_class** | `human_env_only` |
| **blocking** | **non-gate** · **無** GitHub workflow · **禁止**在 CI 設 `TIER=staging/prod` |
| **觸發條件** | human / ops 依 runbook 手動 flip env + 執行步驟（**前置**：governance · Infra endpoint · Security · allowlist · receiver） |
| **結果類型** | 人工 log / Progress 物证 · execute 票 `WH-P7-NOTIF-staging-integration-execute-v2`（**`blocked`**） |
| **與 advisory CI 關係** | **互補 · 不可替代**：Round-2 物证走本 runbook + execute 票；`p7-notification-smoke` **仍 sandbox advisory** |

**advisory / non-gate / non-prod**：本路徑 **≠** GitHub CI · **≠** prod rollout · Round-2 **未完成**時僅 design / local slot 物证可引用。

---

## 3. Local unittest smoke 模組（advisory CI 子集 · 本機可單跑）

| 模組 | 用途 | 典型結果 | ci_class |
|------|------|----------|----------|
| `tests.test_orchestrator_dispatch_full_smoke_v1` | 全鏈 integration smoke | unittest pass/fail · **5/5** 基線 | `local_smoke` · consumed by advisory CI |
| `tests.test_orchestrator_notifications` | orchestrator emit / gateway | unittest pass/fail · **7/7** 基線 | 同上 |
| `tests.test_notification_webhook_dispatch_v1` | webhook adapter / sandbox dispatch | unittest pass/fail · **12/12** 基線 | 同上 |

**本機驗證（戰車根 cwd）**：

```bash
python -m unittest tests.test_orchestrator_dispatch_full_smoke_v1 tests.test_orchestrator_notifications tests.test_notification_webhook_dispatch_v1 -v
```

**advisory / non-gate / non-prod**：本機全綠 **≠** staging POST 物证 · **≠** required CI · **≠** prod enablement。

---

## 4. Governance · required CI 升格模板（G8 · 非 workflow）

| 欄位 | 值 |
|------|-----|
| **SSOT** | `04_Workflows/tickets/WH-P7-PROD-prod-rollout-governance-bootstrap-v1_state.md` · **G8** |
| **current_status** | **`open`** — `p7-notification-smoke` 仍 **advisory · non-blocking** |
| **用途** | 定義 future **required check** 升格證據模板（G1–G8）；**default 仍 advisory** |
| **ci_class** | `governance_template` |
| **blocking** | **non-gate**（模板就緒 **≠** 已升格） |
| **觸發條件** | 尚書省 prod rollout 批文 + Wave-P7-6 獨立 CI governance 票（例：`WH-P7-NOTIF-ci-required-v1` 候選） |
| **結果類型** | 批文 ID · branch protection 設定物证（**尚未存在**） |

---

## 5. Cross-wave 對照（僅索引 · 非 P7 SSOT 正文）

| Workflow | Phase | P7 索引 |
|----------|-------|---------|
| `bridge-smoke.yml` | P8.5 | **不在此檔** → Wave 3 `W3-P8-ADV` |
| `p9-wc-m2-fixture-execute.yml` | P9 | **不在此檔** |
| `p9-payment-sandbox-smoke.yml` | P9 | **不在此檔** |

Wave-G 全局短表仍見 `00_Agent_Work_Progress.md`「Wave-G advisory CI」段 · Dashboard 腳注。

---

## 6. Observability · 如何驗證 advisory 性質

### verify_commands

```bash
# 索引 SSOT 存在且含 P7 advisory 敘事
rg "P7 advisory|advisory / non-gate / non-prod" docs/P7_ADVISORY_CI_INDEX.md

# workflow 仍 non-blocking · localhost mock（不應出現 branch protection required 設定）
rg "continue-on-error|127\\.0\\.0\\.1" .github/workflows/p7-*.yml
rg "required" .github/workflows/p7-*.yml

# G8 仍 open / advisory default
rg "G8|advisory|required CI" 04_Workflows/tickets/WH-P7-PROD-prod-rollout-governance-bootstrap-v1_state.md

# WORKFLOW_INDEX 與 Dashboard 敘事 cross-ref（無 Phase% 數字變更）
rg -i "advisory|continue-on-error|non-blocking|P7_ADVISORY_CI_INDEX" 04_Workflows/WORKFLOW_INDEX.md docs/WAVE_PROGRESS_DASHBOARD.md
```

### trace / grep 路徑

| 要確認什麼 | 去哪裡 |
|------------|--------|
| P7 advisory workflow 清單 | **本檔 §1** · `04_Workflows/WORKFLOW_INDEX.md` §1.45 |
| `continue-on-error` / mock host | `.github/workflows/p7-notification-smoke.yml` |
| Round-2 blocked vs CI 綠燈 | `docs/WAVE_PROGRESS_DASHBOARD.md` Wave-next 敘事 · `WH-P7-NOTIF-staging-integration-execute-v2_state.md` |
| required CI 能否升格 | bootstrap **G8** · `WH-P7-NOTIF-PROD-policy-v1` |
| over-claim 攔截 | `04_Workflows/review_checklists/wave-next-code-inspector-v1.md` §3.2 |
| 票施工狀態 | `04_Workflows/tickets/W2-P7-advisory-ci-ssot-index-v1_state.md` |

### success_signals

- 本檔 + WORKFLOW_INDEX §1.45 均標 **advisory / human_env / governance_template**
- `p7-*.yml` 含 `continue-on-error: true` · **無** `required: true` 或 branch protection 語意
- bootstrap **G8** = `open`
- Dashboard P7 敘事含 Round-2 **`blocked`** 與 advisory 並列 · **Phase% 未改**

### failure_signals

- 任一條目寫「merge gate / required check 已就緒」但無 G8 物证
- 宣稱 advisory CI 綠 = staging S1–S4 完成
- `rg "required" .github/workflows/p7-*.yml` 命中 **branch protection / required check** 升格（現況應 **零** 或僅註解「not required」）

---

## 7. Related STATE 索引

| 票 | 角色 |
|----|------|
| `W2-P7-advisory-ci-ssot-index-v1_state.md` | 本索引施工票 |
| `WH-P7-sandbox-line-wrapup-v1_state.md` | sandbox 線封箱 · advisory CI 形狀 |
| `WH-P7-PROD-prod-rollout-governance-bootstrap-v1_state.md` | G8 required CI 升格模板 |
| `WH-P7-NOTIF-staging-integration-execute-v2_state.md` | Round-2 execute（**blocked**） |
| `WH-REV-2026-06-P7-P8_5-P9-alignment-checklist-v1_state.md` | Global #3/#4 advisory 口徑 |

---

*Last updated: 2026-06-26 · Implementer · W2-P7-advisory-ci-ssot-index-v1*
