# Wave 7 – RUNNER-ENTRY-JOB-INPUT（v0.1）

> **票号**：`RUNNER-ENTRY-JOB-INPUT`  
> **性质**：implementation ticket  
> **范围**：从真实批次/队列/CLI 构造 `job_record` 与 `raw_files[]`  
> **依据**：Wave 6 intake gate（可选前置）；`envelope_writer` 契约  
> **不做**：envelope/manifest 写入、清洗重跑、Telegram/哨兵监听、Postgres jobs 表写入

---

## 0. 背景

Wave 6 E2E smoke 在内存里手工构造 `job_record` + `raw_files`。本票实现 Wave 7 runner 的 **job 构造层**，对接真实文件批次或队列消息。

---

## 1. 目标

实现 Wave 7 runner 的 **job 构造层**：从「文件批次 manifest / 队列 payload / CLI 参数」解析出合规 `job_record` 与 `raw_files[]`，并对接已有 Wave 6 intake gate（可选前置）。

---

## 2. 输入 / 输出

### 2.1 输入

| 输入 | 说明 |
|------|------|
| `intake` 决策或等价字段 | `product_sku`、`client_ref`、`inbound_path_hint` 等 |
| 批次文件列表或 `cleaned_full` JSON 路径集合 | 原始 input 来源 |
| 可选 `job_id` override | 指定 job 标识 |

### 2.2 输出

| 输出 | 说明 |
|------|------|
| `job_record` | 至少含 `job_id`、`sku`、`client_ref`、`created_at` |
| `raw_files[]` | 满足 `envelope_writer` 契约；`stored_logical_path` 为逻辑路径 |
| 结构化回传 | `{ok, message, job_record, input_count, skipped[]}` |

---

## 3. Done 条件（checklist）

- [ ] 支持 **BASIC** 与 **ENRICH** 两 SKU；SKU 与 intake `product_sku` 不一致时拒绝并返回可审计 reason。
- [ ] 从磁盘读 cleaned JSON 时剥离/映射 legacy 字段（`source_path`/`stored_path` → 逻辑路径），不向下游泄漏绝对路径。
- [ ] 空批次、缺 `content_sha256`、SKU 未知 → `ok: false` + 稳定 error code。
- [ ] 单测覆盖：CLI 参数路径、目录扫描、最小 queue JSON fixture 三条路径。
- [ ] 与 intake gate 集成时：`decision=accept` 才进入 job 构造；`defer/reject` 不创建 job。

---

## 4. 边界（明确不做）

- 不做 envelope/manifest 写入
- 不做清洗重跑
- 不实现 Telegram/哨兵监听
- 不写入 Postgres jobs 表（留给 lifecycle 票）

---

## 5. 依赖 / 前置

- `RUNNER-ENV-BOOTSTRAP`（环境引导）
- 可选：Wave 6 intake gate

---

*Wave 7 implementation ticket · `04_Workflows/WAVE7_RUNNER_ENTRY_JOB_INPUT_v0.1.md`*
