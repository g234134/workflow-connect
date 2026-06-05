# W2-3 — Minimal Governance Gate Design（v0.1 · 设计 only）

> **票号**：W2-3-MINIMAL-GATE-DESIGN（总控交付）；**实现** → Wave 3／CI 施工 chat  
> **状态**：设计定稿；**原型实现** `workflow_v2/tools/wf_gov_gate.ps1`（W2-3-MINIMAL-GATE-IMPL）；**无** CI job  
> **消费 artifact**：**ART-GOV-RISK**（`G8_artifact_contract/60_gov_risk.md`）；**imp_state**（`G7_state_machine/40_imp_state_field_v0.1.md`）；部分 **ART-***（见 §3）

---

## 1. 目标与边界

| 项 | 说明 |
|----|------|
| **目标** | 文档层 **最小可用** gate：在高风险或 RISK exit 时，用**可机读**字段组合给出 `allow`／`deny`／`require-human-override` |
| **非目标** | 完整 release gate、deny engine runtime、prod 流量、L1+ monitoring 决策 |
| **实现形态（建议 W3）** | `workflow_v2/tools/wf_gov_gate.ps1` 或 CI job `gov-risk-gate`；输入案卷目录或 JSON 路径 |
| **权威** | 本设计 **不** 修改 G6/G7/G10 条文语义；仅 **读取** G8／案卷 |

---

## 2. Gate 触发点（v0.1）

| Gate ID | 触发时机 | 硬／软 | 说明 |
|---------|----------|--------|------|
| **GATE-RISK-EXIT** | **`IMP-RISK-VALIDATION` exit** → `IMP-QA-READY` | **硬** | 主 gate；验证 **ART-GOV-RISK** signed 或合法 fallback |
| **GATE-REL-ENTRY** | **`IMP-RELEASE-DECISION` entry** | **软** | 再验 RISK artifact 未 `stale`；**ART-QA-REV** 已存在 |
| **GATE-STOP-WORK** | 案卷 `must_stop_work: true` 任意时刻 | **硬** | 与 IMP 前进无关的 **全局停工** 探测 |

```text
IMP-REVIEW-READY
      ↓
IMP-RISK-VALIDATION  ──[ GATE-RISK-EXIT ]──►  IMP-QA-READY
      ↓
   … QA …
      ↓
IMP-RELEASE-DECISION ◄──[ GATE-REL-ENTRY ]（可选复检）
```

**不触发**：`IMP-AI-READY` entry（仅 **ART-ENG-CTX**）；`IMP-SCOPE-DRAFT`（无 GOV 轨要求）。

---

## 3. 最小检查字段组合

### 3.1 输入源（按优先级）

| 优先级 | 源 | 字段／文件 |
|--------|-----|------------|
| P0 | 案卷 | `<CASE>_case.md` → `imp_state` |
| P0 | **ART-GOV-RISK** | JSON 或案卷内嵌块（`60_gov_risk.md` §4） |
| P1 | **ART-ENG-CTX** | `primary_change_class`、`forbidden_zone_types` |
| P1 | guard 摘要 | `trigger_context.guard_verdict_ref`（可选） |
| P2 | **ART-QA-REV** | 仅 **GATE-REL-ENTRY**；`verdict` |
| P2 | **ART-ENG-EVD** | `evidence_refs` 解析失败 → warning，非 sole deny |

### 3.2 GATE-RISK-EXIT 检查表

| # | 检查 | 失败默认 |
|---|------|----------|
| R1 | `imp_state == IMP-RISK-VALIDATION`（exit 前） | `deny` |
| R2 | **ART-GOV-RISK** 存在且 `schema_version` 可识别 | 无 artifact → 走 **fallback 链**（§4） |
| R3 | `status == signed` **或** `fallback_used: true`（票面授权） | `deny` |
| R4 | `nbt_validation.all_required == true` | `deny` |
| R5 | `must_stop_work == false` **或** `override_effective == true` | `deny` 或 `require-human-override` |
| R6 | 无 `risk_items` 中 `open` + `severity` ∈ {high, critical} | `deny` |
| R7 | `primary_change_class` 与 **ART-ENG-CTX** 一致（若双份存在） | `deny` |

### 3.3 GATE-REL-ENTRY 检查表（软）

| # | 检查 | 失败默认 |
|---|------|----------|
| L1 | **ART-GOV-RISK** `status` ≠ `stale` | `require-human-override` |
| L2 | **ART-QA-REV** `verdict` ∈ {accepted, accepted_with_gaps} | `deny` |
| L3 | `risk_types` 不含未关闭的 `release_exit_blocked` | `deny` |

### 3.4 GATE-STOP-WORK

