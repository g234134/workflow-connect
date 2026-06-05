# Ticket Memory — W5-A-DOCSYNC-01

> **用途**：W5-A K-2 rollout **Wave 5 状态 doc-sync**；在 `W5-A-RUNTIME-*` 与 **W5-A-REVIEW-01** 完成后，将 prod rollout / CI / 多 cohort / 多 repo 的**已发生事实**回写 `00`/`90`/`99`，区分 W4-A 与 W5-A，不夸大进度。  
> **父票**：`workflow_v2/40_ticket_memory/W5-A-K2-ROLLOUT-EXPANSION.memory.md`  
> **前置 Review**：`workflow_v2/40_ticket_memory/W5-A-REVIEW-01__ROLLBACK-GATE-REVIEW.memory.md`（**硬依赖**：`verdict=approve`）  
> **控制面**：`workflow_v2/30_control_plane/W4-X_control_plane_mvp.md`（§1.5 Doc-sync · §2.4 Doc-sync lane）  
> **模板**：`workflow_v2/40_ticket_memory/_TEMPLATE_ticket_memory.md`  
> **本文件产出切片**：planning（仅 Ticket Memory；**无** `00`/`90`/`99` 正文变更）

---

## ticket

- id: **W5-A-DOCSYNC-01**
- title: **W5-A rollout 结果 · 00/90/99 doc-sync**

## lane

- lane: **doc-sync**

## priority

- priority: **P1**（主线文档回写；低于 REVIEW-01 的 `P0` 门控——须 Reviewer `approve` 后方可开工）

## mode

- mode: **doc-sync**（仅回写 v2 控制面挂点；**不**补 runtime 功能、**不**替 Reviewer 修 CI）

## goal

在 **W5-A-RUNTIME-01**（及本票 `read_set` 中已 **DONE** 且经 **W5-A-REVIEW-01** `approve` 的 W5-A runtime 子票）完成后，将「真正 prod rollout / CI / multi-cohort / multi-repo 的落地结果」写成 **一等公民**，统一回写：

| 目标文件 | 回写内容（要点） |
|----------|------------------|
| `workflow_v2/00_master_plan.md` | **§15.7**（或等价 Wave 5 小节）：W5-A 能力挂点——首条 prod CI、rollout 流 ID、与 W4-A 分界；**草案 → 已实施** 仅在有 RUNTIME 证据时升格 |
| `workflow_v2/90_run_queue.md` | 各 **W5-A** 子票（父票、RUNTIME-01、REVIEW-01、本票等）**Status / Notes**；**不删历史行** |
| `workflow_v2/99_latest_status.md` | **Wave 5 战报** 一条：本轮发生了什么、证据索引、阻塞、下一步 |

**原则**：

- 以 **Reviewer approve** + **runtime 可索引证据**（CI run id、run_records、gate JSONL）为唯一事实来源。  
- **W4-A** 保持 **DONE（minimal v1）** 口径；**W5-A** 单独叙述 prod/CI/扩面，**不 retro** W4-A。  
- **RUNTIME-02** 未完成时，在 `90`/`99` 标 **IN_PROGRESS / BLOCKED / NOT_STARTED**，**不得** 写成 DONE。  
- 第二条 repo 的完整战报若 REVIEW-02 尚未 `approve` → 由 **W5-A-DOCSYNC-02** 承接，本票仅可写「第二条进行中/未开工」状态句。

## read_set

> 未列出默认不读。

### Reviewer verdict 与 W5-A Memory（必读）

| 路径 | 用途 |
|------|------|
| `workflow_v2/40_ticket_memory/W5-A-REVIEW-01__ROLLBACK-GATE-REVIEW.memory.md` | **§Reviewer Verdict Record** · 须 `approve` |
| `workflow_v2/40_ticket_memory/W5-A-K2-ROLLOUT-EXPANSION.memory.md` | 父票 goal / 整票 DoD / W4-A vs W5-A 对照 |
| `workflow_v2/40_ticket_memory/W5-A-RUNTIME-01__FIRST-PROD-CI.memory.md` | 首条 prod CI 填空、证据、`done_definition` |
| `workflow_v2/40_ticket_memory/W5-A-RUNTIME-02__SECOND-REPO.memory.md` | 第二条状态（只读对账；未完成则不改 DONE） |
| `workflow_v2/30_control_plane/W4-X_control_plane_mvp.md` | Doc-sync lane 边界 |

