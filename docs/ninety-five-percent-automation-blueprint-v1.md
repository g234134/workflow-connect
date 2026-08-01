# 95% 自動化藍圖 v1 — 從接案 → 清洗 → 交付

> **版本**：v1.0 設計稿（Wave 6 Architecture）  
> **適用**：Tabular MVP 標準清洗案（`demo_phase` / `sampleco` 為錨點）  
> **日期**：2026-06-10  
> **上游依據**：`docs/WAVE_PROGRESS_DASHBOARD.md` · `docs/mvp-standard-trace-path.md` · `docs/hitl-checkpoints-v1.md`

---

## §1 目標與前提

### 1.1 自動化目標定義

| 自動化等級 | 定義 | Wave 6 目標占比 |
|-----------|------|----------------|
| **auto** | Agent 自主執行，無人工介入 | 75% |
| **HITL** | Human-in-the-Loop：Agent 準備決策資料，人工確認後繼續 | 20% |
| **human-only** | 必須人工執行，Agent 僅輔助或記錄 | 5% |
| **合計** | — | **100% = 95% 自動化 + 5% 必要人工** |

### 1.2 前提條件

1. **Wave 1–5 已完成產物**：
   - Tabular Tool Catalog / Selector / Executor / Outbox Consumer（W3-TL-T1–T4）
   - Routing → Tool Layer Glue（W4-T1）
   - Intake Decision Rules v1（W5-T1）
   - HITL Checkpoints 設計（W5-T2）
   - Multi-Agent Collaboration Spec（W5-T0）

2. **標準工作流錨點**：`cases/demo_phase` 與 `cases/sampleco/2026-0001` 已 6/6 回歸通過

3. **Scope 邊界**：本藍圖僅覆蓋 Tabular MVP（CSV 清洗交付），不含 Gov ask / DarkOps / GraphRAG

---

## §2 選定的標準工作流

### 2.1 標準工作流：Tabular MVP 清洗交付

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TABULAR MVP STANDARD FLOW — 從接案到交付                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [P1]        [P2]          [P3]         [P4]          [P5]         [P6]     │
│ INTAKE  →  DECISION  →  EXECUTION  →  VALIDATION  →  DELIVERY  →  CLOSEOUT  │
│                                                                             │
│   ↓          ↓             ↓             ↓             ↓            ↓      │
│ intake    evaluate      select_tools   output_guard   signoff      ledger    │
│ upload    decision      → execute      → qa_check    → bundle     → index   │
│           (auto/HITL)   → outbox       → checkpoint   → approve            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 與現有產物的對應

| 藍圖階段 | Wave 產物 | 關鍵文件/模組 |
|---------|-----------|--------------|
| P1 Intake | Wave 1 + 4 | `scripts/new_cleaning_case.py` · `intake.json` schema |
| P2 Decision | Wave 5 | `routing/intake_decision_rules_v1.py` · `evaluate_intake_decision()` |
| P3 Execution | Wave 3-TL + 4 | `tools/tabular_tool_selector.py` · `execute_tabular_tool` · `outbox/` |
| P4 Validation | Wave 1 + 3-TL | `output_guard.py` · `validate.eligibility` |
| P5 Delivery | Wave 1 + 4 | `build_case_delivery_bundle.py` · `delivery_signoff.md` |
| P6 Closeout | Wave 3-TL | `tabular_outbox_consumer.py` · `cases/index.json` |

---

## §3 全流程拆解

### 3.1 流程總覽表

