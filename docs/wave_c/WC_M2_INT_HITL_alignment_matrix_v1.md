# WC M2 · INT / HITL / Fixture 對齊矩陣 v1

> **性質**：**設計 SSOT**（doc-only · FRAME）；**非**實作票、**非** merge gate 授權。  
> **票號**：`WH-P9-M2-INT-alignment-v1`  
> **版本**：v1.1 · 2026-06-24（DOCSYNC · sandbox payment `--include-payment` 口徑同步）  
> **權威位階**：WC-T5 `wc.m2.*` path_id 與 `automation_tier` 以 [`WC_T5_automation_coverage_contract.md`](WC_T5_automation_coverage_contract.md) 為準；INT Tier-A/B 以 [`docs/phase6-int-regression-gate-contract-v1.md`](../phase6-int-regression-gate-contract-v1.md) 與 [`04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md`](../../04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md) 為準；E2E 命令以 [`WC_T7_e2e_walkthrough_runbook.md`](WC_T7_e2e_walkthrough_runbook.md) v0.3 為準。

**本檔回答**：WC M2 walkthrough 每一步在 **dry-run / manual HITL / fixture execute** 三模式下如何驗證；與 **INT Tier-A / Tier-B / PR smoke** 的關係；以及 **pass 的誠實語意**（demo 链 vs 裝配不變量 vs 模組回歸）。

---

## 1. 範圍與非目標

### 1.1 本檔是什麼

| 項 | 說明 |
|----|------|
| **定位** | Wave-C Control Plane M2 與 Wave 6–8 INT gate 的 **逐步對齊設計 SSOT** |
| **讀者** | Orchestrator · Reviewer · Scribe · Multi-Chat 驗收角色 |
| **交付** | 主矩陣 · 三模式總表 · 三軌 gate 語意 · HITL 決策樹 · 下游實作票草案 |

### 1.2 本檔不是什麼

- **不是**實作票：不改 `run_wc_m2_e2e_walkthrough.py`、tests、CI workflow。
- **不是** INT contract 正文：Tier-A/B 定義 **引用** INT SSOT，不重寫。
- **不是** merge gate 批文：fixture execute CI 綠燈 **不** 自動升格為 required check 或 INT pass。
- **不是** production HITL gate：demo skeleton（`WC-DEMO-*` · `artifacts/e2e/`）**默认** `order_status: DRAFT`；加 **`--include-payment`** 可 sandbox 至 **PAID**（**≠ prod 金流**）。

---

## 2. 三模式總表（runner 執行路徑）

> 詳細命令見 WC-T7 runbook 檔頭「執行路徑分工」與 §6.3 / §6.5。

| 模式 | 命令要點 | 適用場景 | 觸及 live `*_state.md` | HITL | 產物範圍 | pass 語意（誠實） |
|------|----------|----------|------------------------|------|----------|-------------------|
| **Dry-run 编排骨架** | `--dry-run` | 本地預覽 §0–§5 命令；CI 無 deps 時 smoke | **否**（runner 不寫 live STATE） | 打印 HITL 提示 | 可建空 `artifacts/e2e/<ticket>/`；**不**写 comms / `orders.jsonl` | **编排预览 pass**：步骤命令可打印；**不**证明业务链闭环 |
| **Manual HITL walkthrough** | `--execute`（默认） | M2/M3 **真人验收**主路径 | **是**（人工编辑 live STATE §1/§3/§4） | **必须** | `artifacts/e2e/<ticket>/` + 依赖 live state 的 comms / order | **Control Plane demo E2E pass**（manual）：真人 HITL + CLI 链在 demo 票上可串联；**≠ INT Tier-A** |
| **Demo fixture execute** | `--execute --use-hitl-fixtures`（可选 **`--include-payment`**） | 本地无 HITL 烟测；CI advisory（Wave-G `p9-wc-m2-fixture-execute`） | **否**（fixture materialize 至 artifact 副本 only） | 跳过 | **仅** `artifacts/e2e/<ticket>/` 内 comms + `orders.jsonl` + materialized 快照 | **Demo fixture execute pass**：step 3/4 自动化 smoke OK；加 **`--include-payment`** 时 step `6-payment` 可 sandbox 至 **PAID**；**≠ production HITL gate** · **≠ INT Tier-A** · **≠ prod 金流** |

**关键区分（AC-3 可勾选）**

