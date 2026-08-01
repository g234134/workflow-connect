# WD-P9-T1-wc-m2-order-demo-e2e-v1 — Ticket State

> FRAME / STATE / B_REPORT 待 Orchestrator / Implementer 回填；本檔 C_REPORT 由 Wave-D Reviewer (C) 於 2026-06-20 交付。

---

## STATE

- **overall_status**: done_with_gaps
- **current_owner**: orchestrator
- **next_action**: 無（文書收口完成 · WD-WG-SCRIBE-REVIEW-closure-v1）
- **last_updated**: 2026-06-22 · scribe
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-20 收口裁決
  - **Implementer (B)**: done
  - **Reviewer (C)**: done — 2026-06-20
  - **Scribe (D)**: done — 2026-06-22
- **gap_summary**:
  - dry-run 仍建立空目錄（已裁決為允許，見 orchestrator_decisions）
  - B_REPORT 待 Implementer/Scribe 補寫
- **orchestrator_decisions**:
  - **dry-run 語義**：dry-run **允許建立空目錄**，但**不寫業務檔**（如 orders.jsonl）；本輪不開 Wave-E 修補票
- **b_report_note**: B_REPORT 待 Implementer/Scribe 補寫

---

## B_REPORT (Implementer)

### backfill_meta

| 欄位 | 值 |
|------|-----|
| **written_date** | 2026-06-20 |
| **author_role** | Wave-D Implementer (B) · WD-DOC-BREPORT-backfill-v1 |
| **source_refs** | 本票 C_REPORT (2026-06-20) · `00_Agent_Work_Progress.md` · `scripts/run_wc_m2_e2e_walkthrough.py` · `tests/test_run_wc_m2_e2e_walkthrough.py` · `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md` |
| **note** | verification 為**引用** Reviewer 2026-06-20 重跑；本 backfill 輪未重新執行 |

### §1 變更檔案清單

| 檔案路徑 | 變更類型 | 說明 |
|----------|----------|------|
| `scripts/run_wc_m2_e2e_walkthrough.py` | 新增/修改 | WC-T7 M2 E2E walkthrough runner：`--dry-run` / `--execute` 雙模式；僅允許 `WC-DEMO-*` ticket；artifacts 限 `artifacts/e2e` 前綴；HITL 步驟 print-only（skeleton） |
| `tests/test_run_wc_m2_e2e_walkthrough.py` | 新增 | 8 個 unittest：ticket/artifacts 驗證、dry-run summary、execute orders.jsonl schema、runbook path 對照 |
| `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md` | 修改 | 對齊 runner CLI；2026-06-20 追加 dry-run 空目錄 Orchestrator 裁決一句 |

### §2 Skeleton / Placeholder

| 項目 | 狀態 | 說明 |
|------|------|------|
| HITL 步驟（§1 setup、§3/§4） | skeleton | runner 僅 print manual STATE 編輯指引；未全自動化（**Wave-E footnote**：fixture execute 模式 `--use-hitl-fixtures` 由 **WD-P9-T2** 提供，仍屬 demo skeleton，不改本 parent 票 live STATE） |
| execute 完整 CI E2E | skeleton | `--execute` 依賴外部 CLI/deps；deps 缺失時步驟 skip；非 CI 完整閉環 |
| 真金流 / prod order ledger | placeholder | 明確拒絕非 `WC-DEMO-*`；不寫正式 order ledger 目錄 |

### §3 Placeholder（無）

除 §2 HITL / execute 自動化 skeleton 外，無額外 placeholder。

### §4 驗證證據

> **來源**：Wave-D Reviewer (C) · 2026-06-20 重跑；**非**本 backfill 輪現場執行。

**命令與結果**（cwd：戰車根）：

```powershell
python -m unittest tests.test_run_wc_m2_e2e_walkthrough -v
```

**結果**：**8/8 OK**

