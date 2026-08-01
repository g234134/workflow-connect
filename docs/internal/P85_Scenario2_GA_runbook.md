# P8.5 Scenario 2 GA — Human Runbook

> **用途**：ops / human 手动触发 **Scenario2 GA** 并回填证据。  
> **SSOT 票**：`04_Workflows/tickets/WH-P85-SMOKE-B-scenario2-ops-run-v1_state.md`  
> **non-claims**：advisory · non-blocking · **≠ required CI · ≠ merge gate · ≠ prod browser**

---

## 背景

- **Scenario1 / 本机 smoke**：设计 + 本机 **14/14 · 7/7 validated**（**≠ 远端 GA pass**）。
- **CI-LAND**：`bridge-smoke.yml` 已 landing **`origin/main`** · Actions 可见 **P85 Bridge Smoke CI (advisory)** · `workflow_dispatch` 含 **`scenario2`** 参数。
- **Scenario2 GA**：**尚未跑** — GitHub API runs **`total_count=0`** · ops-run 票 B_REPORT `ga_run` **N/A** · **无 run URL / run id**。
- **closure-scribe**：`WH-P85-wave-H2-closure-scribe-v1` **维持 `blocked`** — hard blocking = Scenario2 GA run evidence。

---

## 操作步骤

1. GitHub → Repo → **Actions** → 左栏选 **P85 Bridge Smoke CI (advisory)**。
2. 右栏 **Run workflow**：
   - **Use workflow from**：**`main`**
   - **scenario** 下拉：**`scenario2`**（**勿**选 `default`）
3. 点 **Run workflow** · 等待 run **completed**（advisory · 不阻 merge）。
4. 复制 **run URL** 与 **run id**（Actions UI 或 URL 末段数字）。
5. 验收 log：**仅** `p85-bridge-smoke-a-scenario2` · `p85-bridge-smoke-b-scenario2` · 各 job 含 design-skip + deps-gate skip notice · step **exit 0**。

**可选 CLI**（同等权限）：`gh workflow run bridge-smoke.yml --ref main -f scenario=scenario2`

---

## 回填位置

| 目标 | 栏位 |
|------|------|
| **ops-run 票** | B_REPORT **`ga_run`**（run URL · run id · branch · scenario input · 两 job status + notice 摘要） |
| **Progress** | `04_Workflows/00_Agent_Work_Progress.md` **末尾 append**（依 ops-run FRAME Progress 模板） |
| **closure-scribe** | 证据齐后重跑 `WH-P85-wave-H2-closure-scribe-v1` lane |

---

## 禁止项

- **无 run URL 不得宣称 Scenario2 GA pass** · 本机 bash 探针 **≠ GA 证据**。
- advisory CI **≠ required check / merge gate / prod browser**。
- step exit **1** 或 unexpected failure → **勿** append Progress 为 pass · 维持 ops-run **`blocked`**。

---

*版本：v1 · 2026-06-25 · Wave-next doc/SOP Scribe 落档*
