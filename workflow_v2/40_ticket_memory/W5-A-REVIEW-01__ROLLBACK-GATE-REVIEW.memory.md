# Ticket Memory — W5-A-REVIEW-01

> **用途**：W5-A K-2 rollout **实施结果集中总检**；在 `W5-A-RUNTIME-*` 子票交付后，由 Reviewer 对 CI diff、rollout config、gate checklist、rollout 记录做只读审查，产出 `approve` / `request_changes` / `block` verdict。  
> **父票**：`workflow_v2/40_ticket_memory/W5-A-K2-ROLLOUT-EXPANSION.memory.md`  
> **控制面**：`workflow_v2/30_control_plane/W4-X_control_plane_mvp.md`（§1.4 Reviewer · §1.4.1 最小检查清单 · §2.3 Review lane）  
> **模板**：`workflow_v2/40_ticket_memory/_TEMPLATE_ticket_memory.md`  
> **本文件产出切片**：planning（仅 Ticket Memory；**无** CI / runtime / tools / `00`/`90`/`99` 变更）

---

## ticket

- id: **W5-A-REVIEW-01**
- title: **W5-A rollout 实施结果 · Reviewer 总检**

## lane

- lane: **review**

## priority

- priority: **P0**（阻塞 W5-A-DOCSYNC-01 与父票 runtime 切片收口；prod rollout 证据未经 Reviewer 放行不得进入 doc-sync 全局黑板）

## mode

- mode: **review**（Reviewer 只读检查 + verdict；**不**写主代码、**不**修 CI、**不**修 `00`/`90`/`99` 正文）

## goal

在 **W5-A-RUNTIME-01**（首条 prod CI）及本票 `read_set` 所列、**已交付** 的 `W5-A-RUNTIME-*` 子票完成后，由 **Reviewer** 做一次 **集中总检**，对下列对象给出结构化 verdict（`approve` / `request_changes` / `block`）：

1. **CI diff**：票面锁定的 prod（或 prod-equivalent）release workflow 变更（shadow / canary / promote / rollback hook / pause·override 触发点）；是否越界 `write_set`、是否 blanket 改 `.github/workflows/*`、是否 silent 改 `eval-gate-ci.yml` / `gov-gate-metrics.yml` 语义。
2. **Rollout config diff**：新增 prod 流（如 `W5-A-PROD-RELEASE-STREAM-v0.1`）与 `rollout_pipeline_config.json` / `rollout_streams/*` 增量；是否 retro 改写 `W4-A-PILOT-RELEASE-STREAM-v0.1` 或 W4-A 历史 `run_records/**`。
3. **Gate checklist 勾选情况**：Shadow / Canary / Rollback（及 promote）gate 是否与 `W4-A_gate_checklist.md` 范式一致；canary / promote 决策是否引用 **W4-B** index gate 与 **W4-C** gov-metrics JSONL；是否存在「偷偷 release」。
4. **Rollout 记录**：`rollout_trace.jsonl`、`shadow_state.json`、`rollback_record`、ART-REL 风格 JSON（`07_art_rel_*` / `08_art_rel_*`）、**CI workflow run id** 与 RUNTIME 子票 Notes 中的证据链接是否可索引、一致、未篡改 W4-A 历史 run。

**Verdict 写入**：结论落本 Memory（§Reviewer Verdict Record）；必要时在各 runtime 子票 Memory 的 **Notes / followups** 追加「Reviewer verdict」引用（**不**改 runtime 子票 `done_definition` 勾选状态——由 Executor / Supervisor 在验收后更新）。

**与 W5-A-REVIEW-02 分界**：第二条 repo / 服务（`W5-A-RUNTIME-02`）的独立 diff 总检 → **W5-A-REVIEW-02**；本票 **至少** 覆盖 RUNTIME-01；若 RUNTIME-02 已 DONE 且纳入同一 Wave 检查点，可在本票附录并列结论，但 **不得** 以本票 `approve` 替代 REVIEW-02 对第二条目标的 sign-off。

## read_set

> 未列出默认不读。暗部脚本 / venv / `.env` / 未授权 checkpoint **禁止**。

