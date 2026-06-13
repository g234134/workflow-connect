# WC-T2 · Minimal Ticket Comms Path

> **Ticket**: WC-T2 · customer communication on ticket STATE change  
> **Status**: v0.1 minimal (file-log stub sender)  
> **Scope**: One structured message per Multi-Chat ticket STATE transition — not a full CRM

---

## 1. Purpose

When a Multi-Chat ticket `STATE` section changes (e.g. `overall_status` moves from `in_progress` to `review`), generate a **structured communication payload** and deliver it through a pluggable send adapter.

**In scope (v0.1)**

- Diff two ticket STATE snapshots
- Build JSON payload (title, summary, ticket ref)
- Fake sender: append JSONL to `artifacts/ticket_comms/ticket_comms.jsonl`

**Out of scope**

- Full CRM, contact management, or customer preference store
- Real email / Slack / webhook dispatch (extension point only)
- Auto-writing `*_state.md` (STATE changes remain Orchestrator/manual today)

---

## 2. Ticket state change entry points (repo survey)

| Layer | Path | Role |
|-------|------|------|
| **SSOT storage** | `04_Workflows/tickets/*_state.md` | Markdown handoff files; `## STATE` holds `overall_status`, `current_owner`, `next_action`, `status_by_role` |
| **State schema template** | `04_Workflows/tickets/_templates/ticket_state.template.md` | Valid `overall_status`: `draft \| in_progress \| review \| scribe \| done \| blocked` |
| **Parser / reader** | `04_Workflows/dispatch_executor.py` | `parse_ticket_state_markdown()`, `TicketRecord`, `scan_ticket_files()` — **read-only** control plane |
| **Dispatch consumer** | `04_Workflows/_dispatch_cards.py` | Reads parsed state for Cursor instruction cards — **read-only** |
| **Tests / fixtures** | `tests/test_dispatch_executor.py`, `tests/fixtures/dispatch/*.md` | Parsing and bucket classification coverage |

**Important**: There is **no programmatic state machine or event bus** that writes STATE today. `docs/control_plane_dispatch_executor.md` explicitly lists *auto-apply STATE changes* as out of scope. WC-T2 adds the **comms hook** (`emit_ticket_comms_on_change`) for future writers to call after a STATE update.

---

## 3. Module layout

| Module | Path | Responsibility |
|--------|------|----------------|
| Message generator | `04_Workflows/ticket_comms/message_generator.py` | `TicketStateSnapshot`, `compute_state_diff()`, `build_comms_payload()` |
| Send adapter | `04_Workflows/ticket_comms/sender.py` | `CommsSender` protocol; `FileLogSender` (default stub), `NullSender` (dry-run) |
| Transition hook | `04_Workflows/ticket_comms/transition.py` | `emit_ticket_comms_on_change()` — ties diff → payload → sender |

Package import (with `04_Workflows` on `sys.path`):

```python
from ticket_comms import emit_ticket_comms_on_change, snapshot_from_ticket_record
from dispatch_executor import parse_ticket_state_markdown
```

---

## 4. Message format (`ticket_comms_v0.1`)

```json
{
  "schema_version": "ticket_comms_v0.1",
  "ticket_id": "W1-T2",
  "title": "[W1-T2] Under Review",
  "summary": "Ticket W1-T2: status in progress → under review; owner now reviewer.",
  "ticket_ref": "04_Workflows/tickets/W1-T2_state.md",
  "status": {
    "before": { "overall_status": "in_progress", "current_owner": "implementer" },
    "after":  { "overall_status": "review",      "current_owner": "reviewer" }
  },
  "changed_fields": ["overall_status", "current_owner"],
  "diff": {
    "changed_fields": ["overall_status", "current_owner"],
    "before": { "overall_status": "in_progress", "current_owner": "implementer" },
    "after":  { "overall_status": "review",      "current_owner": "reviewer" }
  },
  "generated_at": "2026-06-13T12:00:00Z"
}
```

### Tracked STATE fields

| Field | Notes |
|-------|-------|
| `overall_status` | Primary customer-facing lifecycle signal |
| `implementation_status` | Optional sub-status (e.g. `in_review`) |
| `current_owner` | Role handoff (`implementer`, `reviewer`, `scribe`, `orchestrator`) |
| `next_action` | Truncated in summary when changed |
| `status_by_role` | Full dict diff when any role status changes |

