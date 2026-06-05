# Wave 7 – ORCH-PIPELINE-WIRE（v0.1）

> **票号**：`ORCH-PIPELINE-WIRE`  
> **性质**：implementation ticket  
> **范围**：Wave 6 四模块按冻结顺序硬接线到 orchestrator  
> **依据**：Wave 6 ENVELOPE-V2 / MANIFEST-V2 / QA-M1 已冻结实现  
> **不做**：新增 QA 规则；修改 envelope/manifest writer 业务规则

---

## 0. 背景

现有 E2E 测试存在 ad-hoc 归一化缝隙（如 ENRICH 场景的 `enrichment.present` gate 在 test layer）。本票把 Wave 6 四个模块 **按冻结顺序硬接线** 到 orchestrator，消除该缝隙。

---

## 1. 目标

把 Wave 6 四个模块 **按冻结顺序硬接线** 到 orchestrator，消除 E2E 测试里的 ad-hoc 归一化缝隙（如 ENRICH `present` gate）。

---

## 2. 输入 / 输出

### 2.1 输入

orchestrator 内部 stage 上下文。

### 2.2 输出

各 stage 结构化结果；ENRICH 路径在 **orchestrator 层** 统一做 manifest 输入归一化（从测试层下沉）。

单一入口：

```text
run_wave6_pipeline(job_record, raw_files) -> {envelopes, manifest, report, qa}
```

---

## 3. Done 条件（checklist）

- [ ] 单一函数/类：`run_wave6_pipeline(job_record, raw_files) -> {envelopes, manifest, report, qa}`。
- [ ] ENRICH：`enrichment.present` 转换只在 pipeline wire 一处实现。
- [ ] 禁止 orchestrator 绕过 schema 校验直接改 manifest 行。
- [ ] 与 `test_wave6_e2e_smoke` 行为等价（可 refactor 测试调用 pipeline）。
- [ ] 性能：单 job 千行 manifest 内存可接受（不做流式，Wave 7 不优化）。

---

## 4. 边界（明确不做）

- 不新增 QA 规则
- 不改 envelope/manifest writer 业务规则

---

## 5. 依赖 / 前置

- Wave 6 ENVELOPE-V2 / MANIFEST-V2 / QA-M1 已冻结实现

---

*Wave 7 implementation ticket · `04_Workflows/WAVE7_ORCH_PIPELINE_WIRE_v0.1.md`*
