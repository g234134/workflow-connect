# W5-A-RUNTIME-03-WORKBOARD-01 — W5-A runtime / ENF 工作總表

> **票號**：W5-A-RUNTIME-03-WORKBOARD-01
> **日期**：2026-05-31
> **覆蓋範圍**：W5_planning/ 下所有 W5-A-* 與 W5-D-* 相關文件 + repo 實作驗證
> **對象**：W5 尚書省 / Cursor / Hermes 協作
> **硬邊界**：只讀不寫 — 不修改任何 code / workflow / 規則 / fixture

---

## 1. 總覽

### 1.1 任務統計

| 軸 | 類別 | 總數 | Done | Todo | Deferred |
|----|------|------|------|------|----------|
| **W5-A** | Runtime (design + impl) | 12 | 12 | 0 | 0 |
| **W5-A** | Mining (analysis reports) | 4 | 4 | 0 | 0 |
| **W5-A** | 子總計 | **16** | **16** | **0** | **0** |
| **W5-D** | Plan + Design (Hermes) | 7 | 7 | 0 | 0 |
| **W5-D** | Implementation (Cursor) | 6 | 3 | 3 | 0 |
| **W5-D** | 跨類 (Catalog + Checklist + Templates) | 3 | 3 | 0 | 0 |
| **W5-D** | 子總計 | **16** | **13** | **3** | **0** |
| **合計** | | **32** | **29** | **3** | **0** |

**Done 率：90.6%**（29/32）；**剩餘 Todo：3 項**（全部是 Cursor-facing implementation）

### 1.2 Todo 清單

| 任務 ID | 類別 | 對象 | 預期目的 |
|---------|------|------|---------|
| W5-D-W4-FIX-A-IMPL | D — W4-FIX-A 實作 | Cursor | 修復 W4-A gate checklist 命名不一致、證據路徑錯誤、欄位衝突 |
| W5-D-W4-FIX-B-IMPL | D — W4-FIX-B 實作 | Cursor | W2-1_case index 真實回填（file_count>0）|
| W5-D-CI-GAP-1-IMPL | D — CI-GAP-1 實作 | Cursor | 新增 eval_exporter 步驟到 nightly CI，產出 eval_export JSONL |

---

## 2. 完整任務總表

### 2.1 W5-A — Runtime 軸（12 項）

