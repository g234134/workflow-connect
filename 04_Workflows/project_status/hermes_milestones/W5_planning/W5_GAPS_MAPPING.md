# W5 GAPS MAPPING — 已知 Gap → W5 軸分配

> **設計者**：WAVE5-PLANNING 專線（2026-05-31）
> **用途**：將 W0–W4 交付過程產生的所有已知缺口、P0/P1 gap、未完成子票、明確留後的項目，
>          系統性映射到 Wave 5 各軸（W5-A～W5-E）與建議子票。
> **來源**：`CHK-W4-WAVE4-CLOSURE.memory.md`（§W4-A/B/C Check Record）、
>           `00_master_plan.md`（§15.5 留後、§4 待辦）、
>           `90_run_queue.md`（W2-2/W2-3 TODO 子票、Future 占位）、
>           `99_latest_status.md`（風險表 R5~R10）。

---

## 缺口彙總表

| Gap ID | 描述 | 優先級 | 來源 | 建議歸屬 W5 軸 | 建議子票 | 建議狀態 |
|--------|------|--------|------|----------------|----------|----------|
| **GAP-W4-A1** | Gate checklist trace 鍵名（`step=shadow`/`canary`）與 `rollout_trace.jsonl` 細粒度 step 不一致 | P0 | CHK-W4 §W4-A GAP-1 | **W5-D** | W5-D-W4-FIX-A | **ready** |
| **GAP-W4-A2** | `08_art_rel_exec.json` → `rollback_path_valid: false` 與 checklist B6「須 true」衝突 | P0 | CHK-W4 §W4-A GAP-2 | **W5-D** | W5-D-W4-FIX-A | **ready** |
| **GAP-W4-A3** | `canary_cohort_state.json` 落點與 checklist C1 案卷根路徑不一致；rollback 未顯式回寫 cohort state | P1 | CHK-W4 §W4-A GAP-3 | **W5-D** | W5-D-W4-FIX-A | **ready** |
| **GAP-W4-A4** | 5 樣本 canary 實測 `cohort_in=0/5`（合法但無 in-cohort 樣本）；override 路徑無 `override_record.json` 證據 run | P1 | CHK-W4 §W4-A GAP-4 | **W5-D** | W5-D-W4-FIX-A（或 W5-A-COHORT-DESIGN） | **ready** |
| **GAP-W4-A5** | `90` 仍列 W3-A-SHADOW/CANARY/REL 等為 TODO，與 W4-A DONE（minimal v1）並存——隊列層級敘事需釐清 | P1 | CHK-W4 §W4-A GAP-5 | **W5-D** | W5-D-DOCSYNC-SOP（含 `90` 敘事對齊，非改 Status） | **planning** |
| **GAP-W4-B1** | `index_status.json` 的 file_count/chunk_count=0 — 樣本資料，非真實 indexing 結果 | P0 | CHK-W4 §W4-B GAP-1 | **W5-D** | W5-D-W4-FIX-B | **ready** |
| **GAP-W4-C1** | 僅 `local.jsonl` 含 metrics（未等待 nightly prod 自動運行）；fail-on-deny 未啟用（留 Wave 5+） | P1 | CHK-W4 §W4-C, `99` §1 | **W5-C** | W5-C-NIGHTLY-AUTO-VALIDATE, W5-C-FAIL-ON-DENY-DESIGN | **ready** |
| **GAP-W4-X1** | 自動多 chat／自動排程／自動 merge 未實現（§0 明確留 Wave 5+） | P2 | CHK-W4 §W4-X | **W5-E** | W5-E-REVIEWER-SOP（非實現自動化） | **planning** |
| **GAP-W2-2-HELPER** | `W2-2-HELPER-SCRIPTS`：AC grep helper 工程化（驗證腳本在乾淨環境可跑；補 CHG-GOV-DOC 以外票的 pattern） | P1 | `90_run_queue.md` Wave 2 | **W5-D** | W5-D-W2-2-HELPER | **ready** |
| **GAP-W2-2-QA** | `W2-2-QA-CHECKLIST`：no-blind-trust 清單工程化（NBT-T01～T07 → checker 可勾選表 / ART-QA-REV 字段建議） | P1 | `90_run_queue.md` Wave 2 | **W5-D** | W5-D-W2-2-QA-CHECKLIST | **ready** |
| **GAP-W2-3-PILOT** | `W2-3-GOV-RISK-PILOT`：試點案卷 ART-GOV-RISK 實例（仿 W2-1 RISK 段；替換 WR fallback） | P1 | `90_run_queue.md` Wave 2 | **W5-D** | W5-D-W2-3-PILOT | **ready** |
| **GAP-E1-6** | `03` 範例路徑與 `90` Output 對齊 | P1 | `99` §4 | **W5-D** | W5-D-E1-6 | **ready** |
| **GAP-FUTURE-DENY** | deny engine runtime (G10-2 T3) — Wave 5+ 長期項 | P2 → Future | `00` §15.5, `90` Future | **W5-C** | W5-C-FAIL-ON-DENY-DESIGN（僅設計，非實作） | **defer** |
| **GAP-FUTURE-AUTO** | 95% 自動化、全 IMP 機讀 enforcement、完整 release gate | Future | `00` §15.5 | — | — | **defer** |
| **GAP-FUTURE-K2-P3** | K-2 Phase 3–4／遠端 prod 自動 rollout | Future | `00` §15.5 | — | — | **defer** |
| **GAP-FUTURE-KB-FULL** | 知識層全庫級產品化（即時增量、多 tenant KB、替換 RAG 主路徑） | Future | `00` §15.5 | — | — | **defer** |
| **GAP-FUTURE-CTRL-AUTO** | 控制面自動化：自動開 chat、自動並行排程、自動 merge 決策 | Future | W4-X §0 | — | — | **defer** |
| **GAP-R5** | `ART-GOV-RISK` 案卷實例（中）— 與 GAP-W2-3-PILOT 重疊，但 `99` 另列此風險 | P1 | `99` §5 R5 | **W5-D** | W5-D-W2-3-PILOT（同一票） | **ready** |
| **GAP-R9** | K-2 遠端 prod／Phase 3+（中） | P2 | `99` §5 R9 | **W5-A** | W5-A-RUNTIME-01（首條 prod CI） | **planning** |
| **GAP-R8** | 完整 release gate / deny runtime（中） | P2 | `99` §5 R8 | **W5-C** | W5-C-FAIL-ON-DENY-DESIGN | **planning** |

