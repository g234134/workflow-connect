# Agent Lines README — Tabular Standard Line v2 × Non-Tabular Shadow Flow v1

> **版本**: v2.0 Wave 10 對齊更新版  
> **票號**: W11-T4 · agent-and-non-tabular-lines-readme-v2-wave10-aligned  
> **日期**: 2026-06-10  
> **適用對象**: 未來合作者、新加入 Agent、複習用快速入口  
> **閱讀時間**: 約 15 分鐘（快速瀏覽），30 分鐘（理解細節）
> **更新摘要**: 納入 W10-T1 CI Suite、W10-T2 Metrics、W10-T3 Audit、W10-T4 README v1 演進

---

## 系統現狀一句話摘要

**Tabular Agent Standard Line v2**（實驗線）已達 **~87% 自動化**（Wave 7 實測），支援 **multi-fixture**（4 案型：demo_phase、sampleco/2026-0001、additional_demo、sandbox_client）、**run 模式真執行**（S7–S10）、**HITL Checkpoint A/B**（W6-T5/T6）、**CI 整合**（W10-T1）、**Metrics 離線分析**（W10-T2）與 **Audit 快查**（W10-T3）。**Non-Tabular Shadow Flow v1**（Wave 9）已完成 **routing catalog**（W9-T1）、**decision rules v2 擴展**（W9-T2）、**tool catalog + selector stub**（W9-T3）、**preview orchestrator**（W9-T4），目前僅 preview/sandbox、無 heavy tools 執行。兩條線皆為實驗性質，不改 MVP 主鏈預設行為。

---

## §1 Overview：這兩條線是什麼，解決什麼問題

### 1.1 兩條線的定位

| 維度 | Tabular Agent Standard Line v2 | Non-Tabular Shadow Flow v1 |
|------|-------------------------------|---------------------------|
| **處理對象** | 結構化表格（CSV、里程碑匯出） | 非結構化/半結構化（文件、日誌、圖片、JSON blobs） |
| **Schema** | 固定欄位（`Phase`, `名稱`, `之前`, `現在`） | Schema-free / flexible / 讀時推斷 |
| **處理模型** | Row-level：過濾、映射、轉換 | Content-level：提取、解析、豐富化 |
| **成熟度** | Wave 7 達 **~87% 自動化**（實驗線 run path 穩定） | Wave 9 完成 preview/design（shadow 層） |
| **生產狀態** | 實驗線穩定（demo_phase / sampleco run path），主鏈未改 | 僅設計/預覽，**無 production 行為** |
| **Wave 10 新增** | CI Suite (W10-T1)、Metrics (W10-T2)、Audit (W10-T3) | —（維持 preview） |

### 1.2 解決的問題

**Tabular Line** 解決「重複性 CSV 清洗交付」的痛點：
- 客戶每週/每月匯出相同格式里程碑，人工清洗耗時
- 需要可重現的決策邏輯（哪些行保留、哪些欄位改名）
- 需要品質閘門（刪除比例過高時人工確認）
- **Wave 10 新增**：需要 CI 驗證、metrics 觀測、audit 追蹤

**Non-Tabular Shadow** 解決「下一個邊界」的探索：
- 客戶開始上傳混合格式文件夾（PDF報告、截圖、日誌）
- 不適合硬編成表格 schema
- 需要驗證「內容提取→結構化→交付」的治理模式能否沿用

### 1.3 與主鏈的關係

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Gov Core / HQ 總部                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │  Tabular    │  │ Non-Tabular │  │   Gov Core  │                  │
│  │  MVP 主鏈   │  │ Shadow Flow │  │   Smoke     │                  │
│  │  (stable)   │  │ (preview)   │  │   (infra)   │                  │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┘                  │
│         │                │                                          │
│         └────────────────┼────────────────────────────────          │
│                          ▼                                          │
│              ┌─────────────────────┐                                │
│              │   Agent Lines CI    │  ← W10-T1 合併驗證入口         │
│              │   (W10-T1)          │  ← 可選 PR / nightly           │
│              └─────────────────────┘                                │
│                          │                                          │
│              ┌───────────┴───────────┐                              │
│              ▼                       ▼                                │
│   ┌─────────────────┐    ┌─────────────────┐                        │
│   │ Metrics Extract │    │ Audit Quickview │                        │
│   │ (W10-T2)        │    │ (W10-T3)        │                        │
│   │ offline JSON/CSV│    │ read-only CLI   │                        │
│   └─────────────────┘    └─────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
```

**關鍵原則**：
- Tabular 實驗線 **不改 production 主鏈** 預設行為
- Non-Tabular **shadow** 表示：僅設計層，不寫入主鏈 outbox、不執行 heavy tools（OCR/解析器）
- Wave 10 CI/Metrics/Audit **皆為離線/可選工具**，不影響主鏈運行

---

## §2 Tabular Agent Standard Line v2

### 2.1 流程總覽（S1–S15）

Tabular 標準線將一次 CSV 清洗交付拆分為 **15 個步驟**，每步有明確的驅動者與決策權：

```
[S1 Intake] → [S2 Index] → [S3 Decision] → [S4 Checkpoint A] → [S5 Route] → [S6 Select]
  Human       Auto        Agent/HITL      Human (if triggered)   Auto      Auto

