"""Phase% apply runner — estimate / verify / apply Dashboard SSOT deltas.

Aligns with:
  - docs/phase-progress-impact-protocol-v1.md（提案 Δ vs 寫入 % · §8–§9）
  - docs/WAVE_PROGRESS_DASHBOARD.md（Phase% 唯一數字 SSOT）
  - docs/progress-dashboard-append-protocol-v1.md（僅 W-PROG／Governance 可寫數字格）

Rhythm（用戶權威）:
  1. estimate — 開工／接戰預估 proposed_delta（不寫 Dashboard %）
  2. verify  — 驗收／Review 通過後升格為可 apply 候選
  3. apply   — 僅 W-PROG／Governance + --authorize 寫入 Dashboard

Default is dry-run / propose-only. Writing requires:
  lifecycle=verified + --authorize + ticket apply_phase_pct: true + 已授權寫入

Examples:
  python 04_Workflows/_phase_pct_apply.py estimate --ticket-id TICKET --pretty
  python 04_Workflows/_phase_pct_apply.py estimate --ticket-id TICKET --write-back --pretty
  python 04_Workflows/_phase_pct_apply.py verify --ticket-id TICKET --checks-ok --write-back --pretty
  python 04_Workflows/_phase_pct_apply.py plan --delta P8.5=+2 --pretty
  python 04_Workflows/_phase_pct_apply.py apply --ticket-id W-PROG-... --authorize --pretty
  python 04_Workflows/_phase_pct_apply.py self-test --pretty
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_REL = "docs/WAVE_PROGRESS_DASHBOARD.md"
TICKETS_REL = "04_Workflows/tickets"
PROTOCOL_REL = "docs/phase-progress-impact-protocol-v1.md"

# Canonical Phase ids (Gauge order)
PHASE_IDS: list[str] = [
    "P1",
    "P2",
    "P3",
    "P3.5",
    "P4",
    "P5",
    "P6",
    "P7",
    "P7.5",
    "P8",
    "P8.5",
    "P8.6",
    "P8.7",
    "P8.8",
    "P8.9",
    "P9",
    "P10",
    "P10.5",
]

PHASE_TITLES: dict[str, str] = {
    "P1": "治理層",
    "P2": "知識層 / Index",
    "P3": "可觀測性 / Trace",
    "P3.5": "成本 / 模型治理",
    "P4": "多智能體協作",
    "P5": "Dashboard / 离线健康度",
    "P6": "测试 / 回归 gate",
    "P7": "自動客戶溝通",
    "P7.5": "Intake Gate",
    "P8": "商業化交付 / Operator",
    "P8.5": "Browser / Computer Use",
    "P8.9": "Outbox / Feedback",
    "P9": "訂單 / 金流閉環",
    "P10": "95% 全自動化閉環",
    "P10.5": "學習 / Skill 蒸餾",
    "P8.6": "Tool Catalog SSOT",
    "P8.7": "Selector 推荐契约",
    "P8.8": "Executor / Sandbox",
}

DEFAULT_MAX_DELTA = 15
DEFAULT_MAX_ABS = 100

# --- heuristic v0.1（尚書省 2026-07-13 確認採納 · approved／定稿）---
HEURISTIC_VERSION = "v0.1"
HEURISTIC_STATUS = "approved"  # 定稿
HEURISTIC_NOTE = (
    "heuristic v0.1 · approved／定稿（尚書省 2026-07-13 確認採納）· "
    "對齊歷史慣例（工具票 +0 · 常規貢獻 +1/+2 · 大證據跳 +5/+8）"
)

# impact_size → base Δ（percentage points）
SIZE_BASE_DELTA: dict[str, int] = {
    "micro": 0,  # tool / docs-only / runner plumbing
    "small": 1,
    "medium": 2,  # default when phase_targets present
    "large": 5,
    "xl": 8,  # rare milestone（歷史：P8.5 授權區間保守端 +8）
}

# evidence_gate → cap（blocked → 0）
GATE_CAP: dict[str, int] = {
    "blocked": 0,
    "l-local": 2,
    "ci-advisory": 5,
    "l-local+ci-advisory": 5,
    "ga-remote": 8,
}

LIFECYCLE_NONE = "none"
LIFECYCLE_ESTIMATED = "estimated"
LIFECYCLE_VERIFIED = "verified"
LIFECYCLE_APPLIED = "applied"

GAUGE_HEADER = "### Phase Completion Gauge"
SINGLE_LINE_HEADER = "**单行索引"
PROGRESS_BAR_HEADER = "### Phase 完成度进度条"
MAIN_TABLE_HEADER = "## Phase 完成度表（Toolchain + 跨轨 · SSOT）"
ESTIMATE_SECTION = "## Phase Δ estimate"
VERIFY_SECTION = "## Phase Δ verify"


@dataclass
class PhaseRow:
    phase: str
    title: str
    completion: int
    prev: int
    delta: int


def _ok(message: str, **extra: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"ok": True, "message": message}
    out.update(extra)
    return out


def _fail(message: str, **extra: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"ok": False, "message": message}
    out.update(extra)
    return out


def _dashboard_path(root: Path) -> Path:
    return root / DASHBOARD_REL


def _ticket_path(root: Path, ticket_id: str) -> Path:
    tid = ticket_id.strip()
    if tid.endswith("_state.md"):
        tid = tid[: -len("_state.md")]
    if tid.endswith(".md"):
        tid = tid[: -len(".md")]
    return root / TICKETS_REL / f"{tid}_state.md"


def _normalize_phase(raw: str) -> str | None:
    s = raw.strip().upper().replace("PHASE", "P").replace(" ", "")
    if not s.startswith("P"):
        s = "P" + s
    # P08.5 → P8.5
    m = re.match(r"^P0*(\d+(?:\.\d+)?)$", s)
    if not m:
        return None
    num = m.group(1)
    # strip leading zeros on integer part only
    if "." in num:
        a, b = num.split(".", 1)
        num = f"{int(a)}.{b}"
    else:
        num = str(int(num))
    cand = f"P{num}"
    return cand if cand in PHASE_IDS else None


def _parse_delta_token(token: str) -> tuple[str, int] | None:
    """Accept 'P8.5=+2', 'P8.5+2', 'P4: +2'."""
    t = token.strip()
    m = re.match(
        r"^(P?\d+(?:\.\d+)?)\s*(?:=|:)?\s*([+-]?\d+%?)$",
        t,
        re.I,
    )
    if not m:
        return None
    phase = _normalize_phase(m.group(1))
    if not phase:
        return None
    delta_s = m.group(2).rstrip("%")
    return phase, int(delta_s)


def parse_delta_args(items: list[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for item in items:
        # allow "P8.5=+2,P9=+2"
        for part in re.split(r"[,;·|]+", item):
            part = part.strip()
            if not part:
                continue
            parsed = _parse_delta_token(part)
            if not parsed:
                raise ValueError(f"invalid --delta token: {part!r}")
            phase, delta = parsed
            out[phase] = out.get(phase, 0) + delta
    return out


def parse_proposed_delta_pct(text: str, phase_targets: list[str] | None = None) -> dict[str, int]:
    """Parse FRAME proposed_delta_pct strings into phase→delta."""
    text = (text or "").strip()
    if not text or text.lower() in {"n/a", "na", "0", "+0"}:
        return {}
    out: dict[str, int] = {}
    # Prefer explicit "P8.5 +2" / "P8.5=+2"
    for m in re.finditer(
        r"(P\d+(?:\.\d+)?)\s*(?:=|:)?\s*([+-]\d+)\s*%?",
        text,
        re.I,
    ):
        phase = _normalize_phase(m.group(1))
        if phase:
            out[phase] = out.get(phase, 0) + int(m.group(2))
    if out:
        return out
    # Bare "+8" with single phase_targets
    m = re.fullmatch(r"([+-]?\d+)\s*%?", text)
    if m and phase_targets and len(phase_targets) == 1:
        phase = _normalize_phase(phase_targets[0])
        if phase:
            return {phase: int(m.group(1))}
    return out


def parse_ticket_frame(text: str) -> dict[str, Any]:
    """Extract Phase-impact FRAME fields from ticket STATE markdown."""
    apply_m = re.search(
        r"apply_phase_pct\s*:\s*(true|false)",
        text,
        re.I,
    )
    apply_phase_pct = bool(apply_m and apply_m.group(1).lower() == "true")

    targets: list[str] = []
    tm = re.search(r"phase_targets\s*:\s*\[([^\]]*)\]", text, re.I)
    if tm:
        for raw in re.split(r"[,|]", tm.group(1)):
            p = _normalize_phase(raw.strip().strip("'\""))
            if p:
                targets.append(p)
    if not targets:
        for m in re.finditer(
            r"phase_targets\s*:\s*\n((?:\s*-\s*.+\n?)+)",
            text,
            re.I,
        ):
            for line in m.group(1).splitlines():
                lm = re.match(r"\s*-\s*[`'\"]?(P?\d+(?:\.\d+)?)[`'\"]?", line, re.I)
                if lm:
                    p = _normalize_phase(lm.group(1))
                    if p:
                        targets.append(p)

    baseline = None
    bm = re.search(r"baseline_pct\s*:\s*[\"']?([^\n\"']+)", text, re.I)
    if bm:
        baseline = bm.group(1).strip()

    proposed_raw = None
    pm = re.search(r"proposed_delta_pct\s*:\s*[\"']?([^\n\"']+)", text, re.I)
    if pm:
        proposed_raw = pm.group(1).strip()

    evidence_gate = None
    em = re.search(r"evidence_gate\s*:\s*[\"']?([^\n\"']+)", text, re.I)
    if em:
        evidence_gate = em.group(1).strip()

    impact_size = None
    sm = re.search(
        r"(?:impact_size|ticket_size|impact_class)\s*:\s*[\"']?(micro|small|medium|large|xl|docs|tool|build|milestone)[\"']?",
        text,
        re.I,
    )
    if sm:
        impact_size = sm.group(1).lower()

    lifecycle = LIFECYCLE_NONE
    lm = re.search(
        r"phase_delta_lifecycle\s*:\s*[\"']?(none|estimated|verified|applied)[\"']?",
        text,
        re.I,
    )
    if lm:
        lifecycle = lm.group(1).lower()
    elif re.search(rf"{re.escape(VERIFY_SECTION)}[\s\S]*?lifecycle\s*:\s*verified", text, re.I):
        lifecycle = LIFECYCLE_VERIFIED
    elif re.search(rf"{re.escape(ESTIMATE_SECTION)}[\s\S]*?lifecycle\s*:\s*estimated", text, re.I):
        lifecycle = LIFECYCLE_ESTIMATED
    elif re.search(r"lifecycle\s*:\s*applied", text, re.I) and "Phase Δ" in text:
        lifecycle = LIFECYCLE_APPLIED

    authorized = bool(
        re.search(r"已授權寫入|已授权写入|\*\*已授權\*\*|授权写[入入]", text)
        or re.search(r"authorization\s*:\s*granted", text, re.I)
    )

    review_ok = bool(
        re.search(r"overall_status\s*[:=]\s*[`'\"]?done[`'\"]?", text, re.I)
        or re.search(r"verdict\s*[:=]\s*[`'\"]?accepted[`'\"]?", text, re.I)
        or re.search(r"C_REPORT[\s\S]{0,400}accepted", text, re.I)
        or re.search(r"review(?:er)?\s*[:=]\s*[`'\"]?(?:accepted|pass|ok)[`'\"]?", text, re.I)
    )

    deltas = parse_proposed_delta_pct(proposed_raw or "", targets)
    return {
        "apply_phase_pct": apply_phase_pct,
        "phase_targets": targets,
        "baseline_pct": baseline,
        "proposed_delta_pct": proposed_raw,
        "evidence_gate": evidence_gate,
        "impact_size": impact_size,
        "phase_delta_lifecycle": lifecycle,
        "authorized_marker": authorized,
        "review_ok_marker": review_ok,
        "deltas": deltas,
    }


def _normalize_impact_size(raw: str | None) -> str | None:
    if not raw:
        return None
    s = raw.strip().lower()
    aliases = {
        "docs": "micro",
        "doc": "micro",
        "tool": "micro",
        "tools": "micro",
        "build": "medium",
        "milestone": "xl",
    }
    s = aliases.get(s, s)
    return s if s in SIZE_BASE_DELTA else None


def infer_impact_size(text: str, frame: dict[str, Any]) -> tuple[str, str]:
    """Return (size, reason). Prefer explicit FRAME; else keyword heuristic."""
    explicit = _normalize_impact_size(frame.get("impact_size"))
    if explicit:
        return explicit, f"explicit impact_size={explicit}"

    low = text.lower()
    # micro: tooling / protocol / index-only
    micro_kw = (
        "apply runner",
        "self-test",
        "protocol",
        "index only",
        "docs-only",
        "doc/spec",
        "工具票",
        "不寫數字",
        "不写数字",
        "proposed_delta_pct: \"0",
        "proposed_delta_pct: 0",
        "proposed_delta_pct: \"+0",
    )
    if any(k in low for k in micro_kw) or "runner" in low and "phase%" in low:
        return "micro", "keyword→micro (tool/docs/runner)"

    if any(k in low for k in ("ga-remote", "milestone", "closure-scribe", "war_status")):
        return "xl", "keyword→xl (milestone/GA)"

    if any(k in low for k in ("large", "大證據", "大证据", "+8", "+5")):
        return "large", "keyword→large"

    if any(k in low for k in ("checklist", "onboarding", "cross-ref", "一句索引")):
        return "small", "keyword→small (doc/index)"

    if frame.get("phase_targets"):
        return "medium", "default medium (phase_targets present)"
    return "micro", "default micro (no phase_targets)"


def _normalize_gate(raw: str | None) -> str:
    if not raw:
        return "l-local"
    s = raw.strip().lower().replace(" ", "")
    s = s.replace("＋", "+")
    if "blocked" in s:
        return "blocked"
    if "ga-remote" in s or s == "ga":
        return "ga-remote"
    if "ci-advisory" in s and "l-local" in s:
        return "l-local+ci-advisory"
    if "ci-advisory" in s or "ci" == s:
        return "ci-advisory"
    if "l-local" in s or "local" in s:
        return "l-local"
    return "l-local"


def estimate_deltas_for_ticket(
    text: str,
    frame: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Auto-estimate proposed_delta map.

    Preference:
      1) explicit numeric proposed_delta_pct → source=explicit
      2) heuristic SIZE_BASE_DELTA × phase_targets, capped by evidence_gate
    """
    frame = frame or parse_ticket_frame(text)
    targets = list(frame.get("phase_targets") or [])
    explicit = dict(frame.get("deltas") or {})
    # Treat bare 0 / +0 as "no estimate yet" when we want auto — but keep if intentional zero
    if explicit:
        # If all zeros and proposed says tool/no-write, keep explicit zeros
        return {
            "ok": True,
            "source": "explicit",
            "heuristic": False,
            "heuristic_version": None,
            "heuristic_status": None,
            "impact_size": _normalize_impact_size(frame.get("impact_size")),
            "evidence_gate": frame.get("evidence_gate"),
            "deltas": explicit,
            "rationale": f"parsed proposed_delta_pct={frame.get('proposed_delta_pct')!r}",
            "note": "explicit FRAME delta preferred over heuristic",
        }

    size, size_reason = infer_impact_size(text, frame)
    base = SIZE_BASE_DELTA[size]
    gate = _normalize_gate(frame.get("evidence_gate"))
    cap = GATE_CAP.get(gate, 2)
    delta = min(base, cap)
    if gate == "blocked":
        delta = 0

    if not targets:
        return {
            "ok": True,
            "source": "heuristic",
            "heuristic": True,
            "heuristic_version": HEURISTIC_VERSION,
            "heuristic_status": HEURISTIC_STATUS,
            "impact_size": size,
            "evidence_gate": gate,
            "deltas": {},
            "rationale": f"{size_reason}; no phase_targets → empty deltas",
            "note": HEURISTIC_NOTE,
        }

    deltas = {p: delta for p in targets}
    return {
        "ok": True,
        "source": "heuristic",
        "heuristic": True,
        "heuristic_version": HEURISTIC_VERSION,
        "heuristic_status": HEURISTIC_STATUS,
        "impact_size": size,
        "evidence_gate": gate,
        "deltas": deltas,
        "rationale": (
            f"{size_reason}; base={base}; gate={gate} cap={cap} → Δ={delta} "
            f"for {', '.join(targets)}"
        ),
        "note": HEURISTIC_NOTE,
    }


