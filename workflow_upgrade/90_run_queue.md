# 90 Run Queue — Workflow Upgrade (Sprint 0)

> **權威**：本輪 `workflow_upgrade/` 任務狀態以本檔為準。  
> **總覽**：`workflow_upgrade/00_master_plan.md`（F 線，不寫 A 規格正文）。  
> **狀態字彙**：`TODO` | `DOING` | `BLOCKED` | `DONE`  
> **更新規則**：完工票僅改 **Status** 與 **Notes**；不刪歷史行。

---

## 欄位說明

| 欄位 | 說明 |
|------|------|
| **ID** | 任務代號 |
| **Title** | 一句話標題 |
| **Line** | `F` / `A` / `B` / `C` / `D` / `E` |
| **Status** | `TODO` / `DOING` / `BLOCKED` / `DONE` |
| **Depends on** | 前置任務 ID（無則 `-`） |
| **Output File** | 預期產物路徑（相對戰車根） |
| **Notes** | 派工備註、阻塞、對賬 |

---

## F 線 — 總控

| ID | Title | Line | Status | Depends on | Output File | Notes |
|----|-------|------|--------|------------|-------------|-------|
| F+A-0 | 建立 Sprint 0 最小文件骨架 | F | DONE | - | `workflow_upgrade/` 目錄樹 | 含 `01_context-entry/` 空目錄；不寫 A1–A5 正文 |
| F-1 | 建立 00_master_plan.md | F | DONE | - | `workflow_upgrade/00_master_plan.md` | 高層目標與主線 DoD；無 implementation |
| F-2 | 建立 90_run_queue.md 初版 | F | DONE | F-1 | `workflow_upgrade/90_run_queue.md` | 本檔；含 A 線初始化與 B–E placeholder |

---

## A 線 — Context Entry（規格層）

| ID | Title | Line | Status | Depends on | Output File | Notes |
|----|-------|------|--------|------------|-------------|-------|
| A-0 | 建立 Context Entry overview | A | DONE | F-2 | `workflow_upgrade/01_context-entry/A0_context_entry_overview.md` | overview v0.1：總覽／派工導讀；對齊 contract／code |
| A-1 | 設計 root context spec | A | DONE | A-0 | `workflow_upgrade/01_context-entry/A1_root_context_spec.md` | root spec v0.1：欄位類型／載入時機／subtree 邊界 |
| A-2 | 設計 subtree context spec | A | DONE | A-1 | `workflow_upgrade/01_context-entry/A2_subtree_context_spec.md` | subtree spec v0.1：掛載／繼承／欄位；支撐 A-4／A-5 |
| A-3 | 設計 ignore / deny rules | A | DONE | A-0 | `workflow_upgrade/01_context-entry/30_ignore_deny_rules.md` | deny 規格 v0.1：ignore／deny 層級／類型／順序 |
| A-4 | 設計 navigation map template | A | DONE | A-0 | `workflow_upgrade/01_context-entry/40_navigation_map_template.md` | nav map 模板 v0.1：節點欄位／路徑／隊列對帳 |
| A-5 | 建立 context entry runbook | A | DONE | A-1, A-2, A-3, A-4 | `workflow_upgrade/01_context-entry/50_context_entry_runbook.md` | runbook v0.1：場景／四層／deny-ignore／nav／驗收 |
| A-6 | 回頭更新 90_run_queue.md 狀態 | A | DONE | A-5 | `workflow_upgrade/90_run_queue.md` | Sprint 0 對帳：A-0～A-5 狀態與命名統一 |

### A 線產物命名對齊（Sprint 0）

| 票號 | 正式 Output File | 說明 |
|------|------------------|------|
| A-0～A-2 | `A0_*` / `A1_*` / `A2_*` | 總覽與兩份 spec，檔名帶票序前綴 |
| A-3～A-5 | `30_*` / `40_*` / `50_*` | 規則／nav 模板／runbook，以序號前綴排序 |

