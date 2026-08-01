# Outbox and Feedback Layer Contract v1

> **Ticket**: WB-T3 · outbox-and-feedback-layer-contract-v1  
> **Phase**: 8.9（Outbox · Feedback 層）  
> **Date**: 2026-06-11  
> **Status**: Contract SSOT — **doc + schema index only**; no new consumers or writers  
> **Machine index**: `docs/schemas/outbox_layer_v1.json`

---

## §1 Purpose and scope

This contract **unifies the schema index** for all repo-local outbox namespaces produced by the Tabular MVP tool layer (W3-TL-T3/T4), Agent experiment regression (W6-T8), Agent CI suite (W10-T1), Non-Tabular sandbox preview (W9-T4), sandbox delivery bundles (W12-T1), and derived agent metrics (W10-T2).

**In scope (v1)**

- Namespace table with `schema_id`, producer, consumer, retention guidance
- Feedback event semantics (HITL checkpoints, delivery approval, controlled notify)
- `join_with_case_history` contract aligned with `cases/index.json`
- Legacy / degradation rules when `schema_version` is absent
- Observability field conventions (`events.jsonl`, metrics sidecar, optional `trace_id`)
- Permanent track separation from Phase 8.8 `orchestration_bridge_outbox`

**Out of scope (v1)**

- New outbox consumer implementations (spec + schema index only)
- Replay pipeline / DLQ retry
- Changes to `tools/tabular_outbox_writer.py`, `tools/tabular_outbox_consumer.py`, or `tools/inspect_tabular_outbox.py` behavior
- Changes to per-run artifact filename rules under any namespace
- Local UI surfacing

**Upstream alignment (WB-T1 / WB-T2)**

Outbox writes from `execute_tabular_tool()` follow:

- **WB-T1** — `docs/tool-catalog-and-selector-contract-v1.md`：`tool_id` / Selector 推荐契约（`tools/tabular_tool_catalog_v1.json` 为 `tool_id` 权威）
- **WB-T2** — `docs/tool-executor-and-sandbox-safety-contract-v1.md` §2 四级 `execution_mode` 与 outbox 落盘矩阵

| `execution_mode` / condition | Tabular outbox write |
|------------------------------|----------------------|
| `dry_run` / `plan_only` | **No** per-run JSON; **no** `events.jsonl` |
| `execute`（非 dry-run） | **Yes** — including subprocess failure |
| `sandbox_end_to_end` | **Yes** tabular per-run + **`outbox/sandbox_delivery/`**（allowlist only） |
| Unknown / disabled `tool_id` | **No** write (`ok: false`) |
| `tool_id` | Must match catalog entry |
| `run_id` | `{UTC_compact}_{tool_slug}` |

Implementation detail remains in `docs/tabular-tool-outbox-spec.md` (implementation appendix).

**WA-T4 STATE write freeze (AC-9)**

Per `docs/phase4-multi-agent-collaboration-contract-v1.md` §5.1:

- **FRAME** and **STATE** blocks in ticket state files are **Orchestrator-only**.
- Outbox artifacts are **Implementer deliverables**; Scribe indexes them in Dashboard / WORKFLOW_INDEX / Progress — Scribe **must_not** write outbox JSON or mutate producer scripts.

---

## §2 Outbox namespace table

> **AC-1 / AC-2** — six top-level namespaces. Paths are repo-relative under `outbox/`.

| Namespace path | `schema_id` | Producer | Consumer (read-only) | Retention (suggested) |
|----------------|-------------|----------|----------------------|------------------------|
| `outbox/<case_ref>/` | `tabular_outbox_v1` (+ co-located feedback schemas, §4) | `tools/tabular_tool_executor.py` via `tools/tabular_outbox_writer.py` | `tools/tabular_outbox_consumer.py` · `tools/inspect_tabular_outbox.py` | 90 days per case_ref tree; gitignored in repo |
| `outbox/agent_experiment_regression/` | `agent_experiment_regression_v1` | `scripts/run_agent_standard_case_regression.py` · `scripts/run_agent_standard_case_experiment.py` | `scripts/run_agent_audit_quickview.py` · `scripts/analyze_agent_lines_metrics.py` | 90 days |
| `outbox/agent_ci/` | `agent_lines_ci_suite_v1` | `scripts/run_agent_lines_ci_suite.py` | `scripts/analyze_agent_lines_metrics.py` · CI reviewers | 180 days (CI audit) |
| `outbox/non_tabular_experiment/` | `non_tabular_experiment_preview_v1` | `scripts/run_non_tabular_experiment_preview.py` | `scripts/run_agent_audit_quickview.py` · `scripts/analyze_agent_lines_metrics.py` | 90 days (sandbox only) |
| `outbox/sandbox_delivery/` | `sandbox_delivery_bundle_v1` | `delivery/sandbox_delivery_bundle_v1.py` (W12-T1 orchestrator hook) | `scripts/run_agent_audit_quickview.py` · manual sandbox review | 90 days; **sandbox + allowlist only** |
| `outbox/agent_metrics/` | `agent_lines_metrics_v1` | `scripts/analyze_agent_lines_metrics.py` · `scripts/generate_agent_lines_monthly_report.py` | Offline dashboards · monthly report readers | 365 days (aggregates) |
| `outbox/<case_ref>/intake_gate_decision_*.json` | `intake_gate_result_v1` | `routing/intake_gate_layer_v1.py` (P75-G2) | Checkpoint A cross-ref · notify (`intake.gate_decision`, P75-G4) · audit | 90 days per case_ref |
| `outbox/intake_gate_events.jsonl` | `intake_gate_event_v1` (inline) | `routing/intake_gate_outbox_v1.py` | PM / audit index | 90 days |

### §2.1 Per-namespace notes

**`outbox/<case_ref>/` (tabular + feedback co-location)**

- Per-run tool audit: `outbox/<case_ref>/<run_id>.json` where `run_id = {timestamp}_{tool_slug}`.
- Optional append-only log: `outbox/events.jsonl` (tabular `event_type` enum, §7.1).
- HITL checkpoint JSON, `notify_experiment_*.json`, and delivery-approval sidecars also live under the same `case_ref` slug — see §4.
- `case_ref` equals the path under `cases/` (POSIX slashes), e.g. `demo_phase`, `sampleco/2026-0001`.

**`outbox/agent_experiment_regression/`**

- Filename: `<timestamp>_<case_ref_slug>.json` (slashes in `case_ref` → underscores in slug).
- Does **not** replace MVP mainline regression artifacts.

**`outbox/agent_ci/`**

- Filename: `<timestamp>_ci_summary.json`.
- Merged summary of tabular + non-tabular CI scopes; optional when `--no-ci-summary`.

**`outbox/non_tabular_experiment/`**

- Preview-only; **no** main-chain or tabular per-case outbox writes.
- Filename pattern matches regression line (`<timestamp>_<fixture_slug>.json`).

**`outbox/sandbox_delivery/`**

- Layout: `outbox/sandbox_delivery/<case_ref>/<YYYYMMDDTHHMMSSZ>_<experiment_id_prefix>/manifest.json`.
- **Maturity**: `sandbox: true`; allowlist = `additional_demo` only (see `delivery/sandbox_delivery_bundle_v1.py`).
- Must **not** be confused with production delivery under `cases/<ref>/reports/`.

**`outbox/agent_metrics/`**

- Primary outputs: `metrics_summary.json`, `metrics_summary.csv`, optional `monthly_report_YYYY-MM.md`.
- Metrics are **indirect aggregates** from other namespaces (WB-T4); this directory is not a tool-run audit trail.

### §2.2 Forbidden path merge (AC-10)

| Track | Path / module | Contract rule |
|-------|---------------|---------------|
| **Phase 8.9 tabular + agent lines** | `outbox/` namespaces in §2 | This contract |
| **Phase 8.8 orchestration bridge** | `orchestration_bridge_outbox` (dark `core/`) | **Permanent separate track** — no shared replay CLI, no merged schema index entry |

**FORBID**: importing `orchestration_bridge_outbox` from tabular consumer code; replaying tabular JSON through Phase 8.8 replay CLI; treating `outbox/events.jsonl` as orchestration DLQ.

---

## §3 Tabular list consumer output (`inspect_tabular_outbox`)

Minimum example (fixture tree):

```bash
python -m tools.inspect_tabular_outbox \
  --case-ref demo_phase \
  --json \
  --outbox-root tests/fixtures/outbox
```

