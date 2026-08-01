# 95% 自動化藍圖 v2 — Wave 7 能力對齊版

> **版本**：v2.0 設計收斂稿（Wave 7 · W7-T4）  
> **適用**：Tabular MVP 標準清洗案 · Agent-run 實驗線  
> **日期**：2026-06-10  
> **上游依據**：`docs/ninety-five-percent-automation-blueprint-v1.md` · `docs/agent-standard-line-v1-summary.md` · `docs/WAVE_PROGRESS_DASHBOARD.md` · W7-T1/T2/T3 交付物

---

## §1 目標與 Wave 7 增量

### 1.1 自動化等級（沿用 v1 定義）

| 自動化等級 | 定義 | v2 目標占比 |
|-----------|------|------------|
| **auto** | Agent/Script 自主執行，無人工介入 | 75% |
| **HITL** | Agent 準備決策資料，人工確認後繼續 | 20% |
| **human-only** | 必須人工執行 | 5% → **0%（目標）** |
| **experimental** | 可跑但非 production／非全 fixture 回歸 | （Wave 7 標記，不計入達標率） |
| **controlled_experimental** | 受控準正式線（C/D）；可 run-all-allowed 回歸，仍非 production | （W11-T1 新增，不計入達標率） |

### 1.2 Wave 7 已交付能力（相對 v1）

| 票號 | 能力 | 影響步驟 |
|------|------|---------|
| **W7-T1** | 擴展實驗 fixture：`additional_demo` / `sandbox_client`；orchestrator allowlist 4 案 | S3 preview、Skill Card C/D |
| **W7-T2** | Run path 執行：`demo_phase` → bundle 全鏈；`sampleco` → cleaning 後停 Checkpoint B；live `cleaning_stats` → S11 | S7–S12（run mode） |
| **W7-T3** | Controlled Notify 實驗：讀 signoff/bundle → 模擬 S15 payload → outbox only | S15（experimental） |
| **W6-T8 擴展** | Regression：`--run-mode run-all-allowed`、`--include-extended-fixtures` | 驗收鉤子 |

### 1.3 Scope 邊界（不變）

- Tabular MVP（CSV 清洗交付）；不含 Gov ask / DarkOps / GraphRAG / CLEAN-Orchestrator Wave 7 分軌
- 實驗線 **不改** production 主鏈預設行為

---

## §2 標準工作流（更新）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TABULAR MVP STANDARD FLOW — Wave 7 實驗線 overlay                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  [P1] INTAKE → [P2] DECISION → [P3] EXECUTION → [P4] VALIDATION →           │
│               [P5] DELIVERY → [P6] CLOSEOUT + NOTIFY                        │
│                                                                             │
│  Wave 7 run path（W7-T2）: demo_phase 可跑 S7–S10 + live S11 + CP-B         │
│                            sampleco 可跑 S7–S8，stop_at checkpoint_b        │
│  Wave 7 notify（W7-T3）: S15 模擬 only，demo_phase / sampleco allowlist     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## §3 S1–S15 全流程拆解（v2）

### 3.1 總覽表