- [ ] Manual HITL 是 **唯一** 触及 live `04_Workflows/tickets/*_state.md` 的 walkthrough 路径。
- [ ] `--use-hitl-fixtures` **不** 移除 manual HITL runbook；仅供 CI advisory / 本地无 HITL 烟测。
- [ ] `p9-wc-m2-fixture-execute` 为 **non-blocking**（`continue-on-error: true`）；pass **不** 代表 INT Tier-A 或 production HITL gate。
- [ ] M2 fixture execute **默认** `order_status` 仅到 **DRAFT**；加 **`--include-payment`** 可 sandbox 一鍵至 **PAID**（`step_id=6-payment` · WC-DEMO-* · mock adapter）。**non-claims**：**≠ prod 金流** · **≠ INT Tier-A** · **≠ required CI**。完整状态机见 [`WC_M3_payment_closure_scope_v1.md`](WC_M3_payment_closure_scope_v1.md)。

---

## 3. HITL 模式决策树

```
改动类型 / 验收目的
│
├─ 只想预览步骤命令、零业务档？
│   └─► Dry-run（--dry-run）
│
├─ M2/M3 真人验收 / 须写 live STATE / Orchestrator 裁决？
│   └─► Manual HITL（--execute，手工编辑 §1/§3/§4）
│
├─ CI advisory / 本地无 HITL / 只验证 comms+order 自动化？
│   └─► Fixture execute（--execute --use-hitl-fixtures）
│       ⚠ 仍 demo skeleton；绿灯 ≠ INT pass
│       可选 --include-payment → sandbox DRAFT→PAID（≠ prod 金流）
│
└─ 改 Wave 6/7/8 装配（envelope/manifest/QA/orch/runner）？
    └─► mandatory INT Tier-A（与 M2 E2E 互补，不可互相替代）
```

| 决策问题 | Dry-run | Manual HITL | Fixture execute |
|----------|---------|-------------|-----------------|
| 需要 live STATE 编辑？ | 否 | **是** | 否 |
| 需要 comms JSONL 产出？ | 否 | 是（§3 完成后） | 是（P9-T2 自动化） |
| 需要 `orders.jsonl`？ | 否 | 是（§4 完成后） | 是（P9-T2 自动化） |
| 可作为 M2/M3 签收依据？ | 否 | **是**（主路径） | **否**（仅 smoke / advisory） |
| 可作为 INT Tier-A 依据？ | 否 | **否** | **否** |

---

## 4. INT tier 栏位定义（本票 SSOT）

| 值 | 含义 |
|----|------|
| `N/A` | 该步骤不在 INT gate 覆盖范围（Control Plane CLI 链） |
| `A-indirect` | 不直接测该步骤；若改动触及 Wave 6/7/8 装配，**mandatory** 跑 `python 04_Workflows/_wave7_regression_gate.py --tier A` |
| `A-direct` | INT Tier-A 模块 **直接** 守该域不变量（M2 逐步罕见；见矩阵末「改 Wave 6/7/8 装配」行） |
| `B` | pre-release 建议 `--tier B`（Wave 8 orch 集成等） |
| `PR-smoke-only` | 仅 `core-agent-smoke.yml` / `eval-gate-ci.yml` 部分覆盖；**明示 ≠ INT Tier-A** |

**职责分离（重申）**

1. **Control Plane E2E pass ≠ INT pass**：跑通 M2 walkthrough 不证明 Wave 6/7 装配未退化。
2. **INT Tier-A pass ≠ Control Plane E2E pass**：INT 不覆盖 dispatch cards / comms JSONL / order ledger 链。
3. **Fixture execute pass ≠ INT pass ≠ Manual HITL pass**：三者验证域不同，见 §2 与主矩阵 `pass_means` 列。

---

## 5. 主矩阵（逐步对齐）

> **覆盖下限**：runbook §0–§5 每一步至少一行；WC-T5 附录表 A 关键 `wc.m2.state.write_ticket` 三处 **100% 有对应行**；runner CI 行单独列出。