> **CLI note**: The implemented flag is `--json` (not `--format json`). Behavior is frozen per WB-T3 Non-Goals.

### §3.1 List mode JSON shape

When listing runs (no `--run-id`, no `--join-history`), stdout JSON **must** conform to:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ok` | bool | yes | Always `true` on success |
| `case_ref` | string \| null | yes | Filter slug passed to CLI |
| `tool_id` | string \| null | yes | Filter or `null` |
| `count` | int | yes | Length of `runs` |
| `runs` | array | yes | Run summaries, **newest first** |

Each `runs[]` item (summary):

| Field | Type | Required |
|-------|------|----------|
| `case_ref` | string | yes |
| `run_id` | string | yes |
| `tool_id` | string | yes |
| `started_at` | string (ISO-8601 UTC) | yes |
| `finished_at` | string (ISO-8601 UTC) | yes |
| `ok` | bool | yes |
| `exit_code` | int \| null | yes |
| `message` | string | yes |
| `outbox_path` | string | yes |

Full per-run record schema: `schema_id = tabular_outbox_v1` — see `docs/tabular-tool-outbox-spec.md` §3.

### §3.2 Join-history mode

`--join-history --json` adds fields documented in `docs/tabular-outbox-consumer-spec.md` §2.3; contract alignment in §5.

---

## §4 Feedback sub-object semantics

Feedback events are **human-in-the-loop or simulated delivery signals** that may co-locate under `outbox/<case_ref>/` or appear as nested blocks inside agent-line artifacts.

### §4.1 Authority order

When summary views disagree with on-disk checkpoint files:

1. **Checkpoint JSON** under `outbox/<case_ref>/` (`schema_id = hitl_checkpoint_v1`) — **authoritative**
2. **Outbox summary** fields inside regression / CI artifacts — derived view only
3. **Orchestrator stdout** — observability only; not persisted contract

### §4.2 Event types

| `feedback_kind` | `schema_id` | Trigger | Storage | Key fields |
|-----------------|-------------|---------|---------|------------|
| `hitl_checkpoint_a` | `hitl_checkpoint_v1` | Intake decision `needs_review` or force flag | `outbox/<case_ref>/<checkpoint_id>_<ts>.json` | `checkpoint_id=A-intake-confirmation`, `status`, `agent_output`, `human_decision` |
| `hitl_checkpoint_b` | `hitl_checkpoint_v1` | Output guard / delivery gate | Same layout, `checkpoint_id=B-delivery-confirmation` | `agent_output.output_guard`, `human_decision.action` |
| `delivery_approval` | `hitl_checkpoint_v1` (via `delivery/delivery_approval_cli_v1.py`) | Operator `--confirm` on approval CLI | Updates checkpoint B + `resume_context` | `action` ∈ `approve_delivery` \| `request_changes` \| `hold` |
| `controlled_notify_simulated` | `controlled_notify_experiment_v1` | W7-T3 experiment after signoff exists | `outbox/<case_ref>/notify_experiment_<ts>.json` | `simulated: true`, `external_dispatch: false`, `client_summary` |
| `downstream_ack` | `downstream_ack_v1` | P8.9-T2 handler records ack after workflow notification emit | `outbox/feedback/<case_ref>/acks/<event_id>_<handler_id>.json` | `event_id`, `handler_id`, `status` ∈ `received` \| `failed`, `ledger_row_id`, `source_event_type` |

Append-only HITL audit: `outbox/checkpoint_events.jsonl` — one JSON object per checkpoint lifecycle event.

Workflow notification raw stream: `outbox/notification_events.jsonl` (W6-T10 gateway) — read by `delivery/workflow_event_consumer_v1.py`; downstream acks co-located under `outbox/feedback/<case_ref>/acks/`.

**Workflow notification `event_type` enum (gateway v1 + P75-G4)**

| `event_type` | When | Key payload fields |
|--------------|------|-------------------|
| `checkpoint.awaiting_human` | CP-A/B file written (orchestrator run) | `checkpoint_id`, `checkpoint_status`, `artifacts.checkpoint_path` |
| `checkpoint.approved` | CP auto/human approve | `approval_source`, `checkpoint_id` |
| `delivery.bundle_ready` | Sandbox bundle success | `artifacts.bundle_path` (when present) |
| `run.completed` | Run terminal success | `status_summary.final_status` |
| `run.blocked` | Run blocked / fail-close | `status_summary.final_status` |
| **`intake.gate_decision`** | Gate **run** + notifications enabled (CLI or future orchestrator hook) | `artifacts.intake_decision_id`, `artifacts.decision` (canonical), `artifacts.reason_codes[]`, `artifacts.policy_version`, `artifacts.outbox_record_path`; mirror in `status_summary` |

**`intake.gate_decision` emit rules (P75-G4)**

- Producer: `delivery/notification_gateway_v1.emit_intake_gate_decision_notification()` after durable gate record write.
- **Preview** gate mode: **no** notification (no outbox record).
- Notify failure: **fail-open** — gate result `ok` unchanged.
- Idempotency key includes `intake_decision_id` via envelope `checkpoint_id` slot.

**Downstream ack tracking (P8.9-T2)**

| `tracking_status` | Meaning |
|-------------------|---------|
| `recorded` | Checkpoint stream row or notification before ack merge |
| `pending_ack` | Notification emitted; no downstream ack file for `event_id` |
| `acked` | Ack file present with `status=received` |
| `failed` | Ack file present with `status=failed`; `last_error` = ack `message` |

**Downstream dispatch (P8.9-T3)**

Post-emit local handler registry (`delivery/notification_dispatch_v1.py` + `routing/notification_handlers_v1.yaml`). Invoked **after** gateway writes per-event JSON + `notification_events.jsonl`; **fail-open** (dispatch errors never change emit `ok`).

| Stage | Actor | Persistence |
|-------|-------|-------------|
| 1 emit | `notification_gateway_v1.send_notification` | `outbox/notifications/<case_ref>/` + jsonl |
| 2 dispatch (optional) | `dispatch_event` → registered handler | handler side-effects only (e.g. controlled notify outbox) |
| 3 ack | handler / dispatch wrapper → `record_downstream_ack` | `outbox/feedback/<case_ref>/acks/<event_id>_<handler_id>.json` |
| 4 read model | `workflow_event_consumer_v1.load_workflow_events` | merges ack → `tracking_status` |

Enable gates: `GOV_NOTIFICATION_DISPATCH_ENABLED=1` or `send_notification(..., dispatch_enabled=True)`; W7-T3 handler additionally requires `GOV_CONTROLLED_NOTIFY_ON_DISPATCH=1`.

```
emit → jsonl ──► dispatch (local handlers) ──► record_downstream_ack ──► consumer tracking_status
                      │ fail-open
                      └── does not rollback emit
```

Sandbox HTTP webhook sink（**WD-P7-T2**）已註冊於 v1 registry，但預設由 env gate 關閉；prod URL / HMAC / retrial policy 仍不在 v1 scope。

### §4.4 Webhook sandbox dispatch (WD-P7-T2 / P8.9-T4)

**Status**: Sandbox-only implementation v1 (WD-P7-T2). Fail-open HTTP POST sink.

**Environment gates** (all must be satisfied for actual POST):

| Variable | Purpose | Example |
|----------|---------|---------|
| `GOV_NOTIFICATION_WEBHOOK_ENABLED` | Master switch: `1`/`true`/`yes` to enable | `1` |
| `GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST` | Comma-separated glob patterns for allowed `case_ref` | `demo_*,test_*` |
| `GOV_NOTIFICATION_WEBHOOK_URL` | Target endpoint URL (sandbox-only hosts) | `http://localhost:8080/webhook` |
| `GOV_NOTIFICATION_WEBHOOK_TIMEOUT` | Request timeout in seconds (default: 10) | `30` |

**Sandbox safety**:
- v1 only allows `localhost` or `127.0.0.1` as host
- Non-localhost URLs are rejected (dry-run with logged warning)
- No retry / DLQ / HMAC signature in v1 — prod-tier policy 詳見 **§4.6 Notification governance (prod tier)**

**Fail-open guarantee**:
- Webhook HTTP failures (5xx, connection error, timeout) never change `dispatch_event` `ok` status
- Errors are recorded in `webhook_result.error` and downstream ack with `status=received`
- Main orchestrator flow continues regardless of webhook outcome