### 控制面与票面约束（必读）

| 路径 | 用途 |
|------|------|
| `workflow_v2/30_control_plane/W4-X_control_plane_mvp.md` | Reviewer 职责 · §1.4.1 最小检查清单 · Review lane 完成定义 |
| `workflow_v2/40_ticket_memory/_TEMPLATE_ticket_memory.md` | 字段对账 |
| `workflow_v2/40_ticket_memory/W5-A-K2-ROLLOUT-EXPANSION.memory.md` | 父票 goal / frozen_constraints / 整票 DoD |
| `workflow_v2/40_ticket_memory/W5-A-REVIEW-01__ROLLBACK-GATE-REVIEW.memory.md` | 本票（含 verdict 记录段） |
| `AGENTS.md`、`04_Workflows/HARNESS_CONSTITUTION.md` | 工程红线与憲法 §7 禁区类型 |
| `docs/k2_deployment_governance.md`、`docs/k2_merge_strategy.md` | K-2 prod 流量与合流治理（只读） |

### W5-A runtime 子票 Memory（必读 · 对账 write_set / DoD）

| 路径 | 用途 |
|------|------|
| `workflow_v2/40_ticket_memory/W5-A-RUNTIME-01__FIRST-PROD-CI.memory.md` | 首条 prod CI 契约、Planning 填空、`done_definition`、证据占位 |
| `workflow_v2/40_ticket_memory/W5-A-RUNTIME-02__SECOND-REPO.memory.md` | 第二条目标（**若已交付**则纳入总检；否则只读以确认未越界） |

### CI workflow diff（以 RUNTIME 子票 Planning 填空为准）

| 占位 / 路径 | 用途 |
|-------------|------|
| `<RUNTIME-01_TARGET_WORKFLOW>` | 由 RUNTIME-01 Planning 续卡填入（例 `.github/workflows/service-X-release.yml`） |
| `<RUNTIME-02_TARGET_WORKFLOW>` | 由 RUNTIME-02 Planning 续卡填入（**须 ≠** 首条；仅 RUNTIME-02 已开工时读） |
| `.github/workflows/gov-gate-metrics.yml` | W4-C gov 指标 CI（对照是否被 unauthorized 改动） |
| `.github/workflows/eval-gate-ci.yml` | Shadow nightly 语义（对照是否 silent 变更） |

### Rollout config / runbook / gate

| 路径 | 用途 |
|------|------|
| `workflow_v2/20_pilot/W3-A/rollout_pipeline_config.json` | 试点流 + prod 流增量 |
| `workflow_v2/20_pilot/W3-A/rollout_streams/*`（若存在） | 并行 prod 流配置 |
| `workflow_v2/20_pilot/W3-A/W4-A_rollout_runbook.md` | W4-A 权威 runbook（对照语义） |
| `workflow_v2/20_pilot/W3-A/W5-A_first_prod_ci_runbook.md`（若 RUNTIME-01 已建） | 首条 prod CI SOP |
| `workflow_v2/20_pilot/W3-A/W5-A_second_repo_rollout_runbook.md`（若 RUNTIME-02 已建） | 第二条 SOP |
| `workflow_v2/20_pilot/W3-A_case/W4-A_gate_checklist.md` | Shadow / Canary / Rollback gate 勾选范式 |
| `workflow_v2/20_pilot/W3-B/W4-B_orch_integration.md` | Index / `IMP-AI-READY` gate |
| `workflow_v2/20_pilot/W3-C/ci_gate_wire.md` | PR / nightly / manual 接线 |
| `workflow_v2/20_pilot/W3-C_metrics_schema.md` | `gov-metrics-0.1` schema |

### Run records / 指标 / CI run id

| 路径 | 用途 |
|------|------|
| `workflow_v2/20_pilot/W3-A_case/run_records/**` | **只读**；含 W4-A 历史 + W5-A 新 run id；核对无篡改 |
| `workflow_v2/observability/gov_gate_metrics/*.jsonl` | 治理指标时间序列（canary / promote 决策引用） |
| RUNTIME 子票 Notes / PR 评论 / CI 摘要 | **workflow run id**、可重跑命令、`VERDICT=` / `ok` 语义 |
| `workflow_v2/20_pilot/W3-A_case/07_art_rel_dec.json`、`08_art_rel_exec.json`（若存在） | ART-REL 风格发布记录样例对照 |

