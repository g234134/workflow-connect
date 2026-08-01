# TICKET STATE · WB-T1 · tool-catalog-and-selector-contract-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Phase 8.6（Tool Catalog SSOT）· Phase 8.7（Selector 推荐契约）

---

## FRAME

- Goal: 在 W3-TL-T1/T2、W9-T3 既有实现之上，升格 `docs/tool-catalog-and-selector-contract-v1.md` 为 Wave B/C 可引用的 catalog + selector 单一契约；明确四轨分离与 `governed_by` 字段语义；提供 contract unittest 防止 tool_id 命名空间漂移。
- Scope:
  - 新建 `docs/tool-catalog-and-selector-contract-v1.md`（§1–§7）
  - `docs/tabular-tool-catalog-v1.md` · `docs/tabular-tool-selector-spec.md` §0 指针
  - `docs/non-tabular-routing-catalog-v1.md` 交叉引用（不改 YAML）
  - 唯读校验 `tools/tabular_tool_catalog_v1.json` · `tools/non_tabular_tool_catalog_v1.json`
  - 新建 `tests/test_tool_catalog_and_selector_contract_v1.py`（≥12 断言）
  - `04_Workflows/WORKFLOW_INDEX.md` §1.5 增条 · `docs/WAVE_PROGRESS_DASHBOARD.md` Wave B 区块
- NonScope:
  - 不改 `tools/tabular_tool_selector.py` / `select_non_tabular_tools` 行为逻辑
  - 不改 MVP 主链 / UI / Gov core smoke
  - 不合并 Gov Registry（obs.*/kb.*）或 Phase 8.8（llm.*）进 tabular JSON
  - 不改 eval-gate-ci.yml / INT gate 门槛
  - 不新增 tool 类型或 executor 接线；不引入 Prometheus/Grafana
- AllowedPaths:
  - `docs/tool-catalog-and-selector-contract-v1.md`
  - `docs/tabular-tool-catalog-v1.md`（§0 指针）
  - `docs/tabular-tool-selector-spec.md`（§0 指针）
  - `docs/non-tabular-routing-catalog-v1.md`（交叉引用）
  - `tests/test_tool_catalog_and_selector_contract_v1.py`
  - `04_Workflows/tickets/WB-T1-tool-catalog-and-selector-contract-v1_state.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（§1.5）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
- BlockedPaths:
  - `tools/tabular_tool_selector.py` · `tools/non_tabular_tool_selector_v1.py`
  - `tools/tabular_tool_catalog_v1.json` · `tools/non_tabular_tool_catalog_v1.json`（内容扩展）
  - `.github/workflows/*` · MVP 主链 scripts · `core/*`
- Dependencies: W3-TL-T1 · W3-TL-T2 · W9-T3 · W4-T1（唯读）· WA-T4 · WA-T1 P2
- AcceptanceCriteria:
  - **AC-1**：contract 含 §1 范围、§2 四轨表、§3 命名、§4 selector dict、§5 P4 交叉引用
  - **AC-2**：Tabular SSOT = `tools/tabular_tool_catalog_v1.json`；NT SSOT = `tools/non_tabular_tool_catalog_v1.json`
  - **AC-3**：contract unittest 全绿（schema、必填键、禁止混用 ID）
  - **AC-4**：既有 unittest 不回歸
  - **AC-5**：`python -m unittest tests.test_tool_catalog_and_selector_contract_v1 -v` OK
  - **AC-6**：tabular-tool-catalog-v1.md 文首 contract 指针
  - **AC-7**：Dashboard Phase 8.6 65%→85%、8.7 60%→85%
  - **AC-8**：FRAME 填齐；B_REPORT 附验证命令
  - **AC-9**：contract §6 Wave C 假设
  - **AC-10**：对齐 phase4 contract §3 Implementer allowed paths

---

## STATE

- overall_status: done
- current_owner: orchestrator
- next_action: 無（票面已收口；Toolchain Wave B closure complete）
- last_updated: 2026-06-11 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files:
  - `docs/tool-catalog-and-selector-contract-v1.md`（新建）
  - `tests/test_tool_catalog_and_selector_contract_v1.py`（新建）
  - `docs/tabular-tool-catalog-v1.md`（§0 contract 指针）
  - `docs/tabular-tool-selector-spec.md`（§0 contract 指针）
  - `docs/non-tabular-routing-catalog-v1.md`（交叉引用）
  - `04_Workflows/WORKFLOW_INDEX.md`（§1.5 WB-T1 条目）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（Toolchain Wave B 区块 · P8.6/P8.7 进度）
  - `04_Workflows/tickets/WB-T1-tool-catalog-and-selector-contract-v1_state.md`
- artifacts: `docs/tool-catalog-and-selector-contract-v1.md`
- verification:
  - `python -m unittest tests.test_tool_catalog_and_selector_contract_v1 -v` → **15/15 OK**
  - `python -m unittest tests.test_tabular_tool_catalog tests.test_tabular_tool_selector tests.test_non_tabular_tool_selector_v1 -v` → **28/28 OK**（AC-4 不回歸）
- behavior_notes:
  - contract 定跨轨 SSOT；Tabular/NT 旧 spec 降为实现附录；`plan_only: true` 为文档语义（未改 selector 实现）
  - unittest 校验四轨命名空间、catalog JSON schema、selector 必填键、禁止 tabular/NT ID 碰撞与 llm.*/obs.*/kb.* 混入 tabular JSON
  - 未扩展 catalog tool 清单；未改 selector 行为或 CI
