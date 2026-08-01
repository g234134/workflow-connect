# 全線到 100% — Wave 執行計劃（2026-07-13）

> **角色**：執行 Orchestrator（same_chat）  
> **策略（用戶已確認）**：後端／契約先鎖到 ~90% → UI 一次做完 → 最後統一驗證  
> **Phase% SSOT**：`docs/WAVE_PROGRESS_DASHBOARD.md`（僅 W-PROG + `_phase_pct_apply` 可寫數字格）  
> **匯總票**：`04_Workflows/tickets/W-PROG-full-line-to-100-wave-plan-2026-07-13_state.md`  
> **首票**：`04_Workflows/tickets/P75-G6-alert-sink-contract-v1_state.md`

---

## 0. 核心原則與誠實邊界

| 原則 | 說明 |
|------|------|
| 契約／資料面優先 | Wave 0–1 鎖 DoD 與 schema；不開 Web UI |
| 後端衝 ~90% | Wave 2 無 UI；UI 欄位契約已在 Wave 0 凍結 |
| UI 一次做完 | Wave 4 集中交付（含 P7.5 operator 面） |
| 統一驗證 | Wave 6 才做全線回歸 + 誠實 Phase% apply |
| 禁區 | 憲法 §7；DarkOps blocked 勿改暗部根；無硬編絕對路徑／金鑰 |

**non_claims（計劃級）**

- ≠ 本計劃寫入即 Phase closure  
- ≠ 立刻把 Dashboard 抬到 100  
- ≠ prod alert／PagerDuty／真客戶 staging（除非另授權）  
- ≠ P7 Round-2 GO（仍 human／批文）  
- ≠ 本輪開 UI

---

## 1. Wave 順序總表

| Wave | 名稱 | 目標 | UI？ | 今日優先 |
|------|------|------|------|----------|
| **0** | 定義凍結 | 各關鍵 Phase 90%/100% DoD + UI 必讀欄位草案 | 否（僅契約草案） | **是** |
| **1** | 契約／資料面 | P7.5 alert sink · P8.9 · P5 metrics 等 schema／本地 sink | 否 | **是（P75-G6）** |
| **2** | 後端衝 ~90% | 無 Web UI；runtime／CLI／API／mock | 否 | 否 |
| **3** | 整合煙霧 | CLI／API／mock E2E | 否 | 否 |
| **4** | UI 大波 | Operator／P75／backlog 等一次做完 | **是** | 否 |
| **5** | 真環境／Human | P7 Round-2、staging、批文 | 最小 | 否 |
| **6** | 統一驗證 + W-PROG | 回歸 + `_phase_pct_apply` | 否 | 否 |

---

## 2. Wave 0 — 90% / 100% DoD 凍結表

> 數字為**誠實目標定義**；當前 Dashboard % 見 SSOT，不在本檔改寫。

### 2.1 P7.5 Intake Gate（當前 ≈46%）

| 門檻 | DoD（可驗收） | 證據類型 |
|------|---------------|----------|
| **→90%** | gate+policy+notify+REG 已有；**真本地 alert sink**（file／stub HTTP）可跑；SLO probe→sink 串接；metrics 對照骨架；**無** Web UI | L-local unittest + CLI |
| **→100%** | Operator UI 讀 sink／SLO；prod／staging alert 配線（另授權）；Phase closure 敘事 | L-human + W-PROG |

**UI 必讀欄位草案（Wave 4 · placeholder）**

| 欄位 | 來源 | 狀態 |
|------|------|------|
| `gate.decision` | intake_gate_result_v1 | frozen |
| `slo.latency_ms_p95` / `slo.error_rate` | probe dict | frozen |
| `alerts[]` | probe／sink | frozen |
| `sink.last_delivered_at` / `sink.mode` | alert sink | **Wave 1 契約** |
| `operator_actions[]` | UI only | **placeholder · Wave 4** |

### 2.2 P8.9 Outbox / Feedback（Dashboard ≈40% · 敘事：T1–T4 本地鏈已齊）

| 門檻 | DoD |
|------|-----|
| **→90%** | T1–T3 + metrics；**HTTP webhook sandbox（T4=WD-P7-T2）已落地**；observability／operator fields 投影對齊 |
| **→100%** | staging／prod webhook allowlist + SLA 敘事；UI 消費 feedback |

**T4 對齊**：P8.9-T4 ≡ **WD-P7-T2**／`notification_webhook_adapter_v1`／registry `webhook_dispatch_v1` · **勿重造**。

**UI 必讀欄位草案（placeholder → Wave 2 只讀投影）**：`event_id` · `ack_status` · `handler_id` · `dispatch_registry_hit` · `dlq_flag`（`docs/p89-operator-fields-projection-v1.md`）