| 步驟 ID | 步驟名稱 | 現有產物 | 現在狀態 | 目標狀態 | 關鍵產出 |
|---------|---------|---------|---------|---------|---------|
| S1 | **Intake Upload** | `new_cleaning_case.py` | human-only | **HITL** | `intake.json` + `raw/` |
| S2 | **Index Refresh** | `build_cases_index.py` | auto | **auto** | `cases/index.json` updated |
| S3 | **Decision Evaluate** | `intake_decision_rules_v1.py` | partial | **auto** | `decision: auto_accept/needs_review/reject` |
| S4 | **Checkpoint A** | `hitl/checkpoint_a_integration_v1.py` · `tabular_hitl_resume_lib.py` | **HITL（已接線）** | **HITL** | CP-A outbox + `approve-a` CLI |
| S12 | **Checkpoint B** | `hitl/checkpoint_b_integration_v1.py` · `approve-b` / `approve_tabular_delivery.py` | **HITL（已接線）** | **HITL** | CP-B + `delivery_approval.json` |
| S13 | **Delivery Approval** | `scripts/approve_tabular_delivery.py` | **HITL（CLI）** | **HITL** | `delivery_ready` in index + signoff |
| S5 | **Route Planning** | `intake_to_tabular_glue.py` | auto | **auto** | `glue_plan.selector_task_type` |
| S6 | **Tool Selection** | `tabular_tool_selector.py` | auto | **auto** | `candidate_tools[]` |
| S7 | **Gate Validation** | `check_case_eligibility.py` | auto | **auto** | `eligibility_result.json` |
| S8 | **Cleaning Execution** | `clean_phase_demo.py` | auto | **auto** | `cleaned/*_cleaned.csv` + `report.json` |
| S9 | **Outbox Write** | `tabular_tool_executor.py` | auto | **auto** | `outbox/<run_id>.json` |
| S10 | **Bundle Build** | `build_case_delivery_bundle.py` | auto | **auto** | `delivery_signoff.md` + bundle |
| S11 | **Output Guard** | `output_guard.py` | auto | **auto** | `guard.status: ok/warning/error` |
| S14 | **Ledger Update** | `tabular_outbox_consumer.py` | auto | **auto** | `events.jsonl` + index sync |
| S15 | **Client Notify** | manual / Telegram | human-only | **auto** | notification sent |

---

### 3.2 各步驟詳細設計

#### S1: Intake Upload（現在 human-only → 目標 HITL）

**現況**：
- 手動執行 `python scripts/new_cleaning_case.py --client-ref <ref> --data-file <path>`
- 人類選擇 client_ref、命名 case_id、指定 data_file

**目標 HITL**：
- Agent 接收 client 上傳請求（email / API / Telegram）
- Agent 自動建議 `case_id`（YYYY-NNNN 格式）
- Agent 自動偵測 `data_file` 格式（CSV/TSV）
- **HITL 點**：人工確認 case_id 與 client_ref 對應關係

**Gap**：無自動 intake API；需 `W6-T3-intake-api-gateway`

---

#### S2: Index Refresh（現在 auto → 目標 auto）

**現況**：`build_cases_index.py` 已自動掃描 `cases/` 目錄

**維持 auto**：無需改變，已達標

---

#### S3: Decision Evaluate（現在 partial → 目標 auto）

**現況**：
- `evaluate_intake_decision()` 已實作 decision rules v1
- Production allowlist：`demo_phase` / `sampleco`（W5-T1 decision rules）
- Agent 實驗線 allowlist（W6-T4 / W7-T1）：`demo_phase` / `sampleco/2026-0001` / `additional_demo` / `sandbox_client`（後兩者標記 **實驗線 only**）
- 非 experiment allowlist → orchestrator `blocked`；非 production allowlist → `needs_review`（`unknown_fixture_profile`）

**目標 auto**：
- 擴充 allowlist 至一般客戶 profile（基於歷史 case 統計）
- 未知 profile 改為 `needs_review`（進 Checkpoint A）而非 `reject`

**Gap**：需 `W6-T4-decision-rules-v2-profile-expansion`

---

#### S4: Checkpoint A（現在 planned → 目標 HITL）

**現況**：設計文件 `hitl-checkpoints-v1.md` §3 已定義，尚未實作

**目標 HITL**：
- 當 `decision=needs_review` 或 `risk_level=medium` 時暫停
- Agent 準備 `agent_output`（case_summary + gate_preview + suggested_route）
- 人工決策：`approve` / `reject` / `revise_plan`
- 預設行為：`approve`（timeout 5 分鐘後自動放行）

