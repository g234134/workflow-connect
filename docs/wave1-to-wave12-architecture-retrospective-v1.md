# Wave 1–12 架構演進回顧 — Architecture Retrospective v1

> **角色**: Architect + Historian  
> **日期**: 2026-06-10  
> **目的**: 紀錄系統從「手動流程」到「多 fixture Agent 線 + Non-tabular shadow + CI/Metrics/Audit」的完整演變，為未來合作者提供決策脈絡。

---

## §1 Timeline Overview — Wave 1–12 一行摘要

| Wave | 主題 | 關鍵交付 | 狀態 |
|------|------|----------|------|
| **W1** | MVP 主鏈與治理收口 | Governance Constitution v1 · MVP trace path · Mainline regression | done |
| **W2** | Intake / Routing / Eval 基礎層 | Routing catalog v1 · Eval cases 骨架 | done |
| **W3-TL** | Tabular 工具層 | Catalog → Selector → Executor → Outbox Consumer 四件套 | 4/4 done |
| **W4** | Routing ↔ Tool Layer 銜接 | Glue layer · Eval runner · Intake tool path · CI hooks | 4/4 done |
| **W5** | Multi-Agent 協作 & Decision Helper | 四角色協作規格 · Intake decision rules v1 · HITL Checkpoints 設計 | T0/T1/T1B done |
| **W6** | Skill Card & Agent Standard Line | Skill Cards A/B · Skill Map 8 步驟 · 15 步實驗線設計 | T1–T9 多重 done |
| **W7** | Run Path · Fixtures · Controlled Notify | Extended fixtures C/D · Run mode coverage · v2 藍圖收斂 | T1–T4 done |
| **W8** | Experimental Run Paths · Non-Tabular 設計 | C/D run paths · Delivery approval CLI · **Shadow Flow 藍圖** | T1/T2/T3/T4 done |
| **W9** | Non-Tabular Shadow 實作起點 | Routing catalog · Decision rules v2 (NT-A/NT-B) · Tool selector stub | T1/T2/T3/T4 implementer done |
| **W10** | Agent Lines CI / Metrics / Audit | CI suite · Offline metrics · Audit quickview · README v1 | T1/T2/T3/T4 done |
| **W11** | Controlled Experimental & Lightweight NT | C/D 升格 controlled · NT lightweight content checks · Monthly report · README v2 | T1/T2/T3/T4 done |
| **W12** | **本回顧** | Architecture retrospective · Wave 13+ 風險預警 | **T4 進行中** |

---

## §2 Tabular 線演進 — 從 MVP → Standard Line v1/v2 → Controlled E2E

### 2.1 Wave 1: 奠基（Manual → Structured）

**起點問題**: 多 Agent 協作無標準節奏，互踩、假完成、無證據交付頻繁。

**關鍵決策**:
- 建立 **Governance Constitution v1**: 定義四流派工程法（Context/Source/Incremental/Debugging-Driven）
- 定義 **MVP Trace Path**: `demo_phase` + `sampleco/2026-0001` 兩個錨點案型
- 建立 **Mainline Regression**: `run_mvp_mainline_regression.py` 一鍵驗證 6/6 tests

**Trade-off**: 
- ✅ 穩定性: 錨點案型行為凍結，後續 Wave 不得修改
- ⚠️ 彈性: 僅支援固定 schema，新案型需開票擴展

### 2.2 Wave 2–4: Routing & Tool Layer（Modularization）

**演進脈絡**:

```
Wave 2: Routing Catalog (task_type → tool_family mapping)
    ↓
Wave 3-TL: Tabular Tool Layer (Catalog → Selector → Executor → Outbox)
    ↓
Wave 4: Glue Layer (Routing + Tool Layer 銜接)
```

**關鍵設計決策**:
1. **Catalog/Selector/Executor 分層**: 參考 K8s/ Terraform provider 模式，將「宣告」與「執行」分離
2. **Outbox 模式**: 工具執行結果寫入 `outbox/events.jsonl`，而非直接回傳，支援 replay/audit
3. **Glue Layer `plan_tabular_route()`**: 純 mapping 不執行，為 Wave 8+ non-tabular 預留同構擴展點

