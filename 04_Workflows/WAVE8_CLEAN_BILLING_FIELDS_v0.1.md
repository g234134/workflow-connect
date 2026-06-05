# Wave 8 – CLEAN Billing 欄位規格（v0.1）

> **票號**：`W8-BILLING-FIELDS`  
> **性質**：spec / data model（**不涉真金流閘道**，僅定義對帳與利潤分析所需欄位）  
> **受眾**：財務、CS、運營、產品  
> **前置**：`WAVE8_CLEAN_ORDER_MODEL_v0.1.md`（milestone 與計費錨點設計）  
> **狀態**：**DRAFT-v0.1**

---

## 0. 文件目的

Wave 8 進入「財務開票」預備階段，需要一套**與真金流閘道分離、但可對帳映射**的 Billing 資料模型，用於：

- 記錄報價、折扣、最終價格（支援對帳）
- 追蹤分期付款與里程碑對應（支援應收帳款管理）
- 估計工具成本與人力投入（支援利潤分析）

**與真金流的關係**：本稿僅定義「該記錄什麼」，實際支付閘道、發票開立、金流狀態回寫，另票實作。

---

## 1. Order 層級 Billing 欄位

### 1.1 價格三要素

| 欄位 | 類型 | 說明 | 必填 |
|------|------|------|------|
| `list_price` | decimal | 定價（未折扣前） | ✅ |
| `discount` | decimal | 折扣金額（≥ 0） | 預設 0 |
| `final_price` | decimal | 最終價格 = list_price - discount | ✅（系統計算） |
| `currency` | string(3) | 幣別代碼（ISO 4217，如 TWD、USD） | 預設 TWD |

**約束**：
- `final_price` = `list_price` - `discount`（server-side 驗證）
- `discount` ≤ `list_price`（不允許負價格）

### 1.2 計費方案（Billing Plan）

| 欄位 | 類型 | 說明 | 選項 |
|------|------|------|------|
| `billing_plan.type` | enum | 付款方式 | `ONE_TIME`（一次付清）、`INSTALLMENT`（分期） |
| `billing_plan.installments` | int | 分期期數 | `type=INSTALLMENT` 時必填，≥ 2 |
| `billing_plan.milestone_triggered` | bool | 是否按里程碑觸發付款 | 預設 true（Wave 8 標準模式） |

### 1.3 計費事件陣列（Billing Events）

每個 `billing_event` 對應一個里程碑達成點，記錄「應收款」資訊：

```json
{
  "billing_events": [
    {
      "event_id": "BEV-ORD001-M1",
      "milestone_id": "M1",
      "event_type": "MILESTONE",
      "sequence": 1,
      
      "planned_amount": 15000.00,
      "planned_percent": 30,
      "billable_amount": 15000.00,
      
      "status": "PENDING",
      "achieved_at": null,
      "billed_at": null,
      
      "description": "Demo 樣本完成（M1.2 達成）"
    }
  ]
}
```

#### Billing Event 欄位詳細規格

| 欄位 | 類型 | 說明 |
|------|------|------|
| `event_id` | string | 唯一識別碼（建議格式：`BEV-{order_id}-{milestone_id}`） |
| `milestone_id` | string | 對應里程碑（M1/M2/M3 或 M1.1/M1.2/M2.1/M2.2） |
| `event_type` | enum | 觸發類型：`MILESTONE`（里程碑）、`FIXED_DATE`（固定日期）、`MANUAL`（手動） |
| `sequence` | int | 付款順序（第幾期） |
| `planned_amount` | decimal | 預計金額（基於報價計算） |
| `planned_percent` | int | 佔總價百分比 |
| `billable_amount` | decimal | 實際可計費金額（考量取消/降級後調整） |
| `status` | enum | `PENDING`（待達成）、`ACHIEVED`（已達成未開票）、`BILLED`（已開票）、`PAID`（已收款）、`WAIVED`（豁免）、`CANCELLED`（取消） |
| `achieved_at` | datetime | 里程碑達成時間 |
| `billed_at` | datetime | 開票時間（由財務系統回寫） |
| `description` | string | 人類可讀說明 |

---

## 2. Milestone 層級計費欄位

每個 milestone 在 Order 的 `milestones` 陣列中，增加計費明細子物件：

```json
{
  "milestone_id": "M2.2",
  "status": "achieved",
  "achieved_at": "2026-06-04T14:30:00Z",
  
  "billing": {
    "billable_amount": 20000.00,
    "currency": "TWD",
    "billed_at": null,
    "payment_status": "PENDING",
    
    "adjustment_reason": null,
    "original_estimate": 25000.00
  }
}
```

### 2.1 Milestone Billing 欄位規格

