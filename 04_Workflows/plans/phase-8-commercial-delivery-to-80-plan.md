# Phase 8 商業化交付規劃 — 68% → 80%

> **性質**：Delivery Planner 規劃輸出  
> **日期**：2026-06-16  
> **模型**：Kimi K2.5  
> **本輪僅規劃，不改 code**

---

## 1. 現況總結 (68%)

Wave 6/7 已完成：
- ✅ Checkpoint A/B 人工閘門機制
- ✅ Resume Loop (fail-close 驗證)
- ✅ Notification Gateway (local file stub)
- ✅ HITL CLI 決策工具
- ✅ Sandbox bundle 路徑

**缺口**（阻止達到 80%）：
1. **無標準 delivery bundle schema** — 交付物結構未產品化
2. **Operator 體驗仍為 raw CLI** — 無 pending queue view、無 batch operations
3. **Notify 僅限本機** — 無法可靠觸發下游 webhook

---

## 2. 80% 最小交付形態定義

### 2.1 Delivery Bundle v1 Schema

```
case_delivery_bundle_v1/
├── manifest.json                 # bundle metadata + artifacts index
├── artifacts/
│   ├── eligibility_report.json
│   ├── cleaned_data.csv
│   └── summary_for_client.json   # 客戶可讀摘要 (新增)
├── audit/
│   ├── checkpoint_A_history.jsonl
│   ├── checkpoint_B_history.jsonl
│   └── notification_events.jsonl
└── signature.json                # integrity checksums
```

**Key Fields**:
- `manifest.schema_version`: "delivery_bundle_v1"
- `manifest.case_ref`, `task_type`, `created_at`
- `summary_for_client.deliverables`: 客戶友善的描述清單
- `signature.algorithm`: "sha256"

### 2.2 Operator Surface 最小集

| 功能 | CLI 形式 | 目的 |
|------|----------|------|
| Pending visibility | `list_pending_checkpoints.py --format table` | 統一視圖替代 `ls outbox/` |
| Checkpoint preview | `preview_checkpoint <path>` | 人工決策前看內容 |
| Resume convenience | `--resume-latest-approved` | 免手動找 path |
| Batch operations | `--batch-approve` (同 task_type) | 同質 cases 一次核准 |

### 2.3 Notify v1.5 (Webhook & Basic Reliability)

- Webhook HTTP dispatch (非 dry-run)
- Exponential backoff retry (max 3)
- File-based DLQ + manual replay CLI
- `delivery.bundle_ready` 觸發 client summary 通知

**Non-scope**: Email/Slack/Telegram, multi-tenant, SLA guarantee

---

## 3. Ticket 拆分明細

### P8-T1: Delivery Bundle Schema v1

| 欄位 | 內容 |
|------|------|
| **Goal** | 定義並實作標準化的 case delivery bundle 結構 |
| **Scope** | Bundle manifest JSON Schema; `summary_for_client.json` 規範; integrity signature; `build_case_delivery_bundle_v1()` 實作 |
| **Dependencies** | W7-T3 controlled_notify_experiment_v1 (client summary 內容) |
| **Acceptance Criteria** | [1] CLI 可產生 bundle; [2] manifest 通過 schema validation; [3] integrity_check() 驗證完整; [4] Bundle 規格書文件 |
| **Estimate** | 1–1.5 weeks |
| **Priority** | **P0** — 阻塞後續 notify 內容定義 |

### P8-T2: Operator Surface — Pending Visibility & Batch Operations

| 欄位 | 內容 |
|------|------|
| **Goal** | Operator 可統一查看並批次處理 pending checkpoints |
| **Scope** | **v1 delivered**: `scripts/list_operator_backlog_v1.py`（pending/blocked/completed · JSON/table）；`docs/phase-8-operator-backlog-v1.md`。**Deferred**: `--resume-latest-approved`; `--batch-approve`; checkpoint preview CLI |
| **Dependencies** | P8-T1 (了解 bundle 結構); W6-T5/T6 checkpoint schema; P8.9-T1 workflow event consumer |
| **Acceptance Criteria** | [1] **v1** backlog 顯示 case_ref/task_type/status/last_event/checkpoint_a_status/intake_decision; [2] batch approve 限制同 task_type (**deferred**); [3] resume latest 自動選取 (**deferred**); [4] Operator CLI 手冊 → `docs/phase-8-operator-backlog-v1.md` |
| **Estimate** | 1.5–2 weeks |
| **Priority** | **P1** — 與 T1 可部分並行 |

#### Operator pending view v1（P8-T2 子交付 · 2026-06-19）

| 指令 | 用途 |
|------|------|
| `python scripts/list_operator_backlog_v1.py --status pending --format json` | 列出需人工關注 cases |
| `python scripts/list_operator_backlog_v1.py --status blocked --format table` | 列出 run.blocked/failed 或 reject 類 |
| `python scripts/list_operator_backlog_v1.py --case-ref <slug> --format json` | 單案 backlog 行 |

**分類規則（摘要）**

| `status` | 規則 |
|----------|------|
| `pending` | CP-A `awaiting_human`；或 gate `review_needed` 且 CP-A 未 resolved；或 CP-A 已 resolved 但尚無 `run.completed` |
| `blocked` | 最新 terminal event 為 `run.blocked`/`run.failed`；或 CP-A `rejected`；或 gate `reject` |
| `completed` | 最新 terminal event 為 `run.completed` 且 CP-A 非 `awaiting_human` |