| # | 任務 ID | 類別 | 對象 | 狀態 | 主要輸入 | 主要輸出 | 備註 |
|---|---------|------|------|------|---------|---------|------|
| 1 | **W5-A-RUNTIME-01-DRYRUN-PLAN-01** | runtime (design) | Hermes | **Done** | W4-A artefacts, eval shadow records | `W5-A-RUNTIME-01-DRYRUN_plan.md` | 設計 spec：scope、I/O、invariants、5-bucket governance rules、risk guards |
| 2 | **W5-A-RUNTIME-01-DRYRUN** | runtime (impl) | Cursor | **Done** | eval shadow JSONL | `tools/dryrun/core.py`, `observability/dryrun/` | 首條 runtime line。read-only dry-run CLI，產出 per_record JSONL + summary。✅ 已確認 repo 存在 |
| 3 | **W5-A-RUNTIME-02-LOGGING-FIRST-PLAN-01** | runtime (design) | Hermes | **Done** | RUNTIME-01 plan, PLAYBOOK | `W5-A-RUNTIME-02-LOGGING-FIRST_plan.md` | Logging-first 設計：「lights, not gates」。定義 L1-L6 boundaries |
| 4 | **W5-A-RUNTIME-02-LOGGING-FIRST** | runtime (impl) | Cursor | **Done** | RUNTIME-01 dry-run CLI | `tools/dryrun_ci_wrapper.py`, CI YAML [DRYRUN-LOG] step | ✅ CI YAML L357 已包含 `python -m tools.dryrun_ci_wrapper` step |
| 5 | **W5-A-RUNTIME-03-CI-DATA-PIPELINE-DESIGN-01** | runtime (design) | Hermes | **Done** | eval CI artefacts | `W5-A-RUNTIME-03-CI-DATA-PIPELINE-DESIGN-01.md` | 設計 prod shadow → CI spool pipeline。v0 fetch-fallback 設計 + maturity ladder |
| 6 | **W5-A-RUNTIME-03-CI-DATA-PIPELINE-IMPL-01** | runtime (impl) | Cursor | **Done** | shadow batch JSONL | `scripts/fetch_latest_shadow_batch.sh`, CI YAML fetch step | ✅ CI YAML L249 已包含 `bash scripts/fetch_latest_shadow_batch.sh` |
| 7 | **W5-A-RUNTIME-03-LIMITED-DENY-PLAN-01** | runtime (design) | Hermes | **Done** | PLAYBOOK, logging-first plan | `W5-A-RUNTIME-03-LIMITED-DENY_plan.md` | 設計 limited deny（Phase A preview → Phase B blocking）。Enforceability ladder L0/L1/L2、kill-switch |
| 8 | **W5-A-RUNTIME-03-ENF-PREVIEW** | runtime (impl) | Cursor | **Done** | MINING-01, limited-deny plan, dry-run output | `tools/enf_preview_wrapper.py`, CI YAML [GOV-ENF-PREVIEW] step | ✅ CI YAML L373 已包含 `python -m tools.enf_preview_wrapper` |
| 9 | **W5-A-RUNTIME-03-IBRIDGE-TAG-FIX-01** | runtime (verification) | Hermes | **Done** | MINING-03, ibridge_exporter.py | `W5-A-RUNTIME-03-IBRIDGE-TAG-FIX-01.md` | 驗證 ibridge_exporter tags 傳遞。發現根因在 dryrun/core.py 而非 ibridge |
| 10 | **W5-A-RUNTIME-03-IBRIDGE-TAG-FIX-BRIEF** | runtime (verification) | Cursor | **Done** | IBRIDGE-TAG-FIX-01.md | 無 code change（verification only）| Reassign: verify instead of fix. Pipeline 已正確 |
| 11 | **W5-A-RUNTIME-03-K2-TAGS-TRACE-01** | runtime (analysis) | Hermes | **Done** | 全鏈路 pipeline 檔案 | `W5-A-RUNTIME-03-K2-TAGS-TRACE-01.md` | Tags 全鏈路 trace。發現 3 個 break points + 2 個修復票建議 |
| 12 | **W5-A-RUNTIME-PLAYBOOK** | plumbing (pattern) | Hermes | **Done** | RUNTIME-01 plan, ticket templates | `W5-A-RUNTIME-PLAYBOOK.md` | 定義 reusable dry-run runtime pattern：B1-B7 boundaries、AC-DRY、5-step migration |

### 2.2 W5-A — Mining 軸（4 項）

| # | 任務 ID | 類別 | 對象 | 狀態 | 主要輸入 | 主要輸出 | 備註 |
|---|---------|------|------|------|---------|---------|------|
| 13 | **W5-A-RUNTIME-03-POLICY-MINING-01** | mining | Hermes | **Done** | dryrun per_record（2 runs）| Mining-01 報告 | 首輪 mining。C-01（ENF-RULE-1）→ L2 candidate。C-03（ENF-RULE-2）→ L1 advisory |
| 14 | **W5-A-RUNTIME-03-POLICY-MINING-02** | mining | Hermes | **Done** | dryrun per_record（3 runs）| Mining-02 報告 | 確認 ENF-RULE-1/2 0 FP。資料缺口未改善。建議 30-50 記錄後第三輪 |
| 15 | **W5-A-RUNTIME-03-POLICY-MINING-03** | mining | Hermes | **Done** | dryrun per_record（5 runs）+ 首批 prod-shadow | Mining-03 報告 | 首批真實 prod-shadow infra_risk 記錄。發現 ibridge tag 遺漏（C3-01）。ENF-RULE-1 維持強 L2 但不進 blocking |
| 16 | **W5-A-RUNTIME-03-POLICY-MINING-03.1** | mining | Hermes | **Done** | Post-fix per_record（dryrun_verify + AC2）| Mining-03.1 報告 | Tags 修復後 infra_risk 深度分析。C3-05 L1 warning 建議。ENF-RULE-1 條件調整不建議（100% FP） |

