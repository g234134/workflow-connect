# 99 Latest Status — Workflow v2

> **更新者**：总控 orchestrator（CHK-W4 doc-sync）。
> **最后更新**：2026-05-30（**CHK-W4 收口**：W4-X 控制面 MVP DONE → 四線全部 DONE；Wave 4 整體標記 DONE-WITH-KNOWN-GAPS）

---

## 1. 当前 Wave

| Wave | 状态 | 说明 |
|------|------|------|
| **Wave 0（E1）** | **DONE** | E1-1 / E1-2 / E1-4 / E1-5 |
| **Wave 1（G6/G7/G8/G10）** | **DONE-WITH-NOTES** | 12 张施工票 `DONE`；CHK-W1 PASS-WITH-NOTES |
| **Wave 2 — W2-1** | **DONE** | 试点 `IMP-OBSERVING`；G8-RECON-IMP 实质经 W2-1-ENG 收口 |
| **Wave 2 — W2-2** | **SPEC-DONE + 部分子票** | 总控 + `W2-2-IMP-FIELD` **DONE**；HELPER／QA-CHECKLIST **TODO** |
| **Wave 2 — W2-3** | **SPEC-DONE + 原型** | 总控 + GOV 契约 + gate 设计 + `wf_gov_gate.ps1` 原型 **DONE**；GOV pilot 案卷 **TODO** |
| **Wave 3** | **DESIGN-CLOSED** | 三条主线 **W3-A／W3-B／W3-C** contract／runbook／gate／metrics **已定稿并出口封口**（§13.1–§13.3 语句冻结）；子票施工与试点记录仍可按 `90` 推进，**不**含真 CI／ORCH 实装 |
| **Wave 4** | **DONE-WITH-KNOWN-GAPS** | 四條主線 minimal v1 全部 DONE：**W4-A** 固定流 shadow+canary+rollback/override、**W4-B** index 回填+AI-READY gate、**W4-C** 真 CI+JSONL+artifact、**W4-X** 控制面 MVP+Ticket Memory 模板。已知缺口見 CHK-W4 Memory §W4-A/B/C/X Check Record。**未**全量 prod rollout／多 cohort／Wave 5 級治理收斂。 |

**口径**：Wave 2 交付**可复用规格、案卷模板、gate/helper 原型**；Wave 3 交付**可派工的设计层**（含 W3-C `ci_gate_wire.md` 三场景接线）；Wave 4 将上述设计**接入主工作流与 CI**（可观测、可回滚、可持续运转的第一版实装），**非** production 全自动 rollout 或 Wave 5 级治理收敛。

### Wave 4 当前状态（CHK-W4 收口 · 2026-05-30）

Wave 4 四條主線 minimal v1 全部 DONE：

- **W4-X-CONTROL-PLANE-MVP（DONE）**：控制面 MVP 文档 `30_control_plane/W4-X_control_plane_mvp.md`（角色定义、四类 lane 模型、Reviewer §1.4.1 最小检查清单、Out of Scope）与 Ticket Memory 模板 `40_ticket_memory/_TEMPLATE_ticket_memory.md` 已交付。**未**实现自动多 chat 平台／自动并行调度／自动 merge 决策（留 Wave 5+）。
- **W4-C-CI-INTEGRATION（DONE）**：新增 `.github/workflows/gov-gate-metrics.yml`，并引入 `workflow_v2/tools/wf_emit_gov_gate_metrics.ps1` 作为统一 stdout→JSONL emitter。PR 仅 cross-ref（warning 语义），nightly 固定响铃 Gate A+Gate B，manual/agent 通过 `workflow_dispatch` 复用同一解析与 JSONL 写入；artifact 名 `gov-gate-metrics`。
- **W4-B-INDEX-INTEGRATION（DONE · minimal v1）**：在主 case `W2-1_case` 追加 `kb_index_current`（P0 权威字段段落），并提供 `index_status_*.json` 侧车；`workflow_v2/tools/wf_kb_index_sync.ps1` 真实回填 `kb_index_*`；`workflow_v2/tools/wf_kb_index_gate.ps1` 在 `IMP-AI-READY` 前真实读取并输出 allow/deny（`missing`/`blocker` 硬阻断，`stale` 需显式 ack+flag）。**未扩面**到全 repo/case、**未**做实时增量/多 tenant/GraphRAG 产品化（留 Wave 5+）。
- **W4-A-K2-ROLLOUT-INTEGRATION（DONE · minimal v1）**：固定试点流 **`W4-A-PILOT-RELEASE-STREAM-v0.1`** 已在主 case `20_pilot/W3-A_case/` 可重复跑通 **K2 shadow → internal canary（5% cohort 模拟）**；入口 `workflow_v2/tools/wf_k2_rollout_run.ps1`（`-Phase full` 一次 shadow+canary）；配置 `20_pilot/W3-A/rollout_pipeline_config.json`；Gate `20_pilot/W3-A_case/W4-A_gate_checklist.md`；可重跑证据 `run_records/**`（例 `2026-05-29_111042`：`rollout_trace.jsonl` 含 `step=shadow`/`internal_canary`）。含最小 **rollback**（cohort→0）与 **override**（allowlist 角色 + reason）。**尚未**扩展到 prod 主流、多管道、多 cohort 策略或 CI 接线（留 Wave 5+；候选 `W5-A-K2-ROLLOUT-EXPANSION`）。
- **仍遵守边界**：未启用 deny engine runtime、未将 deny 默认升级为所有 PR hard fail、未触碰暗部脚本、未 retro 修改 W2-1 历史记录、**未**宣称 W4-A 完成全量 prod rollout 或 K-2 Phase 3+ 扩面。

