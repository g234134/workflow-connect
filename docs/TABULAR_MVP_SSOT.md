# Tabular MVP SSOT — Single Source of Truth

> **Role**: Repo **landing doc** for the core product mainline.  
> **Status**: v1 · doc-only · **非** prod gate · **非** closure 宣稱  
> **Date**: 2026-06-27  
> **Audience**: Implementer · Reviewer · Scribe · Orchestrator · PM

**Narrative anchor**

> This repo's core product path is **tabular data cleaning and delivery automation**; governance / CI / GA lines are **supporting rails**, not the primary product outcome.

---

## 1. Document hierarchy

| Layer | Document | Reader | Notes |
|-------|----------|--------|-------|
| **SSOT / landing** | **`docs/TABULAR_MVP_SSOT.md`（本檔）** | 全 repo 進場 | 產品主線收斂、主鏈入口、非目標邊界 |
| 對外產品規格 | `docs/PRODUCT_TABULAR_CLEANING.md` | 客戶、PM | C2-P1 · 服務介紹與交付物說明 |
| L1 trace 對照 | `docs/mvp-standard-trace-path.md` | 開發、QA | `demo_phase` / `sampleco` 可重跑 trace |
| Skill Cards | `docs/skill-cards-v1.md` | Agent 編排 | 工作流卡片與 tool 對照 |
| HITL 設計 | `docs/hitl-checkpoints-v1.md` | 流程設計 | Checkpoint A/B（設計 spec；部分 CLI 為 preview） |
| Agent 實驗線 | `docs/agent-run-standard-case-experiment-v1.md` | 實驗編排 | S1–S15 設計稿 · design-only 段落標示 |
| Tool 機器權威 | `tools/tabular_tool_catalog_v1.json` | 工具層 | `tool_id` · CLI 入口索引 |
| E2E 驗收 | `docs/MVP_CASE_E2E_DoD_v0.1.md` | QA | E2E 權威 · **≠** prod SLA |
| Cleaning profiles | `docs/tabular-cleaning-profiles-v1.md` | 開發、QA | Profile registry · field roles · rules |

**Tabular 主線已支援 `demo_phase` + `sampleco/2026-0001` 兩個標準案**（cleaning profiles：`phase_demo_v1` · `sampleco_order_profile`）。

**Governance guardrail（Batch 1 · 2026-06-27）**：Progress 末尾「Governance Decisions — Batch 1」之 `non_claims` / `hard_no` **仍有效**；本 SSOT **不**改 Phase%、Dashboard、CI gate、closure 狀態。

---

## 2. Product positioning

**一般表格型資料清洗與品質報告** — 針對已有欄位結構的 CSV / Excel 類表格，整理成可分析、可交接的乾淨檔案，並附清洗前後對照的品質報告。

| 維度 | 定義 |
|------|------|
| **核心價值** | 缺失 / 重複 / 異常 / 格式混亂 → 可審計清洗產物 + 品質證據 |
| **服務型態** | 專案制 · 批次處理 · 含人工確認點 · **非** 7×24 託管 |
| **Repo 主鏈** | `intake → eligibility/gate → cleaning → bundle → delivery/validation` |
| **鄰接能力** | Gov Core smoke、RAG、ask H 线、Monitoring Graph、Phase 8.x 编排 — **supporting rails**，非本 repo 首要交付物 |

詳細客戶視角說明見 `docs/PRODUCT_TABULAR_CLEANING.md`。

---

## 3. Supported inputs

| 輸入 | 支援 | 備註 |
|------|------|------|
| **CSV** | ✅ | UTF-8 建議；RFC 4180 相容 |
| **Excel（`.xlsx`）** | ✅（個案） | 多 sheet / 公式欄需事前約定 |
| **Excel（`.xls`）** | ⚪ 視個案 | 非預設保證 |
| 欄位說明 / schema | 建議 | 缺省時僅標記缺失，不猜測填補 |
| 主鍵 / 去重策略 | 建議 | 影響 gate 與 cleaning 行為 |

**規模基線（v1）**：單檔約 **≤ 100 萬列 / 1 GB**；更大需分批或拒收（見 Product Spec §2.4）。

---

## 4. Core problem types

本產品聚焦四類常見表格品質問題：

| 類型 | 英文 | 典型動作 |
|------|------|----------|
| **缺失** | Missing | 標記空值、依約定填預設、或拒絕關鍵欄缺失列 |
| **重複** | Duplicate | 依主鍵去重或輸出重複清單 |
| **異常** | Anomaly | 範圍 / 枚舉 / 跨欄邏輯檢查；標記或隔離 |
| **格式混亂** | Format | 日期統一、trim、數字格式、欄位命名標準化 |

