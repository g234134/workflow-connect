# Phase 6 — Agent Lines Nightly / run-all-allowed Deferred Index (v1)

> **Ticket**: `FP-G6-T3-agent-lines-nightly-deferred-index-v1` · Full-Phase G6 · P6 · **doc/spec · planning/deferred** · evidence_tier **L-local**  
> **Date**: 2026-07-10  
> **对齐**：`W-MASTER-full-phase-plan_state.md#G6` · `docs/agent-lines-ci-suite-v1.md` · INDEX §1.14

---

## non_claims（置顶 · 必读）

| 本索引 **不是** | 说明 |
|-----------------|------|
| ≠ GitHub **required** CI | nightly／PR path-filter **optional**；**不**等于 branch protection 已挂 required check（WC-PRE） |
| ≠ INT **Tier-A** | agent-lines suite 绿 **不覆盖** INT gate／Tier-A |
| ≠ **Phase%** 上调 | 本页仅 deferred／已落地对照；**不**改 Dashboard 数字 |
| ≠ **P6 closure** | 索引齐 ≠ Phase 6 结案 |
| ≠ **Round-2 GO**／prod default run mode | deferred 项仍须批文／另票；本页 **不**授权执行 |

**位阶**

| 文件 | 角色 |
|------|------|
| **本档** | **planning／deferred 索引**（已落地 vs 延后 · 诚实 blocker） |
| [`docs/agent-lines-ci-suite-v1.md`](./agent-lines-ci-suite-v1.md) | Agent Lines CI **用法／JSON／安全边界** SSOT |
| [`04_Workflows/WORKFLOW_INDEX.md`](../04_Workflows/WORKFLOW_INDEX.md) **§1.14** | Runner／票 state 索引 |
| [`.github/workflows/agent-lines-ci.yml`](../.github/workflows/agent-lines-ci.yml) | optional PR + **schedule nightly** + `workflow_dispatch`（**只读引用**；本票不改） |
| [`docs/phase6-int-regression-gate-contract-v1.md`](./phase6-int-regression-gate-contract-v1.md) | INT／optional smoke 矩阵；`TS-AGENT-LINES-CI` = optional |

---

## 1. Purpose

把 **Agent Lines** 上「`run-all-allowed` + nightly CI」相关能力拆成：

1. **已落地（Landed）** — 可本地／optional workflow 复跑，但 **非** required  
2. **明确延后（Deferred）** — 须批文、另票或 human／infra 前置；**禁止**把 deferred 写成已验收  

本票 **只写索引**；不改 workflows、不升格 required、不跑 nightly 7d 监控表。

---

## 2. Landed（诚实已有 · 仍 optional）

| ID | 能力 | 证据／入口 | 诚实边界 |
|----|------|------------|----------|
| L-01 | CI suite 合并入口 | `scripts/run_agent_lines_ci_suite.py` · `docs/agent-lines-ci-suite-v1.md` | optional helper；**不**改 MVP mainline |
| L-02 | Tabular 内部 `run-all-allowed` + `auto-approve-intake` | suite `--scope tabular\|all` → `run_agent_standard_case_regression.py` | L-local／CI optional；≠ prod default run mode |
| L-03 | NT preview（stub） | suite `--scope non_tabular\|all` | preview-only；非 heavy tools |
| L-04 | Optional PR path-filter job | `agent-lines-ci.yml` → `agent-lines-ci-pr` | path-filter；**非** required |
| L-05 | Nightly schedule hook | `agent-lines-ci.yml` → `schedule` cron `30 5 * * *` → `agent-lines-ci-nightly`（`--scope all --include-extended-fixtures`） | schedule **存在** ≠ required／≠ INT Tier-A／≠ 7d uplift 已填 |
| L-06 | Manual dispatch | `workflow_dispatch` inputs（scope／extended／stub） | 人工触发；非 GA 门禁 |
| L-07 | Unittest | `tests/test_agent_lines_ci_suite_v1.py` | 单元层；≠ GA-remote |

