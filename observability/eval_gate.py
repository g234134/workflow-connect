"""
Rule-based evaluation gate (v0.1) for M-line / ibridge records.

Maps task metrics to pass / needs-review tags without LLM-as-judge or Langfuse SDK.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Final

from contract.constants import MAX_TOTAL_TOKEN_BUDGET

# ── 模組級 logger（依 STYLE.md §9 Logging 慣例） ──
logger = logging.getLogger(__name__)

EVAL_GATE_VERSION: Final[str] = "0.2"

# 80% of MAX_TOTAL_TOKEN_BUDGET（128,000 × 0.8 = 102,400）
CONTEXT_HEAVY_RATIO: Final[float] = 0.8
CONTEXT_HEAVY_TOKEN_THRESHOLD: Final[int] = int(MAX_TOTAL_TOKEN_BUDGET * CONTEXT_HEAVY_RATIO)

HIGH_RETRY_THRESHOLD: Final[int] = 2
MANY_HANDOFFS_THRESHOLD: Final[int] = 3
TRACE_COMPLETENESS_THRESHOLD: Final[float] = 0.8

# 基礎設施風險錯誤類型：context_overflow（上下文溢出）或 timeout（逾時）
INFRA_RISK_ERROR_TYPES: Final[frozenset[str]] = frozenset({"context_overflow", "timeout"})

# 必填欄位定義：(欄位名稱, 預期型別)
_REQUIRED_FIELDS: Final[tuple[tuple[str, type], ...]] = (
    ("success", bool),
    ("retry_count", int),
    ("handoff_count", int),
)


def _collect_schema_issues(record: dict[str, Any]) -> list[str] | None:
    """檢查 record 中必填欄位是否存在且型別正確。

    遍歷 _REQUIRED_FIELDS，逐一檢查欄位存在性與型別。
    若所有欄位皆合規，回傳 None；否則回傳人類可讀的缺失原因列表。

    Args:
        record: 待驗證的 task record dict。

    Returns:
        若無問題回傳 None；否則回傳 list[str]，每個元素為缺失或型別錯誤的描述。
        例如：["missing required field: retry_count", "invalid field type: handoff_count must be int"]
    """
    issues: list[str] = []
    for field, expected_type in _REQUIRED_FIELDS:
        if field not in record:
            issues.append(f"missing required field: {field}")
        elif not isinstance(record[field], expected_type):
            issues.append(f"invalid field type: {field} must be {expected_type.__name__}")
    return issues if issues else None


def _int_field(record: dict[str, Any], key: str, default: int = 0) -> int:
    """從 record 中安全取出整數欄位。

    若欄位不存在或無法轉為 int，回傳 default 值（0）。
    假設上游已盡力提供正確型別；此函數為防禦性 fallback。

    Args:
        record: task record dict。
        key: 頂層欄位名稱（例如 "retry_count"、"handoff_count"）。
        default: 欄位缺失或轉換失敗時的回退值。

    Returns:
        整數值。
    """
    raw = record.get(key, default)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _float_field(record: dict[str, Any], path: tuple[str, ...], default: float = 1.0) -> float:
    """從 record 中安全取出嵌套浮點數欄位。

    沿 path 逐層走訪 dict；若中途遇到非 dict 節點、鍵不存在
    或最終值無法轉為 float，回傳 default 值。
    default=1.0 的設計意圖是「預設樂觀」——若無法讀取 trace_completeness.score，
    視為完整性滿分，不觸發 observability_gap 規則。

    Args:
        record: task record dict。
        path: 嵌套鍵路徑 tuple，例如 ("trace_completeness", "score")。
        default: 欄位缺失或轉換失敗時的回退值（預設 1.0）。

    Returns:
        浮點數值。
    """
    node: Any = record
    for part in path:
        if not isinstance(node, dict):
            return default
        node = node.get(part)
    try:
        return float(node)
    except (TypeError, ValueError):
        return default


def _total_context_tokens(record: dict[str, Any]) -> int:
    """從 record 中萃取 context_token_usage.total_tokens。

    假設 record 中 context_token_usage 為 dict 且含 total_tokens 鍵；
    若結構不符預期或值無法轉為 int，回傳 0（靜默 fallback）。
    此函數與 eval_exporter.py 中的 _context_tokens_total 邏輯相同（見 DEBT_LOG D-005）。

    Args:
        record: task record dict。

    Returns:
        context_token_usage.total_tokens 的整數值，或 0。
    """
    usage = record.get("context_token_usage")
    if not isinstance(usage, dict):
        return 0
    raw = usage.get("total_tokens", 0)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def _error_type(record: dict[str, Any]) -> str | None:
    """從 record 中萃取 error_type 欄位。

    若 error_type 為 None（即無錯誤），回傳 None；
    否則強制轉為字串回傳。

    Args:
        record: task record dict。

    Returns:
        錯誤類型字串（例如 "context_overflow"），或 None。
    """
    raw = record.get("error_type")
    if raw is None:
        return None
    return str(raw)


# 規則函數型別別名：接收 record dict，回傳 (tag, reason) 或 None（不觸發）
RuleFn = Callable[[dict[str, Any]], tuple[str, str] | None]


# ── 五條核心規則 ──
#
# 每條規則函數簽章統一：_rule_<name>(record) → (tag, reason) | None。
# - 回傳 tuple：規則觸發，tag 為機器可讀標籤，reason 為人類可讀原因。
# - 回傳 None：規則未觸發。
# 所有規則獨立執行，無彼此依賴。


def _rule_high_retry(record: dict[str, Any]) -> tuple[str, str] | None:
    """規則：高重試次數（high_retry）。

    觸發條件：retry_count >= HIGH_RETRY_THRESHOLD（2）。
    依賴欄位：record["retry_count"]（頂層必填，預設值 0）。
    意圖：標記頻繁重試的 task，可能暗示上游不穩定或資源競爭。

    Args:
        record: task record dict。

    Returns:
        ("high_retry", "retry_count=N >= 2") 或 None。
    """
    count = _int_field(record, "retry_count")
    if count >= HIGH_RETRY_THRESHOLD:
        return (
            "high_retry",
            f"retry_count={count} >= {HIGH_RETRY_THRESHOLD}",
        )
    return None


def _rule_context_heavy(record: dict[str, Any]) -> tuple[str, str] | None:
    """規則：上下文用量過重（context_heavy）。

    觸發條件：context_token_usage.total_tokens > CONTEXT_HEAVY_TOKEN_THRESHOLD（102,400）。
    依賴欄位：record["context_token_usage"]["total_tokens"]（雙層嵌套，非必填 —
              若結構不符預期，_total_context_tokens 靜默回傳 0，不觸發規則）。
    意圖：標記接近 token 預算上限（80% of 128K）的 task，可能面臨截斷風險。
    注意：比較運算子為 strict `>`，與其他規則的 non-strict `>=` 不一致（見 DEBT_LOG D-004）。

    Args:
        record: task record dict。

    Returns:
        ("context_heavy", "context_token_usage.total_tokens=N > 80% of budget (102400)") 或 None。
    """
    total = _total_context_tokens(record)
    if total > CONTEXT_HEAVY_TOKEN_THRESHOLD:
        return (
            "context_heavy",
            (
                f"context_token_usage.total_tokens={total} > "
                f"{int(CONTEXT_HEAVY_RATIO * 100)}% of budget ({CONTEXT_HEAVY_TOKEN_THRESHOLD})"
            ),
        )
    return None


def _rule_many_handoffs(record: dict[str, Any]) -> tuple[str, str] | None:
    """規則：多次交接（many_handoffs）。

    觸發條件：handoff_count >= MANY_HANDOFFS_THRESHOLD（3）。
    依賴欄位：record["handoff_count"]（頂層必填，預設值 0）。
    意圖：標記在 agent 之間多次交接的 task，可能暗示協調複雜度過高。

    Args:
        record: task record dict。

    Returns:
        ("many_handoffs", "handoff_count=N >= 3") 或 None。
    """
    count = _int_field(record, "handoff_count")
    if count >= MANY_HANDOFFS_THRESHOLD:
        return (
            "many_handoffs",
            f"handoff_count={count} >= {MANY_HANDOFFS_THRESHOLD}",
        )
    return None


def _rule_infra_risk(record: dict[str, Any]) -> tuple[str, str] | None:
    """規則：基礎設施風險（infra_risk）。

    觸發條件：error_type 為 "context_overflow" 或 "timeout"。
    依賴欄位：record["error_type"]（頂層可選，可為 None）。
    意圖：標記由基礎設施瓶頸（而非業務邏輯）導致的失敗。

    Args:
        record: task record dict。

    Returns:
        ("infra_risk", "error_type=<type>") 或 None。
    """
    err = _error_type(record)
    if err in INFRA_RISK_ERROR_TYPES:
        return ("infra_risk", f"error_type={err}")
    return None


def _rule_observability_gap(record: dict[str, Any]) -> tuple[str, str] | None:
    """規則：可觀測性缺口（observability_gap）。

    觸發條件：trace_completeness.score < TRACE_COMPLETENESS_THRESHOLD（0.8）。
    依賴欄位：record["trace_completeness"]["score"]（雙層嵌套，非必填 —
              若結構不符預期，_float_field 靜默回傳 1.0，不觸發規則）。
    意圖：標記 trace 覆蓋率不足的 task，可能暗示 logging / tracing 管線有缺口。

    Args:
        record: task record dict。

    Returns:
        ("observability_gap", "trace_completeness.score=N < 0.8") 或 None。
    """
    score = _float_field(record, ("trace_completeness", "score"), default=1.0)
    if score < TRACE_COMPLETENESS_THRESHOLD:
        return (
            "observability_gap",
            f"trace_completeness.score={score} < {TRACE_COMPLETENESS_THRESHOLD}",
        )
    return None


# 規則註冊表（tuple，不可變）
# 執行順序：依 tuple 內順序迭代執行，但目前無語意上的優先級依賴（規則彼此獨立）。
# 新增規則時需將 _rule_<name> 函數加至此 tuple（同步參見 DEBT_LOG D-008、PLAYBOOK P-009）。
_RULES: tuple[RuleFn, ...] = (
    _rule_high_retry,
    _rule_context_heavy,
    _rule_many_handoffs,
    _rule_infra_risk,
    _rule_observability_gap,
)


def evaluate_task_record(
    record: dict[str, Any] | Any,
    *,
    disabled_tags: frozenset[str] | None = None,
) -> dict[str, Any]:
    """
    Screen a single metrics_record or ibridge_record for human review.

    Args:
        record: the metrics/ibridge task record dict.
        disabled_tags: optional frozenset of tag names to skip (e.g. frozenset({"high_retry"})).
            Affects all rule-derived tags; malformed / invalid_record short-circuits
            are not affected by this parameter.

    Returns:
        pass: True when no review tags fire; False when any tag is present.
        tags: machine-readable labels (e.g. high_retry, context_heavy).
        reasons: short explanations aligned with fired tags.
        eval_gate_version: stable version string for downstream contract tracking.
    """
    logger.info("eval_gate v%s: evaluating task record", EVAL_GATE_VERSION)

    if not isinstance(record, dict):
        logger.warning("eval_gate: invalid record (not a dict)")
        return {
            "pass": False,
            "tags": ["invalid_record"],
            "reasons": ["record must be a dict"],
            "eval_gate_version": EVAL_GATE_VERSION,
        }

    schema_reasons = _collect_schema_issues(record)
    if schema_reasons:
        logger.warning("eval_gate: malformed record — %s", schema_reasons)
        return {
            "pass": False,
            "tags": ["malformed_record"],
            "reasons": schema_reasons,
            "eval_gate_version": EVAL_GATE_VERSION,
        }

    tags: list[str] = []
    reasons: list[str] = []
    disabled = disabled_tags or frozenset()

    for rule in _RULES:
        hit = rule(record)
        if hit is None:
            continue
        tag, reason = hit
        if tag in disabled:
            continue
        if tag not in tags:
            tags.append(tag)
            reasons.append(reason)

    if tags:
        logger.info("eval_gate: tags fired — %s", tags)
    else:
        logger.info("eval_gate: passed, no tags fired")

    return {
        "pass": len(tags) == 0,
        "tags": tags,
        "reasons": reasons,
        "eval_gate_version": EVAL_GATE_VERSION,
    }