---

## 5. Deliverables

標準交付包（以 `cases/demo_phase/` 為結構參考）：

| 產物 | 典型路徑 | 說明 |
|------|----------|------|
| **cleaned CSV** | `cases/<case>/cleaned/*_cleaned.csv` | 清洗後資料檔 |
| **cleaning_stats.json** | `cases/<case>/reports/cleaning_stats.json` | 清洗統計（列數、規則觸發等） |
| **report.json** | `cases/<case>/reports/report.json` | 結構化品質報告 |
| **report.md** | `cases/<case>/reports/report.md` | 可讀摘要 |
| **eligibility_result.json** | `cases/<case>/reports/eligibility_result.json` | Gate 判定落盤 |
| **delivery bundle** | `build_case_delivery_bundle` 產出 | 含 output_guard、signoff 等交付包元件 |

一鍵驗證入口：

```bash
python scripts/run_case_e2e_validation.py --case-dir cases/demo_phase --json
```

Near-auto 編排（control plane + unified driver · allowlist only）：

```bash
python scripts/manage_tabular_automation_state.py start \
  --case-dir cases/demo_phase --requested-by operator --json
python scripts/run_tabular_automation.py --case-id demo_phase --force --json
```

主鏈變更最小 regression（含 HITL + delivery approve · **任何 Tabular 主鏈改動必跑**）：

```bash
python scripts/run_demo_phase_regression_smoke.py --json
python scripts/run_tabular_mainline_regression_smoke.py --json
```

> `demo_phase` gate 為 `review_needed`；driver 需 `--force`（internal demo）或 CP-A approve 後 `--resume`。
> 雙案 smoke：`run_tabular_mainline_regression_smoke.py`（`demo_phase` + `sampleco/2026-0001`）。

---

## 6. Reference case — `demo_phase`

| 項 | 值 |
|----|-----|
| 路徑 | `cases/demo_phase/` |
| 輸入 | `raw/Phase.csv`（7 行 · Phase 表四列） |
| `client_ref` | `internal-demo` |
| Gate | `review_needed`（exit 2 · `rows<100`）→ cleaning 需 `--force` |
| 清洗結果 | 7 → 5 行；`qa_status=pass_with_warnings` |
| 用途 | C2-D1 demo · Skill Card A · MVP trace 最小樣本 |

逐步走查：`docs/C2-D1_DEMO_WALKTHROUGH.md` · `docs/MVP_DEMO_WALKTHROUGH_v0.1.md`

---

## 7. Explicit non-goals (out of scope)

以下**不**屬於 Tabular MVP 核心產品主線；repo 內相關工單為 supporting / experimental / design-only：

| 非目標 | 說明 |
|--------|------|
| **OCR / PDF 表格 / 掃描件** | 非結構輸入；不在 CLEAN intake 範圍 |
| **資料倉儲建模** | 不做 Kimball / 星型模型 / 企業級 ETL 平台 |
| **7×24 代運維 / on-call** | 專案制批次；非託管 SLA |
| **prod gate / governance 自動升級** | Batch 1 `hard_no` 仍有效；advisory CI ≠ merge gate |
| **Phase full-line closure 宣稱** | 見 Progress Batch 1 `GOV-PHASE-CLOSURE-FULL: NO` |
| **全自動無 HITL** | v1 保留 Checkpoint A/B 設計（見 §8.6） |
| **Gov ask / RAG / GraphRAG 主答案** | H 线能力；非表格清洗交付物 |
| **Non-tabular 首步處理** | 見 `docs/non-tabular-routing-catalog-v1.md` · shadow / sandbox 線 |
| **客戶自助一鍵上傳 pipeline** | 路線圖項；v1 未承諾 |
| **商業策略 / 定價 / 合約** | 不在本 SSOT |

---

## 8. Main chain — intake → delivery

### 8.1 Flow overview

```text
Intake
  └─ 建案 / 盤點輸入（intake.json + raw/）

Eligibility / Gate
  └─ 可受理性判定（accepted · review_needed · rejected）

Cleaning
  └─ tabular 清洗（缺失 / 重複 / 異常 / 格式）

Bundle
  └─ 組裝交付包 + output_guard

Delivery / Validation
  └─ E2E 驗證 · signoff · 可選 lookup / local UI

HITL Checkpoints（設計 · 極簡人工閘）
  ├─ A: Intake Confirmation（接案 / 路由計畫確認）
  └─ B: Delivery Confirmation（交付草稿確認）
```