**Registry entry** (`routing/notification_handlers_v1.yaml`):
- Handler: `webhook_dispatch_v1`
- Event types: `delivery.bundle_ready`, `checkpoint.approved`, `run.completed`
- Gate: `enabled_when: webhook_dispatch` (requires `GOV_NOTIFICATION_WEBHOOK_ENABLED`)

**Testing with mock server**:

```python
# Example: Using MockWebhookServer in tests
from tests.test_notification_webhook_dispatch_v1 import MockWebhookServer

with MockWebhookServer() as mock:
    os.environ["GOV_NOTIFICATION_WEBHOOK_ENABLED"] = "1"
    os.environ["GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST"] = "demo_*"
    os.environ["GOV_NOTIFICATION_WEBHOOK_URL"] = mock.url
    
    # Your dispatch call here...
    
    requests = mock.get_requests()
    assert len(requests) == 1
    assert requests[0]["body_json"]["event_type"] == "delivery.bundle_ready"
```

**Dry-run indicators**:
When webhook does not actually POST (env off, allowlist miss, no URL, unsafe URL, or explicit `dry_run=True`), `webhook_result.dry_run=True` and `webhook_result.dispatched=False`.

**Test coverage**:
- Unit tests: `tests.test_notification_webhook_dispatch_v1`
- End-to-end orchestrator→dispatch→webhook smoke: `tests.test_orchestrator_dispatch_full_smoke_v1`

**CI**：advisory smoke（§4.5）**仍 sandbox-only · non-blocking**；CI job **must not** 使用 `staging` / `prod` tier env（§4.6.6）。

### §4.5 CI advisory smoke (Wave-G · WD-P7-T3 AC-7)

GitHub Actions workflow **`.github/workflows/p7-notification-smoke.yml`** runs a **non-blocking** advisory job named **`p7-notification-smoke`**.

| Property | Value |
|----------|-------|
| **Blocking** | **No** — job uses `continue-on-error: true`; not a branch protection required check |
| **Environment** | Sandbox-only: `GOV_NOTIFICATION_*` gates on; webhook URL fixed to `http://127.0.0.1:8080/webhook` with a localhost mock HTTP server |
| **Triggers** | `workflow_dispatch`, daily `schedule` (UTC 04:00), and path-filtered `pull_request` |
| **Test modules** | `tests.test_orchestrator_dispatch_full_smoke_v1`, `tests.test_orchestrator_notifications`, `tests.test_notification_webhook_dispatch_v1` |

Purpose: early warning on orchestrator → gateway emit → dispatch registry → webhook sandbox regressions without gating merge. Failures emit a `::warning` annotation and upload `p7_notification_smoke.log` as an artifact.

### §4.6 Notification governance (prod tier)

> **Status**: Policy SSOT — doc only (`WH-P7-NOTIF-PROD-policy-v1`)  
> **Scope**: 制度前提 — webhook dispatch 升格至 staging/prod 前的書面 policy  
> **Baseline**: §4.4 sandbox v1 行為不變；本章定義 *opt-in* prod 能力  
> **Runtime**: retry **partial**（sandbox localhost only；見 §4.6.0）；HMAC sender **partial**（sandbox-only env gate；receiver / prod mandatory 未實作）；DLQ 落盤 **partial**（env gated · default off）；URL tier / allowlist **partial**（adapter gate · staging/prod 尚不建議啟用）

#### §4.6.0 Policy summary table

彙總 §4.6 各節為可審計對照表。欄位：`policy_item` · `default` · `can_override` · `owner` · `impl_status`。

| policy_item | default | can_override | owner | impl_status |
|-------------|---------|--------------|-------|-------------|
| `emit_fail_open` | gateway notify 失敗不改 orchestrator `ok` | no | Wave-H Governance | **implemented**（§4.2） |
| `dispatch_fail_open` | dispatch / webhook 失敗不改 emit `ok` | no | Wave-H Governance | **implemented**（§4.2, §4.4） |
| `webhook_url_tier` | `sandbox_localhost_only` | staging/prod 須雙重 gate + 尚書省批文 | Infra + Wave-H | **partial**（sandbox localhost **implemented**；`TIER` + `URL_ALLOWLIST` adapter gate **partial**·僅 unittest；**prod 線 Non-goals** — staging/prod 實際啟用須 §4.6.6.4 checklist + 批文） |
| `webhook_hmac` | off | per-endpoint secret via env（禁止入庫） | Security + Wave-H | **partial**（sandbox-only **sender** side；env `GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED` + `HMAC_SECRET`；default off；**receiver verification / reference impl not_implemented_yet**；prod mandatory HMAC **not_implemented_yet**） |
| `webhook_retry_max_attempts` | `0`（單次 POST） | yes（env） | Wave-H | **partial**（**sandbox-only** localhost webhook；default off（`max_attempts=0`）；**prod 線 Non-goals** — staging/prod retry mandatory 未 enforce；可搭配 opt-in DLQ） |
| `webhook_dlq_enabled` | `false` | yes（env + tier gate，future） | Wave-H | **partial**（env `GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED` gated；default off；sandbox opt-in 落盤 `events.jsonl`；inspect CLI **not_implemented_yet**；prod mandatory DLQ 未 enforce） |
| `advisory_ci_blocking` | `false` | no | CI Governance | **implemented**（§4.5） |

> 完整 policy 列（backoff、DLQ retention、idempotency header 等）待 Reviewer 擴充；見票 `WH-P7-NOTIF-PROD-policy-v1`。

#### §4.6.1 Threat model & assumptions

本章界定 webhook 通道的主要威脅（偽造 payload、重放、SSRF、secret 洩漏、客戶 endpoint 誤配）與信任邊界：簽名與驗簽責任、repo 內禁止存放 secret。核心假設維持不變 — gateway emit 仍 fail-open；prod 可靠性靠 retry/DLQ 補償可觀測性，不靠阻斷 orchestrator 主流程。

#### §4.6.2 Delivery semantics

各層語意裁決如下：emit 層為 at-least-once 寫盘（jsonl + per-event JSON）；dispatch 為 sync best-effort；webhook HTTP 現況為 at-most-once（單次 POST）。啟用 retry 後 webhook 升格為 at-least-once，需 receiver 以 `event_id` / HTTP 冪等鍵合作。`effectively-once` 列為 future opt-in 目標，非 sandbox 預設。

#### §4.6.3 Retry & backoff policy

`webhook_retry_*` env 鍵：`GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS`（default `0`）、`GOV_NOTIFICATION_WEBHOOK_RETRY_BASE_DELAY_MS`（default `100`）、`GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_DELAY_MS`（default `2000`）。`max_attempts=0` 維持單次 POST（sandbox 預設）。`max_attempts≥1` 時可重試連線失敗 / timeout、408、429、5xx；其他 4xx 不重試；指數退避 clamp 至 `max_delay_ms`。**impl_status**：sandbox localhost adapter **partial**（**sandbox-only**；opt-in DLQ 見 §4.6.4；staging/prod retry mandatory **not_implemented_yet**）。retry 只提升 webhook 送達可觀測性，**不改** emit / dispatch fail-open 語意。

#### §4.6.4 DLQ / audit log

Webhook POST **最終失敗**（retry 用盡或不可重試 4xx 單次失敗）時，adapter **may** 將稽核列 append 至 notification DLQ 命名空間。DLQ 為 **事後 audit 層**：不改 emit / dispatch fail-open 語意；DLQ 寫入失敗 **must not** 阻斷 dispatch（與 §4.2 fail-open 對齊）。**不得**與 Phase 8.8 `orchestration_bridge_outbox` DLQ 混用（§2.2 永久分軌）。

**設計票**：`WH-P7-NOTIF-DLQ-v1` · **impl_status**：**partial**（`WH-P7-NOTIF-DLQ-impl-v1` 已實作 DLQ 寫入 `outbox/notification_dlq/events.jsonl`，受 `GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED` env gate 控制；default off；sandbox opt-in；inspect CLI 見 `WH-P7-NOTIF-DLQ-inspect-cli-v1`）。

**DLQ 寫入觸發（與 §4.6.3 retry 互補 · 不改現有 adapter 語意）**

| 條件 | 寫 DLQ | 說明 |
|------|--------|------|
| HTTP POST 成功（2xx） | 否 | 正常路徑 |
| `dry_run` / webhook disabled / URL gate 拒絕 | 否 | 未實際投遞 |
| 單次 POST 失敗且 `max_attempts=0`（default） | 是（DLQ enabled 時） | sandbox 預設不寫（`DLQ_ENABLED=0`）；opt-in 時落盤 |
| Retry 進行中、尚未用盡 | 否 | 僅最終失敗落 DLQ |
| `retry_exhausted=true` | 是 | 對齊 `webhook_result.retry_exhausted` |
| 不可重試 4xx（如 400）單次失敗 | 是 | 與 retry 用盡同等對待 |

**Env gate（對齊 §4.6.6 · impl partial）**

| Env 鍵 | Default | 說明 |
|--------|---------|------|
| `GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED` | `0` | `1` 時最終失敗事件落 DLQ（**partial** · 票 `WH-P7-NOTIF-DLQ-impl-v1`） |
| `GOV_NOTIFICATION_WEBHOOK_DLQ_PATH` | `outbox/notification_dlq/events.jsonl` | append-only jsonl 路徑（**partial** · 實際 env 鍵；非 `DLQ_ROOT`） |
| `GOV_NOTIFICATION_WEBHOOK_DLQ_TIER` | `sandbox` | DLQ record `tier` 欄位覆寫（**partial**） |

##### §4.6.4.1 DLQ file layout

| 項 | 定案 |
|----|------|
| 根目錄 | `outbox/notification_dlq/`（repo-relative；對齊 §2 outbox 命名空間模型） |
| 主 stream | **`outbox/notification_dlq/events.jsonl`** — append-only；**每行一筆** UTF-8 JSON object；行尾 `\n` |
| 可選 sidecar | `outbox/notification_dlq/<event_id>_<dlq_ts>.json` — 完整 snapshot（Implementer **may** 二選一或雙寫；jsonl **至少**存在） |
| `schema_id` | `notification_webhook_dlq_v1`（每筆 record 必含） |
| Git | **gitignored**（與其他 `outbox/` 樹一致） |

**格式約束**

- 檔案編碼：**UTF-8**。
- 每行 **must** 為單一 JSON object；禁止多行 JSON 或 trailing comma。
- 寫入模式：**append-only**；禁止 in-place 修改或刪除單行（operator 清理見 §4.6.4.3）。
- 與 `outbox/notification_events.jsonl`（gateway emit stream）**分軌**；DLQ 僅記錄 webhook 投遞失敗稽核。

##### §4.6.4.2 DLQ record schema

每筆 jsonl 物件 **must** 含下列欄位。Implementer **may** 增 optional 欄位但 **must not** 刪 required 欄或改變語意。

| field | type | required | description |
|-------|------|----------|-------------|
| `schema_id` | string | yes | 固定 `notification_webhook_dlq_v1` |
| `timestamp` | string (ISO-8601 UTC) | yes | 失敗發生時間（通常取自 `webhook_result.timestamp`） |
| `dlq_written_at` | string (ISO-8601 UTC) | yes | DLQ 落盤時間 |
| `tier` | string | yes | `sandbox` \| `staging` \| `prod`（sandbox impl 固定 `sandbox`） |
| `event_id` | string | yes | gateway event id；與 webhook payload 一致 |
| `event_type` | string | yes | 如 `delivery.bundle_ready` · `intake.gate_decision` |
| `case_ref` | string \| null | yes | dispatch context |
| `endpoint` | string | yes | 實際 POST URL 或 host/path；query 中 secret **must** redact |
| `http_status` | int \| null | yes | 最後一次嘗試 HTTP 狀態；連線失敗可為 `null` |
| `attempt_count` | int | yes | 總嘗試次數（含首次 POST） |
| `retry_exhausted` | bool | yes | 是否 retry 用盡 |
| `last_error` | string \| null | yes | 人類可讀錯誤摘要 |
| `request_headers` | object \| string | yes |  outbound header 摘要；**must not** 含 HMAC secret 或完整 Authorization |
| `payload_digest` | string \| null | no | 可選；canonical body 之 SHA-256 hex，用於對照 **不存整個 body** |
| `webhook_result` | object | yes | 完整 adapter `webhook_result` snapshot（SSOT 引用） |
| `source_notification_path` | string \| null | no | 可選：對應 `outbox/notification_events.jsonl` 或 per-event JSON 路徑 |

**`request_headers` 投影規則**

- **May** 保留：`Content-Type` · `X-Gov-Event-Id` · `X-Gov-Timestamp` · 自訂 header 名稱（值可截斷）。
- **Must redact or omit**：`Authorization` · `X-Gov-Signature-256` 完整值 · 任何 secret / API key · cookie。
- 若無法安全投影，**may** 設為 `"redacted"` 字串或 `{}`。

**避免敏感內容**

- **Must not** 寫入完整 webhook request body 或 `GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET`。
- **Must not** 寫入 env 原文或 `.env` 片段。
- 需要 body 對照時使用 **`payload_digest`**（SHA-256 over canonical JSON bytes）而非 raw payload。
- `webhook_result.response_body` 在 embed 時 **should** 截斷至 ≤512 字元或省略（Implementer 票定稿）。

**與 `webhook_result` 關聯**：DLQ 列 **must** embed 當次 adapter `webhook_result`；top-level 欄位（`timestamp` · `endpoint` · `http_status` 等）為 inspect CLI 投影便利，**must** 與 embed 內容一致。

##### §4.6.4.3 Retention & privacy

| 項 | 建議 |
|----|------|
| 保留期 | **90 天**（與 §2 多數 outbox namespace 一致）；operator 負責定期清理過期 `events.jsonl` 與 sidecar；本 repo **不**強制 cron |
| 備份 | **不得** 將 DLQ 檔案納入長期備份或非必要複製；若必須備份，**must** 限受控存取並排除 secret 欄 |
| 存取 | DLQ 含 endpoint URL 與錯誤摘要；視為 **內部維運資料**，非對外 API contract |
| 寫入失敗 | adapter **must** fail-open（log warning）；**must not** 因 DLQ 不可寫而改 `ok=false` |
| Secret 禁令 | **禁止** 將 HMAC secret · API token · 完整 signed payload 寫入 DLQ；僅 `payload_digest` 與 redacted headers |

##### §4.6.4.4 Inspect CLI (design only)

> **Scope**：本節為 **設計目標 only**；**無**可執行程式。實作分屬 `WH-P7-NOTIF-DLQ-impl-v1`（落盤）與 `WH-P7-NOTIF-DLQ-inspect-cli-v1`（CLI + unittest）。

**建議模組**：`delivery/inspect_notification_dlq_v1.py` 或 `scripts/inspect_notification_dlq_v1.py` — 對齊 `tools.inspect_tabular_outbox` 之 list + `--json` 模式。

**子命令**

| 模式 | 用途 |
|------|------|
| **list**（default） | 列出最近 N 條 DLQ event（newest first） |
| **stats** | 輸出簡單聚合（by endpoint · tier · http_status） |

**CLI 旗標（proposed_default）**

| 旗標 | 說明 |
|------|------|
| `--dlq-root PATH` | 預設 `outbox/notification_dlq` |
| `--json` | stdout 結構化 JSON |
| `--since ISO8601` / `--until ISO8601` | 時間範圍（基於 `dlq_written_at` 或 `timestamp`） |
| `--endpoint URL_SUBSTR` | `endpoint` 子字串過濾 |
| `--event-id ID` | 精確 `event_id` |
| `--tier sandbox\|staging\|prod` | `tier` 過濾 |
| `--code HTTP_STATUS` | 過濾 `http_status`（如 `500`） |
| `--limit N` | 列表上限 |

**list 模式 stdout JSON 形狀（草案）**

| 欄位 | 型別 | Required |
|------|------|----------|
| `ok` | bool | yes |
| `count` | int | yes |
| `entries` | array | yes |

`entries[]` 每項至少投影：`dlq_written_at` · `timestamp` · `event_id` · `event_type` · `endpoint` · `tier` · `attempt_count` · `last_error` · `http_status` · `retry_exhausted` · `payload_digest`（若有）。

**stats 模式 stdout JSON 形狀（草案）**

| 欄位 | 型別 | 說明 |
|------|------|------|
| `ok` | bool | |
| `total_count` | int | 符合 filter 的總筆數 |
| `by_endpoint` | object | `{ "<endpoint>": count }` |
| `by_tier` | object | `{ "sandbox": n, ... }` |
| `by_http_status` | object | `{ "500": n, "null": n }` |

