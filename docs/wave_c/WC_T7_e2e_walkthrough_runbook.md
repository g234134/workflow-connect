# WC-T7 — Control Plane M2 E2E Walkthrough Runbook (v0.1)

> **性质**：Control Plane 端到端手工／半自动验收 runbook。  
> **用途**：M2/M3 Wave C Control Plane 链本地走通（eligibility → dispatch cards → comms → order intake）。  
> **重要**：本 runbook **不等于** INT Tier-A regression gate。Control Plane E2E pass **不**代表 INT pass；两者职责见文末 §INT gate 对齐。

**票号**：`WC-T7`  
**建议 demo 票**：`WC-DEMO-1`（勿用生产票如 `W1-T*`）  
**隔离产物根**：`artifacts/e2e/<ticket_id>/`  
**交叉引用**：`docs/wave_c/WC_T1_eligibility.md` · `WC_T2_comms_minimal.md` · `WC_T4_order_ledger_design.md` · `docs/control_plane_dispatch_executor.md`

---

## 前置条件

| 项 | 要求 |
|----|------|
| 工作目录 | repo 根 |
| Demo 票 | `04_Workflows/tickets/<ticket_id>_state.md` 已按 §1 创建；推荐 `<ticket_id>=WC-DEMO-1` |
| 隔离目录 | `artifacts/e2e/<ticket_id>/` 已创建（comms outbox 与 order ledger 共用父目录） |
| Python | 战车主舱或已配置 `sys.path` 的 shell（脚本位于 `scripts/`） |
| 涉及 CLI | `run_ticket_eligibility.py` · `run_dispatch_cards.py` · `run_ticket_state_update_with_comms.py` · `run_order_intake.py` |

**CLI 约束（只读 ticket state，不写 `*_state.md`）**

| 步骤 | 脚本 | 关键 flags |
|------|------|------------|
| Eligibility + 指令卡 | `scripts/run_dispatch_cards.py` | `--refresh-plan` · `--ticket` · `--role implementer` · `--eligibility-gate block` · 可选 `--force-eligibility` |
| Comms JSONL | `scripts/run_ticket_state_update_with_comms.py` | `--before` · `--after` · `--outbox-dir` |
| Order intake | `scripts/run_order_intake.py` | `create` / `lookup` · `--jsonl-path`（顶层 flag，写在子命令之前） |

**可选 runner（编排骨架，不替代手工 STATE 编辑）**

```bash
python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --dry-run
python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --execute
```

---

## 0. 环境与目录

1. 确认当前目录为 repo 根。
2. 创建隔离目录：`artifacts/e2e/<ticket_id>/`。

**预期输出**：目录存在且为空或仅含本 walkthrough 产物。  
**失败诊断**：若路径不在 `artifacts/e2e/` 下，停止——避免污染默认 `artifacts/ticket_comms/` 或 `artifacts/order_ledger/`。

---

## 1. 准备初始 `*_state.md`（`in_progress` / `implementer`）

1. 复制模板：`04_Workflows/tickets/_templates/ticket_state.template.md` → `04_Workflows/tickets/<ticket_id>_state.md`。
2. 填写 **FRAME**（至少 `Title` · `AllowedPaths` · `Dependencies: 无` · `VerificationCommands` 指向本 runbook）。
3. 填写 **STATE** 为 implementer 可接单态，例如：
   - `overall_status: in_progress`
   - `implementation_status: in_progress`（可选，与 WC-T2 fixture 对齐）
   - `current_owner: implementer`
   - `next_action: Implementer runs M2 E2E smoke`
   - `status_by_role.implementer: in_progress` · `reviewer: pending`
4. **B_REPORT / C_REPORT / D_REPORT** 可留空或占位；dispatch / eligibility 只读 FRAME + STATE。

**可选预检（eligibility 应返回 eligible）**

```bash
python scripts/run_ticket_eligibility.py --ticket <ticket_id> --requested-role implementer --format json
```

**预期输出**：JSON 中 `eligible: true`（或项目惯用等价键）。  
**失败诊断**：检查 STATE `overall_status` / `status_by_role` / FRAME `Dependencies` 是否阻塞；勿对生产票强行 `--force-eligibility`。

---

## 2. Dispatch cards + eligibility gate

1. 刷新 dispatch plan 并生成 Implementer 指令卡：

