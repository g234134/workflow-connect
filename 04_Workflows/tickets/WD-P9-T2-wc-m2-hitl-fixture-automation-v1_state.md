# WD-P9-T2-wc-m2-hitl-fixture-automation-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-E follow-up · 源自 Wave-D P9-T1 accepted_with_gaps（HITL fixture 自動化 · execute CI E2E）

---

## FRAME

- **summary**: 為 WC M2 demo runner 引入 **CI 可跑的 HITL fixture**（預錄 STATE / before_review 快照），讓 `--execute` 在無真人編輯下多走 comms 與 order 步驟。

- **goal**:
  - 在 `tests/fixtures/e2e_walkthrough/` 新增 HITL 快照集（例如 `WC-DEMO-1_before_review.md`、`WC-DEMO-1_state_review.md`、`WC-DEMO-1_state_ready_for_order.md`），對齊 runbook §3 / §4。
  - 擴展 `run_wc_m2_e2e_walkthrough.py`：新增 **`--use-hitl-fixtures`**（或等價 flag），execute 時自動 materialize 至 `artifacts/e2e/<ticket>/`，跳過人工 HITL 提示。
  - 新增 / 擴展 unittest：`--execute --use-hitl-fixtures` 在 temp / 隔離目錄下跑至 **step 4（order create/lookup）**，assert `orders.jsonl` / comms outbox 產物（dependencies 可用時）。
  - 維持 **demo-only 護欄**：僅 `WC-DEMO-*` ticket；artifacts 限 `artifacts/e2e/`；不寫正式 order ledger。
  - 更新 `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md`：標明 CI fixture 路徑與手工 HITL 的差異。

- **non_goals**:
  - 不自動化 Cursor chat 開啟（step 5 `wc.m2.chat.open_cursor` 仍可 skip 或 dry-run 提示）。
  - 不改 production ticket STATE 或 `artifacts/order_ledger/` 預設路徑。
  - 不宣稱 Wave C M2 完整 production E2E 閉環或 INT Tier-A pass。
  - 不推翻 P9-T1 Orchestrator 裁決：dry-run 允許空目錄、不寫業務檔。
  - 不將 execute 路徑升格為 merge-blocking required check（CI 若接，須 advisory）。

- **allowed_paths**:
  - `tests/fixtures/e2e_walkthrough/**`（HITL 快照新增）
  - `scripts/run_wc_m2_e2e_walkthrough.py`（fixture 模式 + step skip 邏輯）
  - `tests/test_run_wc_m2_e2e_walkthrough.py`（execute + fixture 整合 test）
  - `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md`（§3/§4 HITL fixture 小節）
  - `04_Workflows/tickets/WD-P9-T2-wc-m2-hitl-fixture-automation-v1_state.md`
  - `.github/workflows/eval-gate-ci.yml` 或 `core-agent-smoke.yml`（**可選** advisory smoke 一步）

- **blocked_paths**:
  - `04_Workflows/tickets/WC-*` 正式生產票（除 fixture 複製目標說明）
  - `artifacts/order_ledger/**` · 正式 outbox 六空間
  - `scripts/run_order_intake.py` 等 WC 核心 CLI **大改**（僅必要參數對齊時極小改）
  - 暗部 `core/**` · dashboard 百分比 · branch protection 設定

- **acceptance_criteria**:
  - **AC-1**：`python -m unittest tests.test_run_wc_m2_e2e_walkthrough -v` 全綠；既有 dry-run / 護欄 test 無回歸。
  - **AC-2**：新增 test：`--execute --use-hitl-fixtures --ticket WC-DEMO-1` 在隔離 `artifacts/e2e/` 下 **returncode=0**，且 step 3 comms 與 step 4 order **非 skip**（fixture 存在時）。
  - **AC-3**：execute+fixture 路徑產出 `orders.jsonl`（或 runbook 定義之等價產物），schema 與既有 execute test 一致。
  - **AC-4**：非 `WC-DEMO-*` ticket 或非法 artifacts-root 仍被拒；fixture 模式 **不**放寬護欄。
  - **AC-5**：runbook 已文件化 fixture 檔案清單、與手工 HITL 對照表、CI 建議命令。
  - **AC-6**：無 `--use-hitl-fixtures` 時行為與 Wave-D P9-T1 基線一致（仍印 HITL 提示、不自動改 STATE）。
  - **AC-7**（可選）：CI advisory step 可跑 fixture execute；失敗不阻 merge。
  - **AC-8**：B_REPORT 明示仍為 **demo skeleton**；未宣稱真人 HITL 已移除或 production ready。

---

## STATE

- **overall_status**: done_with_gaps
- **current_owner**: orchestrator
- **next_action**: 無（文書收口完成 · WD-WG-SCRIBE-REVIEW-closure-v1）
- **last_updated**: 2026-06-22 · scribe
- **notes**: Wave-E 新票；源自 Wave-D P9-T1 gap（execute 仍仰賴 HITL skeleton，CI 僅部分路徑）
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-20 開票落盤
  - **Implementer (B)**: done — 2026-06-20 HITL fixture + runner flag + tests + runbook §6.5
  - **Reviewer (C)**: done — 2026-06-22（文書回填 · 依 Wave-E 收口證據）
  - **Scribe (D)**: done — 2026-06-22

---

## B_REPORT (Implementer)

