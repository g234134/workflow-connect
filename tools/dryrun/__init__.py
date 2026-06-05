"""
Read-only dry-run CLI for eval-shadow / gate artefact comparison.

Does not modify CI, pipeline state, or existing observability modules.
"""

from tools.dryrun.core import (
    DISCLAIMER,
    build_comparison_rows,
    compute_ideal_verdict,
    discover_input_paths,
    load_records_from_paths,
    map_actual_verdict,
    verdicts_match,
)

__all__ = [
    "DISCLAIMER",
    "build_comparison_rows",
    "compute_ideal_verdict",
    "discover_input_paths",
    "load_records_from_paths",
    "map_actual_verdict",
    "verdicts_match",
]