**舊名／草稿引用 → 正式檔**（隊列與產物目錄以右欄為準）：

| 舊名或誤引 | 正式檔 |
|------------|--------|
| `A3_ignore_and_deny_rules.md`（見 A-4 §12 引用索引） | `30_ignore_deny_rules.md` |
| 票內簡稱 `A1_*`／`A2_*` | 同列 Output File 路徑 |

本輪 **未** 發現 `10_*` 前綴產物；`01_context-entry/` 共 6 檔，與上表 Output File 一致。

**Sprint 0 · A 線出口**：A-0～A-6 均 `DONE`；B–E 仍 placeholder（見下節）。

---

## R 線 — H 線實作（Context Entry · Sprint 1–3）

| ID | Title | Line | Status | Depends on | Output File | Notes |
|----|-------|------|--------|------------|-------------|-------|
| A'-1 | 頂層 `subtree_context` v0.1 mock | R | DONE | A-5 | `core/context_entry.py` | Sprint 1；`list[dict]` + `task_input` 覆寫 |
| A'-2 | 最小 deny 雙閘（pre / post） | R | DONE | A'-1 | `core/context_entry.py` | Sprint 1；合同 §2.4 |
| R-1 | navigation_map 自動生成 v0.1 | R | DONE | A'-1 | `core/context_entry.py` | Sprint 2；`metadata.navigation_map` |
| R-2 | P0.5 subtree trimming heuristic | R | DONE | A'-1 | `core/context_entry.py` | Sprint 2；`metadata.trim` |
| R-3a | ContentRuleTable / ActionRuleTable 抽離 | R | DONE | A'-2 | `context/deny_rules.py` | deny engine v1 打底；規則表自 core 抽離 |
| R-3b | GateRunner v1 pipeline | R | DONE | R-3a | `context/deny_rules.py`, `core/context_entry.py` | `pre_injection` / `post_assembly` 可配置；`subtree` stub 保留未啟用 |
| R-3c | 高風險 content 規則 + observability | R | DONE | R-3b | `context/deny_rules.py`, `core/context_entry.py` | `RULE_TABLE_VERSION=deny-rules-v0.2-r3c`；`metadata.deny.observability`；coverage **content 6/8**（A-3 §5.1）、**action 2/8**（§5.2）；`tests.test_context_entry` **26/26 OK** |

**Sprint 3 · R-3 出口（deny engine v1）**：

- 規則表：`context/deny_rules.py`（`CONTENT_RULE_TABLE` / `ACTION_RULE_TABLE`）
- 執行：`GateRunner` → `build_rooted_context` 雙閘
- 觀測：`metadata.deny.observability`（`GOV_CONTEXT_DENY_OBSERVABILITY` 可關）
- **未啟用**：`subtree` gate 聯集、Z-* 運行時授權器、`full_cli_trace` 等 → 後續票

---

## O 線 — Monitoring subagent（H 線 · Sprint 4）

| ID | Title | Line | Status | Depends on | Output File | Notes |
|----|-------|------|--------|------------|-------------|-------|
| C-1 | Context-driven subagent routing v0.1 | O | DONE | A-5, H v0.1 | `subagents/context_routing.py` | `signal_only`；`ROUTE-MON-1` → `monitoring_subagent`；不改 selector |
| O-2a | Monitoring executor（read-only adapter + stub） | O | DONE | C-1 | `subagents/monitoring_executor.py` | `monitoring-service-adapter`／`v0.1-stub` fallback；不寫 PG |
| O-2b | Ask ibridge 預圖 enrichment | O | DONE | O-2a | `gov_core_system/core/ask_pipeline_ibridge_v0.py` | `enrich_init_with_context_entry`；公開 `ibridge_v0.monitoring_executor` |
| O-2c | HQ／runbook／AGENTS 制度收口 | O | DONE | O-2a, O-2b | `AGENTS.md`, `04_Workflows/TASK_ROUTING.md`, `workflow_upgrade/01_context-entry/50_context_entry_runbook.md` | **無** `hq.monitoring` 路由表項；見根 `00_master_plan.md` §4.11 |

