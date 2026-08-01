# WH-P7-NOTIF-HMAC-prod-mandatory-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-H+1 · **P7 HMAC prod 線 mandatory policy 設計票（doc-only · FRAME 本輪）**  
> 上游：`WH-P7-NOTIF-HMAC-impl-v1`（sender partial · `impl_done`）· `WH-P7-NOTIF-HMAC-receiver-contract-v1`（§4.6.5.2 · `implementer_done_pending_review`）· `WH-P7-NOTIF-PROD-URL-v1` / `WH-P7-NOTIF-PROD-URL-impl-v1`（§4.6.6 tier matrix · URL gate partial）· `WH-P7-NOTIF-RETRY-prod-v1`（tier readiness gate 索引 · `design_accepted`）· `WH-P7-PROD-roadmap-v1`（Wave-P7-3）  
> 產物：staging/prod tier HMAC mandatory policy SSOT 草案；sandbox vs staging vs prod 差異表；合約更新規格；衍伸 impl 票索引。**零 code / 零 CI / 零合約 doc 變更（本輪）**

---

## FRAME

### handoff header

**P7 HMAC prod 線 mandatory policy 設計票**：sender HMAC-SHA256 已 **partial** 實作（env 雙 gate · sandbox default off · **fail-open unsigned**）；receiver contract（§4.6.5.2）已定義驗簽 / 重放 / idempotency，但 **無** reference impl / fixtures；§4.6.6.3 tier matrix 已標 staging/prod **`hmac_required=true`**，但 adapter **尚未** enforce——`TIER=staging|prod` 時仍可能以非簽名 POST 出站（沿用 sandbox fail-open 分支）。本票定義 staging/prod tier 的 HMAC **mandatory** 規則、fail-closed 語意、`blocked_reason` 契約，以及合約 §4.6.0 / §4.6.5 / §4.6.6 須如何補強；**不改 sandbox 行為、不寫實作、不改合約正文**。

---

### 1. Background

| 層級 | 現況 | 證據 |
|------|------|------|
| **Sender HMAC** | **partial**（sandbox-only · env gated · default off） | `WH-P7-NOTIF-HMAC-impl-v1` · `notification_webhook_adapter_v1._apply_hmac_headers` |
| **Env gate** | `GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED=1` **且** `GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET` 非空 → 簽名；否則 **不簽名** | `_should_apply_hmac_signature()` |
| **簽名失敗 / secret 缺失** | **fail-open**：log warning，仍送 **unsigned** POST | impl 票 B_REPORT · §4.6.5.1 |
| **Headers（事實標準）** | `X-Gov-Signature-256` · `X-Gov-Timestamp` · `X-Gov-Event-Id`；signed string = `{timestamp}.{event_id}.{raw_body_utf8}` | adapter · §4.6.5.1 |
| **Receiver contract** | §4.6.5.2 normative SSOT 已落盤；reference impl / fixtures **`not_implemented_yet`** | `WH-P7-NOTIF-HMAC-receiver-contract-v1` |
| **Tier / URL gate** | `TIER` + `URL_ALLOWLIST` minimal gate **partial**（staging/prod https + allowlist）；**未** enforce HMAC mandatory | `WH-P7-NOTIF-PROD-URL-impl-v1` · C_REPORT gaps |
| **§4.6.6.3 matrix** | staging/prod：`hmac_required=**true**`；sandbox：`false`（opt-in partial OK） | `WH-P7-NOTIF-PROD-URL-v1` · 合約 §4.6.6.3 |
| **§4.6.6.4 checklist** | 已索引本票；mandatory enforce **`not_implemented_yet`** | 合約 L705 |
| **Prod 線現況** | adapter 在 `TIER=staging|prod` 且 URL gate 通過後，**仍允許**非 HMAC POST（sandbox fail-open 語意延續） | PROD-URL-impl C_REPORT §3 gaps |

**缺口**：policy 層已宣告 staging/prod HMAC mandatory，但 **sender adapter 無 tier-aware fail-closed 分支**；缺 `HMAC_ENABLED`、空 secret、簽名計算異常時，staging/prod 與 sandbox 行為相同（unsigned POST 或 fail-open skip）。本票填補 **tier HMAC gate** 的 normative 規格真空，對齊 §4.6.6.3 `hmac_required` 與 `WH-P7-NOTIF-RETRY-prod-v1` tier readiness gate 中的 HMAC 檢查項。