---

## 按 W5 軸分組統計

| W5 軸 | P0 Gaps | P1 Gaps | P2 Gaps | Future |
|-------|---------|---------|---------|--------|
| **W5-A**（Rollout 擴面） | 0 | 0 | 1（R9） | 0 |
| **W5-B**（Index 擴面） | 0 | 0 | 0 | 0 |
| **W5-C**（Observability/Gov） | 0 | 1（GAP-W4-C1） | 1（GAP-FUTURE-DENY, GAP-R8） | 1 |
| **W5-D**（清理/閉環） | 2（GAP-W4-A1, GAP-W4-A2, GAP-W4-B1） | 7（GAP-W4-A3~A5, GAP-W2-2-HELPER, GAP-W2-2-QA, GAP-W2-3-PILOT, GAP-E1-6, GAP-R5） | 0 | 0 |
| **W5-E**（控制面效率） | 0 | 0 | 1（GAP-W4-X1） | 0 |

**觀察**：
- W5-D（殘留清理）承擔了最多 P0/P1 gap（9 個），是 Wave 5 最迫切需要先做的軸。
- W5-C 的 GAP-W4-C1（nightly auto-run 確認）雖然只有 P1，但它是 fail-on-deny 設計的前置。
- W5-A 目前已無 P0/P1 gap 需要清理，但其 runtime 任務本身（prod CI 嵌入、多 cohort 設計）是 Wave 5 最重的工期軸。

---

## 建議派工順序（前 5 個開工）

| 順位 | 建議開工票 | 所屬軸 | 理由 |
|------|-----------|--------|------|
| 1 | **W5-D-W4-FIX-B** | W5-D | P0：index 真實回填（file_count>0）是 W4-B 可信度的最低要求，否則 W4-B DONE 口徑受到挑戰 |
| 2 | **W5-D-W4-FIX-A** | W5-D | P0：gate checklist 不一致會影響任何後續 rollout 的品質檢查 |
| 3 | **W5-C-NIGHTLY-AUTO-VALIDATE** | W5-C | P1 但前置屬性：確認 nightly 可自動跑才能累積 metrics 資料，否則 fail-on-deny 設計無資料基礎 |
| 4 | **W5-D-W2-3-PILOT** | W5-D | P1：ART-GOV-RISK 案卷實例是 G8 六軌完整閉環的必要條件（也是 R5 風險解除） |
| 5 | **W5-A-RUNTIME-01** (首條 prod CI) | W5-A | P0（子票自身 priority）：W5 最重的 runtime 任務；盡早規劃可以及早發現 prod 環境特殊限制 |
