# TICKET STATE · W2-T2-routing-eval · Routing / Eval 测试与说明（Wave 2）

> handoff 摘要档；跨 chat 交棒以本档为准。  
> Wave：Wave 2 — MVP Intake / Routing / Eval 基礎層  
> **与旧 W2-T2 区分**：`W2-T2_state.md` = Multi-Chat B→C→D→O 参照票（draft）；**本票** = routing eval guide + eval cases YAML + tests。

---

## FRAME

- Title: W2-T2 · Routing / Eval 测试与说明
- Goal: 定义「如何编写与检查 routing 测试」的人读指南 + 机器可读 eval cases，与 W2-T1 catalog 结构对齐；不实现 router、不改 skills。
- Scope:
  - 新增 `docs/routing-eval-guide-v1.md`
  - 新增 `routing/routing_eval_cases_v1.yaml`
  - 新增 `tests/test_routing_eval_cases.py`
- NonScope:
  - 不改任何现有 `*.py` 实现（router / selector / skills）、`skills/*` 卡本体
  - 不接入 GitHub Actions / CI eval pipeline
  - 不写 LLM-as-a-judge prompt 或自动 trace 比对 runner
  - 不改 `HARNESS_CONSTITUTION` / `ENGINEERING_CONTRACT` / `AGENTS` / `.cursor/rules/*`
- AllowedPaths:
  - `docs/routing-eval-guide-v1.md`
  - `routing/routing_eval_cases_v1.yaml`
  - `tests/test_routing_eval_cases.py`
  - `04_Workflows/tickets/W2-T2-routing-eval_state.md`
