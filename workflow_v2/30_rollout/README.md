# W3-A — Rollout / Canary 总控（`30_rollout/`）

> **票号**：**W3-A-ORCH**（编排骨架；**不**实现 rollout pipeline）  
> **权威索引**：`workflow_v2/00_master_plan.md` §13.1、§13.4–§13.6  
> **邻接只读**：战车根 `00_master_plan.md` §4.8 · `docs/k2_deployment_governance.md`（**非** v2 正文）  
> **案卷落点**：`workflow_v2/20_pilot/W3-A_case/`  
> **状态**：ORCH 骨架已落盘（2026-05-27）；shadow／canary **施工票仍 TODO**

---

## 1. 适用范围

| 项 | 说明 |
|----|------|
| **默认业务链** | **K-2 × ask**（v2 Wave 3 导入试点默认组合；非唯一合法路径） |
| **Wave 3 最低完成** | Phase 1 **shadow** + Phase 2 **internal canary** 各 ≥1 次；有 run 记录 + **ART-REL** 风格案卷（见 `artifact_schema_w3a.md`） |
| **本目录职责** | phase 映射、边界、allowed_paths、案卷 schema、env 清单占位；**不含**可执行 rollout 脚本 |
| **out-of-scope** | 远端 **prod** 全自动 rollout；K-2 **Phase 3+** 扩面；完整 release gate；改 merge adapter／production deploy |

---

## 2. Phase 定义（W3-A 仅 Phase 1–2）

与根 plan §4.8、`docs/k2_deployment_governance.md` §4 **对齐索引**；v2 施工**不宣称**已完成远端 prod Phase 1 七日窗。

| v2 Phase | 邻接 K-2 Phase | 名称 | 用户可见 | K-2 参与 | W3-A 最低观测 |
|----------|----------------|------|----------|----------|----------------|
| **P1** | Phase 1 | **Shadow** | 100% **ask** 主答案 | 异步复制 + `merge_ask_and_k2`（`primary_source=ask`）；结果写 spool／export | **≥7 自然日**连续观测（§13.4 + 邻接 playbook §4.1）；每日指标索引；**≥1** 次可回溯 run 案卷 |
| **P2** | Phase 2 | **Internal canary** | 内部 cohort **5–10%** 真实 K-2 主答案 | `primary_source=k2`（cohort 内）；仍经 **单点** `merge_ask_and_k2` | **≥1** 次试点窗口（建议 ≥7 天再讨论升格）；**ART-REL-DEC** + **ART-REL-EXEC** |
| — | Phase 3+ | Controlled expansion / full switch | — | — | **Wave 4**（`00` §13.6）；**禁止** W3-A 子票宣称 |

**环境口径（v2 试点）**

| Phase | 允许执行环境 | 禁止 |
|-------|--------------|------|
| P1 Shadow | **dev**、**staging**、**远端等价环境**（与 prod 拓扑相近、**非** prod 全量自动切换） | prod 用户-facing 改主答案路径；未批文 prod shadow |
| P2 Canary | 同上 + 已定义的 **internal cohort**（`env/` + `canary_env.md`） | 全域 prod 流量；比例 **>10%**；远端 prod 无人值守 rollout |

---

## 3. 默认业务链边界

详见 **`boundary_k2_ask.md`**；摘要如下。