| # | 检查 | 失败默认 |
|---|------|----------|
| S1 | **ART-GOV-RISK** `must_stop_work == true` | `deny` |
| S2 | `override_effective == false` | `deny` |
| S3 | guard `verdict` ∈ {deny, stop_work}（若提供 ref） | `deny` |

---

## 4. Fallback 链（GOV artifact 缺失）

与 G10-2 §6.3、G8-6 §4.6 对齐：

```text
1) 尝试读取 ART-GOV-RISK（案卷 JSON / 约定文件名 art_gov_risk.json）
      ↓ 缺失
2) 检查票面 / queue Notes 是否明示 fallback_used 授权
      ↓ 否
3) deny + message: "ART-GOV-RISK required"
      ↓ 是
4) 读取 ART-ENG-WR §4 + §7 + G10-2 §6.3 人工勾选镜像（W2-1 过渡）
      ↓
5) 输出 require-human-override（不得自动 allow）
```

**W2-3 之后新案卷**：默认 **禁止** 步骤 4 自动 `allow`；须 governance owner 显式 `fallback_used: true`。

---

## 5. Gate 输出契约

| 值 | 含义 | 下游动作 |
|----|------|----------|
| **`allow`** | 全部硬检查通过 | 允许 IMP exit／queue 标 **DONE**（仍须 checker 等其它 gate） |
| **`deny`** | 硬检查失败 | **禁止** IMP 前进；写案卷 blocker；可选 `rule_ref: G10-2§*` |
| **`require-human-override`** | 仅 fallback、conditional override、或 soft gate 失败 | 须尚書省／governance 留痕后再跑 gate |

**结构化输出（建议 W3 实现）**：

```json
{
  "gate_id": "GATE-RISK-EXIT",
  "ok": false,
  "verdict": "deny",
  "checks_failed": ["R4", "R5"],
  "artifact_refs": { "ART-GOV-RISK": "W2-3-RISK-001" },
  "message": "nbt_validation.all_required is false",
  "imp_state": "IMP-RISK-VALIDATION"
}
```

| 字段 | 必填 |
|------|:----:|
| `gate_id` | ✓ |
| `ok` | ✓ |
| `verdict` | ✓ |
| `checks_failed` | 条件 |
| `message` | ✓ |
| `imp_state` | ✓ |

---

## 6. 与现有 tooling 关系

| 现有 | 关系 |
|------|------|
| `tools/wf_check_cross_ref.ps1` | **不合并**；cross-ref 仍做 AC grep；gate **另脚本** |
| `W2-2_tooling_notes.md` NBT 清单 | gate R4 应对齐 **G10-2-§6.3-v0.1** item_key |
| governance-guard JSON | gate **读取** `guard_verdict_ref`，**不** 替代 guard |
| checker **ART-QA-REV** | gate **不** 签发 QA verdict |

---

## 7. 已实现范围（v0.1 原型 · `wf_gov_gate.ps1`）

| 项 | 状态 |
|----|------|
| **GATE-RISK-EXIT** | ✓ 读 `CaseDir/art_gov_risk.json`；R3–R6 + fallback 链 |
| **GATE-REL-ENTRY** | ✓ 读 `-GovRiskPath` + `CaseDir/06_art_qa_rev.json`；L1–L2 + tooling_checks（若存在） |
| **GATE-STOP-WORK** | ✗ 未独立暴露（逻辑合并在 GOV baseline） |
| **输出** | `verdict`、`checks_failed[]`、人类摘要；`VERDICT=`／`CHECKS_FAILED=` 末行 |
| **参数** | `-Gate`、`-CaseDir`、`-GovRiskPath`、`-AllowFallback`、`-ImpState`、`-RepoRoot` |
| **WR fallback 正文** | ✗ 不解析 `05_art_eng_wr.md` |
| **R7 ENG-CTX 对账** | ✗ |
| **CI** | ✗ → Wave 3 |

调用见 `20_pilot/W2-3_case/README.md` §3.0。

## 8. W3+ 施工建议

1. CI：仅在 `workflow_v2/**` 变更时 optional job；**不** 阻塞 production。  
2. 将 `GATE-RISK-EXIT` 结果写入 **ART-QA-REV** 可选字段 `gov_gate_ref`（需 G8-4 附录票授权）。  
3. 实现 GATE-STOP-WORK 独立入口与 WR fallback 链步骤 4。

---

## 9. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | W2-3 最小 gate 设计 v0.1：三触发点、检查表、输出契约、fallback 链 |
| 2026-05-27 | W2-3-MINIMAL-GATE-IMPL：`wf_gov_gate.ps1` 原型；§7 已实现字段范围 |