### 2.3 W5-D — Plumbing 軸（16 項）

| # | 任務 ID | 類別 | 對象 | 狀態 | 主要輸入 | 主要輸出 | 備註 |
|---|---------|------|------|------|---------|---------|------|
| 17 | **W5-D-W4-FIX-A-PLAN-01** | D — plan | Hermes | **Done** | gate checklist, runbook, CHK-W4 | `W5-D-W4-FIX-A_plan.md` | 分析 W4-A gate checklist 不一致。7 findings, 6-step fix, 6 AC |
| 18 | **W5-D-W4-FIX-A** | D — impl | Cursor | **⚠️ Todo** | gate checklist, run_records/ | 修復 checklist 命名/路徑/欄位衝突 | 預期目的：修復 GAP-W4-A1~A4。TODO：需實作 Step 1-7 |
| 19 | **W5-D-W4-FIX-B-PLAN-01** | D — plan | Hermes | **Done** | W2-1 index, sync/gate scripts | `W5-D-W4-FIX-B_plan.md` | 分析 W2-1_case index 真實回填需求。R1-R6 risks, V1-V8 AC |
| 20 | **W5-D-W4-FIX-B** | D — impl | Cursor | **⚠️ Todo** | W2-1_case/04_art_eng_ctx.md, index_status.json | index_status_W2-1.json 更新 | 預期目的：W2-1_case index file_count>0。需實作 Step 1-5 |
| 21 | **W5-D-W4-FIX-B-IMPLEMENTATION-01** | D — impl template | Cursor | **⚠️ Todo** | （同上）| impl template | Implementation template，非實際完成。W5_OVERVIEW 標 ✓ 但 template 未消 |
| 22 | **W5-D-FIXTURE-PROVENANCE-PLAN-01** | D — plan | Hermes | **Done** | eval_export_sample.jsonl, ibridge_records.jsonl | `W5-D-FIXTURE-PROVENANCE_plan.md` | line_index skew 分析。4 fix 選項（B+C 推薦） |
| 23 | **W5-D-FIXTURE-PROVENANCE** | D — impl | Cursor | **Done** | eval_export_sample.jsonl, schema docs | line_index fix + schema doc update | ✅ 已在 W5_OVERVIEW 標 ✓（FIXTURE-PROVENANCE-IMPLEMENTATION-01） |
| 24 | **W5-D-FIXTURE-PROVENANCE-IMPLEMENTATION-01** | D — impl template | Cursor | **Done** | eval_export_sample.jsonl | impl template | ✅ W5_OVERVIEW 確認完成 |
| 25 | **W5-D-SMOKE-FIXTURE-PROVENANCE-PLAN-01** | D — plan | Hermes | **Done** | smoke fixture files | `W5-D-SMOKE-FIXTURE-PROVENANCE_plan.md` | 同 FIXTURE-PROVENANCE 模式，針對 smoke fixtures |
| 26 | **W5-D-SMOKE-FIXTURE-PROVENANCE** | D — impl | Cursor | **Done** | smoke_eval_results.jsonl | line_index fix | ✅ W5_OVERVIEW 標 ✓（SMOKE-FIXTURE-PROVENANCE-IMPLEMENTATION-01） |
| 27 | **W5-D-CI-GAP-1-PLAN-01** | D — plan | Hermes | **Done** | eval pipeline, CI YAML | `W5-D-CI-GAP-1_plan.md` | CI-GAP-1 survey: eval_export/v1 無 CI producer。3 選項（A 推薦） |
| 28 | **W5-D-CI-GAP-1** | D — impl | Cursor | **⚠️ Todo** | eval-gate-ci.yml, eval_exporter.py | 新增 eval_exporter CI step | 預期目的：CI 可產出 eval_export JSONL。選 A：加入現有 nightly 步驟 |
| 29 | **W5-D-CI-GAP-CHECKLIST-01** | D — catalog | Hermes | **Done** | 全 W5-A/D 規劃 + repo | `W5-D-CI-GAP-CHECKLIST-01.md` | 16 CI/plumbing gaps survey。5 ✅ fixed, 8 ⚠️ unfixed, 2 🔍 pending |
| 30 | **W5-D-FIXTURE-CATALOG-01** | D — catalog | Hermes | **Done** | eval/shadow/gate fixtures | `W5-D-FIXTURE-CATALOG-01.md` | 20 JSON/JSONL files catalogued。5 fixture types, ~75-80 records |
| 31 | **W5_TICKET_TEMPLATES** | D — templates | Hermes | **Done** | control plane MVP, ticket memory template | `W5_TICKET_TEMPLATES.md` | W5-A/B/C 三種 ticket template |
| 32 | **W5-D-CI-GAP-1_IMPLEMENTATION_TEMPLATE** | D — impl template | Hermes | **Done** | CI YAML, eval exporter code | `W5-D-CI-GAP-1_IMPLEMENTATION_TEMPLATE.md` | CI-GAP-1 實作指引。8 AC, 3 options |

