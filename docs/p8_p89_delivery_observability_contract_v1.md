# P8 / P8.9 · Delivery Observability Contract (v1)

> **Ticket**: `W3-P89-OBS-delivery-trace-contract-v1` · **Wave 3** · **doc-only**  
> **Goal**：固定 **trace 欄位 · artifact 路徑 · success/failure signals**，使 Implementer / Reviewer 可不翻多份 STATE 也能追 gate → notify → consumer → backlog 主鏈。  
> **Related**：`docs/p8_p89_evidence_index_v1.md`（**evidence tier**）· `docs/P8_P89_ADVISORY_CI_INDEX.md`（advisory vs gate）· `docs/p75-intake-gate-control-plane-trace-v1.md`（上游 gate 專線）

---

## Non-claims

| 聲明 | 狀態 |
|------|------|
| 本 contract = prod SLO / alert / Grafana | **否** |
| 本 contract = 新增 metrics 欄位或改 producer/consumer | **否** — 僅索引既有 JSON 鍵 |
| MP-SMOKE / P8.9 bundle 綠 = prod-ready / required CI | **否** — tier 見 Evidence Index（**L-local**） |
| bridge `POST /api/orchestration/bridge` = mandatory MP-SMOKE 步驟 | **否** — **optional** cross-ref only |

---

## 1. Trace fields（SSOT · ≥6）

| Field | Source | Meaning | Inspect |
|-------|--------|---------|---------|
| `case_ref` | MP-SMOKE summary · P8.9 `p8.9_verification_run.json` · backlog CLI | 案件鍵（例 `demo_phase`） | 頂層 JSON `case_ref` |
| `run_id` | std-case `experiment_id`（step 3 artifact）· 或彙總時以 `run_at`+`case_ref` 相關聯 | 單次實驗／煙測相關鍵；**MP 摘要無獨立 `run_id` 鍵時以 `experiment_id` 或 `run_at` 代替** | `steps[std_case_experiment].artifact_paths.experiment_id` · summary `run_at` |
| `multi_phase_smoke.ok` | `multi_phase_smoke_run.json` · CLI 頂層 `ok` | 七步全綠 | 頂層 `ok` · `failed_steps` 應空 |
| `events_summary.count` | P8.9 bundle / MP step 6 `detail.events_summary` | 合併 workflow events 筆數 | `p8.9_verification_run.json` → `events_summary.count` |
| `acks_summary.pending_count` | P8.9 bundle / `acks.json` | 待 ack 數 | `acks_summary.pending_count` · `acks.json` |
| `notifications_failed_ack_count` | `export_std_case_metrics_v1` | 失敗 ack 計數（CI-SMOKE pass 規則用） | `python scripts/export_std_case_metrics_v1.py --case-ref demo_phase --format json` |

**建議附加（非 AC 必填）**：`acks_summary.ack_count` · `steps[].step_id` · `gate_run` 的 `outbox_record_path` · backlog `count`。

**evidence_tier**：本鏈主證據為 **`L-local`**（見 Evidence Index）；勿寫成 GA-remote／required。

---

## 2. Artifact 地圖

### 2.1 MP-SMOKE steps 1–7

目錄：`outbox/verification/<case_slug>/`（`case_slug` = `case_ref` 正規化）

| # | `step_id` | 主要產物 / 觀測 | 失敗時看 |
|---|-----------|-----------------|----------|
| 1 | `gate_preview` | step `detail`（decision · reason_codes）；**無** outbox 寫入 | gate CLI preview |
| 2 | `gate_run_notify` | `artifact_paths.outbox_record_path` · optional `notification_path` | gate run + notify sink |
| 3 | `std_case_experiment` | `experiment_id` · `bundle_path` | experiment CLI / HITL auto path |
| 4 | `workflow_events_inspect` | `detail.count` · `streams_read` | events inspect CLI |
| 5 | `feedback_ingest_dry_run` | `detail.pending_count`（dry_run） | feedback ingest |
| 6 | `p89_verification_bundle` | P8.9 四檔（下表）+ `events_summary` / `acks_summary` | bundle 腳本 |
| 7 | `operator_backlog` | `detail.count` · `items[]` | backlog CLI / HTTP |

