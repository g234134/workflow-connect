# W5 OVERVIEW — Wave 5 主軸與演化方向

> **設計者**：WAVE5-PLANNING 專線（2026-05-31）
> **用途**：說明 Wave 5 的核心目標、與 Wave 4 的演進關係、以及本波不做的事。
> **輸入**：`00_master_plan.md`（§15.4–§15.7）、`99_latest_status.md`（CHK-W4 收口）、
>          `40_ticket_memory/W5-A-*.memory.md`（既有 W5 planning 切片）、
>          `30_control_plane/W4-X_control_plane_mvp.md`（控制面 MVP）、
>          `90_run_queue.md`（Wave 4 + W5 草案 + Future 占位）。
> **硬邊界**：不 retro 改 W4 DONE-WITH-KNOWN-GAPS 口徑；不修改任何 repo 檔案。

---

## 1. Wave 5 核心目標

Wave 4 建立了「可接上去、可跑起來、可觀測、可回滾」的第一版實裝（minimal v1）。每條主線（A rollout / B index / C CI / X 控制面）都在單一主 case 或固定流上完成了最小閉環。

**Wave 5 的核心目標是：在 Wave 4 的 minimal v1 基礎上，把已驗證的能力「擴面、收斂、閉環」——讓更多 workflow / 模組 / 服務接上去，同時收斂已知缺口、強化觀測與治理，並開始向「近乎自動化」運轉邁進。**

具體來說，Wave 5 不是重做 Wave 4，而是：
- **擴面**：K-2 rollout 從固定試點流 → prod CI + 多 cohort + 多 repo。
- **閉環**：doc-sync / knowledge sync 從單 case → 完整閉環制度 + 跨 case 覆蓋。
- **收斂**：W4 已知缺口、W2 殘留子票、Wave 3 未派工項目在本波排入實戰並收線。
- **強化**：observability 從「有 metrics 就好」→ 「有趨勢、有 alert、有 gate 引用」。
- **鋪路**：為 Wave 6+ 的 deny engine runtime / 全自動 CI enforcement / 95% 無人值守建立設計與試點基礎。

---

## 2. Wave 5 vs Wave 4 演進方向（不是重做）

| 維度 | Wave 4（minimal v1） | Wave 5（擴面與收斂） |
|------|---------------------|---------------------|
| **A — Rollout** | 固定試點流 `W4-A-PILOT-RELEASE-STREAM-v0.1`；shadow + 5% canary 模擬；本地 helper 觸發 | prod CI 嵌入 shadow→canary→promote；多 cohort 階梯（1%→5%→20%→100%）；至少 2 個 repo/service 擴面 |
| **B — Index / KB** | 主 case W2-1 的 `kb_index_*` 回填；missing→block、stale→需要顯式 ack | 擴面到所有活躍 case；增量 index pipeline 設計；index gate 與 ORCH 更緊密銜接 |
| **C — CI / Gov Gate** | gov-gate-metrics.yml 落地；PR warning + nightly 固定響鈴；仍用 continue-on-error | fail-on-deny 治理討論與分階段試點；metrics 趨勢 dashboard；nightly auto-run 證實 |
| **X — 控制面** | MVP 文件骨架 + Ticket Memory 模板；lane 模型定義但無自動化 | reviewer SOP 自動化；lane routing 規則擴展；doc-sync pipeline 效率化 |
| **Doc-sync** | CHK-W4 一次性封口檢；無長期 doc-sync 制度 | 建立 doc-sync 定期校準制度；跨票 / 跨 wave 狀態一致性維護 |
| **殘留清理** | W2-2 HELPER/QA-CHECKLIST 子票 TODO、W2-3 GOV pilot TODO、E1-6 TODO | 所有 Wave 2/3/4 已知缺口排入實戰或明確 defer |

---

## 3. Wave 5 不做的事（明確留後）

下列事項仍為 **Wave 6+** 或 **Future**，本波不做（除非尚書省以獨立票 override）：

- **deny engine runtime (G10-2 T3)** — 本波僅做設計與試點討論，不啟用 production fail-on-deny。
- **全 IMP 機讀 enforcement** — 全狀態 CI 硬阻斷 + intake→IMP 機讀邊。
- **95% 無人值守** — 導入全鏈自動化比例目標。
- **K-2 Phase 3–4 / 遠端 prod 自動 rollout** — 根 plan §4.8 後續 Phase，超出 W5 scope。
- **知識層全庫級產品化** — 即時增量、多 tenant KB、替換 RAG 主路徑。
- **完整 release gate (G8-5 延續項)**。
- **控制面全自動化** — 自動開 chat、自動並行調度、自動 merge 決策（W4-X §0）。

