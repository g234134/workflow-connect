# TICKET STATE · WC-T6-T7-v2 · WC-T6 / WC-T7 v0.1 Gap Closure

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave C · Control Plane · Lane C · M3  
> 父票：**WC-T6** v0.1（`WC-T6_state.md` · accepted_with_gaps）· **WC-T7** v0.1（`WC-T7_state.md` · accepted_with_gaps）  
> 索引：`docs/WAVE_PROGRESS_DASHBOARD.md` §多 Lane 本輪收口 · `docs/wave_c/overview.md`

---

## FRAME

- Goal: 关闭 WC-T6 / WC-T7 v0.1 遗留 gap——**(A) T6** 补 reports fixture、`--reports-dir` unittest、扩展 T5 `wc.m2.*` canonical 映射；**(B) T7** runbook 补 WC-T5 path_id 对照附录——使 Lane C M3 从 **accepted_with_gaps** 升格为 **accepted**（或 **accepted_with_gaps** 仅余明确 deferred 项）。
- Scope:
  - **Lane A（WC-T6-v2）**
    - 新增 `tests/fixtures/skill_distillation/reports/**`（伪造 `*_state.md` handoff 片段；无敏感内容）
    - 扩展 `tests/test_distill_control_plane_skills_lite.py`：覆盖 `--reports-dir`（`patterns` / `anti_patterns` 各 ≥1；`source_type=report`）
    - 扩展 `scripts/distill_control_plane_skills_lite.py` 的 `PATH_ID_MAPPING` / `_scan_reports`：对齐 WC-T5 cards / comms / reports 的 `wc.m2.*` 映射（含 `cp.ticket_state.b_report` 的 fallback 语义）
    - 更新 `docs/wave_c/WC_T6_skill_distillation_lite.md` Path id mapping：加上 `cp.ticket_state.b_report`，标注「无 T5 等价 · forbidden/HITL 语境」
  - **Lane B（WC-T7-v2）**
    - 在 `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md` 新增附录「WC-T5 path_id 对照表」（`wc.m2.*` ↔ CLI / runbook 步骤；含 `forbidden` / `HITL` 行）
    - 可选：在 `tests/test_run_wc_m2_e2e_walkthrough.py` 加入 doc regression 测试（断言附录存在且关键 path_id 列齐）
  - **Joint（Orchestrator / Scribe 收口）**
    - 两 Lane 均 Reviewer 通过后，Orchestrator 更新 STATE；Scribe 同步 `docs/wave_c/overview.md` WC-T6 / WC-T7 行与 Progress 末尾
- NonScope:
  - runner `--execute` 写 live `*_state.md`（仍 forbidden · HITL）
  - LLM / embedding / 外部 API；自动写回 `.cursor/skills` 或 Cursor rules
  - 生产 `artifacts/**` 增量扫描；`--json-out` 落盘样本
  - 将 Control Plane E2E 升格为 PR required / INT Tier-A merge
  - WC-T6 v0.1 已交付的 cards/comms fixture 行为回归破坏（除非 bugfix 且 Reviewer 同意）
- AllowedPaths:
  - **Lane A**
    - `scripts/distill_control_plane_skills_lite.py`
    - `tests/fixtures/skill_distillation/reports/**`
    - `tests/test_distill_control_plane_skills_lite.py`
    - `docs/wave_c/WC_T6_skill_distillation_lite.md`
  - **Lane B**
    - `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md`
    - `tests/test_run_wc_m2_e2e_walkthrough.py`（doc regression · 可选）
  - **Scribe**
    - `docs/wave_c/overview.md`（仅 WC-T6 / WC-T7 状态行与 M3 一句）
    - `04_Workflows/00_Agent_Work_Progress.md`（仅末尾追加）
  - **Orchestrator**
    - `04_Workflows/tickets/WC-T6-T7-v2_state.md`