---

## 3. 關鍵任務短註解（P0/P1）

### 3.1 已完成的核心基礎設施

| 任務 ID | 影響說明 |
|---------|---------|
| **RUNTIME-01-DRYRUN** | 第一條 runtime line：read-only dry-run CLI，5-bucket governance。後續所有 MINING 報告的資料來源 |
| **RUNTIME-02-LOGGING-FIRST** | 在 nightly CI 嵌入 `[DRYRUN-LOG]` step，零風險開始收集治理觀測資料 |
| **RUNTIME-03-CI-DATA-PIPELINE-IMPL-01** | 解決 nightly CI 永遠只看 fixture 的 void loop 問題。prod shadow 資料優先，fixture fallback |
| **RUNTIME-03-ENF-PREVIEW** | `[GOV-ENF-PREVIEW]` step，ENF-RULE-1 (L2 candidate) + ENF-RULE-2 (L1 observation)。Phase A preview，exit 0 |
| **RUNTIME-03-IBRIDGE-TAG-FIX-01** + **K2-TAGS-TRACE-01** | 全鏈路 tags trace，確認 pipeline tags 傳遞正確。infra_risk 不再被丟失 |
| **DRYRUN-K2-TAG-PRESERVE-01** | dryrun/core.py `_normalize_export_row()` 合併原始 tags + synthetic tags。MINING-03.1 的基礎 |

### 3.2 Mining 報告鏈

| 報告 | 核心結論 |
|------|---------|
| **MINING-01** | C-01 (ENF-RULE-1) → 強 L2 candidate。C-03 (ENF-RULE-2) → L1 advisory |
| **MINING-02** | 0 FP/3 runs。資料缺口明顯：無 score<0.875、無 edge_unknown、僅 smoke fixture |
| **MINING-03** | 首批真實 prod-shadow (2 infra_risk)。發現 ibridge tag 遺漏。ENF-RULE-1 暫不進 blocking |
| **MINING-03.1** | Post-fix infra_risk 深度分析。C3-05 L1 warning 新建議。ENF-RULE-1 條件調整不建議 |

### 3.3 尚未處理的重大已知缺口