**輸出格式**：預設 human-readable 表格；`--json` 時輸出上述結構化 dict（與 tabular inspect 一致）。

#### §4.6.5 Webhook HMAC & idempotency

建議 HMAC-SHA256 覆蓋 canonical payload；header 如 `X-Gov-Signature-256`、`X-Gov-Timestamp`；timestamp 有效窗口與 `event_id` 冪等鍵分 **sender contract**（本 repo · §4.6.5.1）與 **receiver contract**（客戶 webhook · §4.6.5.2）。emit 層 `event_id` 已存在（**partial**）；HTTP `Idempotency-Key` header **not_implemented_yet**。secret 僅 env，禁止入庫。

**impl_status（本章）**：sender HMAC **partial**（sandbox-only env gate · default off；env 鍵見 §4.6.6）；receiver **contract documented**（§4.6.5.2 · 票 `WH-P7-NOTIF-HMAC-receiver-contract-v1`）；receiver reference impl / contract test fixtures **`not_implemented_yet`**（見 §4.6.5.2 末 future 票索引）。

##### §4.6.5.1 Sender contract v1

**票**：`WH-P7-NOTIF-HMAC-impl-v1` · **模組**：`notification_webhook_adapter_v1`

當 `GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED=1` 且 `GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET` 非空時，adapter 對 outbound POST 附加：

| Header | 預設名稱 | 值格式 |
|--------|----------|--------|
| 簽名 | `X-Gov-Signature-256`（env `GOV_NOTIFICATION_WEBHOOK_HMAC_HEADER` 可覆寫） | `sha256=<hex>` |
| 時間戳 | `X-Gov-Timestamp`（env `GOV_NOTIFICATION_WEBHOOK_TIMESTAMP_HEADER`） | Unix epoch **seconds**（UTC） |
| 事件識別 | `X-Gov-Event-Id`（env `GOV_NOTIFICATION_WEBHOOK_EVENT_ID_HEADER`） | 字串；**must** 等於 JSON body `event_id` |

**Body canonicalization**：`Content-Type: application/json`；body = `json.dumps(payload, ensure_ascii=False)` 的 **UTF-8 bytes**（原樣，不重排 key、不 re-parse 後再 serialize）。**Signed string** = `{timestamp}.{event_id}.{raw_body_utf8}`（UTF-8 編碼後作 HMAC message）。

**Sandbox 預設**：HMAC off（無簽名行為不變）。Env gate 與 `impl_status` 見 §4.6.6（`HMAC_ENABLED` + `HMAC_SECRET` 均 **partial** · sender read-only）。簽名失敗（secret 缺失、格式錯誤等）→ **fail-open**，仍送 unsigned POST。Retry 時 **must** 沿用同一 `event_id` 與同一 canonical body；timestamp **may** 刷新（每次 POST 新 timestamp + 新 signature）。

##### §4.6.5.2 Receiver contract

**票**：`WH-P7-NOTIF-HMAC-receiver-contract-v1` · **適用對象**：客戶 webhook endpoint（staging/prod 整合方）

本節為 receiver 端 **normative SSOT**；不含 reference 程式。Header 名稱以 onboarding 文件為準；預設與 §4.6.5.1 sender v1 一致。

**Receiver 假設**

| 項目 | 約定 |
|------|------|
| HTTP method | `POST` |
| Body 型態 | JSON（`Content-Type: application/json`）；驗簽 **must** 讀取 **原樣 HTTP body bytes**，禁止 receiver 自行 `json.dumps` / re-serialize（key 順序變更會導致驗簽失敗） |
| Canonicalization | 與 sender 相同：signed message 覆蓋 `{timestamp}.{event_id}.{raw_body}`（`raw_body` = UTF-8 解碼前的 bytes 序列化為簽名字串時用 UTF-8 文本，與 sender `_build_hmac_signed_message` 一致） |
| Shared secret | Out-of-band 配置（env / secret manager）；**must not** 入庫或寫入 repo |
| 預期 headers | `X-Gov-Signature-256`（或 env 定義值）· `X-Gov-Timestamp` · `X-Gov-Event-Id` |

任一 required header **缺失**或格式無法解析（timestamp 非整數、signature 不含 `sha256=` 前綴等）→ receiver **may** 視為 **驗簽失敗**，無需進入 HMAC 比對。

**簽名驗證 pseudo-code**

```
FUNCTION verify_gov_webhook(request, shared_secret):
  body_bytes = READ_RAW_BODY(request)              // do NOT re-json.dumps
  timestamp  = HEADER(request, "X-Gov-Timestamp")
  event_id_h = HEADER(request, "X-Gov-Event-Id")
  sig_header = HEADER(request, "X-Gov-Signature-256")

  IF missing(timestamp) OR missing(sig_header) OR missing(event_id_h):
    RETURN REJECT(401, "missing_signature_headers")

  IF NOT parse_int(timestamp):
    RETURN REJECT(401, "invalid_timestamp_format")

  IF ABS(now_utc_seconds() - timestamp) > TIMESTAMP_WINDOW_SEC:
    RETURN REJECT(401, "timestamp_out_of_window")

  event_id_b = JSON_FIELD(body_bytes, "event_id")
  IF event_id_h != event_id_b:
    RETURN REJECT(400, "event_id_mismatch")

  message = CONCAT(timestamp, ".", event_id_b, ".", UTF8_DECODE(body_bytes))
  expected = "sha256=" + HMAC_SHA256_HEX(shared_secret, UTF8_ENCODE(message))
  IF NOT constant_time_equals(sig_header, expected):
    RETURN REJECT(401, "invalid_signature")

  storage_key = FORMAT("<tenant>/<endpoint>/{event_id_b}")
  IF seen_set_contains(storage_key):
    RETURN ACCEPT_IDEMPOTENT(200)                  // no side effect

  IF NOT idempotency_store_mark_processed(event_id_b):
    RETURN ACCEPT_IDEMPOTENT(200)                  // concurrent duplicate

  PROCESS_BUSINESS_LOGIC(body_bytes)
  seen_set_store(storage_key, TTL=max_seen_window)
  RETURN ACCEPT(200)
```

**Timestamp 窗口與重放防護**

| 項目 | 建議（`proposed_default`） |
|------|---------------------------|
| `timestamp_window_sec` | **300**（±5 分鐘 UTC skew） |
| `max_seen_window_sec` | **86400**（24 h；`event_id` 去重 TTL；應 ≥ retry 最大跨度 + clock skew） |
| `storage_key` | `<tenant>/<endpoint>/<event_id>` |
| `on_replay` | 記錄並忽略，**不重複 side-effect**；回 **200**（推薦）或 **409**（見下表） |

- **Timestamp 窗口外**：視為時鐘漂移或重放攻擊 → **401**（非 replay 快取命中）。
- **Seen-set**：receiver 在 `max_seen_window_sec` 內維護已處理 `(event_id)` 或 `(storage_key)`；同一 `event_id` 在窗口內再次到達 → **replay**（即使 timestamp 不同、signature 有效）。
- **持久化選型**（`proposed_default`，由後續實作票決定）：in-memory / Redis / DB unique constraint；邏輯鍵 SSOT 為 `event_id`。

**Idempotency 行為**

SSOT 冪等鍵 = gateway `event_id`（header `X-Gov-Event-Id` 與 body `event_id` 一致後方可信任）。Receiver **should** 映射至持久化「已處理」狀態（例如 `processed_events` 表或等價 store）：

| 情境 | 建議行為 |
|------|----------|
| 首次成功處理 | 寫入 `processed`（含 `event_id`、處理時間、可選 payload hash）→ 執行 business side-effect → **200** |
| 同 `event_id` 再次投遞（retry / at-least-once） | 快速確認已 `processed` → **跳過 side-effect** → **200**（推薦） |
| 處理中競態（雙寫） | 以 DB unique / distributed lock 保證 **effectively-once**；對外仍回 **200** |

與 §4.6.3 retry 協作：sender retry **must not** 因 receiver 回 **200**（冪等接受）而停止；receiver **must not** 對同 `event_id` 回 **5xx**（避免 retry 風暴）。

**HTTP 回應語意（推薦）**

