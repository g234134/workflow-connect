# segments/ — 段执行摘要存放目录

> **用途**：Cursor-Worker、小龍蝦 每段结束提交的 SEGMENT 实例。  
> **模板**：[`../SEGMENT_EXEC_SUMMARY_TEMPLATE.md`](../SEGMENT_EXEC_SUMMARY_TEMPLATE.md)

## 命名规则

```
{TASK_ID}__seg{N}__{YYYY-MM-DD}.md
```

示例：

- `T4b-1__seg1__2026-06-01.md`
- `T2__seg1__2026-06-02.md`

## 谁写入

| 角色 | 何时写 |
|------|--------|
| Cursor-Worker | 每个施工段结束 |
| 小龍蝦 | 每批白名单任务结束 |
| Cursor-Orchestrator | **不写** SEGMENT；阶段总结写 `HANDOFF_SUMMARY.md` |

## 示例占位

本目录初始为空。试跑 T2 后，Worker 应在此新增第一份 SEGMENT 文件。