### 全局黑板（只读 · 对账 doc-sync 是否遗漏）

| 路径 | 用途 |
|------|------|
| `workflow_v2/00_master_plan.md`（§15.7 等） | W5-A 能力挂点现状 |
| `workflow_v2/90_run_queue.md` | W5-A 各子票 Status/Notes |
| `workflow_v2/99_latest_status.md` | Wave 5 阶段摘要现状 |

### Helpers（只读 · 不验收实现细节以外的范围）

| 路径 | 用途 |
|------|------|
| `workflow_v2/tools/wf_k2_rollout_run.ps1` | 调用链与结构化输出 |
| `workflow_v2/tools/wf_k2_rollout_canary_sim.py` | Cohort 逻辑 |
| `workflow_v2/tools/wf_emit_gov_gate_metrics.ps1` | CI → JSONL emitter |

## write_set

> **Review lane 硬边界**：默认 **不改** 代码、CI、rollout config、run_records、主文档正文。

### 允许

1. **本票 Memory**  
   - `workflow_v2/40_ticket_memory/W5-A-REVIEW-01__ROLLBACK-GATE-REVIEW.memory.md`  
   - 写入 / 更新：**§Reviewer Verdict Record**（verdict、清单勾选、证据索引、后续票建议）。

2. **Runtime 子票 verdict 引用（可选 · 最小增量）**  
   - 在下列文件 **末尾** 追加短段「Reviewer verdict」（引用本票 id + verdict + 日期），**不** 修改其 `done_definition` 勾选、**不** 改 `write_set` 锁定路径：  
     - `workflow_v2/40_ticket_memory/W5-A-RUNTIME-01__FIRST-PROD-CI.memory.md`  
     - `workflow_v2/40_ticket_memory/W5-A-RUNTIME-02__SECOND-REPO.memory.md`（仅当该子票已纳入本票检查范围）

### 禁止（除非尚書省 override + Progress/notes 末尾留痕）

- 任何 `.github/workflows/*`、`workflow_v2/tools/*`、`rollout_pipeline_config.json`、`run_records/**` 内容  
- `workflow_v2/00_master_plan.md`、`workflow_v2/90_run_queue.md`、`workflow_v2/99_latest_status.md`（→ **W5-A-DOCSYNC-01**）  
- `merge_ask_and_k2`、K-2 adapter、G7/G8 正文、暗部 / venv / `.env`  
- 以 Reviewer 身份 **代修** CI、config 或文档（`request_changes` 须开回 **RUNTIME** 或 **DOCSYNC** 票）

## frozen_constraints

### Review lane 不变式（控制面 §2.3）

1. **只读 + verdict**：Review lane **不写** 主代码、**不修** CI、**不修** `00`/`90`/`99` 全局语义；仅产出 verdict 与可执行建议。  
2. **不代 Executor 签收**：不得自行将 RUNTIME 子票 `done_definition` 勾选为完成；`approve` 仅表示 Reviewer 放行进入 doc-sync，非实施验收替代。  
3. **不实现 W4-X §0 Out of Scope**：审查中若发现自动开 chat、自动 merge、deny engine runtime、复杂 reviewer pipeline 等 → `block` 并引用 §0。

### 复用 W4-X §1.4.1 Reviewer 最小检查清单（逐项必填）

| # | 检查项 | 不通过默认 verdict |
|---|--------|-------------------|
| 1 | **Wave 5 越界**：是否引入 §0 Out of Scope 能力 | `block` |
| 2 | **禁止触及范围**：frozen_constraints、G7/G8 语义、prod 流程、暗部、未授权 `tools`/CI | `block` |
| 3 | **读写边界**：diff 是否超出各 RUNTIME 子票 `read_set`/`write_set`；是否擅自改 `00/90/99` | `request_changes` 或 `block` |
| 4 | **doc-sync 完整性**：是否遗漏 DOCSYNC-01 / 挂点更新计划 | `request_changes` |
| 5 | **语义一致性**：实现与 runbook、父票 DoD、K-2 playbook 是否一致 | `request_changes` |
| 6 | **证据与 DoD**：可重跑证据、rollback 记录、无 skeleton 冒充验收 | `request_changes` 或 `block` |

