# Phase 6 · Inspector Over-claim Spotcheck v1

> **Ticket**: `FP-G6-T4-inspector-overclaim-spotcheck-v1` · Full-Phase G6 · P6 · **doc/spec** · evidence_tier **L-local**  
> **用途**：Reviewer **抽样对照**清单 — 在既有 inspector SSOT 之上，快速拦截 over-claim。  
> **不取代**：`04_Workflows/review_checklists/wave-next-code-inspector-v1.md`（战术 lane 完整清单仍为权威）。

---

## Non-claims（置顶）

| 本清单 **不是** | 说明 |
|-----------------|------|
| ≠ required CI / branch protection 已挂 | WC-PRE 批文前禁止宣称 |
| ≠ INT Tier-A / P6 closure / Round-2 GO | 抽样绿 ≠ 里程碑关闭 |
| ≠ 替代 `wave-next-code-inspector-v1.md` 全文 | 本档 = 抽样加速层 |
| ≠ 授权改 Phase% / master_status / workflows | Reviewer 只读 |

---

## 1. 与三份 checklist 分界

| 档 | 职责 | 本票关系 |
|----|------|----------|
| `wave-next-code-inspector-v1.md` | 战术 lane（P7 / P8.5 / P9）完整 Reviewer 清单 | **SSOT** · 本档抽样项映射其 §3.2–§3.3 |
| `wave-master-plan-reviewer-v1.md` | Master Plan 规划层 | 不混用 |
| `wave-cross-rollup-inspector-v1.md` | 跨 Wave 证据 rollup（W5-T3） | 涉 rollup 时另开；本档不重定义 trace |

**决策一句话**：战术 lane 收口 → 先本档 spotcheck → 有疑点再展开 inspector 全文 §3–§5。

---

## 2. 何时用本档

| 场景 | 动作 |
|------|------|
| Wave-next / G6 相关子票进 Review | 必跑 §3 抽样表（≥1 lane 或 ≥1 Progress 条） |
| Scribe 封存前自检 | 对照 §4 常见 over-claim 句式 |
| Orchestrator 关票前 | 确认 C_REPORT 无 Reject-over-claim 未解 |

**不做**：改 yml · 跑 prod/staging · flip env · 调 Phase%。

---

## 3. 抽样对照表（Reviewer 用）

逐项勾选；任一 **blocking** 与对外宣称冲突 → 不得给 **OK**（映射 inspector verdict）。

### 3.1 证据位阶（必抽）

| # | 抽样问题 | 对照证据 | ☐ |
|---|----------|----------|---|
| S1 | 宣称「CI / GA pass」是否有 **run URL** 或 honest gap？ | 子票 B_REPORT · Progress 末尾 | ☐ |
| S2 | `overall_status: done` 是否与 gaps / blocked_by 诚实一致？ | `*_state.md` STATE + B_REPORT | ☐ |
| S3 | INDEX / runbook / Progress 是否写了与子票相反的状态？ | `WORKFLOW_INDEX.md` · 相关 docs · Progress 末 1–3 条 | ☐ |
| S4 | advisory / local / sandbox 是否被写成 required / prod / SLA？ | workflow 命名 · doc non_claims · C_REPORT | ☐ |

### 3.2 Over-claim 硬拦截（映射 inspector §3.3）

| # | 禁止句式（发现即 Reject-over-claim） | ☐ |
|---|--------------------------------------|---|
| O1 | 「CI landing = GA pass」且无 run URL | ☐ |
| O2 | 「unittest 本地 pass = 远端 validated」 | ☐ |
| O3 | 「本票上调 Phase%」于 ticket / Progress / chat | ☐ |
| O4 | 「required check / merge gate」无批文 + G8 证据 | ☐ |
| O5 | 「release-sanity / MP-SMOKE 绿 = P6 closure / INT Tier-A」 | ☐ |

### 3.3 Human-blocked 诚实（映射 inspector §3.4）

| 阻塞线 | 抽样断言（仍 blocked 时不得宣称完成） | ☐ |
|--------|----------------------------------------|---|
| P7 Round-2 | 未宣称真 staging execute 完成 | ☐ |
| P8.5 Scenario2 GA | 未宣称 Scenario2 GA pass | ☐ |
| P9 CI 首跑 | 无 run URL 时未宣称 CI 首跑 pass | ☐ |
| WC-PRE / required CI | 未宣称 required CI 已挂 | ☐ |
| P6 nightly 7d | 未宣称 7 日绿 → 83→91 已 uplift | ☐ |

### 3.4 建议最小抽样集（一次 Review）

1. 目标子票 `FRAME.non_claims` + `B_REPORT.verification`（各读一遍）。  
2. Progress **末尾 1 条**是否与票号 / AC 对齐。  
3. 若本轮改过 workflow 或 INDEX：各 spot-check **一句** advisory 语意。  
4. 填 §5 迷你 verdict（或贴回子票 C_REPORT）。

完整 traversal 仍见 inspector §5。

---

## 4. 常见 over-claim 句式 → 改写

| 危险说法 | 诚实改写 |
|----------|----------|
| 「CI 已绿，可关 P6」 | 「L-local / advisory CI 路径通过；P6 closure 另票 + 治理」 |
| 「smoke 全过 = INT Tier-A」 | 「MP/MC/CI-SMOKE L-local pass；INT Tier-A 未升格」 |
| 「runbook 写了就等于 required」 | 「runbook = 操作指引；required 需 WC-PRE 批文」 |
| 「observer / rollup 无 gap = GA 完成」 | 「gaps 空 ≠ human GA；须 run URL + verified」 |
| 「doc 设计完成 = runtime 已上线」 | 「doc/spec done；runtime / migration 另开票」 |

---

## 5. 迷你 Verdict 模板（可贴 C_REPORT）

```markdown
## Inspector Over-claim Spotcheck

- **date**: YYYY-MM-DD
- **checklist**: `docs/phase6-inspector-overclaim-spotcheck-v1.md`
- **inspector_ssot**: `04_Workflows/review_checklists/wave-next-code-inspector-v1.md`
- **ticket_id**: …
- **samples**: S1–S4 / O1–O5 / blocked 线（勾选结果）
- **verdict**: OK | Partial | Blocked | Reject-over-claim
- **over_claims_found**: 无 | （列项）
- **next_action**: …
```

Verdict 定义与 inspector §4 一致（OK / Partial / Blocked / Reject-over-claim）。

---

## 6. 交叉引用

| 资源 | 路径 |
|------|------|
| Inspector SSOT | `04_Workflows/review_checklists/wave-next-code-inspector-v1.md` |
| Release-sanity 操作单页 | `docs/phase6-release-sanity-runbook-v1.md`（≠ required CI） |
| Smoke 契约 | `docs/smoke-and-regression-contract-v1.md` |
| Evidence tier | `docs/evidence-tier-contract-v1.md` |
| INDEX Reviewer 收口 | `04_Workflows/WORKFLOW_INDEX.md` §1.55 附近 |

---

*phase6-inspector-overclaim-spotcheck-v1 · FP-G6-T4 · doc-only · L-local · 2026-07-10*
