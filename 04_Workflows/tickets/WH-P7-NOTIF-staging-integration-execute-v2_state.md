# WH-P7-NOTIF-staging-integration-execute-v2 — Ticket State

> handoff 摘要檔；P7 **staging tier 真 Infra / 客戶 endpoint Round-2 演練** execution 票 · Ops/Oncall 面向。  
> 目的：在**真** staging deployment（非 local slot）依 `WH-P7-PROD-staging-smoke-runbook-v1` 完成 Phase S1–S4，並啟動 **48h 穩定觀測**；承接 Round-1 local slot 證據。

---

## FRAME

### Goal

在 Wave-H **真 governance_dual** 批文、Infra staging slot、Security 審查與客戶 staging allowlist 就緒後，依 smoke-runbook S1–S4 於**真 staging endpoint**（非 localhost · 非 prod）執行 Round-2 拔線演練，產出可審計 run log；完成後啟動或排程 **48h 觀測窗口**（DLQ 數量 · 失敗 POST · 重試行為）。

### 上游引用

| 來源 | 角色 |
|------|------|
| **`WH-P7-NOTIF-staging-integration-execute-v1`** | Round-1 · local slot · run_id `20260623T165252Z` · **`validated`** |
| **`WH-P7-PROD-staging-smoke-runbook-v1`** | S1–S4 步驟 SSOT · **`validated`** |
| **`WH-P7-PROD-staging-env-config-v1`** | env matrix · rollback 包 · **`validated`** |
| **`WH-P7-PROD-staging-env-bootstrap-v1`** | S0 provision · local slot **`done_with_gaps`** — Round-2 須 **Infra 真 slot 另 provision** |
| **`WH-P7-PROD-staging-integration-v1`** | checklist §A–§D · S4 48h 前置 · **`validated`** |

### 核心 checklist

- [x] **前置**：Wave-H **`governance_dual`** 真批文留痕（`GOV-DUAL-APPROVAL-2026-07-13-01` · `approved` · 2026-07-28）· **≠** Round-2 GO。
- [ ] **前置**：Infra staging deployment slot / HTTPS endpoint 已配置（non-prod host · allowlist 內）。
- [ ] **前置**：Security 對外部 POST 風險審查通過（allowlist · secret 管理 · 無 prod URL 混入）。
- [ ] **前置**：客戶 staging endpoint allowlist 就緒（**禁止** prod endpoint）。
- [ ] **前置**：Receiver 鏈在 staging slot 可驗簽（`WH-P7-NOTIF-HMAC-receiver-fixtures-impl-v1` 參考 impl 可部署或客戶 receiver 就緒）。
- [ ] **前置／閘門**：尚書省**明示 Round-2 GO**（另於對話／批文；H1 approved **不解**本項）。
- [ ] **S1**：F0–F2 + HMAC co-ready；allowlist match POST 2xx；miss → `blocked_by_url_tier_policy`。
- [ ] **S2**：`DLQ_ENABLED=1` + staging 分軌 path；健康 path 無 DLQ 行；503 注入 → inspect `list` +1。
- [ ] **S3**：signed POST headers 齊；enforce 模式下缺 secret 不 POST；receiver 驗簽通過。
- [ ] **S4**：retry enforce；503 至 retry 用盡 → DLQ +1；happy path 無 DLQ。
- [ ] **48h 觀測**：S1–S4 全 GO 後記錄觀測窗口起訖 · 監看 DLQ 數量 · 失敗 POST · 重試行為。
- [ ] 各 phase 記錄 `event_id`、adapter log 摘要、inspect CLI JSON；演練結束執行 rollback 包。
- [ ] Progress 末尾 append 戰報；cross-ref Round-1 execute 票 D_REPORT。

### Non-goals

- ❌ 不 flip prod tier · 不設 prod URL · 不動 prod env。
- ❌ 不改 `p7-notification-smoke.yml`（CI 仍 advisory · sandbox-only）。
- ❌ 不把 staging 證據說成 prod-ready 或 required CI 已升格。
- ❌ 不調 Phase%。

### AllowedPaths

- staging deployment env（Infra 人工 flip · 非 CI）
- `04_Workflows/tickets/WH-P7-NOTIF-staging-integration-execute-v2_state.md`
- `04_Workflows/tickets/WH-P7-NOTIF-staging-integration-execute-v1_state.md`（D_REPORT cross-ref 一句）
- `04_Workflows/tickets/WH-P7-PROD-prod-rollout-governance-bootstrap-v1_state.md`（G1–G8 checklist 狀態文字）
- `04_Workflows/00_Agent_Work_Progress.md`（**末尾 append only**）

### Acceptance Criteria