- BlockedPaths:
  - `core/*` · `scripts/*` · `skills/gov_cards/*` · `skills/cards/*`
  - `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `HARNESS_CONSTITUTION.md`
  - `.cursor/rules/*`
- Dependencies:
  - W2-T1-intake-routing-catalog · `routing/intake_routing_catalog_v1.yaml`
  - W1-T2-mvp-trace-path · `docs/mvp-standard-trace-path.md`
  - B-F1 · `docs/SKILL_CATALOG_OVERVIEW.md`
- AcceptanceCriteria:
  - **AC-1**: `docs/routing-eval-guide-v1.md` 让工程师能写一个新 routing case 并知道观察点
  - **AC-2**: `routing/routing_eval_cases_v1.yaml` 可 parse；`cases[].id` 唯一；`task_type` 均在 catalog 中存在
  - **AC-3**: 至少覆盖 Tabular（demo_phase + sampleco）与 Gov eval（`gov.observability.eval`）及一条 regression case
  - **AC-4**: 文档与 cases 明确本票 ≠ routing engine / CI runner / LLM judge
  - **AC-5**: 未改 router / skills / 治理母本；tests 只检查 eval cases 与 catalog 一致性
- VerificationCommands:
  - `python -m unittest tests.test_routing_eval_cases -v` → exit 0

---

## STATE

- overall_status: done
- implementation_status: done
- current_owner: orchestrator
- next_action: 索引登錄 WORKFLOW_INDEX；可选未来 Wave 挂 CI eval runner
- last_updated: 2026-06-10 · orchestrator + scribe
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

### 新增文件

| 路径 | 说明 |
|------|------|
| `docs/routing-eval-guide-v1.md` | 人读 routing eval 指南（case 字段、通过语义、观察点） |
| `routing/routing_eval_cases_v1.yaml` | 机器可读 eval cases（4 条：demo_phase、sampleco、gov eval、mainline regression） |
| `tests/test_routing_eval_cases.py` | cases 与 catalog 结构对齐校验 |
| `04_Workflows/tickets/W2-T2-routing-eval_state.md` | 本票 state |

### eval cases 摘要（AC-3）

| id | task_type | family |
|----|-----------|--------|
| `tabular_demo_phase_clean` | `tabular.cleaning.mvp` | tabular_mvp |
| `tabular_sampleco_e2e` | `tabular.cleaning.mvp` | tabular_mvp |
| `gov_obs_eval_gate` | `gov.observability.eval` | gov_registry |
| `tabular_mainline_regression` | `tabular.cleaning.regression` | tabular_mvp |

### 文档章节

1. 目的与假设读者  
2. 测试单位（case 必填 / 可选字段）  
3. 通过 / 失败语义（人工 v1 + 未来自动化挂钩点）  
4. 与 intake catalog 的关系  
5. 样例 walkthrough  
6. 验证  
7. 相关文档  

### verification

- `python -m unittest tests.test_routing_eval_cases -v` → **exit 0**；8 tests OK
- 合并验收：`python -m unittest tests.test_routing_eval_cases tests.test_intake_routing_catalog -v` → **18 tests OK**

---

## C_REPORT

> **覆核**：Orchestrator + Scribe 本回合收口（依 B_REPORT、guide spec 与 unittest 证据覆核）。

- conclusion: **accepted**
- blocking_issues: 無
- checks_summary:
  - **AC-1 ✅**：`routing-eval-guide-v1.md` 含 case 字段表、人工对照步骤、observation_points 说明
  - **AC-2 ✅**：YAML 可 parse；4 条 `id` 唯一；全部 `task_type` 存在于 `intake_routing_catalog_v1.yaml`
  - **AC-3 ✅**：Tabular demo_phase + sampleco + `gov.observability.eval` + `tabular.cleaning.regression` 均已覆盖
  - **AC-4 ✅**：§1 / §1.3 明确 skeleton ≠ router / CI / LLM judge
  - **AC-5 ✅**：未改 router、`skills/*`、治理母本；tests 仅校验 cases ↔ catalog 一致性
  - **補充**：與對應 tests/ docs/ yaml 成功對齊，無 blocking gap
- risk_level: low
- suggestions:
  - 未来 CI：可写 runner script 解析 trace JSONL 与 case YAML diff（本票 out of scope）
  - 新增 case 时同步更新 catalog `task_type`（依赖 W2-T1 SSOT）

---

## D_REPORT

- docs_updates:
  - **交付物**：routing eval 测试骨架 — 人读 `docs/routing-eval-guide-v1.md`、机器 SSOT `routing/routing_eval_cases_v1.yaml`、一致性验证 `tests/test_routing_eval_cases.py`（8/8 OK；与 W2-T1 tests 合计 18/18 OK）。
  - **用途**：定义「给定 task_type，期望哪些 family / tool_id / entrypoint，以及去哪里验证」的可机器读样例 + 人读检查清单；供 Agent 事后对照或未来 eval pipeline 消费，**不**在运行时驱动路由。
  - **边界**：本票只定「如何写与检查 routing 测试」；**不**跑在 CI、**不**做 LLM judge、**不**改 `ask_rag_selector` / Tabular Tool Layer / HQ `_route_task`。cases 引用 W2-T1 catalog 为权威，禁止混用错误 family（例：Tabular 任务不应出现 `obs.eval.export`）。
  - **Wave 关系**：Wave 1 / Wave 3 提供主链与 Tabular 工具层 SSOT；**Wave 2**（T1 catalog + T2 eval cases）提供跨 family 路由规则索引与 eval case 骨架，三件套（doc + YAML + tests）完成度与 W1/W3 对齐。
- progress_entry: |
    [W2-T2-routing-eval] done · 建立 routing eval 指南 + eval cases（Tabular demo_phase/sampleco + Gov eval + regression）；新增 docs/routing-eval-guide-v1.md + routing/routing_eval_cases_v1.yaml + tests（8/8 OK）。Reviewer/Orchestrator accepted。
- followup_suggestions:
  - 后续 Wave 可新增 `scripts/run_routing_eval_check.py` 或 CI job 消费 `routing_eval_cases_v1.yaml`
  - 与 Langfuse / gov-trace JSONL 对齐时另开 observability 票（guide §2.3 已列挂钩点）
  - 保持 `W2-T2_state.md`（Multi-Chat 参照票）与本档分轨，勿合并