[S7 Gate] → [S8 Clean] → [S9 Outbox] → [S10 Bundle] → [S11 Guard] → [S12 Checkpoint B]
  Auto      Auto         Auto          Auto          Auto        Human (if triggered)

[S13 Approve] → [S14 Ledger] → [S15 Notify]
  Human         Auto         Agent (experimental)
```

### 2.2 Wave 7–10 實際狀態（v2）

| 步驟 | Wave 7 狀態 | Wave 10 狀態 | 成熟度 | 說明 |
|------|------------|--------------|--------|------|
| S1 Intake | human-only CLI | human-only CLI | stable | `scripts/new_cleaning_case.py` |
| S2 Index | auto | auto | stable | `scripts/build_cases_index.py` |
| S3 Decision | auto | auto | stable | `routing/intake_decision_rules_v1.py` / v2 |
| S4 Checkpoint A | HITL live | HITL live | stable | `hitl/checkpoint_a_integration_v1.py`；run 模式可寫 state |
| S5 Route | auto | auto | stable | `routing/intake_to_tabular_glue.py` |
| S6 Select | auto | auto | stable | `tools/tabular_tool_selector.py` |
| S7 Gate | auto（run path）| auto（run path）| stable | `validate.eligibility` 真執行 |
| S8 Clean | auto（run path）| auto（run path）| stable | `clean.phase_demo` 真執行 |
| S9 Outbox | auto（run path）| auto（run path）| stable | 寫入 `outbox/{case_ref}/` |
| S10 Bundle | auto（demo run）| auto（demo run）| stable | `export.delivery_bundle` 真執行 |
| S11 Guard | auto | auto | stable | live 讀取 `cleaning_stats.json` |
| S12 Checkpoint B | HITL live | HITL live | stable | `hitl/checkpoint_b_integration_v1.py` |
| S13 Approve | human-only | human-only | stable | `delivery_signoff.md` + index 手改；W8-T3 一鍵 CLI |
| S14 Ledger | auto | auto | stable | consumer 未完整接實驗線 |
| S15 Notify | experimental | experimental | experimental | `controlled_notify_experiment_v1.py` 模擬 only |

### 2.3 Run / Preview / HITL / Notify 如何合作

#### W4-GUARD-01: Experimental Fixture Guard（實驗性 Fixtures 防護閘門）

為防止 experimental fixtures（`additional_demo`, `sandbox_client`）**silent 進入主鏈**或被新人誤跑，regression 腳本現已加入 **fixture guard**：

| 情境 | 行為 | 錯誤訊息 |
|------|------|----------|
| 跑 stable fixtures（`demo_phase`, `sampleco`）| ✅ 正常執行，無需額外 flag | — |
| 未加 flag 直接跑 extended fixtures | ❌ **Guard blocked** | `experimental_fixture_requires_explicit_flag` |
| 加 `--include-extended-fixtures` | ✅ 允許執行 | — |

**為什麼這樣設計**：
- Experimental fixtures 成熟度為 `controlled_experimental`，品質與介面可能變動
- 新人應先熟悉 stable fixtures，理解輸出格式與預期行為後，再主動選擇執行 experimental
- Guard 提供明確錯誤訊息，指引用戶如何正確啟用

**CLI 範例**：
```bash
# 預設只跑 stable fixtures（demo_phase, sampleco）
python scripts/run_agent_standard_case_regression.py --run-mode run-all-allowed

# 明確啟用 experimental fixtures
python scripts/run_agent_standard_case_regression.py \
  --run-mode run-all-allowed --include-extended-fixtures