### 实施产物（只读 · 摘录进 00/90/99）

| 路径 | 用途 |
|------|------|
| RUNTIME-01 PR / diff 摘要 | CI workflow 变更事实 |
| `<RUNTIME-01_TARGET_WORKFLOW>` | Planning 填入的 workflow 路径 |
| `<RUNTIME-01_PROD_STREAM_ID>` | 例 `W5-A-PROD-RELEASE-STREAM-v0.1` |
| `workflow_v2/20_pilot/W3-A/rollout_pipeline_config.json` | prod 流配置段 |
| `workflow_v2/20_pilot/W3-A/W5-A_first_prod_ci_runbook.md`（若存在） | SOP 引用 |
| `workflow_v2/20_pilot/W3-A_case/run_records/**` | 新 run id、trace、rollback（**不** 改内容） |
| `workflow_v2/observability/gov_gate_metrics/*.jsonl` | gate 引用摘要 |
| `workflow_v2/20_pilot/W3-A_case/W4-A_gate_checklist.md` | 勾选状态对照 |

### 当前全局黑板（必读 · 回写前基线）

| 路径 | 用途 |
|------|------|
| `workflow_v2/00_master_plan.md` | 现有 §15 / §15.7 Wave 5 挂点 |
| `workflow_v2/90_run_queue.md` | 现有 W5-A 各行 Status |
| `workflow_v2/99_latest_status.md` | 现有 Wave 5 展望 / 草案段 |

### 制度（边界确认 · 只读）

| 路径 | 用途 |
|------|------|
| `docs/k2_deployment_governance.md` | 引用 playbook Phase，不复制全文 |
| `workflow_v2/20_pilot/W3-A/W4-A_rollout_runbook.md` | W4-A 分界引用 |

## write_set

> **仅** 下列三份全局黑板；**禁止** 改 CI / runtime / tools / run_records。

### 允许

| 路径 | 允许操作 |
|------|----------|
| `workflow_v2/00_master_plan.md` | **§15.7**（或 Supervisor 指定 Wave 5 小节）：增补/修订 W5-A **已实施** 能力描述；保留 W4-A 分界表述 |
| `workflow_v2/90_run_queue.md` | W5-A 相关票 **Status / Notes** 更新；**append-only** 式 Notes，不删历史 |
| `workflow_v2/99_latest_status.md` | **文末 append** 一条 Wave 5 战报（日期、事实、证据索引、下一步） |

### 允许（本票 Memory）

- `workflow_v2/40_ticket_memory/W5-A-DOCSYNC-01__WAVE5-STATUS.memory.md`（本文 · §Doc-sync Record）

### 禁止

- `.github/workflows/*`、`workflow_v2/tools/*`、`rollout_pipeline_config.json`、`run_records/**` 任何内容  
- `workflow_v2/40_ticket_memory/W5-A-REVIEW-01__ROLLBACK-GATE-REVIEW.memory.md` 的 §Reviewer Verdict Record（Reviewer 独占）  
- RUNTIME 子票 `done_definition` 勾选（由 Executor / Supervisor 更新）  
- 暗部、venv、`.env`、G7/G8 正文语义变更  

## frozen_constraints

### Doc-sync lane 不变式（控制面 §2.4）

1. **只写已发生事实**：无 CI run id / 无 Reviewer `approve` / 无 rollback 证据 → **不得** 写「已完成 prod rollout」。  
2. **不夸大进度**：禁止将 planning 草案、占位、RUNTIME 未完成子票标为 **DONE**。  
3. **W4-A vs W5-A 分离**：  
   - W4-A：`W4-A-PILOT-RELEASE-STREAM-v0.1` · 试点 minimal v1 · **不改 prod CI** · **DONE** 口径不变。  
   - W5-A：prod 流 ID、首条 prod CI workflow 名、cohort / 多 repo 状态 **单独叙述**。  
