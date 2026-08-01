# TICKET STATE · W-MVP-W1-INVENTORY · 最小接案 MVP · Wave 1 模块盘点与范围收口

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 1 — Inventory only（盘点／复用判断／范围收口；**禁止功能施工**）

---

## FRAME

- Goal: 围绕「最小接案 MVP（低风险表格型数据清洗接案）」，完成 8 类模块盘点与复用地图，明确 in/out scope 与 Wave 2 最先缺口；**不开发新模块**。
- Scope:
  - Module Reuse Check（A–H 八类）
  - MVP 复用地图 + 范围收口
  - Wave 2 优先缺口（2–4 项）
  - 本票 B_REPORT 回写
- NonScope:
  - 禁止新功能开发、禁止大重构、禁止改 `core/*` 逻辑
  - 不新建 production pipeline、自助入口、RAG 主路径
  - 不替代 C2-P1/P2/D1 既有 FRAME
- AllowedPaths:
  - `04_Workflows/tickets/W-MVP-W1-INVENTORY_state.md`（B_REPORT）
- BlockedPaths:
  - `core/*`、`skills/*`、`config/*`、`tests/*`（本票不施工）
  - `AGENTS.md`、`.cursor/rules/*`、`04_Workflows/00_Agent_Work_Progress.md`
- Dependencies:
  - C2-P1 `docs/PRODUCT_TABULAR_CLEANING.md`（done）
  - C2-P2 `docs/C2-P2_RUNBOOK.md`（in_review）
  - C2-D1 `cases/demo_phase/` + `clean_phase_demo.py`（in_progress）
  - Wave 6/7/8 CLEAN specs · W4-T1/T2（draft）
- AcceptanceCriteria:
  - 8 类模块均有 reuse 结论（direct_reuse / extend / missing）
  - 明确 in-scope / out-of-scope / preconditions / Wave 2 优先项
  - 无功能施工；仅 state 盘点回写

---

## STATE

- overall_status: in_progress
- implementation_status: inventory_done_pending_review
- current_owner: reviewer
- next_action: Reviewer 对照 AC 验收盘点结论；Orchestrator 依 Wave 2 建议开下一票
- last_updated: 2026-06-08 · implementer
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

### changed_files

- `04_Workflows/tickets/W-MVP-W1-INVENTORY_state.md`（新建 · FRAME/STATE/B_REPORT 盘点交付）

### inventory_summary

#### Step 0 — 盘点范围

| 范围 | 路径 | 与本 MVP 关系 |
|------|------|---------------|
| 产品／runbook | `docs/PRODUCT_TABULAR_CLEANING.md` · `docs/C2-P2_RUNBOOK.md` · `docs/C2-D1_DEMO_WALKTHROUGH.md` | C2 接案主锚 |
| Wave CLEAN 制度 | `04_Workflows/WAVE6_*` · `WAVE7_*` · `WAVE8_*` · `PHASE7_5_*` · `PHASE8_6_*` | prod 链规格（多 draft） |
| 控制面 dispatch | `04_Workflows/dispatch_executor.py` · `_dispatch_cards.py` · `scripts/run_dispatch_*.py` | 内部 Multi-Chat，非客户入口 |
| 清洗 demo | `notebooks/csv_cleaning/` · `cases/demo_phase/` | 唯一战車根可跑 tabular demo |
| Wave 8 CLI | `04_Workflows/_wave8_*.py` · `fixtures/intake_*.json` | intake→CleanJob 映射／提交（依赖暗部） |
| 状态／memory | `04_Workflows/tickets/*_state.md` · `workflow_v2/40_ticket_memory/` · `observability/wf_status_summary.py` | 内部 ticket SSOT |
| skills／tests | `skills/gov_cards/*` · `skills/cards/skill-clean-*` · `tests/test_dispatch_*` · `tests/test_wave8_*` | 工具 catalog／Wave8 测试 |
| artifacts | `artifacts/control_plane/` · `artifacts/wf/` · `cases/demo_phase/report.*` | 计划／状态／demo 交付样例 |

---

#### Step 1 — Module Reuse Check（8 类）

##### A. 客户入口 / Intake