---

## 5. Send adapter extension points

### Protocol

```python
class CommsSender(ABC):
    def send(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return { ok, message, channel, artifact_path, ticket_id }."""
```

### Built-in adapters

| Adapter | Channel | Behavior |
|---------|---------|----------|
| `FileLogSender` | `file_log` | Appends one JSONL record per message under `outbox_dir/ticket_comms.jsonl`; `simulated: true`, `external_dispatch: false` |
| `NullSender` | `null` | Dry-run; no I/O |

### Future channels (not implemented)

| Channel | Suggested class | Notes |
|---------|-----------------|-------|
| Webhook | `WebhookSender` | POST payload to configured URL; add retry + idempotency key = `ticket_id` + `generated_at` |
| Email | `EmailSender` | Map `summary` → body, `title` → subject; customer address from external CRM |
| Slack | `SlackSender` | Block kit from `title` + `summary` + `ticket_ref` link |

Wire custom sender:

```python
emit_ticket_comms_on_change(before, after, sender=MyWebhookSender(url))
```

---

## 6. Integration hook

Call after any STATE write (manual tooling, future Orchestrator CLI, or file watcher):

```python
from dispatch_executor import parse_ticket_state_markdown
from ticket_comms import emit_ticket_comms_on_change, snapshot_from_ticket_record

before_rec = parse_ticket_state_markdown(old_text, state_path)
after_rec  = parse_ticket_state_markdown(new_text, state_path)

result = emit_ticket_comms_on_change(
    snapshot_from_ticket_record(before_rec),
    snapshot_from_ticket_record(after_rec),
    outbox_dir="artifacts/ticket_comms",
)
# result: { ok, message, sent, payload, send_result, ticket_id }
```

Use `dry_run=True` to build payload without I/O.

---

## 7. First integration path

Until an Orchestrator or file-watcher auto-writes `*_state.md`, the **first real data path** is a dedicated CLI that compares two STATE snapshots and appends JSONL.

| Item | Path |
|------|------|
| CLI | `scripts/run_ticket_state_update_with_comms.py` |
| Test fixtures | `tests/fixtures/ticket_comms/wc_t2_before_state.md`, `wc_t2_after_state.md` |
| CLI test | `tests/test_ticket_state_update_cli.py` |
| Default outbox | `artifacts/ticket_comms/ticket_comms.jsonl` |

**What it does**

1. Read `--before` and `--after` ticket state markdown (path arguments).
2. Parse both with `dispatch_executor.parse_ticket_state_markdown()` → `TicketRecord`.
3. Convert to `TicketStateSnapshot` and call `emit_ticket_comms_on_change()`.
4. On STATE diff, append one JSONL envelope (`channel: file_log`, `payload.schema_version: ticket_comms_v0.1`).

**Does not** write or mutate live `04_Workflows/tickets/*_state.md` files — callers supply snapshots (e.g. copy before edit, save after edit, then run CLI).

```bash
python scripts/run_ticket_state_update_with_comms.py \
  --before tests/fixtures/ticket_comms/wc_t2_before_state.md \
  --after tests/fixtures/ticket_comms/wc_t2_after_state.md
```

Use `--dry-run` to validate parsing and payload shape without I/O; `--outbox-dir` to override the JSONL directory.

Future writers (Orchestrator STATE apply, git hook, or watcher) should call the same hook after persisting a STATE change.

---

## 8. Verification

```bash
python -m unittest tests.test_ticket_comms tests.test_ticket_state_update_cli -v
python scripts/run_ticket_state_update_with_comms.py \
  --before tests/fixtures/ticket_comms/wc_t2_before_state.md \
  --after tests/fixtures/ticket_comms/wc_t2_after_state.md
```

Key assertions:

- No diff → `message: no_state_change`, `sent: false`
- Status transition → payload with `schema_version`, `title`, `summary`, `ticket_ref`
- `FileLogSender` → JSONL line with `simulated: true`

---

## 9. Related docs

- `docs/control_plane_dispatch_executor.md` — ticket STATE reader (W-next MVP)
- `docs/controlled-delivery-notify-experiment-v1.md` — case-level (not ticket) notify experiment pattern (W7-T3)
- `04_Workflows/tickets/_templates/ticket_state.template.md` — STATE field definitions