| 维度 | 约定 |
|------|------|
| **默认 entrypoint** | 用户请求进入 **ask 主路径**（HTTP `/api/ask` 或等价 ask pipeline）；**H 线** `build_rooted_context` → selector → retrieve → answer 为 user-facing 主权 |
| **K-2 挂接点** | ask 响应路径**之后／并行**：`core/k2_merge_adapter.merge_ask_and_k2`（`ASK_MERGE_INTERFACE`）；shadow 复制经 `k2_prod_shadow_worker_cli` / spool（邻接根 plan §4.8 Wave 1 hook） |
| **非 entry** | 不得将 `run_k2_flow` 作为未批准时的默认 user-facing 入口；不得在 ask 图内散落 K-2 分支（邻接 `k2_deployment_governance.md` §1 单点切换） |
| **Shadow 环境** | dev／staging／远端等价；对照 ask 主答案 + metadata diff；索引 spool／export，**不**改 production merge 逻辑 |
| **Canary 环境** | internal **5–10%** cohort；`target_audience_or_env` 逻辑名（无 secret）；**非** prod 全量 |
| **Rollback / obs（名称索引）** | `eval_ci_check` · P+ nightly export · `k2_shadow_spool` / shadow JSONL · `compare_shadow_profiles` · `tests.test_k2_ask_shadow` · `tests.test_k2_merge_adapter` · AGENTS **Monitoring Graph L0**（`monitoring_executor` / `ibridge_v0.monitoring_*`，**非** selector／SLO）· `wf_gov_gate` / `wf_check_cross_ref`（W3-C 软依赖） |

**与 W2-1 范式**：案卷 IMP 轨可沿用 `imp_state` + **ART-REL-DEC**／**ART-REL-EXEC**；本链为 **CHG-OBS-ONLY**／rollout 观测，**不**等同 G8-RECON 文档 authority 发布。

---

## 4. 与 G8 Release / G10 NBT 的关系（只索引）

| 治理 | 本主线用法 | 索引路径 |
|------|------------|----------|
| **G8-5 Release** | canary／shadow **收口**用 **ART-REL-DEC**、**ART-REL-EXEC**（及可选 **ART-REL-OBS**）；字段契约见 `artifact_schema_w3a.md`，**不**复制 G8 全文 | `10_governance/G8_artifact_contract/50_release_owner.md` |
| **G10-2 NBT** | spool／`eval_ci_check`／monitoring L0／queue `DONE` **不可**单独作为 canary 批准或 IMP 前进依据；须 owner + 命令／案卷证据链 | `10_governance/G10_governance_rulebook/20_no_blind_trust.md`（**NBT-OBS-***、**NBT-GC-07** 等） |
| **G7 IMP** | 可选登记 `IMP-OBSERVING` 观测窗；**不**改 G7 状态机正文 | `10_governance/G7_state_machine/`（只读引用） |

---

## 5. 子票施工摘要（边界 / DoD / allowed_paths）

完整表见 **`allowed_paths.md`** 与 `20_pilot/W3-A_case/README.md`。

| 票 | 目标（DoD 摘要） | 禁区（硬） | 长上下文 |
|----|------------------|------------|----------|
| **W3-A-SHADOW-PILOT** | K-2×ask **shadow** 连续 **≥7 日**；≥1 份 `shadow_run_*.md` + 指标索引；对照 ask 主答案 | prod 主答案切换；改 merge adapter；`.env` 原文 | 否（窄 diff） |
| **W3-A-REMOTE-ENV** | 远端／staging **env 清单** + smoke 描述（无密钥）；cohort 逻辑名 | venv 树；secret；远端 prod 自动 rollout | 否 |
| **W3-A-CANARY-PILOT** | **1 次** internal canary（5–10%）设计与执行记录；`**_art_rel_*.json` | Phase 3+；远端 prod 自动 rollout；改 adapter | 否 |

**依赖链**（`90_run_queue.md`）：`W3-A-ORCH` → `W3-A-SHADOW-PILOT` → `W3-A-CANARY-PILOT`；`W3-A-REMOTE-ENV` ∥ shadow，**硬依赖** canary 前完成。

---

## 6. 本目录文件索引

| 文件 | 用途 |
|------|------|
| `README.md` | 本总控说明 |
| `boundary_k2_ask.md` | 默认链 entry／环境／rollback 索引 |
| `phase_map_k2_ask.md` | K-2×ask 节点 ↔ shadow／canary 观察点 |
| `artifact_schema_w3a.md` | W3-A 案卷 ART-REL 扩展字段（非 G8 正文） |
| `allowed_paths.md` | 各子票 allowed_paths／禁区清单 |
| `env/README.md` | REMOTE-ENV 环境清单模板占位 |

---

## 7. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | **W3-A-ORCH**：初版骨架；Phase 1–2 边界；三子票摘要 |
