# Agent Lines README — Tabular Standard Line v2 × Non-Tabular Shadow Flow v1

> **版本**: v1.0 總覽文件  
> **票號**: W10-T4 · agent-and-non-tabular-lines-readme-v1  
> **日期**: 2026-06-10  
> **適用對象**: 未來合作者、新加入 Agent、複習用快速入口  
> **閱讀時間**: 約 15 分鐘（快速瀏覽），30 分鐘（理解細節）

---

## §1 Overview：這兩條線是什麼，解決什麼問題

### 1.1 兩條線的定位

| 維度 | Tabular Agent Standard Line v2 | Non-Tabular Shadow Flow v1 |
|------|-------------------------------|---------------------------|
| **處理對象** | 結構化表格（CSV、里程碑匯出） | 非結構化/半結構化（文件、日誌、圖片、JSON blobs） |
| **Schema** | 固定欄位（`Phase`, `名稱`, `之前`, `現在`） | Schema-free / flexible / 讀時推斷 |
| **處理模型** | Row-level：過濾、映射、轉換 | Content-level：提取、解析、豐富化 |
| **成熟度** | Wave 7 達 **~87% 自動化**（實驗線 run path 穩定） | Wave 9 僅 **preview/design**（shadow 層） |
| **生產狀態** | 實驗線穩定（demo_phase / sampleco），主鏈未改 | 僅設計/預覽，**無 production 行為** |

### 1.2 解決的問題