- **changed_files**:
  - `scripts/run_wc_m2_e2e_walkthrough.py` — `--use-hitl-fixtures`、materialize、artifact-local comms/order 路径
  - `tests/fixtures/e2e_walkthrough/WC-DEMO-1_before_review.md`（新增）
  - `tests/fixtures/e2e_walkthrough/WC-DEMO-1_state_review.md`（新增）
  - `tests/fixtures/e2e_walkthrough/WC-DEMO-1_state_ready_for_order.md`（新增）
  - `tests/test_run_wc_m2_e2e_walkthrough.py` — fixture execute + 护栏 test
  - `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md` — §6.5 HITL fixture 模式
- **skeleton / placeholder**: 仍为 **demo skeleton**；未移除手工 HITL runbook；未接 CI advisory step（AC-7 可选）
- **verification**:
  - `python -m unittest tests.test_run_wc_m2_e2e_walkthrough -v` → 11 tests OK
  - `python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --execute --use-hitl-fixtures --json` → `ok: true`；step 3/4 `ok`；产出 comms JSONL + `orders.jsonl`（`order_ledger_v1`）
- **guardrails**: 非 `WC-DEMO-*` / 非法 artifacts-root 仍拒；fixture 不写 live `04_Workflows/tickets/*_state.md`、不写 `artifacts/order_ledger/`
- **last_updated**: 2026-06-20 · implementer

---

## C_REPORT (Reviewer)

- **review_date**: 2026-06-20（文書回填 · 依 Wave-E 收口與 Progress 驗證證據；本輪未追加重跑）
- **reviewer_role**: Wave-E Reviewer (C) · WD-WG-SCRIBE-REVIEW-closure-v1 文書回填
- **conclusion**: **accepted_with_gaps**
- **blocking_issues**: 無 blocking；gaps 已記錄於 B_REPORT / D_REPORT / suggestions
- **verification_rerun**:
  - `python -m unittest tests.test_run_wc_m2_e2e_walkthrough -v` → **11/11 OK**
  - `python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --execute --use-hitl-fixtures --json` → `ok: true`（step 3/4 `ok`）
- **checks_summary**:
  - **AC-1～AC-6 ✅**: `--use-hitl-fixtures` execute 路徑產出 comms + `orders.jsonl`；護欄未放寬；無 flag 時與 P9-T1 基線一致
  - **AC-7 ⚠️**: Wave-G 已接 `.github/workflows/p9-wc-m2-fixture-execute.yml` job **`p9-wc-m2-fixture-execute`**（advisory · demo-only · non-blocking）；仍非 production E2E
  - **AC-8 ✅**: B_REPORT 明示 demo skeleton
  - **Rule 3/8 ✅**: demo-only；未寫 live ticket STATE 或 prod order ledger
- **risk_level**: low
- **suggestions**: step 5 Cursor chat 仍 skip；真人 HITL runbook 保留；prod 金流閉環另票

---

## D_REPORT (Scribe)

- **verdict_echo**: Reviewer **`accepted_with_gaps`** — AC-1～AC-6 滿足；`--use-hitl-fixtures` 讓 execute 走 step 3/4 並產出 comms + `orders.jsonl`。
- **closure_summary**: 三份 HITL 快照 fixture + runbook §6.5；仍標 **demo skeleton**。Wave-G 已以 non-blocking advisory CI（`p9-wc-m2-fixture-execute`）部分覆蓋 AC-7，仍保留為非 prod gate 的 gap。
- **gaps**: step 5 `wc.m2.chat.open_cursor` 仍 skip；未宣稱 production E2E 或 INT Tier-A pass。
- **progress_entry**: WD-P9-T2 HITL fixture 自動化 — **`accepted_with_gaps`**；walkthrough unittest **11/11 OK**。
- **scribe_date**: 2026-06-22 · WD-WG-SCRIBE-REVIEW-closure-v1

**下游 Execution 入口票（2026-06-23 · payment closure 鏈）**

| 票 id | 與 fixture execute 關係 |
|-------|-------------------------|
| `WH-P9-PROD-payment-happy-path-execute-v1` | 可沿用 `--use-hitl-fixtures` 至 order DRAFT 後接 payment 步 |
| `WH-P9-PROD-order-status-transition-impl-v1` | step 4 後狀態轉移 CLI |
| `WH-P9-PROD-payment-sandbox-adapter-v1` | charge → PAID mock |

索引：`WH-P9-PROD-payment-closure-bootstrap-v1`（WC-M3 scope 母票）。

#### 2026-06-24 · payment sandbox 補記

- 本票 `--use-hitl-fixtures` execute 路径（step 3/4 comms + order `DRAFT` · **11/11** walkthrough tests）为 payment 演练之上游基线；下游 `WH-P9-PROD-payment-happy-path-execute-v1` 已沿用同一路径延伸至 sandbox **DRAFT→PAID**（`done_with_gaps` · 2026-06-24 战报 · 25/25 tests）。
- fixture execute **尚未** 内建 payment 步 — happy-path 仍依赖 step 4 后手工 `transition` / `pay` CLI；`WH-P9-M2-runner-step6-payment-v1`（`frame_ready`）目标为一键 fixture execute 至 PAID。
- runbook §4+ payment 正文 · advisory CI smoke · prod real provider 分别由 `WH-P9-WC-T7-runbook-payment-section-v1` · `WH-P9-CI-payment-sandbox-smoke-v1` · `WH-P9-PROD-real-provider-v1`（**blocked**）承接；本 parent 票 scope 不变。
- 仍 **demo skeleton** · Wave-G advisory CI **≠** payment sandbox CI **≠** INT Tier-A · **≠** prod 金流 gate。
