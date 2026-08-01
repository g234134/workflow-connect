# Evidence Tier Contract v1

> **Ticket**: `FP-G3-T1-evidence-tier-ssot-v1` · Full-Phase G3 · **SSOT 升格／對齊** · evidence_tier **L-local**  
> **Date**: 2026-07-10（Batch-3 execute · 既有 2026-06-26 正文保留）  
> **Tier 名称 SSOT**：`docs/p8_p89_evidence_index_v1.md` §1（**三 tier 固定命名** · 本文件 **不发明新 tier**）  
> **Ticket 字段**：`docs/ticket-schema-master-v1.md` · FRAME.`evidence_tier`  
> **Reviewer 硬门**：`04_Workflows/review_checklists/wave-next-code-inspector-v1.md` §3.2–3.3  
> **P7 专线索引**：`docs/P7_ADVISORY_CI_INDEX.md`（cross-ref only）

---

## 1. 三种 tier 定义（固定命名）

| Tier ID | 定义 | 典型证据形态 |
|---------|------|--------------|
| **`L-local`** | 开发者或 agent 在**本机**（或 sandbox venv cwd）执行的 unittest · CLI orchestrator · 单次命令记录；**无** GitHub Actions run URL | exit code · `N/N OK` · JSON artifact 路径 · Progress 命令摘要 |
| **`CI-advisory`** | **已 landing** 的 GitHub Actions workflow · job `continue-on-error: true` · **非** branch protection required | workflow 文件名 · job id · landing commit · **可无** completed run |
| **`GA-remote`** | **至少一次** completed 的 GitHub Actions run（或等价远端具名执行），含 **`run_url`** + **`run_id`** | run URL · run id · job 摘要 · artifact 名 · Progress append |

**Ticket / Progress 附加键**（与 index §1 一致）：

```yaml
evidence_tier: L-local | CI-advisory | GA-remote
evidence_kind: local_unittest | local_cli_smoke | ci_advisory_landing | ci_advisory_run | ga_remote_dispatch
```

**规划票无 runtime 证据**：`evidence_tier: n/a`（见 ticket schema master）。

---

## 2. 典型证据栏位

| 栏位 | Tier | 说明 |
|------|------|------|
| **run_url** | GA-remote | GitHub Actions run 页面 URL · **必填** 才可标 GA-remote |
| **run_id** | GA-remote | Numeric run id |
| **log_path** | L-local · GA-remote | 本机日志路径或 CI job log excerpt |
| **metrics_snapshot** | L-local | MP-METRICS / MC-METRICS JSON 输出 |
| **report_id** | Scribe/ops | `_ops_cycle.py validate-report` 通过的战报 id（若使用） |
| **workflow_file** | CI-advisory · GA-remote | 如 `.github/workflows/bridge-smoke.yml` |
| **artifact_paths** | L-local | 如 `outbox/verification/.../multi_phase_smoke_run.json` |
| **verification** | L-local | B_REPORT 可重跑命令 + exit code / ok 计数 |

### GA-remote 记录模板（引用 index §2.3 · 不得自造键名）

```yaml
ga_run:
  evidence_tier: GA-remote
  evidence_kind: ga_remote_dispatch
  workflow_file: .github/workflows/bridge-smoke.yml
  run_url: "<https://github.com/<org>/<repo>/actions/runs/<run_id>>"
  run_id: "<numeric>"
  jobs:
    - job_id: p85-bridge-smoke-a
      conclusion: success | skipped | failure
  non_claims:
    - advisory ≠ merge gate
    - GA pass ≠ prod-ready
```

---

## 3. 各 tier Non-Claims

| Tier | 禁止表述 |
|------|----------|
| **L-local** | 「遠端 validated」「GA pass」「CI 绿（GitHub）」「prod-ready」「INT Tier-A」 |
| **CI-advisory** | 「merge gate」「required check」「landing = GA pass」「landing = 远端 CI 绿」 |
| **GA-remote** | 无 URL 时使用「validated」「首跑 pass」「prod-ready」「required CI」 |

**跨 tier 共通**：

- advisory CI 绿 **≠** P7 Round-2 GO · P8.5 prod browser · P9 prod 金流
- MP-SMOKE 七步绿 **=** L-local 接線 sanity **≠** staging 完成
- bridge 14/14·7/7 **=** L-local **≠** in-memory stub 升格 prod

---

## 4. B / C / D / O 落实方式

| Phase | 负责角色 | 产出 |
|-------|----------|------|
| **B** Spec | Orchestrator / Planner | FRAME.`evidence_tier` · `non_claims` · observability 命令 |
| **C** Code/doc | Implementer | B_REPORT.`verification` 标注 tier；GA 票 **不得**预填假 URL |
| **D** Verify | Reviewer | 对照 index §3 误解表 · inspector §3.3；无 run_url **不得** GA-remote verdict |
| **O** Observe | Scribe | Progress 末尾 append：`evidence_tier` · 命令摘要 · `run_url` 或 `pending` |

### Progress append 最低字段

```markdown
- ticket_id · group_id · evidence_tier: L-local|CI-advisory|GA-remote|n/a
- 命令摘要 + 关键 ok/计数
- GA-remote: run_url + run_id 或 explicit `pending human dispatch`
- blocked / next
```

---

## 5. 与 trace / observability 的分工

| 文档 | 职责 |
|------|------|
| **本 contract** | **何时**可说 validated / GA / advisory · ticket/Progress 栏位 |
| **`p8_p89_evidence_index_v1.md`** | P8/P8.9/P8.5 具名 EVD-* 例子 · Phase% 门坎 §5 |
| **`p75-intake-gate-control-plane-trace-v1.md`** | P7.5 **trace 字段** · join keys |
| **`p8_p89_delivery_observability_contract_v1.md`**（待建） | Delivery **trace 字段** · artifact 路径 |

施工时：**tier** 查本 contract + index · **trace 字段** 查 p75 / OBS contract。

---

## 6. 废弃别名对齐（doc-only）

| 废弃 | 正确 |
|------|------|
| `L-GA-remote` | **`GA-remote`** |
| `M` / `H` tier | **`CI-advisory`** / **`GA-remote`** |
| `evidence_tier: prod` | 用 **`non_claims`** + 另开 prod 票；tier 用 `L-local` / `GA-remote` / `n/a` |

---

## 7. Sub-block readiness

| 子区块 | 状态 | 说明 |
|--------|------|------|
| **Evidence tier 基础契约** | **`ready`** (~100% doc) | 三 tier 名 · 栏位 · Non-Claims · B/C/D/O · 与 index 一致 |
| **GA-remote 物证** | **pending human** | 不改变 tier 定义 · Scenario2 ops-run blocked |

---

## Changelog

| 日期 | 变更 |
|------|------|
| 2026-06-26 | v1 · Lane A G3：从 `p8_p89_evidence_index_v1.md` 抽出 ticket/Progress contract · 对齐 `L-GA-remote`→`GA-remote` |
| 2026-07-10 | FP-G3-T1：標 Full-Phase G3 SSOT · 修正 OBS contract「待建」→已落地 · 未改三 tier 定義 |

---

*Evidence Tier Contract v1 · 2026-06-26 · 不改 Dashboard Phase%*
