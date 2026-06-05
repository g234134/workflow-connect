     1|     1|# 90 Run Queue — Workflow v2（最终 AI 导入）
     2|     2|
     3|     3|> **权威**：本目录任务状态以本档为准。  
     4|     4|> **总览**：`workflow_v2/00_master_plan.md`  
     5|     5|> **状态字汇**：`TODO` | `DOING` | `BLOCKED` | `DONE`  
     6|     6|> **更新规则**：施工票仅改 **Status** 与 **Notes**；不删历史行。总控可增行、调 Depends。
     7|     7|
     8|     8|---
     9|     9|
    10|    10|## 栏位说明（E1-2 schema）
    11|    11|
    12|    12|| 栏位 | 说明 |
    13|    13||------|------|
    14|    14|| **ID** | 任务代号（E1-* / G6-* …） |
    15|    15|| **Title** | 一句话标题 |
    16|    16|| **Wave** | `W0` / `W1` / `W2` / `W3` / `W4` / `FUTURE` |
    17|    17|| **Module** | `E1` / `G6` / `G7` / `G8` / `G10` |
    18|    18|| **Role** | `orchestrator` / `worker` / `checker` |
    19|    19|| **Status** | `TODO` / `DOING` / `BLOCKED` / `DONE` |
    20|    20|| **Depends on** | 前置任务 ID（无则 `-`） |
    21|    21|| **Output File** | 预期产物（相对战车根） |
    22|    22|| **Notes** | 派工、阻塞、对账 |
    23|    23|
    24|    24|---
    25|    25|
    26|    26|## Wave 0 — E1 总体治理骨架
    27|    27|
    28|    28|| ID | Title | Wave | Module | Role | Status | Depends on | Output File | Notes |
    29|    29||----|-------|------|--------|------|--------|------------|-------------|-------|
    30|    30|| E1-1 | 更新 master plan 结构 | W0 | E1 | orchestrator | DONE | - | `workflow_v2/00_master_plan.md` | 2026-05-27 总控轮：Wave 0/1 目标与模块表 |
    31|    31|| E1-2 | 更新 run queue schema | W0 | E1 | orchestrator | DONE | E1-1 | `workflow_v2/90_run_queue.md` | 本档；含 Wave/Module/Role 栏 |
    32|    32|| E1-4 | 定义模块依赖与阶段顺序 | W0 | E1 | orchestrator | DONE | E1-2 | `workflow_v2/02_dependency_map.md` | 含 mermaid 与硬/软依赖 |
    33|    33|| E1-5 | 定义协调 / 施工 / checker chat 规则 | W0 | E1 | orchestrator | DONE | E1-4 | `workflow_v2/03_parallel_execution_rules.md` | 三角色 + T0–T3 并行批次 |
    34|    34|
    35|    35|**Wave 0 出口**：上表四票 `DONE`；`99_latest_status.md` 已同步。
    36|    36|
    37|    37|---
    38|    38|
    39|    39|## Wave 1 — G6 Scope Control
    40|    40|
    41|    41|| ID | Title | Wave | Module | Role | Status | Depends on | Output File | Notes |
    42|    42||----|-------|------|--------|------|--------|------------|-------------|-------|
    43|    43|| G6-1 | 定义 AI change classes | W1 | G6 | worker | DONE | E1-5 | `workflow_v2/10_governance/G6_scope_control/10_change_classes.md` | 2026-05-27：8×CHG-* + §2 与 deny/gate/status 边界；未写 allowed actions；G6-2 可发车 |
    44|    44|| G6-2 | 定义每类 change 的允许动作 | W1 | G6 | worker | DONE | G6-1 | `workflow_v2/10_governance/G6_scope_control/20_allowed_actions.md` | 2026-05-27：§4 八行 CHG-* + ACT-* 词表 + §5 升级/blocked/handoff；G10-2/CHK-W1 可引用 |
    45|    45|
    46|    46|---
    47|    47|
    48|    48|## Wave 1 — G7 State Machine
    49|    49|
    50|    50|| ID | Title | Wave | Module | Role | Status | Depends on | Output File | Notes |
    51|    51||----|-------|------|--------|------|--------|------------|-------------|-------|
    52|    52|| G7-1 | 定义全状态列表 | W1 | G7 | worker | DONE | E1-5 | `workflow_v2/10_governance/G7_state_machine/10_workflow_states.md` | 2026-05-27：10 个 IMP-* + 命名空间 §1；不含 entry/exit |
    53|    53|| G7-2 | 定义每个状态 entry 条件 | W1 | G7 | worker | DONE | G7-1 | `workflow_v2/10_governance/G7_state_machine/20_entry_conditions.md` | 2026-05-27：10 态 entry + §3 全局/owner/blocker + §6 G8 占位对账；不含 exit |
    54|    54|| G7-3 | 定义每个状态 exit 条件 | W1 | G7 | worker | DONE | G7-1 | `workflow_v2/10_governance/G7_state_machine/30_exit_and_transitions.md` | 2026-05-27：10 态 exit+迁移矩阵+REWORK；G8 占位对账表；ART-REL-* 待 G8-5 |
    55|    55|
    56|    56|---
    57|    57|
    58|    58|## Wave 1 — G8 Artifact Contract
    59|    59|
    60|    60|| ID | Title | Wave | Module | Role | Status | Depends on | Output File | Notes |
    61|    61||----|-------|------|--------|------|--------|------------|-------------|-------|
    62|    62|| G8-1 | 定义 PM artifact contract | W1 | G8 | worker | DONE | E1-5 | `workflow_v2/10_governance/G8_artifact_contract/10_pm.md` | G8-B v0.1：ART-PM-* 四件；IMP-* 占位待 G7 对账 |
    63|    63|| G8-2 | 定义 Design artifact contract | W1 | G8 | worker | DONE | E1-5 | `workflow_v2/10_governance/G8_artifact_contract/20_design.md` | G8-B v0.1：ART-DES-* 三件；peer review 对齐 G7-3 |
    64|    64|| G8-3 | 定义 Engineering artifact contract | W1 | G8 | worker | DONE | E1-5 | `workflow_v2/10_governance/G8_artifact_contract/30_engineering.md` | G8-A v0.1：ART-ENG-* 六件；IMP-* 占位待 G7 对账 |
    65|    65|| G8-4 | 定义 QA artifact contract | W1 | G8 | worker | DONE | E1-5 | `workflow_v2/10_governance/G8_artifact_contract/40_qa.md` | G8-A v0.1：ART-QA-* 五件；复用 checker-reviewer + ops_cycle_schema |
    66|    66|| G8-5 | 定义 Release owner artifact contract | W1 | G8 | worker | DONE | E1-5 | `workflow_v2/10_governance/G8_artifact_contract/50_release_owner.md` | G8-B v0.1：ART-REL-* 三件；不含完整 release gate；ART-REL-RECORD→EXEC 待 G7-2 对账 |
    67|    67|
    68|    68|---
    69|    69|
    70|    70|## Wave 1 — G10 Governance Rulebook
    71|    71|
    72|    72|| ID | Title | Wave | Module | Role | Status | Depends on | Output File | Notes |
    73|    73||----|-------|------|--------|------|--------|------------|-------------|-------|
    74|    74|| G10-1 | 定义 AI usage boundary | W1 | G10 | worker | DONE | E1-5 | `workflow_v2/10_governance/G10_governance_rulebook/10_ai_usage_boundary.md` | 2026-05-27：v0.1 §3–§7 宜/不宜+guard/checker/owner+三权+CHG 引用步骤；基于 G6-1/2；G10-2 可发车 |
    75|    75|| G10-2 | 定义禁止直接信任 AI output 的情境 | W1 | G10 | worker | DONE | G10-1 | `workflow_v2/10_governance/G10_governance_rulebook/20_no_blind_trust.md` | 2026-05-27：v0.1 §2 NBT-* + §3 NBT-H-* + §4 停工矩阵 + §5 G6/G10-1/G7/G8 引用；IMP-RISK-VALIDATION/CHK-W1 可引用 |
    76|    76|
    77|    77|---
    78|    78|
    79|    79|## Checker 盘点票（可选挂票）
    80|    80|
    81|    81|| ID | Title | Wave | Module | Role | Status | Depends on | Output File | Notes |
    82|    82||----|-------|------|--------|------|--------|------------|-------------|-------|
    83|    83|| CHK-W1 | Wave 1 治理层只读盘点 | W1 | — | checker | DONE | G6-2, G7-3, G8-5, G10-2 | `workflow_v2/99_latest_status.md` | 2026-05-27：**PASS-WITH-NOTES**；12 票正文齐；R2/R3/R4 关闭；R1 部分关闭；开 G8-RECON-IMP 后封板 |
    84|    84|
    85|    85|---
    86|    86|
    87|    87|## Wave 1 收尾（CHK-W1 后 · 小票）
    88|    88|
    89|    89|| ID | Title | Wave | Module | Role | Status | Depends on | Output File | Notes |
    90|    90||----|-------|------|--------|------|--------|------------|-------------|-------|
    91|    91|| G8-RECON-IMP | G7↔G8 交叉引用 cleanup | W1 | G8 | worker | TODO | CHK-W1 | `G7_state_machine/` + `G8_artifact_contract/30_engineering.md` | P0 实质施工 **并入 W2-1-ENG**；本行保留索引；收口时 Notes 指向 W2-1-ENG |
    92|    92|| E1-6 | 总控索引文件名对齐 | W0 | E1 | orchestrator | TODO | CHK-W1 | `00_master_plan.md`、`02_dependency_map.md`、`03_parallel_execution_rules.md` | P1：`00`/`02` 已对齐 `90` Output；**待** `03` 示例路径；可与 W2-1 并行 |
    93|    93|
    94|    94|---
    95|    95|
    96|    96|## Wave 2 — W2-1 最小闭环 Sprint
    97|    97|
    98|    98|| ID | Title | Wave | Module | Role | Status | Depends on | Output File | Notes |
    99|    99||----|-------|------|--------|------|--------|------------|-------------|-------|
   100|   100|| W2-1-ORCH | W2-1 总控入口与 IMP 索引 | W2 | E1 | orchestrator | DONE | CHK-W1 | `00_master_plan.md` §9；`20_pilot/W2-1_imp_flow_and_artifacts.md`；`20_pilot/W2-1_case/` | 2026-05-27：试点案 G8-RECON-IMP 全链；不写 ART 正文 |
   101|   101|| W2-1-PM-DES | PM+Design：范围与规格 | W2 | PM/DES | worker | DONE | W2-1-ORCH | `20_pilot/W2-1_case/01–03_*`；`W2-1_case.md` | 2026-05-27：**ART-PM-SCOPE/CLARIFY/GAPS**、**ART-DES-SPEC** 落盘；IMP **SPEC-CLARIFY exit** → 待 **AI-READY** entry；G8 PM/Design 附录 A 实例索引 |
   102|   102|| W2-1-ENG | Eng：对账 diff + 工程 artifact | W2 | ENG | worker | TODO | W2-1-PM-DES | `10_governance/G7_state_machine/` + `G8_artifact_contract/30_engineering.md`；`20_pilot/W2-1_case/04–05_*` | **ART-ENG-CTX/WR/FIVE/EVD/DOD**；G8-RECON-IMP 实质；→ **IMP-QA-READY**；只读改 stale 引用，不改治理语义 |
   103|   103|| W2-1-QA-REL | QA+Release：验收与内部发布 | W2 | QA/REL | worker | DONE | W2-1-ENG | `20_pilot/W2-1_case/06–10_*` | QA **accepted_with_gaps**；Release **approve**（internal-doc-authority）；IMP → **IMP-OBSERVING**；gaps: ART-GOV-RISK→W2-3 |
   104|   104|
   105|   105|**W2-1 依赖链**：`W2-1-ORCH` → `W2-1-PM-DES` → `W2-1-ENG` → `W2-1-QA-REL`
   106|   106|
   107|   107|**W2-1 出口**：`IMP-OBSERVING`；案卷 `20_pilot/W2-1_case/` 全链 ART 已登记（2026-05-27）。
   108|   108|
   109|   109|---
   110|   110|
   111|   111|## Wave 2 — W2-2 imp_state + tooling（规格已交付 · 子票待施工）
   112|   112|
   113|   113|| ID | Title | Wave | Module | Role | Status | Depends on | Output File | Notes |
   114|   114||----|-------|------|--------|------|--------|------------|-------------|-------|
   115|   115|| W2-2 | imp_state + helper tooling（总控规格） | W2 | E1/G7 | orchestrator | DONE | W2-1-QA-REL | `00_master_plan.md` §9.3–§10；`20_pilot/W2-2_*`；`tools/wf_check_cross_ref.ps1`；`G7_state_machine/40_imp_state_field_v0.1.md` | 2026-05-27：v0.1 schema + AC helper + NBT 清单；**无** CI；子票见下表 |
   116|   116|| W2-2-IMP-FIELD | 落盘 `imp_state` 字段（案卷模板 + 对账） | W2 | G7 | worker | DONE | W2-2 | `20_pilot/_TEMPLATE_case/`；`W2-1_case/W2-1_case.md`；`G7_state_machine/40_imp_state_field_v0.1.md` §4 | 2026-05-27：模板就绪（§2 `imp_state_current` + §3 `imp_state_transitions`）；W2-1 已对齐；后续 case 复制模板 |
   117|   117|| W2-2-HELPER-SCRIPTS | AC grep helper 工程化 | W2 | ENG | worker | TODO | W2-2 | `workflow_v2/tools/wf_check_cross_ref.ps1`；`20_pilot/W2-2_tooling_notes.md` | 验证脚本在干净环境可跑；补 CHG-GOV-DOC 以外票的 pattern 配置；写入 G8-4 附录引用（若授权） |
   118|   118|| W2-2-QA-CHECKLIST | no-blind-trust 清单工程化 | W2 | G10/QA | worker | TODO | W2-2 | `20_pilot/W2-2_tooling_notes.md` §4；`G10_governance_rulebook/20_no_blind_trust.md`（索引行，若授权） | NBT-T01～T07 → checker 可勾选表／ART-QA-REV 字段建议；**不**实现完整 gate |
   119|   119|
   120|   120|**W2-2 依赖链**：`W2-2`（总控 DONE）→ 三支子票可并行（注意 G10 索引票宜 checker 只读对账）
   121|   121|
   122|   122|---
   123|   123|
   124|   124|## Wave 2 — W2-3 ART-GOV-RISK + minimal gate（规格已交付 · 子票待施工）
   125|   125|
   126|   126|| ID | Title | Wave | Module | Role | Status | Depends on | Output File | Notes |
   127|   127||----|-------|------|--------|------|--------|------------|-------------|-------|
   128|   128|| W2-3 | ART-GOV-RISK + minimal gate（总控规格） | W2 | G8/G10 | orchestrator | DONE | W2-1-QA-REL | `G8_artifact_contract/60_gov_risk.md`；`G10_governance_rulebook/20_no_blind_trust.md`；`20_pilot/W2-3_minimal_gate_design.md`；`00` §11 | 2026-05-27：GOV 轨契约 v0.1 + gate 设计；**无** 脚本／案卷实例 |
   129|   129|| W2-3-GOV-RISK-CONTRACT | 落盘 ART-GOV-RISK 契约与 G8 注册 | W2 | G8 | worker | DONE | W2-3 | `G8_artifact_contract/60_gov_risk.md`；`README.md` | **总控已合并**；子票仅索引；checker 对字段表 |
   130|   130|| W2-3-GOV-RISK-PILOT | 试点案卷 ART-GOV-RISK 实例 | W2 | GOV | worker | TODO | W2-3-GOV-RISK-CONTRACT | `20_pilot/W2-3_case/`（待建） | 仿 W2-1 RISK 段；替换 WR fallback；可 backfill W2-1_case 注释 |
   131|   131|| W2-3-MINIMAL-GATE-DESIGN | 最小治理 gate 设计 | W2 | E1/G10 | worker | DONE | W2-3 | `20_pilot/W2-3_minimal_gate_design.md` | **总控已合并**；W3：`wf_gov_gate` 实现 |
   132|   132|| W2-3-MINIMAL-GATE-IMPL | gate 脚本／可选 CI | W3 | ENG | worker | DONE | W2-3-MINIMAL-GATE-DESIGN；W2-3-GOV-RISK-PILOT | `workflow_v2/tools/wf_gov_gate.ps1` | v0.1 原型：GATE-RISK-EXIT + GATE-REL-ENTRY；stdout only；CI → Wave 3 |
   133|   133|
   134|   134|**W2-3 依赖链**：`W2-3`（总控 DONE）→ `W2-3-GOV-RISK-PILOT`；`W2-3-MINIMAL-GATE-IMPL` 原型 DONE → **W3-C-CI-GATE-WIRE** 接线
   135|   135|
   136|   136|---
   137|   137|
   138|   138|## Wave 3 — 总控开盘（W3-0-ORCH）
   139|   139|
   140|   140|| ID | Title | Wave | Module | Role | Status | Depends on | Output File | Notes |
   141|   141||----|-------|------|--------|------|--------|------------|-------------|-------|
   142|   142|| W3-0-ORCH | Wave 3 总控落盘（§13 + 队列 + 依赖） | W3 | E1 | orchestrator | DONE | W2-3, W2-2, W2-1-QA-REL | `00_master_plan.md` §13；`02_dependency_map.md` §8；`90` 本节；`99_latest_status.md` | 2026-05-27：正式开盘；**无** production 实现 |
   143|   143|
   144|   144|---
   145|   145|
   146|   146|## Wave 3 — W3-A Rollout / Canary（K-2 × ask 默认）
   147|   147|
   148|   148|| ID | Title | Wave | Module | Role | Status | Depends on | Output File | Notes |
   149|   149||----|-------|------|--------|------|--------|------------|-------------|-------|
   150|   150|| W3-A-ORCH | 主线 A 编排骨架（shadow + canary） | W3 | K2/REL | orchestrator | DONE | W3-0-ORCH | `30_rollout/`（README、phase_map、boundary、schema、allowed_paths）；`20_pilot/W3-A_case/` | 2026-05-27：仅文档骨架；**无** rollout 脚本。邻接根 plan §4.8、`docs/k2_deployment_governance.md`（只读）；不重开 G6–G10 全文 |
   151|   151|| W3-A-SHADOW-PILOT | K-2 × ask shadow 试点 ≥1 次 | W3 | K2 | worker | TODO | W3-A-ORCH | `20_pilot/W3-A_case/shadow_run_*.md`；`30_rollout/phase_map_k2_ask.md` §2 | **目标**：shadow ≥7 自然日 + 可回溯 run 案卷。**禁区**：prod 主答案、改 merge adapter。**软依赖**：W3-B-INDEX-PIPELINE（index 可查）。**窄上下文** |
   152|   152|| W3-A-REMOTE-ENV | internal canary 环境／cohort 定义 | W3 | INFRA | worker | TODO | W3-A-ORCH | `30_rollout/env/`；`20_pilot/W3-A_case/canary_env.md`；Runbooks 单节（可选） | **目标**：env 逻辑名 + smoke 清单（零密钥）。**禁区**：`.env`/venv/secret、远端 prod 自动 rollout。**可与 shadow 并行**。**窄上下文** |
   153|   153|| W3-A-CANARY-PILOT | internal canary 试点 ≥1 次 | W3 | K2 | worker | TODO | W3-A-SHADOW-PILOT, W3-A-REMOTE-ENV | `20_pilot/W3-A_case/canary_run_*.md`；`*_art_rel_*.json` | **目标**：1 次 internal 5–10% canary + ART-REL-DEC/EXEC。**禁区**：Phase 3+、远端 prod 自动 rollout、改 adapter。**软依赖**：W3-C-CI-GATE-WIRE nightly PASS。**窄上下文** |
   154|   154|| W3-A-REL-ARTIFACT | ART-REL 风格 release／观测记录 | W3 | REL | worker | TODO | W3-A-CANARY-PILOT | `20_pilot/W3-A_case/07_*.json`、`08_*.json`、`10_art_rel_obs.json`（可选） | 对齐 G8-5 **ART-REL-DEC**／**ART-REL-EXEC**；schema → `30_rollout/artifact_schema_w3a.md`。**窄上下文** |
   155|   155|
   156|   156|**W3-A 依赖链**：`W3-A-ORCH` → `W3-A-SHADOW-PILOT` → `W3-A-CANARY-PILOT`；`W3-A-REMOTE-ENV` → `W3-A-CANARY-PILOT` → `W3-A-REL-ARTIFACT`
   157|   157|
   158|   158|---
   159|   159|
   160|   160|## Wave 3 — W3-B 知识层 / Repo Indexing
   161|   161|
   162|   162|| ID | Title | Wave | Module | Role | Status | Depends on | Output File | Notes |
   163|   163||----|-------|------|--------|------|--------|------------|-------------|-------|
   164|   164|| W3-B-ORCH | 主线 B 编排骨架（index → AI-READY 前置） | W3 | KB | orchestrator | DONE | W3-0-ORCH | `20_pilot/W3-B_kb_contract.md`；`20_pilot/W3-B/README.md` | **长上下文**；`missing`→block **IMP-AI-READY**；`stale`→degrade；**不改** G7/G8 正文／RAG prod 主路径／暗部 code |
   165|   165|| W3-B-KB-CONTRACT | index 字段契约（案卷 + ENG-CTX） | W3 | G8/ENG | worker | TODO | W3-B-ORCH, W2-2-IMP-FIELD | `20_pilot/W3-B/kb_index_contract.md`；`_TEMPLATE_case`；`W3-B_case/` | 施工 **`kb_index_*`** 进模板 §2/§3；**禁止**本票改 G7/G8；`kb_index_status`：ready／stale／missing |
   166|   166|| W3-B-INDEX-PIPELINE | repo index 可查状态（批处理／离线） | W3 | ENG | worker | TODO | W3-B-KB-CONTRACT | `20_pilot/W3-B/index_pipeline_notes.md`；`index_status_*.json` 形状 | **文档 only**；对接 `repo_index_v1`／`repo_index_v1_job`；**非**全库实时；**不写** job 代码；宜先于 W3-A shadow |
   167|   167|| W3-B-GRAPHRAG-MIN | GraphRAG 最小探针（可选） | W3 | RAG | worker | TODO | W3-B-INDEX-PIPELINE | `20_pilot/W3-B/graphrag_min_probe.md` | 单 scope smoke；**不阻塞** §13.4 DoD；无 runbook 禁大型 job；产品化 → Wave 4 |
   168|   168|| W3-B-SELECTOR-HOOK | selector 只读 hook 规格 | W3 | ENG | worker | TODO | W3-B-INDEX-PIPELINE | `20_pilot/W3-B/selector_hook_spec.md` | **规则 only**；`missing`→block repo 工具；`stale`→degrade；**不**改 prod selector／ask 主路径 |
   169|   169|
   170|   170|**W3-B 依赖链**：`W3-B-ORCH` → `W3-B-KB-CONTRACT` → `W3-B-INDEX-PIPELINE` → `W3-B-SELECTOR-HOOK`（`W3-B-GRAPHRAG-MIN` 并行可选）
   171|   171|
   172|   172|---
   173|   173|
   174|   174|## Wave 3 — W3-C 治理自动化闭环
   175|   175|
   176|   176|| ID | Title | Wave | Module | Role | Status | Depends on | Output File | Notes |
   177|   177||----|-------|------|--------|------|--------|------------|-------------|-------|
   178|   178|| W3-C-ORCH | 主线 C 编排骨架（gate + CI/nightly） | W3 | G10/ENG | orchestrator | DONE | W3-0-ORCH | `20_pilot/W3-C_metrics_schema.md`；`20_pilot/W3-C/README.md` | 2026-05-27：接入矩阵 + JSONL 指标 v0.1 + 四子票摘要；**无** CI 代码／**无** deny runtime |
   179|   179|| W3-C-GOV-RISK-PILOT | GOV 案卷 + ART-GOV-RISK 实例 | W3 | GOV | worker | DONE | W3-C-ORCH, W2-1-QA-REL | `20_pilot/W3-C/gov_risk_pilot_notes.md`；`20_pilot/W2-3_case/art_gov_risk.json`；W3-C README / metrics_schema：pilot 字段挂点说明 | 仅作为 W3-C GOV-RISK pilot，不 retro W2-1，只用于后续 gate / metrics 设计与健康检查。 |
   180|   180|| W3-C-CI-GATE-WIRE | wf_gov_gate + cross_ref → CI/nightly | W3 | ENG | worker | TODO | W3-C-GOV-RISK-PILOT, W2-3-MINIMAL-GATE-IMPL | `20_pilot/W3-C/ci_gate_wire.md`；workflow 片段；`observability/gov_gate_metrics/*.jsonl` | **重点**：仅设计 PR/nightly 接线与 JSONL 写入规范（吞掉非 0 exit，指标落地；不实现 deny engine / 不落地 CI 配置）；§13.4 至少响 1 次 |
   181|   181|| W3-C-AGENT-SOP | agent／Cursor SOP 与 gate 对齐 | W3 | E1 | worker | TODO | W3-C-ORCH | `20_pilot/W3-C/agent_sop_gate.md` | **重点**：接战／IMP-RISK／QA T02／Release T07／封存 5 场景；**并行**非硬依赖；**禁区**：不改 G10、gate allow≠关票 |
   182|   182|| W3-C-IMP-STATE-LINT | imp_state lint（增强，非全 enforcement） | W3 | G7 | worker | TODO | W3-C-ORCH, W2-2-IMP-FIELD | `20_pilot/W3-C/imp_state_lint.md`；可选 `tools/wf_imp_state_lint.ps1` 骨架 | **重点**：设计 only + 未来 nightly hook；**并行**；**禁区**：全状态机 CI、自动改 imp_state → Wave 4 |
   183|   183|
   184|   184|**W3-C 依赖链**：`W3-C-ORCH` → `W3-C-GOV-RISK-PILOT` → `W3-C-CI-GATE-WIRE`；`W3-C-AGENT-SOP`／`W3-C-IMP-STATE-LINT` 可并行
   185|   185|
   186|   186|---
   187|   187|
   188|   188|## Checker — Wave 3
   189|   189|
   190|   190|| ID | Title | Wave | Module | Role | Status | Depends on | Output File | Notes |
   191|   191||----|-------|------|--------|------|--------|------------|-------------|-------|
   192|   192|| CHK-W3 | Wave 3 三条主线只读盘点 | W3 | — | checker | TODO | W3-A-REL-ARTIFACT, W3-B-SELECTOR-HOOK, W3-C-CI-GATE-WIRE | `99_latest_status.md` | 对照 `00` §13.4 DoD checklist；**不**改模块正文 |
   193|   193|
   194|   194|---
   195|   195|
   196|   196|## Wave 5 — 草案（Future · 未实施）
   197|   197|
   198|   198|> **状态**：本节票均为 **规划 / 候选**；Status=`FUTURE` 或 `IDEA`。**不**阻塞 Wave 4 收口。runtime 开工前须 Planning lane 续卡并过 governance-guard（若触制度边界）。
   199|   199|
   200|   200|| ID | Title | Wave | Module | Role | Status | Depends on | Output File | Notes |
   201|   201||----|-------|------|--------|------|--------|------------|-------------|-------|
   202|   202|| W5-A-K2-ROLLOUT-EXPANSION | K-2 rollout 扩面：prod / CI / multi-cohort / multi-repo | W5 | K2/REL | orchestrator | **IDEA** | W4-A-K2-ROLLOUT-INTEGRATION（DONE minimal v1）, W4-B, W4-C, CHK-W4（建议） | `40_ticket_memory/W5-A-K2-ROLLOUT-EXPANSION.memory.md` | **2026-05-29：planning 切片 DONE**（仅 Ticket Memory + `00`§15.7 挂点）。承接 W4-A 试点流；目标 prod CI、多 cohort、多 repo。**未**改 runtime/CI/tools。**≠** W4-A DONE 口径。 |
   203|   203|
   204|   204|---
   205|   205|
   206|   206|## Future — Wave 5+ 占位
   207|   207|
   208|   208|| 方向 | 说明 |
   209|   209||------|------|
   210|   210|| ~~Enforcement CI 设计~~ | **Wave 3** → **W3-C-CI-GATE-WIRE**；**第一版真 CI** → **W4-C-CI-INTEGRATION** |
   211|   211|| **95% 自动化** | 全链无人值守 → **Wave 5+** |
   212|   212|| **deny engine runtime** | G10-2 T3 → **Wave 5+** |
   213|   213|| **全 IMP 机读 enforcement** | 全状态 CI + intake 边 → **Wave 5+** |
   214|   214|| **K-2 Phase 3–4／远端 prod 自动 rollout** | 根 plan §4.8 后续 Phase → **Wave 5+** |
   215|   215|| **知识层全库产品化** | 实时增量、多 tenant KB、替换 RAG 主路径 → **Wave 5+** |
   216|   216|| **完整 release gate** | G8-5 out of scope 延续 → **Wave 5+** |
   217|   217|| **fail-on-deny 全 PR 默认** | 分阶段治理议题；**非** W4-C 默认交付 |
   218|   218|
   219|   219|---
   220|   220|
   221|   221|## Wave 4 — Implementation（W3 设计接入主工作流与 CI）
   222|   222|
   223|   223|> **总目标**（`00_master_plan.md` §15）：将 W3-A／W3-B／W3-C 在 Wave 3 已定稿的 contract／runbook／gate／metrics **正式接入**主工作流与 CI；**接上去、跑起来、可观测、可回滚** — **非**最终平台完成度。  
   224|   224|> **Status 随子票实装更新**；W4-A/B/C/X 四條主票已 **DONE（minimal v1）**；CHK-W4 判定 `OK_WITH_KNOWN_GAPS`。
   225|   225|
   226|   226|| ID | Title | Wave | Module | Role | Status | Depends on | Output File | Notes |
   227|   227||----|-------|------|--------|------|--------|------------|-------------|-------|
   228|   228|| W4-A-K2-ROLLOUT-INTEGRATION | K-2×ask shadow／canary → 可重复 rollout integration | W4 | K2/REL | orchestrator | DONE | W3-A-ORCH, W3-A-SHADOW-PILOT, W3-A-CANARY-PILOT, W3-A-REL-ARTIFACT | `20_pilot/W3-A/W4-A_rollout_runbook.md`；`20_pilot/W3-A/rollout_pipeline_config.json`；`20_pilot/W3-A_case/W4-A_gate_checklist.md`；`20_pilot/W3-A_case/W4-A_release_stream.json`；`tools/wf_k2_rollout_run.ps1`；`20_pilot/W3-A_case/run_records/**` | 2026-05-29：**minimal v1 DONE**。主 case/scope=`20_pilot/W3-A_case/`；固定流=`W4-A-PILOT-RELEASE-STREAM-v0.1`。入口=`wf_k2_rollout_run.ps1`（`-Phase full\|shadow\|canary\|rollback\|override`）。可重跑证据=`run_records/**`（例 `2026-05-29_111042`：`VERDICT=OK step=shadow` + `step=canary`）。含 K2 shadow + internal canary（5% cohort）+ 最小 rollback/override。**≠** 全量 prod rollout。**留白 Wave 5+**：Phase 3–4、远端 prod 自动 rollout、多 cohort 策略、CI 集成、多 repo 扩面、完整 release gate。 |
   229|   229|| W4-B-INDEX-INTEGRATION | KB／index pipeline → ORCH／主工作流（主 case／主 repo） | W4 | KB/ENG | orchestrator | DONE | W3-B-ORCH | `20_pilot/W3-B/W4-B_orch_integration.md`；`tools/wf_kb_index_sync.ps1`；`tools/wf_kb_index_gate.ps1`；`20_pilot/W3-B/index_status_W2-1*.json`；`20_pilot/W2-1_case/W2-1_case.md`（回填段） | 2026-05-29：最小实装 v1：主 case=**W2-1_case**，主 scope=subtree `core`。`wf_kb_index_sync` 真实回填案卷 `kb_index_*`；`wf_kb_index_gate` 在 `IMP-AI-READY` 前真实读取并输出 allow/deny（missing/blocker 硬阻断；stale 需显式 ack+flag）。**未扩面**到全 repo/case、**未**做实时增量/多 tenant/GraphRAG 产品化（留 Wave 5+）。 |
   230|   230|| W4-C-CI-INTEGRATION | wf_gov_gate + cross_ref → 真 CI（PR／nightly／manual） | W4 | ENG/G10 | orchestrator | DONE | W3-C-ORCH, W3-C-CI-GATE-WIRE, W2-3-MINIMAL-GATE-IMPL | `.github/workflows/gov-gate-metrics.yml`；`workflow_v2/observability/gov_gate_metrics/*.jsonl`；`workflow_v2/tools/wf_emit_gov_gate_metrics.ps1`；`20_pilot/W3-C/ci_gate_wire.md`；`20_pilot/W3-C_metrics_schema.md` | 2026-05-29：已落地真实 workflow（PR cross-ref + nightly 固定响铃 + workflow_dispatch manual/agent），吞非 0 exit 但写 JSONL 并上传 artifact `gov-gate-metrics`。**未**启用 deny runtime／fail-on-deny 全 PR hard fail（留 Wave 5+）。 |
   231|   231|| W4-X-CONTROL-PLANE-MVP | 控制面 MVP：总调度 + 多 lane 分流 + 独立 reviewer | W4 | E1 | orchestrator | DONE | E1-5 | `30_control_plane/W4-X_control_plane_mvp.md`；`40_ticket_memory/_TEMPLATE_ticket_memory.md` | **MVP DONE**：已交付角色定義（§1.1–§1.5）、四類 lane 模型（§2）、Reviewer 最小檢查清單（§1.4.1）、Out of Scope（§0）。Ticket Memory 模板欄位齊全（`lane`/`priority`/`mode`/`read_set`/`write_set`/`frozen_constraints`）。**已知缺口**：未實現自動多 chat 平台、自動並行調度、自動 merge 決策（§0 明確留 Wave 5+）。CHK-W4 判定 `OK_WITH_KNOWN_GAPS`。 |
   232|   232|
   233|   233|**W4 依赖链（建议）**：三条主票可并行开工；软顺序：**W4-B** index 宜不晚于 **W4-A** canary 扩面；**W4-C** nightly 指标宜在 **W4-A** canary 前留痕（与 W3 相同 R10）。
   234|   234|
   235|   235|---
   236|   236|
   237|   237|## 命名与路径对齐
   238|   238|
   239|   239|| 模块目录 | 队列前缀 |
   240|   240||----------|----------|
   241|   241|| `workflow_v2/10_governance/G6_scope_control/` | G6-* |
   242|   242|| `workflow_v2/10_governance/G7_state_machine/` | G7-* |
   243|   243|| `workflow_v2/10_governance/G8_artifact_contract/` | G8-* |
   244|   244|| `workflow_v2/10_governance/G10_governance_rulebook/` | G10-* |
   245|   245|