4. **不替 Reviewer / Executor**：doc-sync **不** 修 CI、**不** 补 gate 勾选、**不** 将 `request_changes` 写成通过。  
5. **历史保护**：`90_run_queue` **不删除** 既有行；`99` 战报 **append**，不覆盖旧条目的历史事实。  
6. **RUNTIME-02 门控**：第二条 repo 仅当 RUNTIME-02 DONE + REVIEW-02 `approve` 后，方可于 `00`/`99` 写「第二条已完成」；否则用 **IN_PROGRESS / NOT_STARTED / BLOCKED** 等准确状态。  
7. **父票整票 DoD**：本票 **不** 宣称 W5-A-K2-ROLLOUT-EXPANSION 整票完成（多 cohort 全阶梯、第三 repo 等见父票 `pending_followups`）。  
8. **禁区**：憲法 §7 类型、金鑰原文、`AGENTS.md` 红线。

## done_definition

### `00_master_plan.md` 必须达到

- [ ] **§15.7**（或等价小节）存在 **Wave 5 / W5-A** 挂点，且包含：  
  - 与 **W4-A** 的对照句（试点 vs prod CI）；  
  - 首条 prod 流 `stream_id`（与 RUNTIME-01 Planning 一致）；  
  - 首条 prod CI workflow 逻辑名（无则标「Planning 待填」**不得** 标已实施）；  
  - 多 cohort / 多 repo：**仅写已完成部分**，未完成标「待 W5-A-RUNTIME-02+」。  
- [ ] 无「W5-A 整票 DONE」除非父票 `done_definition` 全部满足（本票 **通常不满足**）。

### `90_run_queue.md` 必须达到

- [ ] 至少更新行：**W5-A-K2-ROLLOUT-EXPANSION**、**W5-A-RUNTIME-01**、**W5-A-REVIEW-01**、**W5-A-DOCSYNC-01**（本票）。  
- [ ] **Status** 与事实一致（例：RUNTIME-01=`DONE` 仅当有证据；REVIEW-01=`DONE` 仅当 `approve`；DOCSYNC-01 本票执行后=`DONE`）。  
- [ ] **Notes** 含：CI run id 索引、Review verdict 引用、阻塞/下一步一句。  
- [ ] **W5-A-RUNTIME-02** 行：未完成 **不得** `DONE`。

### `99_latest_status.md` 必须达到

- [ ] **文末** 新增一条 **Wave 5** 战报（含日期）。  
- [ ] 战报含：**执行摘要**、**关键证据**（workflow run id / run_records 路径）、**与 W4-A 分界**、**阻塞**、**下一步**。  
- [ ] 语气：**不过度承诺**（无 fail-on-deny 全 PR、无 Control Plane 自动调度，除非已另票实施）。

### 本子票完成判定

- [ ] **前置**：**W5-A-REVIEW-01** `verdict=approve`（§Reviewer Verdict Record 可索引）。  
- [ ] **三文件** `00`/`90`/`99` 已按上表更新，且与 runtime / review 证据 **一致**。  
- [ ] **自检**：未改 CI / tools / config / run_records；未将未完成子票标 DONE。  
- [ ] **（可选）W5-A-REVIEW-03**：对 doc-sync diff 的文档一致性复审 `approve`（非必须；见 `pending_followups`）。

### 本 planning 产出切片（当前任务）

- [x] 本文 Ticket Memory 落盘，字段齐全  
- [x] 未修改 `00_master_plan.md` / `90_run_queue.md` / `99_latest_status.md`

## pending_followups

