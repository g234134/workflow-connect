# 03 Parallel Execution Rules — Workflow v2

> **产物票**：E1-5  
> **配套**：`02_dependency_map.md`、`90_run_queue.md`

---

## 1. 总则

1. **总控 chat 不写各模块正文**（`10_governance/G*` 下规格文件内容由施工 chat 填写）。  
2. **施工 chat** 只改**指派模块子目录** + 本票在 `90_run_queue.md` 的 **Status / Notes** 栏。  
3. **检查员 chat** 只做**只读**盘点与风险摘要；发现冲突**只标记**，不扩写、不代写正文。  
4. 并行以 **不同文件 / 不同子目录** 为界；同文件禁止双 chat 同时施工。

---

## 2. 三角色定义

### 2.1 总控（Orchestrator）

| 项 | 规则 |
|----|------|
| **可改** | `00_master_plan.md`、`02_dependency_map.md`、`03_parallel_execution_rules.md`、`90_run_queue.md`（结构与新票）、`99_latest_status.md` |
| **可做** | 挂票、调依赖、Wave 出口判定、合并冲突时的**队列**裁决建议 |
| **禁止** | 撰写或润色 G6/G7/G8/G10 模块正文；将未验收模块标为「已定稿」 |

### 2.2 施工（Worker / 模块 chat）

| 项 | 规则 |
|----|------|
| **可改** | 队列指派之 `Output File` 路径；`90_run_queue.md` **本票一行**的 Status、Notes |
| **可做** | 按票写模块 md；在 Notes 引前置票与对账项 |
| **禁止** | 改他模块目录；改总控五件套；删队列历史行；无依赖前提下标 `DONE` |

**Status 更新约定**：

- 开工 → `DOING`  
- 阻塞 → `BLOCKED`（Notes 写原因与所需前置）  
- 完工 → `DONE`（Notes 写验收要点，**不**贴 secret）

### 2.3 检查员（Checker）

| 项 | 规则 |
|----|------|
| **可做** | 只读扫描；向 `99_latest_status.md` 或对应票 Notes 写**风险摘要** |
| **禁止** | 修改模块正文；将风险修复扩成新 scope；替施工标 `DONE` |

**风险标记格式（建议）**：

```text
[RISK] <ID> <severity:低|中|高> <一句话> → 建议: <仅指向票号或文件，不代写>
```

---

## 3. 并行发车矩阵（Wave 1）

| 批次 | 可同发车票 | 前提 |
|------|------------|------|
| **T0** | — | E1-1～E1-5 均 `DONE` |
| **T1a** | G6-1, G7-1, G8-1, G8-2, G8-3, G8-4, G8-5 | T0 |
| **T1b** | （G10-1 可与 T1a 并行草案；定稿前建议 G6-1 可读） | T0 |
| **T2a** | G6-2 | G6-1 `DONE` |
| **T2b** | G7-2, G7-3 | G7-1 `DONE` |
| **T3** | G10-2 | G10-1 `DONE` |

**不可并行示例**：

- G6-2 与 G6-1 同时写 `20_allowed_actions.md`  
- 两施工 chat 同改 `G7_state_machine/10_states.md`

---

## 4. 冲突处理（只标记，不扩 scope）

| 冲突类型 | 处理 |
|----------|------|
| **命名冲突**（同义不同名） | checker 写 `[RISK]`；开**对账票**或由总控在 Notes 冻结术语表（不直接改正文） |
| **文件冲突**（同路径双改） | 立即 `BLOCKED` 相关票；总控裁决保留方 |
| **依赖环** | 总控更新 `02_dependency_map.md`；施工停工直至 E1-4 修订 |

---

## 5. 与 Cursor Subagents 对齐（索引）

| 情境 | 做法 |
|------|------|
| 单模块、单目录多文件 | 可直派 `implementation-worker`（见 `AGENTS.md` Cursor Subagents） |
| 触制度档 / 多模块捆绑 | 必经 `governance-guard` |
| v2 模块正文 | 视为**施工**；总控轮次用主 chat 或 coordinator，**不**用 worker 改 `90` 全局结构 |

---

## 6. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | E1-5 初版：三角色 + 并行矩阵 + 冲突规则 |
