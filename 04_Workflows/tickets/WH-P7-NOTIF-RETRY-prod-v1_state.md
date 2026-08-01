# WH-P7-NOTIF-RETRY-prod-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-H+1 · **P7 prod 線 retry / DLQ 整合設計票（doc-only · FRAME）**  
> 上游：`WH-P7-sandbox-line-wrapup-v1` · `WH-P7-NOTIF-RETRY-SANDBOX-v1` · `WH-P7-NOTIF-DLQ-v1` / `WH-P7-NOTIF-DLQ-impl-v1` · `WH-P7-NOTIF-PROD-URL-v1` / `WH-P7-NOTIF-PROD-URL-impl-v1` · `WH-P7-NOTIF-HMAC-impl-v1` · `WH-P7-NOTIF-HMAC-receiver-contract-v1` · `WH-P7-PROD-roadmap-v1`  
> 產物：staging/prod tier retry policy SSOT 草案；§4.6.3 升格規格；sandbox vs staging vs prod 差異表；衍伸 impl 票索引。**零 code / 零 CI / 零合約 doc 變更（本輪）**

---

## FRAME

### handoff header

**P7 prod 線 retry / DLQ 整合設計票**：sandbox 線 retry 已 **partial**（env 驅動 · default `max_attempts=0` · 無 tier gate · 無 mandatory DLQ）；DLQ 落盤已 **partial**（`WH-P7-NOTIF-DLQ-impl-v1` · env default off）；PROD-URL / HMAC sender 亦 partial。合約 §4.6.6.3 tier matrix 已標 staging/prod **`retry_required=true`**，但 **無** tier-aware retry 強制、**無** staging/prod 預設 attempts/backoff、**無** retry↔DLQ↔HMAC 整合裁決。本票定義 prod 線 retry policy SSOT，供後續 impl 票實作 tier gate 與 env 預設；**不改 sandbox 行為、不寫實作、不改 adapter 現邏輯**。

---

### 1. Background

| 層級 | 現況 | 證據 |
|------|------|------|
| **Sandbox retry** | env 驅動；**default `max_attempts=0`**（單次 POST）；`≥1` 時指數退避；可重試：連線/timeout、408、429、5xx；不可重試：其他 4xx；外層 **fail-open** | `WH-P7-NOTIF-RETRY-SANDBOX-v1` · `notification_webhook_adapter_v1._send_http_post_with_retry` |
| **Retry env 鍵** | `GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS`（default `0`）· `RETRY_BASE_DELAY_MS`（`100`）· `RETRY_MAX_DELAY_MS`（`2000`） | §4.6.3 · adapter `_get_retry_config()` |
| **DLQ 落盤** | **partial**：`DLQ_ENABLED=0` default；`=1` 時最終失敗 append jsonl；retry 中途不寫；sandbox 預設不寫 | `WH-P7-NOTIF-DLQ-impl-v1` · §4.6.4 |
| **Tier / URL** | `TIER` + `URL_ALLOWLIST` minimal gate **partial**（staging/prod https + allowlist）；**未** enforce mandatory retry / DLQ / HMAC | `WH-P7-NOTIF-PROD-URL-impl-v1` |
| **HMAC sender** | **partial**；sandbox default off；fail-open unsigned；retry 時同一 `event_id` · body 不變 · timestamp/signature **may** 刷新 | `WH-P7-NOTIF-HMAC-impl-v1` · §4.6.5.1 |
| **§4.6.6 tier matrix** | staging/prod：`retry_required=true` · `dlq_required=true` · `hmac_required=true`；sandbox：全 false / opt-in partial | `WH-P7-NOTIF-PROD-URL-v1` · §4.6.6.3 |
| **§4.6.3 impl_status** | sandbox localhost adapter **partial**（無 tier gate · 無 prod mandatory） | 合約 SSOT |

**缺口**：prod 線需要比 sandbox 更強的 **送達可靠性 + 失敗可觀測性**（§4.6.1 威脅模型假設 retry/DLQ 補償）。現況 staging/prod tier 即使 env 設了 `TIER=staging`，adapter **仍允許** `max_attempts=0` 單次 POST、DLQ off、HMAC off——與 §4.6.6.3 policy matrix **不一致**。本票填補 staging/prod retry **次數 / backoff / DLQ / HMAC 整合** 的 normative 規格真空。

---

### 2. Goal

產出 **prod 線 retry policy SSOT 草案**（下一輪 Implementer 擴寫 §4.6.3 或等價 doc + impl 票 AC），至少定義：