### 2.3 P5 Dashboard / 離線健康度（當前 ≈70%）

| 門檻 | DoD |
|------|-----|
| **→90%** | toolchain health + `/metrics`；本地 Grafana/JSON 對照 stub（非 PG soak 宣稱） |
| **→100%** | PG soak／真 Grafana 面板 + UI |

**UI 必讀欄位草案（placeholder）**：`health.ok` · `metrics.scrape_ok` · `alert_budget_summary`（對齊暗部 `alert_event_v1` **敘事**，本計劃不改暗部）

### 2.4 P8 商業化交付（當前 ≈100% Dashboard）

| 門檻 | DoD |
|------|-----|
| **誠實 90% runtime** | 已基本滿足（Worker API + webhook gates）；運維 env 自備 |
| **誠實 100%** | Operator Web UI + SLA／exactly-once 敘事（部分屬 P9） |

**UI 必讀欄位草案（placeholder）**：`backlog.status` · `checkpoint_preview` · `notify.delivery_state` · `worker.job_id`

### 2.5 P7 自動客戶溝通（當前 ≈30%）

| 門檻 | DoD |
|------|-----|
| **→90%** | Round-1 已有；Round-2 五頂前置解阻 + staging slot（**human**） |
| **→100%** | prod adapter GO + required CI |

**UI 必讀欄位草案（placeholder）**：`run_id` · `slot_status` · `governance_dual` · `notify_receipt`

### 2.6 P9 訂單／金流（當前 ≈24%）

| 門檻 | DoD |
|------|-----|
| **→90%** | sandbox + advisory CI 穩定；ledger 本地閉環 |
| **→100%** | 真 provider + prod ledger（另授權） |

**UI 必讀欄位草案（placeholder）**：`order_id` · `payment_status` · `ledger_ref` · `sandbox_flag`

---

## 3. Wave 1 — 契約／資料面優先隊列

| 序 | 票建議 | Phase | 內容 | UI |
|----|--------|-------|------|-----|
| **1** | **P75-G6-alert-sink-contract-v1** | P7.5 | 真本地 alert sink 契約 + schema + file／stub HTTP + unittest | **否** |
| 2 | P89-T4-webhook-sandbox 或等價 | P8.9 | HTTP webhook sandbox（若未落地） | 否 |
| 3 | P5-metrics-grafana-stub 或等價 | P5 | metrics 對照／Grafana stub 契約 | 否 |
| 4 | 其餘契約補洞 | 多 | 以 Dashboard「未做」列為準 | 否 |

**延伸既有**：P75-G5 probe（`would_emit` only）→ G6 **實際寫入本地 sink**；不重造 probe 閾值邏輯。

---

## 4. Wave 2–6（摘要）

| Wave | 重點 |
|------|------|
| 2 | 後端 runtime 衝各 Phase ~90%；無 Web UI |
| 3 | MP-SMOKE／multi-case／CLI mock E2E 加嚴 · **2026-07-13 煙霧串線 GO**（`W3-SMOKE`；UI 仍 Wave 4） |
| 4 | **UI 大波**：P75／P8 backlog／必要 operator 面一次做完（**視覺已凍結 2026-07-27** · 首票 Wave4-A） |
| 5 | Human／staging／Round-2／批文 |
| 6 | 統一驗證；W-PROG `estimate→verify→apply --authorize`；誠實寫 Dashboard |

### 4.1 Wave 2 — 後端衝 ~90% 優先隊列（無 UI）

| 序 | 票 | Phase | 內容 | 狀態 |
|----|----|-------|------|------|
| **1** | **P75-G7-intake-gate-http-stub-v1** | P7.5 | loopback `POST /api/intake/gate`（80% Non-Goal → 90% 後端） | **done · 2026-07-13** |
| 2 | P89-W2-narrative-t4-obs-projection-v1 | P8.9 | 敘事 T4=WD-P7-T2 + operator fields 只讀投影 | **done · 2026-07-13** |
| 3 | P2 index ingest 配線 | P2 | FP-G2-T6 `--execute` **仍 blocked** → 另票解阻或改做他項 | **blocked（記 Progress）** |
| 4 | **P868-W2-runtime-inspect-catalog-selector-executor-v1** | P8.6–8.8 | catalog→selector plan_only→executor dry_run inspect | **done · 2026-07-13** |

---

## 5. 今日開工清單

