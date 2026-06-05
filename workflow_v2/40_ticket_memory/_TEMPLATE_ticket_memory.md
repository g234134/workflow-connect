# Ticket Memory / Context Card — Template（MVP）

> **用途**：用于在“最小上下文”下重建票面执行面，支撑多 lane（planning / runtime-only / review / doc-sync）分流。
>
> **参考**：控制面 MVP 文档 `workflow_v2/30_control_plane/W4-X_control_plane_mvp.md`。

---

## ticket

- id:
- title:

## lane

> `planning` | `runtime` | `review` | `doc-sync`
>
> **调度主字段**：Supervisor 据此决定该票当前走哪条工作流（开哪类 chat / 派哪类角色）。应与下方 `mode` 对齐（`runtime` ↔ `runtime-only`）。

- lane:

## priority

> `P0` | `P1` | `P2`（或团队约定等级）
>
> **排程字段**：多票并行时决定开工顺序与抢占；`P0` 高于 `P1`/`P2`；同优先级按 `Depends on`、阻塞状态与 Supervisor 裁决胜出。

- priority:

## mode

> `planning` | `runtime-only` | `review` | `doc-sync`
>
> **执行切片**：描述本张 Context Card 所服务的那一段 lane 工作；与 `lane` 一致，供 Executor / Reviewer 对账。

- mode:

## goal

- goal:

## read_set

> 列出允许读取的文件/目录（相对路径）；未列出则默认不读。

- read_set:

## write_set

> 列出允许修改的文件/目录（相对路径）；未列出则默认不改。

- write_set:

## frozen_constraints

> 本票不可触碰/不可改变的约束（例如：不改暗部脚本、不启用 deny runtime、不改 G7/G8 正文语义等）。

- frozen_constraints:

## done_definition

> “完成”的可验证判定：交付物列表 + 验证证据（命令/runner/断言/可复跑检查点）。

- done_definition:

## pending_followups

> 本票刻意不做或需要后续票承接的事项（写 ticket id 或占位描述）。

- pending_followups:

