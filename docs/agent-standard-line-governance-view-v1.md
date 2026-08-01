# Agent-Run 標準線治理觀點 v1 — Governance View

> **版本**: v1.0 治理設計稿（Governance Design Document）  
> **票號**: W6-T9 · Agent-standard-line-governance-view-v1  
> **適用**: Agent-run Standard Case Experiment Line（W6-T3~T8 全流程）  
> **日期**: 2026-06-10  
> **上游依據**: `docs/agent-run-standard-case-experiment-v1.md` · `docs/ninety-five-percent-automation-blueprint-v1.md` · `docs/hitl-checkpoints-v1.md` · `ENGINEERING_CONTRACT.md`

---

## §1 目的：為什麼要用治理視角看這條線

### 1.1 背景

Agent-run 標準線（W6-T3~T8）設計了一條從 **S1 Intake** 到 **S15 Client Notify** 的 15 步自動化流程，目標是達成 **95% 自動化率**（11 步 auto + 4 步 HITL）。

這條線涉及：
- **10 個自動執行步驟**（Agent/Script 驅動）
- **4 個 HITL 檢查點**（Human-in-the-Loop 決策）
- **1 個實驗性 orchestrator**（`run_agent_standard_case_experiment.py`）
- **2 個關鍵 checkpoint 整合層**（Checkpoint A / B）

### 1.2 治理挑戰

當自動化率從 60% 提升至 95%，治理面臨以下核心問題：

| 問題 | 風險 | 治理需求 |
|------|------|----------|
| 誰有權決定「接案」？ | 錯接風險、資源浪費 | 明確 intake 決策權邊界 |
| 誰對「交付品質」負責？ | 錯交付、客戶損失 | 品質守衛 + checkpoint 機制 |
| 如何審計 Agent 決策？ | 黑箱操作、無法追溯 | 完整 outbox / checkpoint 日誌 |
| 如何升級自動化？ | 治理邊界模糊 | 分級決策權、漸進授權 |

### 1.3 本文檔目標

本文檔從 **治理 / 審計 / 風險控制** 視角，為 W6-T3~T8 標準線建立：

1. **決策權分佈圖** — 人類 vs Agent 的權責邊界
2. **審計材料清單** — 可作為 audit log 依據的檔案與欄位
3. **風險類型與 safeguard** — 錯接、錯清洗、錯交付的防護層
4. **升級路徑治理原則** — 從 95% 再往上推時的治理邊界維護

---

## §2 決策權分佈：人類 vs Agent

### 2.1 15 步決策權矩陣

| 步驟 | 名稱 | 驅動者 | 決策者 | 決策類型 | 預設行為 |
|------|------|--------|--------|----------|----------|
| S1 | Intake Upload | Human | **Human** | 接案／拒案 | Human 主導 |
| S2 | Index Refresh | Script | **Auto** | 無決策 | 自動執行 |
| S3 | Decision Evaluate | Agent | **Agent** | auto_accept / needs_review / reject | 依規則判定 |
| S4 | Checkpoint A | Agent + Human | **Human** | approve / reject / revise_plan | 5min timeout → approve |
| S5 | Route Planning | Script | **Auto** | 無決策 | 自動執行 |
| S6 | Tool Selection | Agent | **Auto** | 無決策 | 自動執行 |
| S7 | Gate Validation | Script | **Auto** | accepted / review_needed / rejected | 依條件判定 |
| S8 | Cleaning Execution | Script | **Auto** | 無決策 | 自動執行 |
| S9 | Outbox Write | Script | **Auto** | 無決策 | 自動執行 |
| S10 | Bundle Build | Script | **Auto** | 無決策 | 自動執行 |
| S11 | Output Guard | Script | **Auto** | ok / warning / error | 依條件判定 |
| S12 | Checkpoint B | Agent + Human | **Human** | approve_delivery / request_changes / hold | 無 timeout，必須人工 |
| S13 | Delivery Approval | Human | **Human** | confirm / reject | 一鍵確認 |
| S14 | Ledger Update | Script | **Auto** | 無決策 | 自動執行 |
| S15 | Client Notify | Script | **Auto** | 無決策 | 自動執行 |

### 2.2 決策權分類

#### 2.2.1 Agent 決策（Auto Decision）

**範圍**: S3, S7, S11

| 步驟 | 決策內容 | 判定依據 | 權限邊界 |
|------|----------|----------|----------|
| **S3** | intake_decision | `routing/intake_decision_rules_v1.py` | allowlist (demo_phase / sampleco) |
| **S7** | gate_validation | `scripts/check_case_eligibility.py` | row count / schema / file size |
| **S11** | output_guard | removal_ratio / schema_check / forced flag | ratio > 0.5 → warning |

