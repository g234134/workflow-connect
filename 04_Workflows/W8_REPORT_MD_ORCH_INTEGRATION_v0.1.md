# Wave 8 – REPORT-MD-ORCH（v0.1）

> **票号**：`REPORT-MD-ORCH`  
> **性质**：implementation ticket  
> **范围**：Wave 7 lifecycle **finalize 之后** 可选生成 `report.md` 并刷新 `report_md` ref  
> **依据**：`wave7_artifact_storage` 占位；`wave7_orch_job_lifecycle` 回传；R4 四件套 refs  
> **不做**：改编排阶段顺序默认值（须配置显式开启）、invoice/ack、bridge 写入

---

## 0. 背景

Artifact store 已在 `{job_id}/report.md` 写入占位并预留 `w6://.../report_md`。需在 `report.json` 落盘成功后，用 Wave 8 渲染器替换占位，并把 `display_context` 从 lifecycle 回传组装传入。

---

## 1. 目标

配置项 **`render_report_md: bool`（默认 false）** 为 true 时：storage finalize 末尾调用渲染器，原子写 `report.md`，回传 `artifacts.report_md_ref`。

---

## 2. 输入 / 输出

| 输入 | 说明 |
|------|------|
| 内存或磁盘 `report.json` | Wave 7 刚写入版本 |
| `JobRunContext` / lifecycle 回传 | `completion_variant`、`status`、`artifact_refs` |
| 可选 `client_ref` | 来自 `job_record` |

| 输出 | 说明 |
|------|------|
| `report.md` 文件 | 覆盖 Wave 7 占位 |
| 扩展 `run_wave7_job` 回传 | `artifacts.report_md_ref`（已有 kind 时更新） |
| 渲染失败 | `ok` 可仍为 true（job 已成功），但 `report_md_render.ok=false` 侧车键 + 日志；**不回滚** `report.json` |

---

## 3. Done 条件

- [ ] 默认关闭：不开配置时行为与 Wave 7 完全一致。  
- [ ] 开启后 E2E：Tier-A 或专用集成测断言 `report.md` 非占位、含 `summary.qa_status` 字样。  
- [ ] 幂等重跑：同 fingerprint 不重复渲染（或检测 hash 后 skip）。  
- [ ] 失败隔离：渲染异常不删除 manifest/report.json。  
- [ ] `w6://delivery/{job_id}/report_md` 与磁盘文件同步登记。

---

## 4. 边界

- 不将 Markdown 文本写入 `report.json`。  
- 不阻塞 Wave 7 Done  solely 因 Markdown 失败（可配置 `strict_report_md`，默认 false）。  
- 不实现远程 object store 上传。

---

*Wave 8 implementation ticket · `04_Workflows/W8_REPORT_MD_ORCH_INTEGRATION_v0.1.md`*