**CHK-W4 已知缺口摘要**：
- W4-A：gate checklist 键名与 trace 不一致、ART-REL exec rollback_path 字段冲突、canary cohort 0/5 样本、override_record.json 无示例 run
- W4-B：index_status 为样本数据（file_count=0）、ORCH 尚未真正接入 CI production 流程
- W4-C：仅 local.jsonl 含 metrics（未等待 nightly prod 自动运行）、fail-on-deny 未启用（留 Wave 5+）
- W4-X：自动多 chat／自动调度／自动 merge 未实现（§0 明确留 Wave 5+）

- **W4-A**：
  GAP-1 / GAP-2 已由 W4-A-FIX-01 / W4-A-FIX-02 收斂為「命名與語義對齊 · 能力仍為 v0.1 minimal」，實際 rollback / cohort / override 等能力待 W4-A-FIX-03/04 與 Wave 5 結構票補強。

### Wave 5 展望（草案 · 未实施）

**W5-A-K2-ROLLOUT-EXPANSION** 已落盘 Ticket Memory（`40_ticket_memory/W5-A-K2-ROLLOUT-EXPANSION.memory.md`），规划在 W4-A 固定试点流基础上把 K-2 rollout 扩展到 **prod CI、多 cohort 阶梯、多 repo/服务**；当前仅为 **planning**，**未**开工 runtime/CI。与 W4-A（minimal v1 · shadow+5% internal canary 模拟）边界见 `00_master_plan.md` §15.7。

- **W5-A ENF**：
  Phase 2 shadow-only 已穩定（env / wiring / analyzer / operations guide 完成），W5-A-RUNTIME-03-BLOCKING-CRITERIA-01 已定義第一條 blocking canary 的窄範圍與 O/C/F/G readiness 條件，暫不實作，等待 ≥14 日 shadow 數據後再決策。

---

## 2. Wave 2 已完成到哪里

| 线 | 已完成 | 仍开放 |
|----|--------|--------|
| **W2-1** | 最小闭环至 **`IMP-OBSERVING`**；案卷 `20_pilot/W2-1_case/` 全链 ART | `G8-RECON-IMP` 行 Notes 可回填 W2-1-ENG |
| **W2-2** | `imp_state` schema、G7 附录、`wf_check_cross_ref.ps1`、`_TEMPLATE_case` | HELPER-SCRIPTS、QA-CHECKLIST 子票 |
| **W2-3** | **ART-GOV-RISK** G8 轨、`W2-3_minimal_gate_design.md`、`wf_gov_gate.ps1` v0.1 | GOV-RISK-PILOT 案卷实例 |

---

## 3. Wave 3 已正式开盘 — 三条主线

| 主线 | 代号 | 最低完成（摘要） |
|------|------|------------------|
| **A** | **W3-A** Rollout / Canary | ORCH 骨架 **`30_rollout/`** + **`20_pilot/W3-A_case/`** 已建；shadow/canary **仍待** SHADOW／REMOTE-ENV／CANARY 子票 |
| **B** | **W3-B** 知识层 / Repo Indexing | repo index 为 **IMP-AI-READY** 前置；案卷 `kb_index_*`／ENG-CTX `repo_index_job_id` 可查 ready／stale／missing（**missing** block、**stale** degrade）；制度见 `20_pilot/W3-B_kb_contract.md`（**W3-B-ORCH** DONE） |
| **C** | **W3-C** 治理自动化闭环 | `wf_gov_gate` + `wf_check_cross_ref` 接入 CI 或 nightly，留指标 |
| **C · ORCH** | **W3-C-ORCH** **DONE** | 目标 = gate/helper **真正接线** + 指标开张；编排见 `20_pilot/W3-C_metrics_schema.md`（PR warning / nightly JSONL）；子票 TODO |

