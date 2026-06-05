# W3-B-INDEX-PIPELINE — 导入 scope → repo_index_v1 → 状态 JSON → 案卷 KB 字段（Runbook · v0.1）

> **票号**：W3-B-INDEX-PIPELINE（本票：**纯文档**）  
> **前置**：W3-B-KB-CONTRACT 已将 `kb_index_*` 字段写入 `_TEMPLATE_case` 与 `W3-B_case`（P0 案卷权威字段）。  
> **禁区**：不写任何 index job 代码；不触碰暗部脚本与真实命令；不涉及生产密钥；不定义“全库实时 index / 多 tenant KB”（Wave 4）。  
> **权威锚点**：W3-B 总控契约见 `../W3-B_kb_contract.md`（`index-before-AI-READY` 制度与 `kb_index_status` 语义）。

---

## 1. 这条 pipeline 做什么（最小闭环）

在**单一导入 case**中，把 PM/Eng 已确认的 `in_scope`（repo subtree）转成一次离线 `repo_index_v1` index job 的 **scope**，并将 job 的只读 **状态 JSON** 回填到案卷的 **KB 字段**（`kb_index_*`），使 `IMP-AI-READY` entry 能判断：

- **是否真的跑过 index**（`missing` vs `ready`/`stale`）
- **失败原因是“没跑”还是“infra 故障”**（`missing` vs `kb_index_blocker`）
- **这次 index 覆盖的 scope 是什么**（scope digest / subtree / baseline ref）

> 备注：本 runbook 只定义“接点与回填路径”；index job 本体已在暗部系统中存在。

### 1.1 Wave 4 最小接线（W4-B implementation v1）

W4-B 在 HQ 层以 **脚本**把“状态 JSON → 案卷字段 → AI-READY 前置 gate”接上主工作流（不触碰暗部 job 脚本）：

- `workflow_v2/tools/wf_kb_index_sync.ps1`：读取 `index_status_<CASE>.json`，回填案卷 `kb_index_*`
- `workflow_v2/tools/wf_kb_index_gate.ps1`：在进入 `IMP-AI-READY` 前读取 `kb_index_*` 并给出 `allow / require-human-override / deny`
- 主 case / 主 repo 与样例：`workflow_v2/20_pilot/W3-B/W4-B_orch_integration.md`

---

## 2. 触发条件（在导入 case 中的具体哪一步）

### 2.1 推荐触发点（默认）

- **触发时机**：`IMP-SPEC-CLARIFY` **exit**（即 scope 已稳定）到 `IMP-AI-READY` **entry 之前**。
- **触发责任**：Eng owner（或被授权的导入编排器）负责发起 index，并在 job 完成后回填案卷 KB 字段。

### 2.2 允许的提前触发（不阻塞澄清关）

- **触发时机**：在 `IMP-SPEC-CLARIFY` 期间，只要 `in_scope` 已具有明确 repo subtree 语义，可以**并行**触发一次 index。
- **注意**：scope 变更时需要 **re-index** 或将状态降为 `stale`（见 §6）。

### 2.3 与 `IMP-AI-READY` 的硬门禁关系

- **硬门禁**：进入 `IMP-AI-READY` 时，案卷 `kb_index_status` **不得为 `missing`**。
- **允许 degrade**：若 `kb_index_status=stale`，必须走 ORCH 的 `stale_ack` 路径（由 `../W3-B_kb_contract.md` 定义）。

---

## 3. 传给 `repo_index_v1` 的 scope 信息（逻辑名，无密钥）

### 3.1 最小 scope（v0.1）

> scope 仅表达“索引什么”，不携带任何连接信息、密钥或运行参数。

- `schema_version`：`"repo_index_scope_v0.1"`
- `case_id`：导入 case 的逻辑 ID（与案卷一致）
- `kb_index_scope_kind`：`"repo_subtree"`（v0.1 默认）
- `kb_index_repo_root_ref`：逻辑名：`"repo_root"`
- `kb_index_subtree`：例如 `"core"` / `"subagents"` / `"context"`（必须与 `ART-PM-SCOPE.in_scope` 对齐）
- `kb_index_baseline_ref`：可选（commit/tag/`"unpinned"`）
- `kb_index_include_globs`：可选（逻辑 glob 列表）
- `kb_index_exclude_globs`：可选（逻辑 glob 列表）

### 3.2 scope digest（用于 stale 判定）

生成并记录一个**scope 指纹**（digest），供：

- job 状态 JSON 记录“这次跑的 scope”
- 案卷在 scope 变更时，将 `ready` 变为 `stale`（或提示重跑）
- 后续 W3-B-SELECTOR-HOOK 只读对齐输入

**最小建议**：对 §3.1 的字段（排除不影响内容的字段顺序）做 canonical JSON 后 hash，记为 `kb_index_scope_digest`（算法名不在本票冻结；只要求 digest **稳定可复现**）。