| step | step_summary | wc_m2.path_id | automation_tier | demo_fixture | real_HITL_required | INT_tier | recommended_verification | pass_means |
|------|--------------|---------------|-------------------|--------------|-------------------|----------|--------------------------|------------|
| §0 / `0` | 环境与隔离目录 | — | auto | partial（dry-run 可 mkdir 空目录） | no | N/A | `python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --dry-run --json`（step 0 ok） | 目录在 `artifacts/e2e/` 下且未污染默认 outbox/ledger |
| §1 setup | 手工创建初始 STATE（implementer 可接单态） | `wc.m2.state.write_ticket` | forbidden | none（fixture 不写 live） | **yes**（M2 验收） | N/A | runbook §1：复制 `_templates/ticket_state.template.md` → `04_Workflows/tickets/<ticket_id>_state.md` 并填 FRAME/STATE | live demo 票 STATE 为 implementer 可接单态；**仅 manual HITL 路径** |
| §1 预检 | eligibility implementer 预检 | `wc.m2.eligibility.check_role` | auto | full | no | N/A · PR-smoke-only | `python scripts/run_ticket_eligibility.py --ticket WC-DEMO-1 --requested-role implementer --format json` | JSON `eligible: true`（或项目惯用等价键）；模块回归 pass，**非 INT** |
| §2 | dispatch cards + eligibility gate | `wc.m2.dispatch.refresh_and_cards` | auto | full | conditional（gate 拦截时须 Orchestrator 留痕） | N/A | `python scripts/run_dispatch_cards.py --refresh-plan --ticket WC-DEMO-1 --role implementer --eligibility-gate block --out-dir artifacts/e2e/WC-DEMO-1/cards/ --json-summary artifacts/e2e/WC-DEMO-1/dispatch_cards_run.json --pretty` | `cards_generated >= 1`；summary 无 `eligibility_blocked`（STATE 满足 gate 时） |
| §2 override | Orchestrator 一次性 `--force-eligibility` | `wc.m2.dispatch.force_eligibility_override` | HITL | partial（dry-run 可预览） | **conditional**（须 Orchestrator 留痕） | N/A | `python scripts/run_dispatch_cards.py --refresh-plan --ticket WC-DEMO-1 --role implementer --eligibility-gate block --force-eligibility --out-dir artifacts/e2e/WC-DEMO-1/cards/ --pretty` | 强制 override 后写卡成功；战报/STATE 有 override 留痕 |
| §2 dry-run | dispatch dry-run 对照 | `wc.m2.dispatch.refresh_and_cards` | auto | full | no | N/A | `python scripts/run_dispatch_cards.py --refresh-plan --ticket WC-DEMO-1 --role implementer --eligibility-gate block --dry-run --pretty` | summary 可解释 `eligibility_blocked` 原因；不写卡 |
| §3-hitl | 手工编辑 STATE → review/reviewer | `wc.m2.state.write_ticket` | forbidden | partial（fixture 仅 artifact 副本 `state_review.md`） | **yes** | N/A | runbook §3 step 2：手工编辑 live `*_state.md` STATE 字段 | live STATE 为 reviewer 关口；fixture **不**替代此步的 M2 验收 |
| §3 | before/after → comms JSONL | `wc.m2.comms.state_transition` | auto | **full**（P9-T2 三档 fixture 之 comms 链） | no | N/A | `python scripts/run_ticket_state_update_with_comms.py --before artifacts/e2e/WC-DEMO-1/before_review.md --after <after-path> --outbox-dir artifacts/e2e/WC-DEMO-1/comms`（manual 用 live state；fixture 用 materialized 路径） | stdout `ok: true` · `sent: true`；JSONL 新增 `ticket_comms_v0.1` 行 |
| §3 dry-run | comms dry-run | `wc.m2.comms.state_transition_dry_run` | auto | full | no | N/A | `python scripts/run_ticket_state_update_with_comms.py --before artifacts/e2e/WC-DEMO-1/before_review.md --after <after-path> --dry-run` | payload 预览 OK；不写 JSONL |
| §4-hitl | 手工编辑 STATE → ready_for_order | `wc.m2.state.write_ticket` | forbidden | partial（fixture 仅 `state_ready_for_order.md` 副本） | **yes** | N/A | runbook §4 step 1：手工编辑 live STATE `next_action` 含 `ready_for_order` | live STATE 开单就绪；fixture **不**替代 M2 验收 |
| §4 create | order create（隔离 JSONL） | `wc.m2.order.create` | auto | **full**（P9-T2） | no | N/A | `python scripts/run_order_intake.py --jsonl-path artifacts/e2e/WC-DEMO-1/orders.jsonl create --ticket WC-DEMO-1 --amount-minor 10000 --currency TWD --ticket-path <ticket-path>` | `ok: true` · `message: order_created` · `order_id` 为 `ORD-<ticket_id>` |
| §4 lookup | order lookup | `wc.m2.order.lookup` | auto | full | no | N/A | `python scripts/run_order_intake.py --jsonl-path artifacts/e2e/WC-DEMO-1/orders.jsonl lookup --ticket-id WC-DEMO-1` | 返回与 create 相同 order 记录 |
| §4 replay | order 幂等 replay | `wc.m2.order.create` | auto | full | no | N/A | 同 §4 create 命令再跑一次 | `replay: true`；JSONL 无重复脏行 |
| §4+ transition | order → PENDING_PAYMENT（sandbox） | `wc.m2.order.transition` | auto | **full**（`--include-payment` runner step 6 或 happy-path execute） | no | N/A | `python scripts/run_order_intake.py --jsonl-path artifacts/e2e/WC-DEMO-1/orders.jsonl transition --order-id ORD-WC-DEMO-1 --to pending_payment --actor cli --reason sandbox` | DRAFT→PENDING_PAYMENT；非法跳转 `ok: false`；见 WC-M3 scope |
| §4+ pay | sandbox adapter charge → PAID | `wc.m2.order.pay_sandbox` | auto | **full**（`--include-payment` runner step 6） | no | N/A | `GOV_PAYMENT_SANDBOX_ENABLED=1 python scripts/run_order_intake.py --jsonl-path artifacts/e2e/WC-DEMO-1/orders.jsonl pay --order-id ORD-WC-DEMO-1` | PENDING_PAYMENT→PAID + mock `provider_ref`；**≠ prod 金流** |
| §4+ inspect | payment 状态链 JSONL audit | `wc.m2.order.lookup` | auto | **full**（`--include-payment` runner step 6） | no | N/A | `python scripts/run_order_intake.py --jsonl-path artifacts/e2e/WC-DEMO-1/orders.jsonl lookup --order-id ORD-WC-DEMO-1` | 含 `transitioned_at` · `actor` · `reason`；无 secret 原文 |
| §5 / `5` | 模块 unittest 对照 | （多 path_id · 见 T5） | auto | n/a（单测非 E2E） | no | A-indirect（若并改 Wave 7 装配则 mandatory Tier-A） | `python -m unittest tests.test_ticket_eligibility tests.test_dispatch_cards tests.test_ticket_comms tests.test_ticket_state_update_cli tests.test_order_ledger tests.test_order_ledger_integration tests.test_order_ledger_transition tests.test_payment_sandbox_adapter -v` | 各模块 tests OK；**单测 pass 不具 E2E 说服力**（runbook §5） |
| §6（可选） | 清理 demo 票与隔离产物 | — | auto | n/a | no | N/A | runbook §6 手工步骤 | demo 票/产物已移除；默认 ledger/outbox 无 demo 行 |
| runner `3-hitl`/`4-hitl` | runner 标记 HITL 步骤 | `wc.m2.state.write_ticket` | forbidden | partial | **yes**（manual）/ no（fixture 跳过为 ok） | N/A | manual：`--execute` 无 fixture → steps 为 `hitl`；fixture：`--execute --use-hitl-fixtures` → step 3/4 为 `ok` | manual：HITL 步骤 honestly 标记；fixture：demo 自动化 smoke pass，**≠ production HITL** |
| runner `5` | Cursor chat 开启 | `wc.m2.chat.open_cursor` | forbidden | none | yes（Multi-Chat 人工） | N/A | Multi-Chat 人工开 chat；runner 仍 skip/dry-run 提示 | 人工协作就绪；**禁止** runner 自动开 chat |
| runner `6-payment` | sandbox payment 链（transition + pay + lookup） | `wc.m2.order.pay_sandbox` 等 | auto | **full**（须 **`--include-payment`**） | no | N/A | `python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --execute --use-hitl-fixtures --include-payment --json` | sandbox DRAFT→PAID · step `6-payment` ok；**≠ prod 金流** · **≠ INT Tier-A** |
| CI job | `p9-wc-m2-fixture-execute` advisory | — | auto | full（**不含** payment · 无 `--include-payment`） | no | N/A · **明示 ≠ INT Tier-A** | `python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --execute --use-hitl-fixtures --json` + `python -m unittest tests.test_run_wc_m2_e2e_walkthrough -v` | **Demo fixture CI advisory pass**：11 tests OK + runner `ok: true`（默认至 DRAFT）；**non-blocking** · **≠ INT** · **≠ manual HITL 验收** · payment CI 待 `WH-P9-CI-payment-sandbox-smoke-v1` |
| 改 Wave 6/7/8 装配 | envelope/manifest/QA/orch/runner | — | — | — | conditional | **A-direct / mandatory Tier-A** | `python 04_Workflows/_wave7_regression_gate.py --tier A` | INT Tier-A **pass**：Wave 6/7/8 装配不变量 OK；**不**覆盖 M2 comms/order 链 |
| pre-release | Wave 8 orch 集成 | — | — | — | optional | **B** | `python 04_Workflows/_wave7_regression_gate.py --tier B` | INT Tier-B **pass**：更重集成 OK；M2 walkthrough **无**逐步对应行 |

