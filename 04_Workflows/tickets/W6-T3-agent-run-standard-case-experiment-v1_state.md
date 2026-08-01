# W6-T3 · Agent-run Standard Case Experiment v1

> **角色**: Architect + Orchestrator  
> **類型**: Design Only（本票不寫程式碼，僅輸出設計文檔）  
> **Wave**: Wave 6 — 95% Automation Blueprint 延伸  
> **建立日期**: 2026-06-10  
> **狀態**: design_in_progress

---

## FRAME（固定框架）

### Goal（目標）
設計一條「Agent 主導 + 兩個 HITL checkpoint」的標準實驗線，限定在 demo_phase / sampleco Tabular MVP 案型，讓未來可以用一張實作票把它變成可重跑的實驗流程。

### Scope（範圍）
- [x] 定義從 S1 Intake Upload → S15 Client Notify 的 15 步完整流程
- [x] 明確每個步驟的「模組 / CLI / 驅動者（Agent/Script/Human）」
- [x] 整合 W5-T1 `run_agent_intake_decision_demo` 與 W5-T2 HITL checkpoint 設計
- [x] 定義 Checkpoint A（Intake Confirmation）與 Checkpoint B（Delivery Confirmation）的觸發條件與 resume 機制
- [x] 標示 demo_phase / sampleco 兩個案型的理想 happy path
- [x] 標出 2–3 個最可能卡住的點與 fallback 方案

### NonScope（不做）
- [ ] 不實作任何程式碼、CLI、或狀態機（純設計票）
- [ ] 不處理 retry / DLQ 機制（見 W6-T7）
- [ ] 不處理真實金流 / 外部支付整合
- [ ] 不處理真實 Email/Slack/Telegram 通知實作（S15 僅設計預留）
- [ ] 不處理 non-tabular 案型（Gov / HQ / ask routes）
- [ ] 不處理 Langfuse / PG trace 接線（L2 adjacent）
- [ ] 不修改既有 `scripts/new_cleaning_case.py`, `app/local_ui.py`, E2E drivers

### AllowedPaths（可修改路徑）
- `docs/agent-run-standard-case-experiment-v1.md`（新建）
- `04_Workflows/tickets/W6-T3-agent-run-standard-case-experiment-v1_state.md`（本檔）
- `04_Workflows/WORKFLOW_INDEX.md`（追加 Wave 6 條目）
- `docs/WAVE_PROGRESS_DASHBOARD.md`（追加 W6-T3 狀態）

### BlockedPaths（禁止碰觸）
- `routing/intake_decision_rules_v1.py`（W5-T1 產物，僅讀取參考）
- `scripts/run_agent_intake_decision_demo.py`（W5-T1B 產物，僅讀取參考）
- `docs/hitl-checkpoints-v1.md`（W5-T2 產物，僅讀取參考）
- 所有既有 case 目錄下的 `intake.json`, `reports/`, `cleaned/`（僅讀取參考設計）
- `.cursor/rules/`, `AGENTS.md`, `ENGINEERING_CONTRACT.md`（除非尚書省授權 Governance 票）

### Dependencies（前置依賴）
- ✅ W5-T1-intake-decision-rules-v1（decision helper 實作）
- ✅ W5-T1B-intake-decision-agent-entry（Agent CLI 入口）
- ✅ W5-2-hitl-checkpoints-v1（HITL checkpoint 設計文件）
- ✅ W4-T1-routing-to-tabular-glue（glue plan 實作）
- ✅ W4-T3-A-intake-tabular-tool-path（Tabular intake 路徑預演 CLI）
- ✅ W3-TL-T2-tabular-tool-selector（selector 實作）
- ✅ W3-TL-T3-tabular-tool-executor（executor + outbox 實作）
- ✅ W6-T1-skill-card-and-skill-map-v1（Skill Cards 映射參考）
- ✅ W6-T2-ninety-five-percent-automation-blueprint-v1（15 步藍圖參考）

### AcceptanceCriteria（驗收標準）

#### AC-1: 流程完整性
- [x] 15 個步驟（S1–S15）都有明確的「模組 / CLI / 驅動者（Agent/Script/Human）」定義
- [x] 每個步驟標示現在狀態（human-only / auto / partial / planned）與目標狀態（auto / HITL）

#### AC-2: Happy Path 設計
- [x] demo_phase 完整 happy path 文字描述（1 段）
- [x] sampleco 完整 happy path 文字描述（1 段）
- [x] 兩個案型在 Checkpoint A/B 觸發條件上的差異明確標示

#### AC-3: HITL Checkpoint 整合
- [x] Checkpoint A（S4）觸發條件、Human 決策選項、resume context 設計完整
- [x] Checkpoint B（S12）觸發條件、Human 決策選項、resume context 設計完整
- [x] 與 W5-T2 `docs/hitl-checkpoints-v1.md` 的對照關係明確

#### AC-4: 風險與 Fallback
- [x] 標出 2–3 個「最可能卡住的點」
- [x] 每個卡住點提供具體 fallback 命令或流程

#### AC-5: NonScope 明確
- [x] 文件 §9 NonScope 列出 v1 不處理的項目（retry/DLQ/金流/真實通知/non-tabular）

---

## STATE（動態狀態）