**威脅模型（引用 §4.6.1，本票不擴寫）**：staging/prod 對外 POST 若無 HMAC，等同 **trust boundary 缺失**——偽造 payload、中間人篡改、endpoint 誤配時無密鑰驗證；mandatory gate 為升格前置必要條件。

---

### 2. Goal

產出 **staging/prod tier HMAC mandatory policy SSOT 草案**（下一輪 Implementer 擴寫合約 + impl 票 AC），至少定義：

1. **Sandbox 現行 HMAC 行為摘要**（baseline · 本票不變）
2. **Staging / prod HMAC mandatory 要求**（何時必須簽名 · 何時拒 POST）
3. **Tier 對照表**（sandbox vs staging vs prod · HMAC 維度）
4. **Tier HMAC gate 裁決**（fail-closed POST · fail-open dispatch · `blocked_reason` / `blocked_rule`）
5. **合約更新規格**（§4.6.0 / §4.6.5 / §4.6.6 須補強欄位與 cross-ref）
6. **衍伸 impl 票索引**

#### 2.1 Sandbox 現行 HMAC 行為（baseline · 本票不變）

| 項 | 定案（對照現碼 · 只讀） |
|----|-------------------------|
| **Tier** | `sandbox`（或未設 `TIER`） |
| **HMAC mandatory** | **否** — opt-in only |
| **Env gate** | `HMAC_ENABLED=1` **且** `HMAC_SECRET` 非空 → 簽名；否則不簽名 |
| **缺 secret / enabled=0** | **fail-open** — 仍送 unsigned POST；log warning |
| **簽名計算異常** | **fail-open** — `_apply_hmac_headers` catch → unsigned POST |
| **Tier HMAC gate** | **無** — 僅 localhost URL gate（§4.4） |
| **外層語意** | emit / dispatch **fail-open**（`ok=True`） |

> **Partial 邊界**：sandbox 可 opt-in HMAC 演練 signed POST；**不得**誤繼承為 staging/prod 交付語意。

#### 2.2 Staging / prod HMAC mandatory policy（本票 normative 草案）

**原則**：當 `GOV_NOTIFICATION_WEBHOOK_TIER ∈ {staging, prod}` 時，HMAC 為 **policy mandatory**（§4.6.6.3 `hmac_required=true`）；adapter **must not** 以 unsigned POST 出站。與 sandbox **fail-open** 分支 **明確分離**。

##### 2.2.1 Mandatory 條件（proposed_default）

在 `TIER ∈ {staging, prod}` 且 **URL tier gate 已通過**（`WH-P7-NOTIF-PROD-URL-impl-v1`）後、**第一次 HTTP POST 前**，adapter **must** 驗證下列 **全部** 成立：

| 檢查項 | 條件 | 說明 |
|--------|------|------|
| **HMAC master gate** | `GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED=1`（或等價 truthy） | 未設 / `0` → **policy violation** |
| **Secret 存在** | `GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET` 非空（trim 後） | 空 secret → **policy violation**（staging/prod **不得** fail-open unsigned） |
| **event_id 可解析** | outbound payload 含非空 `event_id`（gateway SSOT） | 缺 `event_id` → **policy violation**（無法組 signed string · §4.6.5.1） |
| **簽名可計算** | HMAC-SHA256 計算成功；headers 可附加 | 計算異常 → **policy violation**（staging/prod **不得** fallback unsigned） |

**全部通過** → 進入既有 retry loop（若 tier readiness 亦滿足 RETRY-prod 票）；POST **must** 含 §4.6.5.1 定義之 `X-Gov-Signature-256` · `X-Gov-Timestamp` · `X-Gov-Event-Id`。

**任一失敗** → **reject POST**（fail-closed at HMAC tier gate）：

| 回傳欄位 | proposed_default |
|----------|------------------|
| `webhook_result.ok` | `True`（外層 dispatch fail-open 不變） |
| `webhook_result.dispatched` | `False` |
| `webhook_result.dry_run` | `True` |
| `webhook_result.blocked_reason` | `blocked_by_hmac_tier_policy` |
| `webhook_result.blocked_rule` | 見 §2.2.2 |
| log | tier + rule + **不含** secret 原文 |

##### 2.2.2 `blocked_rule` 枚舉（proposed_default）