def format_proposed_delta_pct(deltas: dict[str, int]) -> str:
    if not deltas:
        return "0"
    parts = []
    for phase in sorted(deltas.keys(), key=lambda x: PHASE_IDS.index(x) if x in PHASE_IDS else 99):
        parts.append(f"{phase} {deltas[phase]:+d}")
    return " · ".join(parts)


def _render_estimate_block(
    *,
    deltas: dict[str, int],
    est: dict[str, Any],
    baseline: str | None,
) -> str:
    lines = [
        ESTIMATE_SECTION + f" (auto · heuristic {est.get('heuristic_version') or 'n/a'})",
        "",
        f"- phase_delta_lifecycle: {LIFECYCLE_ESTIMATED}",
        f"- source: {est.get('source')}",
        f"- heuristic: {str(bool(est.get('heuristic'))).lower()}",
        f"- heuristic_version: {est.get('heuristic_version') or 'n/a'}",
        f"- heuristic_status: {est.get('heuristic_status') or 'n/a'}",
        f"- impact_size: {est.get('impact_size') or 'n/a'}",
        f"- evidence_gate: {est.get('evidence_gate') or 'n/a'}",
        f"- baseline_pct: {baseline or 'n/a'}",
        f"- proposed_delta_pct: \"{format_proposed_delta_pct(deltas)}\"",
        f"- rationale: {est.get('rationale')}",
        f"- note: {est.get('note') or HEURISTIC_NOTE}",
        "- non_claims: ≠ Dashboard write · ≠ Phase closure · 干活≠漲%",
        "",
    ]
    return "\n".join(lines)