1. [x] 本計劃登錄  
2. [x] Progress／票 state／INDEX 最小索引  
3. [x] Wave 0 DoD 表（本檔 §2）  
4. [x] Wave 1 首票 P75-G6 實作與驗證（2026-07-13 · accepted）  
5. [x] Wave 1 #2：P8.9-T4 webhook sandbox — **已確認先前落地**（WD-P7-T2／`notification_webhook_adapter_v1` · 本輪不重造）  
6. [x] Wave 1 #3：P5-metrics-grafana-stub-v1（2026-07-13 · accepted · estimate P5 +2 · 未 apply Dashboard）  
7. [x] Wave 2 #1：P75-G7-intake-gate-http-stub-v1（2026-07-13 · accepted · estimate P7.5 +2 · 未 apply Dashboard）  
8. [x] Wave 2 #2：P89-W2-narrative-t4-obs-projection-v1（2026-07-13 · T4=WD-P7-T2 敘事 + operator fields 投影 · estimate P8.9 +1 · 未 apply）  
9. [x] Wave 3 煙霧前置：W3-SMOKE-g7-gate-notify-mp-chain-v1（2026-07-13 · 串線綠 · estimate P7.5 +1 · 未 apply · **Wave3 煙霧 GO** · UI 仍 Wave 4）
10. [x] Wave 2 #4：P868-W2-runtime-inspect-catalog-selector-executor-v1（2026-07-13 · catalog／selector／executor dry_run inspect · estimate P8.6/8.7/8.8 各 +1 · 未 apply）
11. [x] Wave 5：WAVE5-human-staging-checklist-v1（2026-07-13 · H1–H5 文件清單 · ≠ 已解阻 · P7 +0）
12. [x] Wave 4 UI 視覺凍結＋開 Wave4-A（2026-07-27 · `W4-UI-FREEZE` done · `W4-UI-A` frame_ready · ≠ UI 已交付）

---

## 6. Phase% 政策（本計劃期間）

- 普通票：`apply_phase_pct=false`；只填 `proposed_delta`  
- 契約微票：建議 **+0～+1**；**禁止**擅自大漲  
- 僅匯總 W-PROG 且 verified 後才 `apply --authorize`

---

## Append · 2026-07-13 · Wave 1 續做（P5 stub）

- **裁決**：P8.9-T4 HTTP webhook sandbox 已由 WD-P7-T2 落地（12 tests · registry 雙 sink）→ **不重造**。
- **本輪交付**：`P5-metrics-grafana-stub-v1` — 本地 Grafana/JSON 對照 stub（health.ok · metrics.scrape_ok · alert_budget_summary）。
- **驗證**：`python -m unittest tests.test_p5_metrics_grafana_stub_v1 -v` → 5 OK；CLI `ok=true`。
- **Phase%**：estimate P5 +2 · `apply_phase_pct=false` · **未**寫 Dashboard。
- **下一步**：Wave 1 剩餘契約補洞，或進入 Wave 2（後端衝 ~90% · 無 UI）。

---

## Append · 2026-07-13 · Wave 2 #1（P75-G7 HTTP stub）

- **本輪交付**：`P75-G7-intake-gate-http-stub-v1` — loopback `POST /api/intake/gate` + `--once`／`--serve`（預設 preview）。
- **驗證**：`python -m unittest tests.test_intake_gate_http_stub_v1 -v` → 8 OK；CLI `ok=true`。
- **Phase%**：estimate P7.5 +2 · `apply_phase_pct=false` · **未**寫 Dashboard。
- **阻塞**：P2 index hook `--execute` 仍 blocked（見 Progress）；本輪未開 P2 實作票。
- **下一步**：Wave 2 #2 P8.9 敘事／小補洞，或 P8.6–8.8 薄增量；Wave 3 煙霧條件＝G7 + 既有 gate／notify／MP-SMOKE 串線穩定（仍無 UI）。

---

## Append · 2026-07-13 · Wave 2 #2（P8.9 敘事 + operator fields）

- **裁決**：T4 webhook **不重造**（= WD-P7-T2）；本輪做 Dashboard／計劃／INDEX／obs 敘事對齊 + 只讀 UI 五鍵投影。
- **本輪交付**：`P89-W2-narrative-t4-obs-projection-v1` — `delivery/p89_operator_fields_v1.py` · inspect CLI · 4 tests；Dashboard 敘事改「T4 landed」· **未改** 40% 數字格。
- **驗證**：`python -m unittest tests.test_p89_operator_fields_v1 -v` → 4 OK；CLI `ok=true`。
- **Phase%**：estimate P8.9 +1 · `apply_phase_pct=false` · **未**寫 Dashboard。
- **下一步**：Wave 2 #3（P2 仍 blocked → 跳過或僅敘事）或 P8.6–8.8 薄增量；Wave 3 煙霧仍待 G7 + gate／notify／MP-SMOKE 串線穩定（無 UI）。

