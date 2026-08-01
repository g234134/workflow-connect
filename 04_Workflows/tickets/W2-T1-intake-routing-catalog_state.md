# TICKET STATE · W2-T1-intake-routing-catalog · Routing Catalog（Wave 2 基礎層）

> handoff 摘要档；跨 chat 交棒以本档为准。  
> Wave：Wave 2 — MVP Intake / Routing / Eval 基礎層  
> **与旧 W2-T1 区分**：`W2-T1_state.md` = Core Agent Smoke PR 門禁（done）；**本票** = intake routing catalog spec + YAML。

---

## FRAME

- Title: W2-T1 · Routing Catalog
- Goal: 整理「入口 / 技能 / 工具路由」Catalog，厘清 Skill / Gov tool / Tabular / Product card 关系，交付人读 spec + 机器 routing 清单供 T2 测试。
- Scope:
  - 新增 `docs/intake-routing-catalog-v1.md`
  - 新增 `routing/intake_routing_catalog_v1.yaml`
  - 可选 `tests/test_intake_routing_catalog.py`
- NonScope:
  - 不改任何现有 `*.py` 实现、`skills/*` 卡本体、`config/routing_policy.yaml`
  - 不改 `HARNESS_CONSTITUTION` / `ENGINEERING_CONTRACT` / `AGENTS` / `.cursor/rules/*`
  - 不写 LLM / eval prompt 内容；不实现 routing engine
- AllowedPaths:
  - `docs/intake-routing-catalog-v1.md`
  - `routing/intake_routing_catalog_v1.yaml`
  - `tests/test_intake_routing_catalog.py`
  - `04_Workflows/tickets/W2-T1-intake-routing-catalog_state.md`