def _render_verify_block(*, checks: dict[str, Any], deltas: dict[str, int]) -> str:
    lines = [
        VERIFY_SECTION,
        "",
        f"- phase_delta_lifecycle: {LIFECYCLE_VERIFIED}",
        f"- proposed_delta_pct: \"{format_proposed_delta_pct(deltas)}\"",
        f"- checks: {json.dumps(checks, ensure_ascii=False)}",
        "- write_candidate: true（仍須 apply_phase_pct=true + 已授權寫入 + --authorize）",
        "- non_claims: ≠ auto Dashboard write · verified ≠ applied",
        "",
    ]
    return "\n".join(lines)


def _upsert_lifecycle_and_delta(text: str, lifecycle: str, proposed: str) -> str:
    """Patch or insert FRAME fields for lifecycle + proposed_delta_pct."""
    if re.search(r"phase_delta_lifecycle\s*:", text, re.I):
        text = re.sub(
            r"(phase_delta_lifecycle\s*:\s*)[^\n]+",
            rf"\1{lifecycle}",
            text,
            count=1,
            flags=re.I,
        )
    else:
        # insert after apply_phase_pct if present
        if re.search(r"apply_phase_pct\s*:", text, re.I):
            text = re.sub(
                r"(apply_phase_pct\s*:\s*(?:true|false)[^\n]*\n)",
                rf"\1phase_delta_lifecycle: {lifecycle}\n",
                text,
                count=1,
                flags=re.I,
            )
        else:
            text = text.rstrip() + f"\n\nphase_delta_lifecycle: {lifecycle}\n"

    if re.search(r"proposed_delta_pct\s*:", text, re.I):
        text = re.sub(
            r"(proposed_delta_pct\s*:\s*)[^\n]+",
            rf'\1"{proposed}"',
            text,
            count=1,
            flags=re.I,
        )
    return text


def write_back_estimate(path: Path, text: str, est: dict[str, Any], frame: dict[str, Any]) -> str:
    deltas = est["deltas"]
    proposed = format_proposed_delta_pct(deltas)
    text2 = _upsert_lifecycle_and_delta(text, LIFECYCLE_ESTIMATED, proposed)
    block = _render_estimate_block(
        deltas=deltas,
        est=est,
        baseline=frame.get("baseline_pct"),
    )
    # replace existing estimate section or append
    if ESTIMATE_SECTION in text2:
        start = text2.find(ESTIMATE_SECTION)
        end = len(text2)
        for em in [VERIFY_SECTION, "\n## ", "\n---\n"]:
            idx = text2.find(em, start + 5)
            if idx >= 0:
                end = min(end, idx)
        text2 = text2[:start] + block + text2[end:]
    else:
        text2 = text2.rstrip() + "\n\n" + block
    path.write_text(text2, encoding="utf-8")
    return text2


