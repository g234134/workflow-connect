"""One-off: recalc P7/P8.5/P9 sub-line progress from *_state.md (read-only audit)."""
from __future__ import annotations

import re
from pathlib import Path

STATUS_PCT = {
    "frame_ready": 25,
    "design_accepted": 40,
    "implementer_done_pending_run": 55,
    "implementer_done_pending_review": 60,
    "impl_done": 70,
    "review_done_pending_scribe": 80,
    "done_with_gaps": 90,
    "validated": 100,
    "done": 100,
}

CLOSED = {"validated", "done", "done_with_gaps"}

GROUPS = {
    "P7 sandbox": [
        "WD-P7-T1-orchestrator-gate-bundle-notify-v1",
        "WD-P7-T2-webhook-sandbox-dispatch-v1",
        "WD-P7-T3-orchestrator-dispatch-full-smoke-v1",
        "WH-P7-NOTIF-RETRY-SANDBOX-v1",
        "WH-P7-NOTIF-DLQ-v1",
        "WH-P7-NOTIF-DLQ-impl-v1",
        "WH-P7-NOTIF-DLQ-inspect-cli-v1",
        "WH-P7-NOTIF-DLQ-inspect-cli-impl-v1",
        "WH-P7-NOTIF-contract-doc-sync-v1",
        "WH-P7-NOTIF-HMAC-impl-v1",
        "WH-P7-NOTIF-HMAC-receiver-contract-v1",
        "WH-P7-NOTIF-contract-partials-validation-v1",
        "WH-P7-sandbox-line-wrapup-v1",
    ],
    "P7 prod": [
        "WH-P7-PROD-roadmap-v1",
        "WH-P7-PROD-phase1-wrapup-v1",
        "WH-P7-PROD-RETRY-HMAC-microplan-v1",
        "WH-P7-NOTIF-PROD-policy-v1",
        "WH-P7-NOTIF-PROD-URL-v1",
        "WH-P7-NOTIF-PROD-URL-impl-v1",
        "WH-P7-NOTIF-RETRY-prod-v1",
        "WH-P7-NOTIF-RETRY-prod-impl-v1",
        "WH-P7-NOTIF-HMAC-policy-v1",
        "WH-P7-NOTIF-HMAC-prod-mandatory-v1",
        "WH-P7-NOTIF-HMAC-prod-impl-v1",
    ],
    "P7 staging": [
        "WH-P7-PROD-staging-integration-v1",
        "WH-P7-PROD-staging-env-config-v1",
        "WH-P7-PROD-staging-smoke-runbook-v1",
    ],
    "P8.5 wave-H": [
        "WD-P85-T1-bridge-browser-fixture-smoke-v1",
        "WD-P85-T2-bridge-runbook-index-closure-v1",
        "WD-P85-T3-bridge-index-test-count-closure-v1",
        "WD-P85-T4-bridge-negative-plan-fixture-v1",
        "WH-P85-SMOKE-B-advisory-v1",
        "WH-P85-CI-LAND-v1",
    ],
    "P8.5 wave-H+1": [
        "WH-P85-SMOKE-B-scenario2-v1",
        "WH-P85-CI-LAND-doc-sync-v1",
    ],
    "P8.5 wave-H+2": [
        "WH-P85-wave-H2-entry-v1",
        "WH-P85-SMOKE-B-scenario2-ops-run-v1",
    ],
    "P9 narrow": [
        "WD-P9-T1-wc-m2-order-demo-e2e-v1",
        "WD-P9-T2-wc-m2-hitl-fixture-automation-v1",
        "WH-P9-M2-INT-alignment-v1",
    ],
}

