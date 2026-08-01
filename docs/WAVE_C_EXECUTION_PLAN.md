# Wave C1 Execution Plan — AI Workflow 偵錯與健檢服務

> **票號**：C1-P2 · Execution Plan / Runbook v0.1  
> **性質**：對內操作流程指南（承接 C1-P1 Product Spec §5 high-level steps）  
> **前提**：Wave B-Final 已交付（B-F1 Skill Catalog、B-F3 Routing Policy）  
> **權威索引**：`docs/SKILL_CATALOG_OVERVIEW.md`（tool_id）、`docs/ROUTING_POLICY_GUIDE.md`（route_id）

---

## 概述

本文件將 C1-P1 Product Spec 的 §5 high-level 流程詳化為**可執行的操作步驟**，供內部執行者（Implementer / 分析師）依序執行。每個步驟包含：

- **目的**：本步要做什麼
- **對應 Product Spec**：與 §2 Input、§3 Deliverables、§5 Steps 的對照
- **相關 tool_id / route_id**：使用哪個 Gov Tool Catalog 工具或 Routing Policy 路由
- **輸入**：需要準備的檔案或參數
- **輸出**：本步產生的產物
- **CLI 範例**：可複製貼上的命令（人工執行）
- **人工判讀點**：標註哪些輸出需要人工判讀（非全自動化）

---

## Step 0 — Intake（接案與輸入盤點）

### 目的
確認調查目標、時間窗、環境，檢查客戶提供的輸入是否滿足 C1-P1 §2.1 Minimum Requirements。

### 對應 Product Spec
- §2.1 必備輸入（工作流樣本紀錄、trace 日誌、調查目標、程式庫存取授權）
- §2.4 前置假設（可匯出 eval_export/v1 或 gov-trace-v2）

### 輸入檢查清單

| 輸入項目 | 格式 | 檢查命令 | 備註 |
|---------|------|---------|------|
| 工作流樣本紀錄 | `ibridge` 或相容 JSONL | `head -5 <file>.jsonl` | 至少含 `gate_result`、`task_id` |
| Trace 日誌（建議） | gov-trace-v2 JSONL | `head -5 <file>.jsonl` | 需與樣本時間窗重疊 |
| 調查目標 | 文字描述 | — | 例如：「為何 infra_risk 標籤升高？」 |
| Index scope（可選） | 路徑清單或 scope JSON | `cat scope.json` | KB index 健檢時需要 |

### 工具驗證（內部自檢）

```bash
# 驗證 Gov Tool Catalog 可讀（非客戶必跑）
python -m skills.gov_tool_registry list

# 驗證 Routing Policy 可讀（非客戶必跑）
python -m core.routing_policy_loader validate
```

### 輸出
- Intake 摘要（記錄於工作筆記）：
  - 調查目標：`<文字>`
  - 時間窗：`<start> ~ <end>`
  - 環境：`dev` / `staging` / `shadow`
  - 輸入缺口：`<無 / 缺 trace / 缺 scope>`
  - 降級聲明（若輸入不足）：`<degraded scope 說明>`

### 人工判讀點
- [ ] 確認輸入缺口是否影響交付範圍（參考 Product Spec §2.4 降級說明）
- [ ] 與客戶確認調查目標優先級（Gate / Trace / Index）

---

## Step 1 — 工具選擇與路徑規劃

### 目的
依據調查目標與 C1-P1 §3.1 標準交付包，選擇本次要執行的 tool_id / route_id 組合。

### 對應 Product Spec
- §3.1 標準交付包（Eval 健檢報表、WF 健康總覽、Flagged 個案追查、Trace 深查、Index 狀態側車、RAG smoke）
- §4.1 適用場景（品質退化調查、單案追溯、知識層就緒檢查、跨域一頁總覽）

### 典型工具組合

| 調查目標類型 | 建議工具組合 | route_id（參考） |
|-------------|-------------|-----------------|
| **品質退化調查** | `obs.eval.export` → `obs.eval.report` → `obs.wf.status_summary` | `wave_b.eval_report` |
| **單案追溯** | `obs.eval.correlate`（triage-md） → `obs.trace.query` | — |
| **知識層就緒檢查** | `kb.index.bootstrap` → `kb.index.rag_smoke` → `obs.wf.status_summary` | `wave_b.kb_index_bootstrap` |
| **完整健檢** | 以上全部 + `obs.wf.status_summary` 總覽 | 組合執行 |

### 工具詳細對照

