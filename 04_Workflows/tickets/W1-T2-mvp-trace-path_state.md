# TICKET STATE · W1-T2-mvp-trace-path · MVP 主链最小标准 trace 路径定义

> handoff 摘要档；跨 chat 交棒以本档为准，不是完整工作日志。  
> Wave：Wave 1 — Governance & Observability  
> **与旧 W1-T2 区分**：`W1-T2_state.md` = Monitoring PG Ingest（done）；**本票** = tabular MVP 标准 trace spec。

---

## FRAME

- Goal: 为 MVP 主链（intake → gate → cleaning → bundle → E2E）定义最小标准 trace 参考路径（`demo_phase` + `sampleco`），含 L1 信号表、rerun 指令与最小回归。
- Scope:
  - 新增 `docs/mvp-standard-trace-path.md`
  - 本票 state 记录施工与验收
  - L1 trace（CLI JSON + artifacts）；L2 标 adjacent / 未接线 `[待确认]`
- NonScope:
  - 不改 `W1-T2_state.md`（PG ingest）
  - 不改宪法母本 / `ENGINEERING_CONTRACT` / `AGENTS` / `.cursor/rules/*`
  - 不预定义 Langfuse span / `workflow_name`
  - 不改 gate / cleaning / bundle 业务逻辑
  - 不实施 MVP → Langfuse 接線
- AllowedPaths:
  - `docs/mvp-standard-trace-path.md`
  - `04_Workflows/tickets/W1-T2-mvp-trace-path_state.md`