```bash
python scripts/run_dispatch_cards.py \
  --refresh-plan \
  --ticket <ticket_id> \
  --role implementer \
  --eligibility-gate block \
  --out-dir artifacts/e2e/<ticket_id>/cards/ \
  --json-summary artifacts/e2e/<ticket_id>/dispatch_cards_run.json \
  --pretty
```

2. 若 demo 票因依赖 / blocked 被 gate 拦截、但仍需验证写卡路径，Orchestrator 可 **一次性** override（须留痕）：

```bash
python scripts/run_dispatch_cards.py \
  --refresh-plan \
  --ticket <ticket_id> \
  --role implementer \
  --eligibility-gate block \
  --force-eligibility \
  --out-dir artifacts/e2e/<ticket_id>/cards/ \
  --pretty
```

3. **Dry-run 对照**（不写卡，只看 summary）：

```bash
python scripts/run_dispatch_cards.py \
  --refresh-plan \
  --ticket <ticket_id> \
  --role implementer \
  --eligibility-gate block \
  --dry-run \
  --pretty
```

**预期输出**：`cards_generated >= 1`；`artifacts/e2e/<ticket_id>/cards/<ticket_id>__implementer.cursor.md` 存在；summary 无 `eligibility_blocked`（除非 STATE 不满足 gate）。  
**失败诊断**：先跑 `--dry-run` 看 `eligibility_blocked` 原因；必要时一次性 `--force-eligibility` 并记入战报。

---

## 3. STATE → `review` / `reviewer` + comms JSONL

> WC-T2 CLI **不写入** live state；先快照再改文件，再对比 before/after。  
> **顺序**：本步全部完成后再进入 §4；勿与 `ready_for_order` 编辑并行，否则 comms diff 会混入开单态字段。

1. 保存变更前快照：

```bash
cp 04_Workflows/tickets/<ticket_id>_state.md artifacts/e2e/<ticket_id>/before_review.md
```

（Windows PowerShell：`Copy-Item 04_Workflows/tickets/<ticket_id>_state.md artifacts/e2e/<ticket_id>/before_review.md`）

2. **手工编辑** `04_Workflows/tickets/<ticket_id>_state.md` 的 **STATE** 为 reviewer 关口，例如：
   - `overall_status: review`
   - `implementation_status: in_review`
   - `current_owner: reviewer`
   - `next_action: Reviewer validates comms JSONL`
   - `status_by_role.implementer: done` · `reviewer: in_progress`

3. 生成 comms（append JSONL）：

```bash
python scripts/run_ticket_state_update_with_comms.py \
  --before artifacts/e2e/<ticket_id>/before_review.md \
  --after 04_Workflows/tickets/<ticket_id>_state.md \
  --outbox-dir artifacts/e2e/<ticket_id>/comms
```

4. **Dry-run**（不写 JSONL）：

```bash
python scripts/run_ticket_state_update_with_comms.py \
  --before artifacts/e2e/<ticket_id>/before_review.md \
  --after 04_Workflows/tickets/<ticket_id>_state.md \
  --dry-run
```

**预期输出**：stdout `ok: true` · `sent: true`；`artifacts/e2e/<ticket_id>/comms/ticket_comms.jsonl` 新增一行 `ticket_comms_v0.1`（`overall_status`：`in_progress` → `review`）。  
**失败诊断**：确认 `before`/`after` 路径正确且 STATE 字段确有差异；用 `--dry-run` 查看 payload 再决定是否写 JSONL。

---

## 4. `ready_for_order` + order create + lookup

1. **手工编辑** **STATE** 为开单就绪（主路径：`next_action` 含 `ready_for_order`），例如：
   - `overall_status: review`（或 `done`；见 WC-T4 §4.2 备选）
   - `current_owner: orchestrator`
   - `next_action: ready_for_order — create order for <ticket_id> E2E demo`
   - `status_by_role.reviewer: done`

2. 创建 order（使用隔离 JSONL）：

```bash
python scripts/run_order_intake.py \
  --jsonl-path artifacts/e2e/<ticket_id>/orders.jsonl \
  create \
  --ticket <ticket_id> \
  --amount-minor 10000 \
  --currency TWD
```

3. Lookup 验证：

```bash
python scripts/run_order_intake.py \
  --jsonl-path artifacts/e2e/<ticket_id>/orders.jsonl \
  lookup \
  --ticket-id <ticket_id>
```