**Agent 決策原則**:
- 嚴格依據規則代碼，無自由裁量權
- 輸出必須結構化（`decision`, `risk_level`, `rationale`）
- 高風險（medium/high）必須觸發 HITL checkpoint

#### 2.2.2 人類決策（Human Decision）

**範圍**: S1, S4, S12, S13

| 步驟 | 決策內容 | 決策依據 | 時間限制 |
|------|----------|----------|----------|
| **S1** | 是否接受 case | intake 資料完整性 | 無 |
| **S4** | 是否批准 intake 計畫 | Agent 提供的 `case_summary` + `gate_preview` | 5min timeout → auto approve |
| **S12** | 是否批准 delivery | `execution_summary` + `cleaning_results` + `output_guard` | 無 timeout，必須確認 |
| **S13** | 最終交付確認 | `delivery_signoff.md` 內容 | 無 |

**人類決策原則**:
- Checkpoint A（S4）: 預設放行，但保留否決權
- Checkpoint B（S12）: 預設暫停（hold），品質把關
- 所有 human decision 必須寫入 checkpoint JSON，供審計

### 2.3 決策權流程圖

```
[S1 Intake] ──→ Human 決定是否接案
    │
    ▼
[S3 Decision] ──→ Agent 判定 risk_level
    │
    ├──→ low risk ──→ 跳過 S4 ──→ 自動執行 S5-S11
    │
    └──→ medium/high ──→ [S4 Checkpoint A] ──→ Human 決策
                                    │
                                    ├──→ approve ──→ 繼續自動流程
                                    ├──→ reject ──→ 流程終止
                                    └──→ revise_plan ──→ Agent 重算

[S11 Output Guard] ──→ status=warning? ──→ [S12 Checkpoint B] ──→ Human 決策
                                                    │
                                                    ├──→ approve_delivery
                                                    ├──→ request_changes
                                                    └──→ hold

[S13 Delivery Approval] ──→ Human 最終確認 ──→ [S14-S15] Auto closeout
```

---

## §3 審計材料：哪些檔案應被視為 audit log

### 3.1 Audit Log 檔案清單

| 類別 | 檔案路徑 | 內容 | 保留期限 |
|------|----------|------|----------|
| **Intake** | `cases/{case_ref}/intake.json` | 原始接案資料 | 永久 |
| **Decision** | `outbox/{case_ref}/checkpoint_A-intake-confirmation_*.json` | Checkpoint A 狀態與決策 | 永久 |
| **Route Plan** | orchestrator output / `planned_route` | Selector + planned_tools | 隨 run 日誌 |
| **Execution** | `outbox/{case_ref}/{run_id}_*.json` | 每步執行結果 | 永久 |
| **Cleaning Stats** | `cases/{case_ref}/reports/cleaning_stats.json` | 清洗前後行數、removal_ratio | 永久 |
| **Output Guard** | `cases/{case_ref}/reports/eligibility_result.json` | Gate 判定結果 | 永久 |
| **Checkpoint B** | `outbox/{case_ref}/checkpoint_B-delivery-confirmation_*.json` | Checkpoint B 狀態與決策 | 永久 |
| **Delivery Signoff** | `cases/{case_ref}/delivery_signoff.md` | 交付摘要 | 永久 |
| **Index** | `cases/index.json` | Case 狀態追蹤 | 永久 |
| **Events** | `outbox/events.jsonl` | 所有 outbox 事件串流 | 永久 |

### 3.2 關鍵審計欄位

#### Checkpoint A（`checkpoint_A-intake-confirmation_*.json`）

```json
{
  "checkpoint_id": "A-intake-confirmation",
  "case_ref": "demo_phase",
  "status": "awaiting_human | approved | rejected",
  "created_at": "2026-06-10T08:30:00Z",
  "agent_output": {
    "intake_decision": {
      "decision": "needs_review",
      "risk_level": "medium",
      "rationale": ["task_type=tabular.cleaning.mvp", "..."]
    },
    "case_summary": { "client_ref": "...", "estimated_rows": 7 },
    "gate_preview": { "eligibility": "review_needed", "exit_code": 2 }
  },
  "human_decision": {
    "action": "approve",
    "by": "operator_001",
    "at": "2026-06-10T08:32:00Z",
    "notes": "LGTM"
  },
  "resume_context": { "resume_from": "selector", "planned_tools": [...] }
}
```