| 步驟 ID | 步驟名稱 | Wave 7 狀態 | 成熟度 | v2 分類 | 關鍵產物 / 模組 |
|---------|---------|------------|--------|---------|----------------|
| S1 | Intake Upload | human-only | **stable**（CLI） | **HITL** | `scripts/new_cleaning_case.py` |
| S2 | Index Refresh | auto | **stable** | **auto** | `scripts/build_cases_index.py` |
| S3 | Decision Evaluate | auto（allowlist 有限） | **stable**（2 fixture）/ **experimental**（+2 fixture） | **auto** | `routing/intake_decision_rules_v1.py` |
| S4 | Checkpoint A | HITL live（run mode） | **stable**（run 回歸） | **HITL** | `hitl/checkpoint_a_integration_v1.py` · orchestrator inline |
| S5 | Route Planning | auto | **stable** | **auto** | `routing/intake_to_tabular_glue.py` |
| S6 | Tool Selection | auto preview | **stable** | **auto** | `run_tabular_intake_tool_path.py` |
| S7 | Gate Validation | auto（run path） | **stable**（demo/sampleco run） | **auto** | `execute_tabular_tool` → `validate.eligibility` |
| S8 | Cleaning Execution | auto（run path） | **stable**（demo/sampleco run） | **auto** | `execute_tabular_tool` → `clean.phase_demo` |
| S9 | Outbox Write | auto（run path） | **stable**（run 回歸） | **auto** | `outbox/{case_ref}/{run_id}.json` |
| S10 | Bundle Build | auto（demo run only） | **stable**（demo run）/ **planned**（sampleco 停 delivery 前） | **auto** | `export.delivery_bundle` |
| S11 | Output Guard | auto live read | **stable**（run path）/ mock（preview） | **auto** | `cleaning_stats.json` → live guard |
| S12 | Checkpoint B | HITL live（run path） | **stable**（sampleco run + demo 可寫） | **HITL** | `hitl/checkpoint_b_integration_v1.py` |
| S13 | Delivery Approval | human-only | **stable**（manual） | **HITL** | `delivery_signoff.md` · index 手改 |
| S14 | Ledger Update | auto partial | **experimental** | **auto** | outbox consumer 未接實驗線 |
| S15 | Client Notify | experimental simulated | **experimental** | **experimental→auto** | `delivery/controlled_notify_experiment_v1.py` |

**成熟度圖例**

| 標記 | 含義 |
|------|------|
| **stable** | 有 unittest／回歸命令；行為可重跑 |
| **experimental** | 可跑但 allowlist 窄、dry-run 預設、或未進預設 CI |
| **planned** | 設計已定、程式未接或僅 preview |

### 3.2 實驗 only → 可回歸穩定流程（Wave 7 升格）

| 步驟 | v1 狀態 | Wave 7 升格 | 驗收命令 |
|------|---------|------------|---------|
| S4 Checkpoint A | planned / preview only | **run mode 可寫 outbox** | `tests/test_agent_standard_case_experiment.py` · run + write CP-A |
| S7–S9 Execution chain | stub / preview | **W7-T2 run path 真執行** | demo_phase run → outbox entries |
| S11 Output Guard | mock only | **run path 讀 live cleaning_stats** | `output_guard.source=live_cleaning_stats` |
| S12 Checkpoint B | planned / mock | **W6-T6 + W7-T2 整合寫入** | sampleco `run-all-allowed` → `stopped_at_checkpoint_b` |
| S15 Notify | human-only stub | **W7-T3 模擬 outbox**（仍 experimental） | `tests/test_controlled_delivery_notify_experiment_v1.py` |

### 3.3 仍為實驗性質（Wave 11 受控升格後）

| 項目 | 原因 | Wave 11 狀態 |
|------|------|-------------|
| `additional_demo` / `sandbox_client` **run path** | 非 production fixture；受控 stopping point | **W11-T1** `controlled_experimental` · run-all-allowed 回歸 |
| S3 對新 fixture | `intake_decision_rules_v1` allowlist 仍 demo/sampleco | W8-T2 decision rules v2 |
| S13 一鍵 approve | 無 `approve_delivery.py` | W8-T3 delivery automation |
| S15 正式通知 | `external_dispatch=false` 恆真 | W8-T4 notification gateway |
| S14 index 自動 sync | consumer 未接 orchestrator | W8-T5 ledger integration |
| `--resume-from-checkpoint` | 仍手動提取 resume_context | W8-T6 resume framework |

---

## §4 auto / HITL / human-only 分佈

### 4.1 Wave 5 完成後（v1 基線 · 現在狀態）

```
auto:        S2, S5, S6                    （3 步 · 20%）
partial:     S3                             （1 步）
planned:     S4, S12                        （2 步）
auto chain:  S7–S11, S14                    （6 步 · 主鏈已有，實驗線未接）
human-only:  S1, S13, S15                   （3 步 · 20%）
```

**實測自動化率（v1 實驗線 preview）**：(9 + 0×0.5) / 15 ≈ **60%**