1. **Sandbox 現行行為摘要**（baseline · 不變）
2. **Staging / prod retry mandatory 要求**（次數下限 · backoff · 與 DLQ / HMAC 關係）
3. **Tier 對照表**（sandbox vs staging vs prod）
4. **Tier gate 裁決**（staging/prod 不滿足 mandatory 時 adapter 行為）
5. **衍伸 impl 票索引**

#### 2.1 Sandbox 現行行為（baseline · 本票不變）

| 項 | 定案（對照現碼 · 只讀） |
|----|-------------------------|
| **Default attempts** | `GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS` 未設或 `≤0` → **單次 POST**（`attempt_count=1`） |
| **Opt-in retry** | 設 `≥1` → 至多 N 次 POST；指數退避 `base * 2^(attempt-1)` clamp 至 `max_delay_ms` |
| **Default backoff env** | `BASE_DELAY_MS=100` · `MAX_DELAY_MS=2000` |
| **可重試** | 連線錯誤 / timeout · HTTP **408** · **429** · **5xx** |
| **不可重試** | 其他 **4xx**（400/401/403/404 等）→ 單次失敗即停 |
| **DLQ** | **無 mandatory**；`DLQ_ENABLED` default `0` → 失敗僅 `webhook_result` + log |
| **HMAC** | **無 mandatory**；default off · fail-open unsigned |
| **Tier gate** | sandbox tier（或未設 `TIER`）→ localhost-only URL gate；**不**檢查 retry/DLQ/HMAC mandatory |
| **外層語意** | emit / dispatch **fail-open**（`ok=True`）；retry 用盡仍外層 `ok=True` |

> **Partial 邊界**：sandbox 可 opt-in retry + opt-in DLQ + opt-in HMAC 組合演練；**不得**誤繼承為 staging/prod 交付。

#### 2.2 Staging / prod retry policy（本票 normative 草案）

**原則**：staging/prod tier 下 retry 為 **policy mandatory**（§4.6.6.3 `retry_required=true`）；須與 DLQ、HMAC **同時**滿足才可 POST（tier readiness gate · 對齊 PROD-URL / HMAC-prod-mandatory 升格鏈）。

##### 2.2.1 Attempts 與 backoff（proposed_default）

| 參數 | staging | prod | 說明 |
|------|---------|------|------|
| **`max_attempts` 下限** | **≥ 1**（mandatory） | **≥ 1**（mandatory） | `≤0` 視為 **policy violation** · adapter **must reject POST**（fail-closed at tier readiness gate） |
| **`max_attempts` 建議 default**（env 未設時 tier default） | **3** | **5** | Implementer 票可微調；**不得**低於 1 |
| **`base_delay_ms` 建議 default** | **500** | **1000** | 指數退避起點 |
| **`max_delay_ms` 建議 default** | **8000** | **30000** | 退避上限；staging 較短以便內部測試收斂 |
| **Backoff 算法** | 與 sandbox 相同：`base * 2^(failed_attempt-1)` clamp 至 `max_delay_ms` | 同上 | 不引入新算法；僅 tier default 不同 |
| **可重試 / 不可重試** | 與 §4.6.3 / sandbox 相同 | 同上 | 401/403（HMAC 驗簽失敗）**不可重試** · 對齊 §4.6.5.2 |

**總重試跨度估算**（operator 參考）：prod `max_attempts=5` · `base=1000` · `max_delay=30000` → 最壞約 **≤ ~90s** 級（含 HTTP timeout）；receiver `max_seen_window_sec=86400` 已覆蓋（§4.6.5.2）。

##### 2.2.2 與 DLQ 整合（mandatory · 用盡才寫）

| 項 | staging | prod |
|----|---------|------|
| **`DLQ_ENABLED`** | **must be `1`**（tier readiness gate） | **must be `1`** |
| **寫入時機** | 僅 **最終失敗**（retry 用盡 · 或不可重試 4xx 單次失敗） | 同上 |
| **Retry 進行中** | **不寫** DLQ | 同上 |
| **2xx 成功** | **不寫** DLQ | 同上 |
| **`tier` 欄位** | DLQ record `tier=staging`（來源 `GOV_NOTIFICATION_WEBHOOK_TIER` 或 `DLQ_TIER` env） | `tier=prod` |
| **DLQ 寫入失敗** | adapter **fail-open**（log warning · 外層 `ok=True`） | 同上 |

