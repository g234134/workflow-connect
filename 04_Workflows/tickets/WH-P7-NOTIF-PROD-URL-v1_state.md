# WH-P7-NOTIF-PROD-URL-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-H+1 · **prod URL / tier / allowlist policy 設計票（doc-only · FRAME 本輪）**  
> 上游：`WH-P7-sandbox-line-wrapup-v1`（sandbox 線已封箱）· `WH-P7-NOTIF-PROD-policy-v1`（§4.6 骨架 · `design_accepted`）  
> 產物：§4.6.6 tier / URL / allowlist 完整 policy 表 + 升格前置條件 + 衍伸實作票索引；**零程式、零 CI 變更（本輪僅 FRAME）**

---

## FRAME

### 1. Background

P7 **sandbox 通知線已封箱**（`WH-P7-sandbox-line-wrapup-v1` · `validated`）。sandbox 線 URL 行為已固定：

| 面向 | sandbox 現況 | 證據 |
|------|--------------|------|
| URL gate | **localhost / 127.0.0.1 only** | `notification_webhook_adapter_v1._is_safe_sandbox_url()` · §4.4 |
| Env | `GOV_NOTIFICATION_WEBHOOK_URL` 可設，但 non-localhost **拒絕 POST**（`dry_run` / unsafe URL） | WD-P7-T2 · **12/12** 基線 |
| CI | `p7-notification-smoke.yml` 固定 `http://127.0.0.1:8080/webhook` · advisory · non-blocking | §4.5 · Wave-G |
| Tier env | `GOV_NOTIFICATION_WEBHOOK_TIER` **未讀取** | §4.6.6 env 表 · `not_implemented_yet` |
| Allowlist env | `GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST` **未讀取** | 同上 |

**prod / staging URL 目前完全未定義**：合約 §4.6.6 僅有一段三級 tier 摘要與 env 鍵草案（`TIER` / `URL_ALLOWLIST` 標 `not_implemented_yet`），**缺少**可審計的 tier 定義表（allowed_hosts / 強制 HMAC / retry / DLQ / 批文門檻）、host/path pattern 語法、以及「升格至 staging/prod 前須完成哪些票」的硬性前置清單。

**風險**：若未制度化即允許 `GOV_NOTIFICATION_WEBHOOK_URL` 指向外部客戶 endpoint，可能觸發 **SSRF / 資料外洩 / 法遵（未授權 PII 出站）/ SLA（retry 無 DLQ 時 silent loss）**；CI 或開發機誤設 prod URL 亦可能對客戶 production webhook 造成非預期流量。本票填補該 policy 真空，**不啟用任何對外 POST、不改 sandbox 行為**。

**與既有 partial 能力的關係**：retry（`WH-P7-NOTIF-RETRY-SANDBOX-v1`）與 HMAC sender（`WH-P7-NOTIF-HMAC-impl-v1`）僅在 **sandbox localhost** 上 opt-in；§4.6.6 尚未定義 staging/prod 下這些能力是否 **mandatory**、與 URL allowlist 的依賴鏈（`TIER` → allowlist → HMAC? → retry? → DLQ?）。

### 2. Goal

產出 **prod URL / tier / allowlist policy SSOT**，作為合約 §4.6.6 的完整規格（Implementer B 輪落盤目標），須包含：

#### 2.1 `GOV_NOTIFICATION_WEBHOOK_TIER` 語意

| tier 值 | 語意（草案 · B 輪定稿） |
|---------|-------------------------|
| `sandbox`（default） | 等同 §4.4：僅 `localhost` / `127.0.0.1`；CI / 開發預設；**禁止** non-localhost |
| `staging` | 允許 **內部 staging host**（allowlist 內）；須 HMAC + retry + DLQ **policy 層 mandatory**（實作待 impl 票）；須 **Wave-H Governance 雙人批准**（類型描述，不寫實例路徑） |
| `prod` | 允許 **per-customer registered endpoint**（allowlist + registry）；HMAC **mandatory**（缺簽名須拒絕 POST，與 sandbox fail-open 不同）；retry + DLQ **mandatory**；須 **尚書省 prod 批文** + Security sign-off |

**解析規則（future impl 對照）**：

