# W2-3 试点案卷 — ART-GOV-RISK pilot

> **票号**：W2-3-GOV-RISK-PILOT  
> **契约**：`10_governance/G8_artifact_contract/60_gov_risk.md`（G8-6）  
> **Gate 设计**（文档层 only）：`20_pilot/W2-3_minimal_gate_design.md`  
> **状态**：pilot 实例已落盘；gate 原型脚本 **`workflow_v2/tools/wf_gov_gate.ps1`**（W2-3-MINIMAL-GATE-IMPL）；**无** CI enforcement

---

## 1. Pilot case 来源（W2-1）

本 pilot **参考** [`../W2-1_case/`](../W2-1_case/) 在 **`IMP-RISK-VALIDATION`** 阶段的风险叙事，将其从 **ART-ENG-WR** §4／§7 折叠为可机读的 **ART-GOV-RISK** JSON。

| 项 | 说明 |
|----|------|
| **源案卷** | `W2-1-G8-RECON-PILOT`（CHG-GOV-DOC；G7↔G8 交叉引用 cleanup） |
| **WR 段落** | [`05_art_eng_wr.md`](../W2-1_case/05_art_eng_wr.md) **§4**（验证证据／ART-ENG-EVD）、**§7**（override 无） |
| **迁移日志** | [`W2-1_case.md`](../W2-1_case/W2-1_case.md) §3：`IMP-REVIEW-READY` → `IMP-RISK-VALIDATION` 行注明 WR 临时对照 |
| **QA 缺口** | [`06_art_qa_rev.json`](../W2-1_case/06_art_qa_rev.json) → `gaps.GAP-GOV-RISK` |

**重要边界**

- **不** 修改 W2-1 的 `imp_state`（仍为 **`IMP-OBSERVING`**）、**不** 改 QA `accepted_with_gaps`、**不** 改 Release `approve`。  
- 本目录 JSON 为 **文档层 retroactive 结构化** + gate 消费性证明；W2-1 历史决策保持不变。  
- W2-1 案卷 README 已加注释指向本 pilot（见 W2-1 `README.md`）。

---

## 2. 交付物

| 文件 | 说明 |
|------|------|
| [`art_gov_risk.json`](art_gov_risk.json) | **ART-GOV-RISK** v0.1 实例（`status: signed`；`fallback_used: true`） |
| [`gov_risk_pilot_notes.md`](gov_risk_pilot_notes.md) | **W3-C** 可引用案例说明（W2-1 对齐、fallback 路线、契约对照） |
| 本 README | case 来源、G10-2 对照、gate 消费说明 |

（`W2-3_case.md` IMP 迁移日志留待后续票；本票仅 GOV artifact pilot。）

---

## 3. 如何使用此 GOV artifact（gate 原型 v0.1）

脚本：`workflow_v2/tools/wf_gov_gate.ps1`（只读；stdout only）。案卷约定文件名：`art_gov_risk.json`（见 `W2-3_minimal_gate_design.md` §3.1、§4）。

### 3.0 调用示例（repo 根目录）

```powershell
# GATE-RISK-EXIT（本目录）
powershell -NoProfile -File workflow_v2/tools/wf_gov_gate.ps1 `
  -Gate GATE-RISK-EXIT `
  -CaseDir workflow_v2/20_pilot/W2-3_case

# 票面已批 WR fallback 过渡窗时，显式_ack fallback：
powershell -NoProfile -File workflow_v2/tools/wf_gov_gate.ps1 `
  -Gate GATE-RISK-EXIT `
  -CaseDir workflow_v2/20_pilot/W2-3_case `
  -AllowFallback `
  -ImpState IMP-RISK-VALIDATION

# GATE-REL-ENTRY（W2-1 案卷 + 本目录 GOV JSON）
powershell -NoProfile -File workflow_v2/tools/wf_gov_gate.ps1 `
  -Gate GATE-REL-ENTRY `
  -CaseDir workflow_v2/20_pilot/W2-1_case `
  -GovRiskPath workflow_v2/20_pilot/W2-3_case/art_gov_risk.json