### 4.2 Wave 7 完成後（實際 · demo_phase + sampleco run path）

```
┌────────────┬──────────────┬────────────────────────────────────────────┐
│   Step     │ v2 分類      │ Wave 7 備註                                 │
├────────────┼──────────────┼────────────────────────────────────────────┤
│ S1 Intake  │ HITL         │ human-only CLI；無 intake API               │
│ S2 Index   │ auto         │ stable                                      │
│ S3 Decide  │ auto         │ stable（2 fixture）；+2 experimental         │
│ S4 CP-A    │ HITL         │ stable run 模式可寫 state                   │
│ S5 Route   │ auto         │ stable                                      │
│ S6 Select  │ auto         │ stable preview                              │
│ S7 Gate    │ auto         │ stable（run path）                          │
│ S8 Clean   │ auto         │ stable（run path）                          │
│ S9 Outbox  │ auto         │ stable（run path）                          │
│ S10 Bundle │ auto         │ stable demo run；sampleco 停 delivery 前   │
│ S11 Guard  │ auto         │ stable live（run）；mock（preview）         │
│ S12 CP-B   │ HITL         │ stable run 整合層                           │
│ S13 Approve│ HITL         │ 仍 human-only edit signoff/index            │
│ S14 Ledger │ auto         │ experimental partial                        │
│ S15 Notify │ experimental │ W7-T3 simulated only                      │
└────────────┴──────────────┴────────────────────────────────────────────┘

分類計數（15 步）:
  auto:          10 步（S2, S3*, S5–S11, S14†）
  HITL:           4 步（S1, S4, S12, S13）
  experimental:   1 步（S15）
  human-only:     0 步（S1 已歸 HITL）

* S3 對 additional_demo/sandbox_client 仍 needs_review + unknown_fixture_profile
† S14 未完整接 consumer，計入 auto 但標 experimental
‡ W11-T1：C/D run coverage 納入 `run-all-allowed` 回歸，成熟度 `controlled_experimental`（不計入 95% 達標率）
```

**Wave 7 實測自動化率（含 HITL 半權重）**：

```
(10 + 4×0.5) / 15 = 13/15 ≈ 86.7%
```

**距離 95% 目標缺口**：≈ **8.3%**（主要 S1→HITL 輕確認、S13 一鍵化、S15 升格 auto、S14 完整化）

### 4.3 目標狀態（Wave 8 完成後 · 維持 v1 95% 目標）

| 分類 | 步驟數 | 步驟 |
|------|--------|------|
| **auto** | 11 | S2, S3, S5–S11, S14, S15 |
| **HITL** | 4 | S1, S4, S12, S13 |
| **human-only** | 0 | — |

**目標公式**：(11 + 4×0.5) / 15 = **93.3% ≈ 95%**

---

## §5 關鍵 Checkpoint（Wave 7 實際行為）

### 5.1 Checkpoint A

| 屬性 | Wave 7 實際 |
|------|-------------|
| 觸發 | `needs_review` / `risk_level=medium`（四 fixture preview 皆可能） |
| Run 模式 | `written` 或 `auto_approved`（`--auto-approve-intake`） |
| 產出 | `outbox/{case_ref}/checkpoint_A-intake-confirmation_*.json` |
| 回歸 | `run_agent_standard_case_regression.py --run-mode run` |

### 5.2 Checkpoint B

| 屬性 | Wave 7 實際 |
|------|-------------|
| demo_phase run | live guard `ok`；可能 `written` 或 skipped |
| sampleco run | `stop_before_delivery=true` → `stopped_at_checkpoint_b` |
| 整合 | `maybe_create_checkpoint_b`（W6-T6） |
| Preview | 仍 mock + `would_trigger` |

---

## §6 Wave 8 缺口與建議票列表

