# GA-remote Closure Checklist v1 — Human Operations Playbook

> **角色**：Groundwork Finisher B · Governance / GA-remote  
> **性质**：**doc-only** · 人类操作 checklist · **不**执行 GA dispatch · **不**修改 workflow yml  
> **Tier SSOT**：`docs/evidence-tier-contract-v1.md` · `docs/p8_p89_evidence_index_v1.md` §1–§2  
> **现状（2026-06-26）**：**全线 GA-remote 仍 pending / blocked** — 本档 **不得** 写「已完成」

---

## 0. 使用说明

### 0.1 读者与 RACI

| 角色 | 职责 |
|------|------|
| **Ops / Platform（执行）** | GitHub Actions `workflow_dispatch` · 复制 run URL / run id · 上传 artifact 摘要 |
| **Security / Infra（前置）** | P7 Round-2 五顶前置 · staging endpoint · POST 审查（**非** GA dispatch 本身） |
| **尚書省 / 治理委员会（审批）** | governance_dual 真批文 · Round-2 解阻 · closure sign-off |
| **Scribe（记录）** | Progress **末尾 append** · 票 STATE B_REPORT 回填 · **禁止** 覆盖历史段 |
| **Reviewer（验收）** | 对照本 checklist + evidence index · 无 `run_url` **不得** GA-remote verdict |
| **AI / Implementer（禁止项）** | **不得** dispatch GA · **不得** 预填假 URL · **不得** 宣称 GA pass / Phase 收口 |

### 0.2 全局 Non-Claims

| 声明 | 状态 |
|------|------|
| **CI-advisory landing**（yml on `origin/main`）= GA-remote pass | **否** |
| **L-local** N/N OK = 远端 validated | **否** |
| GA-remote completed = **required CI** / merge gate | **否** |
| GA-remote completed = **prod-ready** / INT Tier-A | **否** |
| 本 checklist 就绪 = Phase% 上调 | **否** |

### 0.3 Batch 1 GA-remote 授权（2026-06-27 · observation-only · 执行仍 pending）

> **裁決 SSOT**：Progress 末尾「2026-06-27 Governance Decisions — Batch 1」· `ga_authorized_observation_only`

Batch 1（尚書省）已将以下三条 GA-remote **授权**为 **single-run · observation-only · non-gate**：

| 裁決 ID | Phase | Workflow | 授权范围 | 执行状态 |
|---------|-------|----------|----------|----------|
| **GOV-GA-P85-S2-01** | P8.5 | `bridge-smoke.yml` · `scenario=scenario2` | 回填 EVD-GR-P85-S2 · tier=`GA-remote` | **PASS** · run_id=`29157178993` · Scenario2 A/B success |
| **GOV-GA-P9-PAY-01** | P9 | `p9-payment-sandbox-smoke.yml` | sandbox-only · prod provider **仍 blocked** | **PASS（二次）** · run_id=`29159159265` · fixtures+happy-path+unit |
| **GOV-GA-P7-ADV-01** | P7 | `p7-notification-smoke.yml` | advisory GA · **non-merge-gate** | **DISPATCHED（二次）** · run_id=`29159219044` · **job FAIL** · 51 ran / **11 AssertionError**（非缺檔）· continue-on-error → run-level success |

**Ops 状态**：

- Batch-1：**授权** observation-only · 当时未 dispatch。
- Batch-2（2026-07-10）：排程 07-11。
- **Decision confirm（2026-07-11）**：尚書省 **A1=GO**。
- **H1 首跑**：P85 PASS · P9/P7/P6 缺資產／`core` → H3 已記 RED／FAIL。
- **資產 landing + 二次 dispatch（2026-07-11）**：P9 **PASS** `29159159265` · P6 **PASS** `29159219832`（112/112 · 綠日鐘 DAY1）· P7 **功能性 FAIL** `29159219044`（另票修 AssertionError）。
- **≠** required CI · **≠** Phase 收口 · **≠** Round-2 GO · P7 **≠** functional GA pass · P6 **≠** 83→91。
### 0.4 GA-remote 最低证据栏位（全 Phase 通用）

引用 `docs/p8_p89_evidence_index_v1.md` §2.3 · **不得自造键名**：

```yaml
ga_run:
  evidence_tier: GA-remote
  evidence_kind: ga_remote_dispatch | ci_advisory_run
  workflow_file: .github/workflows/<name>.yml
  run_url: "<必填 · GitHub Actions run 页面 URL>"
  run_id: "<必填 · numeric>"
  branch: main
  jobs:
    - job_id: <string>
      conclusion: success | failure | skipped
      log_excerpt: "<one-line>"
  artifact_names: []   # 若有
  non_claims:
    - advisory ≠ merge gate
    - GA pass ≠ prod-ready
```