### 5.1 三模式 × 步骤速查（runner step_id）

| step | Dry-run | Manual HITL | Fixture execute |
|------|---------|-------------|-----------------|
| `0` | ok（预览） | ok | ok |
| `2` dispatch | ok 或 preview | ok | ok |
| `3-hitl` | hitl 提示 | **hitl**（须人工） | skipped → materialized |
| `3` comms | skipped / preview | ok（§3 完成后） | **ok**（P9-T2） |
| `4-hitl` | hitl 提示 | **hitl** | skipped → materialized |
| `4` order | ok 或 skipped | ok | **ok**（P9-T2） |
| `6-payment` | skipped（须 `--include-payment`） | optional（`--include-payment`） | **ok**（加 flag · sandbox DRAFT→PAID · **≠ prod**） |
| `5` unittest | ok | ok | ok |

---

## 6. 三轨 gate 对照小表

> 扩展 WC-T7 §INT gate 草稿；改動類型 × 最低驗證組合。

| 改动类型 | M2 demo E2E（本矩阵） | INT Tier-A/B | PR smoke（core-agent + eval-gate） |
|----------|----------------------|--------------|-----------------------------------|
| Control Plane CLI（eligibility · dispatch · comms · order） | manual HITL runbook §1–§4 **或** §5 单测 + 可选 fixture execute（**advisory only**） | **N/A**（INT 不覆盖此链） | 部分模块间接覆盖；**≠ M2 E2E pass** |
| 模块实现细节（`ticket_eligibility` · `_dispatch_cards` · `order_ledger`） | §5 对应 unittest | **N/A** | PR smoke 可能跑到部分 unittest；**≠ INT Tier-A** |
| Wave 6/7 装配（envelope · manifest · QA · orchestrator · runner） | **不**覆盖 | **mandatory Tier-A**：`python 04_Workflows/_wave7_regression_gate.py --tier A` | **≠ INT Tier-A** |
| Wave 8 M2 契约 / artifact storage / orch pipeline | **不**覆盖 | **mandatory Tier-A**（见 INT contract §1） | **≠ INT Tier-A** |
| PR merge 最低门槛 | **不**替代 PR CI | **不**替代 PR CI | `core-agent-smoke.yml` + `eval-gate-ci.yml` → PR CI **pass**（**仍非 INT Tier-A**） |
| M2 demo E2E 完整 walkthrough | manual HITL **`--execute`** 或 fixture **`--use-hitl-fixtures`**（后者 **≠** 签收依据） | **须另跑** Tier-A（若动装配） | **须另跑** PR smoke；三者 **互补不可互替** |
| pre-release 集成 | 建议 manual HITL + §5 单测 | 建议 **Tier-B** | PR smoke 必要但 **不足** |

