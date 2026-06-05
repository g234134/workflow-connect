# Wave 7 – ARTIFACT-STORAGE-PATH-GOV（v0.1）

> **票号**：`ARTIFACT-STORAGE-PATH-GOV`  
> **性质**：implementation ticket  
> **范围**：Wave 7 job 工件落盘、路径治理、幂等重跑与错误回收  
> **依据**：R4 `w6://delivery/{job_id}/{kind}`；`gov_paths`  
> **不做**：tar/zip deliverables 打包、Chariot_Registry 注册、远程 object store

---

## 0. 背景

Wave 6 模块层产出主要在内存；尚无 envelope/manifest/report 的正式落盘与路径治理。本票统一管理 Wave 7 job 的 **工件落盘**。

---

## 1. 目标

统一管理 Wave 7 job 的 **工件落盘**：per-file envelope、`manifest.json`、`report.json` 草稿目录、失败回收区；支持幂等重跑与部分失败隔离。

---

## 2. 输入 / 输出

### 2.1 输入

| 输入 | 说明 |
|------|------|
| `job_id`、`sku` | job 标识 |
| 内存中的 envelope 列表 / manifest dict / report dict | 待写入 artifact |
| 写模式 | `create` \| `overwrite_stage` \| `finalize` |

### 2.2 输出

各 artifact 的 **逻辑 ref** + 可选 staging 物理写入；结构化回传：

```text
{ok, artifact_refs: {kind → logical_ref}, paths_logical: {...}, idempotent_hit: bool}
```

---

## 3. Done 条件（checklist）

- [ ] 目录布局与 R4 `w6://delivery/{job_id}/{manifest|report_json|report_md|deliverables}` 对齐（md 可先占位 ref）。
- [ ] Envelope 按 `file_id` 或 `content_sha256` 命名；重跑同 `job_id` 同 inputs 时 **不重复计费性写入**（hash 比对或 generation 标记）。
- [ ] 写失败 → 移入 job 级 `failed/` 或 quarantine 逻辑区，保留 last-good manifest 可选策略（文档化）。
- [ ] 全路径经 `gov_paths`；静态扫描无 `C:\` / `file://` 泄漏。
- [ ] 单测：create → 重跑 idempotent → 模拟 IO 错误回收。

---

## 4. 边界（明确不做）

- 不打包 tar/zip deliverables（可留空目录 + ref）
- 不注册 Chariot_Registry
- 不实现远程 object store

---

## 5. 依赖 / 前置

- `RUNNER-ENTRY-JOB-INPUT`（需 `job_id`）
- R4 #H-2 `w6://delivery/{job_id}/{artifact_kind}` 裁定

---

*Wave 7 implementation ticket · `04_Workflows/WAVE7_ARTIFACT_STORAGE_PATH_GOV_v0.1.md`*
