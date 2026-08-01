# TICKET STATE · WC-T1-INTEGRATION · Ticket Eligibility 接入 Control Plane 首入口

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave C · Control Plane · M2（智能接单）  
> 父票：**WC-T1**（eligibility 工具层已完成；见 `docs/wave_c/WC_T1_eligibility.md` §8）

---

## FRAME

- Goal: 将 `ticket_eligibility.check_ticket_eligibility` 从独立 CLI 工具接入 **一个真实 Control Plane 入口**，使 Orchestrator 在生成 Implementer 指令卡前自动挡下 ineligible 票；首版 **不** 改 Cursor hook、**不** 写 STATE、**不** 开 chat。
- Scope:
  - 在 `04_Workflows/_dispatch_cards.py` → `generate_cards()` 循环内，写卡前调用 `check_ticket_eligibility(tid, repo_root, context={"requested_role": recommended_role})`
  - `scripts/run_dispatch_cards.py` 增加 `--eligibility-gate {off,warn,block}`（默认 `block`）与 `--force-eligibility`（Orchestrator override，summary 留痕）
  - run summary JSON（`dispatch_cards_run.latest.json`）增加 `eligibility_blocked[]`、`eligibility_gate` 字段
  - 单元测试：`tests/test_dispatch_cards.py` 增 ≥2 场景（ineligible skip + eligible 仍写卡；可选 force override）
  - 文档：`docs/control_plane_dispatch_executor.md` § Dispatch Cards 增 Eligibility gate 小节；`docs/wave_c/WC_T1_eligibility.md` §8 与本票交叉引用（Implementer 已含 §8 草稿）
- NonScope:
  - 不修改 `ticket_eligibility.py` 判定规则（除非集成 bugfix 另开子项）
  - 不接 `.cursor/hooks/capture_session_context.py`（入口 B · 见 WC_T1 §8.3 · 后续票）
  - 不改 `dispatch_executor.build_dispatch_plan` 分桶逻辑（入口 C · 后续票）
  - 不调用 Cursor API、不自动开 chat、不写 `*_state.md`
  - 不替代 W5-T1 `check_case_eligibility`（case 目录 SSOT 不同）
- AllowedPaths:
  - `04_Workflows/_dispatch_cards.py`
  - `scripts/run_dispatch_cards.py`
  - `tests/test_dispatch_cards.py`
  - `tests/fixtures/dispatch/`（可增 eligibility 相关 fixture 或复用 `TEST-BLK` 等）
  - `docs/control_plane_dispatch_executor.md`
  - `docs/wave_c/WC_T1_eligibility.md`（§8 状态同步：标注「入口 A 已由本票实现」— 仅验收后）
  - `artifacts/control_plane/dispatch_cards_run.latest.json`（summary 字段扩展；样例可选 commit）