| 项 | 内容 |
|----|------|
| **Existing assets** | C2-P1 §2 输入要求 · C2-P2 Runbook Stage A · `WAVE6_CLEAN_INTAKE_SCRIPT_v0.1.md` · `fixtures/intake_basic_sample.json` · `run_tabular_cleaning_plan.py --stage intake` |
| **Candidate paths** | `PHASE7_5_INTAKE_GATE_MVP_PLAN_v0.1.md` · `PHASE8_6_MINIMAL_ORCHESTRATION_BRIDGE_MVP_v0.1.md` · 暗部 `intake_decider.py`（spec 引用，不在战車根 `core/`） |
| **Reuse level** | **extend** |
| **Notes** | 接案**流程与清单已有**（C2-P2 + Wave6 script）；**无**客户自助上传／API／表单 UI。v1 接案 = 人工收档 + runbook checklist，不另造入口系统。 |

##### B. 输入校验 / Eligibility

| 项 | 内容 |
|----|------|
| **Existing assets** | `WAVE6_CLEAN_INTAKE_ELIGIBILITY_v0.1.md` · `WAVE6_CLEAN_PRODUCT_MATRIX_v0.1.md` · `fixtures/intake_basic_sample.json` · `_wave8_preview_clean_job_mapping.py`（映射校验） |
| **Candidate paths** | `_wave8_submit_clean_job.py` · W4-T1 `intake_gate_scorer`（draft，暗部） |
| **Reuse level** | **extend** |
| **Notes** | 规则**文档化 + fixture 样例**齐全；战車根**无**针对「低风险 tabular CSV」的一键 eligibility CLI。preview 仅验证 intake→CleanJob 映射，非 C2 业务 gate。 |

##### C. 搜索 / Retrieval / RAG

| 项 | 内容 |
|----|------|
| **Existing assets** | 战車根 `core/ask_rag_selector.py` · `kb_index_selector_hook.py` · `skills/gov_cards/kb_index_*` · `docs/ROUTING_POLICY_GUIDE.md` |
| **Candidate paths** | Wave B eval／trace 工具（内部 QC 可选） |
| **Reuse level** | **extend**（adjacent） |
| **Notes** | C2-P1 §6 明示清洗主路径**不依赖** Gov tool catalog／RAG。接案 MVP **不纳入** RAG；仅未来内部品控可选用。 |

##### D. 触发 / Dispatch / Runner

| 项 | 内容 |
|----|------|
| **Existing assets** | **内部控制面**：`dispatch_executor.py` · `_dispatch_cards.py` · `scripts/run_dispatch_*.py` · `artifacts/control_plane/dispatch_plan.latest.json` · **HQ**：`_route_task.py` · `_ops_cycle.py` · **CLEAN 链**：`_wave7_run_job.py` · `_wave8_submit_clean_job.py` · W4-T2（draft） |
| **Candidate paths** | `run_tabular_cleaning_plan.py`（pseudo CLI，列步骤不执行） |
| **Reuse level** | **extend** |
| **Notes** | dispatch cards = **Orchestrator→Implementer 内部 handoff**，非客户触发。客户案执行触发 = 人工按 C2-P2 跑 demo／Wave8 submit（后者需暗部 + W4-T2）。 |

##### E. 清洗执行

| 项 | 内容 |
|----|------|
| **Existing assets** | **`clean_phase_demo.py`**（可重跑 · `ok: true`）· `cases/demo_phase/*` · `skills/cards/skill-clean-basic-*` · Wave 6/7 runner 规格 |
| **Candidate paths** | 暗部 `code_cleaning_pipeline_v2` · W4-T2 e2e chain |
| **Reuse level** | demo：**direct_reuse**；prod 链：**extend** |
| **Notes** | 战車根**唯一**自包含 tabular 清洗器 = C2-D1 demo；文件自述 **NOT prod pipeline**。低风险 MVP 第一版可复用 demo 模式 + 人工规则扩展，不必先接 Wave7 orchestrator。 |

##### F. 人工确认 / Review gate