**Tabular Line** 解決「重複性 CSV 清洗交付」的痛點：
- 客戶每週/每月匯出相同格式里程碑，人工清洗耗時
- 需要可重現的決策邏輯（哪些行保留、哪些欄位改名）
- 需要品質閘門（刪除比例過高時人工確認）

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
│              │   Agent Lines CI    │  ← 可選合併驗證入口              │
│              │   (W10-T1)          │                                │
│              └─────────────────────┘                                │
└─────────────────────────────────────────────────────────────────────┘
```

**關鍵原則**：
- Tabular 實驗線 **不改 production 主鏈** 預設行為
- Non-Tabular **shadow** 表示：僅設計層，不寫入主鏈 outbox、不執行 heavy tools（OCR/解析器）

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

### 2.2 Wave 7 實際狀態（v2）

| 步驟 | Wave 7 狀態 | 成熟度 | 說明 |
|------|------------|--------|------|
| S1 Intake | human-only CLI | stable | `scripts/new_cleaning_case.py` |
| S2 Index | auto | stable | `scripts/build_cases_index.py` |
| S3 Decision | auto | stable | `routing/intake_decision_rules_v1.py` |
| S4 Checkpoint A | HITL live | stable | `hitl/checkpoint_a_integration_v1.py`；run 模式可寫 state |
| S5 Route | auto | stable | `routing/intake_to_tabular_glue.py` |
| S6 Select | auto | stable | `tools/tabular_tool_selector.py` |
| S7 Gate | auto | stable (run path) | `validate.eligibility` 真執行 |
| S8 Clean | auto | stable (run path) | `clean.phase_demo` 真執行 |
| S9 Outbox | auto | stable (run path) | 寫入 `outbox/{case_ref}/` |
| S10 Bundle | auto | stable (demo run) | `export.delivery_bundle` 真執行 |
| S11 Guard | auto | stable | live 讀取 `cleaning_stats.json` |
| S12 Checkpoint B | HITL live | stable | `hitl/checkpoint_b_integration_v1.py` |
| S13 Approve | human-only | stable | `delivery_signoff.md` + index 手改 |
| S14 Ledger | auto | experimental | consumer 未完整接實驗線 |
| S15 Notify | experimental | experimental | `controlled_notify_experiment_v1.py` 模擬 only |

### 2.3 Run / Preview / HITL / Notify 如何合作

**Preview 模式（無 side effect）**：
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

### 3.3 未來如何演進（Wave 9+ → Wave 10+）

**Wave 9 已交付**：
- W9-T1: Routing catalog skeleton (`non_tabular_routing_catalog_v1.yaml`)
- W9-T2: Decision rules v2 支援 `non_tabular.*` (`intake_decision_rules_v2.py`)
- W9-T3: Tool catalog + selector stub (`non_tabular_tool_catalog_v1.json`, `select_non_tabular_tools`)
- W9-T4: Preview orchestrator CLI (`run_non_tabular_experiment_preview.py`)

**Wave 10+ 可能方向**（需尚書省裁決）：
- **Heavy tools 實作**：PDF text extraction (pdfminer/Tika)、OCR (Tesseract)、log parser
- **Fixture 真實化**：從 `cases/_experiment_samples/` 移到 `cases/docu-corp/`
- **Run path 解鎖**：執行 S7-S10 真實內容處理（需容量/安全評估）
- **與 Tabular 合流**：統一的 `cases/index.json`、共享 outbox schema

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

### 4.2 Metrics（W10-T2 — 待實作）

規劃中的 metrics 觀測點：

| 指標 | 來源 | 用途 |
|------|------|------|
| Decision accuracy | `intake_decision_rules_v*.py` output | 驗證 allowlist case 的決策穩定性 |
| Run path success rate | `run_agent_standard_case_regression.py` | Wave 7 run 模式成功率 |
| Checkpoint trigger rate | Checkpoint A/B JSON in outbox | HITL 介入頻率評估 |
| Removal ratio distribution | `cleaning_stats.json` | Output guard 閾值校準 |
| End-to-end latency | Experiment regression JSON | 從 intake 到 bundle 的耗時 |

**Metrics 收集方式**：
- 解析 `outbox/agent_experiment_regression/` 下的 regression artifacts
- 讀取 `cases/*/reports/cleaning_stats.json`
- 統計 Checkpoint JSON 的 `created_at` / `resolved_at`

### 4.3 Audit（W10-T3 — 待實作）

規劃中的 audit 快速檢視：

```bash
# 檢視單一 case 的完整審計鏈
python scripts/audit_case_trace.py --case-ref demo_phase --from-date 2026-06-01

# 檢視 Checkpoint A/B 決策分布
python scripts/audit_checkpoint_summary.py --wave 7

# 檢視 Non-Tabular preview 使用情況（sandbox 日誌）
python scripts/audit_nt_preview_usage.py
```

**Audit 材料清單**：

| 類型 | 路徑 | 保留期限 | 內容 |
|------|------|---------|------|
| Run execution | `outbox/agent_experiment_regression/` | 90 days | `tool_results[]`, `final_status` |
| Regression artifact | `outbox/agent_experiment_regression/{ts}_{case}.json` | 90 days | Wave 6/7/8 回歸紀錄 |
| Notify experiment | `outbox/{case_ref}/notify_experiment_*.json` | permanent | `external_dispatch=false` 證據 |
| Live output guard | `cases/{case}/reports/cleaning_stats.json` | permanent | 品質閘門讀數 |
| Checkpoint A | `outbox/{case_ref}/checkpoint_A-intake-confirmation_*.json` | permanent | Human decision + resume_context |
| Checkpoint B | `outbox/{case_ref}/checkpoint_B-delivery-confirmation_*.json` | permanent | Delivery approval record |

---

## §5 Governance & HITL

### 5.1 決策權分佈（人類 vs Agent）

**Tabular v2 15 步決策權矩陣**：

| 步驟 | 驅動者 | 決策者 | Wave 7 行為 |
|------|--------|--------|------------|
| S1 Intake | Human | **Human** | 人工上傳 CSV + intake.json |
| S2 Index | Script | **Auto** | 自動更新 `cases/index.json` |
| S3 Decision | Agent | **Agent** | 依 rules 決定 `auto_accept/needs_review/reject` |
| S4 Checkpoint A | Agent + Human | **Human** | `needs_review` 時暫停，等待人工確認 |
| S5 Route | Script | **Auto** | 依 `task_type` → `planned_tools` |
| S6 Select | Agent | **Auto** | Tool selector 推薦 |
| S7-S11 | Script | **Auto** | Gate → Clean → Bundle → Guard |
| S12 Checkpoint B | Agent + Human | **Human** | `output_guard=warning` 時暫停 |
| S13 Delivery | Human | **Human** | `delivery_signoff.md` 確認 |
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
│  └── 禁止：S15 external_dispatch=true（無批文）                 │
├─────────────────────────────────────────────────────────────────┤
│  Non-Tabular v1（Shadow）                                        │
│  ├── 允許：preview（僅 decision/route/select）                   │
│  ├── 允許：sandbox outbox（隔離目錄）                             │
│  ├── 禁止：執行 heavy tools（OCR/parser）                        │
│  ├── 禁止：寫入 Tabular 主 outbox                                 │
│  └── 禁止：任意 case_dir（僅允許 stub fixtures）                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## §6 Roadmap Glimpse：Wave 11+ 的粗略方向

以下為 **方向性規劃**，尚未開票，需尚書省/架構師評估後才會成為正式工單：

### Wave 11（預估主題：穩定化 + Metrics/Audit 補全）

| 方向 | 目標 | 依賴 |
|------|------|------|
| Metrics dashboard | 自動化收集 §4.2 指標，產生趨勢圖 | W10-T2 設計定稿 |
| Audit quickview CLI | 實作 §4.3 審計命令 | W10-T3 設計定稿 |
| Tabular v2 → 主鏈 | 評估是否將實驗線併入 production | Wave 7/8 連續 30 天零 P0 |
| Extended fixtures 升格 | `additional_demo`, `sandbox_client` 進入穩定 allowlist | Wave 8 連續 50 次回歸全綠 |

### Wave 12+（預估主題：Non-Tabular 解鎖 + 跨家族統一）

| 方向 | 目標 | 前置條件 |
|------|------|---------|
| NT Heavy tools v1 | 實作 `extract.text_content` (PDF)、`parse.log_structure` | Wave 9 decision/glue/selector 穩定 30 天 |
| NT Run path 解鎖 | 允許 S7-S10 真執行（容量限制：文件<100、日誌<1GB） | Heavy tools 穩定 + 資安審核 |
| Unified outbox schema | Tabular + Non-Tabular 共用 outbox 結構 | 兩家族都達到 stable |
| Resume framework | 實作 `--resume-from-checkpoint` CLI | Checkpoint A/B 累積足夠使用數據 |

### 長期方向（未排期）

- **GraphRAG 整合**：Non-Tabular 提取的內容進入圖結構 RAG
- **Multi-modal**：圖片/音訊的內容處理（超出 Wave 9 NT-A/NT-B 範圍）
- **Client self-service**：S1 Intake 從 CLI 改為 Web UI（需大幅擴展認證/授權）

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
| 本 README | `docs/agent-and-non-tabular-lines-readme-v1.md` |

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

# CI 合併驗證
python scripts/run_agent_lines_ci_suite.py --scope all --format json

# Checkpoint A/B 列表
python scripts/run_hitl_checkpoint_cli.py --list
```

### Wave Dashboard

進度總覽見：`docs/WAVE_PROGRESS_DASHBOARD.md`

---

*Agent and Non-Tabular Lines README v1 · W10-T4 · 2026-06-10 · Architect + Scribe*