**Trade-off**:
- ✅ 可測試性: Selector/Executor 可獨立單元測試
- ⚠️ 延遲: Outbox 寫入增加 I/O，但換得可觀測性

### 2.3 Wave 5–7: Agent Standard Line（Experimentation）

**15 步實驗線設計 (S1-S15)**:

| 階段 | 步驟 | 權責 | HITL |
|------|------|------|------|
| Intake | S1-S3 | Agent | CP-A (Intake Confirmation) |
| Routing | S4-S6 | Agent | — |
| Execution | S7-S11 | Agent + Human | CP-B (Delivery Gate) |
| Delivery | S12-S15 | Human-led | Notify Experiment |

**關鍵決策**:
- **Skill Card 模板**: 10 欄位標準化（名稱/條件/輸入/路由/Selector/Executor/Outbox/DoD/失敗模式/HITL）
- **Fixture 成熟度分級**: `stable` (demo/sampleco) → `experimental` (C/D) → `controlled_experimental` (W11)
- **HITL Checkpoint A/B**: A=intake 確認，B=交付閘門，均為「檔案型 state + CLI」非改主鏈

**Trade-off**:
- ✅ 治理: 人類保留關鍵決策點（CP-A/CP-B），自動化率達 ~87%
- ⚠️ 複雜度: 多 fixture 管理成本上升

### 2.4 Wave 8–11: Controlled & CI（Productionization）

**演進里程碑**:

| Wave | 增量 | 意義 |
|------|------|------|
| W8-T1 | C/D `controlled_experimental` | 實驗 fixture 可受控執行至 CP-B |
| W8-T3 | Delivery Approval CLI | S13 一鍵交付確認 |
| W10-T1 | CI Suite | Tabular + Non-Tabular 合併驗證 |
| W11-T1 | C/D `controlled_experimental` 升格 | regression bundle probe |
| W11-T3 | Monthly Metrics Report | 離線 Markdown 報表 |

---

## §3 Non-Tabular 線演進 — 從 Blueprint → Shadow → Metadata → First Step

### 3.1 Wave 8-T4: Shadow Flow Blueprint（設計層 only）

**核心問題**: Tabular 線（CSV 結構化）無法處理 Document/Log/Image 等非結構化資料。

**設計決策**:
- **Shadow 定位**: 與 Tabular 主鏈並行，不修改既有 `run_mvp_mainline_regression.py`
- **沿用治理模式**: Checkpoint A/B、HITL、Audit log 格式全部沿用 Tabular 標準線
- **差異對照**:

| 維度 | Tabular v2 | Non-Tabular Shadow v1 |
|------|------------|----------------------|
| Input | CSV / 結構化表格 | Documents, logs, images, JSON blobs |
| Schema | Fixed columns | Schema-free / flexible |
| S3 Decision | `tabular.cleaning.mvp` rules | `non_tabular.*` family rules |
| S5 Route | `plan_tabular_route()` | `plan_non_tabular_route()` |
| S7-S8 | Row cleaners | Content processors |
| S11 Guard | `removal_ratio` | `extraction_coverage`, `quality_score` |

### 3.2 Wave 9: 實作起點（Skeleton First）

**Wave 9 票分佈**:

| 票號 | 內容 | 狀態 |
|------|------|------|
| W9-T1 | Routing catalog (NT-A/NT-B/generic) | implementer done |
| W9-T2 | Decision rules v2 擴展 non-tabular | implementer done |
| W9-T3 | Tool catalog + selector stub | implementer done |
| W9-T4 | Preview orchestrator CLI | implementer done |

**關鍵決策**:
- **Symbolic Tool Names Only**: W9-T3 僅定義 `non_tabular_tool_catalog_v1.json`，實際 heavy tools (OCR/log-parser) 延後
- **Stub 優先**: Selector 回傳 `planned_tools` 但不執行，驗證路由邏輯先行
- **NT-A/NT-B 案型**: Document Processing (NT-A) / Log Analysis (NT-B) 作為兩個 exemplar