| tool_id | 用途 | 對應 Product Spec 交付物 |
|---------|------|-------------------------|
| `obs.eval.export` | 匯出 ibridge → eval JSONL | 輸入前處理 |
| `obs.eval.report` | 產出 Eval 健檢報表 | §3.1 Eval 健檢報表 |
| `obs.eval.correlate` | Flagged eval 列 join trace | §3.1 Flagged 個案追查 |
| `obs.eval.stats` | Tag 分佈統計 | §3.2 可選統計附錄 |
| `obs.trace.query` | Trace 深查 | §3.1 Trace 深查摘要 |
| `obs.wf.status_summary` | WF 健康總覽 | §3.1 WF 健康總覽 |
| `kb.index.bootstrap` | KB index bootstrap | §3.1 Index 狀態側車 |
| `kb.index.rag_smoke` | Manifest RAG smoke | §3.1 RAG smoke 結果 |

### 輸出
- 工具執行計畫（記錄於工作筆記）：
  - 選定 tool_ids：`[<列表>]`
  - 執行順序：`<線性或分支>`
  - 預計產出：`artifacts/eval/`、`artifacts/wf/`、`index_status_*.json`

### 人工判讀點
- [ ] 根據輸入缺口調整工具組合（缺 trace 則 skip correlate/trace.query）
- [ ] 確認客戶授權範圍與 Index scope 對齊

---

## Step 2 — 執行 Wave B 工具

### 目的
依 Step 1 計畫，人工執行各個 Gov Tool CLI，產生中間產物。

### 對應 Product Spec
- §5 Step 1–3（Eval 健檢、Trace 對齊、Index 健檢）的詳化執行

### Step 2.1 — Eval 健檢（Gate）

**相關 tool_id**：`obs.eval.export` → `obs.eval.report`

```bash
# 2.1.1 匯出 eval（含可選 kb_index_status sidecar）
GOV_EVAL_EXPORT_KB_INDEX_STATUS=1 \
  python -m observability.eval_exporter \
  tests/fixtures/eval/ibridge_records.jsonl \
  --case-index-map tests/fixtures/eval/case_index_map_W2-1.json \
  -o artifacts/eval/eval_export_sample.jsonl

# 2.1.2 產出 Eval 報表
python -m observability.eval_report \
  artifacts/eval/eval_export_sample.jsonl \
  --out-dir artifacts/eval
```

**輸入**：
- `ibridge_records.jsonl`（客戶提供或 fixture）
- `--case-index-map`（可選，for kb_index_status sidecar）

**輸出**：
- `artifacts/eval/eval_export_sample.jsonl`
- `artifacts/eval/eval_report.latest.md`
- `artifacts/eval/eval_report.latest.json`

**驗證**：
```bash
python -m unittest tests.test_eval_exporter tests.test_eval_report -v
```

---

### Step 2.2 — Trace 對齊與追查

**相關 tool_id**：`obs.eval.correlate` → `obs.trace.query`

```bash
# 2.2.1 Correlate flagged eval 列到 trace
python -m observability.eval_trace_correlate \
  --eval artifacts/eval/eval_export_sample.jsonl \
  --trace tests/fixtures/trace/sample_traces.jsonl \
  --format triage-md \
  -o artifacts/eval/correlate_triage.md

# 2.2.2 對特定 trace_id 深查（需要時）
python -m observability.trace_query \
  --file tests/fixtures/trace/sample_traces.jsonl \
  --trace-id trace-wb-fixture-001 \
  --format triage
```

**輸入**：
- `eval_export_sample.jsonl`（Step 2.1 產出）
- `sample_traces.jsonl`（客戶提供或 fixture）
- `--trace-id` / `--task-id`（已知問題單）

**輸出**：
- `correlate_triage.md`（Markdown triage 附錄）
- Trace query 終端輸出（或 `--output` 指定檔案）

**驗證**：
```bash
python -m unittest tests.test_eval_trace_correlate tests.test_trace_query -v
```

---

### Step 2.3 — Index 健檢（可選）

**相關 tool_id**：`kb.index.bootstrap` → `kb.index.rag_smoke`

```bash
# 2.3.1 Bootstrap index（限定 scope）
python -m workflow_v2.kb.repo_index_bootstrap \
  --scope-json workflow_v2/kb/wave_b_gov_scope.json \
  --output-dir workflow_v2/20_pilot/W3-B \
  --manifest workflow_v2/20_pilot/W3-B/index_manifest_W2-1.json

# 2.3.2 RAG smoke（驗證 manifest）
python -m workflow_v2.kb.rag_index_smoke \
  --manifest workflow_v2/20_pilot/W3-B/index_manifest_W2-1.json \
  --index-dir workflow_v2/20_pilot/W3-B/index_W2-1 \
  --output workflow_v2/20_pilot/W3-B/smoke_result.json
```

**輸入**：
- `wave_b_gov_scope.json`（scope 定義）
- 客戶授權之 repo 子樹路徑

**輸出**：
- `index_manifest_W2-1.json`
- `index_status_W2-1.json`（`file_count`、`chunk_count`、`kb_index_status`）
- `smoke_result.json`

