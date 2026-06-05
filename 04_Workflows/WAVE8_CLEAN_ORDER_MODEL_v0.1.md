# Wave 8 – CLEAN Order & Milestone 資料模型（v0.1）

> **票號**：`W8-ORDER-MODEL`  
> **性質**：spec / data model（**不涉真金流**，僅資料結構設計）  
> **受眾**：CS、運營、財務預開票、尚書省  
> **前置**：`WAVE6_CLEAN_PRODUCT_MATRIX_v0.1.md`、`WAVE7_CLEAN_ORCH_STATE_MACHINE_v0.1.md`、`WAVE7_CLEAN_ORCH_TASK_MODEL_v0.1.md`、`WAVE8_OVERVIEW_v0.1.md`  
> **狀態**：**DRAFT-v0.1**

---

## 0. 文件目的

Wave 8 將進入「財務開票」與「客戶橋接」階段，需要一套**與 orchestrator 技術狀態分層、但可映射對齊**的 Order（訂單）資料模型，用於：

- CS 與客戶溝通進度（商務視角）
- 里程碑觸發通知與計費錨點（財務預備）
- 支持「半自動結算」所需的歷史追溯（本稿僅資料模型，金流邏輯另票）

**與 orchestrator 狀態機的關係**：
- `orch_status`（PENDING / RUNNING / DONE / FAILED...）是**技術執行層**狀態
- `order_status`（DRAFT / CONFIRMED / IN_PROGRESS...）是**商務合約層**狀態
- 一個 Order 可包含多個 job（多批次），milestones 跨 job 聚合

---

## 1. Order 狀態機（商務層）

### 1.1 主狀態定義

| 狀態 | 語義 | 終態？ | 技術層對應 |
|------|------|--------|------------|
| **DRAFT** | 訂單草稿：客戶需求收集、SKU 選型、報價確認中 | 否 | 尚無 job 或僅有預覽 demo job |
| **CONFIRMED** | 訂單確認：客戶確認 SKU、規模、里程碑計劃，尚未開工 | 否 | `orch_status=PENDING` 或等待 intake |
| **IN_PROGRESS** | 執行中：至少一個批次進入技術執行段（S1–S5） | 否 | `orch_status=RUNNING` / `BLOCKED` |
| **DELIVERED** | 交付完成：所有里程碑達成，報告已生成，待客戶驗收 | 否* | `orch_status=DONE` + S5 finalize |
| **CLOSED** | 結單：客戶驗收通過或自動結單（TTL），可計費 | **是** | 商務確認完成 |
| **CANCELLED** | 取消：客戶主動取消或我方無法履約 | **是** | 對應 `FAILED` / `NEED-HUMAN` 棄單 |

\* `DELIVERED` 為「技術完工」但商務尚未結案，預留客戶異議/重跑窗口。

### 1.2 狀態轉移圖（文字版）

```text
                              ┌─────────────────────────────┐
                              │      [客戶需求輸入]          │
                              │   intake_request / 報價單   │
                              └──────────────┬──────────────┘
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │     DRAFT       │
                                    │   選型/報價確認   │
                                    └────────┬────────┘
                                             │ 客戶確認
                                             ▼
                                    ┌─────────────────┐
                                    │   CONFIRMED     │
                                    │  合約生效/待開工  │
                                    └────────┬────────┘
                                             │ intake accept
                                             ▼
                                    ┌─────────────────┐
              ┌────────────────────│   IN_PROGRESS   │───────────────────┐
              │                    │   多批次執行中    │                   │
              │                    └────────┬────────┘                   │
              │                             │                            │
   部分失敗可  │              ┌──────────────┼──────────────┐          │  全部取消
   降級交付    │              ▼              ▼              ▼          │
              │       ┌──────────┐   ┌──────────┐   ┌──────────┐     │
              │       │M1 樣本   │   │M2 整批   │   │M3 交付   │     │
              │       │demo 完成 │   │清洗完成  │   │復核完成  │     │
              │       └────┬─────┘   └────┬─────┘   └────┬─────┘     │
              │            │              │              │            │
              │            └──────────────┴──────────────┘            │
              │                             │                        │
              │              全部里程碑達成   │                        │
              │                             ▼                        │
              │                    ┌─────────────────┐                 │
              │                    │    DELIVERED    │◀────────────────┘
              │                    │   報告已交付     │
              │                    │   待客戶驗收     │
              │                    └────────┬────────┘
              │                             │
      ┌───────┴────────┐                   │ 客戶驗收通過 / TTL 到期
      │                │                   ▼
      │   客戶異議      │          ┌─────────────────┐
      │  (重跑/降級)    │          │     CLOSED      │
      │                │          │     結單可計費   │
      └───────┬────────┘          └─────────────────┘
              │
              ▼
      ┌─────────────────┐
      │    CANCELLED    │
      │  取消/棄單不計費  │
      └─────────────────┘
```