- **AC-1**：必備前置批文／條件 D_REPORT 可審計；未齊則 **blocked**、不執行 POST。
- **AC-2**：前置齊備時 S1–S4 各 phase 有 log 摘要 + go/no-go + 新 `run_id`。
- **AC-3**：rollback 演練通過 · 無 orphan staging POST 至 prod。
- **AC-4**：48h 觀測已啟動，或 B_REPORT 誠實標 gap + 下一步。
- **AC-5**：Progress 戰報已 append。

---

## STATE

- **overall_status**: `blocked`
- **current_owner**: orchestrator
- **next_action**: **blocked** — **P-1 已解**（`GOV-DUAL-APPROVAL-2026-07-13-01` · **`approved`** · 2026-07-28 具名）· **P-2–P-5 仍未齊**（Infra／Security／allowlist／receiver）· **無尚書省 Round-2 GO** → **禁止**分配 `run_id`／跑 S1–S4。票已 **armed**（閘門矩陣就緒）。Track A Round-2 閘門再確認（2026-07-28）：五頂未齊＋無 P-GO → **armed-not-run**。
- **last_updated**: 2026-07-28 · Track A Round-2 GO gate check（未執行）- **human_action_pack**: `docs/governance/h2_h5_wet_ink_human_action_pack_v1.md`
- **unlock_attempt_ticket**: `WAVE5-h2-h5-wet-ink-unlock-attempt-v1`
- **wave**: Wave-P7-5 · staging integration execute · Round-2
- **status_by_role**:
  - **Orchestrator (O)**: done — FRAME + 2026-07-28 閘門編排／催辦
  - **Implementer (B)**: blocked — 五頂未齊 · 無 GO · 未 flip 真 staging tier
  - **Reviewer (C)**: pending — 待 execute 證據
  - **Scribe (D)**: pending — Progress 本輪 append 催辦／arm 敘事
- **notes**:
  - Round-1 參照：run_id `20260623T165252Z` · local slot · simulated governance_dual
  - Round-2 **未分配 run_id** · **未執行** S1–S4 POST · **票已 armed ≠ execute 完成**
  - 48h 觀測：**未啟動**（須 S1–S4 全 GO 後）
  - **H1 approved ≠ Round-2 GO**（須另一次尚書省明示）

### 解阻最短路徑（human · 依序 · 缺任一步仍 blocked）

| 步 | 負責方 | 動作 | 解阻項 | 完成標記 |
|----|--------|------|--------|----------|
| 1 | 尚書省 / Wave-H | 核發 **`governance_dual`** 真批文留痕（≠ Round-1 `simulated_local_execute_2026-06-24`） | P-1 · G4 | 批文 ID / Progress 末尾引用 |
| 2 | Infra | Provision **真 staging deployment slot** + non-prod **HTTPS endpoint**（allowlist 內 host） | P-2 · G3 | endpoint URL + slot 名寫入 env matrix |
| 3 | Security | 外部 POST 風險審查 sign-off（allowlist · secret 管理 · 無 prod URL 混入） | P-3 · G6 | 書面 sign-off 留痕 |
| 4 | Infra / 客戶 | 客戶 **staging allowlist** 就緒（**禁止** prod endpoint） | P-4 | allowlist 檔 / config 已部署至 slot |
| 5 | Infra / Oncall | **Receiver** 部署至 staging slot（或客戶 receiver 就緒 · 可驗簽） | P-5 | staging slot 上 verify 探針 2xx |
| 6 | Implementer / Ops | 前置 1–5 齊備後 **分配新 `run_id`** · 依 runbook 跑 **S1–S4** · rollback · Progress append | execute-v2 AC-2 | B_REPORT phase 表全 GO + 新 run_id |

**最短路徑一句話**：先拿 **governance_dual 批文** → 配 **Infra staging endpoint** → 過 **Security** → 上 **allowlist** + **receiver** → 才能跑 Round-2 S1–S4。

---

## B_REPORT (Implementer / Ops)

- **status**: blocked — 前置未齊 · 未執行真 staging POST
- **executed_at**: *(pending)*
- **run_id**: *(pending — 前置齊備後依 repo 慣例 `YYYYMMDDTHHMMSSZ` UTC)*
- **run_url**: *(pending — non-prod 客戶 staging HTTPS endpoint · 禁止 prod)*
- **go_no_go**: *(pending)*
- **commands**: *(pending)*
  - 預期：`python tools/p7_staging_integration_execute_v1.py`（或 Infra 指定 runner · 須指向真 slot env）
- **phase_summary**: *(pending)*

| Phase | go | 關鍵 event_id | 摘要 |
|-------|-----|---------------|------|
| **S1** | — | — | 未執行 |
| **S2** | — | — | 未執行 |
| **S3** | — | — | 未執行 |
| **S4** | — | — | 未執行 |