def write_back_verify(
    path: Path,
    text: str,
    *,
    deltas: dict[str, int],
    checks: dict[str, Any],
) -> str:
    proposed = format_proposed_delta_pct(deltas)
    text2 = _upsert_lifecycle_and_delta(text, LIFECYCLE_VERIFIED, proposed)
    block = _render_verify_block(checks=checks, deltas=deltas)
    if VERIFY_SECTION in text2:
        start = text2.find(VERIFY_SECTION)
        end = len(text2)
        for em in ["\n## ", "\n---\n"]:
            idx = text2.find(em, start + 5)
            if idx >= 0:
                end = min(end, idx)
        text2 = text2[:start] + block + text2[end:]
    else:
        text2 = text2.rstrip() + "\n\n" + block
    path.write_text(text2, encoding="utf-8")
    return text2


def _baseline_from_dashboard(root: Path, targets: list[str]) -> str:
    try:
        rows = rows_to_map(read_gauge_rows(_dashboard_path(root).read_text(encoding="utf-8")))
        parts = []
        for p in targets:
            if p in rows:
                parts.append(f"{p}={rows[p].completion}%")
        if parts:
            return f"Dashboard SSOT · " + " · ".join(parts)
    except Exception:
        pass
    return "Dashboard SSOT (see WAVE_PROGRESS_DASHBOARD)"


def _extract_section(text: str, start_marker: str, end_markers: list[str]) -> tuple[int, int, str]:
    start = text.find(start_marker)
    if start < 0:
        raise ValueError(f"section not found: {start_marker}")
    end = len(text)
    for em in end_markers:
        idx = text.find(em, start + len(start_marker))
        if idx >= 0:
            end = min(end, idx)
    return start, end, text[start:end]


def read_gauge_rows(dashboard_text: str) -> list[PhaseRow]:
    _, _, section = _extract_section(
        dashboard_text,
        GAUGE_HEADER,
        [SINGLE_LINE_HEADER, PROGRESS_BAR_HEADER, "\n## "],
    )
    rows: list[PhaseRow] = []
    for line in section.splitlines():
        m = re.match(
            r"^\|\s*(P\d+(?:\.\d+)?)\s+([^|]+?)\s*\|\s*\*\*(\d+)%\*\*\s*\|\s*(\d+)%\s*\|\s*(.+?)\s*\|\s*$",
            line.strip(),
        )
        if not m:
            continue
        phase = _normalize_phase(m.group(1))
        if not phase:
            continue
        title = m.group(2).strip()
        completion = int(m.group(3))
        prev = int(m.group(4))
        delta_cell = m.group(5).strip()
        dm = re.search(r"([+-]?\d+)", delta_cell.replace("%", ""))
        delta = int(dm.group(1)) if dm else 0
        rows.append(
            PhaseRow(
                phase=phase,
                title=title,
                completion=completion,
                prev=prev,
                delta=delta,
            )
        )
    if not rows:
        raise ValueError("no Gauge rows parsed from Dashboard")
    return rows


def rows_to_map(rows: list[PhaseRow]) -> dict[str, PhaseRow]:
    return {r.phase: r for r in rows}


def plan_updates(
    current: dict[str, PhaseRow],
    deltas: dict[str, int],
    *,
    max_delta: int = DEFAULT_MAX_DELTA,
    max_abs: int = DEFAULT_MAX_ABS,
    allow_large_delta: bool = False,
) -> dict[str, Any]:
    if not deltas:
        return _fail("no deltas provided", updates=[], mode="plan")
    updates: list[dict[str, Any]] = []
    errors: list[str] = []
    for phase, delta in sorted(deltas.items(), key=lambda x: PHASE_IDS.index(x[0]) if x[0] in PHASE_IDS else 99):
        if phase not in current:
            errors.append(f"unknown phase in Dashboard Gauge: {phase}")
            continue
        if delta == 0:
            continue
        if not allow_large_delta and abs(delta) > max_delta:
            errors.append(
                f"{phase} delta {delta:+d} exceeds max_delta={max_delta} "
                "(pass --allow-large-delta to override)"
            )
            continue
        row = current[phase]
        new_pct = row.completion + delta
        if new_pct < 0 or new_pct > max_abs:
            errors.append(f"{phase} result {new_pct}% out of [0,{max_abs}]")
            continue
        updates.append(
            {
                "phase": phase,
                "title": row.title,
                "prev_completion": row.completion,
                "delta": delta,
                "new_completion": new_pct,
                "gauge_prev_was": row.prev,
            }
        )
    if errors:
        return _fail(
            "plan rejected: " + "; ".join(errors),
            updates=updates,
            errors=errors,
            mode="plan",
        )
    if not updates:
        return _fail("all deltas are zero; nothing to apply", updates=[], mode="plan")
    avg_before = sum(r.completion for r in current.values()) / len(current)
    projected = dict(current)
    for u in updates:
        old = projected[u["phase"]]
        projected[u["phase"]] = PhaseRow(
            phase=old.phase,
            title=old.title,
            completion=u["new_completion"],
            prev=old.completion,
            delta=u["delta"],
        )
    avg_after = sum(r.completion for r in projected.values()) / len(projected)
    return _ok(
        f"plan ok: {len(updates)} phase(s)",
        mode="plan",
        updates=updates,
        average_before=round(avg_before, 2),
        average_after=round(avg_after, 2),
        average_delta_pp=round(avg_after - avg_before, 2),
        non_claims=[
            "≠ auto-uplift without authorize",
            "≠ Phase closure",
            "≠ prod / required CI / Round-2 GO",
        ],
    )


def _bar(pct: int, width: int = 20) -> str:
    filled = max(0, min(width, round(pct / 100 * width)))
    return "█" * filled + "░" * (width - filled)


def _fmt_delta_cell(delta: int) -> str:
    if delta == 0:
        return "0"
    return f"**{delta:+d}%**"


def _render_gauge_table(rows: list[PhaseRow], label: str) -> str:
    lines = [
        f"### Phase Completion Gauge（{label}）",
        "",
        "> **口径**：下列 `completion` 为 **全局 Phase%**（本表「当前」列）；**≠** Tabular 子域独立 Phase%。"
        "`cases/demo_phase/raw/Phase.csv` 为 Tabular 输入 maturity 范例，**不是**本表数据源。",
        "",
        "| Phase | completion | prev | delta |",
        "|-------|------------|------|-------|",
    ]
    for r in rows:
        title = PHASE_TITLES.get(r.phase, r.title)
        lines.append(
            f"| {r.phase} {title} | **{r.completion}%** | {r.prev}% | {_fmt_delta_cell(r.delta)} |"
        )
    return "\n".join(lines) + "\n"