```

#### W4-GUARD G2–G4（opt-in · FP-G1-T3 · 預設關閉）

Schema／比例／`--strict-guards` 升格為**可開關**旁路；詳見 `docs/w4-guard-g2-g4-escalation-frame-v1.md`。

| 旗標 | 預設 | 行為 |
|------|------|------|
| （無） | off | 僅寫入 `guard_escalation` 觀測；**不**改 E2E exit |
| `--enable-guard-escalation` | off | 套用 G2／G3 `applied` recommendations |
| `--strict-guards` | off | G4：`pass_with_warnings` + G3 → E2E `ok=false` |

```bash
python scripts/run_case_e2e_validation.py --case-dir cases/sampleco/2026-0001 --json
python scripts/run_case_e2e_validation.py --case-dir cases/sampleco/2026-0001 --strict-guards --json
```

**禁止**：默升產線必開／required CI。

#### Preview 模式（無 side effect）
```bash
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode preview --format json
```
- 跑 S3 Decision → S5 Route → S6 Tool Path Preview → S11 Output Guard (mock)
- Checkpoint A/B 標示 `would_trigger`，但不寫入 outbox
- 用於快速驗證決策邏輯與工具規劃

**Run 模式（真執行，受控）**：
```bash
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode run --auto-approve-intake --format json
```
- `--auto-approve-intake`：跳過 S4 Checkpoint A（intake 已確認）
- 真執行 S7 Gate → S8 Clean → S9 Outbox → S10 Bundle
- S12 Checkpoint B 依 `output_guard` 狀態決定是否觸發

**Run Path Profile（Wave 7/8）**：

| case_ref | stop_at | 執行範圍 | experimental |
|----------|---------|---------|--------------|
| `demo_phase` | `bundle` | full chain (S7-S10) | no |
| `sampleco/2026-0001` | `checkpoint_b` | S7-S8 only，delivery 前停止 | no |
| `additional_demo` | `checkpoint_b` | S7-S8 (force clean) | **yes** |
| `sandbox_client` | `cleaning_preview` | S7 only (gate) | **yes** |

> **契約註（W4-REG suite）**：`--include-extended-fixtures` + `run-all-allowed` 下，`sandbox_client` 可為 **controlled fail**：`final_status=blocked`／`decision=needs_review`／`ok=false`，同時 `run_path_stop_at=cleaning_preview` 且 `guard_sanity_ok=true`（stable+`additional_demo` 仍須通過；≠ G2–G4 升格）。

**Controlled Notify（S15 實驗）**：
```bash
python scripts/run_controlled_delivery_notify_experiment.py \
  --case-dir cases/demo_phase --format json
```
- 讀取 `delivery_signoff.md` + bundle → 生成 notify payload
- **永遠** `external_dispatch=false`（硬編碼安全閘門）
- 輸出僅寫入 `outbox/{case_ref}/notify_experiment_*.json`

---

## §3 Non-tabular Shadow Flow v1

### 3.1 目前能做到的事情

Wave 9 實際交付（**preview-only，不執行 heavy tools**）：

```bash
# NT-A: 文件提取預覽
python scripts/run_non_tabular_experiment_preview.py \
  --task-type non_tabular.document.extract \
  --case-dir cases/_experiment_samples/nt_docu_stub \
  --format json

# NT-B: 日誌分析預覽
python scripts/run_non_tabular_experiment_preview.py \
  --task-type non_tabular.log.analyze \
  --case-dir cases/_experiment_samples/nt_log_stub \
  --format json
