# TICKET STATE · WC-T7 · Control Plane E2E Walkthrough + INT Gate Alignment

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave C · Control Plane · M3

---

## FRAME

- Goal: 将 M2 Control Plane 手工 E2E 链（eligibility → dispatch cards → comms → order intake）制度化为独立 runbook，并提供可选 runner 骨架与 INT gate 边界对齐草稿，使 M2/M3 验收与 Wave 7 INT Tier-A 职责分离、可交叉引用。
- Scope:
  - 新建 `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md`：从 `overview.md` §M2 E2E 抽离并整理（前置条件、每步预期输出、失败诊断）
  - runbook 开头声明：本链为 **Control Plane E2E**，用于 M2/M3 验收，**不等于** INT Tier-A
  - runbook 末尾「INT gate 对齐」草稿：3–5 条对照行 + 明确 Control Plane E2E pass ≠ INT pass
  - 更新 `docs/wave_c/overview.md`：M2 E2E 改简短概要 + runbook 链接；M3 T7 一句话 + 链接；registry WC-T7 → In Progress
  - 可选 runner 骨架：`scripts/run_wc_m2_e2e_walkthrough.py`（`--dry-run` / `--execute` · 仅 demo 票 + `artifacts/e2e/` 隔离目录）
  - 本票 `*_state.md` FRAME/STATE 正式落盘
- NonScope:
  - 不将 Control Plane E2E 升格为 PR required / prod blocking gate
  - 不实现 INT Tier-A runner 或修改 `_wave7_regression_gate.py` 模块列表
  - 不自动写 live `*_state.md` STATE（HITL 手工编辑仍由 runbook 描述；runner 仅编排可脚本化 CLI）
  - 不含 WC-T5 覆盖率契约正文（可 cross-ref path_id，待 T5 关票）
  - 不含 WC-T6 skill distillation
- AllowedPaths:
  - `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md`（新建）
  - `docs/wave_c/overview.md`（M2/M3/registry 更新）
  - `scripts/run_wc_m2_e2e_walkthrough.py`（新建 · 可选 skeleton）
  - `04_Workflows/tickets/WC-T7_state.md`（本檔）