**回填位置（三处同步）**：

1. 对应票 `*_state.md` → B_REPORT `ga_run` 或 `<RUN_URL>` 占位替换  
2. `04_Workflows/00_Agent_Work_Progress.md` → **末尾 append**  
3. （P8.5）`docs/p8_p89_evidence_index_v1.md` §2.3 对应 EVD-GR-* 行 — 由 Scribe / Governance 授权更新

---

## 1. P7 · Round-2 Staging · Advisory CI

> **索引 SSOT**：`docs/P7_ADVISORY_CI_INDEX.md`  
> **关键区分**：P7 有两条 **不同** 的人类证据线 — **(A) advisory CI GA-remote** 与 **(B) Round-2 staging execute**（human-env-only，**非** GitHub GA）。

### 1.1 P7 Advisory CI — GA-remote 首跑（可选 · 观测用）

| 项 | 值 |
|----|-----|
| **Workflow** | `.github/workflows/p7-notification-smoke.yml` |
| **Actions 名** | P7 notification smoke (advisory) |
| **Job id** | `p7-notification-smoke` |
| **触发** | `workflow_dispatch` · `pull_request` · cron |
| **blocking** | **non-gate** · `continue-on-error: true` |
| **SSOT 票** | `W2-P7-advisory-ci-ssot-index-v1` · upstream `WD-P7-T3-orchestrator-dispatch-full-smoke-v1` |
| **现况** | GA-remote **recorded** · run_id=`29159219044` · **job FAIL**（11 AssertionError · 非缺檔）· 另票 `W2-P7-ADV-assertion-fix-v1` · **≠** functional pass |

#### Human-only 步骤

1. GitHub → Actions → **P7 notification smoke (advisory)** → Run workflow（from `main`）。
2. 等待 job **completed**（失败亦 **不** 阻 merge — 记录真实 conclusion）。
3. 复制 **run_url** · **run_id**。
4. 检查 log：localhost mock `:8080` · sandbox-only · **无** `TIER=staging/prod`。
5. 下载 artifact `p7-notification-smoke-<run_id>`（若有）· 摘要 `p7_notification_smoke.log`。

#### 必备 evidence 项

| # | 栏位 | 必填 |
|---|------|------|
| E1 | `run_url` + `run_id` | 是 |
| E2 | job `conclusion` | 是 |
| E3 | unittest 模块 exit 摘要（5/5 · 7/7 · 12/12 或实际计数） | 是 |
| E4 | `non_claims`：advisory · ≠ Round-2 GO | 是 |
| E5 | artifact 名 / retention | 若有则填 |

#### 角色

| 动作 | 负责 |
|------|------|
| dispatch | Ops |
| 验收 log 语义 | Reviewer |
| Progress append | Scribe |
| required CI 升格 | **禁止** — 见 G8 · `WH-P7-PROD-prod-rollout-governance-bootstrap-v1` |

#### AI 禁止

- 宣称 advisory CI 绿 = **Round-2 execute GO**
- 将 localhost mock run 写成 **客户 staging endpoint** 物证
- 自行开启 branch protection / required check

---

### 1.2 P7 Round-2 Staging Execute — Human-env（**非** GA-remote tier）

> **SSOT 票**：`WH-P7-NOTIF-staging-integration-execute-v2` · **status：`blocked`**  
> **Runbook**：`04_Workflows/tickets/WH-P7-PROD-staging-smoke-runbook-v1_state.md` B_REPORT  
> **Tier**：`human_env_only` — **不用** `ga_run` YAML；用 **staging execute 物证**

#### 五顶前置（全部 human/infra/security · **未齐则不得 execute**）

| # | 前置 | 负责 | 交付物 |
|---|------|------|--------|
| P-1 | **governance_dual 真批文**（≠ Round-1 simulated） | 尚書省 / Wave-H | 批文 ID · Progress 引用 |
| P-2 | **Infra staging slot / HTTPS endpoint** | Infra | endpoint URL（实例锚点 · 不写死进 doc 正文） |
| P-3 | **Security 外部 POST sign-off** | Security | 审查记录 |
| P-4 | **客户 staging allowlist**（non-prod） | PM + Security | allowlist 配置物证 |
| P-5 | **receiver 部署至 staging slot** | Infra / Ops | 部署确认 |

#### Round-2 执行 checklist（前置齐后）