```

**實際輸出**：
- `decision`：v2 decision helper 的 `needs_review` / `auto_accept` / `reject`
- `planned_route`：`plan_non_tabular_route()` 規劃的 skill_card + notes
- `planned_tools`：symbolic tool names（`validate.content_accessible`, `extract.text_content`...）
- `selector_view`：selector stub 候選清單（全部標 `planned_only`）
- `outbox_path`：sandbox outbox JSON（僅 metadata，無敏感內容）

### 3.2 為什麼是「Shadow」

| 層面 | Tabular v2 | Non-Tabular v1 |
|------|-----------|----------------|
| **Routing catalog** | `routing/intake_routing_catalog_v1.yaml` 穩定 | `routing/non_tabular_routing_catalog_v1.yaml` skeleton |
| **Decision rules** | v1/v2 穩定，allowlist 驗證 | v2 支援 `non_tabular.*`，但僅 preview |
| **Tool executor** | 真執行（clean, bundle） | **stub only**，無 OCR/parser 實作 |
| **Outbox 寫入** | 真寫入 `outbox/{case_ref}/` | 僅 sandbox `outbox/non_tabular_experiment/` |
| **主鏈影響** | 不改主鏈，但 outbox 結構相同 | **完全隔離**，無主鏈 outbox 寫入 |
| **Cases 目錄** | `cases/demo_phase/`, `cases/sampleco/` | 僅 stub fixtures `cases/_experiment_samples/` |

**Shadow 的含義**：
1. **設計驗證**：驗證 S1-S15 流程框架能否適用於非表格資料
2. **治理沿用**：Checkpoint A/B HITL 模式直接繼承
3. **風險隔離**：任何 Non-Tabular 實驗不影響 Tabular 主鏈穩定性

### 3.3 Wave 9 實作狀態

| 票號 | 狀態 | 交付摘要 |
|------|------|----------|
| W9-T1 | implementer done · Reviewer pending | `routing/non_tabular_routing_catalog_v1.yaml` skeleton（3 entries: NT-A, NT-B, generic） |
| W9-T2 | implementer done · Reviewer pending | `routing/intake_decision_rules_v2.py` 支援 `non_tabular.*` 分支；NT-A/NT-B profile |
| W9-T3 | implementer done · Reviewer pending | `tools/non_tabular_tool_catalog_v1.json`（4 tools）；`select_non_tabular_tools` stub |
| W9-T4 | implementer done · Reviewer pending | `scripts/run_non_tabular_experiment_preview.py` preview CLI；sandbox outbox |

### 3.4 未來如何演進（Wave 11+）

**Wave 10 未變動**：Non-Tabular 維持 preview-only

**Wave 11+ 可能方向**（需尚書省裁決）：
- **Heavy tools 實作**：PDF text extraction (pdfminer/Tika)、OCR (Tesseract)、log parser
- **Fixture 真實化**：從 `cases/_experiment_samples/` 移到 `cases/docu-corp/`
- **Run path 解鎖**：執行 S7-S10 真實內容處理（需容量/安全評估）
- **與 Tabular 合流**：統一的 `cases/index.json`、共享 outbox schema

---

## §3.5 Non-Tabular Controlled Walkthrough (docu-corp + log-analytics-co)

> **票號**: W9-NT-CONTROLLED-WALKTHROUGH-V1  
> **目標**: 讓一線開發者可依序跑通 NT-A + NT-B controlled fixtures，得到可解讀 JSON 與 audit quickview。  
> **範圍**: preview-only；OCR / heavy execute 為 deferred（W9-T7/W12+）。

### 準備條件

1. **Repo 根目錄**: 所有命令假設執行於 `D:\大唐三省六部`（或你的 clone 路徑）。
2. **Python 環境**: 已安裝 `routing/`, `tools/`, `scripts/` 所需相依（如 `PyYAML`）。
3. **Fixtures 已就緒**: 確認 W9-T5/T6 fixtures 已落地（`cases/docu-corp/2026-0001/`、`cases/log-analytics-co/2026-0001/`）。

### 步驟 1–8：End-to-End 命令鏈

```bash
# Step 1: 確認 NT-A fixture 存在
ls cases/docu-corp/2026-0001/
cat cases/docu-corp/2026-0001/intake.json

# Step 2: 確認 NT-B fixture 存在
ls cases/log-analytics-co/2026-0001/
cat cases/log-analytics-co/2026-0001/intake.json

# Step 3: 驗證 NT-A 結構（unittest）
python -m unittest tests.test_non_tabular_fixture_docu_corp_v1 -v

# Step 4: 驗證 NT-B 結構（unittest）
python -m unittest tests.test_non_tabular_fixture_log_analytics_co_v1 -v

# Step 5: NT-A preview — Document Extraction
python scripts/run_non_tabular_experiment_preview.py \
  --task-type non_tabular.document.extract \
  --case-dir cases/docu-corp/2026-0001 --format json

# Step 6: NT-B preview — Log Analysis
python scripts/run_non_tabular_experiment_preview.py \
  --task-type non_tabular.log.analyze \
  --case-dir cases/log-analytics-co/2026-0001 --format json

# Step 7: NT-A audit quickview
python scripts/run_agent_audit_quickview.py \
  --case-ref cases_docu-corp_2026-0001 --format json

# Step 8: NT-B audit quickview
python scripts/run_agent_audit_quickview.py \
  --case-ref cases_log-analytics-co_2026-0001 --format json
