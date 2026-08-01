# W5 AXES AND THEMES — Wave 5 主軸詳細規劃

> **設計者**：WAVE5-PLANNING 專線（2026-05-31）
> **用途**：將 Wave 5 拆成 5 條主軸（W5-A～W5-E），每條定義目標、影響面、成功標準。
> **與現有 W5-A planning 切片關係**：W5-A 軸繼承既有 `W5-A-K2-ROLLOUT-EXPANSION` 父票及其四張子票（RUNTIME-01/RUNTIME-02/REVIEW-01/DOCSYNC-01）；W5-B/W5-C/W5-D/W5-E 為本規劃新增建議。

---

## 軸 A — W5-A：K-2 Rollout 擴面（prod CI + 多 cohort + 多 repo）

**目標**：在 W4-A 固定試點流（`W4-A-PILOT-RELEASE-STREAM-v0.1`）的 minimal v1 基礎上，將 K-2 rollout 擴展到真實 production CI 流水線、多 cohort 階梯交付、以及至少第二個 repo/service。

**主要影響面**：
- `.github/workflows/*`：至少 1 條 prod release workflow 嵌入 shadow→canary→promote 階段
- `workflow_v2/20_pilot/W3-A/`：新增 prod 流配置、runbook、gate checklist
- `workflow_v2/30_rollout/`：phase map / cohort 策略表更新
- `workflow_v2/tools/wf_k2_rollout_*`：擴展 helper（非 adapter 改動）
- `workflow_v2/observability/`：rollout 專用 metrics

**成功標準（高層）**：
1. 首條 prod CI 流水線已完成至少 1 次成功 rollout（shadow→canary→promote 可索引）
2. 最少 2 種 cohort 階梯（如 1% → 5% → 20%）有 documented 進入/停留/退出條件
3. 最少 2 個不同 repo/service 已完成 rollout 擴面，各自有獨立 workflow run id
4. 每一階段均有 rollback 證據與 override 審計記錄
5. W4-A 試點流定義與歷史運行記錄未被 retro 改寫

**既有基線**：`W5-A-K2-ROLLOUT-EXPANSION`（父票 planning DONE）、`W5-A-RUNTIME-01`（首條 prod CI planning DONE）、`W5-A-RUNTIME-02`（第二 repo planning DONE）、`W5-A-REVIEW-01`（reviewer planning DONE）、`W5-A-DOCSYNC-01`（doc-sync planning DONE）

**建議進階子票（新）**：
- `W5-A-COHORT-DESIGN`：多 cohort 階梯策略表 + traffic routing 文檔
- `W5-A-RUNTIME-03`：第三 repo 擴面（可選，視資源）

---

## 軸 B — W5-B：Knowledge / Index 擴面與閉環

**目標**：將 W4-B 從「單一主 case（W2-1）」擴展到至少 3 個活躍 case 覆蓋；讓 `kb_index_*` 回填與 gate 成為常態化運轉機制；設計增量 index pipeline 方案，不再依賴全量重新 index。

**主要影響面**：
- `workflow_v2/20_pilot/W2-1_case/` 以外的新 case 目錄
- `workflow_v2/tools/wf_kb_index_sync.ps1` / `wf_kb_index_gate.ps1`：參數化支援多 case
- `workflow_v2/20_pilot/W3-B/`：增量 pipeline 設計文檔
- `workflow_v2/40_ticket_memory/`：新 case 的 ticket memory

**成功標準（高層）**：
1. 至少 3 個活躍 case 的 `kb_index_*` 已真實回填（非樣本 file_count=0）
2. `wf_kb_index_gate` 在這些 case 上可正確回傳 allow/deny
3. 增量 index pipeline 設計稿已交付，包含 `since_last_index` 或等價策略
4. ORCH 在這些 case 上被 `kb_index_*` 正確阻止/允許 IMP-AI-READY 進入

**建議子票（planning → runtime）**：
- `W5-B-ORCH`：規劃編排（總控）
- `W5-B-MULTI-CASE`：W2-1 以外 2 個新 case index 回填
- `W5-B-INCREMENTAL-PIPELINE`：增量 index pipeline 設計
- `W5-B-GATE-STRENGTHEN`：index gate 參數化 + 多 case 支援
- `W5-B-INDEX-METRICS`：index 狀態觀測指標（ready/stale/missing 趨勢）

---

## 軸 C — W5-C：Observability & Governance 強化

**目標**：讓 W4-C 的 gov metrics 從「有資料就好」升格為「可觀測、可趨勢分析、可 gate 引用」的穩定指標系統。同時開始 fail-on-deny 的治理討論與試點設計（非 production 啟用）。

