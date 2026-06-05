# W3-C — 治理自动化闭环（主线 C）

> **总控交付**：[`../W3-C_metrics_schema.md`](../W3-C_metrics_schema.md)（接入矩阵 + 指标 v0.1 + 子票摘要）  
> **计划**：`00_master_plan.md` §13.3 · `90_run_queue.md` Wave 3 — W3-C 节

---

## 子票产出（待施工）

| ID | 产出文件（计划） |
|----|------------------|
| **W3-C-GOV-RISK-PILOT** | [`../W2-3_case/gov_risk_pilot_notes.md`](../W2-3_case/gov_risk_pilot_notes.md)；[`../W2-3_case/art_gov_risk.json`](../W2-3_case/art_gov_risk.json) |
| **W3-C-CI-GATE-WIRE** | `ci_gate_wire.md`（接线设计+命令解析示例）；CI workflow 片段；首条 JSONL 样例 |
| **W3-C-AGENT-SOP** | `agent_sop_gate.md` |
| **W3-C-IMP-STATE-LINT** | `imp_state_lint.md`；可选 `tools/wf_imp_state_lint.ps1` 骨架 |

## 前置工具（已存在）

| 脚本 | 说明 |
|------|------|
| `workflow_v2/tools/wf_gov_gate.ps1` | `GATE-RISK-EXIT` / `GATE-REL-ENTRY` |
| `workflow_v2/tools/wf_check_cross_ref.ps1` | AC-1～AC-4b（G8Recon） |

## 指标目录（候选 · 未创建）

`workflow_v2/observability/gov_gate_metrics/` — 见总控文档 §3.5。