| # | 步骤 | evidence 项 |
|---|------|---------------|
| R1 | 分配新 **run_id**（≠ `20260623T165252Z` Round-1） | run_id 字符串 |
| R2 | 依 runbook 执行 **S1–S4**（shadow/enforce · POST · retry/DLQ） | 逐步 log 路径 |
| R3 | 记录 **48h 观测窗口** 启动时间（DLQ · 失败 POST · 重试） | 窗口起止 · 指标快照 |
| R4 | execute 票 B_REPORT + Progress append | `evidence_tier: human_env`（非 GA-remote） |
| R5 | Reviewer 对照 `WH-P7-NOTIF-staging-integration-execute-v2` AC | C_REPORT |

#### 必备 evidence 项（staging · 非 GA）

| 栏位 | 说明 |
|------|------|
| `run_id` | 人类分配 · 可审计 |
| `tier` | `staging` · explicit non-prod |
| `governance_dual_approval_id` | 真批文引用 |
| `endpoint_class` | infra_staging · **≠** localhost · **≠** prod |
| `s1_s4_log_paths` | 或 redacted excerpt |
| `48h_observation` | scheduled / in_progress / completed |

#### AI 禁止

- 在 P-1–P-5 未齐时写「staging 集成已完成」
- 将 Round-1 local slot（`20260623T165252Z`）冒充 Round-2
- 用 `p7-notification-smoke` GA run 替代 staging POST 物证

---

## 2. P8.5 · Scenario1 / Scenario2 · Bridge GA-remote

> **Runbook**：`docs/internal/P85_Scenario2_GA_runbook.md` · `docs/phase8_5-bridge-smoke-runbook-v1.md`  
> **Ops 票**：`WH-P85-SMOKE-B-scenario2-ops-run-v1` · **blocked** · `total_count=0` runs  
> **Closure 票**：`WH-P85-wave-H2-closure-scribe-v1` · **blocked**（hard = Scenario2 GA evidence）

### 2.1 Workflow 路径

| 项 | 值 |
|----|-----|
| **Workflow** | `.github/workflows/bridge-smoke.yml` |
| **Actions 名** | P85 Bridge Smoke CI (advisory) |
| **Input** | `scenario`: `default` \| `scenario2` |
| **Jobs（Scenario1）** | `p85-bridge-smoke-a` · `p85-bridge-smoke-b` |
| **Jobs（Scenario2）** | `p85-bridge-smoke-a-scenario2` · `p85-bridge-smoke-b-scenario2` |
| **blocking** | **non-gate** · `continue-on-error: true` |
| **L-local 基线** | EVD-LL-P85-A/B · **14/14 · 7/7**（**≠** GA） |

### 2.2 EVD-GR-P85-S1 · Scenario1 远端 GA（pending）

| # | Human-only 步骤 |
|---|----------------|
| 1 | Actions → **P85 Bridge Smoke CI (advisory)** → Run workflow · **`scenario=default`** |
| 2 | 等待 A+B jobs **completed** |
| 3 | 记录 run_url · run_id · 各 job conclusion |
| 4 | 回填 index **EVD-GR-P85-S1** · Progress append |

**必备 evidence**：`ga_run` 全套 · scenario=`default` · job log 含 unittest 摘要

### 2.3 EVD-GR-P85-S2 · Scenario2 远端 GA（**recorded 2026-07-11**）

| # | Human-only 步骤 |
|---|----------------|
| 1 | **勿选** `default` — 必须 **`scenario=scenario2`** |
| 2 | CLI 等价：`gh workflow run bridge-smoke.yml --ref main -f scenario=scenario2` |
| 3 | 验收：**仅** scenario2 jobs 运行 · 含 design-skip + deps-gate skip notice · **exit 0** |
| 4 | 回填 ops-run 票 B_REPORT `ga_run` · Progress · 触发 closure-scribe 重跑 |

**本輪實錄（GOV-GA-P85-S2-01）**：

```yaml
ga_run:
  evidence_tier: GA-remote
  evidence_kind: ga_remote_dispatch
  workflow_file: .github/workflows/bridge-smoke.yml
  scenario: scenario2
  run_url: "https://github.com/g234134/workflow-connect/actions/runs/29157178993"
  run_id: "29157178993"
  branch: main
  event: workflow_dispatch
  conclusion: success
  jobs:
    - job_id: p85-bridge-smoke-a-scenario2
      conclusion: success
    - job_id: p85-bridge-smoke-b-scenario2
      conclusion: success
    - job_id: p85-bridge-smoke-a
      conclusion: skipped
    - job_id: p85-bridge-smoke-b
      conclusion: skipped
  non_claims:
    - advisory ≠ merge gate
    - GA pass ≠ prod browser / bridge prod-ready
```

