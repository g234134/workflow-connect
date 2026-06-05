#!/usr/bin/env bash
#
# build_shadow_spool.sh — Two-Pool sampling for nightly shadow spool.
#
# Reads a shadow batch JSONL, splits into baseline + risk-retained pools,
# merges (deduped by task_id), and writes SHADOW_SPOOL.
#
# Usage:
#   SHADOW_BATCH=artifacts/eval/shadow_batch_20260530.jsonl \
#   SHADOW_SPOOL=artifacts/eval/k2_shadow_spool.jsonl \
#   bash scripts/build_shadow_spool.sh
#
# Env vars:
#   SHADOW_BATCH            — input batch path (required)
#   SHADOW_SPOOL            — output spool path (default: artifacts/eval/k2_shadow_spool.jsonl)
#   SHADOW_BASELINE_LIMIT   — max baseline records (default: 20)
#   SHADOW_RISK_RETAIN_LIMIT — max records per risk tag (default: 3)
#   SHADOW_RISK_TAGS        — comma-separated risk tags (default: infra_risk,high_retry)
#
# Design: W5-A-RUNTIME-03-SHADOW-SAMPLING-DESIGN-01
#

set -euo pipefail

SHADOW_BATCH="${SHADOW_BATCH:-}"
SHADOW_SPOOL="${SHADOW_SPOOL:-artifacts/eval/k2_shadow_spool.jsonl}"
SHADOW_BASELINE_LIMIT="${SHADOW_BASELINE_LIMIT:-20}"
SHADOW_RISK_RETAIN_LIMIT="${SHADOW_RISK_RETAIN_LIMIT:-3}"
SHADOW_RISK_TAGS="${SHADOW_RISK_TAGS:-infra_risk,high_retry}"

if [[ -z "${SHADOW_BATCH}" ]]; then
    echo "[SHADOW-PIPELINE] sampling: error=SHADOW_BATCH not set" >&2
    exit 1
fi

if [[ ! -s "${SHADOW_BATCH}" ]]; then
    echo "[SHADOW-PIPELINE] sampling: error=empty batch ${SHADOW_BATCH}" >&2
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "[SHADOW-PIPELINE] sampling: error=jq not found" >&2
    exit 1
fi

mkdir -p "$(dirname "${SHADOW_SPOOL}")"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

export SHADOW_BASELINE_LIMIT SHADOW_RISK_RETAIN_LIMIT SHADOW_RISK_TAGS

jq -s -c --arg risk_tags "${SHADOW_RISK_TAGS}" \
    --argjson baseline_limit "${SHADOW_BASELINE_LIMIT}" \
    --argjson risk_retain_limit "${SHADOW_RISK_RETAIN_LIMIT}" '
  def parse_risk_tags:
    ($risk_tags | split(",") | map(gsub("^\\s+|\\s+$"; "")) | map(select(length > 0)));

  def record_task_id:
    if (.task_id // null) != null then (.task_id | tostring)
    elif (.record.task_id // null) != null then (.record.task_id | tostring)
    elif (.case_name // null) != null then ("shadow-" + (.case_name | tostring))
    else empty
    end;

  def record_ts:
    (.end_time // .timestamp // .record.end_time // .record.timestamp // "") | tostring;

  def record_tags:
    ((.tags // []) + (.k2_summary.tags // []) + (.k2_merge.k2_eval_tags // [])
     + (.ask_summary.tags // []))
    | map(tostring) | unique;

  def enrich($idx):
    . as $rec
    | {
        rec: $rec,
        idx: $idx,
        tid: (if ($rec | record_task_id) != null then ($rec | record_task_id)
              else ("line-" + ($idx | tostring)) end),
        ts: ($rec | record_ts),
        tags: ($rec | record_tags)
      };

  def dedup_newest($items):
    ($items
     | sort_by(.ts)
     | reduce .[] as $item (
         {};
         . + {($item.tid): $item}
       )
     | [.[]]
     | sort_by(.ts));

  (parse_risk_tags) as $rtags
  | [range(0; length) as $i | .[$i] | enrich($i)] as $enriched
  | ($enriched | map(select(.tags as $t | ($rtags | any(. as $r | ($t | index($r)) != null))))) as $risk_all
  | ($enriched | map(select(.tags as $t | ($rtags | all(. as $r | ($t | index($r)) == null))))) as $baseline_all
  | (dedup_newest($baseline_all)
     | if length > $baseline_limit then .[-$baseline_limit:] else . end) as $baseline_pool
  | (
      reduce $rtags[] as $tag (
        [];
        . + (
          dedup_newest([$risk_all[] | select(.tags | index($tag) != null)])
          | if length > $risk_retain_limit then .[-$risk_retain_limit:] else . end
        )
      )
    ) as $risk_raw
  | (reduce ($risk_raw | sort_by(.ts))[] as $item ({}; . + {($item.tid): $item}) | [.[]]) as $risk_pool
  | (reduce ($baseline_pool + $risk_pool | sort_by(.idx))[] as $item ({}; . + {($item.tid): $item}) | [.[]]) as $merged
  | {
      baseline_count: ($baseline_pool | length),
      risk_retained_count: ($risk_pool | length),
      total: ($merged | length),
      tag_source_counts: (
        reduce $rtags[] as $tag (
          {};
          . + {($tag): ([$risk_all[] | select(.tags | index($tag) != null)] | length)}
        )
      ),
      lines: ($merged | map(.rec))
    }
' "${SHADOW_BATCH}" > "${TMP_DIR}/result.json"

jq -c '.lines[]' "${TMP_DIR}/result.json" > "${SHADOW_SPOOL}"

BASELINE_COUNT="$(jq -r '.baseline_count' "${TMP_DIR}/result.json")"
RISK_COUNT="$(jq -r '.risk_retained_count' "${TMP_DIR}/result.json")"
TOTAL="$(jq -r '.total' "${TMP_DIR}/result.json")"
TAG_COUNTS="$(jq -c '.tag_source_counts' "${TMP_DIR}/result.json")"

echo "[SHADOW-PIPELINE] sampling: baseline=${BASELINE_COUNT} risk_retained=${RISK_COUNT} total=${TOTAL} tag_source_counts=${TAG_COUNTS}"