| `blocked_rule` | 觸發條件 | staging | prod |
|----------------|----------|---------|------|
| `hmac_disabled` | `HMAC_ENABLED` 未設 / `0` / 非 truthy | reject | reject |
| `hmac_secret_missing` | `HMAC_ENABLED=1` 但 secret 空 | reject | reject |
| `hmac_event_id_missing` | payload 無 `event_id` 或空字串 | reject | reject |
| `hmac_signing_failed` | 簽名計算拋錯或產物不完整 | reject | reject |

> **與 sandbox 對照**：上述四種情況在 **sandbox** tier 下仍為 **fail-open unsigned**（或 skip 簽名）；僅 staging/prod 改為 **reject POST**。

##### 2.2.3 Gate 順序（與 URL / retry readiness 協作）

建議 adapter preflight 順序（impl 票可微調，**不得**在 staging/prod 跳過 HMAC gate）：

```
1. Env master switch（webhook enabled）
2. URL tier gate（§4.6.6 · PROD-URL-impl）
3. HMAC tier gate（本票 · staging/prod only）     ← 本票交付
4. Tier readiness gate（retry + DLQ · RETRY-prod-v1）  ← 可合併或串行
5. HTTP POST + retry loop
```

**Sandbox 豁免**：`TIER=sandbox`（或未設）→ 步驟 3 **跳過**；維持 §2.1 baseline。

**與 RETRY-prod 票關係**：`WH-P7-NOTIF-RETRY-prod-v1` §2.2.3 已索引 HMAC mandatory；本票為 HMAC gate **專票**；impl 時 **must** 裁決合併為單一 `tier_preflight()` 或分離函式，但 staging/prod 語意 **不得** 弱於本 FRAME。

##### 2.2.4 Receiver 側對照（文檔義務 · 本票不實作）

staging/prod sender **must** 送齊 §4.6.5.1 headers 後，receiver（§4.6.5.2）**must** 驗簽；缺 headers 的 inbound request 在 staging/prod integration 場景 **must** 回 401/403（receiver 責任）。本票僅定義 **sender 不得發送 unsigned**；receiver reference impl 留 `WH-P7-NOTIF-HMAC-receiver-fixtures-v1` · `WH-P7-NOTIF-HMAC-receiver-sample-impl-v1`。

#### 2.3 Sandbox vs staging vs prod — HMAC 差異表（normative）

| 維度 | **sandbox** | **staging** | **prod** |
|------|-------------|-------------|----------|
| **`hmac_required`（policy）** | **false** | **true** | **true** |
| **Default HMAC** | off（無 env） | **must** enabled + secret | **must** enabled + secret |
| **缺 `HMAC_ENABLED`** | 不簽名 · 仍 POST | **reject POST** · `hmac_disabled` | **reject POST** |
| **缺 secret** | fail-open unsigned POST | **reject POST** · `hmac_secret_missing` | **reject POST** |
| **簽名失敗** | fail-open unsigned POST | **reject POST** · `hmac_signing_failed` | **reject POST** |
| **缺 `event_id`** | 可送（無 `X-Gov-Event-Id`） | **reject POST** · `hmac_event_id_missing` | **reject POST** |
| **Unsigned POST 允許** | **是**（預設） | **否** | **否** |
| **Tier HMAC gate** | 無 | **有**（fail-closed POST） | **有** |
| **外層 dispatch** | fail-open `ok=True` | fail-open `ok=True`（blocked 時不 POST） | 同上 |
| **CI 使用** | 允許（§4.5 advisory） | **禁止** CI env | **禁止** CI env |
| **Approval** | none | governance_dual | shangshu_prod + security |

**一句話對照**（供 AC 與 handoff）：

- **sandbox**：HMAC **可選**；預設不簽名；缺 secret / 簽名失敗 **fail-open** 仍 POST。
- **staging**：HMAC **強制**；未啟用、缺 secret、缺 `event_id` 或簽名失敗 → **拒 POST** 並記 `blocked_by_hmac_tier_policy`。
- **prod**：同 staging mandatory；語意更嚴（§4.6.6.3「缺簽名 reject POST」）；須尚書省批文後才啟用 tier。

#### 2.4 合約更新規格（Implementer 下一輪 · 本票不動 docs）

下一輪 doc-sync / impl 票 **must** 更新下列位置（本票僅定義需求）：