4. 幂等 replay（同 ticket 再次 create 应返回 `replay: true`）：

```bash
python scripts/run_order_intake.py \
  --jsonl-path artifacts/e2e/<ticket_id>/orders.jsonl \
  create \
  --ticket <ticket_id> \
  --amount-minor 10000 \
  --currency TWD
```

**预期输出**：create → `ok: true` · `message: order_created` · `order.order_id` 为 `ORD-<ticket_id>`；lookup 返回同 order；replay → `replay: true`。  
**失败诊断**：确认 `--jsonl-path` 在子命令 **之前**；STATE `next_action` 含 `ready_for_order`；JSONL 路径在 `artifacts/e2e/<ticket_id>/` 下。

---

## 5. 一键 unittest 对照（非 E2E 替代）

各模块单测仍应独立全绿；E2E 为跨 CLI 手工串联：

```bash
python -m unittest tests.test_ticket_eligibility tests.test_dispatch_cards tests.test_ticket_comms tests.test_ticket_state_update_cli tests.test_order_ledger tests.test_order_ledger_integration -v
```

**预期输出**：全部 tests OK。  
**失败诊断**：定位失败模块单测后再重跑 E2E；单测失败时 E2E pass 不具说服力。

---

## 6. 清理（可选）

- 删除 `04_Workflows/tickets/<ticket_id>_state.md`（demo 票）
- 删除 `artifacts/e2e/<ticket_id>/` 整目录
- 若曾写入默认路径，检查 `artifacts/ticket_comms/ticket_comms.jsonl` 与 `artifacts/order_ledger/orders.jsonl` 是否误污染

**预期输出**：demo 票与隔离产物已移除；默认 outbox/ledger 无 demo 行。  
**失败诊断**：grep JSONL 中 `<ticket_id>`；发现污染则从默认 ledger 手工剔除或整文件重置（仅本地 demo 环境）。

---

## INT gate 对齐（草稿 · v0.1）

> **职责分离**：Control Plane E2E 验证 **Wave C M2 CLI 链**在 demo 票上的可串联性；INT Tier-A 验证 **Wave 6/7 装配层** unittest 不变量。**两者互补，不可互相替代。**

| 改动类型 | 推荐验证 | 过 gate 含义 |
|----------|----------|--------------|
| Control Plane CLI（eligibility · dispatch cards · comms · order intake） | 本 runbook §1–§4 或 §5 单测 + 本 runbook 手工链 | Control Plane E2E **pass** |
| `ticket_eligibility` · `_dispatch_cards` · `order_ledger` 实现细节 | §5 对应模块 unittest | 模块回归 **pass**（非 INT） |
| envelope / manifest / QA / orchestrator / runner（Wave 6/7 装配） | `python 04_Workflows/_wave7_regression_gate.py --tier A` | INT Tier-A **pass** |
| Wave 8 M2 契约 / artifact storage / orch pipeline | 同上 Tier-A（见 `docs/phase6-int-regression-gate-contract-v1.md` §1） | INT Tier-A **pass** |
| PR merge 最低门槛 | `core-agent-smoke.yml`（PR smoke）+ `eval-gate-ci.yml` | PR CI **pass**（仍 **非** INT Tier-A） |

**明确声明**

1. **Control Plane E2E pass ≠ INT pass**：跑通本 runbook 不证明 Wave 6/7 装配未退化。
2. **INT Tier-A pass ≠ Control Plane E2E pass**：INT 不覆盖 dispatch cards / comms JSONL / order ledger 链。
3. 改 Control Plane 路径：至少跑 §5 单测；发版或 M2/M3 验收前跑本 runbook。
4. 改 Wave 6/7 装配路径：本地 **mandatory** 跑 INT Tier-A（见 `04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md` §2.1）。
5. 升格 PR required / prod gate：须尚書省批文；本对齐表 **不**自动开启任何 blocking CI。

**索引**

- INT SSOT：`docs/phase6-int-regression-gate-contract-v1.md`
- 实现附录：`04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md`
- Wave C 总览：`docs/wave_c/overview.md`

---

*WC-T7 E2E Walkthrough Runbook · v0.1 · 2026-06-13 · doc-only skeleton · runner 见 `scripts/run_wc_m2_e2e_walkthrough.py`*