**業務狀態節點**（L1 · 非 Langfuse span）：  
`uploaded → validated → gate_decision → processing → delivered`  
詳見 `docs/mvp-standard-trace-path.md` §4。

### 8.2 Stage → entrypoints

| 階段 | 腳本 / 模組 | 角色 |
|------|-------------|------|
| **Intake** | `scripts/new_cleaning_case.py` | 新案建 `case_dir` + `intake.json` + `raw/` |
| | `scripts/run_order_intake.py` | 訂單式 intake（若啟用 order ledger 路徑） |
| | `scripts/build_cases_index.py` | 掃描 `cases/` → `cases/index.json` |
| **Eligibility / Gate** | `scripts/check_case_eligibility.py` | P2 gate · `--json` 結構化輸出 |
| | `scripts/run_intake_gate_cli.py` | Intake gate layer preview / notify 路徑 |
| | `scripts/run_ticket_eligibility.py` | Ticket 級 eligibility 輔助 |
| **Cleaning** | `notebooks/csv_cleaning/clean_phase_demo.py` | P3 tabular 清洗（主鏈 runner） |
| | `notebooks/csv_cleaning/run_tabular_cleaning_plan.py` | Runbook planner（規劃用） |
| **Bundle** | `scripts/build_case_delivery_bundle.py` | P4 交付包 + output_guard |
| **Delivery / Validation** | `scripts/run_case_e2e_validation.py` | 一鍵 gate → clean → bundle |
| | `scripts/approve_tabular_delivery.py` | CP-B 後結構化 delivery approve/reject · 更新 index/signoff |
| | `scripts/run_mvp_mainline_regression.py` | 雙案（demo + sampleco）回歸 |
| | `scripts/run_demo_phase_regression_smoke.py` | **主鏈最小 smoke**（start→HITL→approve · `demo_phase`）· `docs/tabular-demo_phase-regression-v1.md` |
| | `scripts/lookup_case_history.py` | 只讀 case 索引查詢 |
| | `scripts/tabular_ops_summary.py` | **運營查 Tabular 案件現況**（automation · CP-A/B · delivery · DLQ） |
| | `app/local_ui.py` | Local UI 包裝上述 CLI · **NOT PROD** |
| **Routing / Tool layer（adjacent · plan_only 預設）** | `routing/intake_to_tabular_glue.py` | `task_type` → tool plan |
| | `tools/tabular_tool_selector.py` | Selector 推薦 |
| | `tools/tabular_tool_executor.py` | Executor + outbox |
| | `scripts/run_tabular_intake_tool_path.py` | Intake → tool path dry-run preview |

**工作目錄**：repo 根（與 `scripts/`、`cases/` 同级）· **Python**：3.10+

### 8.3 One-command E2E (reference)

```bash
# 最小 demo 案
python scripts/run_case_e2e_validation.py --case-dir cases/demo_phase --json

# 近真实客户对照案
python scripts/run_case_e2e_validation.py --case-dir cases/sampleco/2026-0001 --json
```

### 8.4 Step-by-step (demo_phase)

```bash
python scripts/build_cases_index.py

python scripts/check_case_eligibility.py --case-dir cases/demo_phase --json

python notebooks/csv_cleaning/clean_phase_demo.py \
  --case-dir cases/demo_phase --skip-eligibility --force

python scripts/build_case_delivery_bundle.py --case-dir cases/demo_phase --json
```

### 8.5 L1 artifacts checklist

| 信號 | 路徑 |
|------|------|
| Gate 落盤 | `cases/<case>/reports/eligibility_result.json` |
| 清洗報告 | `cases/<case>/reports/report.json` · `report.md` |
| 清洗統計 | `cases/<case>/reports/cleaning_stats.json` |
| 清洗檔 | `cases/<case>/cleaned/*_cleaned.csv` |
| 交付 signoff | `cases/<case>/delivery_signoff.md`（bundle 後） |
| Delivery approval state | `cases/<case>/delivery_approval.json` · mirrored on `automation_state.json` → `delivery` |

### 8.7 Delivery approval（CP-B 後 · v1）

結構化欄位（`delivery_approval.json` + index 鏡像）：