### 1.3 狀態轉移規則

| 轉移 | 觸發條件 | 誰可執行 |
|------|----------|----------|
| DRAFT → CONFIRMED | 客戶書面/系統確認 SKU、報價、里程碑計劃 | CS / 客戶 |
| CONFIRMED → IN_PROGRESS | intake accept，首個 job 進入 `RUNNING` | 系統自動 |
| IN_PROGRESS → DELIVERED | 所有 milestone 達成（見 §2），最終報告生成 | 系統自動 |
| DELIVERED → CLOSED | 客戶驗收通過（手動確認）或自動 TTL 到期（建議 72h） | 客戶 / 系統 |
| DELIVERED → IN_PROGRESS | 客戶異議觸發重跑（rollback 到里程碑 2 或 3） | CS / 客戶 |
| 任意 → CANCELLED | 客戶主動取消（DRAFT/CONFIRMED 階段）或我方棄單（IN_PROGRESS 後 `FAILED` 不可恢復） | CS / 尚書省 |

---

## 2. 里程碑（Milestones）設計

### 2.1 三個核心里程碑

| 里程碑 ID | 名稱 | 一句話定義 |
|-----------|------|------------|
| **M1** | 樣本 Demo 完成 | S3 清洗完成 + M2 抽樣深檢通過（如有），客戶可預覽品質 |
| **M2** | 整批清洗完成 | 全部批次 S4 QA（M1+M2）通過，manifest 完整 |
| **M3** | 交付復核完成 | S5 報告生成 + 交付物 finalize，客戶可下載 |

### 2.2 里程碑詳細規格

#### M1 – 樣本 Demo 完成

| 屬性 | 內容 |
|------|------|
| **觸發條件** | `orch_status=DONE` + 至少一個 demo 批次 S3 完成 + M2 抽樣通過（如 SKU 含 M2） |
| **對應 Stage** | S3（執行清洗）+ S4 M2（抽樣深檢） |
| **可否計費** | ⚠️ **可計費（部分）**：僅對 demo 批次行數計費；或作為「預付款」錨點 |
| **失敗回退** | M2 P0 → 回退到 S3（重跑清洗）或 S2（修規則）；M2 僅 P1 → 帶 warning 繼續，CS 裁定 |
| **取消策略** | Demo 失敗可轉為 CANCELLED（不計費）或降級為 CLEAN-BASIC（重新報價） |

#### M2 – 整批清洗完成

| 屬性 | 內容 |
|------|------|
| **觸發條件** | 全部批次 `orch_status=DONE` + 所有 S4 QA（M1 全量 + M2 抽樣）通過 |
| **對應 Stage** | S4（QA M1+M2）完成 |
| **可否計費** | ✅ **可計費（主體）**：按 `accepted_units` 行數計費 |
| **失敗回退** | M1 P0 → 回退到 S3（manifest 已存可只重跑 S4/S5）；M2 P0 → 回退到 S3（數據問題）或 S2（規則問題） |
| **取消策略** | 整批失敗可部分交付（`completed_with_failures`）降價，或協商 CANCELLED |

#### M3 – 交付復核完成

| 屬性 | 內容 |
|------|------|
| **觸發條件** | S5 報告生成完成 + 交付物 finalize + `report.json` / `report.md` 可下載 |
| **對應 Stage** | S5（匯總與報告生成）完成 |
| **可否計費** | ✅ **可計費（尾款）**：確認交付完成，觸發尾款或全款結算 |
| **失敗回退** | Report build 失敗 → S5 重試（checkpoint manifest，不重算 S3）；Storage IO 失敗 → 重試至多 3 次 |
| **取消策略** | M3 失敗極少見（技術問題），通常阻塞修復；客戶拒收可進入異議流程（DELIVERED → IN_PROGRESS 重跑） |

### 2.3 里程碑狀態子欄位

每個 milestone 在 Order 中記錄：

```json
{
  "milestone_id": "M1",
  "status": "achieved | failed | pending | waived",
  "achieved_at": "2026-06-04T12:00:00Z",
  "trigger_job_id": "uuid-of-triggering-job",
  "billing_eligible": true,
  "billing_amount_hint": 1500.00,
  "currency": "TWD",
  "failure_context": {
    "failed_at": "2026-06-04T10:30:00Z",
    "error_category": "M2_P0",
    "rollback_target": "S3",
    "human_required": true
  }
}
```

---

## 3. CLEAN-BASIC / CLEAN-ENRICH 里程碑組合表

### 3.1 里程碑適用矩陣