| 位置 | 更新內容 |
|------|----------|
| **§4.6.0** `webhook_hmac` policy 列 | 增 **tier gate** 語意：`partial` → staging/prod mandatory gate **`not_implemented_yet`**（impl 後 **`partial`**）；sandbox sender 仍 partial opt-in |
| **§4.6.5.1 Sender contract** | 增 **§4.6.5.1.1 Tier HMAC gate**（或等價子標）：staging/prod fail-closed vs sandbox fail-open 對照表；`blocked_reason` / `blocked_rule` |
| **§4.6.5.2 Receiver contract** | cross-ref：staging/prod sender **must not** 送 unsigned；receiver 缺 header → 401（既有） |
| **§4.6.6.3 Tier policy matrix** | `hmac_required` 欄增 **enforce 語意** 脚注：sandbox = opt-in partial；staging/prod = adapter gate reject（impl 票 `WH-P7-NOTIF-HMAC-prod-impl-v1`） |
| **§4.6.6 env 表** | `HMAC_ENABLED` / `HMAC_SECRET` 列增 **tier 語意** 欄或脚注：staging/prod **required**；sandbox optional |
| **§4.6.6.4 Enablement checklist** | 本票 FRAME sign-off 後，impl 票完成時更新 `impl_status` |

**`hmac_required` 欄位擴寫建議（§4.6.6.3）**：

| tier | `hmac_required`（policy） | `hmac_enforce`（runtime · proposed） |
|------|---------------------------|--------------------------------------|
| `sandbox` | false | opt-in · fail-open unsigned |
| `staging` | true | adapter gate · reject if not signed-ready |
| `prod` | true | 同 staging · + governance 批文 |

> Implementer 可將 `hmac_enforce` 併入 `hmac_required` 脚注，避免雙表漂移。

#### 2.5 交付位置偏好（Implementer 下一票）

| 方案 | 位置 | 採用 |
|------|------|------|
| **A — 擴寫 §4.6.5.1 + §4.6.6.3 脚注** | `docs/outbox-and-feedback-layer-contract-v1.md` | **首選** |
| **B — §4.6.6.3 matrix 連結** | 摘要句 + 本票 FRAME cross-ref | 輔助 |

§4.6.0 `webhook_hmac` 在 impl 票完成後：`partial` → staging/prod tier gate **`partial`**（sandbox 仍 partial opt-in）。

---

### 3. Non-Goals