### 6.1 Pass 语意对照（防误读）

| 轨 | 命令示例 | pass **代表** | pass **不代表** |
|----|----------|---------------|-----------------|
| **M2 demo E2E · manual** | `--execute` + 手工 STATE | Control Plane demo 链在 demo 票上可串联 | INT Tier-A · prod HITL · 金流闭环 |
| **M2 demo E2E · fixture** | `--execute --use-hitl-fixtures`（可选 `--include-payment`） | comms+order 自动化 smoke；加 flag 时 sandbox 至 PAID；CI advisory 观测 | manual HITL 验收 · INT Tier-A · merge gate · prod 金流 |
| **INT Tier-A** | `_wave7_regression_gate.py --tier A` | Wave 6/7/8 装配不变量 | M2 comms/order 链 · dispatch cards 写卡路径 |
| **INT Tier-B** | `_wave7_regression_gate.py --tier B` | 更重 orch 集成 | M2 walkthrough 逐步覆盖 |
| **PR smoke** | core-agent-smoke · eval-gate-ci | PR 最低门槛 | INT Tier-A · M2 E2E · fixture execute |

---

## 7. 下游实作票草案（FRAME 摘要）

> 本票 **仅提案**；施工须另开 Implementer 票 + 尚書省批文（若涉 CI required / INT 升格）。

