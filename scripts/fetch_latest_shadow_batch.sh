#!/usr/bin/env bash
#
# fetch_latest_shadow_batch.sh — v0 CI data pipeline: fetch latest shadow batch
# before falling back to fixture bootstrap.
#
# Usage:
#   bash scripts/fetch_latest_shadow_batch.sh
#
# Reads env vars:
#   SHADOW_BATCH_DIR   — directory containing shadow_batch_*.jsonl files
#                        (default: artifacts/eval)
#   SHADOW_SPOOL       — target spool path (Two-Pool sampling output)
#                        (default: artifacts/eval/k2_shadow_spool.jsonl)
#   SHADOW_BASELINE_LIMIT / SHADOW_RISK_RETAIN_LIMIT / SHADOW_RISK_TAGS
#                        — passed through to build_shadow_spool.sh
#
# Behavior:
#   - Scans SHADOW_BATCH_DIR for files matching shadow_batch_*.jsonl.
#   - Selects the one with the highest stamp (lexicographic sort by filename).
#   - If found and non-empty:
#       Runs Two-Pool sampling via build_shadow_spool.sh → SHADOW_SPOOL.
#       Prints  [SHADOW-PIPELINE] mode=shadow batch=<stamp>
#       Exits 0.
#   - If not found:
#       Prints  [SHADOW-PIPELINE] mode=fixture
#       Does NOT touch SHADOW_SPOOL (leaves it empty for fixture bootstrap).
#       Exits 0.
#
# Exit status:
#   0 — always (non-zero only on genuine errors like missing directory)
#
# Design doc: W5-A-RUNTIME-03-SHADOW-SAMPLING-DESIGN-01
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ── defaults ──────────────────────────────────────────────────────────────
SHADOW_BATCH_DIR="${SHADOW_BATCH_DIR:-artifacts/eval}"
SHADOW_SPOOL="${SHADOW_SPOOL:-artifacts/eval/k2_shadow_spool.jsonl}"

# ── ensure batch directory exists (if not, treat as "no batch available") ─
if [[ ! -d "${SHADOW_BATCH_DIR}" ]]; then
    echo "[SHADOW-PIPELINE] mode=fixture"
    exit 0
fi

# ── find the latest shadow_batch_*.jsonl (lexicographic = newest stamp) ───
# Uses filename sort: shadow_batch_20260530.jsonl < shadow_batch_20260531.jsonl
LATEST=$(cd "${SHADOW_BATCH_DIR}" && ls -1 shadow_batch_*.jsonl 2>/dev/null | sort | tail -1 || true)

if [[ -z "${LATEST}" ]]; then
    echo "[SHADOW-PIPELINE] mode=fixture"
    exit 0
fi

# ── extract stamp from filename ───────────────────────────────────────────
# shadow_batch_20260530.jsonl → 20260530
STAMP=$(basename "${LATEST}" .jsonl | sed 's/^shadow_batch_//')

SRC="${SHADOW_BATCH_DIR}/${LATEST}"

if [[ ! -s "${SRC}" ]]; then
    echo "[SHADOW-PIPELINE] mode=fixture"
    exit 0
fi

# ── Two-Pool sampling → spool ─────────────────────────────────────────────
export SHADOW_BATCH="${SRC}"
export SHADOW_SPOOL

if ! bash "${SCRIPT_DIR}/build_shadow_spool.sh"; then
    echo "[SHADOW-PIPELINE] sampling: warning=build_shadow_spool failed, leaving spool empty" >&2
    echo "[SHADOW-PIPELINE] mode=fixture"
    exit 0
fi

echo "[SHADOW-PIPELINE] mode=shadow batch=${STAMP}"
exit 0