| 票号 | lane | 说明 |
|------|------|------|
| **W5-A-DOCSYNC-02** | `doc-sync` | RUNTIME-02 + REVIEW-02 `approve` 后第二条 repo 战报与 `00` 多 repo 挂点 |
| **W5-A-REVIEW-03**（可选） | `review` | 对本票 `00`/`90`/`99` diff 做文档一致性复审 |
| **W5-A-K2-ROLLOUT-EXPANSION** | planning / runtime | 父票剩余 DoD：多 cohort 全阶梯、第三 repo、Dashboard 等 |
| **W5-A-2 · Dashboard / Alert** | 占位 | 父票 pending |
| **CHK-W4** | — | 若战报引用 CHK 结论，须与 `90` 一致 |

---

## §Doc-sync Record（执行时填写）

> **本段为 doc-sync 执行摘要**（planning 切片可留空模板）。

| 字段 | 值 |
|------|-----|
| **executor** | （角色/id） |
| **date** | YYYY-MM-DD |
| **review_ref** | W5-A-REVIEW-01 · verdict=approve · date |
| **runtime_scope** | RUNTIME-01 · （RUNTIME-02 状态一句） |

### 回写锚点

| 文件 | 小节 / 行 | 变更摘要 |
|------|-----------|----------|
| `00_master_plan.md` | §15.7 | |
| `90_run_queue.md` | W5-A-* 行 | |
| `99_latest_status.md` | 战报条目 id/日期 | |

### 证据索引（战报用）

- CI run id：  
- run_records：  
- Review verdict：  

---

## 附录 A — 00 / 90 / 99 回写要点（执行清单）

### `00_master_plan.md` · §15.7 建议结构

1. **状态行**：W5-A · 首条 prod CI · （第二条 repo 状态）  
2. **与 W4-A 分界**（1–2 句）  
3. **已交付**：stream id、workflow 逻辑名、shadow/canary/promote 一句  
4. **未交付**（父票）：全阶梯 cohort、第三 repo、Control Plane 集成等 → 指向 `90` 票号  

### `90_run_queue.md` · 建议 Status 枚举

| Status | 含义 |
|--------|------|
| `DONE` | 本子票 DoD 满足且有证据 |
| `IN_PROGRESS` | 已开工未完成 |
| `BLOCKED` | 有阻塞条 |
| `NOT_STARTED` | 未派工 |
| `FUTURE` / `IDEA` | 父票规划态 |

### `99_latest_status.md` · 战报模板（append）

```markdown
### Wave 5 · W5-A doc-sync（YYYY-MM-DD）

- **范围**：首条 prod CI（W5-A-RUNTIME-01）；Review：W5-A-REVIEW-01=approve
- **事实**：（1–3 句）
- **证据**：workflow run id …；run_records/…
- **与 W4-A**：试点 minimal v1 不变；prod 流 …
- **阻塞**：（无则写「无」）
- **下一步**：RUNTIME-02 / 多 cohort / …
```

---

## 附录 B — 与 REVIEW / RUNTIME 分界

| 顺序 | 票 | 产出 |
|------|-----|------|
| 1 | W5-A-RUNTIME-01 | CI + config + 证据 |
| 2 | W5-A-REVIEW-01 | `approve` |
| 3 | **W5-A-DOCSYNC-01** | `00`/`90`/`99` |
| 4 | W5-A-RUNTIME-02 | 第二条（可选并行规划，doc-sync 另票） |
| 5 | W5-A-REVIEW-02 | 第二条 review |
| 6 | W5-A-DOCSYNC-02 | 第二条战报 |

---

## 附录 C — 本 planning 产出切片自检

| 检查 | 结果 |
|------|------|
| 未改 `00`/`90`/`99` 正文（仅本文） | pass |
| 未改 CI / runtime / tools / run_records | pass |
| 硬依赖 REVIEW-01 `approve` | pass（frozen_constraints / done_definition） |
| W4-A vs W5-A 分离、不夸大、未完成不写 DONE | pass |
| 对齐 W4-X Doc-sync lane 与 W5-A 父票 | pass |
| 与 RUNTIME-02 的 DOCSYNC-02 分界 | pass（pending_followups） |

**规划切片签收**：Ticket Memory 落盘即视为本 **planning** 切片可交付；doc-sync 执行须待 REVIEW-01 `approve` 后另派工。