| 優先 | Gap ID | 缺口 | 建議票 | 預估 uplift |
|------|--------|------|--------|-------------|
| P0 | G8-1 | **Decision Rules v2**：`additional_demo` / `sandbox_client` profile + 降 reject | `W8-T2-decision-rules-v2-profile-expansion` | S3 stable +3% |
| P0 | G8-2 | **Run path 擴面**：新 fixture run profile + E2E 產物 | `W8-T1-extended-fixture-run-paths` | 覆蓋率 |
| P0 | G8-3 | **Delivery Automation**：`approve_delivery.py` + index 更新 | `W8-T3-delivery-approval-automation` | S13 HITL 輕量化 +3% |
| P1 | G8-4 | **Notification Gateway**：Telegram/Email 正式管線（非 simulated） | `W8-T4-client-notification-gateway` | S15 auto +2% |
| P1 | G8-5 | **非 Tabular 支援**：routing catalog 擴 family + experiment block | `W8-T5-non-tabular-intake-shadow` | 案型邊界 |
| P1 | G8-6 | **Ledger Integration**：S14 consumer 接 experiment closeout | `W8-T5-ledger-experiment-integration` | S14 stable |
| P2 | G8-7 | **Resume Framework**：`--resume-from-checkpoint` CLI | `W8-T6-checkpoint-resume-cli` | 運維效率 |
| P2 | G8-8 | **Intake API Gateway**：S1 human-only → HITL | `W8-T7-intake-api-gateway` | S1 +3% |
| P2 | G8-9 | **CI 升格**：experiment regression 進 eval-gate（可選 `--include-extended-fixtures`） | `W8-T8-experiment-regression-ci` | 治理 |
| P3 | G8-10 | **Executor Retry + DLQ** | `W8-T9-executor-retry-dlq` | 韌性 |

### 6.1 Wave 8 票依賴（建議）

```
W8-T2 (Decision v2)
    │
    ├──→ W8-T1 (Run path 擴面)
    │
    └──→ W8-T3 (Delivery approve)
              │
              └──→ W8-T4 (Notify gateway)
                        │
                        └──→ W8-T5 (Ledger)
```

---

## §7 驗收與回歸命令（Wave 7）

```bash
# 實驗線 unittest（含 W7-T2 run path）
python -m unittest tests.test_agent_standard_case_experiment -v

# 輕量回歸（2 fixture preview）
python scripts/run_agent_standard_case_regression.py --format json

# W7-T2 run-all-allowed（demo + sampleco run path）
python scripts/run_agent_standard_case_regression.py \
  --run-mode run-all-allowed --auto-approve-intake --format json

# W7-T1 擴展 fixture preview（4 cases）
python scripts/run_agent_standard_case_regression.py \
  --include-extended-fixtures --format json

# W7-T3 Controlled Notify（dry-run）
python scripts/run_controlled_delivery_notify_experiment.py \
  --case-dir cases/demo_phase --format json

python -m unittest tests.test_controlled_delivery_notify_experiment_v1 -v

# MVP 主鏈守護（不變）
python scripts/run_mvp_mainline_regression.py -v
```

---

## §8 與 v1 對照索引

| v1 引用 | v2 狀態 |
|---------|---------|
| G1 Intake API | 仍 planned → **W8-T7** |
| G2/G3 Checkpoint A/B 實作 | **done**（W6-T5/T6 + W7-T2 run 接線） |
| G5 Glue-Selector 接線 | **partial**（W7-T2 run path 實驂 subset） |
| G7 Delivery Automation | planned → **W8-T3** |
| G8 Client Notification | **experimental**（W7-T3 simulated）→ **W8-T4** prod |
| G10 Resume Framework | planned → **W8-T6** |
| W6-T2 95% 目標 | Wave 7 達 **~87%**；Wave 8 收 **95%** |

---

## §9 附錄：自動化計算

```
Wave 7 實測（demo/sampleco run path stable）:
  (10 auto + 4 HITL×0.5) / 15 = 86.7%

Wave 8 目標（S15 auto + S13 一鍵 + S1 HITL）:
  (11 auto + 4 HITL×0.5) / 15 = 93.3% ≈ 95%
```

---

*95%-AUTOMATION-BLUEPRINT-v2 · W7-T4 · Architecture Design Convergence · 2026-06-10*