**Trade-off**:
- ✅ 風險控制: 無 heavy tool 執行，避免資源耗盡
- ⚠️ 功能缺口: 僅 metadata-level processing，content 解析待 Wave 13+

### 3.3 Wave 10–11: Lightweight & Observability

**Wave 11-T2**: Non-Tabular Lightweight Content Checks
- 僅掃描 ext/size/pattern stats，不讀內容、不跑 OCR
- 作為 preview 階段快速拒絕明顯不合規案型

**Wave 10-T2/T3/T4**: Metrics / Audit / README
- 離線指標: `outbox/agent_metrics/` JSON + CSV summary
- 審計快查: `run_agent_audit_quickview.py` 聚合 regression/agent_ci/non-tabular artifact

---

## §4 Governance / HITL / Eval / CI / Metrics / Audit 演進

### 4.1 Governance 框架定型（Wave 1–5）

| 組件 | 首次出現 | 目的 |
|------|----------|------|
| 四流派工程法 | Wave 1 (Constitution) | 標準化 Agent 行為節奏 |
| 12-rule 行為合約 | Wave 1 | 強制規則：先讀後寫、最小觸及、dict 契約 |
| Multi-Chat 四角色 | Wave 5-T0 | Orchestrator/Implementer/Reviewer/Scribe 協作 |
| Ticket State 模板 | Wave 1 | FRAME/STATE/B_REPORT/C_REPORT/D_REPORT/O_NOTES |

### 4.2 HITL 模式演進

```
Wave 5-T2: Checkpoint A/B 設計 (design only)
Wave 5-T2B: Checkpoint 檔案型 state/events CLI
Wave 6-T5/T6: Checkpoint A/B Integration 層
Wave 8-T3: Delivery Approval CLI (S13 一鍵確認)
```

**設計原則**: 
- HITL 為「側車」不阻塞主鏈自動化
- Checkpoint 僅產生 `resume_context`，resume 動作由 Agent/人類顯式觸發

### 4.3 Eval / CI 整合

| Wave | 增量 |
|------|------|
| W2-T2 | Routing eval cases YAML (dry-run only) |
| W4-T4 | PR CI `eval-gate-ci.yml` routing eval dry-run step |
| W6-T7 | Experiment eval guide (三級成功定義/五階段 replay/六類失敗) |
| W10-T1 | Agent Lines CI Suite (Tabular + Non-Tabular 合併) |

**關鍵決策**: CI 僅執行 `--dry-run` 與 unittest，不執行實際 cleaning/bundle，避免污染 production data。

### 4.4 Metrics / Audit 離線化

- **Wave 10-T2**: `analyze_agent_lines_metrics.py` 讀取 regression/outbox JSON，產生 CSV + summary
- **Wave 11-T3**: `generate_agent_lines_monthly_report.py` 產生 Markdown 報表
- **設計原則**: 離線計算、不連外部 monitoring、僅讀 `outbox/agent_metrics/`

---

## §5 核心設計原則

### 5.1 Incremental / Skeleton First

> 「先骨架，後血肉」— 每 Wave 先定義 interface/schema/placeholder，再填充實作。

**案例**:
- Wave 9 Non-Tabular: 先有 catalog YAML → glue stub → selector stub → 未來才實際 OCR
- Wave 6 15 步實驗線: 先有 S1-S15 設計文件 → CP-A/B integration → run path profiles

### 5.2 可審計 / Outbox 模式

> 所有工具執行結果寫入 outbox，而非直接回傳，支援 replay 與 postmortem。

**Outbox 階層**:
```
outbox/
├── tabular_runs/{run_id}.json       # Wave 3-TL Executor 產出
├── agent_experiment_regression/      # Wave 6-8 experiment runs
├── non_tabular_experiment/           # Wave 9-11 NT preview
└── agent_ci/                         # Wave 10 CI merged summary
```

### 5.3 可回滾 / Fixture 錨點

> `demo_phase` + `sampleco/2026-0001` 為「行為凍結」錨點，後續 Wave 不得修改其 run path。