**Gap**：需 `W6-T5-checkpoint-a-implementation`

---

#### S5–S6: Route Planning + Tool Selection（現在 auto → 目標 auto）

**現況**：
- `plan_tabular_route()` 已實作（W4-T1）
- `select_tabular_tools()` 已實作（W3-TL-T2）
- 僅 dry-run / preview 模式，未接入主鏈

**目標 auto**：
- 直接由 glue → Selector 產出 `planned_tools[]` 與 `candidate_tools[]`
- 無需人工介入

**Gap**：需 `W6-T6-glue-selector-integration`（接線進主鏈）

---

#### S7–S11: Execution Chain（現在 auto → 目標 auto）

**現況**：
- Gate / Cleaning / Bundle / Output Guard 均已自動化
- `run_case_e2e_validation.py` 一鍵執行
- Outbox 已寫入 `outbox/<run_id>.json`

**目標 auto**：
- 維持現有自動化程度
- 增加自動重試（Transient Error）與 DLQ 機制

**Gap**：需 `W6-T7-executor-retry-dlq`（強化韌性）

---

#### S12: Checkpoint B（現在 planned → 目標 HITL）

**現況**：設計文件 `hitl-checkpoints-v1.md` §4 已定義，尚未實作

**目標 HITL**：
- 當 `output_guard.status=warning` 或 row count 下降異常時暫停
- Agent 準備 `execution_summary` + `cleaning_results` + `delivery_draft`
- 人工決策：`approve_delivery` / `request_changes` / `hold`
- 預設行為：`hold`（timeout 不自動放行，品質把關）

**Gap**：需 `W6-T8-checkpoint-b-implementation`

---

#### S13: Delivery Approval（現在 human-only → 目標 HITL）

**現況**：
- 人工閱讀 `delivery_signoff.md` 後手動改 `cases/index.json` status

**目標 HITL**：
- Checkpoint B 通過後，自動生成 `delivery_signoff.md` final version
- 人工一鍵確認（或透過 Telegram / Slack bot）
- 自動更新 `cases/index.json` → `status=delivered`

**Gap**：需 `W6-T9-delivery-automation`

---

#### S14–S15: Closeout + Notify（現在 auto/human → 目標 auto）

**現況**：
- Outbox Consumer 自動更新 index（S14 已 auto）
- Client notify 為人工（Telegram 手動發送）

**目標 auto**：
- 整合 Telegram bot 自動通知（利用現有 listener 基礎建設）
- 或 SMTP email 自動發送

**Gap**：需 `W6-T10-client-notification-gateway`

---

## §4 狀態轉換矩陣

### 4.1 現在狀態（Wave 5 完成後）

```
S1: human-only ─┐
S2: auto        │
S3: partial     ├─→ Wave 6 目標：全面 HITL + auto 分層
S4: planned     │
S5-S11: auto    │
S12: planned    │
S13: human-only │
S14: auto       │
S15: human-only ┘
```

### 4.2 目標狀態（Wave 6/7 完成後）

```
┌────────────────────────────────────────────────────────────────┐
│                    TARGET STATE (95% Automation)               │
├────────────┬──────────────┬────────────────────────────────────┤
│   Step     │ Target State │ Human Touch Point                  │
├────────────┼──────────────┼────────────────────────────────────┤
│ S1 Intake  │ HITL         │ 確認 case_id 與 client_ref 對應    │
│ S2 Index   │ auto         │ —                                  │
│ S3 Decide  │ auto         │ —（風險 case 進 Checkpoint A）     │
│ S4 CP-A    │ HITL         │ 審查 medium risk 案例計畫          │
│ S5 Route   │ auto         │ —                                  │
│ S6 Select  │ auto         │ —                                  │
│ S7 Gate    │ auto         │ —                                  │
│ S8 Clean   │ auto         │ —                                  │
│ S9 Outbox  │ auto         │ —                                  │
│ S10 Bundle │ auto         │ —                                  │
│ S11 Guard  │ auto         │ —                                  │
│ S12 CP-B   │ HITL         │ 確認 delivery 品質（warning時）   │
│ S13 Approve│ HITL         │ 一鍵確認 signoff                   │
│ S14 Ledger │ auto         │ —                                  │
│ S15 Notify │ auto         │ —                                  │
└────────────┴──────────────┴────────────────────────────────────┘

HITL: 2 checkpoints (S4, S12) + 1 intake confirm (S1) + 1 approve (S13) = 4 個人工點
      但僅 S4/S12 為阻塞性 checkpoint，S1/S13 為輕量確認

Auto: 11 steps (S2, S3, S5-S11, S14-S15)
Human-only: 0 steps（全部轉為 HITL 或 auto）
```