| 條件 | 建議 HTTP | Sender retry？ | 備註 |
|------|-----------|----------------|------|
| 驗簽失敗 / 缺 header / 無效 signature | **401** 或 **403** | **否**（4xx 非可重試） | **must not** 回 **5xx** |
| Timestamp 超出窗口 | **401** | **否** | |
| `X-Gov-Event-Id` ≠ body `event_id` | **400** | **否** | |
| Replay（已處理同 `event_id`） | **200**（推薦）或 **409** | **否**（200 時 sender 視成功；409 亦為非可重試 4xx） | 推薦 **200 + skip side-effect**，與 at-least-once 最相容 |
| 首次成功處理 | **200** 或 **202** | — | |
| Business 邏輯暫時失敗（receiver 內部） | **503** / **500** | **是**（若 sender retry 已啟用） | 與驗簽失敗區分；驗簽通過後才進入 |

**範例時序（文本）**

1. **Sender → Receiver**：`POST /webhook`，body = JSON notification envelope，headers 含 `X-Gov-Signature-256` · `X-Gov-Timestamp` · `X-Gov-Event-Id`。
2. **Receiver**：讀 raw body → 驗 timestamp 窗口 → 驗 header/body `event_id` 一致 → HMAC 比對 → 查 idempotency / seen-set → 決定處理或跳過。
3. **Receiver → Sender**：驗簽失敗 **401**；replay **200**（無 side-effect）；首次成功 **200**。

**Future 實作票（本 repo · 非本章交付）**

| 票號（建議） | 範圍 |
|--------------|------|
| `WH-P7-NOTIF-HMAC-receiver-fixtures-v1` | `tests/fixtures/webhook_hmac/` 已簽名樣本（body + headers sidecar + README） |
| `WH-P7-NOTIF-HMAC-receiver-sample-impl-v1` | 最小 reference receiver + contract test（成功 / 失簽 / 過期 / replay / event_id mismatch） |

> **仍由後續實作票決定**：seen-set 持久化後端、`409` vs `200` 的客戶可配置策略、staging/prod tier 下「缺 HMAC headers 是否拒絕」的強制 gate（§4.6.6）、HTTP `Idempotency-Key` header 是否與 `event_id` 並送。

#### §4.6.6 URL policy & environment gates

**票**：`WH-P7-NOTIF-PROD-URL-v1` · **SSOT**：tier 語意、URL allowlist grammar、tier policy 對照表、升格前置 checklist。

**impl_status 摘要（2026-06-22 · doc-sync v2）**

| 能力 | `impl_status` | 說明 |
|------|---------------|------|
| sandbox localhost URL gate | **implemented** | `_is_safe_sandbox_url()` · 等同 §4.4 |
| `GOV_NOTIFICATION_WEBHOOK_TIER` 讀取與 tier 分支 | **partial** | adapter 已讀取；sandbox default；staging/prod gate 僅 unittest；**尚不建議真環境啟用** |
| `GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST` 解析與 match | **partial** | adapter 已實作 grammar match；staging/prod 須 allowlist；**尚不建議真環境啟用** |
| staging / prod tier 完整啟用 | **not_implemented_yet** | HMAC/retry/DLQ mandatory reject · prod registry · governance 批文未就緒（§4.6.6.4） |

硬規則（policy · normative）：CI workflow（§4.5）**must** 固定 `TIER=sandbox`（或未設）；**禁止** CI job env 使用 `staging` / `prod`；§4.5 advisory job **仍 non-blocking · sandbox-only**。未設 `TIER` → 視為 `sandbox`（向後相容 §4.4）。`TIER` 與 `URL` host 不一致 → adapter **must reject** POST（fail-closed at URL gate；外層 dispatch 仍 fail-open）。

##### §4.6.6.1 Tier semantics

| tier 值 | 語意 | `impl_status` |
|---------|------|---------------|
| **`sandbox`**（default） | 等同 §4.4：**僅** `localhost` / `127.0.0.1`；`http` 與 `https` 均可；CI / 開發預設；**禁止** non-localhost POST | **implemented**（現行 localhost-only gate） |
| **`staging`** | **內部測試** webhook endpoint；host **must** 為 allowlist 內具名 internal host（**https only**）；須 HMAC + retry + DLQ **policy mandatory**（程式 gate **partial** · mandatory enforce **not_implemented_yet**） | **partial**（adapter URL/https/allowlist gate · 僅 unittest；**尚不建議啟用**） |
| **`prod`** | **客戶真實** webhook endpoint；`URL` **must** match allowlist **∩** per-customer registry；**https only**；HMAC **mandatory**（缺簽名 **reject POST**，與 sandbox fail-open 不同）；retry + DLQ **mandatory** | **partial**（adapter gate **partial** · registry **not_implemented_yet**；**尚不建議啟用**） |

**現況聲明**：adapter 已實作 `sandbox` tier（§4.4 localhost gate）及 `staging`/`prod` **minimal URL gate**（票 `WH-P7-NOTIF-PROD-URL-impl-v1` · 僅 unittest）。**prod 線 Non-goals**：不得在真實 staging/prod 環境啟用 tier，直至 §4.6.6.4 checklist 與 governance 批文完成。

**Env 鍵**：`GOV_NOTIFICATION_WEBHOOK_TIER` ∈ {`sandbox`, `staging`, `prod`} — **partial**（adapter 已讀取；未設等同 `sandbox`）。

##### §4.6.6.2 URL allowlist grammar

**Env 鍵**：`GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST` — **partial**（adapter 已實作 grammar match；staging/prod tier 須設；sandbox tier **ignore** allowlist；**尚不建議真環境啟用** · 實作見 `WH-P7-NOTIF-PROD-URL-impl-v1`）。

**格式**

- 多 entry；entry 之間以 **逗號** `,` 分隔（trim 空白）。
- 每 entry 為下列之一：
  - **`host`** — 具名字 hostname（literal 或 glob，見下）
  - **`host:port`** — 具名 host + 明確 port
  - **`host/path-prefix`** — host（可含 port）+ 可選 path glob

**Host pattern**

- **允許**：literal hostname（如 `staging.internal.example.com`）；子域 glob 以 `*.` 前綴（如 `*.staging.internal.example`）。
- **禁止**（staging / prod）：bare IP（減 SSRF 面）；sandbox tier 仍僅 localhost / 127.0.0.1（§4.4），**不**經 allowlist。

**Path pattern（可選）**

- 未指定 path → entry 僅約束 host（全 path 允許 — future impl 票可裁決是否限縮）。
- 可指定 path 前綴或 glob，如 `/webhook` 或 `/webhook/*`。

**Scheme 規則**

- **sandbox**：`http` / `https` 均可；host **must** 為 `localhost` 或 `127.0.0.1`。
- **staging / prod**：`GOV_NOTIFICATION_WEBHOOK_URL` scheme **must** be `https`。

**與 `GOV_NOTIFICATION_WEBHOOK_URL` 的關係**

- `URL` 的 `(scheme, host, port, path)` **must** match 至少一 allowlist entry（staging / prod tier）。
- **prod** tier 額外要求 endpoint 登記於 **per-customer registry**（檔案或 DB 類型 · 不寫實例路徑）；allowlist 為全域上限，registry 為客戶級精確允許。

**範例 entry（類型說明 · 非 exhaustive · 非真實客戶域名）**

| tier | 範例 allowlist entry | 說明 |
|------|----------------------|------|
| sandbox | *(無 allowlist)* | localhost-only；由 §4.4 gate 強制 |
| sandbox | `127.0.0.1:8080` | 僅作 grammar 示例；sandbox 仍須 host ∈ {localhost, 127.0.0.1} |
| staging | `staging.internal.example.com` | 內部具名 host |
| staging | `*.staging.internal.example/webhook` | 子域 glob + path 前綴 |
| prod | `api.customer.com` | 客戶具名 endpoint（須 registry 登記） |

**Negative example（policy）**：**禁止** sandbox tier / CI / 未批文環境將 `URL` 設為客戶 **production** hostname（類型：`api.<customer>.com` · 不列真實域名）。

##### §4.6.6.3 Tier policy matrix

Normative policy 對照表（`hmac_required` / `retry_required` / `dlq_required` 為 **policy mandatory**；sandbox 現行 **partial** 實作可 opt-in，不得誤繼承為 prod 交付）。

