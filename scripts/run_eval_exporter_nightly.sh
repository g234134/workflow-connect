#!/usr/bin/env bash
#
# run_eval_exporter_nightly.sh — produce eval_export/v1 JSONL from shadow ibridge export.
#
# Non-gating: intended for eval-shadow-nightly only (continue-on-error in CI).
# Reuses flat ibridge JSONL from the shadow pipeline; does not re-run eval_ci_check.
#
# Usage:
#   bash scripts/run_eval_exporter_nightly.sh
#
# Env:
#   EVAL_EXPORT_INPUT — source JSONL (default: SHADOW_EXPORT_OUT or
#                        artifacts/eval/shadow_ibridge_records.latest.jsonl)
#   EVAL_EXPORT_DIR   — output directory (default: artifacts/eval)
#

set -euo pipefail

INPUT="${EVAL_EXPORT_INPUT:-${SHADOW_EXPORT_OUT:-artifacts/eval/shadow_ibridge_records.latest.jsonl}}"
OUT_DIR="${EVAL_EXPORT_DIR:-artifacts/eval}"
DATE="$(date -u +%Y%m%d)"
OUT="${OUT_DIR}/eval_export_v1_shadow_nightly.${DATE}.jsonl"
LATEST="${OUT_DIR}/eval_export_v1_shadow_nightly.latest.jsonl"

if [[ ! -s "${INPUT}" ]]; then
  echo "[EVAL-EXPORT] error: input missing or empty: ${INPUT}" >&2
  exit 1
fi

mkdir -p "${OUT_DIR}"

python -m observability.eval_exporter "${INPUT}" -o "${OUT}"
cp "${OUT}" "${LATEST}"

echo "[EVAL-EXPORT] input=${INPUT}"
echo "[EVAL-EXPORT] wrote ${OUT}"
echo "[EVAL-EXPORT] wrote ${LATEST}"
