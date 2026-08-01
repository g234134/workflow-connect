# WC-PRE-06／07 批文追踪 SSOT（v1）

> **Ticket**: `FP-G1-T2-wc-pre-06-07-approval-tracker-v1` · Full-Phase G1 · P3.5／P10 · **doc/spec** · evidence_tier **L-local**  
> **Date**: 2026-07-10  
> **对齐**：`W-MASTER-full-phase-plan_state.md#G1` · Wave B／W5 WC-PRE design · Dashboard WC-PRE 脚注

---

## non_claims（置顶 · 必读）

| 本 tracker **不是** | 说明 |
|---------------------|------|
| ≠ **批文已获**／`approval_status=approved` | 状态机可写到 `pending_approval`；**仅 human** 可关 `approved` |
| ≠ **required CI** 已挂／branch protection 已改 | 升格仍须批文后另票（G6／WC-IMPL） |
| ≠ **Phase closure**／Phase% 上调 | 仅追踪 doc |
| ≠ **AI 代填已批准** | Implementer／Scribe **禁止**把本页写成已批准 |

**位阶**

| 文件 | 角色 |
|------|------|
| **本档** | WC-PRE-06／07 **批文状态机 SSOT**（追踪 · 非批文正文） |
| [`docs/toolchain-observability-governance-upgrade-v1.md`](./toolchain-observability-governance-upgrade-v1.md) | WC-PRE-06 设计稿 |
| [`docs/governance/WC_PRE_06_approval_template.md`](./governance/WC_PRE_06_approval_template.md) | 06 批文空白模板 |
| [`docs/toolchain-smoke-mandatory-ci-runner-v1.md`](./toolchain-smoke-mandatory-ci-runner-v1.md)（若存在）／W5-WC-PRE-07 | 07 mandatory smoke 设计 |
| Wave design 票 `W5-WC-PRE-06`／`W5-WC-PRE-07` | design_ready 资产（**≠** approved） |

---

## 1. Purpose

为 WC-PRE-06（toolchain health L2／required 升格）与 WC-PRE-07（mandatory smoke CI）提供 **统一状态枚举 + 转换条件**，并列出 `blocks_if_missing` 下游。  
本票交付 = **tracker doc**；关 `approved` = **human-only**。

---

## 2. 状态枚举（两票共用）

| 状态 | 含义 | 谁可写入 |
|------|------|----------|
| `design_ready` | 设计稿／模板／policy JSON 已齐；可开批文流程 | AI／Implementer（doc） |
| `pending_approval` | 批文包已提交尚书省；等待 sign-off | human 启动；AI 可标「已提交」但 **不可**标 approved |
| `approved` | 批文 ID + sign-off 齐；允许开下游 implementation／升格票 | **仅 human** |
| `rolled_back`／`rejected`（可选） | 批文撤回或否决 | **仅 human** |

### 转换条件

```text
design_ready
    --(批文包提交：模板字段齐 + Progress 末尾占位)--> pending_approval
pending_approval
    --(尚书省／治理委员会 sign-off + wc_pre_approval_id)--> approved   【仅 human】
pending_approval
    --(否决／撤回)--> rejected | rolled_back | design_ready（重提） 【仅 human】
approved
    --(回滚批文)--> rolled_back 【仅 human】
```

**硬规则**：AI／lane chat **不得**把任一票从 `pending_approval` 推到 `approved`。

---

## 3. 两票当前追踪表（诚实快照）

| 票 | 设计资产 | tracker 状态（本页） | 关票交付物占位 |
|----|----------|----------------------|----------------|
| **WC-PRE-06** | `toolchain-observability-governance-upgrade-v1.md` · `WC_PRE_06_approval_template.md` · policy JSON | **`design_ready` + Batch-2 defer**（`WC-2026-07-10-06D`）· **≠ approved** | `wc_pre_approval_id: WC-PRE-06-APPROVAL-________` · approver · approval_date · scope L0\|L1\|L2 |
| **WC-PRE-07** | W5-WC-PRE-07 design bundle · mandatory smoke 设计稿／approval template | **`design_ready` + Batch-2 defer**（`WC-2026-07-10-07D`）· **≠ approved** | `wc_pre_approval_id: WC-PRE-07-APPROVAL-________` · approver · approval_date · smoke scope |

> 上表状态以 Dashboard／Progress 为准刷新；**本页默认不写 approved**。  
> **Batch-2（2026-07-10）**：尚書省確認繼續 defer · 觀察期門檻維持 ≥14 日 health/flake 後再裁 L1 · defer ID **不是** approval ID。  
> **Decision confirm（2026-07-11 B3）**：維持 defer（06D／07D）· ≥14d 後再裁 L1 · **required CI 本階段不開** · 仍 ≠ approved。

### 关票交付物（human 填）

```yaml
# 复制到 Progress 末尾（append-only）· 仅 human 在 approved 时填满
wc_pre_ticket: WC-PRE-06 | WC-PRE-07
tracker_status: approved
wc_pre_approval_id: WC-PRE-0X-APPROVAL-________
approver: ________
approval_date: YYYY-MM-DD
sign_off_ref: meeting|email|________  # 非 run URL 亦可
```

---

## 4. blocks_if_missing（下游仍 blocked）

在 **06 或 07 未 `approved`** 前，下列项 **不得**宣称已解阻：

| 下游 | 为何 blocked | 指针 |
|------|--------------|------|
| **G6 required CI**／`FP-G6-T1`／`FP-G6-required-ci` | 无批文不得改 branch protection／required checks | QUEUE `FP-G6-T1` · `branch_human_gated` |
| **W4-GUARD G2–G4 升格** | 与 WC-PRE／治理批文同族 | `FP-G1-T3`（仍 BLOCKED 占位） |
| **WC-IMPL-L2**（及 L1 required 路径） | 须 06／07 approved 后另开 implementation | Wave B／WC-IMPL 线 |
| **OG-TOOLCHAIN-HEALTH 作 PR required** | design ≠ required 已挂 | Dashboard WC-PRE 脚注 |

---

## 5. Mini checklist（编排／Reviewer）

- [ ] 提及 WC-PRE-06／07 时：写明 `design_ready`／`pending_approval`／`approved` 之一；未 human 签则 **禁止**写 approved  
- [ ] 若声称 required CI／GUARD G2–G4／WC-IMPL-L2 已开：对照 §4 → **Reject-over-claim**  
- [ ] 未改 `.github/workflows/**`／branch protection／Phase%／`core/**`  

---

## 6. Verification（本票 AC · `rg`）

```bash
rg "WC-PRE-06|WC-PRE-07|approved|non_claims" docs/wc-pre-06-07-approval-tracker-v1.md
```

期望命中：`non_claims`、两票状态枚举、`approved` 仅 human、`blocks_if_missing`（G6／GUARD／WC-IMPL）。