**主要影響面**：
- `workflow_v2/observability/`：metrics schema 擴展（v0.2）、dashboard 配置占位
- `workflow_v2/20_pilot/W3-C/`：fail-on-deny 設計稿
- `.github/workflows/gov-gate-metrics.yml`：可選增強（artifact 保留策略、trend 檢查）
- `workflow_v2/40_ticket_memory/W5-C-*.memory.md`：新票

**成功標準（高層）**：
1. gov metrics JSONL 已累計 ≥14 日連續資料（含 nightly 自動 run）
2. nightly CI 固定 run 已自動執行 ≥3 次且有 artifact 可查
3. fail-on-deny 的治理設計稿已交付（可行方案 + 風險評估 + 分階段 rollout 建議）
4. metrics 可產生簡單趨勢摘要（例如每週通過率、blocking rate）

**建議子票（planning → runtime）**：
- `W5-C-ORCH`：軸 C 規劃編排
- `W5-C-METRICS-V0.2`：schema 擴展 + dashboard 占位
- `W5-C-NIGHTLY-AUTO-VALIDATE`：nightly auto-run 確認 ≥3 次（W4-C 仍缺）
- `W5-C-FAIL-ON-DENY-DESIGN`：fail-on-deny 治理設計稿
- `W5-C-TREND-REPORT`：metrics 趨勢摘要腳本或 report template

---

## 軸 D — W5-D：Doc-sync / 跨 Wave 殘留清理

**目標**：把 W2、W3、W4 交付過程中產生的所有已知 P0/P1 缺口、未完成子票、跨文件不一致集中清理；建立可持續的 doc-sync 制度。

**主要影響面**：
- `workflow_v2/40_ticket_memory/`：各 W4-FIX 票 memory 新增
- `workflow_v2/00_master_plan.md`：E1-6 索引對齊
- `workflow_v2/20_pilot/W2-3_case/`：W2-3-GOV-RISK-PILOT 案卷實例
- `workflow_v2/tools/`：W2-2-HELPER-SCRIPTS 增強
- `workflow_v2/10_governance/G10_governance_rulebook/`：W2-2-QA-CHECKLIST 索引行

**成功標準（高層）**：
1. 所有 W4-FIX-* 子票已修復或明確 defer
2. W2-2-HELPER-SCRIPTS DONE（驗證腳本在乾淨環境可跑）
3. W2-2-QA-CHECKLIST DONE（NBT 可勾選表 + ART-QA-REV 字段建議）
4. W2-3-GOV-RISK-PILOT DONE（ART-GOV-RISK 案卷實例）
5. E1-6 DONE（`03` 範例路徑與 `90` Output 對齊）
6. W4-A-FIX-01~04 已修復（gate checklist trace 鍵名、rollback_path、cohort state 落點、override 證據）
7. W4-B-FIX-01 已修復（真實 index 回填 file_count>0）
8. doc-sync 制度已建立（定期校準 + 跨票一致性維護 SOP）

**建議子票（planning → runtime）**：
- `W5-D-ORCH`：軸 D 規劃編排 + gap inventory 確認
- `W5-D-W4-FIX-A`：W4-A-FIX-01~04
- `W5-D-W4-FIX-B`：W4-B-FIX-01
- `W5-D-W2-2-HELPER`：W2-2-HELPER-SCRIPTS
- `W5-D-W2-2-QA-CHECKLIST`：W2-2-QA-CHECKLIST
- `W5-D-W2-3-PILOT`：W2-3-GOV-RISK-PILOT
- `W5-D-E1-6`：E1-6 索引對齊
- `W5-D-DOCSYNC-SOP`：doc-sync 定期校準制度

---

## 軸 E — W5-E：Control Plane 效率化（選擇性增強）

**目標**：在 W4-X Control Plane MVP 文檔骨架基礎上，做 select 幾項輕量效率改進，使 Reviewer 和 Doc-sync 流程更可復用、更少人工檢查。

**主要影響面**：
- `workflow_v2/30_control_plane/`：reviewer SOP 補充、lane routing 擴展
- `workflow_v2/tools/`：可選 reviewer helper script（非替代 Reviewer 判斷）
- `workflow_v2/40_ticket_memory/`：doc-sync 效率改進的配套文件

**成功標準（高層）**：
1. Reviewer 有可復用的 checklist 模板（基於 §1.4.1，擴展為可執行的 checklist 文件）
2. doc-sync pipeline 有明確的 Q/A 清單（已回寫 vs 未回寫的判斷標準）
3. lane routing 規則已擴展（例如 W5-E 特有的`efficiency` lane 或 reviewer 效率指引）

**建議子票（planning → runtime）**：
- `W5-E-ORCH`：軸 E 規劃編排
- `W5-E-REVIEWER-SOP`：reviewer checklist 模板 + 效率指引
- `W5-E-DOCSYNC-EFFICIENCY`：doc-sync pipeline 效率指引