**W3-C 当前状态战报（Wave 3 收口口径）**

> **W3-C-CI-GATE-WIRE（设计完成）**：已在 `20_pilot/W3-C/ci_gate_wire.md` 里定义 PR / nightly / manual 三场景的接线设计：PR 只跑 `wf_check_cross_ref.ps1`，将非 0 exit 视为 warning 而不 fail；nightly 固定按「先 cross-ref，后两次 gate」顺序每天至少各跑一次 W2-3 的 `GATE-RISK-EXIT` 与 W2-1+W2-3 的 `GATE-REL-ENTRY`，吞掉非 0 exit 但将 `VERDICT=` / `CHECKS_FAILED=` 解析为 gov‑metrics‑0.1 JSONL（写入 `workflow_v2/observability/gov_gate_metrics/YYYY-MM-DD.jsonl`，artifact 名建议 `gov-gate-metrics`）；manual/agent 场景使用相同 stdout→JSONL 机制。本票只设计 schema/落点与示例片段，不修改任何 CI 配置或实现 deny engine runtime，run_queue 中 W3-C-CI-GATE-WIRE 仍标记为 TODO，留待 Wave 4 将该设计真正接入 CI 并视治理决策引入 fail‑on‑deny。

**总控索引**：`00_master_plan.md` §13 · `02_dependency_map.md` §8 · `90_run_queue.md` Wave 3 节 · `20_pilot/W3-C/README.md`。

---

## 4. 封板前待办（跨 Wave）

| ID | 项 | 负责 | 票 |
|----|-----|------|-----|
| E1-6 | `03` 示例路径与 `90` Output 对齐 | orchestrator | **E1-6** TODO |
| W2-2 子票 | HELPER／QA-CHECKLIST 工程化 | worker | **W2-2-*** TODO |
| W2-3 pilot | ART-GOV-RISK 案卷实例 | worker | **W2-3-GOV-RISK-PILOT** TODO（可与 W3-C 合并节奏） |

---

## 5. 风险与待检查项

| # | 项 | 严重度 | 状态 |
|---|-----|--------|------|
| R5 | `ART-GOV-RISK` 案卷实例 | 中 | **W3-C-GOV-RISK-PILOT**（延续 W2-3） |
| R7 | gate CI 真实响铃 | 中 | **W3-C-CI-GATE-WIRE** |
| R8 | 完整 release gate / deny runtime | 中 | **Wave 5+**（§15.5） |
| R9 | K-2 远端 prod／Phase 3+ | 中 | **Wave 5+**；W4-A minimal v1（固定试点流）已 DONE；扩面见 `W5-A-K2-ROLLOUT-EXPANSION` |
| R10 | index 与 shadow 顺序 | 低 | 软依赖：W3-B 宜先于或并行 W3-A shadow |

---

## 6. 阻塞

| ID | 阻塞 | 解除条件 |
|----|------|----------|
| — | 无硬阻塞 | — |

---

## 7. 下一步（总控建议）

1. **Wave 4 四條主線 minimal v1 均已 DONE**（W4-A/B/C/X）；CHK-W4 判定 `OK_WITH_KNOWN_GAPS`；Wave 4 整體標記 **DONE-WITH-KNOWN-GAPS**。
2. **W4-A/W4-B/W4-C/W4-X 已知缺口** 可開 FIX 子票（W4-A-FIX-01~04、W4-B-FIX-01 等），或由 Wave 5 疊代處理。
3. **Wave 5（W5-A-RUNTIME-01）門禁**：CHK-W4 判定為**非 BLOCKING** — W5-A-RUNTIME-01 可啟動（但須引用 CHK-W4 已知缺口並在 planning 中涵蓋）。
4. **W3 残余子票**（若未 DONE）：可与 W4 并行，但不得 retro 改写 §13.1–§13.3 出口语句。

**索引**：Wave 4 总纲 → `00_master_plan.md` §15 · 主票 → `90_run_queue.md` Wave 4 节 · CHK-W4 Memory → `40_ticket_memory/CHK-W4-WAVE4-CLOSURE.memory.md` · K-2 邻接 → 战车根 `00_master_plan.md` §4.8（只读）。