---

## 4. Wave 5 總共涵蓋多少條軸

4 條主軸 + 1 條 cleaning 軸：

| 軸代號 | 名稱 | 簡要 | 典型 runtime 子票數估算 |
|--------|------|------|------------------------|
| **W5-A** | K-2 Rollout 擴面 | prod CI + 多 cohort + 多 repo | 6–8（含 RUNTIME-01~02、REVIEW-01~02、DOCSYNC-01~02、cohort 設計） |
| **W5-B** | Knowledge/Index 擴面與閉環 | 多 case index 覆蓋、增量 pipeline、gate 強化 | 4–6 |
| **W5-C** | Observability & Governance 強化 | metrics maturity、fail-on-deny 試點、alert 制度 | 4–5 |
| **W5-D** | Doc-sync / 跨 Wave 殘留清理 | W2-2 HELPER/QA-CHECKLIST、W2-3 GOV pilot、E1-6、W4-FIX 缺口 | 5–7 |
| **W5-E** | Control Plane 效率化 | reviewer SOP 自動化、lane routing 擴展、doc-sync pipeline 效率 | 2–3 |

**合計估算**：20–29 張 runtime 子票（不含 planning、review、doc-sync 配套票）。

---

## 5. 本波出口 DoD（草案 · 高層）

Wave 5 完成時，下列條件須全部滿足（以最後一次 CHK 判定為準）：

- [ ] **W5-A**：至少 1 條 prod CI 流水線已嵌入 K-2 rollout（shadow→canary→promote），且有可索引 CI run id；至少 2 個 repo/service 已完成 rollout 擴面。
- [ ] **W5-B**：至少 3 個活躍 case 的 `kb_index_*` 已回填且 gate 可正確阻斷/降級；index pipeline 增量方案已設計並 pilot 至少 1 次。
- [ ] **W5-C**：gov metrics 已累計 ≥14 日資料；nightly 自動 run 已走通 ≥3 次；fail-on-deny 的治理設計稿已交付（可 defer 到 Wave 6 實作）。
- [ ] **W5-D**：所有已知 P0/P1 gap 已修復或明確 defer；Wave 2 殘留子票已收線。
- [ ] **W5-E**：reviewer SOP 已有可復用檢查清單；doc-sync pipeline 效率可測量。
- [ ] 整體：**「擴面、收斂、閉環」** 三方向均有可索引證據與戰報。

---

## 6. W5 實戰進度（截至 2026-05-31）

> 本節記錄已完成實戰的子票，簡述內容以利總覽時快速定位。詳細設計與驗收條件見對應 plan / brief / PLAYBOOK。

### W5-D — cleanup 軸（已完成 3 張）

- **W5-D-W4-FIX-B-IMPLEMENTATION-01** ✓ — W2-1_case 真實 Index 回填。修復 CHK-W4 GAP-W4-B1（`index_status_W2-1.json` file_count=0 / chunk_count=0 的樣本問題），完成真實檔案 index 回填，讓 index_status 反映實際檔案計數。
- **W5-D-FIXTURE-PROVENANCE-IMPLEMENTATION-01** ✓ — eval fixture 溯源 line_index 修正。修正 `eval_export_sample.jsonl` 中 `source_ref.line_index` 的偏移（指向匯出檔自身行號而非原始輸入行號），補 schema 說明。
- **W5-D-SMOKE-FIXTURE-PROVENANCE-IMPLEMENTATION-01** ✓ — smoke fixture 溯源 line_index 修正。沿襲 W5-D-FIXTURE-PROVENANCE 的 same pattern，修正 smoke 類 fixture 中同類的 line_index 偏移，補 smoke-specific schema 說明。

### W5-A — runtime 軸（已完成 2 張 + 1 PLAYBOOK）