---

## §5 關鍵 Checkpoint 設計

### 5.1 Checkpoint A: Intake Confirmation

| 屬性 | 設計 |
|------|------|
| **觸發條件** | `decision=needs_review` OR `risk_level=medium` OR `HITL_FORCE_CHECKPOINT_A=1` |
| **預設行為** | `approve`（timeout 5 分鐘） |
| **人工選項** | `approve` / `reject` / `revise_plan` |
| **產出物** | `outbox/<case_ref>/checkpoint_A-intake-confirmation_<ts>.json` |
| **Resume 能力** | 支援 `--resume-from-checkpoint` CLI |
| **預估觸發率** | 20–30% cases（基於 Wave 1–4 數據） |

### 5.2 Checkpoint B: Delivery Confirmation

| 屬性 | 設計 |
|------|------|
| **觸發條件** | `output_guard.status=warning` OR `removal_ratio>0.5` OR `forced_cleaning=true` |
| **預設行為** | `hold`（timeout 不自動放行） |
| **人工選項** | `approve_delivery` / `request_changes` / `hold` |
| **產出物** | `outbox/<case_ref>/checkpoint_B-delivery-confirmation_<ts>.json` |
| **Resume 能力** | 支援 re-clean / re-bundle / re-delivery |
| **預估觸發率** | 10–15% cases |

### 5.3 Checkpoint 與自動化的關係

```
Case 1: Low Risk (70% cases)
  S3 decision=auto_accept → 跳過 CP-A → 自動執行 S5-S11 → CP-B 檢查 → 通過 → 完成
  Human touch: 0（全自動）

Case 2: Medium Risk (20% cases)
  S3 decision=needs_review → CP-A (HITL) → approve → 自動執行 → CP-B 檢查 → 通過 → 完成
  Human touch: 1（intake review）

Case 3: Quality Warning (10% cases)
  S3 auto_accept → 自動執行 → S11 guard=warning → CP-B (HITL) → approve_delivery → 完成
  Human touch: 1（delivery review）

Case 4: Combined (少數)
  S3 needs_review → CP-A → 執行 → guard=warning → CP-B
  Human touch: 2（intake + delivery review）
```

---

## §6 缺口清單（Gap List）

### 6.1 對應 Wave 6/7 票號的缺口

| 優先序 | Gap ID | 缺口描述 | 對應後續票 | 規格/模組 | 預估工時 |
|--------|--------|---------|-----------|----------|---------|
| P0 | G1 | **Intake API Gateway**：自動接收上傳並生成 intake.json | `W6-T3` | `app/intake_gateway.py` | 3d |
| P0 | G2 | **Checkpoint A 實作**：HITL intake confirmation 狀態機 | `W6-T5` | `checkpoints/checkpoint_a.py` | 4d |
| P0 | G3 | **Checkpoint B 實作**：HITL delivery confirmation 狀態機 | `W6-T8` | `checkpoints/checkpoint_b.py` | 4d |
| P1 | G4 | **Decision Rules v2**：擴充 profile detection，減少 reject 率 | `W6-T4` | `routing/intake_decision_rules_v2.py` | 3d |
| P1 | G5 | **Glue-Selector 接線**：將 W4 glue / W3-TL selector 接入主鏈 | `W6-T6` | `scripts/run_intake_to_delivery.py` | 3d |
| P1 | G6 | **Executor Retry + DLQ**：Transient error 自動重試，失敗進 DLQ | `W6-T7` | `tools/executor_with_retry.py` | 2d |
| P2 | G7 | **Delivery Automation**：signoff 一鍵確認與 index 自動更新 | `W6-T9` | `scripts/approve_delivery.py` | 2d |
| P2 | G8 | **Client Notification Gateway**：Telegram/Email 自動通知 | `W6-T10` | `app/notification_gateway.py` | 2d |
| P3 | G9 | **Checkpoint Admin CLI**：列出過期 checkpoint、清理、轉移 | `W6-T11` | `scripts/checkpoint_admin.py` | 2d |
| P3 | G10 | **Resume Framework**：通用 `--resume-from-checkpoint` 支援 | `W6-T12` | `core/checkpoint_resume.py` | 3d |