```

| 退出码 | 含义 |
|--------|------|
| `0` | `allow` |
| `1` | `require-human-override` |
| `2` | `deny` |
| `3` | 参数／路径错误 |

末行机器行：`VERDICT=…`、`CHECKS_FAILED=…`（逗号分隔）。

**v0.1 限制**：不读 WR 正文 fallback；不实现 GATE-STOP-WORK 独立入口；`W2-3_case` 无 `*_case.md` 时须 `-ImpState`；`art_gov_risk.json` 中 `fallback_used: true` 默认 **`require-human-override`**（除非 `-AllowFallback`）。

### 3.1 `IMP-RISK-VALIDATION` exit — `GATE-RISK-EXIT`

在 **`IMP-RISK-VALIDATION` → `IMP-QA-READY`** exit 时，gate 应至少检查：

| 检查 ID | 字段／规则 | 本 pilot 预期 |
|---------|------------|---------------|
| R2 | 文件存在；`schema_version` 可识别 | ✓ `0.1` |
| R3 | `status == signed` **或** `nbt_validation.fallback_used == true`（票面授权） | ✓ signed + `fallback_used: true` |
| R4 | `nbt_validation.all_required == true` | ✓ `true`（五项 `item_key` 均 `passed: true`） |
| R5 | `must_stop_work == false` **或** `override_effective == true` | ✓ `must_stop_work: false` → **allow** 倾向 |
| R6 | 无 `risk_items` 中 `open` + `severity` ∈ {high, critical} | ✓ 无 open high/critical |
| R7 | `primary_change_class` 与 **ART-ENG-CTX** 一致 | ✓ `CHG-GOV-DOC` |

**停工组合（须 deny）示例**

- `must_stop_work: true` **且** `override_effective: false` → gate **`deny`**（G8-6 §4.5；gate 设计 R5／S2）。  
- `nbt_validation.all_required: false` → **`deny`**（R4）。  
- 存在 `risk_items[]` 且 `disposition: open` + `severity: high|critical` → **`deny`**（R6）。

**Fallback 链**

- 本实例 `fallback_used: true` + `wr_fallback` 指向 W2-1 WR §4／§7 → 对齐 G10-2 §6.3 读取优先级 #2；gate 输出应为 **`require-human-override`** 或票面 **`allow`**（尚書省已批过渡窗），**不得** 因 fallback  alone 自动 `allow`（见 gate 设计 §4 步骤 5）。  
- 本 pilot 同时 `status: signed`，故 R3 双路径均可满足；新案卷应优先 **signed + fallback_used: false**。

### 3.2 其它触发点（索引）

| Gate | 相关字段 |
|------|----------|
| **GATE-STOP-WORK** | `must_stop_work`、`override_effective`、`trigger_context.guard_verdict_ref` |
| **GATE-REL-ENTRY**（软） | `status` ≠ `stale`；`risk_types` 不含未关闭的 `release_exit_blocked` |

---

## 4. G10-2 §6.3 对照

| G10-2 | 本 pilot |
|-------|----------|
| §6.3 `item_key` 五項 | `nbt_validation.items[]` 1:1 对齐 |
| `checklist_id` | `G10-2-§6.3-v0.1` |
| 读取优先级 #1 | 存在 **ART-GOV-RISK** → 查 `all_required` + `status` |
| Fallback #2 | `fallback_used: true` + `wr_fallback` → WR §4／§7 |
| §5.3 IMP-RISK-VALIDATION | `trigger_context.imp_state`、`nbt_rule_refs` |

字段定义权威：`60_gov_risk.md` §4.6。

---

## 5. 引用

| 主题 | 路径 |
|------|------|
| G8-6 契约 | `10_governance/G8_artifact_contract/60_gov_risk.md` |
| G10-2 NBT | `10_governance/G10_governance_rulebook/20_no_blind_trust.md` |
| 最小 gate 设计 | `20_pilot/W2-3_minimal_gate_design.md` |
| W2-1 源案卷 | `20_pilot/W2-1_case/` |