- 未設 `TIER` → 視為 `sandbox`（向後相容 §4.4）。
- `TIER` 與 `URL` host 不一致 → adapter **must reject**（fail-closed at URL gate，仍不 raise 至 orchestrator emit 層；對齊 dispatch fail-open 外層語意）。
- CI workflow（§4.5）**must** 固定 `TIER=sandbox`（或未設）；**禁止** CI job env 使用 `staging` / `prod`。

#### 2.2 非 sandbox tier 的 URL allowlist 規則

定義 `GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST` 語意（**B 輪落盤至 §4.6.6**）：

| 規則項 | 草案 |
|--------|------|
| **格式** | 逗號分隔 entry；每 entry = `host` 或 `host:port` 或 `host/path-prefix` glob（本票 B 輪定稿 exact grammar） |
| **host pattern** | 允許 literal hostname、`**` 尾綴子域（如 `*.staging.internal.example`）；**禁止** bare IP（staging/prod 須具名 host，減 SSRF 面） |
| **path pattern** | 可選 `/webhook` 或 `/webhook/*`；未指定 path → 僅匹配 host（全 path 允許 — B 輪須裁決是否限縮） |
| **與 `URL` 關係** | `GOV_NOTIFICATION_WEBHOOK_URL` 的 `(scheme, host, port, path)` **must** match 至少一 allowlist entry；scheme **must** be `https`（staging/prod）；`http` 僅 sandbox localhost |
| **registry（prod）** | prod tier 額外要求 endpoint 登記於 **per-customer registry**（檔案或 DB 類型 · 不寫實例路徑）；allowlist 為全域上限，registry 為客戶級精確允許 |
| **硬規則** | **禁止** sandbox tier / CI / 未批文環境將 URL 設為客戶 **production** hostname（§4.6.6 須列 negative example 類型，不寫真實域名） |

#### 2.3 staging / prod 啟用前置條件（gating checklist）

下列為 **policy 層 mandatory**；B 輪 §4.6.6 須以表格 + 票號 cross-ref 寫死：

| 前置項 | staging 最低要求 | prod 最低要求 | 對應票 / 合約 |
|--------|-------------------|---------------|---------------|
| Retry（非零 attempts） | **required**（policy） | **required** | `WH-P7-NOTIF-RETRY-SANDBOX-v1` 為 sandbox partial；staging/prod 升格需 **prod retry + DLQ 票** |
| DLQ 落盤 | **required** | **required** | `WH-P7-NOTIF-DLQ-v1` · §4.6.4 |
| HMAC sender | **required**（enabled + secret） | **required** | `WH-P7-NOTIF-HMAC-impl-v1`（partial → staging/prod mandatory 升格） |
| HMAC receiver contract | **required**（文檔 SSOT） | **required** | `WH-P7-NOTIF-HMAC-receiver-contract-v1` · §4.6.5.2 |
| Receiver fixtures / sample impl | recommended | **required** | `WH-P7-NOTIF-HMAC-receiver-fixtures-v1` · `WH-P7-NOTIF-HMAC-receiver-sample-impl-v1` |
| URL tier + allowlist **程式** gate | **required** | **required** | `WH-P7-NOTIF-PROD-URL-impl-v1`（本票衍伸） |
| Advisory CI 穩定 | N/A | recommended → future required CI 票 | `p7-notification-smoke` 仍 sandbox-only |
| Governance 批文 | Wave-H 雙人批准 | **尚書省 prod 批文** + Security | §4.6.7 門檻 |

**啟用順序（建議 · Orchestrator 裁決）**：DLQ → prod retry 升格 → HMAC receiver fixtures → **PROD-URL-impl** → staging 整合測試（人工 env）→ prod 批文後 rollout。

#### 2.4 交付位置偏好（本票 FRAME 裁決）