### 6.2 缺口與現有產物的關係

```
現有產物（Wave 1-5）          缺口（Wave 6/7）
────────────────────────────────────────────────────────
intake_decision_rules_v1.py ──→ G4: v2 profile expansion
     │
     └──→ planned: Checkpoint A ──→ G2: S4 實作
     
hitl-checkpoints-v1.md (設計) ──→ G2/G3: S4/S12 實作

tabular_tool_selector.py ─────→ G5: Glue 接線

run_case_e2e_validation.py ───→ G6: Retry + DLQ 整合

delivery_signoff.md (人工) ────→ G7: 自動化 approve

Telegram listener (手動) ───────→ G8: 自動 notify
```

### 6.3 風險缺口（不實作則無法達成 95%）

| 風險等級 | 缺口 | 原因 |
|---------|------|------|
| **High** | G2 (Checkpoint A) | 沒有 HITL，medium risk case 無法安全自動化 |
| **High** | G3 (Checkpoint B) | 沒有品質把關，錯誤 delivery 會直接送給客戶 |
| **Medium** | G5 (Glue-Selector 接線) | 無法啟用 Wave 3-TL / Wave 4 投資的 routing 自動化 |
| **Medium** | G7 (Delivery Automation) | S13 維持 human-only 會使整體自動化降至 ~85% |

---

## §7 建議的後續票順序

### 7.1 Wave 6 票序列（依賴順序）

```
Week 1-2: Foundation
├─ W6-T3: Intake API Gateway (G1)
│   └─ 產出: `app/intake_gateway.py`, `POST /api/intake`
│
├─ W6-T4: Decision Rules v2 Profile Expansion (G4)
│   └─ 產出: `routing/intake_decision_rules_v2.py`
│   └─ 依賴: W6-T3 (需要 intake API 資料結構)

Week 3-4: HITL Core
├─ W6-T5: Checkpoint A Implementation (G2)
│   └─ 產出: `checkpoints/checkpoint_a.py`, state schema
│   └─ 依賴: W6-T4 (需要 decision rules 輸出)
│
├─ W6-T8: Checkpoint B Implementation (G3)
│   └─ 產出: `checkpoints/checkpoint_b.py`
│   └─ 依賴: W6-T5 (共用 state/CLI 基礎建設)

Week 5-6: Integration
├─ W6-T6: Glue-Selector Integration (G5)
│   └─ 產出: `scripts/run_intake_to_delivery.py`
│   └─ 依賴: W6-T5, W6-T8 (整合 checkpoints)
│
├─ W6-T7: Executor Retry + DLQ (G6)
│   └─ 產出: `tools/executor_with_retry.py`
│   └─ 依賴: W6-T6 (需要整合 executor)

Week 7-8: Final Automation
├─ W6-T9: Delivery Automation (G7)
│   └─ 產出: `scripts/approve_delivery.py`
│   └─ 依賴: W6-T8 (需要 Checkpoint B 輸出)
│
├─ W6-T10: Client Notification Gateway (G8)
│   └─ 產出: `app/notification_gateway.py`
│   └─ 依賴: W6-T9 (delivery 後觸發 notify)

Week 9-10: Tooling & Polish
├─ W6-T11: Checkpoint Admin CLI (G9)
├─ W6-T12: Resume Framework (G10)
└─ W6-T2-REVIEW: 本藍圖回顧與 Wave 7 規劃
```