**Sprint 4 · O-2 出口**：ask 路徑上 monitoring 為 **signal_only 側車**；維運／API 驗收仍走 `dark.infra` 或 Wave 1 runbook，**不**與 subagent executor 混用。

---

## O 線 — Monitoring graph（H 線 · Sprint 5）

| ID | Title | Line | Status | Depends on | Output File | Notes |
|----|-------|------|--------|------------|-------------|-------|
| M-1 | Monitoring graph skeleton | O | DONE | O-2a | `core/monitoring_graph.py` | v0.1 in-process stub；只读 `service_summary` |
| M-2 | Executor glue + env flag | O | DONE | M-1 | `subagents/monitoring_executor.py` | `GOV_MONITORING_GRAPH_ENABLED`；adapter 成功后才跑 graph |
| M-3 | ibridge public summary | O | DONE | M-2 | `gov_core_system/core/ask_pipeline_ibridge_v0.py` | `ibridge_v0.monitoring_graph`；剥離 `_monitoring_graph_result` |
| C-GOV | monitoring graph → selector／SLO 治理條款 | C | DONE | M-3, A-5 | `50_context_entry_runbook.md` §6.7–§6.8, `AGENTS.md`, `00_master_plan.md` §4.12 | **不改** selector；L0／L1／L2 三級 + L0 Observability 閘門；現僅 L0 |

**Sprint 5 · 出口**：graph 僅 **L0 observability**；參與 selector／gate 須滿足 §6.8.4–§6.8.5 且另開 `M-GOV-L*` 實作票。

### Observability 閘門 · 後續候選票（未開工）

| ID | Title | Line | Status | Depends on | Notes |
|----|-------|------|--------|------------|-------|
| OBS-GATE-1 | 統一 HTTP observability 閘門 alias（可選） | C | TODO | C-GOV | 程式票；`GOV_CORE_API_EXPOSE_OBSERVABILITY` umbrella；保留既有雙閘門向後相容 |
| M-GOV-L1 | L1 shadow selector／advisory 實作 | O | TODO | C-GOV | 須 §6.8.4 門檻 + 尚書省批文 |
| M-GOV-L2 | L2 SLO gate／hard policy 實作 | O | TODO | M-GOV-L1 | 須 §6.8.5 門檻 + gating 批文 + rollback 演練 |

---

## HQ 線 — Cursor Subagents v0.1（治理驗收）

> **Line**：`HQ`（Cursor IDE 協作鏈，非 H 線 runtime `subagents/*`）。  
> **欄位對照**：下表 **ID** = `ticket_id`；**Type** = 工單類型；**Status** = `DONE`／`STOP`；**Output File** = 產物或裁決落點。

| ID | Type | Status | Output File | Notes |
|----|------|--------|-------------|-------|
| TEST-SUB-001 | bugfix | DONE | `subagents/context_routing.py` | worker 單檔 regex；checker **`accepted_with_gaps`**；follow-up：KPI-only regression test 另票 |
| TEST-SUB-002 | doc_clarification | DONE | `workflow_upgrade/01_context-entry/50_context_entry_runbook.md` §6.7 | guard **`allow`**（鎖 §6.7）；checker **`accepted`**；戰報 inline 範例見 `04_Workflows/OPS_CYCLE.md` §5 |
| TEST-SUB-003 | governance_test | STOP | `—`（僅 guard 裁決；無施工產物） | **`stop_work`**；`allowed_worker=none`；未進 implementation-worker／checker |

**出口**：v0.1 三票驗收已封存；派工原則見 `AGENTS.md`「Cursor Subagents v0.1 驗收紀錄」。

---

## K 線 — K-2 Phase 1 rollout（對帳 · 權威 `_workflow_upgrade/90_run_queue.md`）