```yaml
overall_status: design_in_progress
current_owner: orchestrator
next_action: 更新 WORKFLOW_INDEX 與 WAVE_PROGRESS_DASHBOARD，等待尚書省確認設計
last_updated: 2026-06-10

status_by_role:
  orchestrator: done      # FRAME 建立，15 步設計完成
  implementer: pending   # 本票無 implementer（design only）
  reviewer: pending      # 等待 Reviewer 確認設計完整性
  scribe: pending        # 等待 Scribe 更新索引

design_outputs:
  docs_file: docs/agent-run-standard-case-experiment-v1.md
  state_file: 04_Workflows/tickets/W6-T3-agent-run-standard-case-experiment-v1_state.md
  index_updates:
    - WORKFLOW_INDEX.md §Wave 6
    - WAVE_PROGRESS_DASHBOARD.md §Wave 6
```

---

## B_REPORT（實作報告）

> **本票為 Design Only，無 Implementer 實作報告。**
> 
> 若未來開實作票（如 W6-T5 Checkpoint A Implementation），將在此區塊填寫：
> - changed_files
> - artifacts
> - verification
> - behavior_notes
> - deferred_items

---

## C_REPORT（審查報告）

> **等待 Reviewer 填寫。**
> 
> 審查重點：
> 1. 15 步流程是否覆蓋完整（S1–S15）
> 2. 與 W5-T1/W5-T2/W6-T1/W6-T2 上游文件的對照是否正確
> 3. Checkpoint A/B 的設計是否與 `docs/hitl-checkpoints-v1.md` 一致
> 4. NonScope 是否明確，無 scope creep

---

## D_REPORT（文檔報告）

> **等待 Scribe 填寫。**
> 
> 預期內容：
> - docs_updates: 本設計文件與票 state 的新增路徑
> - progress_entry: Wave 6 T3 設計完成條目
> - followup_suggestions: 後續實作票建議（W6-T5, W6-T8 等）

---

## O_NOTES（Orchestrator 筆記）

### 設計決策記錄

#### D1: 為何 S1 Intake Upload 維持 HITL（而非 full auto）
- **考量**: Intake 涉及外部檔案上傳與 client_ref 配對，品質風險高
- **決策**: v1 保持 Human 主導，Agent 輔助建議 case_id；未來可擴充為 full auto
- **對照**: `docs/ninety-five-percent-automation-blueprint-v1.md` §3.2 S1

#### D2: 為何 S15 Client Notify 維持 auto（設計預留）
- **考量**: 通知整合需要外部 webhook / bot 基礎建設，測試複雜
- **決策**: v1 僅設計介面，實作另開 W6-T10
- **對照**: `docs/hitl-checkpoints-v1.md` §7.1

#### D3: Checkpoint A/B 的預設行為差異
- **Checkpoint A (S4)**: 預設 `approve`（timeout 5 分鐘放行）
  - 理由: Intake 階段風險相對可控，且 70% case 為 low risk auto_accept
- **Checkpoint B (S12)**: 預設 `hold`（timeout 不自動放行）
  - 理由: Delivery 前品質把關，錯誤交付成本更高
- **對照**: `docs/hitl-checkpoints-v1.md` §5.1–§5.2

---

### 上游文件對照檢查

| 本設計引用 | 上游文件 | 對照結果 |
|-----------|---------|---------|
| S3 Decision Evaluate | `docs/intake-decision-rules-v1.md` §2 | ✅ 一致 |
| S4 Checkpoint A | `docs/hitl-checkpoints-v1.md` §3 | ✅ 一致 |
| S5 Route Planning | `docs/routing-tool-layer-glue-v1.md` | ✅ 一致 |
| S6 Tool Selection | `docs/tabular-tool-selector-spec.md` | ✅ 一致 |
| S12 Checkpoint B | `docs/hitl-checkpoints-v1.md` §4 | ✅ 一致 |
| 15 步藍圖 | `docs/ninety-five-percent-automation-blueprint-v1.md` §3.1 | ✅ 一致 |
| Skill Card A/B | `docs/skill-cards-v1.md` | ✅ 一致 |

---

## 附錄：15 步快速參考卡

```
S1  Intake Upload      Human      → cases/{client}/{case_id}/intake.json
S2  Index Refresh      Script     → cases/index.json 更新
S3  Decision Evaluate  Agent      → decision: auto_accept/needs_review/reject
S4  Checkpoint A       Human      → approve/reject/revise_plan (HITL)
S5  Route Planning       Script     → glue_plan.selector_task_type
S6  Tool Selection       Agent      → candidate_tools[]
S7  Gate Validation      Script     → eligibility_result.json
S8  Cleaning Execution   Script     → cleaned/*_cleaned.csv
S9  Outbox Write         Script     → outbox/{run_id}.json
S10 Bundle Build         Script     → delivery_signoff.md
S11 Output Guard         Script     → output_guard.status
S12 Checkpoint B         Human      → approve_delivery/request_changes/hold (HITL)
S13 Delivery Approval    Human      → status=delivered (HITL-light)
S14 Ledger Update        Script     → events.jsonl + index sync
S15 Client Notify        Script     → notification (設計預留)

驅動者分布:
- Auto (Agent/Script): S2, S3, S5, S6, S7, S8, S9, S10, S11, S14 (10 步)
- HITL (Human 決策):    S4, S12, S13 (3 步)
- Human-only (v1):      S1, S15 (2 步)
```

---

*W6-T3 · Agent-run Standard Case Experiment v1 · Design Only · 2026-06-10*