| 缺口 ID | 來源 | 影響 | 涉及 W5 軸 |
|---------|------|------|-----------|
| **nightly CI 無真實 prod 資料累積** | W5_OVERVIEW §⚠ | eval-shadow-nightly 永遠 bootstrap fixture。所有 MINING 報告的樣本來自本機手動執行。CI 自 2026-05-25 後無更新 | **W5-A** |
| **CI data pipeline 存活：缺少 upstream batch producer** | CI-GAP-CHECKLIST G3-G4 | fetch_latest_shadow_batch.sh 存在但上游無人放置 shadow batch → 每次都 fallback fixture | **W5-A** |
| **score<0.875 與 edge_unknown 零樣本** | 所有 MINING 報告 | 無法評估門檻值。ENF-RULE-1 的 score ≥ 0.7 條件無實際驗證 | **W5-A** |

---

## 4. 關鍵路徑分析（Critical Path）

### 4.1 目前狀態圖

```
[RUNTIME-01 DRYRUN] → [RUNTIME-02 LOGGING-FIRST] → [RUNTIME-03 ENF-PREVIEW]  
                                                           ↓
                                              [MINING-01/02/03/03.1] ← 4 輪 mining
                                                           ↓
                                              [IBRIDGE-TAG-FIX] + [K2-TAGS-TRACE]
                                                           ↓
                                              [DRYRUN-K2-TAG-PRESERVE]
                                                           ↓
                                              C3-05 L1 warning (建議，未實作)
                                              ENF-RULE-1 blocking (不建議)
                                              ─────────────────────────────
                                              3 項 W5-D Todo 等待實作
```

### 4.2 要進 W6 前最關鍵的瓶頸

| 瓶頸 | 狀態 | 阻礙 W6 的條件 |
|------|------|--------------|
| **Nightly CI 真實資料累積** | ❌ 斷鏈 | W6 的 deny engine 試點需要真實資料支撐。目前第 30 天仍會看到相同 fixture |
| **C3-05 L1 warning 實作** | ❌ 尚未實作 | 最簡單的 L1 rule，但需要設計 output 格式、整合到 enf_preview_wrapper |
| **CI-GAP-1: eval_exporter producer** | ❌ Todo | eval_export 無 CI producer → eval_stats 無 CI 資料 |
| **W4-FIX-A / B 清理** | ❌ Todo (2 項) | 雖然不直接 blocking 但影響 W5-D close-out 口徑 |

---

## 5. 文件-狀態對應索引