> **2026-06-05 裁決** `WAVE-CORE-P0-PHASE1-ROLLOUT-DECISION`（Option A）：Phase 1 **local-only gate**；remote prod 见 P1 工單，不纳入 Phase 1 出门。詳表與 yaml 以 `_workflow_upgrade/90_run_queue.md` 為準。

| ID | Title | Status | Notes |
|----|-------|--------|-------|
| K2-phase1-prod-shadow | Phase 1 prod shadow — **local-only gate** (T+0 + local 7d) | in_progress | Phase 1 出门 = 本地 workstation shadow parity；不含 remote |
| K2-phase1-remote-rollout | Phase 1 remote prod cluster shadow + parity (**P1**) | TODO | 非 Phase 1 gate；不阻塞 Phase 2 canary；非 canary 流量 |
| K2-phase1-remote-rollout-runbook | Remote rollout runbook blueprint (docs only) | DONE | `docs/k2_phase1_remote_rollout_runbook.md`；Blueprint only |

---

## B / C / D / E — Placeholder（Sprint 0 不展開細任務）

| ID | Title | Line | Status | Depends on | Output File | Notes |
|----|-------|------|--------|------------|-------------|-------|
| B-* | （預留）工作流編排／handoff 治理 | B | TODO | Sprint 0 出口 | `workflow_upgrade/02_*/`（未定） | Sprint 0 不建子目錄、不寫正文 |
| C-* | （預留）可觀測／eval 治理 | C | TODO | Sprint 0 出口 | `workflow_upgrade/03_*/`（未定） | 同上 |
| D-* | （預留）Skills／能力包治理 | D | TODO | Sprint 0 出口 | `workflow_upgrade/04_*/`（未定） | 同上 |
| E-* | （預留）外部連接／通道邊界 | E | TODO | Sprint 0 出口 | `workflow_upgrade/05_*/`（未定） | 同上 |

---

## A 線 — Knowledge Layer · Week 1（Phase 2 MVP · HQ-A 凍結 2026-05-25）

> **權威**：本節命名與邊界為 **HQ-A 凍結決議**；施工 chat **不得**自行改名或擴 scope。  
> **與 Sprint 0 A 線（Context Entry 規格）無關**——票號 `A-W1-*` 指 Knowledge Layer 實作週。

### 凍結常數（全週有效）

| 項 | 固定值 |
|----|--------|
| `job_type` | `repo_index_v1` |
| Qdrant collection | `repo_chunks` |
| Graph artifact | `artifacts/repo_index/<job_id>/graph.v0.json` |
| Graph schema version | `v0.1` |
| Node id | `file:<repo_rel>` · `sym:<file>#<qualname>` |
| Week 1 edge `type` | `contains` · `imports` **only** |
| 模組前綴 | `repo_index_*` · `code_graph_*` · `repo_chunks_*` |
| 回傳契約 | `{ok, message, job_id?, ...}` |

### Week 1 禁止（不開票）

LSP · 跨語言 symbol · graph→retrieve 擴展 · 接 ask 主線 selector · 改 `document_chunks` 既有 smoke · 改 GRAG-1（`graphrag_grag1`）現有語意。

### 施工順序

`A-W1-A` → 並行 `A-W1-B` + `A-W1-C` → `QA-A-W1`。

共用檔衝突：**新建檔優先**；必改共用檔時 **單檔單票、串行**（Rule 8）。

