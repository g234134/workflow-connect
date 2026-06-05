"""
Analyze ENF shadow summary JSON lines from CI logs.

Reads [GOV-ENF-SHADOW-SUMMARY] JSON lines from a file or stdin,
aggregates per-run statistics, and prints a human-readable report.

Usage:
  python -m tools.analyze_enf_shadow_summaries --log /path/to/nightly.log
  python -m tools.analyze_enf_shadow_summaries --stdin < /path/to/nightly.log
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from dataclasses import dataclass, field
from typing import TextIO

PREFIX: str = "[GOV-ENF-SHADOW-SUMMARY]"

# ── data models ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RuleStats:
    """Aggregated counters for one rule across multiple runs."""

    would_block: int = 0
    would_warn: int = 0
    shadow_retries: int = 0


@dataclass
class ShadowSummaryRow:
    """Parsed summary line from one CI run."""

    status: str
    total: int
    would_block: int
    would_warn: int
    would_noop: int
    rule1_block: int = 0
    rule2_warn: int = 0
    rule2_shadow_retries: int = 0
    c3_05_warn: int = 0
    reason: str | None = None
    samples: list[dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "ShadowSummaryRow":
        rules = d.get("rules") or {}
        r1 = rules.get("ENF-RULE-1") or {}
        r2 = rules.get("ENF-RULE-2") or {}
        r3 = rules.get("C3-05-L1-INFRA-RISK-SUCCESS") or {}
        samples_raw = (d.get("samples") or {}).get("would_block") or []
        return cls(
            status=d.get("status", "unknown"),
            total=d.get("total", 0),
            would_block=d.get("would_block", 0),
            would_warn=d.get("would_warn", 0),
            would_noop=d.get("would_noop", 0),
            rule1_block=r1.get("would_block", 0),
            rule2_warn=r2.get("would_warn", 0),
            rule2_shadow_retries=r2.get("shadow_retries", 0),
            c3_05_warn=r3.get("would_warn", 0),
            reason=d.get("reason"),
            samples=samples_raw[:5],
        )


# ── parsing ────────────────────────────────────────────────────────────────


def parse_line(line: str) -> ShadowSummaryRow | None:
    """
    Parse a single log line.

    Returns a ShadowSummaryRow if it is a [GOV-ENF-SHADOW-SUMMARY] line with
    valid JSON after the prefix; None otherwise (garbage, wrong prefix, etc.).
    """
    stripped = line.strip()
    if not stripped:
        return None
    if not stripped.startswith(PREFIX):
        return None
    payload = stripped[len(PREFIX) :].lstrip()
    try:
        obj = json.loads(payload)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict):
        return None
    return ShadowSummaryRow.from_dict(obj)


def parse_stream(stream: TextIO) -> list[ShadowSummaryRow]:
    """Read all lines from *stream*, return parsed ShadowSummaryRow list."""
    results: list[ShadowSummaryRow] = []
    for raw_line in stream:
        row = parse_line(raw_line)
        if row is not None:
            results.append(row)
    return results


# ── aggregation & reporting ────────────────────────────────────────────────


def _aggregate_rows(rows: list[ShadowSummaryRow]) -> tuple[
    int, int, int, int, int, RuleStats, RuleStats, RuleStats, list[dict], list[dict], list[dict],
]:
    """Compute aggregate counters across *rows*."""
    total_runs = len(rows)
    total_records = sum(r.total for r in rows)
    total_would_block = sum(r.would_block for r in rows)
    total_would_warn = sum(r.would_warn for r in rows)
    total_would_noop = sum(r.would_noop for r in rows)

    rule1_agg = RuleStats(would_block=sum(r.rule1_block for r in rows))
    rule2_agg = RuleStats(
        would_warn=sum(r.rule2_warn for r in rows),
        shadow_retries=sum(r.rule2_shadow_retries for r in rows),
    )
    rule3_agg = RuleStats(would_warn=sum(r.c3_05_warn for r in rows))

    all_block_samples: list[dict] = []
    all_warn_samples: list[dict] = []
    all_c3_samples: list[dict] = []

    for row in rows:
        for s in row.samples:
            if len(all_block_samples) < 5:
                all_block_samples.append(s)
        # also collect warn samples from raw dict if available

    return (
        total_runs,
        total_records,
        total_would_block,
        total_would_warn,
        total_would_noop,
        rule1_agg,
        rule2_agg,
        rule3_agg,
        all_block_samples,
        all_warn_samples,
        all_c3_samples,
    )


def generate_report(rows: list[ShadowSummaryRow], out: TextIO | None = None) -> None:
    """Print human-readable aggregate report to *out* (default: stdout)."""
    out = out if out is not None else sys.stdout

    if not rows:
        out.write("ENF Shadow Summary Report\n")
        out.write("─" * 50 + "\n")
        out.write("  no data\n")
        return

    (
        total_runs,
        total_records,
        total_would_block,
        total_would_warn,
        total_would_noop,
        r1,
        r2,
        r3,
        block_samples,
        _warn_samples,
        _c3_samples,
    ) = _aggregate_rows(rows)

    out.write("ENF Shadow Summary Report\n")
    out.write("─" * 50 + "\n\n")

    # ── Overall ──────────────────────────────────────────────────────────────
    out.write("Overall\n")
    out.write(f"  runs loaded         : {total_runs}\n")
    out.write(f"  total records       : {total_records}\n")
    out.write(f"  would_block (total) : {total_would_block}\n")
    out.write(f"  would_warn  (total) : {total_would_warn}\n")
    out.write(f"  would_noop  (total) : {total_would_noop}\n")

    if total_records > 0:
        out.write(
            f"  block rate          : {total_would_block / total_records * 100:.1f}%\n"
        )

    # ── Per-Rule ─────────────────────────────────────────────────────────────
    out.write("\nPer-Rule\n")
    out.write(f"  ENF-RULE-1 (block): would_block={r1.would_block}\n")
    out.write(
        f"  ENF-RULE-2 (warn)  : would_warn={r2.would_warn}, "
        f"shadow_retries={r2.shadow_retries}\n"
    )
    out.write(
        f"  C3-05-L1 (warn)    : would_warn={r3.would_warn}\n"
    )

    # ── Samples ──────────────────────────────────────────────────────────────
    out.write("\nSamples (would_block)\n")
    if not block_samples:
        out.write("  (none)\n")
    else:
        for s in block_samples:
            tags = s.get("tags") or []
            out.write(
                f"  [{s.get('task_id', '?')}] "
                f"rule={s.get('dryrun_rule', '?')} "
                f"error={s.get('error_type', '?')} "
                f"tags={', '.join(tags) if tags else 'none'}\n"
            )
    out.write("\n")


# ── CLI ─────────────────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze ENF shadow summary logs from CI.",
        prog="analyze_enf_shadow_summaries",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--log",
        metavar="PATH",
        help="Path to log file to analyze.",
    )
    group.add_argument(
        "--stdin",
        action="store_true",
        help="Read log lines from stdin.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.stdin:
        rows = parse_stream(sys.stdin)
    elif args.log:
        try:
            with open(args.log, encoding="utf-8") as fh:
                rows = parse_stream(fh)
        except OSError as exc:
            print(f"[analyze_enf] error reading {args.log}: {exc}", file=sys.stderr)
            return 1
    else:
        # should be unreachable (mutually exclusive group enforces one)
        parser.print_usage(sys.stderr)
        return 1

    generate_report(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())