**Fixture 成熟度**:
| 等級 | 說明 | 代表 |
|------|------|------|
| `stable` | 主鏈錨點，行為凍結 | demo_phase, sampleco |
| `controlled_experimental` | 可 run 至 CP-B，但非 production | additional_demo, sandbox_client |
| `experimental` | 僅 preview，不執行 | NT-A/NT-B stubs |

### 5.4 Sandbox First / Shadow Flow

> Non-Tabular 採「Shadow」模式：與主鏈並行開發，不觸及 Tabular 既有行為。

**Shadow 原則**:
1. 不修改 `run_mvp_mainline_regression.py`
2. 不修改 `scripts/new_cleaning_case.py` intake 主鏈
3. 不新建 `cases/` production fixture（僅 `_experiment_samples/`）

### 5.5 Dict 契約 / 結構化回傳

> 核心路徑回傳 `dict`（`ok`, `message`, `data`），禁純自然語言代替。

---

## §6 未來風險與建議 — Wave 13+ 注意事項

### 6.1 風險 R1: Fixture 組合爆炸

**症狀**: Wave 11 已有 4 fixture (A/B/C/D) × 2 task_type (tabular/non-tabular) × 多 run mode (preview/run/dry-run)。

**建議**:
- Wave 13 引入 **Fixture Registry** 統一管理，避免散落 `cases/`
- 定義 `fixture_capabilities[]` 取代 hardcode `if case_ref in ["demo_phase", ...]`

### 6.2 風險 R2: Non-Tabular Heavy Tools 資源管理

**症狀**: Wave 9 僅 symbolic tool names，實際 OCR/log-parser 執行時可能耗盡 memory/disk。

**建議**:
- 引入 **Resource Quota** 層（pre-flight check: memory/timeout/page count）
- 與 DarkOps Infra 團隊協調 GPU/CPU 排程
- Wave 13+ 實作前，先開「資源隔離 PoC」票驗證

### 6.3 風險 R3: CI 時間膨脹

**症狀**: Wave 10 CI suite 已合併 Tabular + Non-Tabular，Wave 12+ 若加入更多 fixture，CI 時間可能 >10min。

**建議**:
- Wave 13 引入 **Tiered CI**:
  - Tier 1 (PR): unittest + 1 fixture smoke (< 3min)
  - Tier 2 (Merge): full regression + all fixtures (< 10min)
  - Tier 3 (Nightly): experiment runs + metrics analysis

### 6.4 風險 R4: Decision Rules 版本漂移

**症狀**: Wave 8 v2 引入 A/B/C/D profile，Wave 9 又擴展 NT-A/NT-B，`intake_decision_rules_v2.py` 邏輯複雜度上升。

**建議**:
- Wave 13 引入 **Decision Rules Registry** (YAML-based policy table)
- 分離 `routing_policy` (task_type → profile) 與 `decision_logic` (profile → verdict)
- 每 Wave 新增 profile 須附「漂移測試」：舊 case 行為不變

### 6.5 風險 R5: Metrics/Audit 資料累積

**症狀**: Wave 10-11 離線 metrics 寫入 `outbox/agent_metrics/`，長期累積可能達 GB 級。

**建議**:
- Wave 13 定義 **Retention Policy** (30/90/365 天分級)
- 區分「hot metrics」(最近 Wave) 與「cold archive」(歷史 Wave)
- 考慮 `metrics_archive/` 壓縮/清理機制

---

## §7 參考索引

| 文件 | 用途 |
|------|------|
| `docs/WAVE_PROGRESS_DASHBOARD.md` | Wave 1–11 完成度總覽 |
| `docs/ninety-five-percent-automation-blueprint-v2.md` | 95% 自動化藍圖 v2 |
| `docs/non-tabular-shadow-flow-blueprint-v1.md` | Non-Tabular Shadow 設計 |
| `docs/agent-run-experiment-eval-guide-v1.md` | 實驗線驗收/replay 指南 |
| `docs/skill-cards-v2.md` · `docs/skill-map-v2.md` | Skill Card/Map v2 |
| `04_Workflows/tickets/*_state.md` | 各 Wave 票級詳細記錄 |

---

*W12-T4 · Architecture Retrospective v1 · 2026-06-10*