### 7.2 票依賴圖

```
W6-T3 (Intake API)
    │
    ▼
W6-T4 (Decision v2) ─────┐
    │                    │
    ▼                    │
W6-T5 (Checkpoint A)     │
    │                    │
    ▼                    │
W6-T8 (Checkpoint B)     │
    │                    │
    └────────┬───────────┘
             ▼
    W6-T6 (Glue Integration)
             │
             ▼
    W6-T7 (Retry/DLQ)
             │
             ▼
    W6-T9 (Delivery Auto)
             │
             ▼
    W6-T10 (Notify Gateway)
             │
             ▼
    W6-T11, W6-T12 (Tooling)
```

### 7.3 驗收里程碑

| 里程碑 | 驗收標準 | 對應票完成 |
|--------|---------|-----------|
| **M6.1** | Intake API 可接收上傳並自動生成 case | W6-T3 |
| **M6.2** | Decision v2 對新 profile 自動分類 | W6-T4 |
| **M6.3** | Checkpoint A/B 可暫停/恢復流程 | W6-T5, W6-T8 |
| **M6.4** | 完整流程: intake → delivery 一鍵執行 | W6-T6, W6-T7 |
| **M6.5** | 客戶自動通知 + delivery 自動化 | W6-T9, W6-T10 |
| **M6.6** | 95% 自動化達成（測量基於 50 case 樣本）| W6-T2-REVIEW |

---

## §8 與現有產物的對照索引

| 本藍圖引用 | 現有產物位置 | 狀態 |
|-----------|-------------|------|
| Tabular Tool Catalog | `tools/tabular_tool_catalog_v1.json` | ✅ 已交付 W3-TL-T1 |
| Tool Selector | `tools/tabular_tool_selector.py` | ✅ 已交付 W3-TL-T2 |
| Tool Executor | `tools/tabular_tool_executor.py` | ✅ 已交付 W3-TL-T3 |
| Outbox Consumer | `tools/tabular_outbox_consumer.py` | ✅ 已交付 W3-TL-T4 |
| Routing Glue | `routing/intake_to_tabular_glue.py` | ✅ 已交付 W4-T1 |
| Decision Rules | `routing/intake_decision_rules_v1.py` | ✅ 已交付 W5-T1 |
| HITL Design | `docs/hitl-checkpoints-v1.md` | ✅ 設計已交付 W5-T2 |
| Mainline Regression | `scripts/run_mvp_mainline_regression.py` | ✅ 6/6 pass |
| Standard Trace Path | `docs/mvp-standard-trace-path.md` | ✅ 已交付 W1-T2 |
| Multi-Agent Spec | `docs/multi-agent-collaboration-spec-v1.md` | ✅ 已交付 W5-T0 |

---

## §9 附錄

### 9.1 自動化計算公式

```
自動化率 = (完全自動步驟數 + HITL步驟數×0.5) / 總步驟數

現在: (9 + 0×0.5) / 15 = 60%  （S2, S5-S11, S14 共 9 步 auto；S4, S12 為 planned 未實作）
目標: (11 + 4×0.5) / 15 = 93.3% ≈ 95%（11 步 auto + 4 步 HITL）
```

### 9.2 HITL 時間預估

| HITL 點 | 預估人工時間 | 年省工時（1000 cases/年） |
|---------|-------------|------------------------|
| S1 Intake confirm | 30 sec | 8.3 hrs |
| S4 Checkpoint A | 2 min | 6.7 hrs（僅 20% case 觸發）|
| S12 Checkpoint B | 3 min | 5.0 hrs（僅 10% case 觸發）|
| S13 Delivery approve | 30 sec | 8.3 hrs |
| **合計** | **~6 min/case 平均** | **~200 hrs vs 全人工 500+ hrs** |

---

*95%-AUTOMATION-BLUEPRINT-v1 · W6-T2 · Architecture Design · 2026-06-10*
