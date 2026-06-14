# Tabular Outbox Replay Report v1 — Mini Design (W3-TL-T4 follow-up)

> **Ticket**: W3-TL-T4 follow-up · Local UI / outbox replay closure  
> **Implementation**: `scripts/build_tabular_outbox_replay_report.py`  
> **Consumer SSOT**: `docs/tabular-outbox-consumer-spec.md` · `tools/tabular_outbox_consumer.py`  
> **Date**: 2026-06-13

---

## 1. Problem statement

Wave 3-TL T1–T3 deliver catalog → selector → executor + outbox. T4 (consumer) adds read-only list/get/join APIs and `inspect_tabular_outbox.py`. The remaining gap for **Local UI / replay closure** is a **repeatable, human-readable audit view** that Wave 4 runbooks and local developers can run without a web app.

**Replay** in this ticket means **read-only timeline reconstruction** from persisted outbox records — **not** re-executing tools or Phase 8.8 orchestration replay.

---

## 2. T4 minimum scope (what this MVP does)

| Capability | MVP | Notes |
|------------|-----|-------|
| List runs per `case_ref` | yes | Via `join_with_case_history` / `list_outbox_runs` |
| Chronological timeline | yes | Oldest-first table in MD/HTML |
| `last_by_tool_id` summary | yes | Latest run per catalog `tool_id` |
| Case registry join | yes | `cases/index.json` + `lookup_case_history` view |
| Artifact pointers | yes | From full run records when available |
| `events.jsonl` cross-check | yes | Optional appendix when file exists |
| Write MD report | yes | Default under `outbox/reports/` |
| Write self-contained HTML | yes | Inline CSS only; open in browser |
| JSON stdout (`--json`) | yes | For CI / runbook automation |
| CLI + fixture override | yes | `--outbox-root` for tests |

---

## 3. CLI + HTML/MD as MVP (acceptable closure)

A **static report generator** counts as T4 Local UI closure for Tabular MVP because:

1. Developers get a **local, offline, re-runnable** view without npm/React/Flask.
2. Wave 4 (`run_tabular_intake_tool_path`) and Wave C runbooks can cite one command in verification sections.
3. HTML satisfies “open in browser” local viewing; MD satisfies git-diff / Scribe handoff.

**Primary command**

```bash
python scripts/build_tabular_outbox_replay_report.py --case-ref demo_phase
python scripts/build_tabular_outbox_replay_report.py --case-ref demo_phase --format both --json
```

**Inspect-only (no report file)**

```bash
python tools/inspect_tabular_outbox.py --case-ref demo_phase --join-history
```

---

## 4. Explicit non-goals

| Item | Status |
|------|--------|
| Full web app / SPA | **Out of scope** |
| Auth / multi-user / sessions | **Out of scope** |
| Live websocket tail of `events.jsonl` | **Out of scope** |
| Re-execute / replay subprocess from outbox | **Out of scope** — Phase 8.8 / future ticket |
| Langfuse / DLQ / orchestration_bridge_outbox | **Out of scope** |
| Modify `app/local_ui.py` | **Deferred** — optional W-MVP-W5 integration |
| CI merge gate | **Out of scope** — local unittest only |

---

## 5. Architecture

```text
outbox/<case_ref>/*.json  ──┐
outbox/events.jsonl (opt) ──┼──> tabular_outbox_consumer (read-only)
cases/index.json       ───┘              │
                                           v
                          build_tabular_outbox_replay_report.py
                                           │
                     ┌─────────────────────┴─────────────────────┐
                     v                     v                         v
              replay_*.md           replay_*.html            stdout JSON
           outbox/reports/         (self-contained)         (--json)
```

---

## 6. Output layout

Default directory: `outbox/reports/` (gitignored with parent `outbox/`).

| File pattern | Content |
|--------------|---------|
| `replay_<case_ref>_<UTC>.md` | Markdown timeline + case summary |
| `replay_<case_ref>_<UTC>.html` | Same data, browser-friendly |
| `replay_all_<UTC>.md` | When `--case-ref` omitted |

Report schema version: `tabular_outbox_replay_report_v1`.

---

## 7. Verification

```bash
python -m unittest tests.test_build_tabular_outbox_replay_report -v
python scripts/build_tabular_outbox_replay_report.py \
  --case-ref demo_phase \
  --outbox-root tests/fixtures/outbox \
  --output-dir /tmp/tabular_replay_test \
  --format both
```

Wave 3-TL suite (unchanged):

```bash
python -m unittest tests.test_tabular_outbox_consumer -v
```

---

## 8. Future extensions (non-blocking)

- Embed report link in `app/local_ui.py` (W-MVP-W5)
- Incremental `events.jsonl` tail consumer
- Phase 8.8 cross-ref for true re-execute replay
- Pagination for large outbox trees

---

## 9. Related docs

| Doc | Role |
|-----|------|
| `docs/tabular-outbox-consumer-spec.md` | Consumer API + inspect CLI |
| `docs/tabular-tool-outbox-spec.md` | Per-run write schema |
| `docs/WAVE_PROGRESS_DASHBOARD.md` | Wave 3-TL index |