# Alternate sandbox grouping (DLQ in prod per wrapup docs)
GROUPS_ALT_SANDBOX = {
    "P7 sandbox (core WD+WH sandbox only)": [
        "WD-P7-T1-orchestrator-gate-bundle-notify-v1",
        "WD-P7-T2-webhook-sandbox-dispatch-v1",
        "WD-P7-T3-orchestrator-dispatch-full-smoke-v1",
        "WH-P7-NOTIF-RETRY-SANDBOX-v1",
        "WH-P7-NOTIF-HMAC-impl-v1",
        "WH-P7-NOTIF-HMAC-receiver-contract-v1",
        "WH-P7-NOTIF-contract-partials-validation-v1",
        "WH-P7-sandbox-line-wrapup-v1",
    ],
    "P7 prod (+ DLQ/contract in prod phase)": [
        "WH-P7-PROD-roadmap-v1",
        "WH-P7-PROD-phase1-wrapup-v1",
        "WH-P7-PROD-RETRY-HMAC-microplan-v1",
        "WH-P7-NOTIF-PROD-policy-v1",
        "WH-P7-NOTIF-PROD-URL-v1",
        "WH-P7-NOTIF-PROD-URL-impl-v1",
        "WH-P7-NOTIF-RETRY-prod-v1",
        "WH-P7-NOTIF-RETRY-prod-impl-v1",
        "WH-P7-NOTIF-HMAC-policy-v1",
        "WH-P7-NOTIF-HMAC-prod-mandatory-v1",
        "WH-P7-NOTIF-HMAC-prod-impl-v1",
        "WH-P7-NOTIF-DLQ-v1",
        "WH-P7-NOTIF-DLQ-impl-v1",
        "WH-P7-NOTIF-DLQ-inspect-cli-v1",
        "WH-P7-NOTIF-DLQ-inspect-cli-impl-v1",
        "WH-P7-NOTIF-contract-doc-sync-v1",
    ],
}


def extract_status(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    matches = re.findall(
        r"\*\*overall_status\*\*:\s*(?:`([a-z0-9_]+)`|([a-z0-9_]+))",
        text,
        re.I,
    )
    if not matches:
        return None
    last = matches[-1]
    return (last[0] or last[1]).lower()


def summarize(group: str, ids: list[str], tickets_dir: Path) -> dict:
    rows = []
    pcts: list[int] = []
    closed = strict = 0
    for tid in ids:
        paths = list(tickets_dir.glob(f"{tid}_state.md"))
        if not paths:
            rows.append((tid, "MISSING", None))
            continue
        st = extract_status(paths[0])
        p = STATUS_PCT.get(st or "", None)
        if p is not None:
            pcts.append(p)
        if st in CLOSED:
            closed += 1
        if st in ("validated", "done"):
            strict += 1
        rows.append((tid, st, p))
    avg = sum(pcts) / len(pcts) if pcts else 0.0
    return {
        "group": group,
        "avg": avg,
        "closed": closed,
        "total": len(ids),
        "strict": strict,
        "rows": rows,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    tickets_dir = root / "04_Workflows" / "tickets"
    print("=== PRIMARY GROUPING (user table) ===")
    results = []
    for g, ids in GROUPS.items():
        r = summarize(g, ids, tickets_dir)
        results.append(r)
        print(f"\n{g}: avg={r['avg']:.1f}% closed={r['closed']}/{r['total']} strict={r['strict']}/{r['total']}")
        for tid, st, p in r["rows"]:
            print(f"  {tid}: {st} -> {p}")

    p7_ids = GROUPS["P7 sandbox"] + GROUPS["P7 prod"] + GROUPS["P7 staging"]
    p7 = summarize("P7 composite", p7_ids, tickets_dir)
    print(f"\nP7 composite (27): {p7['avg']:.1f}% closed={p7['closed']}/{p7['total']}")

    p85_ids = GROUPS["P8.5 wave-H"] + GROUPS["P8.5 wave-H+1"] + GROUPS["P8.5 wave-H+2"]
    p85 = summarize("P8.5 composite", p85_ids, tickets_dir)
    print(f"P8.5 composite (10): {p85['avg']:.1f}% closed={p85['closed']}/{p85['total']}")

    print("\n=== ALT GROUPING (DLQ under prod) ===")
    for g, ids in GROUPS_ALT_SANDBOX.items():
        r = summarize(g, ids, tickets_dir)
        print(f"{g}: avg={r['avg']:.1f}% closed={r['closed']}/{r['total']}")

    # Read P9 state files for full WC scope mention
    for extra in ["WC-T1", "WC-T2", "WC-T3", "WC-T4", "WC-T5", "WC-T6", "WC-T7"]:
        paths = list(tickets_dir.glob(f"*{extra}*_state.md"))
        if paths:
            st = extract_status(paths[0])
            print(f"Lane C {paths[0].name}: {st} -> {STATUS_PCT.get(st or '', '?')}")


if __name__ == "__main__":
    main()