---

## 4. index job 完成后的状态 JSON（schema · v0.1）

### 4.1 文件定位（pilot 侧车）

建议为每个 case 生成一个只读状态侧车（逻辑路径示例）：

- `workflow_v2/20_pilot/W3-B/index_status_<CASE>.json`

> 注意：路径是**仓库相对路径**示例；不得写磁盘绝对路径。

### 4.2 顶层字段（key + 含义）

状态 JSON 须至少包含以下字段（不要求一次性齐全扩展字段，但 **job_id/status/timestamps/scope_digest** 必须有）：

- `schema_version`：固定 `"repo_index_status_v0.1"`
- `case_id`：与案卷一致
- `job_type`：固定 `"repo_index_v1"`
- `job_id`：index job 的唯一标识
- `status`：`"running" | "succeeded" | "failed" | "canceled"`
- `last_updated`：ISO-8601 UTC（状态最后一次更新）
- `started_at`：ISO-8601 UTC（可空）
- `finished_at`：ISO-8601 UTC（可空）
- `scope`：对象，包含（至少）`kb_index_repo_root_ref` / `kb_index_subtree` / `kb_index_baseline_ref` / `kb_index_scope_kind`
- `scope_digest`：字符串（见 §3.2）

### 4.3 结果与错误（必须能区分 infra vs missing）

当 `status="succeeded"` 时建议包含：

- `result_summary`：对象（如 `file_count` / `chunk_count` / `graph_artifact_ref` 等，均为逻辑名或相对路径，不含密钥）

当 `status="failed"` 时必须包含：

- `error_type`：`"infra_unavailable" | "job_error" | "invalid_scope" | "unknown"`
- `error_message`：短摘要（不得包含密钥或连接串）
- `retryable`：boolean（可选）

**关键区分**：

- **infra 故障**（如 PG/Qdrant 不可达）应体现在：`status="failed"` 且 `error_type="infra_unavailable"`  
  → 回填案卷时写入 `kb_index_blocker`（见 §5），而不是把它当成“没跑过”。
- **missing（没跑 index）**：表示根本没有产生过覆盖 scope 的成功 job（或压根未触发）  
  → 这是 `IMP-AI-READY` 的硬 block 原因，不能用 `failed` 来代替 `missing`。

---

## 5. 用状态 JSON 更新案卷 KB 字段（P0 权威）

> 目标：把“是否跑过/跑的是哪份 scope/最后成功时间/失败是否 infra”落到 `kb_index_*` 字段，让后续 selector hook **只读**这些字段即可工作。

### 5.1 更新规则（从状态 JSON → 案卷字段）

从 `index_status_<CASE>.json` 读取并回填案卷（字段名以 `../W3-B_kb_contract.md` 为准）：

- **当 `status="succeeded"`**：
  - `kb_index_status = "ready"`
  - `kb_index_source = "repo_index_v1"`
  - `kb_index_job_id = <job_id>`
  - `kb_index_last_updated = <finished_at>`（若缺失用 `last_updated`）
  - `kb_index_scope_kind = <scope.kb_index_scope_kind>`
  - `kb_index_subtree = <scope.kb_index_subtree>`
  - `kb_index_baseline_ref = <scope.kb_index_baseline_ref>`
  - `kb_index_blocker = ""`（或 `—`）
  - `kb_index_evidence_refs` 追加：状态 JSON 逻辑路径（以及可选 manifest/graph 逻辑引用）

- **当 `status="failed"` 且 `error_type="infra_unavailable"`**：
  - `kb_index_status = "missing"`（因为没有成功覆盖 scope 的 index；仍然满足“AI-READY entry 要 block”的语义）
  - `kb_index_source = "repo_index_v1"`
  - `kb_index_job_id = <job_id>`（若有）
  - `kb_index_last_updated = "—"`
  - `kb_index_blocker` 填：`infra_unavailable` 的人类可读摘要（不得含密钥）
  - `kb_index_evidence_refs` 追加：状态 JSON 逻辑路径

- **当 `status="failed"` 且 `error_type!="infra_unavailable"`**：
  - `kb_index_status = "missing"`
  - `kb_index_blocker` 填：失败摘要 + 下一步（如“scope 无效需澄清/重跑”）
  - 其余同上（记录 job_id 与 evidence）

### 5.2 为什么失败时仍写 `missing`

`kb_index_status` 的枚举表达的是“是否存在覆盖当前 scope 的成功 index”，而不是“最后一次 job 是否失败”。  
因此只要**没有成功覆盖 scope**，都应是 `missing`（并用 `kb_index_blocker` 提供可操作原因）。这能保证：

- `IMP-AI-READY` 的 gate 可以只看 `kb_index_status`
- infra 故障与未触发可以通过 `kb_index_blocker` 和 evidence refs 区分

---

