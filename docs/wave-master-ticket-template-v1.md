# Wave Master Ticket Template v1

> **SSOT 票**：`W5-T2-wave-master-ticket-template-v1`  
> **Master schema**：`docs/ticket-schema-master-v1.md`（**字段主版本**）  
> **Authority**：Wave 5 = Master CP schema SSOT（`W-MASTER-wave-plan_state.md` §Wave 1/5 去重裁定 · 方案 A）  
> **Playbook 欄位規範**：`docs/wave-master-ticketing-playbook.md` §3  
> **Machine template**：`04_Workflows/tickets/_templates/ticket_state.template.md`

---

## 用途

Wave 1–5 Implementer 開 **執行子票** 時，Orchestrator 複製 `ticket_state.template.md` 為 `<ticket_id>_state.md`，並填寫 **FRAME 標準欄 + Wave Master 擴展欄**。Wave 1 **只消費、不維護** 本模板。

一般 Multi-Chat 票（非 Wave Master 子票）可 **省略** FRAME 內「Wave Master 擴展」小節；仍使用同一 `ticket_state.template.md` 的 B/C/D/O 區塊。

---

## 檔案索引

| 檔案 | 用途 |
|------|------|
| **`docs/ticket-schema-master-v1.md`** | **字段主版本** · group_id · evidence_tier · ticket_class |
| `04_Workflows/tickets/_templates/ticket_state.template.md` | 主 schema（FRAME/STATE/B/C/D + Wave Master 擴展占位） |
| `04_Workflows/tickets/_templates/wave_master_frame_block.template.yaml` | YAML 複製塊（Orchestrator 快速貼上） |
| `04_Workflows/tickets/_templates/*_instruction.template.md` | 四角色 instruction（含 Wave Master 子票提示） |
| `docs/wave-master-ticketing-playbook.md` | 欄位填寫規範 · observability 合格標準 |
| `04_Workflows/tickets/W-MASTER-wave-plan_state.md` §Shared Ticket Schema | 權威欄位定義 |

---

## FRAME 必填（Wave Master 子票）

| 欄位 | 要求 |
|------|------|
| **Goal … AcceptanceCriteria** | 標準 FRAME（見 template） |
| **wave_id** | `W1`…`W5` · 与 Chat 一致 |
| **lifecycle_phase** | 開票 `B`；施工票从 `B` 进入 |
| **phase_targets** | 只列 Dashboard Phase 名 · **不写 %** |
| **estimated_cycles** | `1` 或 `2` |
| **mvp_allowed** | `true` 时 AC 须分 MVP vs stretch |
| **human/infra/security_only_prereqs** | 无则 `[]` |
| **dependencies_detail** | 见 playbook §4.1 |
| **risks** | 见 playbook §4.2 |
| **observability** | 见 playbook §4.3 — **verify_commands 必填** |
| **non_claims** | 复制 global + 票专属 |

---

## STATE 建議欄位

- `lifecycle_phase` 与 FRAME 扩展栏同步（B/C/D/O）
- `overall_status` 含 `frame_ready` · `awaiting_ops` · `done_with_gaps`（Wave Master 票常用）
- `relay_mode`／`ops_checklist`／`current_owner: ops` → 权威见 `docs/ticket-schema-master-v1.md`（W5-T6）

---

## 消費方式（Wave 1 / Wave 2 / Wave-next）

| 消費方 | 做法 |
|--------|------|
| **Wave 1 `W1-P75-*`** | 開票时引用本 template 路径；FRAME 填 Wave Master 扩展；**禁止**自建 schema 主版本 |
| **Wave 2–4 执行子票** | 同上；observability 对照 playbook §4.3 |
| **Wave-next（W-ORCH）** | 战术 lane 子票仍用本 template；战术 Reviewer 用 `wave-next-code-inspector-v1.md`（**不**混用 Master Plan Review checklist） |
| **Orchestrator 起手** | 复制 template → 填 FRAME → 用 `.cursor/commands/ticket-orchestrator.md` 或 `wave-master-planner.md` |

---

## MVP 边界（诚实 defer）

- **本票交付**：template 结构 + YAML 复制块 + instruction 扩展提示 + 本文档  
- **defer W5-T4**：`ticket_reviewer_checklist.template.md`（Reviewer 附页 · 字段对齐 W5-T2）  
- **defer W5-T5**：全 Wave playbook rollup INDEX（`WORKFLOW_INDEX.md` 新节）  
- **不宣稱**：模板已覆盖所有 future ticket 类型 · 不替代 Master Reviewer 人工 verdict

---

*版本：v1 · 2026-06-26 · W5-T2 MVP · Wave 5 Master CP SSOT*
