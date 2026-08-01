# Control Plane Dispatch Executor (W-next MVP)

Read-only **dispatch brain** for Multi-Chat ticket workflow. It scans markdown state files and emits structured suggestions for humans, Cursor, or a future supervisor—without opening chats, calling LLMs, or mutating runtime.

## Purpose

- Reduce manual reading of many `*_state.md` files before deciding the next chat role.
- Classify tickets into `runnable_now`, `blocked`, `in_review`, `done`, `draft`.
- Recommend role (`implementer` / `reviewer` / `scribe` / `orchestrator`), optional parallel groups, and starter commands.

**Out of scope (this version):** auto-open Cursor chats, Cursor API dispatch, auto-apply STATE changes, full workflow engine.

## Inputs

| Source | Path (repo-relative) | Usage |
|--------|----------------------|--------|
| Ticket state | `04_Workflows/tickets/*_state.md` | Primary SSOT — FRAME + STATE sections |
| Run queue | `workflow_v2/90_run_queue.md` (fallback: `workflow_upgrade/90_run_queue.md`) | TODO row heuristic → coordination notes |
| Latest status | `workflow_v2/99_latest_status.md` | Wave summary snippet → coordination notes |

Missing optional files add `warnings[]`; the executor does not crash.

## Run

From repo root:

```powershell
python Scripts/run_dispatch_executor.py --pretty
python Scripts/run_dispatch_executor.py --ticket W1-T2 --pretty
python Scripts/run_dispatch_executor.py --json-out artifacts/control_plane/dispatch_plan.latest.json --md-out artifacts/control_plane/dispatch_plan.latest.md
```

Flags:

- `--ticket` — substring filter on ticket id / filename
- `--json-out` / `--md-out` — artifact paths (default under `artifacts/control_plane/`)
- `--no-write` — stdout only
- `--pretty` — print full JSON plan to stdout

## Output

### JSON (`dispatch_plan.latest.json`)

Key fields:

- `generated_at`, `tickets_scanned`, `warnings`
- `runnable_now[]`, `blocked[]`, `in_review[]`, `done[]`, `draft[]`
- `suggested_next[]` — per-ticket `recommended_role`, `reason`, `commands[]`, `can_parallelize`, `parallel_group`, `blocked_by`, `expected_output`
- `parallel_groups[]` — ticket ids that may run in parallel
- `coordination_notes[]`, `recommended_chat_count`

### Markdown (`dispatch_plan.latest.md`)

Human summary of the same plan (counts, suggested next, coordination notes).

## Decision rules (hardcoded v1)

| Condition | Bucket | Role |
|-----------|--------|------|
| `overall_status=blocked` (unless `infra_unblock` in next_action) | blocked | — |
| Unresolved FRAME dependency not in done set | blocked | — |
| `implementation_status=in_review` or `overall_status=review` or reviewer wait in next_action | in_review | reviewer |
| `overall_status=done` + `current_owner=scribe` | done | scribe (progress append) |
| `overall_status=in_progress` + implement/resume/wire/test in next_action | runnable_now | implementer |
| `overall_status=draft` + assign/implementer in next_action | draft / runnable | implementer or orchestrator |
| Done tickets (e.g. W1-T2) | done | not runnable_now; may be dependency premise |

Parallel groups: runnable tickets with different `recommended_role` and no `blocked_by` may share a `parallel_group`.

## Confidence

Each ticket includes `confidence` per field (`high` / `low`). Missing STATE bullets are parsed with low confidence; warnings are listed at plan level.

## Tests

```powershell
python -m unittest tests.test_dispatch_executor -v
```

Fixtures: `tests/fixtures/dispatch/*.md` (blocked, in_review, scribe-done).

## Known limits

- Markdown parsing is heuristic (bullet keys in STATE/FRAME only).
- Run queue TODO detection is table-line regex, not full schema validation.
- No automatic dependency graph beyond FRAME `Dependencies` vs done ticket ids.
- `accepted_with_gaps` legacy status is treated as done.

## Module layout

- Logic: `04_Workflows/dispatch_executor.py`
- CLI: `Scripts/run_dispatch_executor.py`

---

## Dispatch Cards

Instruction card generator that turns `dispatch_plan.latest.json` plus **read-only** ticket FRAME parsing into copy-paste `*.cursor.md` drafts for Multi-Chat handoff.

### Authority rule

When the plan and a ticket's FRAME disagree (paths, scope, dependencies), **the ticket state FRAME is authoritative**. The plan only ranks tickets and suggests roles/commands; it must **not** override FRAME `AllowedPaths` / `BlockedPaths` / `NonScope`.

### Inputs

| Source | Path | Usage |
|--------|------|--------|
| Dispatch plan | `artifacts/control_plane/dispatch_plan.latest.json` | `runnable_now[]`, `suggested_next[]` |
| Ticket state | `04_Workflows/tickets/{ticket_id}_state.md` | FRAME `AllowedPaths`, `BlockedPaths`, `VerificationCommands` (read-only) |

### Outputs