| 项 | 内容 |
|----|------|
| **Existing assets** | C2-P2 **4 个人工签核点**（#1 规则矩阵 → #4 Lead 交付）· Wave6 REVIEW bucket · Multi-Chat Reviewer 角色 · `_wave7_regression_gate.py` |
| **Candidate paths** | `delivery_signoff.md`（runbook 描述，**未落盘模板**） |
| **Reuse level** | **extend** |
| **Notes** | 流程 gate **direct_reuse**（runbook 已定义）；缺 **可提交签核文件模板** 与 case 级 signoff 落盘约定。 |

##### G. 交付 / Report / Output bundle

| 项 | 内容 |
|----|------|
| **Existing assets** | `cases/demo_phase/report.json` · `report.md` · `Phase_cleaned.csv` · `WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md` · `docs/CASE_REPORTS/C2-D1_*` · `_wave8_render_report_md.py` |
| **Candidate paths** | W4-T2 `delivery/<job_id>/` 布局（draft） |
| **Reuse level** | demo bundle：**direct_reuse**；prod bundle：**extend** |
| **Notes** | C2-D1 已对齐 C2-P1 §3.1 指标 + Wave6 骨架；缺 **case 目录标准化打包脚本**（zip／manifest）与 signoff 一并交付。 |

##### H. 状态追踪 / Memory / Case history

| 项 | 内容 |
|----|------|
| **Existing assets** | `04_Workflows/tickets/*_state.md`（35+）· `cases/demo_phase/` · `workflow_v2/40_ticket_memory/` · `observability/wf_status_summary.py` · `04_Workflows/Status.json` |
| **Candidate paths** | `03_RAG_Database/C3_Logs/` · Phase 7.5 Memory+1 spec |
| **Reuse level** | **extend** |
| **Notes** | 内部 ticket markdown SSOT **direct_reuse**；**无** tabular 客户案 registry（`cases/<client_ref>/` 仅 demo 一例）。接案 MVP 需 **case folder 约定**，不必新建 DB。 |

---

#### Step 2 — MVP 复用地图（摘要）

| 模块 | 现有资产 | 复用判断 | 缺口 | 建议波次 |
|------|----------|----------|------|----------|
| A Intake | C2-P2 Stage A · Wave6 intake script | extend | 无客户通道；需 case 级 intake 清单落盘 | **Wave 2** |
| B Eligibility | Wave6 eligibility doc · intake fixtures | extend | 无低风险 tabular 可执行 gate CLI | **Wave 2** |
| C RAG | 战車根 ask/KB 栈 | extend（非主路径） | 无缺口（v1 不做） | Out |
| D Dispatch | dispatch_executor/cards · Wave8 submit | extend | 客户触发 = 人工；prod 链待 W4-T2 | Wave 3+ |
| E Cleaning | `clean_phase_demo.py` | demo direct_reuse | 参数化 case dir；非 demo 规则配置 | **Wave 2** |
| F Review gate | C2-P2 四签核点 | extend | `delivery_signoff.md` 模板缺失 | **Wave 2** |
| G Delivery | demo report bundle · Wave6 templates | demo direct_reuse | 打包脚本 + manifest | **Wave 2** |
| H Case history | ticket state · demo case | extend | `cases/` 目录约定 + registry 索引 | **Wave 2** |

**复用锚点（禁止重造）**

1. 产品边界：`docs/PRODUCT_TABULAR_CLEANING.md` + `docs/C2-P2_RUNBOOK.md`
2. 演示闭环：`cases/demo_phase/` + `notebooks/csv_cleaning/clean_phase_demo.py`
3. 指标契约：`WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md` + C2-P1 §3.1
4. 内部编排：`04_Workflows/tickets/*_state.md` + dispatch_executor（非客户面）

---

#### Step 3 — MVP 范围收口

**In scope（第一版一定做）**

- 低风险单表 CSV（UTF-8，≤ C2-P1 §2.4 规模假设）
- 人工驱动四阶段：Intake → Cleaning → Quality Report → Delivery（C2-P2）
- 四人工签核点必过
- 交付包：`cleaned.csv` + `report.json` + `report.md` + 规则摘要
- Case 落盘：`cases/<client_ref>/`（以 demo_phase 为模板）
- 内部 ticket state 追踪施工（Multi-Chat SSOT）

