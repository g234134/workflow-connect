# GOV Risk Pilot — 可引用案例说明（W3-C-GOV-RISK-PILOT）

> **权威契约**：`10_governance/G8_artifact_contract/60_gov_risk.md`（G8-6）  
> **机读实例**：[`art_gov_risk.json`](art_gov_risk.json)  
> **接入矩阵**：[`../W3-C_metrics_schema.md`](../W3-C_metrics_schema.md)（W3-C-ORCH）  
> **下游票**：`W3-C-CI-GATE-WIRE`（nightly `wf_gov_gate` + JSONL）

---

## 1. 对应哪条 W2-1 case

本 pilot **不** 新建 IMP 案卷，而是对 **W2-1 最小闭环** 在 **`IMP-RISK-VALIDATION`** 段的风险叙事做 **事后结构化**（retroactive documentation only）。

| 项 | 值 |
|----|-----|
| **源案卷目录** | `20_pilot/W2-1_case/` |
| **artifact_id** | `W2-1-G8-RECON-PILOT` |
| **primary_change_class** | `CHG-GOV-DOC`（G7↔G8 交叉引用 cleanup） |
| **历史 IMP 段** | `IMP-REVIEW-READY` → **`IMP-RISK-VALIDATION`** → `IMP-QA-READY`（见 `W2-1_case.md` §3 迁移日志） |
| **Eng 临时对照** | `05_art_eng_wr.md` **§4**（ART-ENG-EVD）+ **§7**（override 无） |
| **QA 缺口** | `06_art_qa_rev.json` → `gaps.GAP-GOV-RISK`（正式 GOV artifact 缺失；本 pilot **闭合叙事**，**不** 改 QA verdict） |
| **本案卷角色** | `W2-3_case/` 仅承载 **ART-GOV-RISK** 实例 + 说明；**不** 替代 `W2-1_case.md` 的 IMP 真源 |
| **queue 票号** | JSON `ticket_id` = **`W3-C-GOV-RISK-PILOT`**（收口票）；初稿 authoring = `W2-3-GOV-RISK-PILOT` |

**硬边界（W3-C 全票遵守）**

- **不** 修改 W2-1 的 `imp_state`（仍为 **`IMP-OBSERVING`**）、QA `accepted_with_gaps`、Release `approve`。  
- **不** 用本 JSON  retro-fit 历史 transition 的 `artifact_refs` 字段。  
- 解释性文字只在本目录与本文件；W2-1 仅保留既有 README 一行 cross-ref。

---

## 2. 为何 `fallback_used: true`（WR 过渡期）

W2-1 在 **2026-05-27** 走 **IMP-RISK-VALIDATION → IMP-QA-READY** 时，G8-6 **ART-GOV-RISK** 契约尚未落盘（W2-3 契约票与本案卷 pilot 在后）。当时唯一稳定的机读对照是 **ART-ENG-WR** §4／§7，符合 G10-2 §6.3 读取优先级 **#2（WR fallback）**。

| 机制 | 本 pilot 取值 |
|------|----------------|
| `nbt_validation.fallback_used` | **`true`** — 明示 exit 曾依赖 WR，而非「原生 signed GOV JSON」 |
| `wr_fallback` | `wr_section_4` + `wr_section_7` + `reason`（见 JSON） |
| `status` | **`signed`** — 治理侧 **事后** 将同一叙事折叠进 ART-GOV-RISK，供 gate／指标消费 |
| Gate 默认行为 | `wf_gov_gate` **R3** 双路径可满足；`fallback_used=true` 且无 `-AllowFallback` → **`require-human-override`**（见 `W2-3_case/README.md` §3） |

**语义**：`fallback_used: true` **不是** 声称 NBT §6.3 未通过；`all_required: true` 且五项 `item_key` 均为 `passed: true`。它只标记 **证据链来源** 曾走 WR，避免 CI／副官误以为「从未 fallback」而自动 `allow`。

---

## 3. Wave 3 / Wave 4：`fallback_used` → `false` 路线