| 欄位 | 值域 | 說明 |
|------|------|------|
| `delivery_approval_status` | `pending` · `approved` · `rejected` | 人工 approve/reject 或 driver 維持 pending |
| `delivery_approved_by` / `delivery_approved_at` | string · ISO-8601 | approve 審計 |
| `delivery_bundle_path` | string | 預設 `reports/report.json` |
| `delivery_ready` | boolean | **僅當** CP-B approved **且** e2e pass **且** profile 策略允許（通常 `output_guard.status=ok`） |
| `signoff_recorded` | boolean | approve 且 gates 全過時 true |

**Warning guard 策略（v1）**：profile × `output_guard.status` 決定 `delivery_ready` 與 CP-B auto-skip；詳見 manifest **§1.12** · 程式 `scripts/tabular_warning_guard_lib.py`。

| Profile | guard=`ok` | guard=`warning` |
|---------|------------|-----------------|
| `demo_phase` | 可 auto `delivery_ready=true` | CP-B HITL · `delivery_ready=false` · internal only |
| `sampleco` | 可 `delivery_ready=true` | CP-B HITL **必經** · `delivery_ready=false` · internal only |
| `generic_low_risk_case` | 可 `delivery_ready=true` | fail-closed 對外 · partial internal |

**`delivery_ready` 規則**：三閘（CP-B · e2e · warning-guard policy）全過才 true；`rejected` **不可**由 driver 自動變 `approved`（須 explicit `--approve`）；**warning 下人工 approve 亦不可 override 為 true**。

```bash
# CP-B 完成後 · Lead 批准
python scripts/approve_tabular_delivery.py --case-id demo_phase --approve --by lead --json

# 拒絕（須 --reason）
python scripts/approve_tabular_delivery.py --case-id demo_phase --reject --by lead \\
  --reason "output_guard warning" --json

# 只評估 gates（不寫入）
python scripts/approve_tabular_delivery.py --case-id demo_phase --evaluate-only --json
```

Unified driver 在 `checkpoint_b` 步驟後呼叫 `maybe_update_delivery_readiness`：滿足條件且 status≠rejected 時可標 `delivery_ready`；否則保持 pending 並寫入 `readiness_gaps`。

> **邊界**：非 prod closure · 不取代 W8-T3 實驗線 `run_delivery_approval_cli.py`（outbox CP-B）；Lead 對外交付仍須人工最終確認（§19.2）。

### 8.6 HITL checkpoints A / B

| Checkpoint | 時機 | 設計 spec | CLI / 模組（現狀） |
|------------|------|-----------|-------------------|
| **A — Intake Confirmation** | Intake decision / suggested_route 後 | `docs/hitl-checkpoints-v1.md` §3 | `tabular_hitl_resume_lib.py` · `approve-a` · unified driver pause at `checkpoint_a` |
| **B — Delivery Confirmation** | Cleaning + delivery draft 完成後 | `docs/hitl-checkpoints-v1.md` §4 | `approve-b` · `approve_tabular_delivery.py` · `tabular_checkpoint_sync_lib.py` |

**現狀（2026-06-29）**：主鏈 **已接上** unified driver + CP-A/B CLI + delivery approve；`automation_state.json` 與 `automation_run_log.json` 經 `tabular_checkpoint_sync_lib` 同步 CP-B 欄位。仍 **非** prod closure：`review_needed` + `--force` 僅 internal 回歸；對外寄檔與收款在 repo 外。

**Non-Goals（重申）**：接案平台 API · 真實金流 · 客戶自助 SaaS — 見 §7。

### 8.8 Ops summary CLI（運營查現況 · read-only）

```bash
python scripts/tabular_ops_summary.py --case-id demo_phase
python scripts/tabular_ops_summary.py --case-id 2026-0001 --json
python scripts/tabular_ops_summary.py --all
```

輸出欄位：`automation_status` · `current_step` / `steps_completed` · CP-A/B · `output_guard_status` · `delivery_approval_status` / `delivery_ready` · `dlq_status` · `warning_guard_profile`（manifest §1.12）。

---

## 9. Related docs (quick index)