- ❌ **不實作** tier HMAC gate、adapter 分支、或任何 Python / test / CI 變更。
- ❌ **不改** sandbox 行為 — default HMAC off · fail-open unsigned · opt-in 演練 **維持不變**。
- ❌ **不實作** receiver 端驗簽程式、fixtures、sample impl（→ `WH-P7-NOTIF-HMAC-receiver-fixtures-v1` · `WH-P7-NOTIF-HMAC-receiver-sample-impl-v1`）。
- ❌ **不修改** `docs/outbox-and-feedback-layer-contract-v1.md`（本輪 FRAME-only）。
- ❌ **不改** sender header 格式、signed string、env 鍵名（以 `WH-P7-NOTIF-HMAC-impl-v1` 為事實標準）。
- ❌ **不實作** retry / DLQ tier readiness gate 本體（→ `WH-P7-NOTIF-RETRY-prod-impl-v1`）；本票僅定義 HMAC 與其 **順序 / 依賴**。
- ❌ **不啟用**真實 staging/prod endpoint 或要求尚書省執行 prod rollout。
- ❌ **不升格** advisory CI；staging/prod HMAC gate 驗證留 impl + CI 票。
- ❌ **不合併** Phase 8.8 `orchestration_bridge_outbox`（§2.2 永久分軌）。
- ❌ **不修改** 其他票檔 · `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `.cursor/rules/**`。

---

### 4. Acceptance Criteria（設計層 · 本票 FRAME）

- **AC-1**：FRAME 含 Background / Goal / Non-goals / AC / AllowedPaths / BlockedPaths（本檔）。
- **AC-2**：§2.1 準確描述 sandbox 現行 HMAC 行為（opt-in · fail-open unsigned · 無 tier gate）。
- **AC-3**：§2.2 定義 staging/prod **mandatory** HMAC（四項檢查 · reject POST · `blocked_reason` / `blocked_rule`）。
- **AC-4**：§2.3 **tier 對照表** 清楚列出 sandbox vs staging vs prod 在「HMAC 是否 mandatory」上的差異（≥8 維度）。
- **AC-5**：§2.2.3 gate 順序與 PROD-URL-impl blocked 語意一致（fail-closed POST · fail-open dispatch `ok=True`）。
- **AC-6**：§2.4 指明合約 §4.6.0 / §4.6.5 / §4.6.6 須如何補強 `hmac_required` / tier enforce 描述。
- **AC-7**：列出 ≥2 張 **後續實作票**（§5）。
- **AC-8**：與 `WH-P7-NOTIF-PROD-URL-v1` §4.6.6.3 matrix · `WH-P7-NOTIF-RETRY-prod-v1` §2.2.3 HMAC 整合 · `WH-P7-NOTIF-HMAC-impl-v1` sender 行為 **無矛盾**。
- **AC-9**：文檔工單自檢（APP-DOC）：FRAME 正文零本機絕對路徑、零 secret / 真實 URL 範例、禁區僅類型描述。

#### AC 交付物對照（下一輪 · 非本票）

| 交付物 | 位置 | 本票狀態 |
|--------|------|----------|
| §4.6.5.1 tier HMAC gate 擴寫 | `docs/outbox-and-feedback-layer-contract-v1.md` | **待 impl / doc-sync 票** |
| adapter tier HMAC gate | `delivery/notification_webhook_adapter_v1.py` | **待 `WH-P7-NOTIF-HMAC-prod-impl-v1`** |
| §4.6.0 / §4.6.6 env 表 tier 列 | 合約 doc | **待 doc-sync 票** |

---

### 5. 建議衍伸實作票（本票外 · AC-7 要求）

| 票號（建議） | 範圍摘要 | 依賴 |
|--------------|----------|------|
| **`WH-P7-NOTIF-HMAC-prod-impl-v1`** | adapter tier HMAC gate：`TIER ∈ {staging,prod}` 時驗證 HMAC_ENABLED + secret + event_id + 簽名成功；失敗 → `blocked_by_hmac_tier_policy` + `blocked_rule`；sandbox regression（fail-open 不變）；unittest matrix（≥6 scenario）；§4.6.5.1 / §4.6.6.3 擴寫 | 本票 FRAME · `WH-P7-NOTIF-HMAC-impl-v1` · `WH-P7-NOTIF-PROD-URL-impl-v1` |
| **`WH-P7-NOTIF-HMAC-prod-ci-v1`** | CI / doc lint：assert §4.6.6.3 `hmac_required` 與 adapter gate 一致；fixture env matrix（**仍 sandbox-only job** · 不開 staging/prod URL）；可含 tier gate unittest 子集為 advisory check | HMAC-prod-impl-v1 |
| `WH-P7-NOTIF-contract-doc-sync-v1`（或子票） | §4.6.0 `webhook_hmac` · §4.6.6 env 表 · `impl_status` 更新 | HMAC-prod-impl-v1 |

> **升格順序（對齊 §4.6.6.4 · `WH-P7-PROD-roadmap-v1` Wave-P7-3）**：HMAC-impl ✅ → PROD-URL-impl partial ✅ → **本票 design** → HMAC-prod-impl →（可並行 RETRY-prod-impl gate 合併裁決）→ receiver fixtures → staging-integration → prod rollout。

**`WH-P7-NOTIF-HMAC-prod-impl-v1` 建議 unittest scenario（草案）**

| # | Scenario | 斷言 |
|---|----------|------|
| 1 | sandbox · HMAC off | unsigned POST 仍成功（regression） |
| 2 | sandbox · HMAC on · secret 空 | fail-open unsigned POST（regression） |
| 3 | staging · HMAC off | 不 POST · `blocked_rule=hmac_disabled` |
| 4 | staging · HMAC on · secret 空 | 不 POST · `blocked_rule=hmac_secret_missing` |
| 5 | staging · HMAC ready · allowlist OK | signed POST · headers 存在 |
| 6 | prod · HMAC ready · allowlist missing | URL gate 先阻（與 HMAC gate 順序 regression） |
| 7 | staging · payload 無 `event_id` | 不 POST · `blocked_rule=hmac_event_id_missing` |

---

### 6. AllowedPaths / BlockedPaths

#### AllowedPaths

- `04_Workflows/tickets/WH-P7-NOTIF-HMAC-prod-mandatory-v1_state.md`（本票 STATE / FRAME / B/C/D_REPORT）

> 未來可能更新合約文字的票（doc-sync · HMAC-prod-impl）在本票僅作 **reference**；本票 **不動** docs。

#### BlockedPaths

- `delivery/**`（含 `notification_webhook_adapter_v1.py` — 本票 **只讀** 對照）
- `tests/**` · `docs/**` · `.github/workflows/**`
- `routing/**` · `scripts/**` · 暗部 `gov_core_system/core/**`
- 其他票檔 · `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `.cursor/rules/**`
- `.env` · secrets · 客戶實際 webhook URL
- `04_Workflows/00_Agent_Work_Progress.md`（Progress append 留 Scribe 輪）

---

### 7. Dependencies

- `WH-P7-NOTIF-HMAC-impl-v1`（sender HMAC partial · headers / signed string SSOT）
- `WH-P7-NOTIF-HMAC-receiver-contract-v1`（§4.6.5.2 receiver 驗簽 / idempotency）
- `WH-P7-NOTIF-HMAC-policy-v1`（HMAC policy 母本 · `frame_ready`）
- `WH-P7-NOTIF-PROD-URL-v1` / `WH-P7-NOTIF-PROD-URL-impl-v1`（§4.6.6.3 `hmac_required` · URL gate partial）
- `WH-P7-NOTIF-RETRY-prod-v1`（tier readiness gate HMAC 索引 · `design_accepted`）
- `WH-P7-sandbox-line-wrapup-v1`（sandbox 封箱 · prod handoff）
- `WH-P7-PROD-roadmap-v1`（Wave-P7-3 HMAC prod mandatory 索引）
- `docs/outbox-and-feedback-layer-contract-v1.md` §4.6.5 · §4.6.6（只讀）
- `delivery/notification_webhook_adapter_v1.py`（只讀 · HMAC 段）

---

## STATE

- **overall_status**: `done_with_gaps`
- **current_owner**: scribe
- **next_action**: receiver fixtures + 真 staging env 演練（execute 票）；sandbox fail-open 分支不退化
- **last_updated**: 2026-06-23 · progress agent (design SSOT + impl validated 收口)
- **wave**: Wave-H+1 · P7 prod line · HMAC mandatory policy design
- **status_by_role**:
  - **Orchestrator (A)**: done — FRAME 已落盤
  - **Implementer (B)**: done — `WH-P7-NOTIF-HMAC-prod-impl-v1` **validated**（unittest tier gate）
  - **Reviewer (C)**: done — 2026-06-23 · **`accepted_with_gaps`**（design FRAME + impl 對照 §4.6.6.3）
  - **Scribe (D)**: done — 2026-06-23 · D_REPORT 收口
- **notes**:
  - FRAME normative 規格已由 `WH-P7-NOTIF-HMAC-prod-impl-v1` unittest 落地；**未**在真 staging/prod env enforce
  - sandbox fail-open unsigned **不變**

---

## B_REPORT

- **status**: design SSOT · impl 由 `WH-P7-NOTIF-HMAC-prod-impl-v1` 承接（**validated** · 39/39 webhook unittest 含 HMAC tier gate）
- **design_deliverable**: FRAME §2.1–§2.4 tier HMAC mandatory · fail-closed POST · `blocked_by_hmac_tier_policy` 契約
- **impl_cross_ref**: `WH-P7-NOTIF-HMAC-prod-impl-v1` B/C_REPORT · 合約 §4.6.5.1 tier gate 段落（doc-sync 票索引）

---

## C_REPORT

- **review_date**: 2026-06-23
- **reviewer_role**: P7 HMAC prod mandatory Reviewer (C)
- **verdict**: **`accepted_with_gaps`**
- **conclusion**: FRAME 與 §4.6.6.3 `hmac_required` · RETRY-prod readiness HMAC 項 · PROD-URL-impl gate 順序 **一致**；impl 票已 validated（unittest only）。
- **gaps**: 真 env enforce · receiver 驗簽鏈 · contract-doc-sync §4.6.5 tier 正文微調仍 deferred。

---

## D_REPORT

- **handoff_date**: 2026-06-23
- **from**: P7 HMAC prod mandatory policy（`done_with_gaps` · design + impl unittest）
- **to**: staging S3 演練（receiver fixtures · execute 票）