- **48h_observation**:
  - **status**: `not_started`
  - **window**: *(pending — 須 S1–S4 全 GO 後起算)*
  - **metrics**: DLQ 行數 · 失敗 POST 計數 · retry_exhausted 事件 · adapter `blocked_rule` 分布
  - **gap**: 本輪時間不足以完成 48h；下一步 = Round-2 execute 全 GO 後由 Oncall 開窗口並每日 inspect `stats --tier staging`

- **rollback**: *(pending)*

---

## C_REPORT (Reviewer)

- **review_date**: *(pending)*
- **verdict**: `not_yet_reviewed`
- **core**: Round-2 票 FRAME 就緒；前置 blocked · 無 staging POST 證據。
- **gaps**: 真 governance_dual · Infra slot · Security sign-off · 客戶 endpoint · 48h 觀測

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-06-24
- **depends_on**:
  - `WH-P7-NOTIF-staging-integration-execute-v1` — Round-1 **`validated`** · run_id `20260623T165252Z`
  - `WH-P7-PROD-staging-smoke-runbook-v1` — runbook SSOT
  - `WH-P7-PROD-staging-env-bootstrap-v1` — local slot only · **須 Infra Round-2 provision**

### 必備前置批文／條件（execute 前 must）

| # | 條件 | 現況 | 阻塞 | 負責方 |
|---|------|------|------|--------|
| P-1 | Wave-H **`governance_dual`** 真批文留痕 | ✅ `GOV-DUAL-APPROVAL-2026-07-13-01` · **`approved`**（2026-07-28 具名） | **否** | 尚書省 / Wave-H |
| P-2 | Infra staging slot / HTTPS endpoint 已配置 | ❌ 規格表 §2 空白 · 僅 Round-1 local slot | **是** | Infra |
| P-3 | Security 外部 POST 風險審查通過 | ❌ 動作包 §3 待簽 | **是** | Security |
| P-4 | 客戶 staging endpoint allowlist 就緒（non-prod） | ❌ 動作包 §4 待填 | **是** | Infra / 客戶 |
| P-5 | Receiver 依賴 OK（staging 可驗簽） | ⚠️ 參考 impl 可用 · **未**部署至真 staging slot | **是** | Infra / Oncall |
| P-GO | 尚書省 **明示 Round-2 GO** | ❌ 本輪**無** GO（H1 approved **不解**本項） | **是** | 尚書省 |

**裁決**：P-1 已解 · **P-2–P-5 + P-GO 未齊** → **`overall_status=blocked`** · 閘門已 armed · **不做**真 staging S1–S4 execute · **不**開 48h 觀測。

### Append · 2026-07-28 · Round-2 arm（stage-round2-go · 未執行）

| 項 | 狀態 |
|----|------|
| S1–S4 | **未跑** |
| `run_id` | **未分配** |
| 48h 觀測 | **not_started** |
| 解阻條件 | H1–H5 全齊 **且** 尚書省明示 GO |
| AI 本輪 | 僅編排／催辦／Progress · **禁止** POST |

### unlocks（前置齊備 + execute GO 後）

- P7 staging 子線可誠實升級敘事：**local slot + 真 endpoint Round-2 GO**
- `WH-P7-PROD-prod-rollout-governance-bootstrap-v1` G3 / G5 可升 `done` 或 `partial`
- Wave-P7-6 prod rollout 仍 **blocked**（≠ prod flip）

**Progress**：見 `00_Agent_Work_Progress.md` 2026-06-24 Round-2 條目 + 2026-07-28 Wave5 Human Unlock 條。

### Append · 2026-07-28 · Track A Round-2 GO 閘門（track-a-round2 · **未執行**）

> 前置條件未滿足 → **STOP** · 不分配 `run_id` · 不跑 S1–S4 · 不開 48h。

| 閘門 | 現況 | 通過？ |
|------|------|--------|
| H1–H5 全齊 | H1=`approved` · H2–H5=`blocked`（規格表 §7／動作包 §3–§5） | **否** |
| 尚書省明示 Round-2 GO（P-GO） | 本對話／批文 **無** GO 字樣 | **否** |
| S1–S4 | **未跑** | — |
| `run_id` | **未分配** | — |
| 48h 觀測 | **not_started** | — |

**裁決**：五頂未齊 **且** 無 P-GO → `overall_status` 維持 **`blocked`** · 票維持 **armed-not-run**。  
**下一步**：Infra／Security／產品填齊 H2–H5 → 尚書省**另**明示 GO → 新對話 boot `--text` 含 Round-2／execute-v2 後再跑 S1–S4＋48h。  
**non_claims**：≠ Round-2 GO · ≠ staging POST · ≠ 48h 開窗 · ≠ Phase% uplift · ≠ DarkOps。