驗收：`python -m unittest tests.test_operator_backlog_v1 -v`

### P8-T3: Notify v1.5 — Webhook & Basic Reliability

| 欄位 | 內容 |
|------|------|
| **Goal** | Notification 可觸發下游 webhook，具基本可靠性 |
| **Scope** | Webhook adapter (live); retry 機制; file-based DLQ; `bundle_ready` → client summary 發送 |
| **Dependencies** | P8-T1 (client summary 內容); W6-T10 notification gateway |
| **Acceptance Criteria** | [1] Webhook 成功記錄 delivered_at; [2] 失敗進入 retry→DLQ; [3] DLQ 可 CLI 重發; [4] Webhook 整合指南 |
| **Estimate** | 1.5–2 weeks |
| **Priority** | **P2** — 可延後至 75-80% 區間 |

---

## 4. 執行順序建議

```
Week 1-2:  P8-T1 (Bundle Schema)
                ↓
Week 2-3:  P8-T2 (Operator Surface) ─┐
                ↓                    ├── 可部分並行
Week 3-4:  P8-T3 (Notify v1.5) ─────┘
```

**為何先 T1 再 T2/T3**：
- Bundle schema 定義「交付物是什麼」
- Operator view 需要知道 bundle 內容才能正確預覽
- Notify webhook 需要知道 client summary 結構才能發送

---

## 5. 可延後項目 (不影響 80%)

| 項目 | 延後原因 | 建議 milestone |
|------|----------|--------------|
| Multi-case queue / priority | 超過最小控制平面 | 85%+ |
| Audit dashboard UI | CLI + JSONL 已足夠 | 90%+ |
| Email/Slack/Telegram 通知 | Webhook 優先，通道可外掛 | 85%+ |
| Multi-tenant / org 隔離 | 明確 non-goal | Phase 9 |
| Exactly-once / SLA 承諾 | 需 queue infra + 法律審查 | Phase 9 |
| Real-time multi-operator | Race condition 複雜度高 | Phase 9 |

---

## 6. 風險與緩解

| 風險 | 機率 | 緩解 |
|------|------|------|
| Bundle schema 與 W7-T3 client summary 衝突 | 中 | P8-T1 開工前對齊 W7-T3 owner |
| `--resume-latest-approved` 歧義 | 低 | Fail-close: 多個 approved 時列出選項要求明確指定 |
| Webhook retry 阻塞 main flow | 低 | 保持 fail-open: notify 失敗不影響 orchestrator ok |
| Batch approve 跨 cases 風險 | 低 | 限制同 task_type + 預覽確認 |

---

## 7. 參考文件

- `04_Workflows/reports/W6-standard-case-v2-closure-report.md`
- `04_Workflows/briefs/W7-hitl-delivery-v2_input-for-pm.md`
- `04_Workflows/roadmaps/W7-standard-case-v2_tech-roadmap-draft.md`
- `04_Workflows/onboarding/standard-case-hitl-resume-notify_guide.md`

> **Bridge advisory footnote（W3-P8-BRG）**：P8.5 bridge smoke 為 **optional advisory**（in-memory stub · ≠ prod）· **≠** 本 plan 80% 敘事前置；**batch／webhook 仍 deferred**（見 §3 P8-T2 deferred · §5／P8-T3）。詳見 `docs/phase8_5-bridge-smoke-runbook-v1.md` · `docs/phase-8-operator-backlog-v1.md` §Bridge advisory。

---

*Plan 完成。等待尚書省裁決後開票實作。*

---

## Append · 2026-07-13 · P8→100 誠實缺口註記（末尾追加 · 不改歷史正文）

| 項 | 狀態（07-13） | 說明 |
|----|---------------|------|
| P8-T2 deferred batch／resume | **delivered**（P8-T2b） | backlog CLI |
| P8-T2 deferred preview | **delivered**（P8-T2c） | `scripts/preview_checkpoint_v1.py` |
| P8-T3 Notify v1.5 | **mock MVP landed**（`P8-T3-notify-webhook-mock-mvp-v1`） | 本地 mock／DLQ／replay · **≠ prod webhook** |
| 真 Worker API（batch） | **仍缺口** | 卡誠實 100% |
| 真 prod webhook／SLA | **仍缺口** | 卡誠實 100% |

---

## Append · 2026-07-13 · P8→100 閉合（末尾追加）

| 項 | 狀態（07-13 晚） | 說明 |
|----|------------------|------|
| 真 Worker API（batch） | **delivered**（`P8-T4-worker-api-batch-v1`） | `--mode worker_api` + `POST /api/batch/worker/run` |
| 真 sandbox／staging／prod webhook | **delivered**（`P8-T3-notify-webhook-staging-prod-v1`） | wrap P7 adapter；env gates；≠ repo 內寫死 URL |
| SLA／exactly-once | **仍 §5 延後** | Phase 9；**不**擋本計畫 §2.1–2.3 定義下的 P8 100% |
| Operator Web UI／multi-case queue | **仍 §5 延後** | 85%+ 項；不擋本 100% |