def _render_single_line(rows: list[PhaseRow]) -> str:
    lines = ["**单行索引（playbook / Progress 可引用）**：", ""]
    for r in rows:
        # Phase number for "Phase 4" style: strip leading P
        num = r.phase[1:]
        if r.delta == 0:
            delta_s = "0"
        else:
            delta_s = f"**{r.delta:+d}%**"
        lines.append(
            f"- Phase {num}: completion **{r.completion}%** "
            f"(prev {r.prev}%, delta {delta_s})"
        )
    return "\n".join(lines) + "\n"


def _render_progress_bars(rows: list[PhaseRow], label: str) -> str:
    lines = [
        f"### Phase 完成度进度条（{label} · 人读 Gauge）",
        "",
        "> **bar**：20 格 · `█` = 已完成 · `░` = 未完成 · **≠** CI gate · **≠** Tabular 子域独立 Phase%",
        "",
    ]
    for r in rows:
        title = PHASE_TITLES.get(r.phase, r.title)
        num = r.phase[1:]
        adj = f"调整 {r.delta:+d}" if r.delta else "调整 0"
        if r.delta:
            adj = f"**{r.delta:+d}**"
        lines.append(
            f"- Phase {num} {title}：上一版 {r.prev}% → 目前版 {r.completion}%（{adj}）  "
        )
        lines.append(f"  `{_bar(r.completion)}` **{r.completion}%**")
    return "\n".join(lines) + "\n"


def apply_to_dashboard_text(
    text: str,
    updates: list[dict[str, Any]],
    *,
    label: str,
) -> str:
    rows = read_gauge_rows(text)
    by = rows_to_map(rows)
    for u in updates:
        old = by[u["phase"]]
        by[u["phase"]] = PhaseRow(
            phase=old.phase,
            title=old.title,
            completion=u["new_completion"],
            prev=u["prev_completion"],
            delta=u["delta"],
        )
    ordered = [by[p] for p in PHASE_IDS if p in by]

    # Replace Gauge section
    g_start, g_end, _ = _extract_section(
        text,
        GAUGE_HEADER,
        [SINGLE_LINE_HEADER, PROGRESS_BAR_HEADER],
    )
    text = text[:g_start] + _render_gauge_table(ordered, label) + "\n" + text[g_end:]

    # Replace single-line index
    if SINGLE_LINE_HEADER in text:
        s_start = text.find(SINGLE_LINE_HEADER)
        # end at progress bar or next ###
        s_end = len(text)
        for em in [PROGRESS_BAR_HEADER, "\n### ", "\n## "]:
            idx = text.find(em, s_start + 5)
            if idx >= 0:
                s_end = min(s_end, idx)
        text = text[:s_start] + _render_single_line(ordered) + "\n" + text[s_end:]

    # Replace progress bars section (until next ## or --- horizontal before Wave)
    if PROGRESS_BAR_HEADER in text:
        p_start = text.find(PROGRESS_BAR_HEADER)
        p_end = len(text)
        for em in ["\n## ", "\n---\n"]:
            idx = text.find(em, p_start + 5)
            if idx >= 0:
                p_end = min(p_end, idx)
        text = text[:p_start] + _render_progress_bars(ordered, label) + "\n" + text[p_end:]

    # Patch main SSOT table current column: | **P4** ... | ... | **77%** |
    for u in updates:
        phase = u["phase"]
        new_pct = u["new_completion"]
        # Match table row starting with | **P4** or | **P8.5**
        pattern = re.compile(
            rf"^(\|\s*\*\*{re.escape(phase)}\*\*[^\n]*?\|\s*[^\|]*?\|\s*)\*\*\d+%\*\*",
            re.M,
        )
        text, n = pattern.subn(rf"\1**{new_pct}%**", text, count=1)
        if n == 0:
            # Some rows may use | **P1** without bold on percent already handled
            pattern2 = re.compile(
                rf"^(\|\s*\*\*{re.escape(phase)}\*\*[^\n]*?\|\s*[^\|]*?\|\s*)\*\*\d+%\*\*",
                re.M,
            )
            text, _ = pattern2.subn(rf"\1**{new_pct}%**", text, count=1)

    # Light footer note on refresh line if present
    refresh_pat = re.compile(
        r"(>\s*\*\*刷新\*\*：)([^\n]+)",
    )
    note = (
        f"{label} · apply via `_phase_pct_apply.py` · "
        + " · ".join(f"{u['phase']} {u['prev_completion']}→{u['new_completion']}" for u in updates)
    )
    if refresh_pat.search(text):
        text = refresh_pat.sub(rf"\1{note}", text, count=1)

    return text


def cmd_read(root: Path) -> dict[str, Any]:
    path = _dashboard_path(root)
    if not path.is_file():
        return _fail(f"Dashboard missing: {DASHBOARD_REL}")
    text = path.read_text(encoding="utf-8")
    rows = read_gauge_rows(text)
    avg = sum(r.completion for r in rows) / len(rows)
    return _ok(
        f"read {len(rows)} phases from Gauge",
        mode="read",
        ssot=DASHBOARD_REL,
        protocol=PROTOCOL_REL,
        phases=[
            {
                "phase": r.phase,
                "title": r.title,
                "completion": r.completion,
                "prev": r.prev,
                "delta": r.delta,
            }
            for r in rows
        ],
        average_pct=round(avg, 2),
        phase_count=len(rows),
    )


def cmd_plan(root: Path, deltas: dict[str, int], **kwargs: Any) -> dict[str, Any]:
    path = _dashboard_path(root)
    text = path.read_text(encoding="utf-8")
    current = rows_to_map(read_gauge_rows(text))
    result = plan_updates(current, deltas, **kwargs)
    result["ssot"] = DASHBOARD_REL
    result["dry_run"] = True
    return result


def cmd_from_ticket(
    root: Path,
    ticket_id: str,
    *,
    max_delta: int,
    allow_large_delta: bool,
) -> dict[str, Any]:
    tpath = _ticket_path(root, ticket_id)
    if not tpath.is_file():
        return _fail(f"ticket state not found: {tpath.as_posix().replace(str(root).replace(chr(92), '/') + '/', '')}")
    # Prefer repo-relative in message
    rel = tpath.relative_to(root).as_posix()
    frame = parse_ticket_frame(tpath.read_text(encoding="utf-8"))
    deltas = dict(frame["deltas"])
    if not deltas and frame["phase_targets"]:
        # targets listed but no numeric delta → treat as propose-only zero plan
        return _ok(
            "ticket has phase_targets but no parseable proposed_delta_pct",
            mode="from-ticket",
            ticket=rel,
            frame=frame,
            dry_run=True,
            write_allowed=False,
            next_step="run estimate --ticket-id … or fill proposed_delta_pct then re-run",
        )
    plan = cmd_plan(
        root,
        deltas,
        max_delta=max_delta,
        allow_large_delta=allow_large_delta,
    )
    write_allowed = bool(
        frame["apply_phase_pct"]
        and frame["authorized_marker"]
        and frame.get("phase_delta_lifecycle") == LIFECYCLE_VERIFIED
    )
    plan.update(
        {
            "mode": "from-ticket",
            "ticket": rel,
            "frame": {
                "apply_phase_pct": frame["apply_phase_pct"],
                "phase_targets": frame["phase_targets"],
                "baseline_pct": frame["baseline_pct"],
                "proposed_delta_pct": frame["proposed_delta_pct"],
                "evidence_gate": frame["evidence_gate"],
                "authorized_marker": frame["authorized_marker"],
                "phase_delta_lifecycle": frame.get("phase_delta_lifecycle"),
            },
            "write_allowed": write_allowed,
            "dry_run": True,
            "completion_hook": (
                "rhythm: estimate → verify → apply; "
                "apply_phase_pct=false → propose-only; "
                "write needs verified + true + 已授權寫入 + --authorize"
            ),
        }
    )
    if plan.get("ok") and not frame["apply_phase_pct"]:
        plan["message"] = (
            plan["message"]
            + " · apply_phase_pct=false → propose-only (W-PROG required to write)"
        )
    return plan