| 主題 | 文件 |
|------|------|
| **Supporting rails vs 主線 mapping** | **`docs/TABULAR_MVP_NARRATIVE_MAPPING.md`** — GA/WC-PRE/Round-2/payment/K-2/Graph 等噪声收斂 |
| 對外 Product Spec | `docs/PRODUCT_TABULAR_CLEANING.md` |
| 對內 Runbook | `docs/C2-P2_RUNBOOK.md` |
| L1 trace + rerun | `docs/mvp-standard-trace-path.md` |
| E2E DoD | `docs/MVP_CASE_E2E_DoD_v0.1.md` |
| Skill Cards | `docs/skill-cards-v1.md` |
| Tool catalog（人讀） | `docs/tabular-tool-catalog-v1.md` |
| Release checklist | `docs/tabular-mvp-release-checklist.md` |
| **Automation manifest** | `docs/tabular-cleaning-automation-manifest-v1.md`（§1.12 warning guard · §1.13 tool-executor） |
| **Automation control plane** | `docs/tabular-cleaning-control-plane-v1.md` · CLI `scripts/manage_tabular_automation_state.py` |
| **Internal notify hook（占位）** | `scripts/tabular_internal_notify_lib.py` · manifest §1.11 · log `cases/<case>/internal_notify_log.json` |
| **Unified automation driver** | `scripts/run_tabular_automation.py` · log `cases/<case>/reports/automation_run_log.json` |
| **Mainline E2E verification** | `docs/tabular-mainline-e2e-verification-v1.md` · report `docs/tabular-mainline-e2e-verification-report-v1.md` |
| **Mainline progress update** | **`docs/tabular-mainline-progress-update-2026-07-22.md`**（最新快照）· 模板 `docs/tabular-mainline-progress-template.md` |
| **Delivery approval CLI** | `scripts/approve_tabular_delivery.py` · `cases/<case>/delivery_approval.json` |
| Case 目錄約定 | `cases/README.md` |
| Workflow 索引 | `04_Workflows/WORKFLOW_INDEX.md` §1.5+ |

---

## 10. Version & non-claims

| 項 | 狀態 |
|----|------|
| 本檔 | v1 · 2026-06-27 · Tabular MVP SSOT Scribe |
| Prod-ready / closure | **未宣稱** |
| Batch 1 governance | **未改動** · 見 Progress 末尾 YAML |
| Dashboard Phase% | **06-27 敘事已同步** · SSOT 見 `docs/WAVE_PROGRESS_DASHBOARD.md` §Phase 完成度表 |

### 10.1 Phase 完成度 vs Tabular 子域（Gauge 區分 · 2026-07-22 校對）

**全局 Phase 完成度**仍依 Dashboard SSOT（current = 2026-07-13 · 2026-07-22 已重新校對、無新 Δ）——見 `docs/WAVE_PROGRESS_DASHBOARD.md` §Phase Completion Gauge。

**Tabular 主線子域（C2-P2 scope）**：

> **Phase 2/3/6/8/10 (Tabular low-risk cleaning subline): functionally complete for scope C2-P2.**

| Phase | Tabular 子域完工项（C2-P2） | 全局 Phase%（07-22 校對） |
|-------|----------------------------|----------------------|
| **P2** | 3 profiles · case registry · intake 解析 | **66%** |
| **P3** | automation run log · ops summary CLI · E2E report | **82%** (prev 95%, −13%) |
| **P6** | regression smoke · mainline E2E · 三案验证 | **83%** |
| **P8** | delivery approve · bundle · HITL CP-A/B | **100%** |
| **P10** | control plane · unified driver · retry/DLQ · warning guard | **37%** |

**Tabular low-risk cleaning subline 在 Phase 2/3/6/8/10 的 C2-P2 范围内已功能完備。** 分项：

- **P2**：`phase_demo_v1` · `sampleco_order_profile` · `generic_low_risk_profile` · `cases/index.json`
- **P3**：`automation_run_log.json` · `tabular_ops_summary.py` · `tabular-mainline-e2e-verification-report-v1.md`
- **P6**：`run_demo_phase_regression_smoke.py` · checklist · E2E PASS（`demo_phase` · `sampleco/2026-0001` · `internal/generic-low-risk`）
- **P8**：`run_hitl_checkpoint_cli.py` · `approve_tabular_delivery.py` · bundle · `delivery_ready` 策略
- **P10**：`manage_tabular_automation_state.py` · `run_tabular_automation.py` · retry/DLQ（state/run log/dlq 档/测试）· warning guard（manifest §1.12）

**完工范围**：profile + control plane + driver + HITL + approve + retry/DLQ + guard + ops summary + E2E。**≠** 全局 Phase% 上调 · **≠** prod / mandatory CI / closure。

---

*Tabular MVP SSOT v1 · doc-only · supporting rails ≠ primary product outcome*

> Tabular 主線已完成一次可重複的 E2E 驗證；後續變更應以此驗證流程作為回歸基準。（見 `docs/tabular-mainline-e2e-verification-v1.md` · 2026-06-27）  
> **最新進度快照**：`docs/tabular-mainline-progress-update-2026-07-22.md` · 後續更新沿用 `docs/tabular-mainline-progress-template.md`