| tier | allowed_hosts | hmac_required | retry_required | dlq_required | approval_required |
|------|---------------|---------------|----------------|--------------|-------------------|
| `sandbox` | `localhost`, `127.0.0.1` only；`http` + `https` | false（opt-in partial OK · default off） | false（default `max_attempts=0`；opt-in partial OK） | false | none |
| `staging` | allowlist 內 **internal** named hosts；**https only** | **true** | **true**（`max_attempts ≥ 1`） | **true** | governance_dual |
| `prod` | allowlist ∩ per-customer registry；**https only** | **true**（缺簽名 **reject POST**） | **true**（`max_attempts ≥ 1`） | **true** | shangshu_prod + security |

**Runtime 現況（adapter · 2026-06-22）**：`staging` / `prod` 之 URL/https/allowlist gate 現僅 **unit test** 中啟用驗證；真實 staging/prod 環境**不建議啟用**，直至 §4.6.6.4 checklist 與 governance 批文完成（policy mandatory 欄位之 HMAC/retry/DLQ reject 仍 **not_implemented_yet**）。

**欄位語意**

- **`allowed_hosts`**：摘要；精確 grammar 見 §4.6.6.2。
- **`hmac_required`**：policy 層 mandatory；sandbox sender 現 **partial**（§4.6.5.1 · fail-open unsigned）。
- **`retry_required`**：policy 層 mandatory；sandbox retry 現 **partial**（§4.6.3 · 無 DLQ）。
- **`dlq_required`**：retry 用盡或不可重試失敗須可觀測落盤（§4.6.4）；sandbox DLQ 現 **partial**（opt-in env · default off）
- **`approval_required`**：`none` \| `governance_dual`（Wave-H 雙人批准）\| `shangshu_prod + security`（尚書省 prod 批文 + Security sign-off）。

##### §4.6.6.4 Enablement checklist

在將 tier 從 **sandbox** 升格至 **staging** 或 **prod** 前，**must** 完成下列項（policy mandatory；順序建議供 Orchestrator 裁決）：

- **DLQ 設計 / 落盤** — 票 `WH-P7-NOTIF-DLQ-v1` · `WH-P7-NOTIF-DLQ-impl-v1`（**partial** · env gated）· inspect CLI `WH-P7-NOTIF-DLQ-inspect-cli-v1`；staging/prod **required**
- **Retry 升格** — sandbox partial（`WH-P7-NOTIF-RETRY-SANDBOX-v1`）→ prod/staging tier gate；票 `WH-P7-NOTIF-RETRY-prod-v1`（或併入 DLQ 票）
- **HMAC sender prod mandatory** — 票 `WH-P7-NOTIF-HMAC-prod-mandatory-v1`；staging/prod 缺簽名須 reject POST（與 sandbox fail-open 分支）
- **HMAC receiver contract** — §4.6.5.2 · 票 `WH-P7-NOTIF-HMAC-receiver-contract-v1`（doc SSOT · **required**）
- **Receiver fixtures / sample impl** — 票 `WH-P7-NOTIF-HMAC-receiver-fixtures-v1` · `WH-P7-NOTIF-HMAC-receiver-sample-impl-v1`（staging recommended · prod **required**）
- **URL tier + allowlist 程式 gate** — 票 **`WH-P7-NOTIF-PROD-URL-impl-v1`**（**partial** · adapter 已讀取 `TIER` + `URL_ALLOWLIST`；https gate；host/path match；unittest only）
- **Staging 整合測試**（人工 env · 非 CI prod URL）— 票 `WH-P7-NOTIF-staging-integration-v1`；mock 或內部 staging endpoint
- **Governance 批文** — staging：`governance_dual`（Wave-H）；prod：**尚書省 prod 批文** + Security（§4.6.7 門檻）
- **Advisory CI 穩定** — `p7-notification-smoke`（§4.5）仍 **sandbox-only**；CI **禁止** `staging` / `prod` tier env

**建議啟用順序**：DLQ → prod retry 升格 → HMAC receiver fixtures → **PROD-URL-impl** → staging 整合測試 → prod 批文後 rollout。

**衍伸實作票（§4.6.6 外 · 索引）**

| 票號 | 範圍摘要 |
|------|----------|
| **`WH-P7-NOTIF-PROD-URL-impl-v1`** | adapter 讀取 `TIER` + `URL_ALLOWLIST`；host/path match、https gate、tier 分支；**partial**（unittest only） |

##### Env / config 鍵表（§4.6.0 cross-ref）

| env_key | tier | purpose | impl_status |
|---------|------|---------|-------------|
| `GOV_NOTIFICATION_WEBHOOK_ENABLED` | all | master switch | **implemented** |
| `GOV_NOTIFICATION_WEBHOOK_URL` | all | target URL | **implemented**（sandbox host check） |
| `GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_ATTEMPTS` | sandbox | retry 次數上限（`≤0` → 單次 POST） | **partial**（sandbox localhost only；無 DLQ；票 `WH-P7-NOTIF-RETRY-SANDBOX-v1`） |
| `GOV_NOTIFICATION_WEBHOOK_RETRY_BASE_DELAY_MS` | sandbox | 指數退避起點（ms） | **partial**（同上） |
| `GOV_NOTIFICATION_WEBHOOK_RETRY_MAX_DELAY_MS` | sandbox | 退避上限（ms） | **partial**（同上） |
| `GOV_NOTIFICATION_WEBHOOK_HMAC_ENABLED` | sandbox | HMAC 簽名 master gate（`1` + secret 非空才簽名） | **partial**（sender-only · default off；票 `WH-P7-NOTIF-HMAC-impl-v1`） |
| `GOV_NOTIFICATION_WEBHOOK_HMAC_SECRET` | sandbox | signing secret（env only；禁止入庫） | **partial**（sender read-only when enabled；**no receiver verification**） |
| `GOV_NOTIFICATION_WEBHOOK_DLQ_ENABLED` | all | DLQ 落盤 master gate（`1` 時最終失敗 append jsonl） | **partial**（default off；票 `WH-P7-NOTIF-DLQ-impl-v1`） |
| `GOV_NOTIFICATION_WEBHOOK_DLQ_PATH` | all | DLQ jsonl 路徑（append-only stream） | **partial**（default `outbox/notification_dlq/events.jsonl`） |
| `GOV_NOTIFICATION_WEBHOOK_DLQ_TIER` | all | DLQ record `tier` 欄位覆寫 | **partial**（default `sandbox`） |
| `GOV_NOTIFICATION_WEBHOOK_TIER` | all | `sandbox` \| `staging` \| `prod` | **partial**（adapter 已讀取；sandbox default；staging/prod gate 僅 unittest · 票 `WH-P7-NOTIF-PROD-URL-impl-v1`） |
| `GOV_NOTIFICATION_WEBHOOK_URL_ALLOWLIST` | staging / prod | host/path allowlist grammar（§4.6.6.2） | **partial**（adapter match 已實作；sandbox tier ignore；**尚不建議真環境啟用**） |

#### §4.6.7 Future work & non-goals

本章不涵蓋：多通道（Slack/Email）、bridge outbox 合併、CI 升格 required check、monitoring graph 介入 selector。

**已開 / 已交付票（P7 通知鏈 · 2026-06-22 doc-sync v2）**

| 票號 | 狀態 | 範圍 |
|------|------|------|
| `WH-P7-sandbox-line-wrapup-v1` | `validated` | sandbox 線總 wrap-up · prod 入口索引 |
| `WH-P7-NOTIF-PROD-policy-v1` | `design_accepted` | §4.6 prod-tier policy SSOT 骨架 |
| `WH-P7-NOTIF-RETRY-SANDBOX-v1` | `done` | sandbox localhost retry **partial**（env 驅動 · default off） |
| `WH-P7-NOTIF-HMAC-policy-v1` | `frame_ready` | HMAC & idempotency policy 設計（doc-only） |
| `WH-P7-NOTIF-HMAC-impl-v1` | `impl_done` | sender HMAC-SHA256 **partial**（env gated · default off） |
| `WH-P7-NOTIF-HMAC-receiver-contract-v1` | `implementer_done_pending_review` | receiver 驗簽 / 重放 / idempotency 合約（§4.6.5.2） |
| `WH-P7-NOTIF-contract-partials-validation-v1` | `validated` | retry + HMAC partial 合約 vs 現碼驗證 |
| `WH-P7-NOTIF-contract-doc-sync-v1` | `implementer_done_pending_review` | 合約 §4.6 doc sync（v1 env 表 · v2 DLQ/URL partial） |
| `WH-P7-NOTIF-DLQ-v1` | `implementer_done_pending_review` | DLQ 設計 + §4.6.4 合約擴寫 |
| `WH-P7-NOTIF-DLQ-impl-v1` | `review_done_pending_scribe` | DLQ 落盤 **partial**（env gated · `events.jsonl`） |
| `WH-P7-NOTIF-DLQ-inspect-cli-v1` | `frame_ready` | inspect CLI 設計（doc-only） |
| `WH-P7-NOTIF-PROD-URL-v1` | `implementer_done_pending_review` | tier / allowlist policy 設計 + §4.6.6 擴寫 |
| `WH-P7-NOTIF-PROD-URL-impl-v1` | `review_done_pending_scribe` | `TIER` + `URL_ALLOWLIST` adapter gate **partial**（unittest only） |
| `WH-P7-PROD-roadmap-v1` | `design_accepted` | prod 線 wave 規劃 · 票號 DAG 索引 |