def cmd_estimate(
    root: Path,
    ticket_id: str,
    *,
    write_back: bool = False,
    force_heuristic: bool = False,
) -> dict[str, Any]:
    """Pre-work estimate of proposed_delta (does not write Dashboard %)."""
    tpath = _ticket_path(root, ticket_id)
    if not tpath.is_file():
        return _fail(f"ticket state not found for {ticket_id}", mode="estimate")
    rel = tpath.relative_to(root).as_posix()
    text = tpath.read_text(encoding="utf-8")
    frame = parse_ticket_frame(text)

    if force_heuristic:
        # ignore explicit deltas for re-estimate
        frame_h = dict(frame)
        frame_h["deltas"] = {}
        frame_h["proposed_delta_pct"] = None
        est = estimate_deltas_for_ticket(text, frame_h)
    else:
        est = estimate_deltas_for_ticket(text, frame)

    deltas = dict(est.get("deltas") or {})
    targets = frame.get("phase_targets") or list(deltas.keys())
    baseline = frame.get("baseline_pct") or _baseline_from_dashboard(root, targets)

    wrote = False
    if write_back:
        write_back_estimate(tpath, text, est, {**frame, "baseline_pct": baseline})
        wrote = True

    plan = None
    if deltas and any(v != 0 for v in deltas.values()):
        plan = cmd_plan(root, deltas)
    elif deltas:
        plan = _ok(
            "estimate is all-zero (tool/micro or blocked gate)",
            mode="plan",
            updates=[],
            dry_run=True,
        )

    return _ok(
        f"estimate ok: {format_proposed_delta_pct(deltas)} ({est.get('source')})",
        mode="estimate",
        ticket=rel,
        lifecycle=LIFECYCLE_ESTIMATED,
        phase_targets=targets,
        baseline_pct=baseline,
        proposed_delta_pct=format_proposed_delta_pct(deltas),
        deltas=deltas,
        estimate=est,
        plan=plan,
        write_back=wrote,
        dry_run=not wrote,
        apply_phase_pct=frame.get("apply_phase_pct"),
        next_step=[
            "開工可引用本 estimate；干活≠漲%",
            "驗收／Review 通過後：verify --checks-ok [--write-back]",
            "僅 W-PROG：apply_phase_pct=true + 已授權寫入 + apply --authorize",
        ],
        non_claims=[
            "≠ Dashboard write",
            "≠ Phase closure",
            (
                "heuristic v0.1 approved／定稿（尚書省 2026-07-13）"
                if est.get("heuristic")
                else "explicit FRAME delta"
            ),
        ],
    )


def cmd_verify(
    root: Path,
    ticket_id: str,
    *,
    checks_ok: bool = False,
    write_back: bool = False,
    require_unittest: bool = False,
) -> dict[str, Any]:
    """
    Post-check gate: promote estimate → verified (apply candidate).
    Does not write Dashboard %.
    """
    tpath = _ticket_path(root, ticket_id)
    if not tpath.is_file():
        return _fail(f"ticket state not found for {ticket_id}", mode="verify")
    rel = tpath.relative_to(root).as_posix()
    text = tpath.read_text(encoding="utf-8")
    frame = parse_ticket_frame(text)

    # Prefer existing deltas; else re-estimate
    if frame.get("deltas"):
        deltas = dict(frame["deltas"])
        est_meta = {"source": "explicit", "heuristic": False}
    else:
        est = estimate_deltas_for_ticket(text, frame)
        deltas = dict(est.get("deltas") or {})
        est_meta = est

    if not deltas and not frame.get("phase_targets"):
        return _fail(
            "verify refused: no phase_targets / deltas to verify",
            mode="verify",
            ticket=rel,
        )

    checks = {
        "checks_ok_flag": bool(checks_ok),
        "review_ok_marker": bool(frame.get("review_ok_marker")),
        "lifecycle_was": frame.get("phase_delta_lifecycle"),
        "has_deltas": bool(deltas),
    }
    if require_unittest:
        checks["unittest_required"] = True
        checks["unittest_note"] = "caller must pass --checks-ok after running unittest"

    passed = bool(checks_ok or frame.get("review_ok_marker"))
    if not passed:
        return _fail(
            "verify refused: need --checks-ok or ticket review/done marker "
            "(overall_status=done / C_REPORT accepted)",
            mode="verify",
            ticket=rel,
            checks=checks,
            deltas=deltas,
            lifecycle=frame.get("phase_delta_lifecycle") or LIFECYCLE_ESTIMATED,
            write_candidate=False,
            next_step="run review/unittest then re-run verify --checks-ok",
        )

    wrote = False
    if write_back:
        write_back_verify(tpath, text, deltas=deltas, checks=checks)
        wrote = True

    write_candidate = True  # verified; still gated by apply_phase_pct + authorize
    return _ok(
        "verify ok: lifecycle→verified (apply candidate; Dashboard not written)",
        mode="verify",
        ticket=rel,
        lifecycle=LIFECYCLE_VERIFIED,
        deltas=deltas,
        proposed_delta_pct=format_proposed_delta_pct(deltas),
        checks=checks,
        estimate_meta=est_meta,
        write_back=wrote,
        write_candidate=write_candidate,
        apply_phase_pct=frame.get("apply_phase_pct"),
        authorized_marker=frame.get("authorized_marker"),
        dry_run=not wrote,
        next_step=[
            "若 apply_phase_pct=false → 僅提案；待 W-PROG 匯總",
            "若 W-PROG 已授權：apply --ticket-id … --authorize",
        ],
        non_claims=[
            "verified ≠ applied",
            "≠ Dashboard write without authorize",
        ],
    )