**驗證**：
```bash
python -m unittest tests.test_kb_index_bootstrap -v
```

---

### Step 2.4 — 綜合總覽

**相關 tool_id**：`obs.wf.status_summary`

```bash
python -m observability.wf_status_summary \
  --eval artifacts/eval/eval_export_sample.jsonl \
  --index-status workflow_v2/20_pilot/W3-B/index_status_W2-1.json \
  --trace-jsonl tests/fixtures/trace/sample_traces.jsonl \
  --out-dir artifacts/wf
```

**輸入**：
- `--eval`（Step 2.1 產出）
- `--index-status`（Step 2.3 產出，可選）
- `--trace-jsonl`（客戶提供，可選）

**輸出**：
- `artifacts/wf/wf_status_summary.latest.md`
- `artifacts/wf/wf_status_summary.latest.json`

**驗證**：
```bash
python -m unittest tests.test_wf_status_summary -v
```

---

### 人工判讀點（Step 2 全階段）

- [ ] Eval report：`needs_review` 比例是否超過客戶預期閾值？
- [ ] Correlate triage：哪些 flagged case 需要人工優先審查？
- [ ] Trace query：異常事件鏈是否需要截圖/進一步深查？
- [ ] Index status：`file_count`/`chunk_count` 是否符合預期 scope？
- [ ] RAG smoke：manifest 關鍵字命中率是否可接受？
- [ ] WF summary：Gate/Index/Trace join 是否揭示明確問題模式？

---

## Step 3 — 彙整戰報草稿

### 目的
將 Step 2 產出的所有 artifacts 整理成一份可供內部 review 的戰報草稿。

### 對應 Product Spec
- §3.1 標準交付包（彙整為單一戰報）
- §5 Step 4–5（綜合總覽、交付與交接）

### 戰報草稿結構

```markdown
# AI Workflow 健檢戰報 · <case_id> · 草稿

## 摘要
- 調查目標：<文字>
- 時間窗：<start> ~ <end>
- 環境：<dev/staging/shadow>
- 整體評估：<healthy/at_risk/degraded>

## Gate 健檢（Eval）
- 樣本數 N：<數字>
- needs_review 比例：<百分比>
- top tags：<列表>
- 詳見：`artifacts/eval/eval_report.latest.md`

## Trace 追查
- flagged case 數：<數字>
- correlate 命中率：<百分比>
- 高優先審查 case：<列表>
- 詳見：`artifacts/eval/correlate_triage.md`

## Index 就緒（可選）
- kb_index_status：<ready/stale/missing>
- file_count：<數字>
- chunk_count：<數字>
- RAG smoke：<pass/fail>
- 詳見：`workflow_v2/20_pilot/W3-B/index_status_W2-1.json`

## WF 健康總覽
- 引用：`artifacts/wf/wf_status_summary.latest.md`

## 執行證據索引
### 可重跑命令
<!-- 貼上 Step 2 實際執行的 CLI（脫敏後）-->

### 驗證狀態
- [ ] eval_export：ok
- [ ] eval_report：ok
- [ ] correlate：ok
- [ ] wf_summary：ok
- [ ] index_bootstrap：（可選）ok

## 建議分級
### 立即（blocking）
- <項目>

### 短期（index stale 等）
- <項目>

### 路線圖（Wave C 能力）
- <項目>

## 缺口與假設
- <輸入缺口、判讀假設>
```

### 輸入
- Step 2 所有 artifacts（`artifacts/eval/*`、`artifacts/wf/*`、`workflow_v2/20_pilot/W3-B/*`）
- Intake 摘要（Step 0）
- 人工判讀筆記

### 輸出
- `reports/draft_ai_workflow_diagnostic_<case_id>_<timestamp>.md`

### 人工判讀點
- [ ] 確認所有 artifact 路徑正確引用
- [ ] 確認「建議分級」與客戶調查目標對齊
- [ ] 確認缺口與假設誠實揭露（參考 Product Spec §4.3）

---

## Step 4 — Internal Review 與最終報告

### 目的
由 Reviewer（人或 Reviewer chat）過目戰報草稿，產出最終報告。

### 對應 Product Spec
- §1.3 服務性質（investigation-only、不承諾修復）
- §4.2 限制（非 7×24 代維運、非 production SLA）

### Review Checklist

| 檢查項 | 標準 | 備註 |
|-------|------|------|
| 輸入完整性 | Intake 摘要完整 | Step 0 |
| 工具執行 | 所有 CLI 可重跑 | Step 2 verify_command |
| 產物存在 | 所有引用 artifact 存在 | 檔案系統檢查 |
| 誠實基線 | 未宣稱 Wave C 未實作能力 | 無 selector_gate prod 接線、無 dashboard |
| 缺口揭露 | 輸入缺口與假設已標註 | Product Spec §4.3 |
| 建議分級 | 立即/短期/路線圖清晰 | 客戶可執行 |