| 阶段 | 目标 | 本 pilot 贡献 |
|------|------|----------------|
| **Wave 3（W3-C）** | 案卷 **干净可引用**；nightly 可跑 `GATE-RISK-EXIT` / `GATE-REL-ENTRY` 并写 JSONL | 固定路径 `W2-3_case/art_gov_risk.json`；字段对齐 G8-6；**保留** `fallback_used: true` 作为历史诚实标记 |
| **Wave 3（W3-C-CI-GATE-WIRE）** | PR cross-ref warning + nightly gov gate **响过一次** | Case 列表：`W2-3_case` + `W2-1_case` + `-GovRiskPath`（见 metrics schema §2.3） |
| **Wave 4+** | **新案卷** 在 RISK exit 前产出 **signed** ART-GOV-RISK，且 **`fallback_used: false`** | 本 W2-1 回溯实例 **可保持** `true` 作为对照样本；**不** 为「变绿」而改 W2-1 历史 JSON 语义 |

**新票验收口径（供后续 case，非本票 retro）**

1. `IMP-RISK-VALIDATION` exit 前存在 `art_gov_risk.json`（或案卷内嵌块）。  
2. `status: signed`，`nbt_validation.all_required: true`，**`fallback_used: false`**。  
3. `evidence_refs[]` 指向 ART-ENG-EVD／ART-QA-REV 等；**不** 依赖 `wr_fallback` 作为唯一机读依据。  
4. Nightly：`wf_gov_gate` 在无 `-AllowFallback` 时趋向 **`allow`**（仍受 `must_stop_work`／open high risk 约束）。

---

## 4. 契约字段对齐（摘要）

完整逐项对照见 [`art_gov_risk.json`](art_gov_risk.json) 与同目录 README §4。

| G8-6 区块 | 实例状态 |
|-----------|----------|
| §4.1 元数据 | ✓ 齐全（`signed_at` / `signed_by_role` 已填） |
| §4.2–§4.3 风险类型与 `trigger_context` | ✓；`guard_verdict_ref` **省略**（本案无 guard JSON 指针需求） |
| §4.4 `risk_items[]` | ✓ 3 项；无 `open` + high/critical |
| §4.5 停工／override | ✓；`override_ref` **省略**（`override_effective: false`） |
| §4.6 `nbt_validation` | ✓ 含五项 `item_key` + `checklist_id` |
| §4.7 `evidence_refs` + `wr_fallback` | ✓（`fallback_used: true` 时 `wr_fallback` 必填） |

**已知 TODO（契约外、不阻塞 W3-C-CI-GATE-WIRE）**

- [ ] 可选：后续新 case 增加 `trigger_context.guard_verdict_ref`（有 Cursor guard JSON 时）。  
- [ ] `W2-3_case.md` IMP 迁移表（队列占位；非本票范围）。  
- [ ] Wave 4：评估是否将本实例复制为「零 fallback」对照条目的 **新** `artifact_instance_id`（**不** 覆盖本文件）。

---

## 5. 本地 gate 复现（CI 接线前自检）

```powershell
# GATE-RISK-EXIT（默认 → require-human-override，因 fallback_used）
powershell -NoProfile -File workflow_v2/tools/wf_gov_gate.ps1 `
  -Gate GATE-RISK-EXIT `
  -CaseDir workflow_v2/20_pilot/W2-3_case `
  -ImpState IMP-RISK-VALIDATION

# 票面_ack fallback 过渡窗 → allow（exit 0）
powershell -NoProfile -File workflow_v2/tools/wf_gov_gate.ps1 `
  -Gate GATE-RISK-EXIT `
  -CaseDir workflow_v2/20_pilot/W2-3_case `
  -AllowFallback `
  -ImpState IMP-RISK-VALIDATION

# GATE-REL-ENTRY（W2-1 + 本 GOV 路径）
powershell -NoProfile -File workflow_v2/tools/wf_gov_gate.ps1 `
  -Gate GATE-REL-ENTRY `
  -CaseDir workflow_v2/20_pilot/W2-1_case `
  -GovRiskPath workflow_v2/20_pilot/W2-3_case/art_gov_risk.json
```

---

## 6. 引用

| 主题 | 路径 |
|------|------|
| W2-3 case README | [`README.md`](README.md) |
| Gate 设计 | `20_pilot/W2-3_minimal_gate_design.md` |
| W2-1 源案卷 | `20_pilot/W2-1_case/` |