| 里程碑 | CLEAN-BASIC | CLEAN-ENRICH | 說明 |
|--------|-------------|--------------|------|
| **M1 樣本 Demo** | ✅ 可選（建議 >10k 行啟用） | ✅ 建議啟用（enrich 品質需驗證） | BASIC 小批次可跳過 M1 |
| **M1.1 Demo 清洗完成** | ✅ S3 完成 | ✅ S3 完成 | 技術達成點 |
| **M1.2 Demo M2 通過** | ❌ 無 M2 | ✅ 抽樣深檢 | ENRICH 建議 M2 抽樣驗證 enrich 品質 |
| **M2 整批清洗完成** | ✅ M1 全量檢查 | ✅ M1 全量 + M2 抽樣 | ENRICH 需 M2 保證 enrich API 品質 |
| **M2.1 全量 manifest 通過** | ✅ M1 全量 | ✅ M1 全量 | 兩者皆需 |
| **M2.2 整批 M2 抽樣通過** | ❌ 不適用 | ✅ 分層抽樣 | ENRICH 大批次強烈建議 |
| **M3 交付復核** | ✅ S5 報告 | ✅ S5 報告 + enrich 指標 | ENRICH 報告含 enrich 統計 |

### 3.2 典型里程碑組合（推薦配置）

#### CLEAN-BASIC 小型批次（< 10k 行）

| 階段 | 里程碑 | 計費錨點 | 備註 |
|------|--------|----------|------|
| 開工 | — | 預付款（可選） | — |
| 完成 | M2 整批完成 | ✅ 全款 | 無 M1 Demo，一次性交付 |
| 交付 | M3 復核完成 | — | 觸發報告 |

**狀態流**：CONFIRMED → IN_PROGRESS → DELIVERED → CLOSED

#### CLEAN-BASIC 大型批次（≥ 10k 行）

| 階段 | 里程碑 | 計費錨點 | 備註 |
|------|--------|----------|------|
| 開工 | — | 預付款（建議 30%） | — |
| Demo | M1 樣本完成 | ✅ 階段款 | 前 1k 行品質確認 |
| 整批 | M2 整批完成 | ✅ 主體款（扣預付） | 剩餘行數 |
| 交付 | M3 復核完成 | ✅ 尾款（可合併） | 報告確認 |

**狀態流**：CONFIRMED → IN_PROGRESS →（M1 達成通知）→（M2 達成）→ DELIVERED → CLOSED

#### CLEAN-ENRICH 標準流程

| 階段 | 里程碑 | 計費錨點 | 備註 |
|------|--------|----------|------|
| 開工 | — | 預付款 30% | — |
| Demo | M1.1 Demo 清洗 | 階段款 20% | 技術驗證 |
| Demo QA | M1.2 Demo M2 | ✅ Demo 計費確認 | enrich 品質驗證 |
| 整批 | M2.1 全量 M1 | — | 全量檢查 |
| 抽樣 | M2.2 整批 M2 | ✅ 主體款 40% | enrich 深檢 |
| 交付 | M3 復核完成 | ✅ 尾款 10% | 報告 + enrich 指標 |

**狀態流**：CONFIRMED → IN_PROGRESS →（M1.1 → M1.2 達成）→（M2.1 → M2.2 達成）→ DELIVERED → CLOSED

#### CLEAN-ENRICH 簡化流程（信任客戶/緊急）

| 階段 | 里程碑 | 計費錨點 | 備註 |
|------|--------|----------|------|
| 開工 | — | 預付款 50% | — |
| 整批 | M2.1 全量 M1 | ✅ 尾款 50% | 跳過 M2 抽樣（風險由客戶承擔） |
| 交付 | M3 復核完成 | — | 報告標記「無 M2」|

**風險警告**：無 M2 抽樣時，enrich API 品質問題可能未發現，需在合約中明確免責。

---

## 4. 資料結構草稿

### 4.1 Order 主表（建議欄位）

```json
{
  "order_id": "ORD-20260604-001",
  "order_status": "IN_PROGRESS",
  "product_sku": "CLEAN-ENRICH",
  "client_ref": "client-acme-2026",
  "created_at": "2026-06-04T09:00:00Z",
  "confirmed_at": "2026-06-04T10:00:00Z",
  "delivered_at": null,
  "closed_at": null,
  "cancelled_at": null,
  
  "milestone_plan": ["M1.1", "M1.2", "M2.1", "M2.2", "M3"],
  "milestones_achieved": ["M1.1", "M1.2"],
  "milestones_pending": ["M2.1", "M2.2", "M3"],
  
  "jobs": [
    {"job_id": "uuid-1", "batch_tag": "demo", "orch_status": "DONE"},
    {"job_id": "uuid-2", "batch_tag": "batch-1", "orch_status": "RUNNING"},
    {"job_id": "uuid-3", "batch_tag": "batch-2", "orch_status": "PENDING"}
  ],
  
  "billing_plan": {
    "currency": "TWD",
    "total_estimate": 50000.00,
    "milestones": [
      {"milestone_id": "M1", "percent": 30, "trigger": "M1.2 achieved"},
      {"milestone_id": "M2", "percent": 60, "trigger": "M2.2 achieved"},
      {"milestone_id": "M3", "percent": 10, "trigger": "M3 achieved"}
    ]
  },
  
  "cancellation_reason": null,
  "rollback_history": []
}
```