| 檔案 | 對應任務 | 角色 | 狀態 |
|------|---------|------|------|
| `W5-A-RUNTIME-01-DRYRUN_BRIEF_TASK_FOR_CURSOR.md` | RUNTIME-01 impl | Cursor brief | Done |
| `W5-A-RUNTIME-01-DRYRUN_plan.md` | RUNTIME-01 plan | Design spec | Done |
| `W5-A-RUNTIME-02-LOGGING-FIRST_BRIEF_TASK_FOR_CURSOR.md` | RUNTIME-02 impl | Cursor brief | Done |
| `W5-A-RUNTIME-02-LOGGING-FIRST_plan.md` | RUNTIME-02 plan | Design spec | Done |
| `W5-A-RUNTIME-03-CI-DATA-PIPELINE-BRIEF-FOR-CURSOR.md` | RUNTIME-03 CI impl | Cursor brief | Done |
| `W5-A-RUNTIME-03-CI-DATA-PIPELINE-DESIGN-01.md` | RUNTIME-03 CI design | Design spec | Done |
| `W5-A-RUNTIME-03-ENF-PREVIEW_BRIEF_TASK_FOR_CURSOR.md` | RUNTIME-03 ENF impl | Cursor brief | Done |
| `W5-A-RUNTIME-03-IBRIDGE-TAG-FIX-01.md` | Ibriage tag fix verification | Verification report | Done |
| `W5-A-RUNTIME-03-IBRIDGE-TAG-FIX-BRIEF-FOR-CURSOR.md` | Ibriage tag fix cursor brief | Cursor brief | Done |
| `W5-A-RUNTIME-03-K2-TAGS-TRACE-01.md` | K2 tags trace | Analysis report | Done |
| `W5-A-RUNTIME-03-LIMITED-DENY_plan.md` | Limited deny plan | Design spec | Done |
| `W5-A-RUNTIME-03-POLICY-MINING-01.md` | Mining 01 | Mining report | Done |
| `W5-A-RUNTIME-03-POLICY-MINING-02.md` | Mining 02 | Mining report | Done |
| `W5-A-RUNTIME-03-POLICY-MINING-03.md` | Mining 03 | Mining report | Done |
| `W5-A-RUNTIME-03-POLICY-MINING-03.1_INFRA-RISK.md` | Mining 03.1 | Mining report | Done |
| `W5-A-RUNTIME-PLAYBOOK.md` | RUNTIME-PLAYBOOK | Governance pattern | Done |
| `W5-D-CI-GAP-1_IMPLEMENTATION_TEMPLATE.md` | CI-GAP-1 impl | Impl template | Todo |
| `W5-D-CI-GAP-1_plan.md` | CI-GAP-1 plan | Plan card | Done |
| `W5-D-CI-GAP-CHECKLIST-01.md` | CI-GAP-CHECKLIST | Survey doc | Done |
| `W5-D-FIXTURE-CATALOG-01.md` | FIXTURE-CATALOG | Survey doc | Done |
| `W5-D-FIXTURE-PROVENANCE_BRIEF_TASK_FOR_CURSOR.md` | FIXTURE-PROVENANCE impl | Cursor brief | Done |
| `W5-D-FIXTURE-PROVENANCE_IMPLEMENTATION_TEMPLATE.md` | FIXTURE-PROVENANCE impl | Impl template | Done |
| `W5-D-FIXTURE-PROVENANCE_plan.md` | FIXTURE-PROVENANCE plan | Plan card | Done |
| `W5-D-SMOKE-FIXTURE-PROVENANCE_BRIEF_TASK_FOR_CURSOR.md` | SMOKE-FIXTURE impl | Cursor brief | Done |
| `W5-D-SMOKE-FIXTURE-PROVENANCE_plan.md` | SMOKE-FIXTURE plan | Plan card | Done |
| `W5-D-W4-FIX-A_IMPLEMENTATION_TEMPLATE.md` | W4-FIX-A impl | Impl template | **Todo** |
| `W5-D-W4-FIX-A_plan.md` | W4-FIX-A plan | Plan card | Done |
| `W5-D-W4-FIX-B_BRIEF_TASK_FOR_CURSOR.md` | W4-FIX-B impl | Cursor brief | **Todo** |
| `W5-D-W4-FIX-B_IMPLEMENTATION_TEMPLATE.md` | W4-FIX-B impl | Impl template | **Todo** |
| `W5-D-W4-FIX-B_plan.md` | W4-FIX-B plan | Plan card | Done |
| `W5_TICKET_TEMPLATES.md` | TICKET_TEMPLATES | Template doc | Done |

---

## 6. 剩餘工作與建議派工順序

### 6.1 建議的 Todo 處理順序

| 順位 | 任務 | 所屬 | 耗時估計 | 理由 |
|------|------|------|---------|------|
| **1** | **W5-D-CI-GAP-1-IMPL** | W5-D | 小（~0.5h）| 最簡單的 remaining Todo。僅新增一個 CI step |
| **2** | **W5-D-W4-FIX-A-IMPL** | W5-D | 中（~1-2h）| 7-step 但屬 doc-sync，無 code 風險 |
| **3** | **W5-D-W4-FIX-B-IMPL** | W5-D | 中（~1h）| 5-step。需 PowerShell 環境。可手動或下輪 Cursor |
| **4** | **C3-05-L1-INFRA-RISK-SUCCESS 實作** | W5-A | 小（~0.5h）| 最便宜的 L1 rule。10-15 行 enf_preview_wrapper.py 邏輯。可與 W6 一起排 |

