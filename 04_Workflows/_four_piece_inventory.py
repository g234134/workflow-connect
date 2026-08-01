#!/usr/bin/env python3
"""Scan ticket state files and classify four-piece delivery status."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TICKETS_DIR = REPO / "04_Workflows" / "tickets"
CODE_EXT = {".py", ".sh", ".ps1", ".yml", ".yaml", ".json"}


def norm(p: str) -> str:
    return p.replace("\\", "/").strip().strip("`").strip('"').strip("'")


def is_test(p: str) -> bool:
    s = p.replace("\\", "/").lower()
    if "/tests/" in s or s.startswith("tests/"):
        return True
    name = Path(p).name.lower()
    return name.startswith("test_") or name.endswith("_test.py")


def is_doc(p: str) -> bool:
    if is_test(p):
        return False
    s = p.replace("\\", "/")
    if s.endswith("_state.md"):
        return False
    ext = Path(p).suffix.lower()
    if ext == ".md":
        return True
    if ext in {".yml", ".yaml"} and ".github/workflows/" in s:
        return True
    return False


def is_code(p: str) -> bool:
    if is_test(p):
        return False
    ext = Path(p).suffix.lower()
    return ext in CODE_EXT and not p.endswith(".md")


def extract_paths(text: str) -> list[str]:
    paths: set[str] = set()
    for m in re.finditer(r"`([^`]+)`", text):
        p = norm(m.group(1))
        if any(ext in p for ext in CODE_EXT) or p.endswith(".md"):
            paths.add(p.split("（")[0].split("(")[0].strip())
    for m in re.finditer(
        r"[-*]\s*([^\n`]+?\.(?:py|md|yml|yaml|json|ps1|sh))",
        text,
    ):
        p = norm(m.group(1))
        if "/" in p:
            paths.add(p.split("（")[0].split("(")[0].strip())

    cleaned: list[str] = []
    for p in sorted(paths):
        if any(x in p for x in ["<!--", "§", "...", "<", ">", "*"]):
            continue
        if p.startswith("04_Workflows/tickets/") and not p.endswith("_state.md"):
            continue
        cleaned.append(p)
    return cleaned


def extract_status(text: str) -> dict[str, str | None]:
    overall = re.search(r"overall_status:\s*([^\n]+)", text)
    conclusion = re.search(r"conclusion:\s*\*?\*?([^\n*]+)", text, re.I)
    impl = re.search(r"implementation_status:\s*([^\n]+)", text)
    return {
        "overall_status": overall.group(1).strip() if overall else None,
        "conclusion": conclusion.group(1).strip() if conclusion else None,
        "implementation_status": impl.group(1).strip() if impl else None,
    }


def bucket_paths(paths: list[str], state_path: str) -> tuple[list[str], list[str], list[str]]:
    code_paths: list[str] = []
    test_paths: list[str] = []
    doc_paths: list[str] = []
    for p in paths:
        if p == state_path or p.endswith("_state.md"):
            continue
        if is_test(p):
            test_paths.append(p)
        elif is_doc(p):
            doc_paths.append(p)
        elif is_code(p):
            code_paths.append(p)
        elif p.endswith(".md"):
            doc_paths.append(p)
    return sorted(set(code_paths)), sorted(set(test_paths)), sorted(set(doc_paths))


def classify(
    code_paths: list[str],
    test_paths: list[str],
    doc_paths: list[str],
    state_path: str,
    text: str,
    status: dict[str, str | None],
) -> tuple[str, dict[str, bool]]:
    has_state = Path(state_path).exists()
    has_code = any((REPO / p).exists() for p in code_paths)
    has_tests = any((REPO / p).exists() for p in test_paths)
    has_docs = any((REPO / p).exists() for p in doc_paths)
    exists = {"code": has_code, "tests": has_tests, "docs": has_docs, "state": has_state}

    b_report = ""
    if "## B_REPORT" in text:
        tail = text.split("## B_REPORT", 1)[1]
        b_report = tail.split("## C_REPORT", 1)[0] if "## C_REPORT" in tail else tail
    b_empty = (
        "changed_files:" in b_report
        and "`" not in b_report[:1200]
        and "<!-- Implementer 填 -->" in b_report
    )

    st = (status.get("overall_status") or "").lower()
    if b_empty and not has_code and not has_tests and not has_docs:
        return "unclear", exists
    if st == "draft" and not has_code and not has_tests and not has_docs:
        return "unclear", exists

    kinds = sum([has_code, has_tests, has_docs, has_state])
    if has_code and has_tests and has_docs and has_state:
        return "done_4piece", exists
    if kinds == 3:
        return "partial_3piece", exists
    if kinds == 2:
        return "partial_2piece", exists
    if (has_docs or has_state) and not has_code:
        return "design_only", exists
    return "unclear", exists


def overclaim_note(ticket_id: str, text: str, status: dict[str, str | None]) -> list[str]:
    notes: list[str] = []
    st = (status.get("overall_status") or "").lower()
    conc = (status.get("conclusion") or "").lower()
    blob = text.lower()

    if "accepted_with_gaps" in conc or "accepted_with_gaps" in st:
        notes.append("accepted_with_gaps ≠ fully done")
    if st == "done" and "accepted_with_gaps" in conc:
        notes.append("state=done but reviewer=accepted_with_gaps")
    if "plan_only" in blob or "plan-only" in blob:
        notes.append("plan_only; not blocking gate / main-chain execute")
    if "skeleton" in blob:
        notes.append("skeleton/reference ≠ prod gate implemented")
    if "nightly" in blob and ("ci" in blob or "workflow" in blob):
        notes.append("nightly/e2e ≠ PR blocking gate")
    if "l1" in ticket_id.lower() or ("l1" in blob and "advisory" in blob):
        notes.append("L1 advisory ≠ blocking CI")
    if "design" in blob and ("draft" in blob or "design only" in blob):
        notes.append("design draft ≠ implemented gate")
    if "reviewer: pending" in blob or "reviewer pending" in blob:
        notes.append("reviewer pending; ticket not closed")
    if st in {"in_progress", "in_review", "implementer done · reviewer pending", "implementer_done"}:
        notes.append(f"state={status.get('overall_status')}; do not overclaim closure")
    if "first ci" in blob or "placeholder" in blob or "_tbd_" in blob:
        notes.append("CI green-run evidence placeholder; not proven in Actions")
    if "doc-only" in blob or "document-only" in blob:
        notes.append("doc-only/contract ticket; spec ≠ runtime wiring")
    if "investigation-only" in blob:
        notes.append("investigation-only; not SLA or production gate")
    if "feature flag" in blob and ("default off" in blob or "default 0" in blob or "預設 off" in text):
        notes.append("feature flag default off; not wired to main chain")
    if "guard draft" in blob:
        notes.append("guard draft ≠ gate implemented")

    deduped: list[str] = []
    for n in notes:
        if n not in deduped:
            deduped.append(n)
    return deduped[:5]


def main() -> None:
    state_files = sorted(set(TICKETS_DIR.glob("*_state.md")))
    results: list[dict] = []
    for sf in state_files:
        text = sf.read_text(encoding="utf-8", errors="replace")
        ticket_id = sf.stem.replace("_state", "")
        state_path = str(sf.relative_to(REPO)).replace("\\", "/")

        b_report = ""
        if "## B_REPORT" in text:
            tail = text.split("## B_REPORT", 1)[1]
            b_report = tail.split("## C_REPORT", 1)[0] if "## C_REPORT" in tail else tail
        paths = extract_paths(b_report) if b_report else []
        if len(paths) < 2:
            paths = extract_paths(text)

        code_paths, test_paths, doc_paths = bucket_paths(paths, state_path)
        status = extract_status(text)
        classification, exists = classify(code_paths, test_paths, doc_paths, state_path, text, status)
        results.append(
            {
                "ticket_id": ticket_id,
                "classification": classification,
                "overall_status": status.get("overall_status"),
                "reviewer_conclusion": status.get("conclusion"),
                "code_paths": code_paths,
                "test_paths": test_paths,
                "doc_paths": doc_paths,
                "state_path": state_path,
                "exists": exists,
                "overclaim_warnings": overclaim_note(ticket_id, text, status),
            }
        )

    out = REPO / ".cursor" / "hooks_state" / "four_piece_inventory.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = Counter(r["classification"] for r in results)
    print(json.dumps({"total": len(results), "summary": dict(summary)}, ensure_ascii=False))
    print(f"WROTE {out}")


if __name__ == "__main__":
    main()