- BlockedPaths:
  - `04_Workflows/ticket_eligibility.py`（除非 blocker 级 bugfix 且 Reviewer 同意）
  - `.cursor/hooks/**`
  - `04_Workflows/dispatch_executor.py`（分桶逻辑）
  - `04_Workflows/tickets/*_state.md`（只读）
  - `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `HARNESS_CONSTITUTION.md`
  - `core/**` · `.github/workflows/**`
- Dependencies:
  - **WC-T1**（`04_Workflows/ticket_eligibility.py` + `scripts/run_ticket_eligibility.py` + `tests/test_ticket_eligibility.py`）
  - **W-next-DISPATCH-CARDS-MVP** / `_dispatch_cards.generate_cards`（已存在）
  - 设计 SSOT：`docs/wave_c/WC_T1_eligibility.md` §8.1–§8.2
- AcceptanceCriteria:
  - AC-1: `--eligibility-gate block` 时，对 `overall_status=blocked` 或 unresolved dependency 的 fixture 票 **不** 生成 `*.cursor.md`，且 summary 含 `eligibility_blocked` 与 `reasons`
  - AC-2: `--eligibility-gate off` 行为与集成前一致（回归）
  - AC-3: `--eligibility-gate warn` 仍写卡，但 summary/card provenance 含 eligibility warning
  - AC-4: `--force-eligibility` 在 block 模式下仍写卡，且 summary 记录 `eligibility_override: true`
  - AC-5: `python -m unittest tests.test_dispatch_cards tests.test_ticket_eligibility -v` 全绿
  - AC-6: `docs/control_plane_dispatch_executor.md` 已文档化 gate flags 与 Orchestrator 操作示例
- **需审批／批文**: **否**（Control Plane 本地脚本；默认不启用 hook 硬闸）

---

## STATE

- overall_status: accepted_with_gaps
- implementation_status: done
- current_owner: orchestrator
- next_action: 关票完成；可选 follow-up UT（unresolved-dependency + gate=block 集成场景）；入口 B/C 仍 deferred（WC-T1 §8.3 / §8.1 #C）
- last_updated: 2026-06-14 · orchestrator · scribe
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files:
  - `04_Workflows/_dispatch_cards.py` — `generate_cards` 接入 `check_ticket_eligibility`；gate off/warn/block + force override；summary 增 `eligibility_blocked` / `eligibility_gate`
  - `scripts/run_dispatch_cards.py` — `--eligibility-gate`、`--force-eligibility` CLI
  - `tests/test_dispatch_cards.py` — `TestDispatchCardsEligibilityGate` 四类 gate 覆盖
  - `tests/fixtures/dispatch/blocked_plan.json` — blocked ticket plan fixture
  - `docs/wave_c/WC_T1_eligibility.md` — §8 入口 A 标 implemented
- artifacts: summary 含 `eligibility_blocked[]`、`eligibility_gate`、`eligibility_override`（force 时）
- verification: `python -m unittest tests.test_dispatch_cards tests.test_ticket_eligibility -v` → 21 tests OK
- behavior_notes:
  - 默认 `--eligibility-gate block`；ineligible 票跳过写卡并记入 `eligibility_blocked`
  - `warn` 仍写卡，Provenance 与 summary 含 `eligibility_warning`
  - `off` 不调用 gate，行为与集成前一致
  - `--force-eligibility` 在 block 下 override，summary `eligibility_override: true` + `eligibility_overridden_tickets[]`
- deferred_items:
  - 入口 B：`.cursor/hooks/capture_session_context.py` 软/硬闸（WC-T1 §8.3）
  - 入口 C：`build_dispatch_plan` eligibility annotate（WC-T1 §8.1 表 #C）
  - AC-6：`docs/control_plane_dispatch_executor.md` Dispatch Cards 小节（Scribe 或后续）

---

## C_REPORT

- conclusion: **accepted_with_gaps**
- blocking_issues: 无（无 boundary violation；无须返工 code）
- checks_summary: |
  - AC-1（block · ineligible skip）：PASS — `test_gate_block_skips_ineligible_ticket`；`cards_generated=0`、`eligibility_blocked[0].reasons` 含 `overall_status_blocked`；未写 `*.cursor.md`。集成层仅 `overall_status=blocked` fixture（TEST-BLK）；unresolved dependency 未做 generate_cards 级 fixture，但 `test_ineligible_unresolved_dependency` 已绿。
  - AC-2（gate off 回归）：PASS — `test_gate_off_generates_despite_ineligible`；`eligibility_gate=off`、仍写卡。
  - AC-3（gate warn + provenance）：PASS — `test_gate_warn_generates_with_warning`；summary `eligibility_warn:*`、card record `eligibility_warnings`、Provenance 含 `eligibility_warning`。
  - AC-4（force override）：PASS — `test_force_eligibility_override_in_block_mode`。
  - AC-5（unittest 全绿）：PASS — `python -m unittest tests.test_dispatch_cards tests.test_ticket_eligibility -v` → **21/21 OK**；與 Lane C smoke 62/62 OK 一致。
  - AC-6（dispatch executor 文檔）：GAP — `docs/control_plane_dispatch_executor.md` 尚無 eligibility gate 說明；與 B_REPORT deferred_items 一致。
  - Boundary：PASS — 變更限於 AllowedPaths。
  - Spec 對齊：PASS — `WC_T1_eligibility.md` §8 入口 A implemented；入口 B/C deferred。
- risk_level: low
- suggestions: |
  1. Scribe 補 AC-6：`docs/control_plane_dispatch_executor.md` § Dispatch Cards 增 Eligibility gate 小節。
  2. 可選 follow-up UT：unresolved-dependency + gate=block 集成場景；非 blocking。
  3. Orchestrator 更新 STATE：`overall_status` → done/accepted_with_gaps、`reviewer: done`；Scribe 末尾追加 Progress/Dashboard。
- reviewed_by: reviewer
- reviewed_at: 2026-06-14

---

## D_REPORT

- docs_updates:
  - `docs/control_plane_dispatch_executor.md` — § Dispatch Cards 增 **Eligibility gate** 小節（AC-6 收口）
  - `docs/WAVE_PROGRESS_DASHBOARD.md` — 分票收口表 WC-T1-INTEGRATION 行更新
  - `04_Workflows/00_Agent_Work_Progress.md` — 末尾关票条目
- progress_entry: WC-T1-INTEGRATION Reviewer **accepted_with_gaps**（21/21 UT）；Scribe 已补 AC-6 eligibility gate 文档与 Progress/Dashboard 索引。
- followup_suggestions:
  - 可选 UT：unresolved-dependency + `--eligibility-gate block` 集成 fixture
  - 入口 B：`.cursor/hooks/capture_session_context.py` 软/硬闸（WC-T1 §8.3）
  - 入口 C：`build_dispatch_plan` eligibility annotate
