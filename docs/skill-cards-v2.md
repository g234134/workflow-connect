# Skill Cards v2 — Tabular MVP · Wave 7 擴展

> **Ticket**: W7-T4 · update-ninety-five-percent-blueprint-and-skills-wave7-v1  
> **Date**: 2026-06-10  
> **Role**: Architect + Governance  
> **Purpose**: 在 v1 Card A/B 基礎上，對齊 W7-T1 新 fixture、W7-T2 run path、W7-T3 Controlled Notify

**上游**：`docs/skill-cards-v1.md` · `docs/ninety-five-percent-automation-blueprint-v2.md`

---

## 概述

v2 新增：

| Card | Skill Name | 來源 | 成熟度 |
|------|------------|------|--------|
| **A** | `tabular.cleaning.phase_demo` | `cases/demo_phase` | **stable** · v1.0 |
| **B** | `tabular.cleaning.sampleco_milestone` | `cases/sampleco/2026-0001` | **stable** · v1.0 |
| **C** | `tabular.cleaning.additional_demo` | `cases/additional_demo` | **controlled_experimental** · W11-T1 |
| **D** | `tabular.cleaning.sandbox_client` | `cases/sandbox_client` | **controlled_experimental** · W11-T1 |
| **N** | `delivery.controlled_notify_experiment` | W7-T3 | **experimental** · simulated only |

---

## Skill Card A：demo_phase 標準清洗案

> v1 完整內容見 `docs/skill-cards-v1.md` §Skill Card A。v2 增量如下。

### v2 增量（W7-T2 run path）

| 欄位 | v2 值 |
|------|-------|
| **Run Path Profile** | `stop_at=bundle` · tools: gate → clean → bundle |
| **W7 Run 命令** | `run_agent_standard_case_experiment.py --mode run --auto-approve-intake` |
| **S11 來源** | run 模式：`live_cleaning_stats`；preview：`mock_profile_demo_phase` |
| **Checkpoint B** | run 後可能 `written` 或 skipped（forced_cleaning 仍可能 would_trigger） |
| **Notify（Card N）** | 允許 Controlled Notify（bundle 就緒後） |

---

## Skill Card B：sampleco/2026-0001 標準清洗案

> v1 完整內容見 `docs/skill-cards-v1.md` §Skill Card B。v2 增量如下。

### v2 增量（W7-T2 controlled run）

| 欄位 | v2 值 |
|------|-------|
| **Run Path Profile** | `stop_at=checkpoint_b` · `stop_before_delivery=true` |
| **Tools Executed** | `validate.eligibility` → `clean.phase_demo`（**無** bundle） |
| **final_status** | `stopped_at_checkpoint_b` |
| **Checkpoint B** | live 整合層寫入或 `stopped_before_delivery` |
| **Notify（Card N）** | 允許（需先有 reports；通常先跑主鏈 E2E 產物） |

---

## Skill Card C：additional_demo 擴展 Phase 表

### 基本資訊

| 欄位 | 值 |
|------|-----|
| **Skill Name** | `tabular.cleaning.additional_demo` |
| **Alias** | 擴展 Phase 表（12 行 · review_needed） |
| **Source Case** | `cases/additional_demo` |
| **Maturity** | **controlled_experimental** · W11-T1（非 production） |
| **ticket_type** | `tabular.cleaning.mvp` |

### 適用條件

- **Input Schema**: Phase 表四列 + 擴展欄（`Phase`, `名稱`, `之前`, `現在（建議）`）
- **Data Volume**: 12 行（<100 → gate `review_needed`）
- **Gate Status**: `review_needed`（exit 2）
- **Client Profile** | `additional-demo`（**非** v1 decision allowlist）

### 輸入

```yaml
intake.json:
  client_ref: "additional-demo"
  case_id: "additional_demo"
  data_file: "raw/Phase_extended.csv"
  scale.row_count: 12

raw/Phase_extended.csv:
  - 12 行 Phase 進度表（含重複 phase 2 列）
```

### 路由 / Glue

| 階段 | 輸出 |
|------|------|
| `plan_tabular_route` | `case_profile=additional_demo` · `inferred_gate_notes: [phase_like, ...]` |
| Decision（v1 rules） | `needs_review` + `unknown_fixture_profile` signal |

### Selector / planned_tools

| 步驟 | Tool ID | 備註 |
|------|---------|------|
| P2 Gate | `validate.eligibility` | 預期 exit 2 |
| P3 Cleaning | `clean.phase_demo` | 需 `--force`（與 demo_phase 類似） |
| P4 Bundle | `export.delivery_bundle` | run path **W8-T1**：stop at CP-B（experimental） |

### Wave 7 / Wave 8 實驗線行為

| 模式 | 行為 |
|------|------|
| `preview` | ✅ allowlist · CP-A `would_pause` · mock S11 |
| `run` | ✅ **W11-T1** · gate → cleaning + outbox · stop at CP-B · `maturity=controlled_experimental` |
| regression | ✅ `run-all-allowed` + `--include-extended-fixtures` · `regression_bundle_probe`（test only） |

### 完成定義（DoD · controlled_experimental）

- [x] preview orchestrator `ok: true`
- [x] `decision=needs_review`
- [x] `final_status=waiting_for_human`（preview）或 `stopped_at_checkpoint_b`（run）
- [x] 納入 regression：`--include-extended-fixtures` + `--run-mode run-all-allowed`

### Human Checkpoint

