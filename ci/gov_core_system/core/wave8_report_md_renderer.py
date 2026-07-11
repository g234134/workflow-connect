"""
Wave 8 Markdown renderer for Wave 7 ``report.json`` (REPORT-MD-RENDER).

Read-only formatting: does not recompute accepted_units, qa_status, overall_ok, or cost amounts.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

WAVE8_RENDERER_VERSION = "wave8_report_md_v0.1"

DISCLAIMER_NOT_INVOICE = "DISCLAIMER-NOT-INVOICE"
DISCLAIMER_M2_SKIPPED = "DISCLAIMER-M2-SKIPPED"
DISCLAIMER_CHARGEABLE_FALSE = "DISCLAIMER-CHARGEABLE-HINT-FALSE"
DISCLAIMER_CHARGEABLE_TRUE = "DISCLAIMER-CHARGEABLE-HINT-TRUE"
DISCLAIMER_CUSTOMER_ACK = "DISCLAIMER-CUSTOMER-ACK-NOT-RECORDED"

QA_STATUS_LABELS: dict[str, str] = {
    "pass": "通过",
    "pass_with_warnings": "通过（有警告）",
    "fail": "未通过",
}

REMEDIATION_LABELS: dict[str, str] = {
    "fix_manifest": "修正 manifest 数据后重新跑 QA",
    "rerun_pipeline": "重新执行清洗流水线",
    "review_sample": "人工复核抽样结果",
    "contact_support": "联系运营支持",
}

_REQUIRED_TOP_KEYS = ("schema_version", "job_id", "summary", "qa")
_REQUIRED_SUMMARY_KEYS = (
    "job_id",
    "sku",
    "accepted_units",
    "rejected_units",
    "total_rows",
    "billing_units",
    "qa_status",
)


def _normalize_audience(audience: str) -> str:
    text = str(audience or "external").strip().lower()
    if text in {"internal", "ops", "cs"}:
        return "internal"
    return "customer"


def _dash(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, str) and not value.strip():
        return "—"
    return str(value)


def _format_money(value: Any) -> str:
    if value is None:
        return "—"
    return str(value)


def _format_price(value: Any) -> str:
    if value is None:
        return "待财务表"
    return str(value)


def _qa_status_label(qa_status: str) -> str:
    return QA_STATUS_LABELS.get(str(qa_status), str(qa_status))


def _severity_badge(severity: str) -> str:
    sev = str(severity or "P0").upper()
    return f"**{sev}**"


def _layer_badge(layer: str) -> str:
    return str(layer or "M1")


def _remediation_label(hint: Any) -> str:
    if hint is None:
        return "—"
    key = str(hint).strip()
    return REMEDIATION_LABELS.get(key, key)


def _sort_failures(failures: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    layer_order = {"M1": 0, "M2": 1}

    def sort_key(item: Mapping[str, Any]) -> tuple[int, str, str]:
        layer = str(item.get("layer", "M1"))
        severity = str(item.get("severity", "P0")).upper()
        sev_order = {"P0": 0, "P1": 1, "P2": 2}.get(severity, 9)
        return (layer_order.get(layer, 9), sev_order, str(item.get("check_id", "")))

    return sorted(failures, key=sort_key)


def _validate_report(report: Mapping[str, Any]) -> str | None:
    for key in _REQUIRED_TOP_KEYS:
        if key not in report:
            return f"missing required report key: {key}"
    summary = report.get("summary")
    if not isinstance(summary, Mapping):
        return "report.summary must be an object"
    for key in _REQUIRED_SUMMARY_KEYS:
        if key not in summary:
            return f"missing required summary key: {key}"
    qa = report.get("qa")
    if not isinstance(qa, Mapping):
        return "report.qa must be an object"
    return None


def _resolve_generated_at(display_context: Mapping[str, Any] | None) -> str:
    if display_context and display_context.get("generated_at"):
        return str(display_context["generated_at"])
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _section_meta(
    report: Mapping[str, Any],
    *,
    generated_at: str,
    display_context: Mapping[str, Any] | None,
) -> list[str]:
    lines = [
        "## 报告元数据",
        "",
        "| 字段 | 值 |",
        "| --- | --- |",
        f"| schema_version | `{report.get('schema_version', '—')}` |",
        f"| job_id | `{report.get('job_id', '—')}` |",
        f"| rendered_at | `{generated_at}` |",
        f"| renderer | `{WAVE8_RENDERER_VERSION}` |",
    ]
    if display_context:
        client_ref = display_context.get("client_ref")
        if client_ref:
            lines.append(f"| client_ref | `{client_ref}` |")
    lines.append("")
    return lines


def _section_executive_summary(
    report: Mapping[str, Any],
    *,
    display_context: Mapping[str, Any] | None,
    audience: str,
) -> list[str]:
    summary = report["summary"]
    qa = report["qa"]
    qa_status = str(summary.get("qa_status", "—"))
    overall_ok = qa.get("overall_ok")

    lines = [
        "## 执行摘要",
        "",
        f"- **QA 结论（qa_status）**：{_qa_status_label(qa_status)} (`{qa_status}`)",
        f"- **overall_ok**：{'是' if overall_ok else '否'}",
        f"- **SKU**：`{summary.get('sku', '—')}`",
        f"- **accepted_units**：{summary.get('accepted_units', '—')}",
        f"- **billing_units**：U={summary.get('billing_units', {}).get('U', '—')}, "
        f"L={summary.get('billing_units', {}).get('L', '—')}",
        "",
    ]

    sample = qa.get("sample_validation")
    if isinstance(sample, Mapping) and sample.get("status") == "skipped":
        lines.extend(
            [
                "> **M2 说明**：本版未执行 M2 抽样 QA（sample validation skipped）；"
                "下方 `overall_ok` 主要反映 M1 清单完整性结论。",
                "",
            ]
        )

    if display_context:
        completion_variant = display_context.get("completion_variant")
        if completion_variant:
            lines.extend(
                [
                    "### 作业完成形态",
                    "",
                    f"- **completion_variant**：`{completion_variant}`",
                ]
            )
            if completion_variant == "completed_with_failures":
                lines.append(
                    "- 流水线已结束，部分输入行未纳入交付；"
                    "此形态与 `qa_status=pass` 不同层，请结合 §3–§5 一并阅读。"
                )
            run_status = display_context.get("run_status")
            if run_status and audience == "internal":
                lines.append(f"- **run_status**（lifecycle）：`{run_status}`")
            lines.append("")

    return lines


def _section_volume(report: Mapping[str, Any]) -> list[str]:
    summary = report["summary"]
    billing = summary.get("billing_units") or {}
    return [
        "## 处理量与计费单位",
        "",
        "| 指标 | 值 |",
        "| --- | --- |",
        f"| accepted_units | {summary.get('accepted_units', '—')} |",
        f"| rejected_units | {summary.get('rejected_units', '—')} |",
        f"| total_rows | {summary.get('total_rows', '—')} |",
        f"| billing_units.U | {billing.get('U', '—')} |",
        f"| billing_units.L | {billing.get('L', '—')} |",
        "",
    ]


def _section_qa_m1(report: Mapping[str, Any]) -> list[str]:
    qa = report["qa"]
    integrity = qa.get("manifest_integrity") or {}
    ok = integrity.get("ok")
    badge = "✅ 通过" if ok else "❌ 未通过"
    return [
        "## 清单完整性（M1）",
        "",
        f"**结论**：{badge}",
        "",
        "| 指标 | 值 |",
        "| --- | --- |",
        f"| ok | {ok} |",
        f"| checked_rows | {integrity.get('checked_rows', '—')} |",
        f"| failed_rows | {integrity.get('failed_rows', '—')} |",
        f"| failed_checks | {integrity.get('failed_checks', '—')} |",
        "",
    ]


def _section_qa_m2(report: Mapping[str, Any]) -> list[str]:
    qa = report["qa"]
    sample = qa.get("sample_validation")
    if not isinstance(sample, Mapping):
        sample = {}

    status = str(sample.get("status", "unknown"))
    lines = [
        "## 抽样校验（M2）",
        "",
    ]

    if status == "skipped":
        reason = sample.get("reason") or "M2 sample validation not executed in this release."
        lines.extend(
            [
                "> **本版未执行 M2 抽样 QA**（`sample_validation.status=skipped`）。",
                "> This release did **not** run M2 sample QA; the result must **not** be read as a pass.",
                "",
                f"- **status**：`skipped`",
                f"- **reason**：{reason}",
                f"- **sample_validation.ok**：{sample.get('ok', '—')}（skipped 时不代表抽样通过）",
                "",
                f"<!-- {DISCLAIMER_M2_SKIPPED} -->",
                "",
            ]
        )
        return lines

    ok = sample.get("ok")
    badge = "✅ 通过" if ok else "❌ 未通过"
    lines.extend(
        [
            f"**结论**：{badge}",
            "",
            "| 指标 | 值 |",
            "| --- | --- |",
            f"| status | `{status}` |",
            f"| ok | {ok} |",
            f"| sample_size | {sample.get('sample_size', '—')} |",
            f"| failed_checks | {sample.get('failed_checks', '—')} |",
            "",
        ]
    )
    if ok is False:
        lines.extend(
            [
                "> **警告**：M2 抽样校验未通过，请结合 §5 质量问题明细处理。",
                "",
            ]
        )
    return lines


def _section_qa_failures(
    report: Mapping[str, Any],
    *,
    audience: str,
) -> list[str]:
    qa = report["qa"]
    raw_failures = qa.get("failures")
    if not isinstance(raw_failures, Sequence) or isinstance(raw_failures, (str, bytes)):
        failures: list[Mapping[str, Any]] = []
    else:
        failures = [item for item in raw_failures if isinstance(item, Mapping)]

    lines = ["## 质量问题明细", ""]

    if not failures:
        lines.extend(["无 recorded QA failures。", ""])
        return lines

    sorted_failures = _sort_failures(failures)
    if audience == "internal":
        lines.extend(
            [
                "| layer | severity | check_id | file_id | message | remediation_hint |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for item in sorted_failures:
            lines.append(
                "| {layer} | {severity} | `{check_id}` | {file_id} | {message} | {hint} |".format(
                    layer=_layer_badge(str(item.get("layer", "M1"))),
                    severity=_severity_badge(str(item.get("severity", "P0"))),
                    check_id=_dash(item.get("check_id")),
                    file_id=_dash(item.get("file_id")),
                    message=_dash(item.get("message")),
                    hint=_remediation_label(item.get("remediation_hint")),
                )
            )
    else:
        lines.extend(
            [
                "| layer | severity | check_id | message |",
                "| --- | --- | --- | --- |",
            ]
        )
        for item in sorted_failures:
            lines.append(
                "| {layer} | {severity} | `{check_id}` | {message} |".format(
                    layer=_layer_badge(str(item.get("layer", "M1"))),
                    severity=_severity_badge(str(item.get("severity", "P0"))),
                    check_id=_dash(item.get("check_id")),
                    message=_dash(item.get("message")),
                )
            )
    lines.append("")
    return lines


def _section_cost_skeleton(report: Mapping[str, Any]) -> list[str]:
    summary = report["summary"]
    cost = summary.get("cost")
    if not isinstance(cost, Mapping):
        cost = {}
    chargeable_hint = summary.get("chargeable_hint")
    if chargeable_hint is None:
        chargeable_hint = cost.get("chargeable_hint")

    lines = [
        "## 费用结构（预估 · 未开票）",
        "",
        "> 本节为 R2 cost skeleton 展示，**非发票**；金额未填时仅为结构预留。",
        f"> <!-- {DISCLAIMER_NOT_INVOICE} -->",
        "",
        f"- **currency**：{_dash(cost.get('currency'))}",
        f"- **billing_table_version**：{_dash(cost.get('billing_table_version'))}",
        f"- **chargeable_hint**：{chargeable_hint}",
        "",
    ]

    line_items = cost.get("line_items")
    if isinstance(line_items, Sequence) and not isinstance(line_items, (str, bytes)):
        lines.extend(
            [
                "| SKU | unit | quantity | unit_price | amount | formula_ref |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for item in line_items:
            if not isinstance(item, Mapping):
                continue
            lines.append(
                "| {sku} | {unit} | {qty} | {price} | {amount} | `{formula}` |".format(
                    sku=_dash(item.get("sku")),
                    unit=_dash(item.get("unit")),
                    qty=_dash(item.get("quantity")),
                    price=_format_price(item.get("unit_price")),
                    amount=_format_price(item.get("amount")),
                    formula=_dash(item.get("formula_ref")),
                )
            )
        lines.append("")

    lines.extend(
        [
            "| 汇总项 | 值 |",
            "| --- | --- |",
            f"| amount_basic | {_format_money(cost.get('amount_basic'))} |",
            f"| amount_enrich | {_format_money(cost.get('amount_enrich'))} |",
            f"| amount_total | {_format_money(cost.get('amount_total'))} |",
            f"| minimum_fee_adjustment | {_format_money(cost.get('minimum_fee_adjustment'))} |",
            "",
        ]
    )

    if chargeable_hint is False:
        lines.extend(
            [
                f"<!-- {DISCLAIMER_CHARGEABLE_FALSE} -->",
                "",
                "_牌价未配置或不可计费，非最终 Chargeable 裁定。_",
                "",
            ]
        )
    elif chargeable_hint is True:
        lines.extend(
            [
                f"<!-- {DISCLAIMER_CHARGEABLE_TRUE} -->",
                "",
                "_chargeable_hint=true 仅为提示；需 customer_ack 与 invoice 流程后方为正式收费。_",
                "",
            ]
        )

    return lines


def _resolve_artifact_refs(
    report: Mapping[str, Any],
    *,
    config: Mapping[str, Any] | None,
    display_context: Mapping[str, Any] | None,
) -> list[Mapping[str, Any]]:
    for source in (display_context, config, report):
        if not isinstance(source, Mapping):
            continue
        refs = source.get("artifact_refs")
        if isinstance(refs, Sequence) and not isinstance(refs, (str, bytes)):
            out: list[Mapping[str, Any]] = []
            for item in refs:
                if isinstance(item, Mapping) and item.get("ref"):
                    out.append(dict(item))
                elif isinstance(item, str) and item.startswith("w6://"):
                    out.append({"label": item.rsplit("/", 1)[-1], "ref": item})
            if out:
                return out

    job_id = report.get("job_id")
    if job_id:
        return [
            {"label": "report.json", "ref": f"w6://delivery/{job_id}/report"},
            {"label": "report.md", "ref": f"w6://delivery/{job_id}/report_md"},
            {"label": "manifest", "ref": f"w6://delivery/{job_id}/manifest"},
        ]
    return []


def _section_artifacts(
    report: Mapping[str, Any],
    *,
    config: Mapping[str, Any] | None,
    display_context: Mapping[str, Any] | None,
) -> list[str]:
    refs = _resolve_artifact_refs(report, config=config, display_context=display_context)
    lines = [
        "## 交付物索引",
        "",
        "逻辑引用（w6://）；非磁盘路径。",
        "",
    ]
    if not refs:
        lines.extend(["_无可用 artifact_refs；请由编排注入 display_context.artifact_refs。_", ""])
        return lines

    lines.extend(
        [
            "| 交付物 | w6 ref |",
            "| --- | --- |",
        ]
    )
    for item in refs:
        label = item.get("label") or item.get("kind") or "artifact"
        lines.append(f"| {label} | `{item.get('ref')}` |")
    lines.append("")
    return lines


def _section_disclaimers(report: Mapping[str, Any]) -> list[str]:
    summary = report["summary"]
    qa = report["qa"]
    qa_status = str(summary.get("qa_status", ""))
    sample = qa.get("sample_validation") if isinstance(qa.get("sample_validation"), Mapping) else {}

    lines = [
        "## 声明与下一步",
        "",
        f"<!-- {DISCLAIMER_NOT_INVOICE} -->",
        f"<!-- {DISCLAIMER_CUSTOMER_ACK} -->",
        "",
        "- 本 Markdown 由 `report.json` 只读渲染，不构成发票或正式计费承诺。",
        "- 客户确认（customer_ack）与开票状态未在本报告中记录或推断。",
        "",
    ]

    if sample.get("status") == "skipped":
        lines.append(
            "- M2 抽样 QA 未执行：请勿将本报告理解为已完成抽样验收。"
        )

    if qa_status == "fail":
        lines.append("- QA 未通过：请处理 §5 质量问题明细后再安排交付或计费讨论。")
    elif qa_status == "pass_with_warnings":
        lines.append("- QA 通过但有警告：请审阅 §5 中的 P1/P2 项。")
    else:
        lines.append("- QA 清单校验通过：可进入交付存档与后续 customer_ack / 财务流程。")

    lines.append("")
    return lines


def _section_appendix_internal(
    report: Mapping[str, Any],
    *,
    display_context: Mapping[str, Any] | None,
) -> list[str]:
    lines = [
        "## 内部附录",
        "",
        f"- **report.schema_version**：`{report.get('schema_version')}`",
        f"- **renderer**：`{WAVE8_RENDERER_VERSION}`",
    ]
    summary = report.get("summary") or {}
    lines.append(f"- **summary.qa_status (raw)**：`{summary.get('qa_status')}`")

    qa = report.get("qa") or {}
    integrity = qa.get("manifest_integrity") if isinstance(qa.get("manifest_integrity"), Mapping) else {}
    sample = qa.get("sample_validation") if isinstance(qa.get("sample_validation"), Mapping) else {}
    lines.extend(
        [
            f"- **qa.manifest_integrity.ok**：{integrity.get('ok')}",
            f"- **qa.sample_validation.status**：`{sample.get('status', '—')}`",
            f"- **qa.overall_ok**：{qa.get('overall_ok')}",
        ]
    )

    if display_context:
        lines.append("")
        lines.append("### display_context（非真相）")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(dict(display_context), ensure_ascii=False, indent=2))
        lines.append("```")

    lines.append("")
    return lines


def render_data_clean_report(
    report: Mapping[str, Any],
    *,
    config: Mapping[str, Any] | None = None,
    display_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Render ``report.json`` to Markdown.

    Returns ``{ok, markdown, message}``. On validation failure ``markdown`` is empty.
    """

    cfg = dict(config or {})
    audience = _normalize_audience(str(cfg.get("audience", "customer")))
    include_appendix = bool(cfg.get("include_appendix_internal", audience == "internal"))

    err = _validate_report(report)
    if err:
        return {"ok": False, "markdown": "", "message": err}

    generated_at = _resolve_generated_at(display_context)
    if cfg.get("generated_at"):
        generated_at = str(cfg["generated_at"])

    job_id = report.get("job_id", "unknown")
    title = f"# 数据清洗交付报告 · {job_id}"

    parts: list[str] = [title, ""]
    parts.extend(_section_meta(report, generated_at=generated_at, display_context=display_context))
    parts.extend(_section_executive_summary(report, display_context=display_context, audience=audience))
    parts.extend(_section_volume(report))
    parts.extend(_section_qa_m1(report))
    parts.extend(_section_qa_m2(report))
    parts.extend(_section_qa_failures(report, audience=audience))
    parts.extend(_section_cost_skeleton(report))
    parts.extend(_section_artifacts(report, config=cfg, display_context=display_context))
    parts.extend(_section_disclaimers(report))
    if include_appendix and audience == "internal":
        parts.extend(_section_appendix_internal(report, display_context=display_context))

    markdown = "\n".join(parts).rstrip() + "\n"
    return {"ok": True, "markdown": markdown, "message": "report_md_rendered"}


def render_report_md(
    report: dict,
    *,
    audience: str = "external",
    display_context: dict | None = None,
    config: dict | None = None,
) -> str:
    """
    Convenience wrapper returning Markdown text.

    ``audience`` accepts ``external`` / ``customer`` (customer view) or ``internal``.
    Raises ``ValueError`` when required report blocks are missing.
    """

    cfg = dict(config or {})
    cfg.setdefault("audience", audience)
    out = render_data_clean_report(report, config=cfg, display_context=display_context)
    if not out.get("ok"):
        raise ValueError(str(out.get("message") or "render failed"))
    return str(out["markdown"])


__all__ = [
    "DISCLAIMER_CHARGEABLE_FALSE",
    "DISCLAIMER_CHARGEABLE_TRUE",
    "DISCLAIMER_CUSTOMER_ACK",
    "DISCLAIMER_M2_SKIPPED",
    "DISCLAIMER_NOT_INVOICE",
    "QA_STATUS_LABELS",
    "WAVE8_RENDERER_VERSION",
    "render_data_clean_report",
    "render_report_md",
]