---

## Append · 2026-07-13 · Wave 3 煙霧前置（W3-SMOKE）

- **本輪交付**：`W3-SMOKE-g7-gate-notify-mp-chain-v1` — G7 preview → layer 對齊 → G7 run+notify → G6 file sink → MP-SMOKE 七步。
- **驗證**：`python -m unittest tests.test_wave3_smoke_chain_v1 -v` → 2 OK；CLI `ok=true` · `failed_steps=[]`。
- **Phase%**：estimate P7.5 +1 · `apply_phase_pct=false` · **未**寫 Dashboard。
- **Wave 3 GO**：煙霧串線 **GO**（L-local）；**Wave 4 UI 仍等**用戶照片／欄位凍結（不因煙霧綠自動開工）。
- **阻塞沿用**：P2 `--execute` blocked；Dashboard % 未 authorize。
- **下一步**：可選 P8.6–8.8 薄增量；或等用戶凍結後開 Wave 4 UI；統一 % 留 Wave 6／W-PROG。

---

## Append · 2026-07-13 · Wave 2 #4（P868 runtime inspect）

- **本輪交付**：`P868-W2-runtime-inspect-catalog-selector-executor-v1` — catalog 碰撞檢查 → selector `plan_only` → executor `dry_run` + WB-T2 allowlist 摘要。
- **驗證**：`python -m unittest tests.test_p868_runtime_inspect_v1 -v` → 3 OK；CLI `ok=true` · `collision_tool_ids=[]`。
- **Phase%**：estimate P8.6 +1 · P8.7 +1 · P8.8 +1 · `apply_phase_pct=false` · **未**寫 Dashboard。
- **non_claims**：≠ prod browser · ≠ Wave4 UI · ≠ Phase closure · ≠ DarkOps · ≠ execute subprocess。
- **下一步**：等用戶開 Wave 4 UI；或 Wave 5 human／staging 清單（文件 only）；W6-T10 cleanup／% apply 另票。

---

## Append · 2026-07-13 · Wave 5 · Human／staging 清單（文件 only）

- **本輪交付**：`WAVE5-human-staging-checklist-v1` — H1–H5＝P7 Round-2 五前置（owner／前置／驗收／blocked／下一票）+ A1–A4（P8.5 browser／P9 prod／Wave4 HOLD／WC-PRE）。
- **產物**：`04_Workflows/plans/wave5-human-staging-checklist-2026-07-13.md` · `.yaml` · `tests/test_wave5_human_staging_checklist_v1.py`。
- **驗證**：`python -m unittest tests.test_wave5_human_staging_checklist_v1 -v`。
- **Phase%**：proposed P7 +0 · `apply_phase_pct=false` · **未**寫 Dashboard。
- **non_claims**：≠ 已解阻 · ≠ Round-2 GO · ≠ prod GO · ≠ 改環境密鑰 · ≠ Wave4 UI · ≠ DarkOps。
- **下一步**：用戶貼 UI 照片開 Wave 4；**或** 解 H1（governance_dual 真批文）串 H2–H5 → 再談 execute-v2。


## Append · 2026-07-13 · W-PROG-wave013 Phase% + H1 批文

- **W-PROG**：W-PROG-wave013-pct-apply-2026-07-13 — Dashboard 寫入 P7.5 46→49 · P5 70→72 · P8.9 40→41 · P8.6/7/8 各 +1；WAVE5 P7 +0 跳過。
- **H1**：GOV-DUAL-APPROVAL-2026-07-13-01 · docs/governance/GOVERNANCE_DUAL_approval_template.md · pproved_pending_countersign（對話授權 + 模板齊；實體副署 pending）。
- **H2 準備**：W2-T2-infra-staging-slot-spec-request-v1 · docs/governance/infra_staging_slot_spec_request_v1.md（≠ H2 已解阻）。
- **non_claims**：≠ Round-2 GO · ≠ execute-v2 · ≠ H2–H5 全解 · ≠ 改密鑰 · ≠ DarkOps。
- **下一步**：Infra 填 H2 → H3–H5 → execute-v2；或 Wave4 UI 照片。

---

## Append · 2026-07-15 · 盤點＋P6 DAY5＋P4 dispatch replay min

