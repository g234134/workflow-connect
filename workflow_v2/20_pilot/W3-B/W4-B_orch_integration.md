# W4-B-INDEX-INTEGRATION — KB index 接入 ORCH / IMP-AI-READY（implementation v1）

> **目标**：把 Wave 3（W3-B）已定稿的 `kb_index_*` 字段契约与 index pipeline runbook **真实接入**主工作流，使 `IMP-AI-READY` 进入前能基于 `kb_index_*` 产生 **allow / block** 行为（最小可运行版，先锁定主 case / 主 repo）。
>
> **硬边界**：不改 G7/G8 正文语义；不触碰暗部脚本；不扩面到全 repo / 全 case；不混入 Wave 5（实时增量 / 多 tenant / GraphRAG 产品化 / 替换 RAG 主路径）。

---

## 1. 主 case / 主 repo（W4-B 最小落地对象）

- **主 case**：`workflow_v2/20_pilot/W2-1_case/`
- **主 repo（scope）**：`kb_index_scope_kind=repo_subtree`，`kb_index_repo_root_ref=repo_root`，`kb_index_subtree=core`（v0.1）

案卷权威字段落点：`workflow_v2/20_pilot/W2-1_case/W2-1_case.md` → `kb_index_current` 小节。

---

## 2. 最小状态文件（index_status 侧车）

W4-B 以“只读状态 JSON”作为 index pipeline 与案卷回填的接点（不触碰暗部 job 本体）：

- 成功样例：`workflow_v2/20_pilot/W3-B/index_status_W2-1.json`
- 失败（infra blocker）样例：`workflow_v2/20_pilot/W3-B/index_status_W2-1.failed_infra.json`

schema 见 `W3-B_index_pipeline_runbook.md` §4（`repo_index_status_v0.1`）。

---

## 3. 案卷回填（kb_index_*）

### 3.1 回填工具

- 回填脚本：`workflow_v2/tools/wf_kb_index_sync.ps1`

### 3.2 用法（从 repo root）

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_kb_index_sync.ps1 `
  -CaseDir workflow_v2/20_pilot/W2-1_case `
  -StatusJson workflow_v2/20_pilot/W3-B/index_status_W2-1.json
```

回填后的案卷字段至少可见：

- `kb_index_status`（`ready|stale|missing`）
- `kb_index_job_id` / `kb_index_last_updated`
- `kb_index_blocker`（用于区分 infra/pipeline 故障 vs “没跑过”）
- `kb_index_evidence_refs`（指向 `index_status_*.json`）

---

## 4. ORCH / IMP-AI-READY 前置检查（真实读取与阻断）

### 4.1 ORCH precheck 工具（最小实现）

- gate 脚本：`workflow_v2/tools/wf_kb_index_gate.ps1`

### 4.2 判定语义（v0.1）

- **`ready`**：`allow`
- **`missing`**：`deny`（AI-READY 硬阻断）
- **`blocker`**：仍表现为 `deny`，但会输出 `kb_index_blocker_present`，用于区分“infra/pipeline 故障类阻断”而非“没跑过”
- **`stale`**：默认 `deny`；只有在案卷同时满足 `kb_index_stale_ack=true` + `kb_index_stale_reason` + `kb_index_reindex_ticket` 且调用方显式传 `-AllowStaleWithAck` 时，才返回 `require-human-override`

> 注：上述 `stale` 处理保持与 `W3-B_kb_contract.md` 的 degrade 语义一致（允许但需明确 ack / 留痕）；本实现把“允许”落为 `require-human-override`（显式旗标），避免静默放行。

### 4.3 用法（从 repo root）

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_kb_index_gate.ps1 `
  -CaseDir workflow_v2/20_pilot/W2-1_case `
  -TargetImpState IMP-AI-READY
```

---

## 5. 留给 Wave 5 的内容（刻意不做）

- 全 repo / 全 case 扩面（多案卷、多 scope）
- 实时增量 index（持续刷新与自动 stale→reindex）
- 多 tenant KB / 产品化权限模型
- GraphRAG 产品化（不止最小探针）
- 替换 RAG prod 主路径或 ask selector 生产默认