- `test_reject_non_demo_ticket` / `test_non_demo_ticket_rejected_in_execute` — 非 demo ticket 拒絕或降級
- `test_dry_run_with_demo_ticket` / `test_dry_run_does_not_write_files` — dry-run 模式與業務檔不寫入
- `test_reject_non_e2e_artifacts_root` — artifacts-root 前綴護欄
- `test_runbook_contains_wc_t5_path_id_appendix` — runbook path 對照
- `test_execute_creates_orders_jsonl` — execute 路徑 orders.jsonl schema（deps 可用時）
- `test_non_demo_ticket_allowed_in_dry_run` — dry-run 下非 demo 行為

### §5 阻塞

無 blocking。Reviewer 結論：**accepted_with_gaps**。

### §6 behavior_notes

- **dry-run / execute 雙模式**：dry-run 印 summary、不跑 destructive 步驟；execute 僅 demo ticket + `artifacts/e2e` root。
- **dry-run 空目錄（Orchestrator 裁決）**：dry-run **允許**建立空的 `artifacts/e2e/<ticket_id>/` 目錄，但**不寫業務檔**（如 `orders.jsonl`）；嚴格「零 filesystem touch」**非**本輪 AC；**不開 Wave-E 修補票**。
- **命名**：測試 ticket 如 `WC-DEMO-TEST` 仍屬 demo 前綴；易誤解但行為正確。
- **非 prod**：未宣稱真金流閉環；execute 寫入限 demo artifacts 樹。

### §7 known_gaps / deferred_items

| Gap | 現狀 | 後續 |
|-----|------|------|
| 正式 B_REPORT 缺失 | 本段 backfill 補齊 | — |
| dry-run 仍 mkdir 空目錄 | 已裁決為允許 | B_REPORT 明示；不開 Wave-E 票 |
| HITL 未自動化 | skeleton print-only | 可選 **WD-P9-T2** HITL fixture 自動化 |

> **Wave-E footnote（2026-06-20）**：**WD-P9-T2** 已交付 `--use-hitl-fixtures` execute 路徑（`tests.test_run_wc_m2_e2e_walkthrough` **11/11 OK**）；無 flag 時行為仍與 Wave-D P9-T1 基線一致（print-only HITL）。本 parent 票仍 **demo skeleton**，STATE verdict 不變。
| execute 非 CI 完整 E2E | deps 缺失時 skip | P9-T2 或 CI 整合票 |
| `WC-DEMO-TEST` 命名易誤解 | 仍屬合法 demo 前綴 | 可選 rename 測試 fixture |

### §8 下一步

1. **Scribe (D)** 填 D_REPORT。
2. **Wave-E（可選）** WD-P9-T2 HITL fixture 自動化。

### §9 Override / 特殊留痕

無 override。變更限 demo runner + tests + runbook；未觸 prod order ledger 或其它 Phase 模組。

---

## C_REPORT (Reviewer)

- **review_date**: 2026-06-20
- **reviewer_role**: Wave-D Reviewer (C)
- **conclusion**: **accepted_with_gaps**
- **blocking_issues**: 無
- **verification_rerun**:
  - `python -m unittest tests.test_run_wc_m2_e2e_walkthrough -v` → **8/8 OK**
- **checks_summary**:
  - **Rule 3 (最小觸及) ✅**: 主要修改 `run_wc_m2_e2e_walkthrough.py`、對應 tests 與 runbook；未觸 prod order ledger 或其它 Phase 模組
  - **Rule 6 (路徑權威) ✅**: repo root 由 script 推導；artifacts 嚴格限制在 `artifacts/e2e` 下
  - **Rule 7 (skeleton 誠實標示) ✅**: 腳本 docstring 與 runbook 明示 skeleton、HITL 步驟未全自動化
  - **Rule 8 (邊界尊重) ✅**: execute 僅允許 `WC-DEMO-*`；未寫入正式 order ledger 目錄
  - **Rule 11 (驗證後宣稱) ✅**: demo unittest 8/8 綠；含 dry-run、execute、目錄驗證
  - **FRAME ✅**: dry-run / execute 雙模式；demo tickets only；未宣稱真金流閉環