def cmd_apply(
    root: Path,
    *,
    ticket_id: str | None,
    deltas: dict[str, int] | None,
    authorize: bool,
    label: str | None,
    max_delta: int,
    allow_large_delta: bool,
    dry_run: bool,
) -> dict[str, Any]:
    if not authorize and not dry_run:
        return _fail(
            "refuse write: pass --authorize (and prefer --ticket-id W-PROG with "
            "apply_phase_pct: true + verified + 已授權寫入). Use --dry-run to preview.",
            mode="apply",
        )

    frame: dict[str, Any] | None = None
    ticket_rel = None
    if ticket_id:
        tpath = _ticket_path(root, ticket_id)
        if not tpath.is_file():
            return _fail(f"ticket state not found for {ticket_id}")
        ticket_rel = tpath.relative_to(root).as_posix()
        frame = parse_ticket_frame(tpath.read_text(encoding="utf-8"))
        if not deltas:
            deltas = dict(frame["deltas"])
        if not dry_run:
            if not frame["apply_phase_pct"]:
                return _fail(
                    "refuse write: ticket apply_phase_pct is false "
                    "(ordinary tickets only propose Δ)",
                    mode="apply",
                    ticket=ticket_rel,
                    frame=frame,
                )
            lifecycle = frame.get("phase_delta_lifecycle") or LIFECYCLE_NONE
            if lifecycle != LIFECYCLE_VERIFIED:
                return _fail(
                    "refuse write: phase_delta_lifecycle must be verified "
                    f"(got {lifecycle!r}). Run: estimate → verify --checks-ok --write-back",
                    mode="apply",
                    ticket=ticket_rel,
                    lifecycle=lifecycle,
                    frame={
                        "apply_phase_pct": frame["apply_phase_pct"],
                        "phase_delta_lifecycle": lifecycle,
                        "authorized_marker": frame["authorized_marker"],
                    },
                )
            if not frame["authorized_marker"]:
                return _fail(
                    "refuse write: ticket missing 已授權寫入 / authorization marker",
                    mode="apply",
                    ticket=ticket_rel,
                    frame=frame,
                )
            if not authorize:
                return _fail("refuse write: --authorize required", mode="apply")
    elif not dry_run:
        return _fail(
            "refuse write without --ticket-id (W-PROG／Governance gate). "
            "CLI-only deltas allowed with --dry-run.",
            mode="apply",
        )

    deltas = deltas or {}
    plan = cmd_plan(
        root,
        deltas,
        max_delta=max_delta,
        allow_large_delta=allow_large_delta,
    )
    if not plan.get("ok"):
        plan["mode"] = "apply"
        return plan

    use_label = label or f"{date.today().isoformat()} · W-PROG · `_phase_pct_apply`"
    if dry_run or not authorize:
        plan.update(
            {
                "mode": "apply",
                "dry_run": True,
                "would_write": DASHBOARD_REL,
                "label": use_label,
                "ticket": ticket_rel,
                "lifecycle": (frame or {}).get("phase_delta_lifecycle") if frame else None,
                "message": plan["message"] + " · dry-run (no file write)",
            }
        )
        return plan

    path = _dashboard_path(root)
    old = path.read_text(encoding="utf-8")
    new = apply_to_dashboard_text(old, plan["updates"], label=use_label)
    if new == old:
        return _fail(
            "apply produced identical text (parser/writer mismatch?)",
            mode="apply",
            updates=plan["updates"],
        )
    path.write_text(new, encoding="utf-8")
    # verify round-trip
    verify_rows = rows_to_map(read_gauge_rows(new))
    verify_ok = True
    verify_errors: list[str] = []
    for u in plan["updates"]:
        got = verify_rows[u["phase"]].completion
        if got != u["new_completion"]:
            verify_ok = False
            verify_errors.append(f"{u['phase']} expected {u['new_completion']} got {got}")
    return _ok(
        f"applied {len(plan['updates'])} phase delta(s) to Dashboard",
        mode="apply",
        dry_run=False,
        ssot=DASHBOARD_REL,
        ticket=ticket_rel,
        label=use_label,
        lifecycle=LIFECYCLE_APPLIED,
        updates=plan["updates"],
        average_before=plan.get("average_before"),
        average_after=plan.get("average_after"),
        verify_ok=verify_ok,
        verify_errors=verify_errors,
        non_claims=plan.get("non_claims"),
        next_step=[
            "append Progress 末尾 Phase 影響（实际上调=是）",
            "optional: mark ticket phase_delta_lifecycle: applied",
            "optional: WORKFLOW_INDEX §1.7 one-liner",
            "≠ war_status unless separate 尚書省授权",
        ],
    )