| 欄位 | 類型 | 說明 |
|------|------|------|
| `billing.billable_amount` | decimal | 此里程碑可計費金額 |
| `billing.currency` | string(3) | 幣別 |
| `billing.billed_at` | datetime | 實際開票時間（財務回寫） |
| `billing.payment_status` | enum | `PENDING`（未處理）、`INVOICED`（已開票）、`PAID`（已付款）、`PARTIAL_PAID`（部分付款）、`DISPUTED`（爭議中）、`WRITTEN_OFF`（呆帳） |
| `billing.adjustment_reason` | string | 金額調整原因（如降級交付、協議折扣） |
| `billing.original_estimate` | decimal | 原始報價金額（調整前） |

---

## 3. 成本側欄位（利潤分析用）

### 3.1 Order 層級成本估計

| 欄位 | 類型 | 說明 |
|------|------|------|
| `cost_estimate.tool_cost_estimate` | decimal | 工具成本預估（含 token / compute / 外部 API） |
| `cost_estimate.human_hours_estimate` | decimal | 預估人力工時（小時） |
| `cost_estimate.human_hour_rate` | decimal | 人力時薪參考（用於計算機會成本） |
| `cost_estimate.total_cost_estimate` | decimal | 總成本預估 = tool_cost + (human_hours × hour_rate) |

### 3.2 成本明細結構

```json
{
  "cost_estimate": {
    "tool_cost_estimate": 2500.00,
    "tool_cost_breakdown": {
      "token_cost": 800.00,
      "compute_cost": 1200.00,
      "external_api_cost": 500.00,
      "note": "基於預估 50k tokens + 2hr compute + enrich API calls"
    },
    
    "human_hours_estimate": 4.5,
    "human_hour_rate": 1500.00,
    "human_cost_estimate": 6750.00,
    
    "total_cost_estimate": 9250.00,
    "margin_estimate": 5750.00,
    "margin_percent": 38.3
  }
}
```

### 3.3 Tool Cost 明細欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| `tool_cost_breakdown.token_cost` | decimal | LLM token 費用預估 |
| `tool_cost_breakdown.compute_cost` | decimal | 運算資源費用（雲端實例） |
| `tool_cost_breakdown.external_api_cost` | decimal | 外部 API 調用費用（如 enrich API） |
| `tool_cost_breakdown.storage_cost` | decimal | 儲存費用預估 |
| `tool_cost_breakdown.note` | string | 計算依據說明 |

---

## 4. 完整範例：BASIC 訂單 Billing 記錄

以下為一個 `CLEAN-BASIC` 小型批次（< 10k 行）訂單的完整 billing 記錄範例：

```json
{
  "order_id": "ORD-20260604-B001",
  "order_status": "DELIVERED",
  "product_sku": "CLEAN-BASIC",
  
  "billing": {
    "list_price": 10000.00,
    "discount": 1000.00,
    "final_price": 9000.00,
    "currency": "TWD",
    
    "billing_plan": {
      "type": "ONE_TIME",
      "installments": 1,
      "milestone_triggered": true
    }
  },
  
  "billing_events": [
    {
      "event_id": "BEV-B001-M2",
      "milestone_id": "M2",
      "event_type": "MILESTONE",
      "sequence": 1,
      "planned_amount": 9000.00,
      "planned_percent": 100,
      "billable_amount": 9000.00,
      "status": "ACHIEVED",
      "achieved_at": "2026-06-04T16:00:00Z",
      "billed_at": null,
      "description": "整批清洗完成（M2）- 全款計費"
    }
  ],
  
  "milestones": [
    {
      "milestone_id": "M2",
      "status": "achieved",
      "achieved_at": "2026-06-04T16:00:00Z",
      "billing": {
        "billable_amount": 9000.00,
        "currency": "TWD",
        "billed_at": null,
        "payment_status": "PENDING",
        "adjustment_reason": null,
        "original_estimate": 10000.00
      }
    },
    {
      "milestone_id": "M3",
      "status": "achieved",
      "achieved_at": "2026-06-04T17:30:00Z",
      "billing": {
        "billable_amount": 0.00,
        "currency": "TWD",
        "billed_at": null,
        "payment_status": "NA",
        "adjustment_reason": "BASIC 訂單 M3 不計費（已含於 M2）",
        "original_estimate": 0.00
      }
    }
  ],
  
  "cost_estimate": {
    "tool_cost_estimate": 800.00,
    "tool_cost_breakdown": {
      "token_cost": 300.00,
      "compute_cost": 400.00,
      "external_api_cost": 0.00,
      "storage_cost": 100.00,
      "note": "BASIC: 10k 行 × 預估 30 tokens/row + 30min compute"
    },
    "human_hours_estimate": 1.0,
    "human_hour_rate": 1500.00,
    "human_cost_estimate": 1500.00,
    "total_cost_estimate": 2300.00,
    "margin_estimate": 6700.00,
    "margin_percent": 74.4
  },
  
  "financial_summary": {
    "revenue": 9000.00,
    "estimated_cost": 2300.00,
    "estimated_margin": 6700.00,
    "actual_cost_tracked": false,
    "actual_cost_note": "Wave 8 僅預估，實際成本追蹤另票"
  }
}
```