- **behavior_notes**:
  - 非 `WC-DEMO-*` ticket 被拒或降級 dry-run；artifacts-root 非 `artifacts/e2e` prefix 拒絕
  - **dry-run gap**: 仍會建立空目錄（`mkdir()`）；嚴格來說非「完全零寫入」
  - **命名**: 測試用 `WC-DEMO-TEST` 易誤解（實際仍屬 demo 前綴）
- **test_coverage**:
  - ticket/artifacts 驗證、dry-run summary、execute orders.jsonl schema（dependencies 可用時）、runbook path 對照
- **b_report_gap**: 缺正式 `_state.md` B_REPORT
- **risk_level**: low
- **suggestions**:
  - 補 ticket state + B_REPORT
  - 若對齊 AC「dry-run 零寫入」：改 dry-run 不建目錄；或 B_REPORT 註明「允許空目錄 side-effect」
  - 可選 WD-P9-T2：HITL fixture 自動化，讓 execute 在 CI 完成更完整 E2E

---

## D_REPORT (Scribe)

- **verdict_echo**: Reviewer **`accepted_with_gaps`**（2026-06-20）；WC M2 demo E2E walkthrough runner 已交付。
- **closure_summary**: `run_wc_m2_e2e_walkthrough.py` dry-run/execute 雙模式；僅 `WC-DEMO-*` + `artifacts/e2e` 護欄；Wave-D **8/8 OK**（後續 P9-T2 擴至 **11/11**）。已知 gap：dry-run 允許空目錄（Orchestrator 裁決）；HITL 仍 skeleton（**WD-P9-T2** 已補 fixture execute 路徑）。
- **progress_entry**: WD-P9-T1 WC M2 order demo E2E — **`accepted_with_gaps`**；walkthrough unittest **8/8 OK**（Wave-D 基線）。
- **scribe_date**: 2026-06-22 · WD-WG-SCRIBE-REVIEW-closure-v1

**下游 Execution 入口票（2026-06-23 已建檔 · WC-M3 payment closure）**

| 票 id | 與本 parent 關係 |
|-------|------------------|
| `WH-P9-PROD-payment-closure-bootstrap-v1` | WC-M3 scope SSOT · 對齊 runner 護欄 |
| `WH-P9-PROD-order-status-transition-impl-v1` | 擴展 order create 後狀態鏈 |
| `WH-P9-PROD-payment-sandbox-adapter-v1` | mock charge 模組 |
| `WH-P9-PROD-payment-happy-path-execute-v1` | 擴展 `--use-hitl-fixtures` execute 至 pay→paid |

完成 happy-path execute 後本票 gap「無 pending→paid」可縮小 · parent 仍 **`done_with_gaps`**（≠ prod 金流）。

#### 2026-06-24 · payment sandbox 補記

- 本 parent 票交付之 M2 demo runner（dry-run / manual HITL / `--use-hitl-fixtures` execute）護欄不變；**payment 段**已由下游 `WH-P9-PROD-payment-happy-path-execute-v1` 在 sandbox 完成首條 **DRAFT→PAID** 可重跑演練（`WC-DEMO-1` · 25/25 tests · `done_with_gaps`）。
- 現況 gap 已從「无 pending→paid」縮至：**runner 未内建 step 6-payment**（仍須手工 CLI 或 follow-up 票收编）· **无 prod 金流** · **无 required CI**。
- payment 線後續演進不在本 parent 票 scope，而由四張 follow-up 承接：`WH-P9-M2-runner-step6-payment-v1`（runner）· `WH-P9-WC-T7-runbook-payment-section-v1`（runbook）· `WH-P9-CI-payment-sandbox-smoke-v1`（advisory CI）· `WH-P9-PROD-real-provider-v1`（**blocked** · prod 批文）。
- parent 票 overall 仍 **`done_with_gaps`**；sandbox payment pass **不可** 解读为本票或 INT Tier-A 升格。