### W5-A rollout 专项（追加）

7. **W4-A 边界**：不得 retro 改写 W4-A DONE 口径、试点流定义、历史 `run_records`。  
8. **渐进交付**：禁止证据显示一次性全量 K-2 主答案或无 flag 全量 promote。  
9. **Gate 对齐**：canary / promote 须有 W4-B + W4-C 引用；override 须有 allowlist + `reason`。  
10. **CHK-W4**：RUNTIME 子票声称开工/完成时，须有 CHK-W4 PASS 或豁免留痕（对账 `90_run_queue`）。  
11. **governance-guard**：若票面要求 guard `allow`，须有 guard 结论索引（`stop_work` → 本票 `block`）。  
12. **第二条目标**：若检查 RUNTIME-02，须核对与 RUNTIME-01 **目标互斥** 与 `diff_from_runtime_01`；**不得** 以 RUNTIME-01 的 `approve` 覆盖 RUNTIME-02 未审查 diff。

## done_definition

> 仅针对 **W5-A-REVIEW-01**（Reviewer 总检切片）。

### Reviewer 必须检查的维度（全部须有记录）

| 维度 | 检查内容 | 证据要求 |
|------|----------|----------|
| **A. CI diff** | 单 workflow 范围、阶段完整（shadow→canary→promote）、rollback/pause/override 钩子 | PR diff / workflow run 日志索引 |
| **B. Rollout config** | 新 `stream_id`、与 W4-A 试点流并存、无 retro | config diff + stream id 列表 |
| **C. Gate checklist** | Shadow / Canary / Rollback（+ promote）勾选与 runbook 一致 | checklist 副本或 PR 评论链接 |
| **D. W4-B / W4-C** | Index 非 unauthorized `missing` 绕过；gov-metrics JSONL 可引用 | 文件路径 + 行号 / job 产物 |
| **E. Rollout 记录** | `rollout_trace`、rollback 审计、CI run id、无篡改 W4-A 历史 | run_records 路径 + run id |
| **F. 控制面清单** | W4-X §1.4.1 六项 | 本票 §Reviewer Verdict Record 逐项勾选 |
| **G. 依赖与边界** | CHK-W4、RUNTIME `write_set`、无 merge adapter 变更 | 子票 Memory + queue 行 |

### `approve` 条件（全部满足）

- §1.4.1 清单 **六项均为通过**（本票记录为 `[x]`）。  
- **W5-A-RUNTIME-01** 子票声称的 `done_definition` 证据（CI run id、rollback、gate 引用、可重跑命令）经 Reviewer **抽样核对一致**。  
- 无 `block` 级禁区触及；无未解释的 prod 全量 promote。  
- 已明确 **W5-A-DOCSYNC-01** 可开工（doc-sync 范围与勿夸大约束已写入 verdict 建议）。

### `request_changes` 时应产出

- **问题清单**：按维度 A–G 编号；每项 **可修复**、指向具体文件/行或缺失证据。  
- **建议承接票**：  
  - CI/config/runbook 缺陷 → 回 **W5-A-RUNTIME-01**（或 RUNTIME-02）补丁，**不开** Reviewer 修 CI。  
  - 仅文档 / 队列 / 战报 → 注记 **W5-A-DOCSYNC-01** 先决条件未满足。  
- **不得** 标 `approve`；**不得** 触发 DOCSYNC 写 `00/90/99` 为 DONE。

### `block` 时应产出

- **阻塞原因**：触禁区类型（憲法 §7）、W4-X §0 越界、无 CHK-W4、guard `stop_work`、retro W4-A、未授权 blanket workflow 变更等。  
- **停工建议**：停止 merge / 停止 doc-sync；须尚書省或 governance-guard 裁決。  
- **后续票建议**：单独开「豁免 + 留痕」或「缩小 write_set 重跑 RUNTIME」票；**不** 在本 Review 票内修代码。