**衍伸實作票（未開或待 Orchestrator 裁決 · 門檻：policy sign-off + 尚書省 prod/staging 批文）**

| 票號（建議） | 範圍 |
|--------------|------|
| `WH-P7-NOTIF-DLQ-inspect-cli-impl-v1` | DLQ inspect list/stats CLI + fixture + unittest（T-5–T-7） |
| `WH-P7-NOTIF-HMAC-receiver-fixtures-v1` | `tests/fixtures/webhook_hmac/` 已簽名樣本 + sidecar headers |
| `WH-P7-NOTIF-HMAC-receiver-sample-impl-v1` | reference receiver + contract test（驗簽 / 重放 / idempotency） |
| `WH-P7-NOTIF-HMAC-prod-mandatory-v1` | staging/prod 缺 HMAC 拒 POST（fail-closed · 與 sandbox fail-open 分支） |
| `WH-P7-NOTIF-RETRY-prod-v1` | retry 從 sandbox partial 升格至 staging/prod tier gate |
| `WH-P7-NOTIF-staging-integration-v1` | 真 staging env 人工整合測試（非 CI prod URL） |
| prod registry gate（待 Orchestrator 定 id） | allowlist ∩ per-customer registry match |

---

### §4.3 `feedback` envelope (nested summary)

Agent-line artifacts (`agent_experiment_regression_v1`, `agent_lines_ci_suite_v1`) may embed a read-only `feedback` object for quickview:

```json
{
  "feedback": {
    "checkpoint_a_status": "would_pause | approved | rejected | n/a",
    "checkpoint_b_status": "would_trigger | approved_delivery | hold | n/a",
    "delivery_approval_recorded": false,
    "controlled_notify_simulated": false,
    "authority": "checkpoint_json_preferred"
  }
}
```

Nested `feedback` is **not** a write target for new producers in v1; producers continue writing authoritative checkpoint / notify files per existing modules.

---

## §5 `join_with_case_history` contract

Function: `tools/tabular_outbox_consumer.join_with_case_history(case_ref)` — read-only.

### §5.1 Success payload (`ok: true`)

| Field | Type | Source |
|-------|------|--------|
| `ok` | bool | `true` when `case_ref` is non-empty |
| `case_ref` | string | Normalized slug |
| `case` | object \| null | Subset from `cases/index.json` matched by `case_dir == cases/<case_ref>` |
| `history` | object | `scripts/cases_index_lib.lookup_cases(client_ref=...)` view |
| `runs` | array | Outbox summaries, **chronological (oldest first)** |
| `last_by_tool_id` | object | Map `tool_id` → latest run summary |
| `run_count` | int | `len(runs)` |

### §5.2 `case` object fields (from `cases/index.json`)

Aligned with index entry when present:

| Field | Index key | Notes |
|-------|-----------|-------|
| `case_dir` | `case_dir` | e.g. `cases/demo_phase` |
| `client_ref` | `client_ref` | Lookup key for `history` |
| `case_id` | `case_id` | Business case id |
| `product_sku` | `product_sku` | |
| `gate_status` | `gate_status` | |
| `schema_headers` | `schema_headers` | |
| `known_limits` | `known_limits` | |

When case absent from index: `case: null`, `history.ok` may be `false` with note `case_not_in_index`; `runs` still returned from outbox scan.

### §5.3 Index SSOT

- **Case registry SSOT**: `cases/index.json` (`schema_version: gov-cases-index-v0.1`)
- **Outbox audit SSOT**: per-run JSON under `outbox/<case_ref>/`
- **Join result**: derived ephemeral view — not persisted

---

## §6 Legacy and degradation rules (AC-8)

When an on-disk artifact lacks `schema_version`:

| Step | Behavior |
|------|----------|
| 1 | Classify `schema_id` as `unknown` |
| 2 | Attempt `case_ref` lookup: path parent dir (for `outbox/<case_ref>/…`) or `case_ref` / `case_summary.case_ref` field inside JSON |
| 3 | If `case_ref` resolves and file matches tabular run filename `{timestamp}_{tool_slug}.json`, treat as **provisional** `tabular_outbox_v1` for list scans only |
| 4 | `get_outbox_run()` remains strict: missing or mismatched `schema_version` → `ok: false`, `message: unsupported_schema_version` |
| 5 | Log degradation at consumer discretion; **no** auto-migration writes |

Namespace inference for flat files (agent lines):

| Path prefix | Provisional `schema_id` when version missing |
|-------------|-----------------------------------------------|
| `outbox/agent_experiment_regression/` | `agent_experiment_regression_v1` |
| `outbox/agent_ci/` | `agent_lines_ci_suite_v1` |
| `outbox/non_tabular_experiment/` | `non_tabular_experiment_preview_v1` |
| `outbox/sandbox_delivery/` | `sandbox_delivery_bundle_v1` |
| `outbox/agent_metrics/` | `agent_lines_metrics_v1` |

---

## §7 Observability conventions

### §7.1 Tabular `events.jsonl` (`outbox/events.jsonl`)

Optional append-only file. One JSON object per line after each non-dry-run tabular execute.

**`event_type` enum (v1)**

| `event_type` | When |
|--------------|------|
| `tabular_tool_run` | Default line written by `append_event_line()` |
| `tabular_tool_run_failed` | Reserved — same writer today; consumers may distinguish via `ok: false` |

Line shape (minimum): `case_ref`, `run_id`, `tool_id`, `ok`, `exit_code`, `started_at`, `finished_at`, `dry_run`.

### §7.2 Metrics (WB-T4 indirect)

| Metric key | Source | Notes |
|------------|--------|-------|
| `outbox_write_count` | Aggregated from parsed runs in `outbox/agent_metrics/metrics_summary.json` | Not a live counter |
| `outbox_read_count` | Reserved for future consumer instrumentation | v1: undefined live hook |

### §7.3 Traces

| Field | Status |
|-------|--------|
| `run_id` | Always present on tabular per-run records |
| `trace_id` | **Optional sidecar** — may appear in agent-line experiment payloads; **not guaranteed** per run |
| `suite_id` / `regression_id` | CI / regression correlation ids |

Contract **does not** require Langfuse or Phase 8.8 trace join.

---

## §8 Implementation appendices (pointers)

| Topic | SSOT appendix (implementation detail) |
|-------|---------------------------------------|
| Tabular per-run write + `events.jsonl` | `docs/tabular-tool-outbox-spec.md` |
| Consumer API + CLI flags | `docs/tabular-outbox-consumer-spec.md` |
| Agent regression artifacts | `docs/agent-standard-case-regression-v1.md` |
| Agent CI merged summary | `docs/agent-lines-ci-suite-v1.md` |
| Non-tabular preview sandbox | `docs/non-tabular-orchestrator-preview-v1.md` |
| Sandbox delivery bundle | `docs/tabular-controlled-end-to-end-delivery-sandbox-v1.md` |
| Agent metrics | `docs/agent-lines-metrics-and-monitoring-v1.md` |
| HITL design | `docs/hitl-checkpoints-v1.md` |

---

## §9 Verification

```bash
python -m unittest tests.test_outbox_and_feedback_layer_contract_v1 -v
python -m tools.inspect_tabular_outbox --case-ref demo_phase --json --outbox-root tests/fixtures/outbox
```

---

*WB-T3 · Phase 8.9 Outbox · Feedback Layer Contract v1 · 2026-06-11*