**失败处理**：step exit 1 或 unexpected failure → **维持** ops-run `blocked` · **勿** append pass

### 2.4 角色与 AI 禁止

| 动作 | 负责 |
|------|------|
| Scenario2 dispatch | Ops（human） |
| log 验收 | Reviewer |
| closure-scribe 解阻 | Scribe + Orchestrator（**后** GA 证据齐） |
| Phase% 上调 | Governance 独占 · **本 checklist 不授权** |

**AI 禁止**：本机 bash 探针填入 `ga_run` · 无 URL 写「Scenario2 GA pass」· 宣称 prod browser ready

---

## 3. P9 · Payment Sandbox CI · Fixture Execute GA-remote

> **Runbook**：`docs/internal/P9_payment_sandbox_CI_runbook.md`  
> **CI 票**：`WH-P9-CI-payment-sandbox-smoke-v1` · B_REPORT run_url **已回填（二次 PASS）**  
> **现况**：L-local **21/21** · e2e PAID OK · **GA-remote PASS** `29159159265` · **≠** prod provider

### 3.1 EVD · Payment sandbox smoke 首跑

| 项 | 值 |
|----|-----|
| **Workflow** | `.github/workflows/p9-payment-sandbox-smoke.yml` |
| **Actions 名** | P9 payment sandbox smoke (advisory) |
| **Job scope** | `GOV_PAYMENT_SANDBOX_ENABLED=1` · sandbox-only |
| **Local 对照** | `run_wc_m2_e2e_walkthrough.py` · `--include-payment` · `order_status=PAID` |
| **GA-remote（二次）** | run_id=`29159159265` · [run URL](https://github.com/g234134/workflow-connect/actions/runs/29159159265) · **success** · 2026-07-11 |

#### Human-only 步骤

1. 确认 `main` 已含 yml（landing ✅ · 2026-06-24 叙事）。
2. Actions → **P9 payment sandbox smoke (advisory)** → Run workflow（from `main`）。
3. 等待 **completed** · 复制 run_url · run_id。
4. 验证 log/summary：`walkthrough_ok` · `order_status=PAID` 语义。
5. 替换 CI 票 B_REPORT placeholder · Progress append（用 runbook §模板）。

#### 必备 evidence 项

| # | 栏位 |
|---|------|
| E1 | `run_url` · `run_id` |
| E2 | job conclusion |
| E3 | walkthrough JSON 摘要（redacted） |
| E4 | `non_claims`：sandbox · ≠ prod provider/ledger · ≠ INT Tier-A · ≠ required CI |

### 3.2 EVD · WC-M2 fixture execute advisory 首跑（cross-ref）

| 项 | 值 |
|----|-----|
| **Workflow** | `.github/workflows/p9-wc-m2-fixture-execute.yml` |
| **性质** | advisory · non-blocking |
| **现况** | landing · **GA-remote pending**（若需首跑 · 同 §0.4 模板） |
| **SSOT** | Wave 4 `W4-P9-CI-*` · `WH-P9-M2-INT` cross-ref |

**Human-only**：dispatch → run_url → Progress · **禁止** 宣称 prod 金流

### 3.3 P9 prod 升格（**不在 GA-remote checklist 范围**）

prod provider / ledger · INT Tier-A · required CI 升格 → 另开 governance 票 · **须尚书省批文** · 见 `docs/required-ci-and-wc-pre-checklist-v1.md`

---

## 4. P8 / P8.9 · Delivery OBS · Webhook 远端证据

> **Tier 索引**：`docs/p8_p89_evidence_index_v1.md`  
> **OBS contract**（trace 字段）：`p8_p89_delivery_observability_contract_v1.md`（待建/full index 引用）  
> **现况**：P8/P8.9 主链 **无** 独立 advisory GA workflow · release sanity = **L-local**（EVD-LL-P89-*）

### 4.1 L-local 基线（已 landing · 非 GA-remote）

| ID | 命令 | 用途 |
|----|------|------|
| EVD-LL-P89-MP | `run_multi_phase_smoke_v1.py` | 七步 cross-phase smoke |
| EVD-LL-P89-BND | `run_p8_9_verification_bundle_v1.py` | P8.9 verification bundle |
| EVD-LL-P89-CI | `run_ci_smoke_check_v1.py` | local release sanity |
| EVD-LL-P89-MC | `run_multi_case_smoke_v1.py` | fleet smoke |

**AI 禁止**：将七步全绿写成 **HTTP webhook prod** 或 **INT real provider** 就绪

### 4.2 P8.9 HTTP Webhook · 远端证据（T4 deferred · 规划位）

| 项 | 说明 |
|----|------|
| **票** | P8.9-T4 HTTP webhook · **deferred** |
| **Tier（未来）** | 真 staging/prod webhook 投递 → **human_env** 或 **GA-remote**（若走 Actions 探针） |
| **现况** | local dispatch registry only · **无** 远端 webhook ACK 物证要求 |

#### 未来 human checklist（T4 解阻后启用）

| # | 步骤 |
|---|------|
| W1 | staging webhook endpoint provision（Infra + Security） |
| W2 | 测试 payload 投递 · 记录 `trace_id` · `ack_status` · HTTP status |
| W3 | audit quickview `workflow_notifications` 对照 |
| W4 | Progress append · **non_claims**：≠ prod SLA |

### 4.3 P8 Operator / Backlog 远端（只读 HTTP · 非 GA）

| 项 | 说明 |
|----|------|
| **能力** | `GET /operator/backlog` · read-only |
| **证据** | L-local curl / integration test · **非** GA-remote |
| **deferred** | batch approve · resume-latest · prod operator UI |

### 4.4 Cross-line GA 汇总表（2026-06-26 快照）

| EVD ID | Phase | Workflow / 路径 | 现况 | Ops runbook |
|--------|-------|-----------------|------|-------------|
| EVD-GR-P85-S1 | P8.5 | `bridge-smoke.yml` · default | **pending** | §2.2 |
| EVD-GR-P85-S2 | P8.5 | `bridge-smoke.yml` · scenario2 | **recorded PASS** · `29157178993` | `docs/internal/P85_Scenario2_GA_runbook.md` |
| P7 advisory GA | P7 | `p7-notification-smoke.yml` | **recorded · job FAIL** · `29159219044` · 11 AssertionError · 另票 | §1.1 |
| P7 Round-2 | P7 | human-env staging | **blocked**（五頂 · earliest 07-18） | §1.2 |
| P9 payment GA | P9 | `p9-payment-sandbox-smoke.yml` | **recorded PASS** · `29159159265` | `docs/internal/P9_payment_sandbox_CI_runbook.md` |
| P9 fixture GA | P9 | `p9-wc-m2-fixture-execute.yml` | **pending** | §3.2 |
| P8.9 webhook | P8.9 | T4 deferred | **n/a** | §4.2 |

---

## 5. Phase 收口前置 · GA-remote 维度

**GA-remote 全线完成**（治理叙事用 · **≠** Phase 100%）需至少：

| # | 条件 | 现况（2026-06-26） |
|---|------|-------------------|
| G1 | P8.5 **EVD-GR-P85-S2** run_url 回填 + ops-run 非 blocked | **满足（evidence）** · `29157178993` · 仍 ≠ Phase closure |
| G2 | P9 payment sandbox **首跑** run_url 回填 | **满足（二次 PASS）** · `29159159265` · 仍 ≠ prod provider |
| G3 | （建议）P8.5 Scenario1 **EVD-GR-P85-S1** run_url | **未满足** |
| G4 | P7 Round-2 staging execute（**独立**于 GA · §1.2） | **blocked** |
| G5 | Reviewer 无 over-claim · inspector §3.3 通过 | **partial** · P7 functional FAIL 另票 |
| G6 | **不**自动触发 Phase% / master_status 变更 | Governance 独占 |

**即使 G1–G2 满足**：仍 **≠** prod-ready · **≠** required CI · bridge stub / prod payment gap 仍在 · P7 advisory **≠** functional pass。

---

## 6. 相关索引

| 类型 | 路径 |
|------|------|
| Evidence tier contract | `docs/evidence-tier-contract-v1.md` |
| P8/P8.9 evidence index | `docs/p8_p89_evidence_index_v1.md` |
| P7 advisory index | `docs/P7_ADVISORY_CI_INDEX.md` |
| Required CI checklist | `docs/required-ci-and-wc-pre-checklist-v1.md` |
| Phase closure playbook | `docs/phase-closure-governance-playbook-v1.md` |
| Dashboard（Phase% SSOT） | `docs/WAVE_PROGRESS_DASHBOARD.md` |
| Inspector | `04_Workflows/review_checklists/wave-next-code-inspector-v1.md` §3.2–3.3 |

---

*ga-remote-closure-checklist-v1 · 2026-06-27 · Groundwork Finisher B + Governance Scribe Batch 1 · doc-only · Batch-1 三条 GA 已授权 · 执行仍 pending*