#### Checkpoint B（`checkpoint_B-delivery-confirmation_*.json`）

```json
{
  "checkpoint_id": "B-delivery-confirmation",
  "case_ref": "demo_phase",
  "status": "awaiting_human | approved | changes_requested | on_hold",
  "agent_output": {
    "execution_summary": { "tools_executed": [...] },
    "cleaning_results": {
      "input_rows": 7,
      "output_rows": 5,
      "removal_ratio": 0.286
    },
    "output_guard": { "status": "warning", "checks": {...} }
  },
  "human_decision": {
    "action": "approve_delivery",
    "by": "operator_002",
    "at": "2026-06-10T08:35:00Z"
  }
}
```

### 3.3 審計追蹤路徑

**完整 case 審計鏈**:

```
intake.json ──→ checkpoint_A ──→ outbox runs (S5-S11) ──→ checkpoint_B ──→ delivery_signoff ──→ index.json update
   │                │                  │                    │                  │
   │                │                  │                    │                  │
   ▼                ▼                  ▼                    ▼                  ▼
 S1 接案        S4 人工決策        S5-S11 執行紀錄        S12 品質把關       S13 最終交付
```

---

## §4 風險類型與 Safeguard

### 4.1 風險矩陣

| 風險代碼 | 風險名稱 | 發生階段 | 影響 | 機率 |
|----------|----------|----------|------|------|
| **R1** | 錯接案（Wrong Intake） | S1-S3 | 資源浪費、錯誤處理 | 中 |
| **R2** | 錯路由（Wrong Route） | S4-S6 | 工具選擇錯誤、無法完成 | 低 |
| **R3** | 錯清洗（Wrong Cleaning） | S7-S8 | 資料損壞、品質下降 | 中 |
| **R4** | 錯交付（Wrong Delivery） | S11-S13 | 客戶損失、信譽損害 | 高 |
| **R5** | 狀態遺失（State Loss） | S4, S12 | 流程中斷、無法 resume | 低 |

### 4.2 Safeguard 分層

#### Layer 1: 預防（Prevention）

| 風險 | Safeguard | 位置 | 有效性 |
|------|-----------|------|--------|
| R1 錯接案 | Intake Decision Rules（allowlist） | S3 | 高（僅限 demo_phase / sampleco）|
| R1 錯接案 | Gate Validation（row count / schema）| S7 | 高 |
| R2 錯路由 | Glue + Selector 規則驗證 | S5-S6 | 高（dry-run 預演）|
| R3 錯清洗 | `--force` flag 需明確 | S8 | 中（依賴 S7 exit_code）|

#### Layer 2: 檢測（Detection）

| 風險 | Safeguard | 位置 | 觸發條件 |
|------|-----------|------|----------|
| R3 錯清洗 | Output Guard（removal_ratio > 0.5）| S11 | ratio > 50% |
| R4 錯交付 | Checkpoint B | S12 | output_guard=warning OR forced_cleaning |
| R4 錯交付 | Delivery Signoff 人工閱讀 | S13 | 所有 cases |

#### Layer 3: 回應（Response）

| 風險 | Safeguard | 位置 | 動作 |
|------|-----------|------|------|
| R1-R4 | Checkpoint A/B Human 決策 | S4, S12 | approve / reject / revise |
| R5 | Checkpoint State 持久化 | S4, S12 | outbox/checkpoint_*.json |
| R5 | Resume Context | S4, S12 | `resume_from` + `planned_tools` |

### 4.3 風險與 Checkpoint 對應

```
R1 錯接案 ──→ S3 Decision Evaluate ──→ medium/high risk ──→ S4 Checkpoint A
R3 錯清洗 ──→ S8 Cleaning Execution ──→ --force / exit 2 ──→ S11 Output Guard
R4 錯交付 ──→ S11 Output Guard ──→ warning status ──→ S12 Checkpoint B
```

---

## §5 升級路徑：從 95% 再往上推

### 5.1 現況（Wave 6-T3~T8）

| 步驟 | 狀態 | 自動化貢獻 |
|------|------|------------|
| S1 Intake | human-only | 0% |
| S4 Checkpoint A | planned → HITL | 50%（timeout auto-approve）|
| S12 Checkpoint B | planned → HITL | 50%（timeout 不自動）|
| S13 Delivery Approval | human-only | 0% |
| S15 Client Notify | human-only | 0% |

**當前自動化率**: (11 + 2×0.5) / 15 = **80%**（實際，因 S4/S12 剛實作）

**目標自動化率**: 95%

### 5.2 升級選項與治理邊界

#### 選項 A: S1 Intake → HITL（預估 +5%）

