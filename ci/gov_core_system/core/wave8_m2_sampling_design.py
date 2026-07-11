"""
Wave 8 M2 sampling design — pure deterministic SamplingPlan contract.

Implements R3 §G.2 / §G.2.1 sample sizing and index selection only.
No filesystem I/O, manifest reads, or envelope validation.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import asdict, dataclass, field
from typing import Any

W6_BILLING_TABLE_VERSION_DEFAULT = "w6_billing_v0.1"

_CODE_EXTENSIONS = frozenset({".py", ".js", ".ts", ".rs", ".go"})
_MARKUP_EXTENSIONS = frozenset({".md", ".json", ".yaml", ".yml", ".toml"})

_G21_BUCKET_MINIMUMS: dict[str, int] = {
    "code": 3,
    "markup": 3,
    "other": 2,
}


@dataclass(frozen=True)
class SamplingPlan:
    """Deterministic M2 row selection plan over sorted ok-row positions (0..N-1)."""

    N: int
    sample_size: int
    seed: str
    row_indexes: tuple[int, ...]
    billing_table_version: str
    stride: float | None = None
    strata_coverage: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["row_indexes"] = list(self.row_indexes)
        return data


def compute_sample_size(n: int) -> int:
    """R3 §G.2: ``min(N, max(20, ceil(0.10 * N)))`` with full sample when ``N < 20``."""
    if n <= 0:
        return 0
    if n < 20:
        return n
    return min(n, max(20, math.ceil(0.10 * n)))


def derive_seed(*, billing_table_version: str, n: int) -> str:
    """Visible deterministic seed (execution layer may extend with ``job_id``)."""
    payload = f"{billing_table_version.strip()}|N={n}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def normalize_extension(ext: str) -> str:
    text = str(ext).strip().lower()
    if not text:
        return ""
    return text if text.startswith(".") else f".{text}"


def extension_bucket(ext: str) -> str:
    """R3 §G.2.1 strata bucket for an extension label."""
    normalized = normalize_extension(ext)
    if normalized in _CODE_EXTENSIONS:
        return "code"
    if normalized in _MARKUP_EXTENSIONS:
        return "markup"
    return "other"


def _validate_per_extension_counts(n: int, per_extension_counts: dict[str, int] | None) -> None:
    if per_extension_counts is None:
        return
    if n < 0:
        raise ValueError(f"N must be non-negative, got {n}")
    for ext, count in per_extension_counts.items():
        if not isinstance(count, int) or count < 0:
            raise ValueError(f"per_extension_counts[{ext!r}] must be a non-negative int, got {count!r}")
    total = sum(per_extension_counts.values())
    if total != n:
        raise ValueError(
            f"sum(per_extension_counts.values())={total} must equal N={n}"
        )


def _build_extension_labels(
    n: int, per_extension_counts: dict[str, int] | None
) -> list[str] | None:
    if per_extension_counts is None or n == 0:
        return None
    labels: list[str] = []
    for ext in sorted(per_extension_counts.keys()):
        labels.extend([ext] * per_extension_counts[ext])
    if len(labels) != n:
        raise ValueError(f"extension label expansion length {len(labels)} != N={n}")
    return labels


def _seed_offset(seed: str, n: int) -> int:
    if n <= 0:
        return 0
    return int(seed[:8], 16) % n


def _deterministic_pick(group: list[int], *, seed: str, salt: str) -> int:
    ordered = sorted(group)
    if len(ordered) == 1:
        return ordered[0]
    digest = hashlib.sha256(f"{seed}|{salt}".encode("utf-8")).hexdigest()
    return ordered[int(digest[:8], 16) % len(ordered)]


def _stride_candidates(n: int, sample_size: int, *, seed: str) -> list[int]:
    if sample_size <= 0 or n <= 0:
        return []
    if sample_size >= n:
        return list(range(n))
    offset = _seed_offset(seed, n)
    out: list[int] = []
    for i in range(sample_size):
        base = min(n - 1, int((i + 0.5) * n / sample_size))
        out.append((base + offset) % n)
    return out


def _dedupe_preserve_order(indexes: list[int]) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for idx in indexes:
        if idx not in seen:
            seen.add(idx)
            out.append(idx)
    return out


def _indices_for_extension(labels: list[str], ext: str) -> list[int]:
    return [i for i, label in enumerate(labels) if label == ext]


def _indices_for_bucket(labels: list[str], bucket: str) -> list[int]:
    return [i for i, label in enumerate(labels) if extension_bucket(label) == bucket]


def _apply_strata_minimums(
    selected: list[int],
    *,
    n: int,
    sample_size: int,
    seed: str,
    labels: list[str] | None,
    per_extension_counts: dict[str, int] | None,
) -> list[int]:
    if n <= 500 or sample_size <= 0:
        return selected

    chosen = list(selected)

    if per_extension_counts is not None and labels is not None:
        for ext in sorted(per_extension_counts.keys()):
            if per_extension_counts[ext] <= 0:
                continue
            group = _indices_for_extension(labels, ext)
            if not group:
                continue
            pick = _deterministic_pick(group, seed=seed, salt=f"ext:{ext}")
            if pick not in chosen:
                chosen.append(pick)

    if labels is not None:
        for bucket, minimum in _G21_BUCKET_MINIMUMS.items():
            group = _indices_for_bucket(labels, bucket)
            if not group:
                continue
            need = min(minimum, len(group), sample_size)
            already = [i for i in chosen if i in group]
            remaining = need - len(already)
            if remaining <= 0:
                continue
            pool = [i for i in group if i not in chosen]
            for j in range(remaining):
                if not pool:
                    break
                pick = _deterministic_pick(pool, seed=seed, salt=f"bucket:{bucket}:{j}")
                chosen.append(pick)
                pool = [i for i in pool if i != pick]

    return _dedupe_preserve_order(chosen)


def _fill_to_sample_size(
    selected: list[int],
    *,
    n: int,
    sample_size: int,
    seed: str,
    protected: list[int] | None = None,
) -> list[int]:
    protected_set = set(protected or [])
    chosen = _dedupe_preserve_order(selected)
    if len(chosen) >= sample_size:
        if not protected_set:
            return sorted(chosen)[:sample_size]
        must_keep = [i for i in chosen if i in protected_set]
        optional = [i for i in chosen if i not in protected_set]
        keep = sorted(must_keep)
        for idx in sorted(optional):
            if len(keep) >= sample_size:
                break
            keep.append(idx)
        return sorted(keep)[:sample_size]

    for idx in _stride_candidates(n, sample_size, seed=seed):
        if idx not in chosen:
            chosen.append(idx)
        if len(chosen) >= sample_size:
            break

    if len(chosen) < sample_size:
        for idx in range(n):
            if idx not in chosen:
                chosen.append(idx)
            if len(chosen) >= sample_size:
                break

    return _fill_to_sample_size(
        chosen,
        n=n,
        sample_size=sample_size,
        seed=seed,
        protected=protected,
    ) if len(chosen) > sample_size else sorted(chosen)


def _compute_strata_coverage(
    row_indexes: list[int], labels: list[str] | None
) -> dict[str, int]:
    if labels is None:
        return {}
    coverage: dict[str, int] = {}
    for idx in row_indexes:
        ext = labels[idx]
        coverage[ext] = coverage.get(ext, 0) + 1
    return dict(sorted(coverage.items()))


def build_sampling_plan(
    n: int,
    *,
    per_extension_counts: dict[str, int] | None = None,
    billing_table_version: str = W6_BILLING_TABLE_VERSION_DEFAULT,
) -> SamplingPlan:
    """
    Build a deterministic M2 sampling plan over ``N`` ok-row positions.

    ``row_indexes`` are 0-based positions in the ok-row ordering (execution sorts
    by ``content_sha256`` before mapping indexes to manifest rows).
    """
    if n < 0:
        raise ValueError(f"N must be non-negative, got {n}")

    version = (billing_table_version or W6_BILLING_TABLE_VERSION_DEFAULT).strip()
    _validate_per_extension_counts(n, per_extension_counts)

    sample_size = compute_sample_size(n)
    seed = derive_seed(billing_table_version=version, n=n)
    labels = _build_extension_labels(n, per_extension_counts)

    if sample_size == 0:
        return SamplingPlan(
            N=n,
            sample_size=0,
            seed=seed,
            row_indexes=(),
            billing_table_version=version,
            stride=None,
            strata_coverage={},
        )

    stride = n / sample_size if sample_size > 0 else None
    base = _stride_candidates(n, sample_size, seed=seed)
    merged = _apply_strata_minimums(
        base,
        n=n,
        sample_size=sample_size,
        seed=seed,
        labels=labels,
        per_extension_counts=per_extension_counts,
    )
    protected = merged if n > 500 else None
    row_indexes = _fill_to_sample_size(
        merged,
        n=n,
        sample_size=sample_size,
        seed=seed,
        protected=protected,
    )

    return SamplingPlan(
        N=n,
        sample_size=sample_size,
        seed=seed,
        row_indexes=tuple(row_indexes),
        billing_table_version=version,
        stride=stride,
        strata_coverage=_compute_strata_coverage(row_indexes, labels),
    )