### 本子票完成判定

- [ ] **依赖满足**：**W5-A-RUNTIME-01** 已提交 Review 材料（PR / diff 摘要 / 证据包）；RUNTIME-02 仅在其 DONE 且纳入范围时检查。  
- [ ] **§Reviewer Verdict Record** 已填写：`verdict`、`reviewer`、`date`、§1.4.1 六项、A–G 维度摘要、证据索引。  
- [ ] **Verdict 已传达**：`approve` | `request_changes` | `block` 三者之一；后续票建议已列出（若非常规通过）。  
- [ ] **未越 write_set**：自检无 CI/runtime/`00`/`90`/`99` 改动。  
- [ ] **Doc-sync 门控**：仅当 `verdict=approve` 时，Supervisor 可派发 **W5-A-DOCSYNC-01**。

### 本 planning 产出切片（当前任务）

- [x] 本文 Ticket Memory 落盘，字段齐全  
- [x] 未修改 CI / runtime / tools / `00`/`90`/`99` / run_records

## pending_followups

| 票号 | lane | 说明 |
|------|------|------|
| **W5-A-DOCSYNC-01** | `doc-sync` | `approve` 后回写 `00`/`90`/`99` Wave 5 状态 |
| **W5-A-REVIEW-02** | `review` | `W5-A-RUNTIME-02` 专用第二条目标总检（**不** 与本票合并 sign-off） |
| **W5-A-RUNTIME-01**（补丁） | `runtime` | `request_changes` 时回修首条 prod CI |
| **W5-A-RUNTIME-02**（补丁） | `runtime` | 第二条目标 `request_changes` 时回修 |
| **W5-A-REVIEW-03**（可选） | `review` | 对 **DOCSYNC-01** 产物的文档一致性复审（非必须；见 DOCSYNC-01 `pending_followups`） |

---

## §Reviewer Verdict Record（执行时填写）

> **本段为 Review lane 唯一允许写入的正文增量**（planning 切片可留空模板）。

| 字段 | 值 |
|------|-----|
| **verdict** | `approve` \| `request_changes` \| `block` |
| **reviewer** | （角色/id） |
| **date** | YYYY-MM-DD |
| **scope** | RUNTIME-01 · （可选）RUNTIME-02 |
| **evidence_index** | PR # / workflow run id / `run_records/<id>/` / JSONL 路径 |

### W4-X §1.4.1 清单（执行时勾选）

- [ ] 1. Wave 5 越界  
- [ ] 2. 禁止触及范围  
- [ ] 3. 读写边界  
- [ ] 4. doc-sync 完整性  
- [ ] 5. 语义一致性  
- [ ] 6. 证据与 DoD  

### 维度摘要（A–G）

- **A–G**：（各 1–3 句结论 + 关键链接）

### 后续票建议

- （`approve` 时：派发 DOCSYNC-01；`request_changes`/`block` 时：列回修票号）

---

## 附录 A — 与 RUNTIME / DOCSYNC 分界

| 角色 | 本票 W5-A-REVIEW-01 | W5-A-DOCSYNC-01 |
|------|---------------------|-----------------|
| lane | `review` | `doc-sync` |
| 改 CI/config | **禁止** | **禁止** |
| 改 `00/90/99` | **禁止** | **允许**（approve 后） |
| 产出 | verdict | Wave 5 状态正文 |

---

## 附录 B — 本 planning 产出切片自检

| 检查 | 结果 |
|------|------|
| 未改 CI / runtime / tools / `00`/`90`/`99` / run_records | pass（仅本文） |
| 对齐 W4-X §1.4.1 与 Review lane §2.3 | pass |
| 明确 Review 不写代码 / 不修 CI / 不修文档 | pass（frozen_constraints §1） |
| 与 W5-A 父票、RUNTIME-01/02 Memory 引用一致 | pass |
| `approve` / `request_changes` / `block` 条件与后续票建议 | pass（done_definition） |

**规划切片签收**：Ticket Memory 落盘即视为本 **planning** 切片可交付；Review 执行须待 RUNTIME-01 提交证据包后另派工。