---

## 5. ENRICH 訂單分期範例（對照）

`CLEAN-ENRICH` 標準流程（含 M1 Demo）的分期 billing_events 配置：

```json
{
  "order_id": "ORD-20260604-E001",
  "billing": {
    "list_price": 50000.00,
    "discount": 0.00,
    "final_price": 50000.00,
    "currency": "TWD",
    "billing_plan": {
      "type": "INSTALLMENT",
      "installments": 3,
      "milestone_triggered": true
    }
  },
  
  "billing_events": [
    {
      "event_id": "BEV-E001-DEPOSIT",
      "milestone_id": null,
      "event_type": "FIXED_DATE",
      "sequence": 0,
      "planned_amount": 15000.00,
      "planned_percent": 30,
      "billable_amount": 15000.00,
      "status": "PAID",
      "achieved_at": "2026-06-04T09:00:00Z",
      "billed_at": "2026-06-04T09:30:00Z",
      "description": "開工預付款（CONFIRMED 時收取）"
    },
    {
      "event_id": "BEV-E001-M1",
      "milestone_id": "M1.2",
      "event_type": "MILESTONE",
      "sequence": 1,
      "planned_amount": 10000.00,
      "planned_percent": 20,
      "billable_amount": 10000.00,
      "status": "ACHIEVED",
      "achieved_at": "2026-06-04T12:00:00Z",
      "billed_at": null,
      "description": "Demo 完成計費（M1.2 達成）"
    },
    {
      "event_id": "BEV-E001-M2",
      "milestone_id": "M2.2",
      "event_type": "MILESTONE",
      "sequence": 2,
      "planned_amount": 20000.00,
      "planned_percent": 40,
      "billable_amount": 20000.00,
      "status": "PENDING",
      "achieved_at": null,
      "billed_at": null,
      "description": "整批 M2 抽樣通過（M2.2 達成）"
    },
    {
      "event_id": "BEV-E001-M3",
      "milestone_id": "M3",
      "event_type": "MILESTONE",
      "sequence": 3,
      "planned_amount": 5000.00,
      "planned_percent": 10,
      "billable_amount": 5000.00,
      "status": "PENDING",
      "achieved_at": null,
      "billed_at": null,
      "description": "交付復核完成（M3 達成）- 尾款"
    }
  ]
}
```

---

## 6. 欄位與現有模型的對齊

### 6.1 與 WAVE8_CLEAN_ORDER_MODEL_v0.1 的對應

| 本稿欄位 | 來源模型欄位 | 說明 |
|----------|--------------|------|
| `billing_events[].milestone_id` | `milestone_plan[]` | 對應 milestone 計費錨點 |
| `billing_events[].planned_percent` | `billing_plan.milestones[].percent` | 繼承報價時的百分比配置 |
| `milestones[].billing.*` | `milestone.billing_node` + `billing_eligible` | 擴展原有 billing 標記為完整欄位組 |

### 6.2 與 Orchestrator 狀態的關係

- `billing_events[].achieved_at` ← 當 `milestone.status` 變為 `achieved` 時自動填入
- `billing_events[].status` 流轉：`PENDING` → `ACHIEVED`（里程碑達成）→ `BILLED`（財務開票）→ `PAID`（金流回寫）

---

## 7. 非目標（本稿 v0.1）

| 項 | 說明 |
|----|------|
| 支付閘道整合 | 串接綠界、Stripe 等金流，另票實作 |
| 發票開立 API | 開立電子發票、上傳財政部，另票實作 |
| 退款/折讓 | 退款邏輯、折讓單流程，另票實作 |
| 實際成本追蹤 | 真實 token 用量、compute 成本回寫，Wave 9+ 規劃 |
| 多幣別匯率 | 即時匯率換算、外幣轉換，另票實作 |

---

## 8. 版本歷史

| 版本 | 日期 | 變更 |
|------|------|------|
| v0.1 | 2026-06-04 | 初始草稿：價格三要素、billing_plan、billing_events、milestone billing、成本估計欄位、BASIC/ENRICH 範例 |

**下一版預期**：實際 PostgreSQL schema DDL、與金流閘道 API 對接欄位、實際成本追蹤機制。

---

*Wave 8 CLEAN Billing Fields · `04_Workflows/WAVE8_CLEAN_BILLING_FIELDS_v0.1.md`*