**方案 A — 直接擴寫 `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.6（首選）**

- 理由：`WH-P7-NOTIF-PROD-policy-v1` 已將 URL policy 錨定於 §4.6.6；§4.6.0 `webhook_url_tier` 列已 cross-ref 同節；避免雙 SSOT；sandbox wrap-up 與 partial validation 均以 §4.6.6 env 表為索引。
- B 輪作法：將現 §4.6.6 一段摘要**替換/擴寫**為：
  - **§4.6.6.1** Tier 定義與 env 解析
  - **§4.6.6.2** URL allowlist grammar & matching rules
  - **§4.6.6.3** **Tier policy 對照表**（AC 欄位：`tier` / `allowed_hosts` / `hmac_required` / `retry_required` / `dlq_required` / `approval_required`）
  - **§4.6.6.4** Staging / prod 啟用前置 checklist（票號索引）
  - 保留並更新現 env 鍵表（與 §4.6.0 一致）

> **不採方案 B**（獨立 `docs/notification-webhook-url-tier-policy-v1.md`）：除非 B 輪 Reviewer 認定 §4.6.6 過長；若採 B，§4.6.6 僅保留摘要 + 連結，**tier 對照表仍須在 §4.6.6 可見**（至少嵌入精簡表或 normative 引用句）。

### 3. Non-Goals

- ❌ **不實作**任何 tier 判斷、allowlist 解析、或 URL gate 程式邏輯（含 `notification_webhook_adapter_v1`、tests、CI）。
- ❌ **不改**現有 sandbox 行為 — §4.4 localhost-only、fail-open、retry/HMAC sandbox partial、advisory CI 均維持不變。
- ❌ **不開啟**任何真實對外 endpoint — 不設定 prod/staging URL、不要求尚書省執行 prod rollout。
- ❌ **不修改** Python / YAML / tests / `.github/workflows/**`（本輪 FRAME-only；B 輪亦僅 docs）。
- ❌ **不升格** advisory CI 為 required check；CI 仍固定 sandbox localhost mock。
- ❌ **不合併** Phase 8.8 `orchestration_bridge_outbox`（§2.2 永久分軌）。
- ❌ **不寫**客戶真實 webhook URL、secret、或本機絕對路徑（APP-DOC）。

### 4. Acceptance Criteria

- **AC-1**：§4.6.6（或 §4.6.6.3 + cross-ref）含 **tier policy 對照表**，至少欄位：

  | 欄位 | 說明 |
  |------|------|
  | `tier` | `sandbox` \| `staging` \| `prod` |
  | `allowed_hosts` | host/path pattern 摘要（非 exhaustive 實例值） |
  | `hmac_required` | bool · policy mandatory |
  | `retry_required` | bool · `max_attempts ≥ 1` policy |
  | `dlq_required` | bool |
  | `approval_required` | none \| governance_dual \| shangshu_prod |

- **AC-2**：§4.6.6 明確列出 **staging / prod 啟用前須先完成的票**（至少：DLQ · prod retry 升格 · HMAC sender+receiver · receiver fixtures · `WH-P7-NOTIF-PROD-URL-impl-v1` · governance 批文），與 §2.3 checklist 一致。
- **AC-3**：allowlist grammar（host / path glob / scheme=https）**唯一且可審計**；含 CI 禁止 staging/prod tier 硬規則。
- **AC-4**：`impl_status` 維持：`TIER` / `URL_ALLOWLIST` / prod tier gate = **`not_implemented_yet`**；sandbox localhost check = **`implemented`**（與現碼一致）。
- **AC-5**：至少列出 **1 張**後續實作票 `WH-P7-NOTIF-PROD-URL-impl-v1`（tier 判斷 + allowlist + https gate + unittest）；附建議 AC 一句話。
- **AC-6**：B_REPORT 含與 `WH-P7-sandbox-line-wrapup-v1` B_REPORT §2「不能做什麼」、§4.6.6 現 env 表、§4.5 CI env 的對照（無矛盾）。
- **AC-7**：文檔工單自檢（APP-DOC）：零本機絕對路徑、零 secret / 真實 URL 範例、禁區僅類型描述。

#### §4.6.6.3 Tier policy 對照表（FRAME 草案 · B 輪 normative 定稿）

> 下列為 FRAME 預填；Implementer B 輪寫入合約時可微調措辞，**不得**放寬 prod mandatory 欄位。

| tier | allowed_hosts | hmac_required | retry_required | dlq_required | approval_required |
|------|---------------|---------------|----------------|--------------|-------------------|
| `sandbox` | `localhost`, `127.0.0.1` only；`http`+`https` | false（opt-in partial OK） | false（default `max_attempts=0`） | false | none |
| `staging` | allowlist 內 **internal** named hosts；**https only** | **true** | **true** | **true** | governance_dual |
| `prod` | allowlist ∩ per-customer registry；**https only** | **true**（缺簽名 **reject POST**） | **true** | **true** | shangshu_prod + security |

### 5. 衍伸實作票（本票外 · FRAME 索引）

| 票號 | 範圍摘要 | 依賴 |
|------|----------|------|
| **`WH-P7-NOTIF-PROD-URL-impl-v1`** | 在 adapter 讀取 `GOV_NOTIFICATION_WEBHOOK_TIER` + `URL_ALLOWLIST`；實作 host/path match、https gate、staging/prod 與 sandbox 分支；unittest 覆蓋 reject/accept matrix | 本票 AC-1–AC-3 定稿 · sandbox 行為 regression |
| `WH-P7-NOTIF-DLQ-v1` | §4.6.4 DLQ 落盤；staging/prod retry 失敗可觀測 | retry partial |
| `WH-P7-NOTIF-RETRY-prod-v1`（或 DLQ 併票） | 將 retry 從 sandbox-only 升格至 staging/prod tier gate | DLQ · 本票 tier 表 |
| `WH-P7-NOTIF-HMAC-prod-mandatory-v1` | staging/prod 缺 HMAC 拒絕 POST（fail-closed）；與 sandbox fail-open 分支 | HMAC-impl · 本票 `hmac_required` |
| `WH-P7-NOTIF-staging-integration-v1` | 人工 env staging 整合測試（非 CI prod URL）；mock 或內部 staging endpoint | PROD-URL-impl · receiver fixtures |

### 6. AllowedPaths / BlockedPaths

| Allowed | Blocked |
|---------|---------|
| `04_Workflows/tickets/WH-P7-NOTIF-PROD-URL-v1_state.md`（本票） | `delivery/**` · `routing/**` · `scripts/**` · `tests/**` |
| `docs/outbox-and-feedback-layer-contract-v1.md`（**§4.6.6 擴寫 · B 輪**） | `.github/workflows/**` |
| `docs/notification-webhook-url-tier-policy-v1.md`（**可選附錄 · 僅當 Reviewer 選方案 B**） | 暗部 `gov_core_system/core/**` |
| | `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `.cursor/rules/**` |
| | `.env` · secrets · 客戶實際 webhook URL |
| | 其他票檔之 C/D_REPORT（除非 Reviewer 交叉引用） |

### 7. Dependencies

- `WH-P7-sandbox-line-wrapup-v1`（`validated` · prod handoff 入口）
- `WH-P7-NOTIF-PROD-policy-v1`（`design_accepted` · §4.6 骨架）
- `docs/outbox-and-feedback-layer-contract-v1.md` §4.4 · §4.5 · §4.6.0–§4.6.6（現狀 SSOT）
- Partial：`WH-P7-NOTIF-RETRY-SANDBOX-v1` · `WH-P7-NOTIF-HMAC-impl-v1` · `WH-P7-NOTIF-HMAC-receiver-contract-v1`

---

## STATE

- **overall_status**: `done_with_gaps`
- **current_owner**: scribe
- **next_action**: 真 staging/prod env 啟用留 `WH-P7-NOTIF-staging-integration-execute-v1` · governance 批文
- **last_updated**: 2026-06-23 · reviewer + scribe (C/D)
- **wave**: Wave-H+1 · P7 prod URL / tier policy design
- **status_by_role**:
  - **Orchestrator (A)**: done — 開票 FRAME
  - **Implementer (B)**: done — §4.6.6.1–§4.6.6.4 + env 表落盤合約
  - **Reviewer (C)**: done — 2026-06-23 · **`accepted_with_gaps`**
  - **Scribe (D)**: done — 2026-06-23 · D_REPORT 收口
- **notes**:
  - §4.6.6.3 tier matrix normative SSOT 已落盤合約
  - runtime gate 由 `WH-P7-NOTIF-PROD-URL-impl-v1`（**validated**）承接 · staging 演練 `WH-P7-PROD-staging-smoke-runbook-v1` S1

---

## B_REPORT

> Implementer (B) · 2026-06-22 · doc-only · 文檔工單自檢：見 APP-DOC（零本機絕對路徑 · 零 secret / 真實 URL · 禁區僅類型描述）✅

### §1 變更檔案

| 檔案 | 變更 |
|------|------|
| `docs/outbox-and-feedback-layer-contract-v1.md` | §4.6.6 擴寫為 §4.6.6.1–§4.6.6.4 + env 表 + impl_status 摘要 |
| `04_Workflows/tickets/WH-P7-NOTIF-PROD-URL-v1_state.md` | B_REPORT / STATE |

### §2 §4.6.6 落盤摘要

| 子節 | 內容 |
|------|------|
| **§4.6.6.1 Tier semantics** | 定義 `sandbox` / `staging` / `prod` 三級；sandbox = §4.4 localhost-only（**implemented**）；staging/prod = 設計目標（**not_implemented_yet**）；未設 `TIER` → sandbox；CI 禁止 staging/prod |
| **§4.6.6.2 URL allowlist grammar** | 逗號分隔 entry；`host` / `host:port` / `host/path-prefix`；子域 `*.` glob；staging/prod https-only、禁止 bare IP；sandbox/staging/prod 範例 entry；**僅 grammar，非 impl** |
| **§4.6.6.3 Tier policy matrix** | normative 表：`allowed_hosts` / `hmac_required` / `retry_required` / `dlq_required` / `approval_required`；與 FRAME §4 AC-1 草案一致 |
| **§4.6.6.4 Enablement checklist** | 升格 staging/prod 前置：DLQ · RETRY-prod · HMAC prod mandatory · receiver contract/fixtures/sample · **PROD-URL-impl** · staging 整合 · governance 批文 · CI sandbox-only |

### §3 仍為設計目標 / `not_implemented_yet`

- `GOV_NOTIFICATION_WEBHOOK_TIER` / `URL_ALLOWLIST` **程式讀取與 gate**
- **staging / prod** tier 啟用與 non-localhost POST
- allowlist 解析、https gate、per-customer registry match（→ `WH-P7-NOTIF-PROD-URL-impl-v1`）
- prod mandatory HMAC reject、prod retry + DLQ（→ 各衍伸 impl 票）

### §4 與 sandbox wrap-up / CI 對照

| 來源 | 對照結果 |
|------|----------|
| `WH-P7-sandbox-line-wrapup-v1` B_REPORT §2「不能做什麼」 | ✅ 一致：non-localhost / DLQ / prod HMAC 強制仍留 prod 線 |
| §4.6.6 env 表 | ✅ `TIER` / `URL_ALLOWLIST` = **not_implemented_yet**；sandbox URL = **implemented** |
| §4.5 / `p7-notification-smoke.yml` | ✅ CI 固定 `127.0.0.1:8080`、未設 `TIER`；§4.6.6 明文 CI 禁止 staging/prod tier |

### §5 驗證

- 無 runtime 驗證（純文檔票）。
- 人工對照 FRAME AC-1–AC-7 與 §4.6.0 policy 表 `webhook_url_tier` 列。

### §6 阻塞

無 blocking。

---

## C_REPORT

- **review_date**: 2026-06-23
- **reviewer_role**: P7 prod URL policy Reviewer (C)
- **verdict**: **`accepted_with_gaps`**
- **conclusion**: §4.6.6.1–§4.6.6.4 tier matrix · allowlist grammar · enablement checklist 與 sandbox wrap-up · §4.5 CI 邊界 **無矛盾**；設計 SSOT 可作 impl 票 AC 依據。
- **gaps**: 本票 **doc-only**；runtime tier/allowlist gate 由 `WH-P7-NOTIF-PROD-URL-impl-v1`（**validated** · unittest only）承接；真 env 啟用仍 deferred。

---

## D_REPORT

- **handoff_date**: 2026-06-23
- **from**: P7 prod URL / tier policy design（`done_with_gaps`）
- **to**: staging integration wave（env-config · smoke-runbook · execute 票）
- **notes**: 勿在 governance 批文前 flip `TIER=staging/prod`。
