# P3 Langfuse ↔ PG Align FRAME — v1（planning only）

> **Ticket**: `P3-LANGFUSE-PG-ALIGN-FRAME-v1`  
> **Date**: 2026-07-15 · Wave C 前置 · Multi-Chat same_chat  
> **ticket_class**: `doc/spec · planning`（本票**無** runtime／無真 PG 連線）  
> **上游**：`docs/langfuse-pg-alignment-deferred-index-v1.md`（FP-G3-T3 · done）· near-100 §P3 #2  
> **切換來源**：原派 `P1-OPS-CHECKLIST-CLOSURE-v1` 與已封 `P1-GOV-RESIDUAL-CHECKOFF-v1` 範圍重複 → 改開本票  

---

## §0 non_claims（必讀）

| 禁止宣稱 | 說明 |
|----------|------|
| 本 FRAME **≠** Langfuse↔PG 已對齊／已驗收 | 僅設計邊界；無 sync／ingest 實作 |
| 本票 **≠** 真接 Langfuse API · ≠ 改暗部 observability | 憲法 §7；實作另授權票 |
| 本票 **≠** 連真 PostgreSQL · ≠ soak／migration | 不讀寫 live PG |
| 本票 **≠** P3 closure · ≠ Phase% apply | `apply_phase_pct=false` |
| 本票 **≠** 以 Langfuse 驅動 selector／SLO | Monitoring Graph **僅 L0**（D-04 禁止） |
| deferred 索引存在 **≠** 對齊完成 | 見 FP-G3-T3；本 FRAME 只升「可審查設計」 |

---

## §1 Goal 與 ticket_class

### Goal

為 **Langfuse traces ↔ Postgres 營運表（`task_runs`／相關）** 對齊缺口產出可審查的 planning FRAME：欄位對照、MVP vs stretch、解阻閘門、後續實作票占位；**本票停在 FRAME**。

### ticket_class

| 字段 | 值 |
|------|-----|
| `ticket_class` | **doc/spec · planning** |
| `evidence_tier` | L-local（doc + 薄測） |
| 本票交付 | 本文檔 + `tests/test_p3_langfuse_pg_align_frame_v1.py` |
| 本票**不**交付 | Langfuse client、PG DSN、暗部 core、CI workflow、soak runner |

---

## §2 與 deferred 索引對照（FP-G3-T3）

| Deferred ID | 項 | 本 FRAME 角色 |
|-------------|-----|----------------|
| **D-01** | Langfuse trace body 全量對齊 | 定義 MVP 欄位映射與驗收口（§3–§4）；**不**實作 |
| **D-02** | PG 持久化 trace／查詢對齊 | 定義目標表語意與對齊鍵（§3）；**不**連 PG |
| **D-03** | 生產預設導出 Langfuse | stretch／產品批文；本票 NonScope |
| **D-04** | 以 Langfuse 驅動 selector／SLO | **硬禁止**（L0 only） |

**Landed 錨點（引用 · 非本票新跑）**：gov-trace-v2 · local harden `P3-TRACE-LOCAL-HARDEN-v1` · 歷史 Wave 4A/4B soak 敘事（Progress；≠ 本票重跑）。

---

## §3 欄位對照（設計 · 邏輯名 only）

> **禁止**在本檔寫入實例 DSN、env 鍵原文、磁碟絕對路徑（合約 META-0.4）。環境鍵僅經實例錨點查閱。

### 3.1 對齊鍵（canonical）

| 邏輯鍵 | Langfuse 側（語意） | PG 側（語意） | 備註 |
|--------|---------------------|---------------|------|
| `trace_id` | Langfuse trace id | `task_runs.trace_id`（或等價欄） | **主對齊鍵** |
| `session_id`／`run_id` | session／metadata | 營運 run 關聯欄（若有） | 輔鍵；缺則允許 null |
| `task_type`／`name` | trace name／tags | task 類型欄 | 用於 cohort 過濾 |
| `status`／`biz_ok` | 成功語意（觀測） | `status`／業務成功旗標 | 對齊前須定義「成功」口徑 |
| `started_at`／`ended_at` | timestamps | 對應時間欄 | 時區 UTC |
| `total_cost`／usage | generations rollup | `totalCost`／usage 欄 | 歷史缺口：根 trace 常 $0；SLO 口徑見 §4 |

### 3.2 對齊判定（規劃定義 · 非本票已達成）