**本地复跑（索引用 · 非本票验收 runner）**

```bash
python -m unittest tests.test_agent_lines_ci_suite_v1 -v
python scripts/run_agent_lines_ci_suite.py --scope all --format json
# nightly 等价（extended）：
python scripts/run_agent_lines_ci_suite.py --scope all --include-extended-fixtures --format json
```

---

## 3. Deferred 索引（本票正文）

| Deferred ID | 延后项 | 为何延后 | 解阻 owner／前置 | 另票／指针 |
|-------------|--------|----------|------------------|------------|
| D-01 | Agent Lines／suite **升格 required CI** | WC-PRE／branch protection 未批 | 尚书省批文 · `FP-G6-required-ci` · `FP-G6-T1` | **blocked_on_approval** · 勿本轮 execute |
| D-02 | Nightly 绿 → **P6 Phase%／INT uplift** | 须 merge + 连续监控证据；治理 uplift 另流程 | `WF-P6-INT-NIGHTLY-MONITOR` · human 7d 表 | **human-blocked**（P6-nightly-7d） |
| D-03 | **production v2 default** run mode = `run-all-allowed` | 产品／治理批文；非 CI helper 范围 | 尚书省 · Wave 7 deferred 注记 | Dashboard Wave 7 deferred 句 |
| D-04 | Extended fixtures **作为 mandatory** PR／release gate | 现仅 nightly／manual 可选；mandatory 须批文 | G6 required-CI 线 | 与 D-01 同批文族 |
| D-05 | NT fixture **扩面**（超 NT-A／NT-B stub） | W9 线 follow-up；非 G6 本索引施工 | W9／corpus 策略 | W10-T1 deferred_items |
| D-06 | Suite 失败 **阻塞 PR merge** | 现 optional class（`TS-AGENT-LINES-CI`） | 同 D-01 | `phase6-int-regression-gate-contract` § optional |
| D-07 | Agent-lines nightly **纳入 INT Tier-A 硬门禁** | Tier-A 另契约；agent-lines ≠ Tier-A | INT／G6 required 线 | contract §5 矩阵 |

### Deferred 阅读规则

- 表内任一项 **未** 解阻前：Progress／Reviewer **禁止**写「nightly required 已挂」「run-all-allowed 已成 prod 默认」「agent-lines = INT Tier-A」。  
- L-05（schedule 已存在）与 D-01／D-02 **可并存**：有 cron ≠ 已升格／≠ uplift 完成。

---

## 4. 与相邻 G6 文档分界

| 文档 | 本索引关系 |
|------|------------|
| `phase6-release-sanity-runbook-v1.md`（T2） | MP→MC→CI-SMOKE **操作单页**；**不含** agent-lines deferred 表 |
| `phase6-inspector-overclaim-spotcheck-v1.md`（T4） | Reviewer over-claim **抽样**；可引用本表防「nightly=required」误读 |
| `agent-lines-ci-suite-v1.md` | **用法 SSOT**；本档不取代其 CLI／JSON 说明 |
| `FP-G6-T1`／`FP-G6-required-ci` | **批文后** required 升格；本档仅索引指向 |

---

## 5. Mini checklist（编排／Reviewer）

- [ ] 提及 agent-lines nightly 时：写明 **optional** 或指向 L-05  
- [ ] 若声称 required／Tier-A／Phase%／Round-2：对照 D-01…D-07 → **Reject-over-claim** 或 honest blocked  
- [ ] 未改 `.github/workflows/**`／Dashboard Phase%／金钥  

---

## 6. Verification（本票 AC · `rg`）

```bash
rg "deferred|run-all-allowed|nightly|non_claims|agent-lines|required" docs/phase6-agent-lines-nightly-deferred-index-v1.md
```

期望命中：`non_claims`、Landed／Deferred 表、`run-all-allowed`、nightly／schedule 诚实边界、required／Tier-A 否定句。