| 項目 | 內容 |
|------|------|
| 改變 | Human-only → HITL（Agent 準備 + Human 確認）|
| Agent 權限 | 自動偵測 data_file 格式、建議 case_id |
| Human 保留 | 確認 client_ref / case_id 對應關係 |
| 風險 | 自動偵測錯誤格式 → 誤建 case |
| Safeguard | Intake API Gateway 驗證 + S3 Decision 第二層防護 |
| 實作票 | W6-T3-intake-api-gateway |

**治理原則**: Human 保留「最終確認權」，Agent 僅提供建議。

#### 選項 B: S4 Checkpoint A → Auto-approve Low Risk（預估 +3%）

| 項目 | 內容 |
|------|------|
| 改變 | 5min timeout → 完全 auto-approve for low risk |
| Agent 權限 | `auto_accept` + `low` risk 直接通過，無等待 |
| Human 保留 | 事後抽查（post-hoc audit）|
| 風險 | 低風險誤判 |
| Safeguard | 保留「HITL_FORCE_CHECKPOINT_A=1」覆寫選項 |
| 實作票 | W6-T4-decision-rules-v2 |

**治理原則**: 人類保留「啟用強制 checkpoint」的覆寫權。

#### 選項 C: S13 Delivery Approval → HITL（預估 +3%）

| 項目 | 內容 |
|------|------|
| 改變 | Human-only → HITL（一鍵確認）|
| Agent 權限 | 自動生成 delivery_signoff.md final version |
| Human 保留 | 一鍵確認 / 拒絕 |
| 風險 | 品質問題未被 S12 攔截 |
| Safeguard | S12 Checkpoint B 必須先通過 |
| 實作票 | W6-T9-delivery-automation |

**治理原則**: 即使自動化，Human 仍保留「最終一鍵否決權」。

#### 選項 D: S15 Client Notify → Auto（預估 +2%）

| 項目 | 內容 |
|------|------|
| 改變 | Human-only → Auto |
| Agent 權限 | 自動發送 Telegram/Email 通知 |
| Human 保留 | 無（純通知，無決策）|
| 風險 | 通知內容錯誤 |
| Safeguard | 模板驗證 + S13 通過後才觸發 |
| 實作票 | W6-T10-client-notification-gateway |

**治理原則**: 純通知步驟可完全自動化，但內容模板需 Human 預審。

### 5.3 治理邊界維護原則

無論自動化率如何提升，以下邊界 **永不開放給 Agent**:

| 邊界 | 原因 | 永遠 Human |
|------|------|------------|
| **DarkOps 解禁** | 憲法 §7 禁區 | 尚書省專屬 |
| **Production config 變更** | 環境風險 | 維運團隊 |
| **新客戶 profile 首次接入** | 業務風險 | 業務負責人 |
| **removal_ratio > 90%** | 品質風險 | Checkpoint B 強制介入 |

### 5.4 升級檢查清單（Governance Gate）

任何自動化升級前，必須通過以下治理檢查：

- [ ] **Audit Trail 完整**: 所有 Agent 決策寫入 outbox / checkpoint
- [ ] **Fallback 就緒**: 每個 auto-decision 都有對應的 rollback / human-escalation 路徑
- [ ] **監控就緒**: 自動化步驟有 metrics / alerting
- [ ] **測試通過**: 連續 100 次 run 無誤判（shadow mode）
- [ ] **文件更新**: 本治理觀點文件更新對應章節

---

## §6 參考索引

| 文件 | 用途 |
|------|------|
| `docs/agent-run-standard-case-experiment-v1.md` | W6-T3 15 步標準實驗線設計 |
| `docs/ninety-five-percent-automation-blueprint-v1.md` | W6-T2 自動化藍圖（含 S1-S15 分佈）|
| `docs/hitl-checkpoints-v1.md` | W5-T2 Checkpoint A/B 設計母本 |
| `docs/checkpoint-a-integration-v1.md` | W6-T5 Checkpoint A 整合層 |
| `docs/checkpoint-b-integration-v1.md` | W6-T6 Checkpoint B 整合層 |
| `docs/agent-run-experiment-eval-guide-v1.md` | W6-T7 驗收與升級條件（G1-G7）|
| `ENGINEERING_CONTRACT.md` | 12-rule / 四流派 / Work Report 規範 |
| `HARNESS_CONSTITUTION.md` | 禁區類型表 / 權威位階 |

---

*AGENT-STANDARD-LINE-GOVERNANCE-VIEW-v1 · W6-T9 · 2026-06-10*