```

### 預期輸出

**Step 3–4 (unittest)**: 各 4 tests OK
```
test_case_directory_structure ... ok
test_intake_required_keys_and_values ... ok
test_raw_documents_has_readable_sample ... ok  # 或 test_raw_server_logs_has_parseable_sample
test_v2_decision_nt_*_shadow_needs_review ... ok
```

**Step 5–6 (preview JSON)**: 關鍵字段
```json
{
  "ok": true,
  "flow_family": "non_tabular",
  "decision": {
    "decision": "needs_review",
    "risk_level": "medium",
    "fixture_profile_tier": "NT-A"  // 或 "NT-B"
  },
  "final_status": "preview_ready",
  "outbox_path": "outbox/non_tabular_experiment/YYYYMMDDTHHMMSSZ_*.json"
}
```

**Step 7–8 (audit quickview)**: 關鍵字段
```json
{
  "ok": true,
  "flow_family": "non_tabular",
  "latest_run": {
    "found": true,
    "source_kind": "non_tabular_experiment",
    "decision": "needs_review",
    "risk_level": "medium"
  },
  "checkpoint_a": { "on_disk": false },
  "checkpoint_b": { "on_disk": false }
}
```

### 錯誤排查提示

| 症狀 | 檢查項 | 修復 |
|------|--------|------|
| `ModuleNotFoundError` | Python path 是否包含 repo 根？ | `cd` 到 repo 根再執行 |
| `case_not_in_allowlist` | 使用正確 fixture 路徑？ | 確認 `--case-dir` 指向 `docu-corp/2026-0001` 或 `log-analytics-co/2026-0001` |
| `ok: false` (audit) | 已跑過 preview？ | 先執行 Step 5–6 產生 outbox |
| unittest failure | fixtures 被修改？ | 還原 `cases/*/intake.json` 為 W9-T5/T6 原始狀態 |

### Deferred 項目說明

- **OCR / PDF extraction**: `--with-metadata-extraction` 僅對 allowlisted NT-A 可用，實際內容提取（pdfminer/Tika）為 W9-T7 範圍，不在本 walkthrough。
- **Run mode (S7–S10)**: W12+ 才解鎖真執行；現階段僅 `preview_ready`。
- **Checkpoint A/B**: Non-Tabular shadow 無 HITL checkpoint（設計如此），故 `checkpoint_a/b.on_disk: false` 為預期行為。

---

## §4 CI / Metrics / Audit

### 4.1 CI 整合（W10-T1）

**Agent Lines CI Suite** 提供可選的 PR / nightly 驗證入口：

```bash
# 合併驗證兩條線（Tabular run-all-allowed + Non-Tabular preview）
python scripts/run_agent_lines_ci_suite.py --scope all --format json

# 僅 Tabular（含 extended fixtures）
python scripts/run_agent_lines_ci_suite.py --scope tabular --include-extended-fixtures

# 僅 Non-Tabular preview
python scripts/run_agent_lines_ci_suite.py --scope non_tabular
```

**CI 產出**：
- `outbox/agent_ci/<timestamp>_ci_summary.json`：合併摘要（`schema_version: agent_lines_ci_suite_v1`）
- `outbox/agent_experiment_regression/`：Tabular per-case artifacts
- `outbox/non_tabular_experiment/`：NT sandbox artifacts

**CI 邊界**：
- ❌ 不改 `scripts/run_mvp_mainline_regression.py`
- ❌ 不改 main-chain E2E / UI tests
- ❌ 不執行 NT heavy tools
- ✅ 可選 PR job，不強制 gate merge

### 4.2 Metrics（W10-T2）

**Agent Lines Metrics & Monitoring v1** 提供離線指標抽取：

```bash
# 預設：掃描 outbox/agent_experiment_regression/、outbox/agent_ci/、outbox/non_tabular_experiment/
python scripts/analyze_agent_lines_metrics.py

# JSON 輸出
python scripts/analyze_agent_lines_metrics.py --format json

# 不干預寫入（只讀預覽）
python scripts/analyze_agent_lines_metrics.py --no-write --format json
```

**指標清單**：

| 指標 | 來源 | 用途 |
|------|------|------|
| Decision accuracy | `intake_decision_rules_v*.py` output | 驗證 allowlist case 的決策穩定性 |
| Run path success rate | `run_agent_standard_case_regression.py` | Wave 7 run 模式成功率 |
| Checkpoint trigger rate | Checkpoint A/B JSON in outbox | HITL 介入頻率評估 |
| Removal ratio distribution | `cleaning_stats.json` | Output guard 閾值校準 |
| End-to-end latency | Experiment regression JSON | 從 intake 到 bundle 的耗時 |

**輸出檔案**：
- `outbox/agent_metrics/metrics_summary.json`：完整結構化摘要
- `outbox/agent_metrics/metrics_summary.csv`：扁平化表格（aggregate + by_source + by_case_ref）

**Metrics 邊界**：
- ✅ 純離線讀取 outbox JSON，無外部 monitoring 系統連線
- ❌ 不改 outbox writers（`run_agent_standard_case_regression.py` 等）
- ❌ 不整合 Prometheus / Langfuse / PG

### 4.3 Audit（W10-T3 · WB-T5 spec）

**Agent-Lines Audit Quickview** — 只讀審計快查；**正式契約 SSOT** 見  
[`docs/audit-quickview-and-case-history-spec-v1.md`](audit-quickview-and-case-history-spec-v1.md)（本 README **不** 雙維護 namespace 表／JSON 形狀）。

```bash
# 文字摘要（預設）
python scripts/run_agent_audit_quickview.py --case-ref demo_phase

# Wire JSON（agent_audit_quickview_v1；investigation view 見 spec §2.4）
python scripts/run_agent_audit_quickview.py --case-ref demo_phase --format json
```

**要點（詳見 spec）**：
- 追溯鏈：decision → route → CP-A → CP-B → delivery approval → outbox join
- 資料來源優先序：`agent_ci` > `agent_experiment_regression` > checkpoint JSON > tabular outbox（WB-T3 命名空間對齊）
- **investigation-only** — 非 production SLA；不取代 ticket STATE 權威（WA-T4）
- WB-T4 dashboard 可選消費 `audit_sections_found` / `audit_gaps_count`

**實作附錄**：`docs/agent-lines-audit-quickview-v1.md`（W10-T3 範例）

### 4.4 典型開發者流程

以下展示 Tabular Agent Standard Line 的典型開發者工作流程，結合 CI、Metrics、Audit 形成完整閉環：

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    典型開發者流程（Typical Developer Flow）               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. 開發階段（Development）                                              │
│     └── 修改 decision rules / tool selector / checkpoint 整合程式碼        │
│         └── 本地跑單測：python -m unittest tests.test_xxx -v               │
│                                                                         │
│  2. PR 提交（Pull Request）                                                │
│     └── 建立 PR → CI 自動觸發（可選）                                     │
│         └── python scripts/run_agent_lines_ci_suite.py --scope tabular     │
│             └── 驗證：demo_phase + sampleco preview/run 通過              │
│                 └── outbox/agent_ci/<timestamp>_ci_summary.json           │
│                                                                         │
│  3. Metrics 檢視（Wave 10-T2）                                             │
│     └── 合併後跑 metrics 分析                                             │
│         └── python scripts/analyze_agent_lines_metrics.py --format json  │
│             └── 檢視：error_rate、checkpoint_trigger_rate、duration        │
│                 └── outbox/agent_metrics/metrics_summary.json            │
│                                                                         │
│  4. Audit 追蹤（Wave 10-T3）                                               │
│     └── 客戶回報問題 → 需要追溯某 case 的完整歷史                          │
│         └── python scripts/run_agent_audit_quickview.py \               │
│               --case-ref demo_phase --format json                        │
│             └── 檢視：decision → route → CP-A → tools → CP-B → approval   │
│                 └── 所有步驟的時間戳、人工決策記錄、產物路徑              │
│                                                                         │
│  5. 持續監控（Ongoing）                                                    │
│     └── 定期跑 regression + metrics → 趨勢分析                            │
│         └── python scripts/run_agent_standard_case_regression.py \       │
│               --run-mode run-all-allowed --auto-approve-intake           │
│         └── python scripts/analyze_agent_lines_metrics.py               │
│             └── 比較不同 wave 的 error_rate、duration 趨勢                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**快捷命令參考**：

```bash
# PR → CI 驗證
python scripts/run_agent_lines_ci_suite.py --scope all --format json

# CI 結果檢視
cat outbox/agent_ci/*_ci_summary.json | jq '.ok, .tabular.ok, .non_tabular.ok'

# Metrics 分析
python scripts/analyze_agent_lines_metrics.py --format json
jq '.aggregate.error_rate, .aggregate.checkpoint_a_trigger_rate' \
  outbox/agent_metrics/metrics_summary.json

# Audit 追溯
python scripts/run_agent_audit_quickview.py --case-ref demo_phase
python scripts/run_agent_audit_quickview.py --case-ref sampleco/2026-0001 --format json
```

---

## §5 Governance & HITL

### 5.1 決策權分佈（人類 vs Agent）

**Tabular v2 15 步決策權矩陣**：

| 步驟 | 驅動者 | 決策者 | Wave 7–10 行為 |
|------|--------|--------|---------------|
| S1 Intake | Human | **Human** | 人工上傳 CSV + intake.json |
| S2 Index | Script | **Auto** | 自動更新 `cases/index.json` |
| S3 Decision | Agent | **Agent** | 依 rules 決定 `auto_accept/needs_review/reject` |
| S4 Checkpoint A | Agent + Human | **Human** | `needs_review` 時暫停，等待人工確認 |
| S5 Route | Script | **Auto** | 依 `task_type` → `planned_tools` |
| S6 Select | Agent | **Auto** | Tool selector 推薦 |
| S7-S11 | Script | **Auto** | Gate → Clean → Bundle → Guard |
| S12 Checkpoint B | Agent + Human | **Human** | `output_guard=warning` 時暫停 |
| S13 Delivery | Human | **Human** | `delivery_signoff.md` 確認；W8-T3 一鍵 CLI |
| S14 Ledger | Script | **Auto** | Index 更新（實驗線 partial）|
| S15 Notify | Script | **Agent** (experimental) | 模擬產生 payload，`external_dispatch=false` |

### 5.2 安全邊界與風險聲明

**五大禁止事項（憲法 §7 級）**：

| ID | 風險 | Safeguard | 位置 |
|---|------|-----------|------|
| **R1** | 錯接案（case 誤判） | Checkpoint A live + `needs_review` 不 auto_accept | `checkpoint_a_integration_v1.py` |
| **R3** | 錯清洗（資料損壞） | `removal_ratio>0.5` → Checkpoint B 強制 | `checkpoint_b_integration_v1.py` |
| **R4** | 錯交付（品質不符） | `output_guard.status=warning/blocked` 攔截 | S11 + S12 |
| **R6** | 通知誤送（資料外洩） | `external_dispatch=false` 硬編碼 + unittest | `controlled_notify_experiment_v1.py` |
| **R8** | Run path 越界（未授權執行） | `_RUN_PATH_PROFILES` allowlist，無 profile 不執行 | `run_agent_standard_case_experiment.py` |

**Non-Tabular 特有风险（R-NT1 ~ R-NT5）**：

| 風險 | 說明 | 現狀 safeguard |
|------|------|---------------|
| R-NT1 內容不可讀 | 損壞 PDF、加密文件 | Preview 階段 `validate.content_accessible` stub |
| R-NT2 內容安全 | 惡意程式碼、超大檔案 | Wave 9 僅 symbolic，無真實解析 |
| R-NT3 處理時間不可預測 | OCR、大文件耗時 | 僅 preview，無真執行 |
| R-NT4 品質難量化 | 文字提取準確度主觀 | 設計階段 `text_quality_score` 欄位，未實作 scorer |
| R-NT5 Schema drift | 文件格式版本演進 | Wave 9 僅 2 固定 stub fixtures |

**安全邊界速查表**：

```
┌─────────────────────────────────────────────────────────────────┐
│  Tabular v2（實驗線）                                           │
│  ├── 允許：preview（無 side effect）                              │
│  ├── 允許：run mode（auto-approve-intake 跳過 CP-A）            │
│  ├── 允許：執行 cleaning/bundle（有 outbox 寫入）                │
│  ├── 允許：CI Suite / Metrics / Audit（離線工具）                  │
│  └── 禁止：S15 external_dispatch=true（無批文）                   │
├─────────────────────────────────────────────────────────────────┤
│  Non-Tabular v1（Shadow）                                        │
│  ├── 允許：preview（僅 decision/route/select）                     │
│  ├── 允許：sandbox outbox（隔離目錄）                             │
│  ├── 允許：CI Suite 驗證 NT-A/NT-B preview（W10-T1）              │
│  ├── 允許：Metrics 掃描 NT sandbox artifacts（W10-T2）             │
│  ├── 允許：Audit 查詢 NT preview 產物（W10-T3）                    │
│  ├── 禁止：執行 heavy tools（OCR/parser）                         │
│  ├── 禁止：寫入 Tabular 主 outbox                                  │
│  └── 禁止：任意 case_dir（僅允許 stub fixtures）                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## §6 Roadmap：Wave 11+ 方向

> 以下為 **方向性規劃**，尚未開票，需尚書省/架構師評估後才會成為正式工單

### Wave 11（預估主題：穩定化 + Metrics/Audit 升格 + Tabular 擴面）

| 方向 | 目標 | 依賴 | 參考藍圖 |
|------|------|------|---------|
| Metrics dashboard | 自動化收集 §4.2 指標，產生趨勢圖，整合至本地 UI | W10-T2 穩定 30 天 | `docs/ninety-five-percent-automation-blueprint-v2.md` |
| Audit quickview 擴展 | 支援批次查詢、時間區間過濾、匯出報告 | W10-T3 穩定 | — |
| Tabular v2 → 主鏈 | 評估是否將實驗線併入 production | Wave 7/8/10 連續 60 天零 P0 | `docs/ninety-five-percent-automation-blueprint-v2.md` §6 |
| Extended fixtures 升格 | `additional_demo`, `sandbox_client` 進入穩定 allowlist | Wave 8 連續 50 次回歸全綠 | `docs/agent-standard-line-governance-view-v2.md` |
| CI Suite 強化 | nightly regression、自動 metrics 比對、趨勢告警 | W10-T1 穩定 | `docs/agent-lines-ci-suite-v1.md` |

### Wave 12+（預估主題：Non-Tabular 解鎖 + 跨家族統一）

| 方向 | 目標 | 前置條件 | 參考藍圖 |
|------|------|---------|---------|
| NT Heavy tools v1 | 實作 `extract.text_content` (PDF)、`parse.log_structure` | Wave 9 decision/glue/selector 穩定 30 天 | `docs/non-tabular-shadow-flow-blueprint-v1.md` §5 |
| NT Run path 解鎖 | 允許 S7-S10 真執行（容量限制：文件<100、日誌<1GB）| Heavy tools 穩定 + 資安審核 | `docs/non-tabular-shadow-flow-blueprint-v1.md` §6 |
| Unified outbox schema | Tabular + Non-Tabular 共用 outbox 結構 | 兩家族都達到 stable | `docs/non-tabular-shadow-flow-blueprint-v1.md` §6 |
| Resume framework | 實作 `--resume-from-checkpoint` CLI | Checkpoint A/B 累積足夠使用數據 | `docs/ninety-five-percent-automation-blueprint-v2.md` §6 G8-7 |

### 長期方向（未排期）

- **GraphRAG 整合**：Non-Tabular 提取的內容進入圖結構 RAG
- **Multi-modal**：圖片/音訊的內容處理（超出 Wave 9 NT-A/NT-B 範圍）
- **Client self-service**：S1 Intake 從 CLI 改為 Web UI（需大幅擴展認證/授權）
- **跨線統一 Metrics**：Tabular + Non-Tabular 共用 metrics schema
- **Audit 溯源強化**：與 Gov Core 主鏈 audit log 對接

### 藍圖參考索引

| 藍圖文件 | Wave 涵蓋 | 關鍵內容 |
|---------|---------|---------|
| `docs/ninety-five-percent-automation-blueprint-v2.md` | Wave 7–8 | S1–S15 v2 分佈、86.7% 自動化實測、Wave 8 缺口 G8-1–G8-10 |
| `docs/non-tabular-shadow-flow-blueprint-v1.md` | Wave 8–9 | S1-S15 對照表、Wave 9 建議票 W9-T1~T9、NT-A/NT-B Skill Cards |
| `docs/agent-standard-line-governance-view-v2.md` | Wave 7 | R6–R8 風險、Checkpoint A/B 整合、15 步決策權矩陣 |

---

## 附錄：快速索引

### 核心文件

| 主題 | 文件路徑 |
|------|----------|
| Tabular 標準線總結 | `docs/agent-standard-line-v1-summary.md` |
| 95% 自動化藍圖 v2 | `docs/ninety-five-percent-automation-blueprint-v2.md` |
| 治理觀點 v2 | `docs/agent-standard-line-governance-view-v2.md` |
| 實驗線驗收指南 | `docs/agent-run-experiment-eval-guide-v1.md` |
| Non-Tabular 藍圖 | `docs/non-tabular-shadow-flow-blueprint-v1.md` |
| Non-Tabular Routing | `docs/non-tabular-routing-catalog-v1.md` |
| Non-Tabular Preview | `docs/non-tabular-orchestrator-preview-v1.md` |
| CI 整合 | `docs/agent-lines-ci-suite-v1.md` |
| Metrics | `docs/agent-lines-metrics-and-monitoring-v1.md` |
| Audit spec (SSOT) | `docs/audit-quickview-and-case-history-spec-v1.md` |
| Audit appendix (W10-T3) | `docs/agent-lines-audit-quickview-v1.md` |
| 本 README v1 | `docs/agent-and-non-tabular-lines-readme-v1.md` |
| 本 README v2 (Wave 10) | `docs/agent-and-non-tabular-lines-readme-v2.md` |

### 核心命令速查

```bash
# Tabular 快速預覽
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp --case-dir cases/demo_phase \
  --mode preview --format json

# Tabular 受控執行
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp --case-dir cases/demo_phase \
  --mode run --auto-approve-intake --format json

# Tabular 全回歸
python scripts/run_agent_standard_case_regression.py \
  --run-mode run-all-allowed --auto-approve-intake --format json

# Non-Tabular Preview
python scripts/run_non_tabular_experiment_preview.py \
  --task-type non_tabular.document.extract \
  --case-dir cases/_experiment_samples/nt_docu_stub --format json

# CI 合併驗證（W10-T1）
python scripts/run_agent_lines_ci_suite.py --scope all --format json

# Metrics 分析（W10-T2）
python scripts/analyze_agent_lines_metrics.py --format json

# Audit 快查（W10-T3）
python scripts/run_agent_audit_quickview.py --case-ref demo_phase
python scripts/run_agent_audit_quickview.py --case-ref demo_phase --format json

# Checkpoint A/B 列表
python scripts/run_hitl_checkpoint_cli.py --list
```

### Wave Dashboard

進度總覽見：`docs/WAVE_PROGRESS_DASHBOARD.md`

---

*Agent and Non-Tabular Lines README v2 · W11-T4 · 2026-06-10 · Architect + Scribe*