> **互補原則**（沿用 DLQ 設計票）：retry 提升送達；DLQ 提供 **事後 audit**；兩者語意不變，staging/prod 僅 **強制啟用** 組合。

##### 2.2.3 與 HMAC 整合（mandatory · 對齊 HMAC-prod-mandatory）

| 項 | staging | prod |
|----|---------|------|
| **`HMAC_ENABLED` + secret** | **must** 雙 gate 通過才進入 retry loop | 同上 |
| **缺 HMAC / 空 secret** | **reject POST**（fail-closed · `blocked_reason=tier_hmac_required`）— 與 sandbox fail-open **分支不同** | 同上；prod 更嚴（§4.6.6.3 缺簽名 reject） |
| **Retry 每次 POST** | 同一 `event_id` + canonical body；**may** 刷新 `X-Gov-Timestamp` + 重算 signature | 同上（§4.6.5.1） |
| **Receiver 協作** | receiver **must not** 對同 `event_id` 回 5xx（避免 retry 風暴）；401/403 **不可重試** | 同上 |

**依賴票**：`WH-P7-NOTIF-HMAC-prod-mandatory-v1` 實作 tier HMAC gate；本票 retry impl **must** 在 HMAC gate **之後** 執行 retry loop（或 HMAC 與 retry readiness 合併為單一 tier preflight）。

##### 2.2.4 Tier readiness gate（staging/prod · proposed_default）

在 `TIER ∈ {staging, prod}` 且 URL allowlist gate 通過後、**第一次 HTTP POST 前**，adapter **must** 驗證：

| 檢查 | 失敗時 |
|------|--------|
| `max_attempts ≥ 1` | reject POST · `blocked_rule=retry_policy_violation` · log |
| `DLQ_ENABLED=1` | reject POST · `blocked_rule=dlq_policy_violation` |
| HMAC enabled + secret 非空 | reject POST · `blocked_rule=hmac_policy_violation`（或併入 HMAC-prod-mandatory 票） |

**外層語意不變**：gate 拒絕仍 dispatch **fail-open** `ok=True` · `dispatched=False` · `dry_run=True`（對齊 PROD-URL-impl blocked 路徑）。

**Sandbox 豁免**：`TIER=sandbox`（或未設）→ **不**執行上述 mandatory 檢查；維持 §2.1 baseline。

#### 2.3 Sandbox vs staging vs prod 差異表（normative）

| 維度 | **sandbox** | **staging** | **prod** |
|------|-------------|-------------|----------|
| **Retry mandatory** | 否（default 單次 POST） | **是**（`max_attempts ≥ 1`） | **是** |
| **Default `max_attempts`** | `0` | `3`（建議 tier default） | `5`（建議 tier default） |
| **Default backoff** | 100 / 2000 ms | 500 / 8000 ms | 1000 / 30000 ms |
| **可重試錯誤** | 408/429/5xx/連線/timeout | 同 sandbox | 同 sandbox |
| **DLQ mandatory** | 否（default off） | **是**（`DLQ_ENABLED=1`） | **是** |
| **DLQ 寫入時機** | opt-in enabled 時才寫 | 最終失敗必寫 | 最終失敗必寫 |
| **HMAC mandatory** | 否（opt-in · fail-open unsigned） | **是** | **是**（缺簽名 reject POST） |
| **Tier readiness gate** | 無（僅 localhost URL） | retry + DLQ + HMAC preflight | 同上 + prod registry（URL 票） |
| **URL** | localhost only | https + allowlist | https + allowlist ∩ registry |
| **Approval** | none | governance_dual | shangshu_prod + security |
| **CI 使用** | 允許（§4.5 advisory） | **禁止** CI env | **禁止** CI env |

**一句話對照**：

- **sandbox**：retry/DLQ/HMAC 全 **opt-in** · default 零 retry · 無 DLQ mandatory · 失敗靠 log。
- **staging**：retry **必須非零** · DLQ **必須開** · HMAC **必須簽名** · 三者缺一 **拒 POST** · 失敗必落 DLQ。
- **prod**：同 staging mandatory 組合 · 更高 default attempts/backoff · 更嚴 URL/registry · 尚書省批文後才啟用。

#### 2.4 交付位置偏好（Implementer 下一票）