- deferred_items:
  - Wave C prod selector 接线（WB-T2+）
  - selector 返回 dict 显式 `plan_only` 键（需另票改实现；本票仅 contract 文档化）
  - WB-T4 dashboard 消费 `catalog_tool_count` / `selector_candidate_count`

---

## C_REPORT

- conclusion: **accepted_with_gaps**
- blocking_issues: **无**
- checks_summary:
  - **FRAME**：未被 Implementer 改动；Goal/Scope/NonScope/AllowedPaths/BlockedPaths/AC-1–AC-10 与交付一致。
  - **B_REPORT 证据**：`tests.test_tool_catalog_and_selector_contract_v1` **15/15 OK**（Reviewer 复跑）；回归 `test_tabular_tool_catalog` + `test_tabular_tool_selector` + `test_non_tabular_tool_selector_v1` **28/28 OK**。
  - **AC 对照**：contract 含 §1–§7（四轨表 §2、命名 §3、selector dict §4、P4 交叉引用 §5、Wave C §6）；Tabular/NT SSOT 指向 JSON；`tabular-tool-catalog-v1.md` / `tabular-tool-selector-spec.md` 文首指针已交付；Dashboard P8.6/P8.7 进度已更新；ForbiddenChanges 遵守（未改 selector 实现 / catalog JSON / CI）。
  - **Rule 3/8**：变更均在 AllowedPaths；未触 BlockedPaths。
- risk_level: **low**
- suggestions:
  - **缺但可接受**：selector 返回 dict 无显式 `plan_only` 键（文档语义 vs 实现）；`catalog_tool_count` dashboard hook 留 WB-T4 deferred。
  - 无 blocking；可交 Scribe 收口。

---

## D_REPORT

- docs_updates:
  - Dashboard Toolchain 分栏状态列已对齐 Reviewer 关票口径（WC-PRE-01）
  - 交叉引用：`docs/wave-b-toolchain-readme-v1.md` · `docs/WAVE_B_TOOLCHAIN_EXECUTION_PLAN.md` §5
- progress_entry: WB-T1 交付四轨 catalog+selector contract SSOT（`tests.test_tool_catalog_and_selector_contract_v1` 15/15 OK）；`plan_only` 为文档语义，未改 selector 实现。
- followup_suggestions:
  - **WC-PRE-02**：selector 返回 dict 显式 `plan_only` 键
  - **WB-T4 deferred**：dashboard 消费 `catalog_tool_count` / `selector_candidate_count`