- **盤點**：Dashboard `read` average ≈ **57.89** · 與 07-13／07-14 SSOT **無漂移** · **未** apply Phase%。
- **時間門**：P6 nightly DAY5 `29403223522` GREEN → **5/7**（≠ 83→91）。
- **Wave 0/1**：DoD 已凍結；Wave1 首批已 accepted；本輪增量 = `P4-DISPATCH-REPLAY-MIN-v1`（計劃 Wave A 下一刀）。
- **驗證**：`tests.test_p4_dispatch_replay_min_v1` 5 OK · CLI `ok=true` · `recommended_role=reviewer`。
- **人卡沿用**：H2–H5／濕墨 · WC-PRE · P9 prod · Round-2。
- **下一步**：Reviewer 收 Wave A；P6 DAY6–7；無批文可寫 `P2-INDEX-OBS-FOOTNOTE`／`P3-TRACE-LOCAL-HARDEN`；Wave B 等尚書省 sandbox 裁決。

---

## Append · 2026-07-27 · Wave 4 UI 視覺凍結＋開 Wave4-A

- **凍結裁決**：`unified_P1–P5.png` = 視覺 SSOT → **是**；頁優先序 **未改**（P1→P5→P4→P3→P2）。
- **產物**：`docs/wave4-ui-visual-freeze-v1.md` · 票 `W4-UI-FREEZE-unified-p1-p5-v1`（done）· 施工票 `W4-UI-A-static-shell-align-p1-v1`（frame_ready）。
- **宿主**：獨立靜態／輕量殼 · mock operator fields · 可後接 `app/local_ui` · ≠ 暗部 dashboard 大翻修 · ≠ Grafana。
- **Phase%**：`apply_phase_pct=false` · **未**寫 Dashboard。
- **non_claims**：≠ UI 已交付 · ≠ 金鑰明文 · ≠ DarkOps · ≠ prod。
- **下一步**：Implementer 開工 Wave4-A（靜態殼對齊 P1 + mock）。

## Append · 2026-07-27 · W4-UI-A accepted_with_gaps + Wave4-B P5 + A.1

- **收票**：`W4-UI-A` → `accepted_with_gaps`（8/8 unittest · STATE 已對齊）
- **本輪交付**：`W4-UI-B` P5 泳道靜態殼（`ui/command_center/p5.html`）+ A.1 視覺薄補
- **驗證**：`tests.test_w4_ui_b_p5_swimlane_v1` 8 OK · A 回歸 8 OK
- **開啟**：`python -m http.server 8765` → `/ui/command_center/p5.html`
- **Phase%**：`apply_phase_pct=false` · **未**寫 Dashboard
- **non_claims**：≠ Wave4-C–E · ≠ live API · ≠ Grafana · ≠ DarkOps · ≠ Phase% authorize
- **下一步**：Wave4-C（P4）另票

## Append · 2026-07-28 · W4-UI-C P4 accepted_with_gaps

- **收票**：`W4-UI-C` → `accepted_with_gaps`（8/8 + A/B 回歸合計 24/24）
- **本輪交付**：P4 三省指揮台靜態殼（`ui/command_center/p4.html`）· mock · runbook
- **導覽**：P1／P5／P4 可互點
- **apply_phase_pct**：false
- **non_claims**：≠ Wave4-D–E · ≠ live API · ≠ Grafana · ≠ DarkOps · ≠ Phase% authorize
- **下一步**：Wave4-D（P3）另票

## Append · 2026-07-28 · W4-UI-D P3 accepted_with_gaps

- **收票**：`W4-UI-D` → `accepted_with_gaps`（8/8 + A/B/C 回歸合計 32/32）
- **本輪交付**：P3 暗部執行閉環靜態殼（`ui/command_center/p3.html`）· mock · runbook
- **導覽**：P1／P5／P4／P3 可互點
- **apply_phase_pct**：false
- **non_claims**：≠ Wave4-E · ≠ live API · ≠ Grafana · ≠ DarkOps · ≠ Phase% authorize
- **下一步**：Wave4-E（P2）另票

## Append · 2026-07-28 · W4-UI-E P2 accepted_with_gaps · 五頁靜態殼收口

- **收票**：`W4-UI-E` → `accepted_with_gaps`（8/8 + A/B/C/D 回歸合計 **40/40**）
- **本輪交付**：P2 技能與資源靜態殼（`ui/command_center/p2.html`）· mock · settings stub · runbook
- **導覽**：P1／P2／P3／P4／P5 全部可互點；settings stub
- **freeze**：標 A–E 靜態殼完成（`docs/wave4-ui-visual-freeze-v1.md`）
- **apply_phase_pct**：false
- **non_claims**：≠ live API · ≠ Grafana · ≠ PG soak · ≠ DarkOps · ≠ Phase% authorize · ≠ Operator 全量 prod · ≠ 金鑰明文
- **下一步**：真 API 掛載另票（≠ 本輪已 Operator 全量 prod）