**彙總檔**：`multi_phase_smoke_run.json`（`schema_version` · `ok` · `case_ref` · `run_at` · `steps[]` · `enable_dispatch`）。

### 2.2 P8.9 verification bundle 四檔

| File | Purpose |
|------|---------|
| `p8.9_verification_run.json` | Bundle 摘要（`ok` · `events_summary` · `acks_summary` · `artifact_paths`） |
| `events.json` | 合併 notification + checkpoint timeline |
| `audit_quickview.json` | 調查視圖（含 `workflow_notifications`） |
| `acks.json` | pending + recorded downstream acks |

正文：`docs/p8_9-verification-bundle-v1.md`。

### 2.3 Operator backlog / metrics（旁路）

| Artifact / CLI | Keys |
|----------------|------|
| `python scripts/list_operator_backlog_v1.py --case-ref demo_phase --format json` | `ok` · `count` · `items[]` |
| `GET /operator/backlog`（P8-API） | 同上 JSON 形狀 |
| `python scripts/export_std_case_metrics_v1.py --case-ref demo_phase --format json` | `notifications_failed_ack_count` 等 |

---

## 3. Success / failure signals ↔ CLI

| Signal | Expected (demo_phase 基線) | Inspect command |
|--------|---------------------------|-----------------|
| `S_MP_OK` | `multi_phase_smoke.ok == true` · 七步皆 `ok` | `python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json` |
| `S_P89_OK` | bundle `ok` · 四檔存在 · `events_summary.count > 0` | `python scripts/run_p8_9_verification_bundle_v1.py --case-ref demo_phase --format json` |
| `S_ACK_CLEAN` | `notifications_failed_ack_count == 0`（CI-SMOKE 規則） | `python scripts/export_std_case_metrics_v1.py --case-ref demo_phase --format json` |
| `F_MP_STEP` | 某 `steps[].ok == false` | 同 MP CLI · 看 `steps[].step_id` / `message` |
| `F_EVENTS_EMPTY` | `events_summary.count == 0`（異常於 demo_phase） | 讀 `p8.9_verification_run.json` 或重跑 bundle |
| `F_PENDING_ACK` | `acks_summary.pending_count` 異常升高 / failed_ack > 0 | metrics + `acks.json` |
| `F_BACKLOG` | backlog `ok=false` 或無法列出 | `python scripts/list_operator_backlog_v1.py --case-ref demo_phase --format json` |

**Optional**：`python scripts/run_ci_smoke_check_v1.py --format text`（串 MP + metrics · **local-only** · ≠ GitHub required）。

---

## 4. Cross-references

| Doc / Index | 關係 |
|-------------|------|
| Evidence Index | **何時**可說 validated / GA / advisory |
| 本 contract | **哪個鍵／哪條 CLI** 追主鏈 |
| P7.5 TRACE | 上游 gate 專線（steps 1–2 細節） |
| W5-T3 observer | 可消費本契約路徑做 skeleton 觀測 · ≠ prod metrics |

---

## 5. Operator fields projection（Wave 2 · P89-W2 · append）

> **敘事**：P8.9-T4 HTTP webhook sandbox ≡ **WD-P7-T2**（`notification_webhook_adapter_v1` · registry `webhook_dispatch_v1`）· **已落地 · 勿重造**。

Wave 4 UI 必讀欄位草案（計劃 §2.2）可由只讀投影讀出：

| Field | Inspect |
|-------|---------|
| `event_id` · `ack_status` · `handler_id` · `dispatch_registry_hit` · `dlq_flag` | `python scripts/inspect_p89_operator_fields_v1.py --case-ref demo_phase --format json` |
| 契約正文 | `docs/p89-operator-fields-projection-v1.md` |

**non_claims**：投影 ≠ UI · ≠ prod webhook SLA · ≠ Phase% authorize。

---

## Changelog

| 日期 | 變更 |
|------|------|
| 2026-07-13 | §5 append · T4=WD-P7-T2 敘事 + operator fields 投影索引（`P89-W2-narrative-t4-obs-projection-v1`） |
| 2026-07-10 | v1 · `W3-P89-OBS-delivery-trace-contract-v1` · ≥6 trace_fields · MP 1–7 + P8.9 四檔 · failure↔CLI |