後續**實作票**在宣稱「Langfuse↔PG 對齊可驗收」前，建議同時滿足：

| # | 條件 |
|---|------|
| A1 | 固定 cohort（n≥N，N 由實作票定）每筆 `trace_id` 在 Langfuse **與** PG 皆可查 |
| A2 | 成功語意一致（或顯式記錄不一致率 + 豁免理由） |
| A3 | cost／usage 口徑寫明 primary source（Langfuse generations vs PG）；禁止 silently 混用 |
| A4 | evidence_tier 標註（L-local／staging／prod）；prod 須另批文 |
| A5 | **不得**把對齊結果寫入 selector／SLO gate（D-04） |

---

## §4 MVP vs stretch

### MVP（後續實作票 · 本票僅定義）

| # | 範圍 | 說明 |
|---|------|------|
| M1 | **只讀對齊報告** | 給定已授權環境：輸入 cohort → 輸出結構化 dict（matched／missing_pg／missing_langfuse／mismatch） |
| M2 | **主鍵 = `trace_id`** | 輔鍵可選；失敗回 `ok: false` + `message` |
| M3 | **non_claims 置頂** | ≠ P3 closure ≠ Phase% ≠ selector 升格 |
| M4 | **可重跑 runner** | 專票 CLI／unittest；禁止口頭「soak 過了」 |

### Stretch／另軌（本票明確不做）

| 項 | 歸屬 |
|----|------|
| 生產預設開啟 Langfuse 導出 | D-03 · 產品／安全批文 |
| 改暗部 monitoring ingest／scheduler | 暗部 Infra 票 · §7 |
| 真 Grafana／Dashboard Phase% | P5／W-PROG |
| Monitoring Graph L1／L2 | **禁止**直至 runbook §6.8 門檻 + 批文 |
| 修復根 trace usage=$0 根因 | 可另開 observability 票；≠ 本 FRAME 必達 |

---

## §5 解阻閘門（實作票開工前）

- [ ] 尚書省明示授權（是否觸暗部／Z-DARK-OPS／venv）
- [ ] `assignable: true`（boot／route；DarkOps blocked 時**不得**施工）
- [ ] 環境鍵僅經實例錨點；可移植正文**零**金鑰／DSN 原文
- [ ] 驗收命令 + evidence_tier 寫入實作票 FRAME
- [ ] 對照本 FRAME §3–§4；**不得**宣稱本 FRAME = 已對齊
- [ ] `apply_phase_pct=false` 除非另開 W-PROG

---

## §6 建議後續票占位

| ID（建議） | 類型 | 說明 |
|------------|------|------|
| `P3-LANGFUSE-PG-ALIGN-IMPL-v1` | code／infra（須批文） | 實作只讀對齊 runner + 測；可碰範圍由批文鎖 |
| （可選）cost-口径修復票 | observability | 根 trace usage 與 generations 一致 |

**本衝刺**：無批文 → **停在本 FRAME**（near-100 Wave C）。

---

## §7 切換原因（本輪 O 裁決）

原派 **`P1-OPS-CHECKLIST-CLOSURE-v1`**（計劃 §P1 #1：checklist 一鍵綠 + Onboarding／INDEX）。  
已封 **`P1-GOV-RESIDUAL-CHECKOFF-v1`** 已涵蓋：

- R2：`_ops_cycle.py checklist --mode full` → `ok: true`
- R3：Onboarding／接戰入口
- R4：INDEX 假陰性 → **explicit defer**

→ 範圍完全重複 → stub 標 `superseded` → 改開本 P3 FRAME（無批文薄刀 · Wave C 前置）。

---

## §8 Verification（本票）

```powershell
python -m unittest tests.test_p3_langfuse_pg_align_frame_v1 -v
rg "non_claims|MVP|stretch|trace_id|D-01|apply_phase_pct" docs/p3-langfuse-pg-align-frame-v1.md
```

預期：unittest 全綠；rg 關鍵詞命中；**無** PG 連線嘗試。

---

## Phase% proposal（not applied）

| Field | Value |
|-------|-------|
| phase_targets | P3 |
| baseline_pct | 82 |
| proposed_delta_pct | +0～+1（FRAME only · 敘事） |
| apply_phase_pct | **false** |

---

*P3-LANGFUSE-PG-ALIGN-FRAME-v1 · planning FRAME · 2026-07-15*