### 4.2 Milestone 明細表（建議欄位）

```json
{
  "milestone_id": "M2.2",
  "order_id": "ORD-20260604-001",
  "display_name": "整批 M2 抽樣深檢通過",
  "status": "pending",
  
  "trigger_condition": {
    "orch_status": "DONE",
    "required_stages": ["S4"],
    "qa_requirements": ["M2_sample_passed"],
    "applies_to_batches": ["batch-1", "batch-2"]
  },
  
  "billing_node": {
    "eligible": true,
    "amount_percent": 40,
    "amount_fixed": null,
    "unit_based": false
  },
  
  "failure_handling": {
    "on_m2_p0": {
      "rollback_target": "S3",
      "retryable": true,
      "max_retries": 3,
      "human_escalation_after": 3
    },
    "on_m2_p1_only": {
      "action": "continue_with_warning",
      "cs_approval_required": true
    }
  },
  
  "achieved_snapshot": {
    "achieved_at": null,
    "trigger_job_id": null,
    "qa_summary": null,
    "accepted_units": 0,
    "rejected_units": 0
  }
}
```

---

## 5. 失敗與回退策略總表

| 失敗場景 | 當前里程碑 | 回退目標 | 是否可重試 | 計費影響 | 人為介入 |
|----------|------------|----------|------------|----------|----------|
| Demo M2 P0 | M1 | S3（重跑清洗）或 S2（修規則） | ✅ 是（同 job）| 不計費（未達成）| CS 裁定 |
| Demo M2 僅 P1 | M1 | 不回退，帶 warning 繼續 | — | ⚠️ 可協議降價 | CS 確認 |
| 整批 M1 P0 | M2 | S3（manifest 已存可只重跑 S4/S5） | ✅ 是（checkpoint）| 不計費（未達成）| 自動重試後人工 |
| 整批 M2 P0 | M2 | S3（數據問題）或 S2（規則問題） | ✅ 是 | 不計費（未達成）| 自動重試後人工 |
| 整批 M2 僅 P1 | M2 | 不回退，`pass_with_warnings` | — | ⚠️ 可協議降價 | CS 確認 |
| Report build 失敗 | M3 | S5 重試（checkpoint manifest） | ✅ 是（3 次）| 不影響（已達 M2）| 自動重試 |
| Storage IO 失敗 | M3 | S5 重試 | ✅ 是（3 次）| 不影響 | 自動重試 |
| 客戶異議（品質） | M3（已 DELIVERED）| IN_PROGRESS（重跑 M2 或 M3） | ✅ 是（新 job）| 協議處理 | CS/尚書省 |
| 客戶棄單 | 任意 | CANCELLED | ❌ 否 | 按達成里程碑結算 | 尚書省批准 |

---

## 6. 與 Orchestrator 狀態的映射參考

| Order 狀態 | orch_status 組合 | 里程碑狀態 |
|------------|------------------|------------|
| DRAFT | 無 job 或 job 僅為預覽 | — |
| CONFIRMED | `PENDING`（等待 intake） | — |
| IN_PROGRESS | `RUNNING` / `BLOCKED` / `NEED-HUMAN` | 里程碑進行中 |
| DELIVERED | `DONE`（全部批次） | M1–M3 全部達成 |
| CLOSED | `DONE`（保留） | 結案鎖定 |
| CANCELLED | `FAILED` / `NEED-HUMAN`（棄單） | 取消，記錄已達里程碑 |

---

## 7. 非目標（本稿 v0.1）

| 項 | 說明 |
|----|------|
| 金流實作 | 僅定義 `billing_eligible` 標記與金額 hint，實際支付閘道另票 |
| 發票格式 | 發票欄位、稅率、折讓單另票 |
| 多幣別匯率 | 僅標記 `currency`，匯率換算另票 |
| 退款邏輯 | 取消時退款比例計算另票 |
| 客戶自助 portal | 僅資料模型，UI 另票 |

---

## 8. 版本歷史

| 版本 | 日期 | 變更 |
|------|------|------|
| v0.1 | 2026-06-04 | 初始草稿：六態狀態機、三里程碑設計、BASIC/ENRICH 組合表、資料結構草稿 |

**下一版預期**：實際 PostgreSQL schema DDL、與 Wave 8 Invoice 子域對齊、里程碑達成的 webhook 事件定義。

---

*Wave 8 CLEAN Order & Milestone Model · `04_Workflows/WAVE8_CLEAN_ORDER_MODEL_v0.1.md`*