### 6.2 已關閉的 deferred / 不建議項目

| 項目 | 原因 |
|------|------|
| ENF-RULE-1 → blocking canary | ❌ MINING-03/03.1 連續兩輪不建議。樣本不足 + pipeline 尚未累積真實資料 |
| ENF-RULE-1 前置條件放寬 | ❌ MINING-03.1 斷定會 100% FP |
| C3-02 needs_review + 任意 risk tag | ❌ 無樣本，post-fix 重新評估也未找到新案例 |
| C3-06 低分 + infra_risk | ❌ 無樣本 |
| C3-07 infra_risk + error_type + gate_ok | ❌ 無樣本 |
| deny engine runtime (G10-2 T3) | ❌ W5_OVERVIEW §3 明確留 W6+ |
| K-2 Phase 3-4 / 遠端 prod 自動 rollout | ❌ 超出 W5 scope |

---

## 7. 跨軸相依性圖

```
W5-A (Runtime/ENF) ─────────────────────── W5-D (Plumbing/Cleanup)
       │                                              │
       ├── DRYRUN CLI ◄────────────────────────────── CI-GAP-1 (eval_exporter CI 化)
       │       │                                              │
       │       └── MINING 01/02/03/03.1 ◄───── FIXTURE-CATALOG + CI-GAP-CHECKLIST
       │                                              │
       ├── LOGGING-FIRST (CI step) ◄────────────── FIXTURE-PROVENANCE (fixture 修正)
       │                                              │
       ├── CI-DATA-PIPELINE (fetch step) ◄────────── SMOKE-FIXTURE-PROVENANCE
       │                                              │
       ├── ENF-PREVIEW (CI step) ◄─────────────────── W4-FIX-A (gate checklist)
       │                                              │
       ├── IBRIDGE-TAG-FIX / K2-TAGS-TRACE ◄──────── W4-FIX-B (index real backfill)
       │
       └── C3-05 L1 warning (建議，未實作)
            ENF-RULE-1 blocking (不建議，等待 W6)
            
W5-C (Future) ─ G10-2 deny engine design (deferred to Wave 6+)
```

---

## 附錄 A — 驗證方法

本 workboard 的狀態判斷基於以下方法：

1. **計劃檔案判斷**：所有 `W5_planning/` 下文件的內容與 metadata
2. **Repo 實作驗證**：
   - `tools/dryrun/core.py` ✅ 存在
   - `tools/dryrun_ci_wrapper.py` ✅ 存在
   - `tools/enf_preview_wrapper.py` ✅ 存在
   - `scripts/fetch_latest_shadow_batch.sh` ✅ 存在
   - `observability/dryrun/README.md` ✅ 存在
   - `observability/enf-preview/README.md` ✅ 存在
   - `observability/shadow-pipeline/README.md` ✅ 存在
   - CI YAML L249 (fetch step) ✅ 存在
   - CI YAML L357 (dryrun CI wrapper) ✅ 存在
   - CI YAML L373 (enf preview wrapper) ✅ 存在
3. **W5_OVERVIEW.md 狀態整合**：§6 實戰進度確認
4. **未標記 Done 的項目**：`W5-D-W4-FIX-A_IMPLEMENTATION_TEMPLATE.md`、`W5-D-W4-FIX-B_BRIEF_TASK_FOR_CURSOR.md`、`W5-D-CI-GAP-1_IMPLEMENTATION_TEMPLATE.md` 在 planning 層級仍為 Todo。對應的 Cursor brief/template 未消

## 附錄 B — 版本歷史

| 版本 | 日期 | 變更說明 |
|------|------|---------|
| v0.1 | 2026-05-31 | 基於 W5_planning/ 全部 32 檔 + repo 實作驗證的首版 workboard。W5-A 全部 Done（16/16），W5-D 13/16 Done（3 Todo）。Todo 皆為 Cursor-facing impl。 |
