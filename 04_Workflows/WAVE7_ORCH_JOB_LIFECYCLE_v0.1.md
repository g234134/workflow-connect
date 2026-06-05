# Wave 7 – ORCH-JOB-LIFECYCLE（v0.1）

> **票号**：`ORCH-JOB-LIFECYCLE`  
> **性质**：implementation ticket  
> **范围**：单 job 编排器与状态机  
> **依据**：R3 §G.7（`completed_with_failures` 语义）  
> **不做**：多 job 队列/worker pool、BASIC→ENRICH 升级链、Phase 6.5 `delivery.status` 实体、distributed lock

---

## 0. 背景

Wave 6 模块层可单 job 跑通，但尚无任务级编排控制、job 状态机、失败处理与重试策略。本票设计并实现 **单 job 编排器与状态机**。

---

## 1. 目标

设计并实现 **单 job 编排器与状态机**：串联 intake（可选）→ raw 加载 → envelope → manifest → report summary → QA-M1 → 落盘 finalize，并定义失败/重试/阻塞语义。

---

## 2. 输入 / 输出

### 2.1 输入

runner 构造的 `job_record` + `raw_files` 或 artifact store 中的 checkpoint。

### 2.2 输出

终态 `job_record.status` ∈ `{pending, running, blocked, done, failed}`（及 R3 规定的 `completed_with_failures` 作为 done 子类型或映射）；结构化回传：

```text
{ok, status, stage, artifacts, qa, retryable, message}
```

---

## 3. Done 条件（checklist）

- [ ] 状态迁移表文档化：`PENDING→RUNNING→DONE|FAILED|BLOCKED`；QA M1 P0 失败 → `FAILED` 或 `BLOCKED`（可配置，默认 FAILED 不可 finalize）。
- [ ] 阶段级 checkpoint：manifest 已写但 report 失败时可 **从 report 步重试**，不重算 envelope（单测证明）。
- [ ] 重试策略：幂等写 + 最大重试次数 + 不可重试错误码（SKU 冲突、schema 硬失败）。
- [ ] `completed_with_failures`：当 manifest 有 rejected 行但 M1 通过时设置（对齐 R3 §G.7 语义，即使 Wave 7 未开 M2）。
- [ ] Orchestrator 单测 + 一条 **fake-I/O** 集成测覆盖 happy path 与 M1 失败 path。

---

## 4. 边界（明确不做）

- 不做多 job 队列调度/worker pool
- 不做 BASIC→ENRICH 升级链（§I）
- 不写 Phase 6.5 `delivery.status` 实体
- 不实现 distributed lock

---

## 5. 依赖 / 前置

- `RUNNER-ENTRY-JOB-INPUT`
- `ARTIFACT-STORAGE-PATH-GOV`
- `ORCH-PIPELINE-WIRE`
- `REPORT-SUMMARY-PRODUCER`

---

*Wave 7 implementation ticket · `04_Workflows/WAVE7_ORCH_JOB_LIFECYCLE_v0.1.md`*