- BlockedPaths:
  - `04_Workflows/ticket_eligibility.py` · `_dispatch_cards.py` · `dispatch_executor.py` · `order_ledger/**`（本票 doc + runner 编排；实现变更另票）
  - `.github/workflows/**` · branch protection
  - `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `HARNESS_CONSTITUTION.md`
  - 暗部 `core/**` · `.env` · venv 树
- Dependencies:
  - **WC-T1** — eligibility CLI（`docs/wave_c/WC_T1_eligibility.md`）
  - **WC-T2** — comms payload（`docs/wave_c/WC_T2_comms_minimal.md`）
  - **WC-T3** — dispatch cards（In Progress；E2E 可 `--force-eligibility` 一次性 override）
  - **WC-T4** — order intake v0.1（`docs/wave_c/WC_T4_order_ledger_design.md`）
  - **INT gate contract** — `docs/phase6-int-regression-gate-contract-v1.md` · `04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md`（对齐草稿 cross-ref，非 merge）
  - **WC-T5** — automation coverage path_id（可选；T5 关票后 Scribe 补映射）
- AcceptanceCriteria:
  1. runbook 含完整 M2 E2E 步骤、前置条件、每步「预期输出」与「失败时下一步诊断」各一句
  2. runbook 开头与 INT 对齐节均声明 Control Plane E2E ≠ INT Tier-A
  3. `overview.md` M2 § 不再展开长命令，仅概要 + runbook 链接
  4. `overview.md` M3 集成轨 T7 一句话指向 runbook；registry `WC-T7` 为 In Progress
  5. 若交付 runner：`--dry-run` 打印步骤命令且不写文件；`--execute` 仅允许 `WC-DEMO-*` 票与 `artifacts/e2e/` 下产物

---

## STATE

- overall_status: accepted_with_gaps
- overall_status_rationale: runbook + runner skeleton + overview 概要 + dry-run UT 验收通过；deferred——WC-T5 path_id 映射表写入 runbook、`--execute` 全自动 STATE 过渡（forbidden · HITL）——不阻塞 v0.1 关票。
- current_owner: orchestrator
- next_action: closed · WC-T7 v0.1 accepted_with_gaps；v2 补 T5 path_id 表 · execute 全自动 STATE 仍 forbidden
- last_updated: 2026-06-13 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files:
  - `04_Workflows/tickets/WC-T7_state.md` — FRAME/STATE 正式落盘
  - `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md` — M2 E2E runbook + INT gate 对齐草稿
  - `docs/wave_c/overview.md` — M2/M3 概要、registry WC-T7 → In Progress
  - `scripts/run_wc_m2_e2e_walkthrough.py` — 可选 runner 骨架（dry-run / execute）
  - `tests/fixtures/e2e_walkthrough/WC-DEMO-1_state.md` — demo 票 fixture（E2E / nightly smoke 专用）
  - `tests/test_run_wc_m2_e2e_walkthrough.py` — runner dry-run 最小 UT（demo 票 + artifacts-root 边界）
- artifacts: runbook v0.1 · runner dry-run 步骤清单
- verification:
  - `python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --dry-run`
  - `python -m unittest tests.test_run_wc_m2_e2e_walkthrough -v`
- behavior_notes: doc-first；STATE 编辑保持 HITL；runner 仅允许 WC-DEMO-* + artifacts/e2e/；v0.1 runner 现有最小 dry-run UT，覆盖 demo 票与 artifacts-root 边界
- deferred_items:
  - WC-T5 path_id 映射表写入 runbook（T5 已关票 · v2 补全）
  - runner `--execute` 全自动 STATE 过渡（forbidden · 保持 HITL）

---

## C_REPORT

- conclusion: accepted_with_gaps
- blocking_issues: none
- checks_summary:
  - AC-1：runbook 含完整 M2 E2E 步骤、前置条件、每步预期输出与失败诊断各一句
  - AC-2：runbook 开头与 INT 对齐节均声明 Control Plane E2E ≠ INT Tier-A
  - AC-3：`overview.md` M2 § 改简短概要 + runbook 链接（不再展开长命令）
  - AC-4：overview M3 T7 一句话 + registry 指向 runbook
  - AC-5：runner `--dry-run` 打印步骤不写文件；`--execute` 边界为 WC-DEMO-* + `artifacts/e2e/`（dry-run UT 已覆盖）
  - NonScope 遵守：无 PR required 升格 · 无 INT Tier-A runner 改动 · 无 live STATE 自动写入
  - **Deferred（不阻塞 v0.1）**：WC-T5 path_id 映射表写入 runbook；runner `--execute` 全自动 STATE 过渡（保持 HITL forbidden）
- risk_level: low
- suggestions: T5 关票后 Scribe 补 runbook path_id 附录；INT 对齐节升格时机另票；与 WC-SMOKE-M2-NIGHTLY 脚本交叉引用已就绪

---

## D_REPORT

- docs_updates:
  - `docs/wave_c/overview.md` — M2 E2E 改概要 + `WC_T7_e2e_walkthrough_runbook.md` 链接；WC-T7 registry **In Progress → accepted_with_gaps (v0.1)**
  - `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md` — runbook v0.1 已落盘；INT gate 对齐草稿与 T5 path_id 映射表留 v2 补全
- progress_entry: WC-T7 v0.1 关票：M2 Control Plane E2E runbook + `run_wc_m2_e2e_walkthrough.py` runner skeleton ready；STATE 编辑仍 HITL。
- followup_suggestions:
  - v2：runbook 附录补 WC-T5 `wc.m2.*` path_id 对照表
  - 不将 Control Plane E2E 升格为 PR required；INT Tier-A 职责保持分离