- BlockedPaths:
  - `04_Workflows/tickets/W1-T2_state.md`（只读引用）
  - `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `HARNESS_CONSTITUTION.md`
  - `.cursor/rules/*`
  - `core/*` · 暗部 `core/*`
- Dependencies:
  - W1-T1B done · `docs/governance-constitution-v1.md`
  - MVP Wave 2–4 脚本与 `cases/demo_phase` · `cases/sampleco/2026-0001` 已存在
- AcceptanceCriteria:
  - `docs/mvp-standard-trace-path.md` 含：目的、范围、案例表、状态节点、L1/L2 trace 表、rerun 指令、最小回归、注意事项
  - L2 仅标 adjacent / `[待确认]`，无 span 预定义
  - 未修改旧 `W1-T2_state.md`
  - 至少一条案例完整「步骤 → trace 节点」示意（附录 A）
- VerificationCommands:
  - 文档存在性：`docs/mvp-standard-trace-path.md`
  - 可选 live 回归（非本票阻塞）：`python scripts/run_case_e2e_validation.py --case-dir cases/demo_phase --json` → exit 0

---

## STATE

- overall_status: done
- design_phase: accepted
- implementation_status: done
- current_owner: implementer
- next_action: Reviewer 对照 AC 验收；或 Scribe 写 Progress 末尾（可选）
- last_updated: 2026-06-10 · implementer
- status_by_role:
  - orchestrator: n/a
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

- changed_files:
  - `docs/mvp-standard-trace-path.md`（新建 · MVP 标准 trace spec）
  - `04_Workflows/tickets/W1-T2-mvp-trace-path_state.md`（新建 · 本票 state）
- artifacts:
  - `docs/mvp-standard-trace-path.md`
- verification:
  - 文档结构自检：§1–§9 + 附录 A 齐全
  - 未改 `W1-T2_state.md` / 宪法 / AGENTS / `.cursor/rules`
  - `python scripts/run_case_e2e_validation.py --case-dir cases/demo_phase --json` → exit **0**；`ok=true`；`eligibility=review_needed`；`output_guard.status=ok`
  - `python scripts/run_case_e2e_validation.py --case-dir cases/sampleco/2026-0001 --json` → exit **0**；`ok=true`；`eligibility=accepted`；`output_guard.status=warning`
- behavior_notes:
  - L1 = CLI JSON + case artifacts（MVP 今日权威可观测）
  - L2 = Langfuse / Monitoring Graph / PG 标 adjacent / 未接线 `[待确认]`，不预定义 span
  - 票号与旧 W1-T2（PG ingest）在 spec §8 与 FRAME 中显式区分
- deferred_items:
  - MVP 主链 → Langfuse / gov-trace-v2 接線（另开 trace 接線票）
  - Reviewer 签核 · Scribe Progress 追加（可选）

---

## C_REPORT

- conclusion: **accepted_with_gaps**
- blocking_issues: 無
- checks_summary:
  - **AC-1／AC-3／AC-4／AC-6**：全數通過 — 單檔可讀（§3–§5 + 附錄 A）、最小回歸（§6–§7）、舊 W1-T2 PG ingest 與本票界線清楚、L2 標 adjacent／未接線 `[待確認]`、diff 僅 spec + 本票 state。
  - **AC-2／AC-5**：文檔精度 gap（非阻塞）— §5.2 Cleaning 行將 `qa_status` 列於 stdout（實際在 `reports/report.json`）；Step 0 `build_cases_index.py` 未標 `--json`；B_REPORT 未單列 `sources_consulted`（spec §9 已交叉引用 DoD／walkthrough／cases／scripts）。
  - **spec 定位**：`docs/mvp-standard-trace-path.md` 為 tabular MVP 主鏈 **L1 業務 trace 對照 spec**（`demo_phase` + `sampleco/2026-0001`）；**非** Langfuse span 規範、**非** prod SLA。L2（Langfuse／Monitoring Graph／gov-trace-v2／PG `task_runs`）**adjacent／未接線 `[待確認]`**，MVP CLI 今日權威可觀測僅 CLI JSON + case artifacts。
- risk_level: low
- suggestions:
  - G1：§5.2 Cleaning 行 — `summary.qa_status` 改列 `artifact.report` 或註明「見 report.json，非 stdout」
  - G2：§5.2 Step 0 — 命令補 `--json` 或改預期為人類可讀摘要
  - G3（可選）：§5.3 為 sampleco 補與 §5.2 對稱完整 L1 表
  - G4：B_REPORT 增 `sources_consulted` 列表
  - MVP → Langfuse／gov-trace-v2 接線另開 trace 票（FRAME deferred）

---

## D_REPORT

- docs_updates:
  - **交付**：`docs/mvp-standard-trace-path.md` — `demo_phase` + `sampleco/2026-0001` 標準 trace 路徑；L1 = CLI JSON + `cases/<case>/reports/*` 落盤；L2 尚未接線（§5.4 標 `[待確認]`）。
  - **何時必讀**：改 `scripts/check_case_eligibility.py`、`notebooks/csv_cleaning/*`、`scripts/build_case_delivery_bundle.py`、`scripts/run_case_e2e_validation.py`；改標準樣本夾具；開 trace 接線票；MVP onboarding／demo 走查前對照。
  - **Sources Index 提醒**：權威 E2E → `docs/MVP_CASE_E2E_DoD_v0.1.md`；敘事走查 → `docs/MVP_DEMO_WALKTHROUGH_v0.1.md`；case 約定 → `cases/README.md`；L2 對照 → `docs/observability.md`；入口腳本 → `scripts/run_case_e2e_validation.py` 等（§2.3 表）。
  - **本輪索引**：`04_Workflows/WORKFLOW_INDEX.md` §1.5 已增 MVP trace／回歸兩條指針。
- progress_entry: |
    [W1-T2-mvp-trace-path] done · accepted_with_gaps · 新增 `docs/mvp-standard-trace-path.md`（demo_phase + sampleco L1 trace／最小回歸）；L2 adjacent `[待確認]`；與 `W1-T2_state.md` PG ingest 票區分。Reviewer gaps：§5.2 qa_status／index `--json` 精度。
- followup_suggestions:
  - 可選文檔小修（G1–G2）不阻塞關票
  - MVP → Langfuse 接線另開 trace 票
  - 與 W1-T3B 主鏈回歸互補：`docs/mvp-mainline-regression.md` 一鍵跑 §7.2 序列