- BlockedPaths:
  - `core/*` · `scripts/*` · `skills/gov_cards/*` · `skills/cards/*`
  - `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `HARNESS_CONSTITUTION.md`
  - `.cursor/rules/*`
- Dependencies:
  - W3-TL-T1 done · `tools/tabular_tool_catalog_v1.json`
  - B-F1 · `docs/SKILL_CATALOG_OVERVIEW.md`
  - B-F3 · `config/routing_policy.yaml`
  - W1-T2-mvp-trace-path · `docs/mvp-standard-trace-path.md`
- AcceptanceCriteria:
  - **AC-1**: `docs/intake-routing-catalog-v1.md` 让新工程师 10 分钟内理解主要任务类型应走哪个 Catalog family
  - **AC-2**: `routing/intake_routing_catalog_v1.yaml` schema 合理、可 parse；`routes[].task_type` 唯一
  - **AC-3**: 至少一条 Tabular MVP（`run_case_e2e_validation` + tabular tool_ids）与一条 Gov/Eval 类任务
  - **AC-4**: 文档清楚区分「本票 Catalog/规则」与「真正 routing engine / eval pipeline」
  - **AC-5**: 未改任何现有 code/config/治理文件；若有 tests 只检查 routing 文件本身
- VerificationCommands:
  - `python -m unittest tests.test_intake_routing_catalog -v` → exit 0（若 pyyaml 可用）

---

## STATE

- overall_status: done
- implementation_status: done
- current_owner: implementer
- next_action: W2-T2 routing/eval 测试与说明
- last_updated: 2026-06-10 · implementer
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
| `docs/intake-routing-catalog-v1.md` | 人读 routing catalog spec |
| `routing/intake_routing_catalog_v1.yaml` | 机器可读 routes（10 条主线） |
| `tests/test_intake_routing_catalog.py` | YAML 结构 / task_type 唯一 / family 校验 |
| `04_Workflows/tickets/W2-T1-intake-routing-catalog_state.md` | 本票 state |

### routing YAML 样例（AC-3）

**tabular.cleaning.mvp**

```yaml
task_type: tabular.cleaning.mvp
entrypoint: scripts/run_case_e2e_validation.py
preferred_tool_family: tabular_mvp
tool_ids:
  - validate.eligibility
  - clean.phase_demo
  - export.delivery_bundle
eval_profile: none
```

**gov.observability.eval**

```yaml
task_type: gov.observability.eval
preferred_tool_family: gov_registry
policy_route_id: wave_b.eval_report
tool_ids:
  - obs.eval.export
  - obs.eval.report
  - obs.wf.status_summary
eval_profile: eval_gate_v1
```

### 文档章节

1. 目的与范围  
2. 名词表  
3. 入口 / 任务类型表  
4. 与现有 Catalog 的关系与边界  
5. 未来 routing engine / eval 挂钩点  
6. 验证  
7. 相关文档  
附录 A：10 分钟速读路径  

### verification

- `python -m unittest tests.test_intake_routing_catalog -v` → **exit 0**；10 tests OK

---

## C_REPORT

> **覆核**：Orchestrator + Scribe 本回合收口（Reviewer chat 未獨立跑票；依 B_REPORT 與 unittest 證據覆核）。

- conclusion: **accepted**
- blocking_issues: 無
- checks_summary:
  - **AC-1 ✅**：`docs/intake-routing-catalog-v1.md` 含名词表、任务类型表、§4 边界、附录 A 10 分钟速读；新工程师可对照 `task_type` → family
  - **AC-2 ✅**：`routing/intake_routing_catalog_v1.yaml` 可 parse；`routes[].task_type` 唯一（10 条主线）；`tool_families` schema 合理
  - **AC-3 ✅**：含 `tabular.cleaning.mvp`（Tabular MVP E2E + tabular `tool_ids`）与 `gov.observability.eval`（Gov eval + `eval_gate_v1`）
  - **AC-4 ✅**：§1.3 / §5 明确「catalog / rules only」≠ routing engine / eval pipeline
  - **AC-5 ✅**：未改既有 `*.py` / `skills/*` / `config/routing_policy.yaml` / 治理母本；tests 仅校验 routing 文件本身
  - **補充**：與對應 tests/ docs/ yaml 成功對齊，無 blocking gap
- risk_level: low
- suggestions:
  - 新增 `task_type` 须先更新 catalog YAML 再开实现票（与 D_REPORT 一致）
  - `eval_profile` 占位已由 W2-T2 cases 部分消费；未来 eval runner 可再对齐 `routing_eval_cases_v1.yaml`

---

## D_REPORT

- docs_updates:
  - **交付物**：跨 family intake routing catalog — 人读 `docs/intake-routing-catalog-v1.md`、机器 SSOT `routing/intake_routing_catalog_v1.yaml`、结构验证 `tests/test_intake_routing_catalog.py`（10/10 OK）。
  - **用途**：Wave 2 基础层 SSOT，将 Skill / Gov tool / Tabular / Product card / HQ routing 收敛为「任务类型 → tool family + tool_ids + entrypoint」索引；供 W2-T2 routing eval cases 与后续 routing / eval 票只读引用。
  - **边界**：本票**不**实现 routing engine，**不**改 `ask_rag_selector`、Tabular selector/executor、HQ `_route_task` 或 `skills/*` 卡本体；四套 Catalog 命名空间保持分轨（见 spec §4）。
  - **Wave 关系**：Wave 1 提供治理 onboarding 与 MVP 主链 trace；Wave 3 提供 Tabular 工具层 Catalog / Selector / Executor；**Wave 2 本票**补齐「跨 family 路由规则索引」，与 T2 eval case 骨架并列，完成度对齐 W1/W3 文档 + SSOT + tests 三件套。
- progress_entry: |
    [W2-T1-intake-routing-catalog] done · 建立跨 family routing catalog（Tabular / Gov / product card / hq_routing）；新增 docs/intake-routing-catalog-v1.md + routing/intake_routing_catalog_v1.yaml + tests（10/10 OK）。Reviewer/Orchestrator accepted。
- followup_suggestions:
  - 新任務類型：先补 `intake_routing_catalog_v1.yaml` + spec 表，再开 CLI / Agent 实现票
  - W2-T2 已接續：以本 catalog 为权威写 `routing_eval_cases_v1.yaml`
  - 未来 Wave：可增加 `routing_catalog_loader.py` 或 CI runner 消费 YAML（本票 out of scope）