- Cards: `artifacts/control_plane/cards/{ticket_id}__{role}.cursor.md`
- Optional run summary: `artifacts/control_plane/dispatch_cards_run.latest.json`

Each card includes **Provenance** with `source_path`, `generated_at` (ISO8601 UTC), and `plan_snapshot`.

### Run

From repo root:

```powershell
# Refresh plan (optional), then generate implementer cards
python Scripts/run_dispatch_executor.py --pretty
python Scripts/run_dispatch_cards.py --role implementer --limit 5 --pretty

# Single ticket, dry-run summary only
python Scripts/run_dispatch_cards.py --ticket C2-D1 --role implementer --dry-run --pretty

# Refresh plan inline, all roles
python Scripts/run_dispatch_cards.py --refresh-plan --role all --limit 5 --pretty
```

### CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--plan` | `artifacts/control_plane/dispatch_plan.latest.json` | Plan JSON path |
| `--out-dir` | `artifacts/control_plane/cards/` | Card output directory |
| `--role` | `all` | `implementer` \| `reviewer` \| `scribe` \| `all` |
| `--limit` | `5` | Max `suggested_next` supplement (draft/runnable_now, no `blocked_by`) |
| `--ticket` | — | Single ticket id filter |
| `--refresh-plan` | off | Run `run_dispatch_executor.py` first |
| `--dry-run` | off | JSON summary only; no card files |
| `--json-summary` | `artifacts/control_plane/dispatch_cards_run.latest.json` | Write run summary |
| `--pretty` | off | Pretty JSON to stdout |
| `--eligibility-gate` | `block` | `off` \| `warn` \| `block` — see **Eligibility gate** below |
| `--force-eligibility` | off | Orchestrator override when gate would skip ineligible tickets |

### Eligibility gate

Before writing each card, `generate_cards()` calls `check_ticket_eligibility()` (WC-T1) with `context.requested_role` set to the plan’s recommended role. Gate behavior:

| Mode | Ineligible ticket | Card file | Summary / provenance |
|------|-------------------|-----------|----------------------|
| **`block`** (default) | Skipped — no `*.cursor.md` | — | `eligibility_blocked[]` entry with `ticket_id`, `role`, `reasons`, `bucket`; top-level `eligibility_gate`: `"block"` |
| **`warn`** | Still written | Provenance includes `eligibility_warning` | `warnings[]` includes `eligibility_warn:{ticket_id}:{reasons}`; per-card record has `eligibility_warnings[]` |
| **`off`** | Gate not run | Same as pre-integration | No `eligibility_blocked[]`; `eligibility_gate`: `"off"` |

**`--force-eligibility`** (Orchestrator override): when `--eligibility-gate block` would skip a ticket, still write the card. Summary records `eligibility_override: true`, `eligibility_overridden_tickets[]`, and `warnings[]` includes `eligibility_override:{ticket_id}:{reasons}`. Card Provenance includes `eligibility_override: true`.

**Where records live**

- Run summary (`dispatch_cards_run.latest.json`): `eligibility_gate`, `eligibility_blocked[]`, optional `eligibility_override` / `eligibility_overridden_tickets[]`, plus `warnings[]` tags above.
- Per-card record in summary `cards[]`: `eligibility_warnings[]`, `eligibility_override`, or `skipped: true` with `eligibility` snapshot when blocked.
- Card markdown **Provenance**: `eligibility_warning` / `eligibility_override` lines when applicable.

**Example (block default, dry-run blocked ticket)**

```powershell
python Scripts/run_dispatch_cards.py --ticket TEST-BLK --role implementer --dry-run --pretty
# cards_generated=0; eligibility_blocked[0].reasons contains overall_status_blocked
```

**Example (Orchestrator force override)**

```powershell
python Scripts/run_dispatch_cards.py --ticket TEST-BLK --role implementer --force-eligibility --pretty
```

Design SSOT: `docs/wave_c/WC_T1_eligibility.md` §8 (entry A implemented by WC-T1-INTEGRATION).

### Selection logic

1. Include **all** `runnable_now[]` tickets matching `--role`.
2. Supplement with up to `--limit` entries from `suggested_next[]` where `bucket` is `runnable_now` or `draft` and `blocked_by` is empty.
3. Commands = dedupe(`plan.commands` + FRAME `VerificationCommands`).
4. FRAME parse failures add `[parse_warning]` in the card; generation continues.

### Example card fragment

```markdown
## Provenance
- **source_path**: 04_Workflows/tickets/C2-D1_state.md
- **generated_at**: 2026-06-07T08:00:00+00:00
- **plan_snapshot**: artifacts/control_plane/dispatch_plan.latest.json

## AllowedPaths
- `cases/demo_phase/*`
- `notebooks/csv_cleaning/*`
```

### Tests

```powershell
python -m unittest tests.test_dispatch_cards tests.test_dispatch_executor -v
```

Fixtures: `tests/fixtures/dispatch/sample_plan.json`, `card_ticket_good.md`, `card_ticket_no_paths.md`.

### Module layout (cards)

- Logic: `04_Workflows/_dispatch_cards.py`
- CLI: `Scripts/run_dispatch_cards.py`