def cmd_self_test(root: Path) -> dict[str, Any]:
    """Non-mutating checks: read + plan gates + estimate/verify/apply rhythm."""
    steps: list[dict[str, Any]] = []
    r = cmd_read(root)
    steps.append({"step": "read", "ok": r.get("ok"), "phase_count": r.get("phase_count")})
    if not r.get("ok"):
        return _fail("self-test failed at read", steps=steps)

    # invalid large delta without flag
    bad = cmd_plan(root, {"P4": 99}, allow_large_delta=False, max_delta=DEFAULT_MAX_DELTA)
    steps.append({"step": "reject_large_delta", "ok": not bad.get("ok")})

    # dry-run plan with +0-only should fail
    zero = cmd_plan(root, {"P4": 0})
    steps.append({"step": "reject_zero", "ok": not zero.get("ok")})

    # dry-run apply without authorize must not write
    before = _dashboard_path(root).read_text(encoding="utf-8")
    applied = cmd_apply(
        root,
        ticket_id=None,
        deltas={"P4": 1},
        authorize=False,
        label=None,
        max_delta=DEFAULT_MAX_DELTA,
        allow_large_delta=False,
        dry_run=True,
    )
    after = _dashboard_path(root).read_text(encoding="utf-8")
    steps.append(
        {
            "step": "dry_run_no_write",
            "ok": before == after and applied.get("dry_run") is True,
            "apply_message": applied.get("message"),
        }
    )

    # refuse write without ticket
    refuse = cmd_apply(
        root,
        ticket_id=None,
        deltas={"P4": 1},
        authorize=True,
        label=None,
        max_delta=DEFAULT_MAX_DELTA,
        allow_large_delta=False,
        dry_run=False,
    )
    steps.append({"step": "refuse_write_without_ticket", "ok": not refuse.get("ok")})

    # heuristic estimate produces deltas
    sample = (
        "phase_targets: [P4]\n"
        "baseline_pct: n/a\n"
        "evidence_gate: L-local\n"
        "impact_size: medium\n"
        "apply_phase_pct: false\n"
    )
    est = estimate_deltas_for_ticket(sample)
    steps.append(
        {
            "step": "estimate_heuristic",
            "ok": est.get("ok") and est.get("deltas", {}).get("P4") == 2,
            "deltas": est.get("deltas"),
        }
    )

    # temp ticket under tickets/: estimate → refuse apply → verify → dry-run apply
    tid = "__selftest_phase_pct_estimate_v1"
    tpath = _ticket_path(root, tid)
    body = (
        "# TICKET STATE · __selftest_phase_pct_estimate_v1\n\n"
        "## FRAME\n\n"
        "phase_targets: [P4]\n"
        "baseline_pct: \"self-test\"\n"
        "evidence_gate: L-local\n"
        "impact_size: medium\n"
        "apply_phase_pct: true\n"
        "**已授權寫入**\n"
    )
    try:
        tpath.write_text(body, encoding="utf-8")
        e1 = cmd_estimate(root, tid, write_back=True, force_heuristic=True)
        steps.append(
            {
                "step": "estimate_write_back",
                "ok": e1.get("ok") and e1.get("deltas", {}).get("P4") == 2,
            }
        )
        a_bad = cmd_apply(
            root,
            ticket_id=tid,
            deltas=None,
            authorize=True,
            label=None,
            max_delta=DEFAULT_MAX_DELTA,
            allow_large_delta=False,
            dry_run=False,
        )
        steps.append(
            {
                "step": "refuse_apply_before_verify",
                "ok": not a_bad.get("ok")
                and "verified" in (a_bad.get("message") or "").lower(),
            }
        )
        v1 = cmd_verify(root, tid, checks_ok=True, write_back=True)
        steps.append(
            {
                "step": "verify_ok",
                "ok": v1.get("ok") and v1.get("lifecycle") == LIFECYCLE_VERIFIED,
            }
        )
        dash_before = _dashboard_path(root).read_text(encoding="utf-8")
        a_ok = cmd_apply(
            root,
            ticket_id=tid,
            deltas=None,
            authorize=True,
            label=None,
            max_delta=DEFAULT_MAX_DELTA,
            allow_large_delta=False,
            dry_run=True,
        )
        dash_after = _dashboard_path(root).read_text(encoding="utf-8")
        steps.append(
            {
                "step": "apply_dry_run_after_verify",
                "ok": a_ok.get("ok")
                and a_ok.get("dry_run") is True
                and dash_before == dash_after,
            }
        )
    finally:
        if tpath.is_file():
            tpath.unlink()

    all_ok = all(s.get("ok") for s in steps)
    return (
        _ok(
            "self-test passed",
            mode="self-test",
            steps=steps,
            heuristic_version=HEURISTIC_VERSION,
            heuristic_status=HEURISTIC_STATUS,
        )
        if all_ok
        else _fail("self-test failed", mode="self-test", steps=steps)
    )


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    common.add_argument(
        "--root",
        default=str(REPO_ROOT),
        help="Repo root (default: parent of 04_Workflows)",
    )

    p = argparse.ArgumentParser(
        description="Phase percent estimate/verify/apply runner for WAVE_PROGRESS_DASHBOARD SSOT",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser(
        "read",
        parents=[common],
        help="Read current Phase percent from Dashboard Gauge",
    )
    sub.add_parser("self-test", parents=[common], help="Non-mutating sanity checks")

    p_est = sub.add_parser(
        "estimate",
        parents=[common],
        help="Pre-work auto-estimate proposed_delta (no Dashboard write)",
    )
    p_est.add_argument("--ticket-id", required=True)
    p_est.add_argument(
        "--write-back",
        action="store_true",
        help="Append estimate block + patch FRAME proposed_delta_pct / lifecycle",
    )
    p_est.add_argument(
        "--force-heuristic",
        action="store_true",
        help="Ignore explicit proposed_delta_pct and re-estimate from heuristic",
    )

    p_ver = sub.add_parser(
        "verify",
        parents=[common],
        help="Post-check: promote estimate → verified (still no Dashboard write)",
    )
    p_ver.add_argument("--ticket-id", required=True)
    p_ver.add_argument(
        "--checks-ok",
        action="store_true",
        help="Caller asserts review/unittest/DoD passed",
    )
    p_ver.add_argument(
        "--write-back",
        action="store_true",
        help="Write phase_delta_lifecycle: verified into ticket state",
    )

    p_plan = sub.add_parser("plan", parents=[common], help="Dry-run plan from --delta")
    p_plan.add_argument(
        "--delta",
        action="append",
        default=[],
        help="Phase delta, e.g. P8.5=+2 (repeatable)",
    )
    p_plan.add_argument("--max-delta", type=int, default=DEFAULT_MAX_DELTA)
    p_plan.add_argument("--allow-large-delta", action="store_true")

    p_ft = sub.add_parser(
        "from-ticket",
        parents=[common],
        help="Plan from ticket FRAME Phase impact fields",
    )
    p_ft.add_argument("--ticket-id", required=True)
    p_ft.add_argument("--max-delta", type=int, default=DEFAULT_MAX_DELTA)
    p_ft.add_argument("--allow-large-delta", action="store_true")

    p_ap = sub.add_parser(
        "apply",
        parents=[common],
        help="Apply deltas (needs verified + authorize; default dry-run)",
    )
    p_ap.add_argument("--ticket-id", help="W-PROG/Governance ticket id")
    p_ap.add_argument("--delta", action="append", default=[], help="Override/extra deltas")
    p_ap.add_argument("--authorize", action="store_true", help="Authorized write to Dashboard")
    p_ap.add_argument("--dry-run", action="store_true", help="Force preview (no write)")
    p_ap.add_argument("--label", help="Gauge/label stamp, e.g. 2026-07-13 W-PROG-C")
    p_ap.add_argument("--max-delta", type=int, default=DEFAULT_MAX_DELTA)
    p_ap.add_argument("--allow-large-delta", action="store_true")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    if args.command == "read":
        result = cmd_read(root)
    elif args.command == "self-test":
        result = cmd_self_test(root)
    elif args.command == "estimate":
        result = cmd_estimate(
            root,
            args.ticket_id,
            write_back=bool(args.write_back),
            force_heuristic=bool(args.force_heuristic),
        )
    elif args.command == "verify":
        result = cmd_verify(
            root,
            args.ticket_id,
            checks_ok=bool(args.checks_ok),
            write_back=bool(args.write_back),
        )
    elif args.command == "plan":
        try:
            deltas = parse_delta_args(args.delta)
        except ValueError as e:
            result = _fail(str(e), mode="plan")
        else:
            result = cmd_plan(
                root,
                deltas,
                max_delta=args.max_delta,
                allow_large_delta=args.allow_large_delta,
            )
    elif args.command == "from-ticket":
        result = cmd_from_ticket(
            root,
            args.ticket_id,
            max_delta=args.max_delta,
            allow_large_delta=args.allow_large_delta,
        )
    elif args.command == "apply":
        try:
            deltas = parse_delta_args(args.delta) if args.delta else {}
        except ValueError as e:
            result = _fail(str(e), mode="apply")
        else:
            # Default dry-run unless authorize without --dry-run
            dry = bool(args.dry_run or not args.authorize)
            result = cmd_apply(
                root,
                ticket_id=args.ticket_id,
                deltas=deltas or None,
                authorize=bool(args.authorize),
                label=args.label,
                max_delta=args.max_delta,
                allow_large_delta=args.allow_large_delta,
                dry_run=dry,
            )
    else:
        result = _fail(f"unknown command: {args.command}")

    if args.pretty:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