| ID | Title | Line | Status | Depends on | Output File | Notes |
|----|-------|------|--------|------------|-------------|-------|
| A-W1-A | repo_index job + schema（`repo_index_v1`） | A | BLOCKED | - | 暗部 `core/repo_index_job.py`；`Departments/05_Data_Vault/db/011_repo_index_schema.sql`；`repo_index_agent.py` | **IMPLEMENTED_WAITING_DB**（HQ 2026-05-25）：實作完成；待 PG 四步驗收（schema→run→manifest COUNT→Gov Core smoke） |
| A-W1-B | code graph v0.1（file + import） | A | TODO | A-W1-A | `artifacts/repo_index/<job_id>/graph.v0.json` | 模組 `code_graph_*`；靜態 Python ast；邊僅 contains/imports |
| A-W1-C | `repo_chunks` semantic retrieve smoke | A | TODO | A-W1-A | 暗部 `core/repo_chunks_*.py`（或 `repo_retrieve` 薄封裝） | 模組 `repo_chunks_*`；**不**改 ask selector／`skill_retrieve_for_ask` 預設 |
| QA-A-W1 | Week 1 三票最小驗收 | A | TODO | A-W1-A, A-W1-B, A-W1-C | Work Report + 可重跑命令輸出 | `hq.qa`；三票 `ok` + 證據語意入隊列 Notes |

---

## 派工提示（給後續 chat）

1. **Knowledge Layer Week 1**（`A-W1-*`）依上節凍結常數施工；**Sprint 0 Context Entry**（A-0～A-6）已 `DONE`，勿混票號。  
2. 其餘新規格派工改走 B–E placeholder 或實作票（見 `50_context_entry_runbook.md` §12）。  
3. 執行期合同以 `context/context_entry_contract.md` 為準；`workflow_upgrade/01_context-entry/` 為治理補充。  
4. 勿與 `_workflow_upgrade/`（底線）歷史隊列混路徑。  
5. 下游 ask 圖路由見 `skills/skills_contract.md` §10.5；**A-W1** 不修改該節路由表。

---

## 變更紀錄

| 日期 | 變更 |
|------|------|
| 2026-05-25 | 初版：F+A-0 建立骨架；F-1/F-2/F+A-0 → DONE；A-0～A-6 → TODO；B–E placeholder |
| 2026-05-25 | A-1 → DONE（`A1_root_context_spec.md`） |
| 2026-05-25 | A-2 → DONE（`A2_subtree_context_spec.md`） |
| 2026-05-25 | A-0 → DONE（`A0_context_entry_overview.md`） |
| 2026-05-25 | A-3 → DONE（`30_ignore_deny_rules.md`） |
| 2026-05-25 | A-4 → DONE（`40_navigation_map_template.md`） |
| 2026-05-25 | A-5 → DONE（`50_context_entry_runbook.md`） |
| 2026-05-25 | A-6 → DONE；Sprint 0 A 線收口；A-0～A-5 Notes／Output 對帳；命名對齊小節 |
| 2026-05-25 | R-3a / R-3b / R-3c → DONE；Sprint 3 deny engine v1 收口；治理文件對齊 |
| 2026-05-25 | Sprint 4 O 線：C-1／O-2a／O-2b／O-2c → DONE；隊列與根 `00_master_plan.md` §4.11 對帳 |
| 2026-05-25 | Sprint 5 O 線：M-1／M-2／M-3／C-GOV → DONE；§6.7–§6.8 L0／L1／L2 治理；根 plan §4.12 |
| 2026-05-25 | C 線後續：Observability 閘門統一模型 + 候選票 OBS-GATE-1／M-GOV-L1／M-GOV-L2 |
| 2026-05-25 | HQ 線：TEST-SUB-001／002／003 Cursor Subagents v0.1 驗收封存（001 DONE+gaps；002 DONE；003 STOP） |
| 2026-05-25 | A 線 Week 1：HQ-A 凍結 `repo_index_v1`／`repo_chunks`／`graph.v0.json` v0.1；隊列登錄 A-W1-A／B／C + QA-A-W1 |
| 2026-05-25 | A-W1-A → BLOCKED（**IMPLEMENTED_WAITING_DB**）：實作交付；待 PG 四步驗收後方可解阻 A-W1-B/C |
| 2026-06-05 | K 線對帳：`WAVE-CORE-P0-PHASE1-ROLLOUT-DECISION` Option A — Phase 1 **local-only gate**；新增 P1 `K2-phase1-remote-rollout`；見 `_workflow_upgrade/90_run_queue.md` 與根 `00_master_plan.md` §4.8 |