| 方案 | 位置 | 採用 |
|------|------|------|
| **A — 擴寫 §4.6.3** | `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.3 增 **§4.6.3.1 Tier retry defaults** · **§4.6.3.2 Tier readiness gate** | **首選** |
| **B — 交叉引用** | §4.6.3 摘要 + §4.6.6.3 matrix 連結 | 輔助 |

§4.6.0 `webhook_retry_max_attempts` 在 impl 票完成後：**partial** → staging/prod tier gate **partial**（sandbox 仍 partial opt-in）。

---

### 3. Non-Goals

- ❌ **不實作** tier retry gate、env default 覆寫、或任何 adapter / test / CI 變更。
- ❌ **不改** sandbox 行為 — default `max_attempts=0` · opt-in retry · DLQ default off · HMAC fail-open **維持不變**。
- ❌ **不改** 現有 retry loop 算法（`_is_retriable_http_result` · backoff 公式）— 僅定義 tier **policy 層** 預設與 mandatory。
- ❌ **不實作** DLQ inspect CLI · replay pipeline（→ 既有 DLQ-inspect / future replay 票）。
- ❌ **不實作** HMAC prod mandatory gate 本體（→ `WH-P7-NOTIF-HMAC-prod-mandatory-v1`）；本票僅定義 retry 與 HMAC **順序與依賴**。
- ❌ **不修改** `docs/outbox-and-feedback-layer-contract-v1.md`（本輪 FRAME-only）。
- ❌ **不升格** advisory CI；staging/prod retry 驗證留 impl + 可選 CI 票。
- ❌ **不合併** Phase 8.8 `orchestration_bridge_outbox` DLQ（§2.2 永久分軌）。

---

### 4. Acceptance Criteria（設計層 · 本票 FRAME）

- **AC-1**：FRAME 含 Background / Goal / Non-goals / AC / AllowedPaths / BlockedPaths（本檔）。
- **AC-2**：§2.1 準確描述 sandbox 現行行為（default 0 · 可重試碼 · 無 DLQ mandatory · fail-open）。
- **AC-3**：§2.2 定義 staging/prod **mandatory** retry（`max_attempts ≥ 1` · backoff default · DLQ 用盡才寫 · HMAC 對齊）。
- **AC-4**：§2.3 **tier 對照表** 清楚列出 sandbox vs staging vs prod 差異（≥8 維度）。
- **AC-5**：§2.2.4 tier readiness gate 與 PROD-URL blocked 語意一致（fail-closed POST · fail-open dispatch）。
- **AC-6**：列出 ≥2 張 **後續實作票**（§5）。
- **AC-7**：與 `WH-P7-NOTIF-DLQ-impl-v1` DLQ 觸發表 · `WH-P7-NOTIF-PROD-URL-v1` §4.6.6.3 matrix **無矛盾**。
- **AC-8**：文檔工單自檢（APP-DOC）：FRAME 正文零本機絕對路徑、零 secret / 真實 URL 範例。

#### AC 交付物對照（下一輪 Implementer · 非本票）

| 交付物 | 位置 | 本票狀態 |
|--------|------|----------|
| §4.6.3 tier retry 擴寫 | `docs/outbox-and-feedback-layer-contract-v1.md` | **待 impl 票** |
| adapter tier retry gate | `delivery/notification_webhook_adapter_v1.py` | **待 `WH-P7-NOTIF-RETRY-prod-impl-v1`** |
| §4.6.0 / §4.6.6 env 表 tier 列 | 合約 doc | **待 doc-sync 票** |

---

### 5. 建議衍伸實作票（本票外 · AC-6）

| 票號（建議） | 範圍摘要 | 依賴 |
|--------------|----------|------|
| **`WH-P7-NOTIF-RETRY-prod-impl-v1`** | adapter tier readiness gate：staging/prod 驗證 `max_attempts≥1` · `DLQ_ENABLED=1` · HMAC ready；tier default env fallback；blocked_rule 擴充；unittest matrix（sandbox regression + staging/prod reject/accept）；§4.6.3 擴寫 | 本票 FRAME · `WH-P7-NOTIF-DLQ-impl-v1` · `WH-P7-NOTIF-PROD-URL-impl-v1` · `WH-P7-NOTIF-HMAC-prod-mandatory-v1`（可並行 · gate 合併裁決） |
| **`WH-P7-NOTIF-RETRY-prod-ci-v1`** | 將 prod retry policy 納入 CI 檢查：fixture env matrix assert tier gate（**仍 sandbox-only job** · 不開 staging/prod URL）；或 doc lint 驗 §4.6.3/§4.6.6.3 一致 | RETRY-prod-impl-v1 |
| `WH-P7-NOTIF-contract-doc-sync-v1`（或子票） | §4.6.0 `webhook_retry_max_attempts` · §4.6.6 env 表 tier 列 · `impl_status` 更新 | RETRY-prod-impl-v1 |

> **升格順序（對齊 §4.6.6.4 · `WH-P7-PROD-roadmap-v1` Wave-P7-2）**：DLQ-impl ✅ → **本票 design** → RETRY-prod-impl → HMAC-prod-mandatory → PROD-URL（partial ✅）→ staging-integration → prod rollout。

---

### 6. AllowedPaths / BlockedPaths

#### AllowedPaths

- `04_Workflows/tickets/WH-P7-NOTIF-RETRY-prod-v1_state.md`（本票 STATE / FRAME / B/C/D_REPORT）

#### BlockedPaths

- `delivery/**`（含 `notification_webhook_adapter_v1.py` — 本票 **只讀** 對照）
- `tests/**` · `docs/**` · `.github/workflows/**`
- 其他票檔 · `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `.cursor/rules/**`
- `.env` · secrets · 客戶實際 webhook URL

---

### 7. Dependencies

- `WH-P7-sandbox-line-wrapup-v1`（sandbox 封箱 · prod 入口）
- `WH-P7-NOTIF-RETRY-SANDBOX-v1`（retry loop SSOT · sandbox partial）
- `WH-P7-NOTIF-DLQ-v1` / `WH-P7-NOTIF-DLQ-impl-v1`（DLQ 觸發 · 落盤 partial）
- `WH-P7-NOTIF-PROD-URL-v1` / `WH-P7-NOTIF-PROD-URL-impl-v1`（§4.6.6 tier matrix · URL gate partial）
- `WH-P7-NOTIF-HMAC-impl-v1` · `WH-P7-NOTIF-HMAC-receiver-contract-v1`（HMAC · retry 協作）
- `WH-P7-PROD-roadmap-v1`（Wave-P7-2 retry 升格索引）
- `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.3 · §4.6.4 · §4.6.6（只讀）
- `delivery/notification_webhook_adapter_v1.py`（只讀 · retry 段）

---

## STATE

- **overall_status**: `done_with_gaps`
- **current_owner**: scribe
- **next_action**: prod CI 升格 · 真 env enforce 留 staging execute / prod rollout 票
- **last_updated**: 2026-06-23 · progress agent (Reviewer C 代收口 · impl 已 validated)
- **wave**: Wave-H+1 · P7 prod line · notification retry policy design
- **status_by_role**:
  - **Orchestrator (A)**: done — FRAME 落盤
  - **Implementer (B)**: n/a — 本票 doc-only
  - **Reviewer (C)**: done — 2026-06-22 · **`accepted_with_gaps`**
  - **Scribe (D)**: done — 2026-06-22 · D_REPORT 由 Reviewer 代填（本輪邊界）
- **notes**:
  - **policy-only** · runtime tier retry gate 由 `WH-P7-NOTIF-RETRY-prod-impl-v1`（**validated**）承接 · sandbox 對照 `WH-P7-NOTIF-RETRY-SANDBOX-v1`
  - 真 env enforce · required CI 留 staging execute / Wave-P7-6

---

## B_REPORT

- **status**: doc-only design SSOT · FRAME §2.1–§2.4 normative spec
- **design_deliverable**: sandbox baseline（opt-in retry · default 0）· staging/prod mandatory retry+DLQ+HMAC · tier readiness gate · sandbox vs staging vs prod 對照表
- **impl_cross_ref**: `WH-P7-NOTIF-RETRY-prod-impl-v1`（**validated** · adapter tier readiness + tier defaults · 39/39 webhook unittest）· sandbox 對照 `WH-P7-NOTIF-RETRY-SANDBOX-v1`
- **policy_scope_only**: 本票不宣稱 runtime enforce；§4.6.3 正文擴寫留 `WH-P7-NOTIF-contract-doc-sync-v1`

---

## C_REPORT

- **review_date**: 2026-06-22
- **reviewer_role**: P7 prod line Reviewer (C)
- **verdict**: **`accepted_with_gaps`**
- **conclusion**: sandbox / staging / prod retry·DLQ·HMAC 三層差異清楚且與 §4.6.6.3 tier matrix、§4.6.6.4 enablement checklist 相容；staging/prod mandatory 組合、tier readiness gate、attempts/backoff 建議 default 足以支撐後續 impl 票。**缺口**：仍為 **design-only**（adapter tier gate / §4.6.3 擴寫未實作）；HMAC prod mandatory gate 依賴 `WH-P7-NOTIF-HMAC-prod-mandatory-v1`（gate 合併裁決留 impl）；§4.6.3 tier default 尚未落合約正文（§2.4 明示待 impl/doc-sync）。

### FRAME 三層 vs 合約對照

| 檢查句 | FRAME（§2.3 一句話） | §4.6.6.3 / §4.6.4 | 結果 |
|--------|------------------------|-------------------|------|
| **sandbox** | retry/DLQ/HMAC opt-in · default 零 retry · 失敗靠 log | `retry_required=false` · `dlq_required=false` · `hmac_required=false`；§4.6.3 default `max_attempts=0` | ✅ |
| **staging** | retry 非零 · DLQ 必開 · HMAC 必簽 · 缺一拒 POST · 最終失敗必落 DLQ | matrix 全 **true** · `max_attempts ≥ 1`；§4.6.4 最終失敗落盤 | ✅ |
| **prod** | 同 staging mandatory · 更高 attempts/backoff · 更嚴 URL/registry · 批文 | 同 matrix + `approval_required=shangshu_prod + security`；§4.6.6.1 prod registry | ✅ |

**設計 vs 實作邊界**：§2.2 標 **normative 草案** · §2.4 / Non-Goals / AC 交付物表均明示 **待 `WH-P7-NOTIF-RETRY-prod-impl-v1`**；與 §4.6.3 `staging/prod retry mandatory not_implemented_yet` 一致，未宣稱已 enforce。

### acceptance_criteria_review（設計層 AC-1～AC-8）

| AC | 結果 | 備註 |
|----|------|------|
| AC-1～AC-4 | **pass** | Background / sandbox baseline / staging-prod mandatory / ≥8 維 tier 表齊全 |
| AC-5 | **pass** | §2.2.4 readiness gate 對齊 PROD-URL-impl blocked 路徑（fail-closed POST · fail-open dispatch） |
| AC-6 | **pass** | §5 列 ≥2 張衍伸票（impl · ci · doc-sync） |
| AC-7 | **pass** | DLQ 觸發（最終失敗才寫 · retry 中途不寫）與 DLQ-impl · §4.6.4 無矛盾 |
| AC-8 | **pass** | FRAME 正文零本機絕對路徑 · 零 secret / 真實 URL |

### non-blocking gaps

- HMAC tier gate 與 retry readiness **合併 vs 串行** — 留 impl 與 `WH-P7-NOTIF-HMAC-prod-mandatory-v1` 裁決（FRAME §2.2.3 已索引）。
- §4.6.6.4 建議順序與 FRAME §5 升格順序在 PROD-URL-impl / HMAC 票間略有並行空間 — Orchestrator 裁決，不阻 design sign-off。
- prod `max_attempts=5` / backoff default 為 **proposed_default**，impl 票可微調但不得低於 1。

---

## D_REPORT

- **scribe_date**: 2026-06-23 · progress agent 收口
- **verdict_echo**: Reviewer **`accepted_with_gaps`** — prod retry policy FRAME 可作 SSOT；impl **`validated`**（unittest only）；`overall_status` → **`done_with_gaps`**
- **handoff_one_liner**: P7 prod retry 設計已定案 — sandbox 維持 opt-in 單次 POST；staging/prod 須 retry+DLQ+HMAC 三 gate 通過才 POST，用盡或不可重試 4xx 必落 DLQ；實作留 impl 票。
- **next_tickets**（建議順序）:

| 順序 | 票號 | 說明 |
|------|------|------|
| **1** | **`WH-P7-NOTIF-RETRY-prod-impl-v1`** | adapter tier readiness gate · staging/prod default attempts/backoff · §4.6.3 擴寫 · unittest matrix |
| **2** | **`WH-P7-NOTIF-RETRY-prod-ci-v1`** | sandbox-only CI / doc lint 驗 tier gate 與 §4.6.3/§4.6.6.3 一致（**依賴 impl**） |
| 3（可並行） | `WH-P7-NOTIF-HMAC-prod-mandatory-v1` | HMAC tier gate（與 impl 票 gate 合併裁決） |
| 4 | `WH-P7-NOTIF-contract-doc-sync-v1`（或子票） | §4.6.0 / §4.6.6 env 表 · `impl_status` 更新 |

- **progress_entry**: 本輪 **未** append `00_Agent_Work_Progress.md`（任務邊界 · 僅改本票）