- **W5-A-RUNTIME-01-DRYRUN** ✓ — read-only dry-run CLI 完成。新增 `tools/dryrun/**` CLI module，讀取現有 eval-shadow-nightly artefact，用五 bucket 簡化治理規則產出 per-record JSONL + summary markdown 觀察報表。全部輸出到新路徑 `observability/dryrun/`，不修改任何既有 code/CI/artefact。已將此模式抽象為 **W5-A-RUNTIME-PLAYBOOK** 治理條目（`W5-A-RUNTIME-PLAYBOOK.md`），定義了 dry-run runtime-first 的標準結構、邊界與 AC-DRY 驗收條件，可套用到未來其他 repo。
- **W5-A-RUNTIME-02-LOGGING-FIRST-IMPLEMENTATION-01** ✓ — 在 `eval-shadow-nightly` job 掛上 logging-only step（`[DRYRUN-LOG]`），複用既有 dry-run CLI，僅寫 log / 附加 artefact，不改 gate verdict / exit code；與 W5-A-RUNTIME-PLAYBOOK 及 RUNTIME-02 logging-first plan 對齊。
- **W5-A-RUNTIME-03-ENF-PREVIEW** ✓ — `tools/enf_preview_wrapper.py` 落地，`observability/enf-preview/README.md` 定義 ENF-RULE-1/2 條件與輸出格式。
- **W5-A-RUNTIME-03-POLICY-MINING-02** ⬜（資料不足，待 infra 改善後重啟）

### ⚠ Nightly CI Status (W5-A-RUNTIME-03-NIGHTLY-STATUS-CHECK-01)

> **結論：nightly CI 的 eval-shadow-nightly job 有排程（`0 6 * * *`, UTC 06:00）但無法累積真實資料。所有 dry-run / preview 產出均來自 smoke fixture。以下為實證細節。**

| 項目 | 狀態 |
|------|------|
| **排程**（cron） | ✅ 存在 — `eval-gate-ci.yml` `on.schedule` 設定為 `cron: "0 6 * * *"`（每日 UTC 06:00） |
| **eval-shadow-nightly job** | ✅ 存在 — `eval-shadow-nightly` job 以 `github.event_name == 'schedule'` 為條件觸發 |
| **是否有 [DRYRUN-LOG] step** | ✅ 有 — `run: python -m tools.dryrun_ci_wrapper ...`，印 `[DRYRUN-LOG] event=summary` |
| **是否有 [GOV-ENF-PREVIEW] step** | ✅ 有 — `run: python -m tools.enf_preview_wrapper ...`，印 `[GOV-ENF-PREVIEW] event=summary` |
| **本地檔案推算** | ❌ 關鍵 artefacts 多日未更新 — `k2_shadow_spool.jsonl` 最後修改 2026-05-25 |
| **資料累積機制** | ❌ **不存在。** 見下方 `ci-data-pipeline-issue` |

**關鍵問題：CI 沒有機制餵入真實生產資料（`ci-data-pipeline-issue`）**

`eval-shadow-nightly` job 的 bootstrap 步驟：
```
if [[ ! -s "${SHADOW_SPOOL}" ]]; then
    cp "${SHADOW_SPOOL_BOOTSTRAP}" "${SHADOW_SPOOL}"
fi
```

由於 GitHub Actions runner 是 **ephemeral**（每次全新啟動），`SHADOW_SPOOL` (`artifacts/eval/k2_shadow_spool.jsonl`) 在每次 CI run 開始時都不存在 → 總是從 fixture (`tests/fixtures/eval/shadow_raw_records.jsonl`) 複製。這代表：

- **每次 nightly 看到的都是完全相同的 4-6 筆 fixture 記錄**
- **沒有任何真實 prod shadow 資料進入治理鏈**
- 即使每天 UTC 06:00 順利執行，dry-run 和 preview 的輸出也永遠不變
- 檔案時間戳也證實了未更新：本地 `k2_shadow_spool.jsonl` 最後修改在 May 25 01:51（可能是本機測試寫入），而三天後的 May 30-31 的 per-record JSONL 是由本機手動執行產生（非 CI）

兩個相關 workflow 皆無資料餵入管道：`eval-gate-ci.yml` 僅讀取 spool + fixture；`gov-gate-metrics.yml` 完全不同維度（workflow_v2 gate metrics，不涉及 eval-shadow pipeline）。

**對未來 MINING 的影響**

| 維度 | 影響 |
|------|------|
| **MINING-03 能否取得真實樣本** | ❌ 不能 — 除非先解決資料餵入管道。 |
| **POLICY-SELECTION 門檻** | ⏳ 無法達到 §2.2 要求的「觀察 ≥N 週期」，因為每個週期都是同一組資料。 |
| **ENF-RULE-1 的 0 FP 結論** | ⚠️ 仍脆弱 — N=1 且資料來自 fixture，非真實 CI |