### 7.1 WH-P9-M2-INT-gate-impl-v1（实作 · release checklist 钩子）

| 项 | 内容 |
|----|------|
| **目的** | 将本矩阵 §6 中 `A-indirect` / mandatory Tier-A 触发条件接入 `_ops_cycle.py checklist` 或 release CLI 自检；输出 structured `dict`（`ok` · `message` · `recommended_commands[]`） |
| **depends_on** | `WH-P9-M2-INT-alignment-v1`（本票 · 设计 SSOT） |
| **allowed_paths（草案）** | `04_Workflows/_ops_cycle.py` · `04_Workflows/checklists/**` · 本矩阵 cross-ref 一句 |
| **non_goals** | **不**升格 PR required check；**不**改 INT contract 正文；**不**宣称 fixture execute = INT pass |

### 7.2 WH-P9-M2-HITL-runbook-automation-v2（实作 · manual HITL 半自动辅助）

| 项 | 内容 |
|----|------|
| **目的** | manual HITL checklist 半自动化：before/after STATE 快照 diff 提示、FRAME/STATE 字段校验 script；**不写** live `*_state.md` |
| **depends_on** | `WH-P9-M2-INT-alignment-v1` · `WD-P9-T2`（fixture 路径已存在） |
| **allowed_paths（草案）** | `scripts/**`（新校验 CLI）· `tests/**` · runbook §3/§4 追加「校验命令」cross-ref |
| **non_goals** | **不**自动化 `wc.m2.state.write_ticket`（forbidden）；**不**移除 manual HITL 主路径 |

### 7.3 WH-P9-M2-fixture-ci-tier-mapping-v1（可选 · CI 升格设计）

| 项 | 内容 |
|----|------|
| **目的** | 评估 `p9-wc-m2-fixture-execute` 从 advisory → required 的 G1–G8 证据模板与 rollback playbook |
| **depends_on** | 本票 · `WC-GOV-EXEC-ARTIFACTS-LLM` CP-AUTO 分级 |
| **allowed_paths（草案）** | `.github/workflows/p9-wc-m2-fixture-execute.yml` · governance 设计稿 |
| **non_goals** | **blocked_on_approval**；无批文 **不得**改 branch protection；升格 **不**等价 INT Tier-A 接入 |

---

## 8. 交叉引用

| 文档 | 用途 |
|------|------|
| [`WC_T7_e2e_walkthrough_runbook.md`](WC_T7_e2e_walkthrough_runbook.md) | E2E 命令正文 · WC-T5 path_id 附录 |
| [`WC_T5_automation_coverage_contract.md`](WC_T5_automation_coverage_contract.md) | `wc.m2.*` automation_tier SSOT |
| [`docs/phase6-int-regression-gate-contract-v1.md`](../phase6-int-regression-gate-contract-v1.md) | INT Tier-A/B contract |
| [`04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md`](../../04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md) | Tier-A/B runner 细则 |
| [`04_Workflows/tickets/WD-P9-T1-wc-m2-order-demo-e2e-v1_state.md`](../../04_Workflows/tickets/WD-P9-T1-wc-m2-order-demo-e2e-v1_state.md) | runner 双模式基线 |
| [`04_Workflows/tickets/WD-P9-T2-wc-m2-hitl-fixture-automation-v1_state.md`](../../04_Workflows/tickets/WD-P9-T2-wc-m2-hitl-fixture-automation-v1_state.md) | fixture execute 实装 |
| [`04_Workflows/tickets/WH-P9-M2-INT-alignment-v1_state.md`](../../04_Workflows/tickets/WH-P9-M2-INT-alignment-v1_state.md) | 本设计票 state |
| [`WC_M3_payment_closure_scope_v1.md`](WC_M3_payment_closure_scope_v1.md) | P9 sandbox payment closure SSOT · §4+ 步骤 |

---

*WC M2 INT / HITL / Fixture Alignment Matrix v1 · WH-P9-M2-INT-alignment-v1 · doc-only · 设计 SSOT · 非实作票*