**Out of scope（第一版明确不做）**

- 客户自助上传／API／Web UI
- Wave 7/8 全自动 orchestrator 作为 v1 硬依赖
- ENRICH／OCR／PDF／多表 join
- RAG／KB index 作为主路径
- SLA／7×24／无人值守宣称为
- 新建 `core/` 清洗引擎或重复实现 dark pipeline

**Preconditions（进入 Wave 2 前）**

- C2-P2 Reviewer `accepted*`（runbook 为执行 SSOT）
- C2-D1 Reviewer `accepted*`（demo 锚点稳定）
- 「低风险 profile」书面定义：对齐 `WAVE6_CLEAN_INTAKE_ELIGIBILITY` ACCEPT 条件 + C2-P1 §2.4
- Orchestrator 确认 Wave 2 走 **战車根 manual case 链** 而非等待 W4-T2 prod e2e

**Risks / open questions**

- W4-T2（intake→delivery prod）与 manual MVP **并行可能重复** → Wave 2 应 extend demo/case 模式，不 fork 第二套清洗逻辑
- `delivery_signoff.md` 谁维护（PM vs Scribe）待 Orchestrator 指定
- C2-P2 / C2-D1 尚在 review/in_progress，Wave 2 开工前需收口

---

#### Step 4 — Wave 2 建议（最短闭环，2–4 项）

| 优先级 | 缺口 | 做法 | 复用来源 |
|--------|------|------|----------|
| **P1** | Case folder + intake 清单落盘 | 从 `cases/demo_phase/` 抽 `_TEMPLATE_case/`；扩展 `run_tabular_cleaning_plan.py` 输出 intake checklist JSON | C2-D1 · C2-P2 Stage A |
| **P2** | 低风险 eligibility 可执行检查 | 薄 CLI：CSV 存在性／编码／列数／规模 vs C2-P1 §2.4 + Wave6 ACCEPT 规则 | `WAVE6_CLEAN_INTAKE_ELIGIBILITY` · fixtures |
| **P3** | 参数化清洗 runner | 泛化 `clean_phase_demo.py` → `--case-dir`；规则仍 demo 级，人工签核补业务规则 | `clean_phase_demo.py` |
| **P4** | 交付 bundle + signoff 模板 | 新增 `delivery_signoff.md` 模板 + 打包脚本（csv+report+manifest） | Wave6 templates · `_wave8_render_report_md.py` |

**刻意后排**：W4-T1 intake gate scorer · W4-T2 prod e2e · dispatch cards（内部效率，非客户闭环）· RAG QC

---

### artifacts

- 本票 state 文件即盘点交付物；无代码／无 runner 变更

### verification

- 本轮 **仅盘点与 state 回写**，无功能施工
- 盘点依据：已读 `tickets/README.md` · `ticket_state.template.md` · C2-P1/P2/D1 state · W4-T1/T2 state · `PRODUCT_TABULAR_CLEANING.md` · `C2-P2_RUNBOOK.md` · `clean_phase_demo.py` · `intake_basic_sample.json` · `dispatch_executor.py` · `_wave8_preview_clean_job_mapping.py` · 目录 glob（docs/04_Workflows/scripts/tests/artifacts/skills/cases/notebooks）
- 未执行 pytest／清洗命令（非本票 AC）

### behavior_notes

- 未发现既有「最小接案 MVP 盘点」票；新建 `W-MVP-W1-INVENTORY` 供 Wave 2 延续
- 「Wave 1」在本 repo 亦指 Governance/Observability（W1-T*）；本票 Wave 1 = **MVP 盘点波**，与 W1-T* 不冲突
- 冲突裁决：以 C2 产品线 + C2-P2 runbook 为接案 MVP 权威，Wave 6/7/8 prod 链为 extend 目标而非 v1 阻塞

### deferred_items

- Wave 2 四票拆分（P1–P4）由 Orchestrator 开 FRAME
- W4-T2 prod e2e 独立 commercialization 轨，不并入 MVP v1 关键路径
- C2-P2 Reviewer 验收后再冻结 Wave 2 AllowedPaths