### Reviewer 指令（人工或 chat）

```markdown
你是 Reviewer。請審查這份 AI Workflow 健檢戰報草稿：

1. 檢查所有 artifact 引用是否正確（eval_report、correlate_triage、wf_summary、index_status）
2. 確認未宣稱未實作能力（如 kb.index.selector_gate prod 接線、Grafana dashboard）
3. 確認輸入缺口與假設已誠實揭露
4. 確認建議分級（立即/短期/路線圖）清晰可執行

結論：accepted / accepted_with_gaps / needs_changes
```

### 最終報告輸出

- 最終報告路徑：`reports/ai_workflow_diagnostic_<case_id>_<timestamp>.md`
- 附件打包：`artifacts/` 目錄壓縮
- 交付清單：
  - [ ] Eval 健檢報表（Markdown + JSON）
  - [ ] WF 健康總覽
  - [ ] Flagged 個案追查（triage-md，如適用）
  - [ ] Index 狀態側車（如適用）
  - [ ] RAG smoke 結果（如適用）
  - [ ] 執行證據索引（可重跑命令清單）

### 人工判讀點
- [ ] Reviewer 確認戰報品質
- [ ] 與客戶確認交付範圍與後續行動

---

## 附錄 A — Tool ID 快速索引

| tool_id | verify_command | 主要用途 |
|---------|---------------|---------|
| `obs.eval.export` | `unittest tests.test_eval_exporter` | Eval 匯出 |
| `obs.eval.report` | `unittest tests.test_eval_report` | Eval 報表 |
| `obs.eval.correlate` | `unittest tests.test_eval_trace_correlate` | Eval-trace join |
| `obs.eval.stats` | `unittest tests.test_eval_stats` | 統計分佈 |
| `obs.trace.query` | `unittest tests.test_trace_query` | Trace 深查 |
| `obs.wf.status_summary` | `unittest tests.test_wf_status_summary` | 總覽 |
| `kb.index.bootstrap` | `unittest tests.test_kb_index_bootstrap` | Index 啟動 |
| `kb.index.rag_smoke` | `unittest tests.test_kb_index_bootstrap` | RAG 驗證 |
| `kb.index.selector_gate` | `unittest tests.test_kb_index_selector_hook` | **skeleton only** |

---

## 附錄 B — Routing Policy 路由索引

| route_id | steps（tool_id 順序） | 用途 |
|---------|---------------------|------|
| `wave_b.eval_report` | `obs.eval.export` → `obs.eval.report` → `obs.wf.status_summary` | Eval 完整鏈 |
| `wave_b.kb_index_bootstrap` | `kb.index.bootstrap` → `kb.index.rag_smoke` | Index 完整鏈 |

---

## 附錄 C — 與其他文件關係圖

```
C1-P1 Product Spec（對外）
    │ §5 high-level steps
    ▼
WAVE_C_EXECUTION_PLAN.md（對內）
    │ Step 2 CLI 執行
    ▼
┌─────────────────┬─────────────────┬─────────────────┐
│ WAVE_B_EXECUTION_PLAN.md │ SKILL_CATALOG_OVERVIEW.md │ ROUTING_POLICY_GUIDE.md │
│ （各票交付與 CLI） │ （tool_id 權威） │ （route_id 編排） │
└─────────────────┴─────────────────┴─────────────────┘
```

---

## 附錄 D — 常見問題（FAQ）

### Q1: 客戶沒有 trace 日誌怎麼辦？
A: 依 Product Spec §2.4，trace 為「建議」非「必備」。Step 1 調整工具組合：skip `obs.eval.correlate` 與 `obs.trace.query`，改以 `obs.eval.report` + `obs.wf.status_summary` 為主。戰報中標註「trace join 缺失」。

### Q2: 客戶需要 Index 健檢但沒給 scope 授權？
A: 依 Product Spec §2.1，「程式庫存取」為必備。若無授權，Index 健檢降級為「scope 差距清單」交付（僅能說明需要哪些路徑，無法實際 bootstrap）。

### Q3: 可以自動執行整個 Step 2 嗎？
A: 目前 v0.1 為人工執行 CLI。自動化 pipeline 為 Wave C 後續票（見本檔 §Deferred）。

### Q4: `kb.index.selector_gate` 可以用嗎？
A: **不可以**。該 tool_id 在 B-F1 catalog 中標為 **skeleton**，僅供參考。實際 prod selector 接線為 Wave C 留項（見 Product Spec §3.3、§4.3）。

---

*文件版本：v0.1 · 2026-06-07 · C1-P2 Execution Plan*