### Append · 2026-07-28 · Unlock 支 · P-GO + S1–S4 跑卡（human-round2-go-exec · **未執行**）

> plan todo `human-round2-go-exec` · 裁決一頁 Unlock 鏈末端  
> **閘門未滿足 → STOP** · 不分配 `run_id` · 不跑 S1–S4 · 不開 48h

| 閘門 | 現況 | 通過？ |
|------|------|--------|
| Unlock／五頂路徑 | H1=approved · H2–H5=blocked | **否** |
| P-1–P-5 | 僅 P-1 ✅ | **否** |
| 尚書省明示 Round-2 **P-GO** | **無** | **否** |
| S1–S4 | **未跑** | — |
| 48h 觀測 | **not_started** | — |

#### GO 後跑卡（僅五頂齊 + P-GO 明文後）

| 步 | 動作 | 驗收 |
|----|------|------|
| G0 | Progress／本票記錄 P-GO 引用（對話／批文 ID） | 可審計一句 |
| S1–S4 | 依 `WH-P7-PROD-staging-smoke-runbook-v1` · 真 staging（非 localhost） | phase 表全 GO + 新 `run_id` |
| 48h | 開觀測窗 · DLQ／失敗 POST／retry | window 起訖入 B_REPORT |
| 收尾 | rollback 演練 · Progress 戰報 | AC-1–AC-5 |

**AI 本輪**：**禁止** POST／假 GO／用 Round-1 local slot 冒充 Round-2。  
**Defer 路徑**：見 `docs/governance/wave5_h2_defer_pivot_playbook_v1.md` · 正式 DEFER 時本票維持 armed-not-run + review_by。

### Append · 2026-07-28 · Defer 樞紐預留（defer-pivot-queue · 待裁決勾選／逾期）

| 項 | 預留值 |
|----|--------|
| defer_reason | *(pending — Unlock逾期｜尚書省DEFER)* |
| review_by | 建議 `2026-08-11` |
| overall_status | 維持 `blocked` · `armed-not-run` |
| tip 目標 | QUEUE tip#1 → `P6-nightly-continue`（勾 Defer 後依 playbook） |

### Append · 2026-07-28 · Plan Implement 閘門（shangshu-check-decision · branches STOP）

> Cursor plan Implement · **未**代勾 Unlock／Defer · **未**跑 S1–S4

| 分支 todo | 結果 |
|-----------|------|
| `branch-unlock-fill` | **STOP** · UNLOCK 未勾 · §2 仍空白 · **未**假 host · **未**代簽 H3–H5 · **無** P-GO |
| `branch-defer-apply` | **STOP** · DEFER 未勾 · 未逾期（截止 08-04）· **未**覆寫 tip#1＝P6 · defer_reason 仍 pending |
| `branch-p6-authorize` | **STOP** · P6 裁決包未簽 · **未** `_phase_pct_apply --authorize` |

**裁決**：`overall_status` 維持 **`blocked`** · **`armed-not-run`** · `decision_status=awaiting_explicit_unlock_or_defer`。  
**解阻**：尚書省於裁決一頁勾選或回覆 `UNLOCK`／`DEFER`（可加 `P6_SIGN`／`P6_HOLD`）後再開新對話施工。

### Append · DEFER pivot · 2026-07-28T03:55+08:00

> 口令 **`DEFER + P6_SIGN`** · 裁決一頁 §4 DEFER 已勾 · playbook §2 tip 已覆寫

| 項 | 值 |
|----|-----|
| overall_status | **`blocked`** · **`armed-not-run`**（維持） |
| defer_reason | 尚書省DEFER |
| review_by | `2026-08-11` |
| QUEUE tip#1 | → `P6-nightly-continue` |
| S1–S4／run_id／48h | **未跑**／**未分配**／**not_started** |

**禁止**：S1–S4 · 假 endpoint · 未授權 prod · 以 Round-1 local slot 冒充 Round-2。  
**non_claims**：≠ Round-2 GO · ≠ UNLOCK · ≠ H2–H5 解阻 · ≠ DarkOps。

### Append · 2026-07-28 · next-r2-review（複審閘預排）

> plan todo `next-r2-review` · **≠** 提前開議 · **≠** UNLOCK／GO

| 項 | 值 |
|----|-----|
| overall_status | **`blocked`** · **`armed-not-run`**（維持） |
| review_by | `2026-08-11`（維持） |
| 複審議程 | `docs/governance/wave5_round2_review_agenda_2026-08-11_v1.md` |
| 提前開議 | 須口令 `R2_REVIEW`（本輪未授） |
| 假 host | **仍禁** localhost／自簽冒充 |

**non_claims**：≠ Round-2 GO · ≠ execute S1–S4 · ≠ H2–H5 解阻 · ≠ DarkOps。