| 檢查點 | 條件 | 預設 |
|--------|------|------|
| CP-A | `needs_review` | would_pause |
| 新 profile | 非 v1 allowlist | 需 W8 decision v2 |

---

## Skill Card D：sandbox_client 沙盒客戶樣本

### 基本資訊

| 欄位 | 值 |
|------|-----|
| **Skill Name** | `tabular.cleaning.sandbox_client` |
| **Alias** | 沙盒客戶 milestone export（55 行） |
| **Source Case** | `cases/sandbox_client` |
| **Maturity** | **controlled_experimental** · W11-T1（非 production） |
| **ticket_type** | `tabular.cleaning.mvp` |

### 適用條件

- **Input Schema**: milestone export（`sandbox_milestone_export.csv`）
- **Data Volume**: 55 行（<100 → gate `review_needed`）
- **Client Profile**: `sandbox-client`
- **Schema Notes**: 待 E2E 後補 `gate_notes`（目前 preview mock）

### 輸入

```yaml
intake.json:
  client_ref: "sandbox-client"
  case_id: "sandbox_client"
  data_file: "raw/sandbox_milestone_export.csv"
  scale.row_count: 55
  sensitivity: internal
```

### Wave 7 / Wave 8 實驗線行為

| 模式 | 行為 |
|------|------|
| `preview` | ✅ mock `output_guard.source=mock_profile_sandbox_client` |
| `run` | ✅ **W11-T1** · gate + cleaning（live stats）· `stop_at=cleaning_preview` · `maturity=controlled_experimental` |
| Controlled Notify | ❌ 不在 W7-T3 notify allowlist |

### 完成定義（DoD · controlled_experimental）

- [x] preview `ok: true` · `case_ref=sandbox_client`
- [x] run `final_status=stopped_at_cleaning_preview`
- [x] regression artifact 寫入 `outbox/agent_experiment_regression/`
- [x] raw CSV 存在且 row count 穩定

### Human Checkpoint

| 檢查點 | 條件 |
|--------|------|
| CP-A | `needs_review`（unknown profile） |
| Schema | `schema_check=review` in mock guard |

---

## Skill Card N：Controlled Notify（W7-T3）

### 基本資訊

| 欄位 | 值 |
|------|-----|
| **Skill Name** | `delivery.controlled_notify_experiment` |
| **Alias** | S15 模擬客戶通知（sandbox only） |
| **Module** | `delivery/controlled_notify_experiment_v1.py` |
| **CLI** | `scripts/run_controlled_delivery_notify_experiment.py` |
| **Maturity** | **experimental** · v1 |
| **Schema** | `controlled_notify_experiment_v1` |

### 適用條件

- **Allowlist case_ref**: `demo_phase` · `sampleco/2026-0001` **only**
- **Sensitivity**: `internal` only
- **Blocked**: `acme*` · `*-prod` client_ref · 非 allowlist case
- **前置產物**: `delivery_signoff.md` · `reports/report.json`

### 輸入

```yaml
case_dir: cases/demo_phase  # or sampleco/2026-0001
dry_run: true               # 預設；不寫 outbox
```

### 執行 / 產物

| 模式 | 產物 |
|------|------|
| `--dry-run`（預設） | `client_summary_text`（stdout only） |
| `--no-dry-run` | `outbox/{case_ref}/notify_experiment_{ts}.json` |

**Record 必填鍵**：`schema_version` · `simulated=true` · `external_dispatch=false` · `notify_payload`

### 完成定義（DoD）

- [ ] `ok: true` · `simulated=true` · `external_dispatch=false`
- [ ] summary 含 "sandbox only" 免責
- [ ] 非 allowlist → `blocked=true`
- [ ] unittest 5/5 pass

### Safeguard（治理）

| 規則 | 說明 |
|------|------|
| 禁止 external dispatch | 程式恆 `external_dispatch=false` |
| 禁止 prod client_ref | `is_experiment_case_allowed()` 攔截 |
| 必須 internal sensitivity | 非 internal → blocked |

### 常見失敗模式

| 失敗 | 處理 |
|------|------|
| missing report.json | 先跑 E2E / demo run path 產 bundle |
| acme case | 預期 blocked；非 bug |
| 誤以為已發 Telegram | 檢查 `notify_channel=experiment_log` |

---

## Skill Card 對照表（v2 全集）

| 維度 | A: demo_phase | B: sampleco | C: additional_demo | D: sandbox_client |
|------|---------------|-------------|--------------------|--------------------|
| **輸入行數** | 7 | 115 | 12 | 55 |
| **Gate** | review_needed | accepted | review_needed | review_needed |
| **Run path** | ✅ bundle | ✅ stop CP-B | ✅ stop CP-B · **W8-T1** | ✅ cleaning_preview · **W8-T1** |
| **Decision allowlist** | ✅ | ✅ | ❌ experimental | ❌ experimental |
| **Notify Card N** | ✅ | ✅ | ❌ | ❌ |
| **Maturity** | stable | stable | experimental · run path done | experimental · run path done |

---

## 版本記錄

| 版本 | 日期 | 變更 |
|------|------|------|
| v1.0 | 2026-06-10 | W6-T1 · Card A/B |
| v2.0 | 2026-06-10 | W7-T4 · Card C/D/N + A/B run path 增量 |
| v2.1 | 2026-06-10 | W8-T1 · Card C/D experimental run path profiles |

---

*SKILL-CARDS-v2 · W7-T4 · 2026-06-10*