## 6. stale / scope 变更与回填（最小规则）

### 6.1 何时判定 `stale`

满足任一条件，视为 `stale`：

- 案卷声明的 scope（subtree/baseline/include-exclude）与状态 JSON 的 `scope_digest` 不一致
- baseline ref 发生变化（如从 `unpinned` → pinned，或 commit/tag 变化）
- staleness 时间阈值超过（阈值由 ORCH/后续票冻结；本票只要求“必须存在阈值或明确不启用时间阈值”）

### 6.2 stale 后的动作（不在本票实现）

- **不在本票**定义自动重跑机制；仅规定案卷必须记录 `stale`，并登记 `kb_index_reindex_ticket`（若要带 stale 进入 AI-READY，还需 `stale_ack`，见 ORCH）。

---

## 7. 为 W3-B-SELECTOR-HOOK 提供的 I/O 约定（只读）

### 7.1 Selector hook 的最小输入（来自案卷/ENG-CTX 镜像）

后续 selector hook **不得依赖暗部 job 细节**，只读取（或镜像读取）：

- `kb_index_status`
- `kb_index_source`
- `kb_index_job_id`
- `kb_index_last_updated`
- `kb_index_scope_kind`
- `kb_index_subtree`
- `kb_index_baseline_ref`
- `kb_index_blocker`
- `kb_index_evidence_refs`

### 7.2 Selector hook 的最小输出（建议）

selector hook 输出一个只读决策结构（示例字段名，具体以 W3-B-SELECTOR-HOOK 票冻结）：

- `kb_precondition_ok`（boolean）
- `kb_precondition_reason`（string）
- `kb_index_bucket`：`ready|stale|missing`
- `kb_index_job_ref`：`kb_index_job_id` 或 evidence ref

---

## 8. 验收方式（本票不执行，只定义证据形状）

在任一试点 case 中，能提供以下证据即可视为“对接可用”：

- 案卷 P0：`kb_index_status` 不为 `missing`（至少一次成功覆盖 scope）
- 侧车 P2：存在 `index_status_<CASE>.json`，且包含 §4.2 必填字段
- 迁移到 `IMP-AI-READY` 时，案卷迁移日志记录 `kb_index_status_at_transition`

### 8.1 W4-B implementation v1 的可重跑证据（最小）

从 repo root 可重跑：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_kb_index_sync.ps1 -CaseDir workflow_v2/20_pilot/W2-1_case -StatusJson workflow_v2/20_pilot/W3-B/index_status_W2-1.json
powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_kb_index_gate.ps1 -CaseDir workflow_v2/20_pilot/W2-1_case -TargetImpState IMP-AI-READY
```

---

## 附录 A — Wave B bootstrap scope（`WAVE-B-P1-REPO-INDEX-GOV-SCOPE-LIVE` · 2026-06-05）

> **定位**：HQ 侧离线 bootstrap runner；**不**依赖 PostgreSQL／Qdrant。暗部 `repo_index_v1` 就绪后可替换 runner，但须保持 `index_status`／manifest 契约不变。

### A.1 冻结 scope

权威配置：`workflow_v2/kb/wave_b_gov_scope.json`

| 项 | 值 |
|----|-----|
| **case** | `W2-1` |
| **subtrees** | `core`、`subagents`、`context`、`observability`、`04_Workflows` |
| **root files** | `AGENTS.md` |
| **include_globs** | `*.py`、`*.md` |
| **scope_digest** | 见 `index_status_W2-1.json`（SHA-256 canonical JSON） |

### A.2 可重跑 CLI 序列（repo root）

```bash
# 1) 扫描 subtree → manifest + index_status
python workflow_v2/kb/repo_index_bootstrap.py run --case W2-1

# 2) 案卷回填
powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_kb_index_sync.ps1 `
  -CaseDir workflow_v2/20_pilot/W2-1_case `
  -StatusJson workflow_v2/20_pilot/W3-B/index_status_W2-1.json

# 3) IMP-AI-READY gate（期望 verdict=allow）
powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_kb_index_gate.ps1 `
  -CaseDir workflow_v2/20_pilot/W2-1_case `
  -TargetImpState IMP-AI-READY

# 4) manifest RAG smoke（期望 hits>=1）
python workflow_v2/kb/rag_index_smoke.py "AGENTS.md" --top-k 5
```

### A.3 Wave B vs Wave C

| 项目 | Wave B（本附录） | Wave C 之后 |
|------|------------------|-------------|
| Runner | `workflow_v2/kb/repo_index_bootstrap.py` | 暗部 `repo_index_agent` + PG manifest |
| Case | 仅 `W2-1` | 多 case 动态 scope |
| 向量检索 | manifest 关键词 smoke | Qdrant `repo_chunks` prod 路径 |

**Wave C 留项**：全库增量、多 tenant KB、暗部 embed job 自动触发。

