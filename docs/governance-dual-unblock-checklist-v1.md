# governance_dual 解阻 FRAME — 五頂 Checklist（v1）

> **Ticket**: `FP-G1-T1-governance-dual-unblock-frame-v1` · Full-Phase G1 · P7 / P3.5 · **doc/spec** · evidence_tier **L-local**  
> **Date**: 2026-07-10  
> **对齐**：`W-MASTER-full-phase-plan_state.md#G1` · Dashboard P7 Round-2 · Wave 2 staging 票（W2-T1／W2-T2）

---

## non_claims（置顶 · 必读）

| 本 FRAME **不是** | 说明 |
|-------------------|------|
| ≠ **P7 Round-2 GO** | checklist 齐 ≠ 授权 execute-v2／staging notify |
| ≠ **governance_dual 真批文已齐** | 本页只列要件与 defer；**不**代填批文 ID |
| ≠ **Phase closure**／Phase% 上调 | 仅 doc；**不**改 Dashboard 数字 |
| ≠ **prod endpoint flip**／客户 staging 已通 | Infra／Security／receiver 仍 human／infra |
| ≠ **required CI** 已挂 | 与 WC-PRE／G6 required 线无关 |

**位阶**

| 文件 | 角色 |
|------|------|
| **本档** | governance_dual **解阻 FRAME**（五顶 checklist · owner／交付物／defer） |
| [`docs/WAVE_PROGRESS_DASHBOARD.md`](./WAVE_PROGRESS_DASHBOARD.md) | P7 Round-2 叙事 SSOT（**只读** Phase%） |
| [`docs/P7_ADVISORY_CI_INDEX.md`](./P7_ADVISORY_CI_INDEX.md) | advisory CI 诚实索引（≠ Round-2 GO） |
| Wave 2 票 `W2-T1`／`W2-T2`（QUEUE） | 真批文 request／Infra staging **占位**（human／infra） |

---

## 1. Purpose

把 P7 Round-2 **五顶前置**写成可勾选 FRAME：每项有 **owner**、**交付物**、**blocked 时 defer 规则**、**Wave 2 票链**。  
本票 **只写 checklist**；不取得真批文、不跑 staging notify、不改 workflows／Phase%。

---

## 2. 五顶 Checklist

| # | 要件 | owner | 交付物（关票条件） | blocked 时 defer | Wave 2／占位 |
|---|------|--------|--------------------|------------------|--------------|
| **1** | **governance_dual 真批文** | **human**（尚书省／治理） | 批文 ID 或 sign-off 留痕（Progress 末尾 + 对应票 FRAME）；**非** simulated Round-1 | 维持 Round-2 `blocked`；Progress 写 `blocked_on_approval`；**禁止** AI 代填 approved | **W2-T1**（governance_dual 真批文 request runbook · QUEUE BLOCKED）→ **2026-07-13 更新**：批文模板已落地 `docs/governance/GOVERNANCE_DUAL_approval_template.md` · ID `GOV-DUAL-APPROVAL-2026-07-13-01` · lifecycle **`approved_pending_countersign`**（对话授权 + 模板齐；实体副署仍待填）· **≠ Round-2 GO** |
| **2** | **Infra staging slot／HTTPS endpoint** | **infra** | staging slot 说明 + HTTPS endpoint 规格（路径见 Master_Map 逻辑名；**不**硬编本机绝对路径） | defer execute-v2；开 Infra spec 票后再施工；**禁止**假 endpoint | **W2-T2**（Infra staging slot + HTTPS endpoint · QUEUE BLOCKED） |
| **3** | **Security 对外 notify 路径批文** | **security**（+ 尚书省） | Security 对 outbound notify／客户通道的书面批准或等价留痕 | defer staging notify；advisory smoke **≠** Security GO | **planning／blocked** 占位（随 W2-T1／Security 批文；非本票施工） |
| **4** | **客户 allowlist** | **human**（产品／客户对接） | allowlist 范围与生效条件（cohort／tenant／case 边界） | defer 客户向流量；local／simulated **≠** allowlist 已开 | **planning／blocked** 占位（Round-2 前置；另票） |
| **5** | **receiver 部署就绪** | **infra**（+ human 验收） | receiver 部署证据（环境／健康检查摘要；**不**贴密钥） | defer end-to-end notify；adapter unittest **≠** receiver GA | **planning／blocked** 占位（Round-2 前置；另票） |

### 阅读规则

- 任一项 **未** 交付前：Progress／Reviewer／Orchestrator **禁止**写「Round-2 GO」「governance_dual 批文已齐」「客户 staging 已通」。  
- Round-1 **local slot validated**（simulated governance_dual）与本表 **可并存**：Round-1 绿 ≠ 五顶已齐。  
- advisory CI（`p7-notification-smoke` 等）绿 **≠** 本 FRAME 关票。

---

## 3. Mini checklist（编排／Reviewer）

- [ ] 提及 Round-2 时：对照五顶表 → 未齐则 **honest blocked**  
- [ ] 若声称批文已齐／Phase closure／prod flip：→ **Reject-over-claim**  
- [ ] 未改 `.github/workflows/**`／Dashboard Phase%／`core/**`／金钥  

---

## 4. Verification（本票 AC · `rg`）

```bash
rg "governance_dual|五顶|non_claims" docs/governance-dual-unblock-checklist-v1.md
```

期望命中：`non_claims`、五顶表、`governance_dual`、owner／交付物／defer、Wave 2 票链。
