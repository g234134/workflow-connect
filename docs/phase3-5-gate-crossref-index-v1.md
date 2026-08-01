# Phase 3.5 — eval-gate／K-2／ENF 交叉索引（v1）

> **Ticket**: `FP-G1-T4-eval-gate-k2-enf-crossref-index-v1` · Full-Phase G1 · P3.5 · **doc/spec** · evidence_tier **L-local**  
> **Date**: 2026-07-10  
> **对齐**：WA-T3 contract · `eval-gate-ci` · K-2 playbook · ENF shadow · engineering-contract **REF-9.7**

---

## non_claims（置顶 · 必读）

| 本索引 **不是** | 说明 |
|-----------------|------|
| ≠ **blocking canary 已开** | ENF／K-2 canary 仍须尚书省批文；默认 shadow-only |
| ≠ **K-2 prod 主答案**／partial rollout | 见 `k2_deployment_governance.md`；本页仅交叉索引 |
| ≠ **改 eval 阈值**／升格 CI required | 不改 workflows／门槛数值 |
| ≠ **Phase closure**／Phase% 上调 | 仅索引 |

**位阶**

| 文件 | 角色 |
|------|------|
| **本档** | 诚实 **交叉索引**（gate · blocking? · evidence · non-claim） |
| [`docs/phase3-5-cost-model-governance-contract-v1.md`](./phase3-5-cost-model-governance-contract-v1.md) | Gate 分类 **SSOT**（WA-T3） |
| [`docs/k2_deployment_governance.md`](./k2_deployment_governance.md) | K-2 流量分轨／Phase 门控 |
| [`docs/k2_merge_strategy.md`](./k2_merge_strategy.md) | 合流语义 |
| `.cursor/rules/engineering-contract.mdc` **REF-9.7** | Agent 执行层：未经批准禁 prod K-2 主答案 |
| ENF shadow 操作指南（W5-A／`enf_config`） | `GOV_ENF_BLOCKING_CANARY` 默认 **0** |

---

## 1. Purpose

防止 Wave／lane chat **误开** blocking canary 或把 shadow nightly 读成 required eval gate。  
本票 **只写索引**；不改 eval 阈值、不启 prod K-2、不改 `.github/workflows/**`。

---

## 2. 交叉索引表

| gate／能力 | blocking? | evidence／入口 | non-claim（诚实边界） |
|------------|-----------|----------------|------------------------|
| **eval-gate PR**（`MG-EVAL-UNIT`／`MG-EVAL-CI-CHECK`） | **是**（PR job；若 repo 设 required check） | `.github/workflows/eval-gate-ci.yml` → job `eval-gate` · WA-T3 §2.1 | PR 绿 ≠ INT Tier-A ≠ K-2 canary ≠ Phase% |
| **core-agent-smoke PR** | **是**（PR tier） | `core-agent-smoke.yml` · `docs/testing.md` | smoke 绿 ≠ ENF blocking |
| **eval-shadow-nightly** | **否**（shadow-only；`continue-on-error`） | `eval-gate-ci.yml` → `eval-shadow-nightly` · WA-T3 §2.2 | nightly 存在 ≠ blocking gate |
| **ENF Preview（Phase A）** | **否**（shadow；`GOV_ENF_BLOCKING_CANARY=0`） | ENF shadow guide · `observability/enf_config.py` | **禁止**自行设 blocking canary=1 |
| **K-2 shadow export** | **否**（shadow／logging） | `ibridge_exporter --source shadow` · `k2_ask_shadow` | shadow ≠ prod 主答案 |
| **K-2 Phase 1+ prod shadow／canary** | **否（未批则禁止）** | `k2_deployment_governance.md` §4–§6 · REF-9.7 | 须尚书省批文；worker 不得自订 rollout |
| **routing-eval dry-run** | **否**（optional class；可出现在 eval-gate step） | `run_routing_eval.py --dry-run` · WA-T3 §2.3 | dry-run ≠ `--execute` |
| **agent-lines CI** | **否**（optional） | `agent-lines-ci-suite-v1.md` · FP-G6-T3 deferred 索引 | ≠ required／≠ INT Tier-A |

---

## 3. 阅读规则（防误开）

1. 凡写「canary」「blocking ENF」「K-2 主答案」→ 先查本表 + K-2 playbook Phase；无批文 → **honest blocked**。  
2. 凡写「eval gate 已 blocking」→ 区分 **PR mandatory trio** vs **nightly shadow**；勿把 shadow 写成 merge blocker 以外的「已开 canary」。  
3. REF-9.7：未经尚书省批准，**禁止**在 prod 启用 K-2 主答案或 partial rollout。

---

## 4. Mini checklist（编排／Reviewer）

- [ ] 索引表含 gate · blocking? · evidence · non-claim  
- [ ] 已链 WA-T3 contract + K-2 治理 doc + REF-9.7  
- [ ] 未改 workflows／eval 阈值／Phase%／`core/**`  

---

## 5. Verification（本票 AC · `rg`）

```bash
rg "eval-gate|K-2|ENF|non_claims|blocking" docs/phase3-5-gate-crossref-index-v1.md
```

期望命中：`non_claims`、`eval-gate`、`K-2`、`ENF`、`blocking` 诚实列。
