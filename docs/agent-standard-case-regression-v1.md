# Agent-Run Standard Case Experiment Regression v1

> **Ticket**: W6-T8 · agent-standard-case-experiment-regression-hook-v1  
> **Implementation**: `scripts/run_agent_standard_case_regression.py`  
> **Upstream**: `scripts/run_agent_standard_case_experiment.py` (W6-T4)  
> **Date**: 2026-06-10  
> **Status**: experimental-line regression hook — **does not** replace or modify MVP mainline regression

---

## 1. Purpose

Provide a **one-command lightweight regression hook** for the Agent-run standard case experiment line (`demo_phase` + `sampleco/2026-0001`).

This helper:

- Runs the W6-T4 experiment orchestrator in preview (default) or partial run (demo_phase only)
- Writes comparable JSON artifacts under `outbox/agent_experiment_regression/`
- Emits a per-case summary (`final_status`, `checkpoint_a_status`, `checkpoint_b_status`)

It is **independent** from `scripts/run_mvp_mainline_regression.py` and does not integrate into the existing MVP regression unittest suite.

---

## 2. What is covered

| Case | Directory | Default mode | Notes |
|------|-----------|--------------|-------|
| **demo_phase** | `cases/demo_phase` | `preview` | Checkpoint A `would_pause`; `final_status=waiting_for_human` |
| **sampleco** | `cases/sampleco/2026-0001` | `preview` | Checkpoint B `would_trigger`; ratio guard warning profile |

Optional `--run-mode run` applies **only to demo_phase**; sampleco stays `preview`.  
W7-T2: `--run-mode run-all-allowed` runs **both** allowlist fixtures per `run_path_profile` (demo_phase→bundle; sampleco→checkpoint_b).

---

## 3. How to run

### One command (recommended)

```bash
python scripts/run_agent_standard_case_regression.py
```

JSON summary to stdout:

```bash
python scripts/run_agent_standard_case_regression.py --format json
```

### Partial run (demo_phase only)

```bash
python scripts/run_agent_standard_case_regression.py --run-mode run --auto-approve-intake
```

### Run-all-allowed (W7-T2)

```bash
python scripts/run_agent_standard_case_regression.py --run-mode run-all-allowed --auto-approve-intake
```

### Unittest

```bash
python -m unittest tests.test_agent_standard_case_regression -v
```

**Success**: exit code `0`; summary shows `ok: true` and `passed: 2/2`.  
**Failure**: exit code `1`; inspect per-case `ok` and artifact JSON under outbox.

---

## 4. Artifact layout

Each case run writes:

```text
outbox/agent_experiment_regression/<timestamp>_<case_ref_slug>.json
```

Examples:

- `outbox/agent_experiment_regression/20260610T120000Z_demo_phase.json`
- `outbox/agent_experiment_regression/20260610T120000Z_sampleco_2026-0001.json`

Artifact envelope:

```json
{
  "schema_version": "agent_experiment_regression_v1",
  "written_at": "2026-06-10T12:00:00Z",
  "regression_meta": {
    "regression_id": "<uuid>",
    "timestamp": "20260610T120000Z",
    "run_mode": "preview",
    "requested_mode": "preview"
  },
  "case_summary": {
    "case_ref": "demo_phase",
    "final_status": "waiting_for_human",
    "checkpoint_a_status": "would_pause",
    "checkpoint_b_status": "planned"
  },
  "experiment": { "...": "full W6-T4 orchestrator result" }
}
```

---

## 5. CLI parameters

| Flag | Default | Description |
|------|---------|-------------|
| `--run-mode` | `preview` | `preview` (default); `run` (demo_phase only); `run-all-allowed` (W7-T2 profiles) |
| `--auto-approve-intake` | off | Skip Checkpoint A when demo_phase uses `run` mode |
| `--outbox-root` | `outbox/agent_experiment_regression` | Override artifact directory |
| `--format` | `text` | `text` summary or `json` |

---

## 6. When to re-run

Re-run after changes to:

| Area | Typical paths |
|------|----------------|
| Experiment orchestrator | `scripts/run_agent_standard_case_experiment.py` |
| Decision rules | `routing/intake_decision_rules_v1.py` |
| Glue / tool path preview | `routing/intake_to_tabular_glue.py`, `scripts/run_tabular_intake_tool_path.py` |
| Checkpoint helpers | `hitl/checkpoints_v1.py` |
| Standard fixtures | `cases/demo_phase/**`, `cases/sampleco/2026-0001/**` |

**Not a substitute for** MVP mainline E2E regression (`scripts/run_mvp_mainline_regression.py`).

---

## 7. Related docs

| Doc | Focus |
|-----|-------|
| `docs/agent-run-standard-case-orchestrator-v1.md` | W6-T4 orchestrator CLI |
| `docs/agent-run-experiment-eval-guide-v1.md` | Eval / replay methodology |
| `docs/mvp-mainline-regression.md` | Production main-chain regression (separate) |