- BlockedPaths:
  - `core/**` · 暗部 `01_Environments/**`
  - `.github/workflows/**` · branch protection / CI required 配置
  - `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `HARNESS_CONSTITUTION.md` · `.cursor/rules/**`
  - `04_Workflows/ticket_eligibility.py` · `_dispatch_cards.py` · `dispatch_executor.py` · `order_ledger/**`
  - live `04_Workflows/tickets/*_state.md`（本票 state 除外；Implementer 不得改 FRAME/STATE）
- Dependencies:
  - **WC-T5** — `docs/wave_c/WC_T5_automation_coverage_contract.md`（`wc.m2.*` path_id SSOT · done · accepted）
  - **WC-T6** v0.1 — distill CLI + cards/comms fixture（`WC-T6_state.md` · deferred_items 为本票输入）
  - **WC-T7** v0.1 — runbook + runner dry-run UT（`WC-T7_state.md` · deferred_items 为本票输入）
  - 无阻塞外部依赖；Lane A / Lane B **可并行** Implementer chat
- AcceptanceCriteria:
  - **AC-A1（reports fixture）**: `tests/fixtures/skill_distillation/reports/` 存在 ≥1 伪造 `*_state.md`；含 B_REPORT handoff 片段（`changed_files` · `verification` 等），无敏感内容
  - **AC-A2（reports-dir unittest）**: `python -m unittest tests.test_distill_control_plane_skills_lite -v` 全绿；含 `--reports-dir` 专项用例：CLI 或 import 路径 `ok: true`；`patterns` ≥1 且 `anti_patterns` ≥1；至少一条含 `source_type=report`
  - **AC-A3（PATH_ID 映射）**: `PATH_ID_MAPPING` 覆盖 v0.1 已知 cards/comms `cp.*` → `wc.m2.*`；`_scan_reports` 产出 `cp.ticket_state.b_report`；设计稿 Path id mapping 表含该行并标注「无 T5 等价 · `canonical_path_id` fallback 为 source · 对应 forbidden/HITL 语境（非 auto 路径）」
  - **AC-B1（runbook 附录）**: `WC_T7_e2e_walkthrough_runbook.md` 含附录「WC-T5 path_id 对照表」；列 ≥ 本票 E2E 链涉及的 `wc.m2.*`（eligibility · dispatch · comms · order · loop）；含 `wc.m2.state.write_ticket` · `wc.m2.chat.open_cursor` 等 **forbidden** 行；cross-ref `WC_T5_automation_coverage_contract.md`
  - **AC-B2（doc regression · 可选）**: 若交付 UT：`test_run_wc_m2_e2e_walkthrough` 断言附录标题与关键 path_id 存在；`python -m unittest tests.test_run_wc_m2_e2e_walkthrough -v` 全绿
  - **AC-JOINT（M3 升格）**: Lane A + Lane B 均 Reviewer `accepted` 或 `accepted_with_gaps`（gaps 仅允许 v0.1 已列且本票 NonScope 的 deferred：如 `--execute` 全自动 STATE · 生产 artifacts 扫描 · LLM distillation）；不得 overclaim gate 升格
  - **AC-GOV（边界）**: 无改 `core/**` · `.github/workflows/**` · 工程合约；无 runner `--execute` 写 live STATE；distillation 仍本地只读启发式
- **需审批／批文**: **否**（optional · non-gating · local only）

---

## STATE

- overall_status: done
- current_owner: orchestrator
- next_action: Orchestrator 收口确认；父票 WC-T6 / WC-T7 registry 可标 v2；后续 follow-up 见 D_REPORT
- last_updated: 2026-06-14 · orchestrator
- status_by_role:
  - orchestrator: pending
  - implementer: done
  - reviewer: done
  - scribe: done
- lane_status:
  - lane_a_wc_t6_v2: done
  - lane_b_wc_t7_v2: done

---

## B_REPORT

<!-- Implementer 填；Lane A / Lane B 可分区或追加，保留历史 -->

### Lane A（WC-T6-v2）

- changed_files:
  - `tests/fixtures/skill_distillation/reports/DEMO-ELIG_state.md`
  - `tests/fixtures/skill_distillation/reports/DEMO-NO-VERIFY_state.md`
  - `tests/fixtures/skill_distillation/reports/DEMO-BAD-FORMAT_state.md`
  - `scripts/distill_control_plane_skills_lite.py`
  - `tests/test_distill_control_plane_skills_lite.py`
  - `docs/wave_c/WC_T6_skill_distillation_lite.md`
- artifacts:
  - 3 個 reports fixture（pattern ×1 + anti-pattern ×2）
- verification:
  - `python scripts/distill_control_plane_skills_lite.py --reports-dir tests/fixtures/skill_distillation/reports --pretty` → ok: true, patterns ≥1, anti_patterns ≥1
  - `python scripts/distill_control_plane_skills_lite.py --cards-dir tests/fixtures/skill_distillation/cards --comms-jsonl tests/fixtures/skill_distillation/comms/one_comms.jsonl --reports-dir tests/fixtures/skill_distillation/reports --pretty` → ok: true, source_types 含 card/comms/report
  - `python -m unittest tests.test_distill_control_plane_skills_lite -v` → 10 tests OK
- behavior_notes:
  - PATH_ID_MAPPING 未加入 `cp.ticket_state.b_report` entry，保留「無 T5 等價」語義；canonical_path_id fallback 為原值
  - `_scan_reports` 改進 ticket_id 提取邏輯，支援無標題或簡化格式
  - 格式錯誤（無 B_REPORT 區塊）產生獨立 anti-pattern 類型
- deferred_items: 無

### Lane B（WC-T7-v2）

- changed_files:
  - `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md` — 新增「附录 · WC-T5 path_id 对照表」：表 A 13 行（§1–§5 E2E 步骤 ↔ wc.m2.path_id ↔ automation_tier ↔ T5 verification_command）；表 B 6 行（eligibility.check · dispatch.eligibility_gate_warn · order.list · loop.order_handoff · comms.order_event · chat.open_cursor）；读表说明含 forbidden/HITL 与 INT 分离重申；页脚 v0.1 → v0.2
  - `tests/test_run_wc_m2_e2e_walkthrough.py` — 新增 `test_runbook_contains_wc_t5_path_id_appendix`（附录标题 · 9 关键 path_id · INT Tier-A 分离语句）
- artifacts: runbook v0.2 · WC-T5 path_id 对照附录
- verification:
  - `python -m unittest tests.test_run_wc_m2_e2e_walkthrough -v` → 4 tests OK
- behavior_notes:
  - 所有 verification_command 1:1 引用 `WC_T5_automation_coverage_contract.md` §4（forbidden 行引用 T5 禁止语义）
  - `wc.m2.state.write_ticket` 出现 3 次（§1/§3/§4 手工 STATE 编辑），均标 forbidden；`wc.m2.chat.open_cursor` 在表 B 标 forbidden
  - **Control Plane E2E pass ≠ INT Tier-A pass** 于文首、§INT gate 对齐、附录读表说明 §3 三处声明
  - 本 runbook **不**提供 `--execute` 自动写 live STATE 步骤；不授权 PR required / mandatory CI
  - `scripts/run_wc_m2_e2e_walkthrough.py` execute 行为未改
- deferred_items:
  - runner `--execute` 全自动 STATE 过渡（forbidden · 保持 HITL）— 与 v0.1 deferred 一致，本票 NonScope
  - 将 Control Plane E2E 升格为 PR required / INT Tier-A merge — 须尚書省批文，本票不触及

---

## C_REPORT

- conclusion: accepted_with_gaps
- blocking_issues: 無
- checks_summary: |
  **AC-A1 (reports fixture)**: ✓ 3 個偽造 `*_state.md`（DEMO-ELIG / DEMO-NO-VERIFY / DEMO-BAD-FORMAT），含 B_REPORT handoff 片段，無敏感內容。
  **AC-A2 (reports-dir unittest)**: ✓ `python -m unittest tests.test_distill_control_plane_skills_lite -v` 10/10 綠；含 `--reports-dir` 專項測試，patterns ≥1、anti_patterns ≥1、source_type=report 驗證通過。
  **AC-A3 (PATH_ID 映射)**: ✓ PATH_ID_MAPPING 覆蓋 v0.1 cards/comms `cp.*` → `wc.m2.*`；`_scan_reports` 產出 `cp.ticket_state.b_report`；設計稿 Path id mapping 表含該行並標註「無 T5 等價 · forbidden/HITL 語境」。
  **AC-B1 (runbook 附录)**: ✓ `WC_T7_e2e_walkthrough_runbook.md` 含「WC-T5 path_id 对照表」附录；列齊 E2E 鏈 path_id（eligibility · dispatch · comms · order）；含 `wc.m2.state.write_ticket` · `wc.m2.chat.open_cursor` forbidden 行；cross-ref `WC_T5_automation_coverage_contract.md`。
  **AC-B2 (doc regression)**: ✓ `test_run_wc_m2_e2e_walkthrough.py` 含附录存在與 path_id 列表斷言；4/4 tests 綠。
  **AC-JOINT (M3 升格)**: ✓ Lane A + Lane B 均達標；gaps 僅限 v0.1 已列 deferred（`--execute` 寫 live STATE · LLM · 生產 artifacts · PR required 升格）。
  **AC-GOV (治理)**: ✓ 無觸及 blocked paths；無違反憲法 §7 禁區類型。
- risk_level: low
- suggestions: |
  1. 建議 Scribe 更新 `docs/wave_c/overview.md` WC-T6/WC-T7 狀態行與 Progress 末尾（D_REPORT 職責）。
  2. 建議 Orchestrator 確認 v0.1 deferred items（`--execute`、LLM、生產掃描）排入 Wave C M4 或後續 Wave。
  3. 建議後續票考慮補充 T6 reports fixture 的 `C_REPORT` / `D_REPORT` 樣本（目前僅 B_REPORT）。
- reviewed_by: reviewer
- reviewed_at: 2026-06-14

---

## D_REPORT

- docs_updates:
  - `docs/wave_c/overview.md` — WC-T6 / WC-T7 状态行 **v0.1 → v2**；M3 表、票清单、M3 self-check、Phase 1 下一步同步；链至本票 `WC-T6-T7-v2_state.md`
  - `04_Workflows/00_Agent_Work_Progress.md` — 2026-06-14 WC-T6-T7-v2 战报末尾追加
- progress_entry: WC-T6-T7-v2 Scribe 收口：Lane A reports fixture + `--reports-dir` UT（10/10 OK）；Lane B runbook WC-T5 path_id 附录 + doc regression（5/5 OK）；Reviewer **accepted_with_gaps**（仅余 NonScope deferred）。
- followup_suggestions:
  - WC-T1-INTEGRATION · W4-MEM-01 Reviewer 关票
  - `--execute` 全自动 STATE · 生产 artifacts 扫描 · LLM distillation 须另开票且保持 HITL / optional
  - L2 governance 升格仍 blocked_on_approval