---

## C_REPORT

- conclusion: accepted_with_minor_edits
- blocking_issues:
  - 无（盘点票本身无功能施工，AC 已满足；Wave 2 **开票**可 proceed）
  - **Wave 2 施工**仍受前置票约束：C2-P2（`in_review` · Reviewer pending）、C2-D1（B_REPORT 完成 · Reviewer pending）须 `accepted*` 后再冻结 AllowedPaths 开工（B_REPORT Preconditions 已列，非本票 revision 理由）
- checks_summary:
  - **AC-1 · 8 类 reuse 结论**：A–H 均有 `direct_reuse` / `extend` / Out 判定与 Notes；复用地图 Step 2 与 Step 1 一致。抽样：`clean_phase_demo.py`、`run_tabular_cleaning_plan.py`、`cases/demo_phase/*`、`WAVE6_CLEAN_INTAKE_ELIGIBILITY_v0.1.md`、`dispatch_executor.py` 路径存在且角色描述准确。
  - **AC-2 · in/out scope**：Step 3 明确 in（低风险单表 CSV、四阶段、四签核、交付包、case 落盘）与 out（自助入口、Wave7/8 硬依赖、ENRICH/OCR/RAG 主路径、SLA）；preconditions 与 risks 可支撑 Orchestrator 裁 Wave 2 轨。
  - **AC-3 · 避免重复开发**：四条复用锚点 + 「W4-T2 prod e2e 刻意后排 Wave 3+」+ dispatch cards 标内部 + 「extend demo/case 不 fork 第二套清洗逻辑」— 与 W4-T1/T2（draft）、W-next-DISPATCH-CARDS（draft）对照一致，方向正确。
  - **AC-4 · Wave 2 P1–P4 最短闭环**：P1 case/intake → P2 eligibility → P3 参数化 runner → P4 bundle/signoff 覆盖 A/B/E/F/G/H 缺口；C 标 Out；D 标 Wave 3+。**无需重排优先级**（P4 依赖 P3 产出；P1 模板宜先于 P2 gate 落盘路径）。
  - **AC-5 · blocking ambiguity**：无「会导致 Wave 2 做错方向」级缺口。残余为非阻塞：F 模块 reuse 标签 `extend` 与 Notes「流程 gate direct_reuse」略不一致；H「registry 索引」仅 P1 隐含、未单列；「低风险 profile」书面化留 P2 票 FRAME 即可；`delivery_signoff.md` 维护者待 O 指定。
  - **边界**：仅改 `W-MVP-W1-INVENTORY_state.md` B_REPORT，符合 FRAME AllowedPaths；无 code/docs 施工。
- risk_level: low
- suggestions:
  - **Orchestrator · Wave 2 开票前（小修，非重做盘点）**：（1）在 Step 3 Preconditions 补一句：「低风险 profile」= `WAVE6_CLEAN_INTAKE_ELIGIBILITY` ACCEPT 区间 ∩ C2-P1 §2.4，由 **Wave 2 P2 票 FRAME** 引用，不必另开 W1 轮次。（2）P1 FRAME 显式含 `cases/README.md` 或 `cases/index.json` stub，收口 H registry。（3）P4 FRAME 指定 `delivery_signoff.md` 模板落盘路径（建议 `04_Workflows/tickets/_templates/` 或 `cases/_TEMPLATE_case/`）与维护角色（PM vs Scribe）。
  - **P1–P4 拆分**：维持四票顺序；若 P1+P2 过薄可合并为单票「Case bootstrap + eligibility gate」，但非必须。
  - **依赖同步**：FRAME Dependencies 中 C2-P2/C2-D1 状态可随各票 Reviewer 收口后由 O 更新 STATE，不影响本 C 结论。
  - **下一棒**：Scribe D_REPORT + Progress 摘要；O 更新 STATE（`reviewer: done`、`overall_status: scribe` 或关票）；并行推进 C2-P2/C2-D1 Reviewer 收口后再开 Wave 2 Implementer。

---

## D_REPORT

<!-- Scribe 填 -->

- docs_updates:
- progress_entry:
- followup_suggestions:
