#!/usr/bin/env python3
"""Hermes Coding Agent — LangGraph ReAct agent for simple code tasks.

Uses LangChain + LangGraph to create an autonomous coding agent that can
read, write, search files and run commands. Routes simple tasks through this
agent; complex tasks go to Cursor.

Usage:
    # Simple invocation
    python core/coding_agent.py --goal "在 core/ 建一個 hello.py"

    # With context
    python core/coding_agent.py --goal "修復 smart_router.py 的 bare except" \
        --context core/smart_router.py

    # JSON output for Hermes integration
    python core/coding_agent.py --goal "..." --json
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path isolation — must run with langchain_latest venv, avoid hermes-agent
# contamination. Set this BEFORE any langchain imports.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent  # D:\大唐三省六部
_SITE = str(_REPO_ROOT / "01_Environments" / "python_venvs" / "langchain_latest" / "lib" / "site-packages")
sys.path = [p for p in sys.path if "hermes" not in p.lower() or "langchain" in p.lower()]
if _SITE not in sys.path:
    sys.path.insert(0, _SITE)

# ---------------------------------------------------------------------------
# LangChain imports
# ---------------------------------------------------------------------------
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FORBIDDEN_PATHS = {
    ".env", ".env.local", ".env.production",
    "runtime/checkpoints",
}
MAX_FILE_READ = 50_000  # chars
MAX_CMD_OUTPUT = 10_000  # chars


# ---------------------------------------------------------------------------
# Tools — the agent's hands
# ---------------------------------------------------------------------------

@tool
def read_file(path: str) -> str:
    """Read a file's contents. Returns the full text (truncated at 50K chars)."""
    p = _resolve(path)
    try:
        _check_forbidden(p)
    except PermissionError as e:
        return f"BLOCKED: {e}"
    if not p.is_file():
        return f"ERROR: {path} not found"
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
        if len(text) > MAX_FILE_READ:
            return text[:MAX_FILE_READ] + f"\n... [truncated, {len(text)} total chars]"
        return text
    except Exception as e:
        return f"ERROR reading {path}: {e}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file. Creates parent dirs. Overwrites existing."""
    p = _resolve(path)
    _check_forbidden(p)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"OK: wrote {len(content)} chars to {path}"
    except Exception as e:
        return f"ERROR writing {path}: {e}"


@tool
def search_files(pattern: str, directory: str = ".") -> str:
    """Search for files matching a glob pattern. Returns list of paths."""
    d = _resolve(directory)
    if not d.is_dir():
        return f"ERROR: {directory} not a directory"
    matches = sorted(d.rglob(pattern))
    paths = [str(m.relative_to(_REPO_ROOT)) for m in matches[:50]]
    if not paths:
        return f"No files matching '{pattern}' in {directory}"
    return "\n".join(paths)


@tool
def search_content(pattern: str, directory: str = ".", file_glob: str = "*.py") -> str:
    """Search file contents using ripgrep-style regex. Returns matching lines."""
    cmd = ["rg", "-n", "--glob", file_glob, pattern, str(_resolve(directory))]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        output = r.stdout.strip()
        if not output:
            return f"No matches for '{pattern}'"
        lines = output.split("\n")
        if len(lines) > 40:
            return "\n".join(lines[:40]) + f"\n... [{len(lines)} total matches]"
        return output
    except FileNotFoundError:
        # Fallback: use Python grep
        return _pygrep(pattern, _resolve(directory), file_glob)
    except Exception as e:
        return f"ERROR: {e}"


@tool
def run_command(command: str, timeout: int = 30) -> str:
    """Run a shell command. Returns stdout+stderr. Max 30s timeout."""
    # Block dangerous commands
    dangerous = ["rm -rf", "del /f", "format", "shutdown", "reboot"]
    for d in dangerous:
        if d in command.lower():
            return f"BLOCKED: '{d}' is a dangerous command"
    try:
        r = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=str(_REPO_ROOT),
        )
        output = r.stdout + r.stderr
        if len(output) > MAX_CMD_OUTPUT:
            output = output[:MAX_CMD_OUTPUT] + "\n... [truncated]"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return f"TIMEOUT after {timeout}s"
    except Exception as e:
        return f"ERROR: {e}"


@tool
def list_directory(path: str = ".") -> str:
    """List files and subdirectories in a path."""
    d = _resolve(path)
    if not d.is_dir():
        return f"ERROR: {path} not a directory"
    entries = []
    for item in sorted(d.iterdir()):
        prefix = "📁 " if item.is_dir() else "📄 "
        entries.append(f"{prefix}{item.name}")
    return "\n".join(entries[:100]) or "(empty)"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve(path: str) -> Path:
    """Resolve a path relative to repo root."""
    p = Path(path)
    if not p.is_absolute():
        p = _REPO_ROOT / p
    return p.resolve()


def _check_forbidden(path: Path) -> None:
    """Raise if path matches forbidden patterns."""
    rel = str(path.relative_to(_REPO_ROOT)) if _REPO_ROOT in path.parents else str(path)
    for f in FORBIDDEN_PATHS:
        if rel.startswith(f) or rel == f:
            raise PermissionError(f"FORBIDDEN: {rel} is protected")


def _pygrep(pattern: str, directory: Path, file_glob: str) -> str:
    """Fallback grep using Python. Skips venvs, .git, node_modules."""
    import re
    rx = re.compile(pattern)
    SKIP = {".git", "node_modules", "__pycache__", ".venv", "venv",
            "01_Environments", ".mypy_cache", ".pytest_cache", ".tox"}
    hits = []
    for p in directory.rglob(file_glob):
        if not p.is_file():
            continue
        if any(part in SKIP for part in p.parts):
            continue
        try:
            for i, line in enumerate(p.read_text("utf-8", errors="replace").splitlines(), 1):
                if rx.search(line):
                    rel = p.relative_to(_REPO_ROOT)
                    hits.append(f"{rel}:{i}: {line.strip()}")
                    if len(hits) >= 40:
                        return "\n".join(hits)
        except Exception:
            continue
    return "\n".join(hits) or f"No matches for '{pattern}'"


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = textwrap.dedent("""\
    You are Hermes Coding Agent, a careful senior engineer.

    You work in the repo: {repo}

    RULES:
    1. Read before you write. Always read a file before modifying it.
    2. Minimal changes. Fix only what's asked. No drive-by refactors.
    3. Match existing code style. Look at neighboring code for conventions.
    4. Verify your work. After writing code, run tests or the relevant command.
    5. If something fails, try to fix it once. If it fails again, stop and report.
    6. Never touch .env, secrets, or files in FORBIDDEN_PATHS.
    7. When done, report: what you changed, what you ran, what the result was.

    OUTPUT FORMAT when you finish:
    Summarize in this structure:
    - CHANGED: <list of files you modified/created>
    - RAN: <commands you executed and their output>
    - STATUS: completed | failed | partial
    - NEXT: <what should happen next, or "none">
""")


def create_agent(model: str = "groq/llama-3.3-70b-versatile"):
    """Create the LangGraph ReAct agent with coding tools."""
    # Load config for API key / provider selection
    import json as _json
    _cfg_path = _REPO_ROOT / "core" / "agent_config.json"
    _cfg = {}
    if _cfg_path.exists():
        try:
            _cfg = _json.loads(_cfg_path.read_text("utf-8")).get("llm", {})
        except Exception:
            pass

    # If user set a real Cursor API key, use Cursor endpoint; else OmniRoute/Groq
    _cursor_key = _cfg.get("api_key", "")
    if _cursor_key and not _cursor_key.startswith("paste-"):
        base_url = _cfg.get("base_url", "https://api2.cursor.sh")
        api_key = _cursor_key
        model = model or _cfg.get("model", "cursor-small")
    else:
        base_url = _cfg.get("fallback_base_url", "http://localhost:20128/v1")
        api_key = "sk-omniroute"
        model = model or _cfg.get("fallback_model", "groq/llama-3.3-70b-versatile")

    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=0,
        max_tokens=4096,
    )

    tools = [read_file, write_file, search_files, search_content, run_command, list_directory]

    system = SYSTEM_PROMPT.format(repo=str(_REPO_ROOT))

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system,
    )
    return agent


def run_agent(goal: str, context_files: list[str] | None = None,
              model: str = "groq/llama-3.3-70b-versatile", max_steps: int = 15) -> dict:
    """Run the coding agent on a task. Returns structured result."""
    agent = create_agent(model=model)

    # Build the prompt
    prompt_parts = [f"TASK: {goal}"]
    if context_files:
        prompt_parts.append("\nCONTEXT FILES (read these first):")
        for f in context_files:
            prompt_parts.append(f"  - {f}")
    prompt = "\n".join(prompt_parts)

    messages = [HumanMessage(content=prompt)]

    try:
        result = agent.invoke(
            {"messages": messages},
            config={"recursion_limit": max_steps},
        )
        # Extract final message
        msgs = result.get("messages", [])
        final = msgs[-1].content if msgs else "No output"

        # Parse the structured output
        return _parse_result(final, goal)
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "goal": goal,
            "completed_at": _now_iso(),
        }


def _parse_result(text: str, goal: str) -> dict:
    """Parse agent output into structured result."""
    result = {
        "goal": goal,
        "completed_at": _now_iso(),
        "raw_output": text,
    }

    # Try to extract structured fields
    for line in text.split("\n"):
        line = line.strip()
        if line.upper().startswith("- CHANGED:") or line.upper().startswith("CHANGED:"):
            files = line.split(":", 1)[1].strip()
            result["files_changed"] = [f.strip() for f in files.split(",") if f.strip()]
        elif line.upper().startswith("- RAN:") or line.upper().startswith("RAN:"):
            result["commands_run"] = line.split(":", 1)[1].strip()
        elif line.upper().startswith("- STATUS:") or line.upper().startswith("STATUS:"):
            result["status"] = line.split(":", 1)[1].strip().lower()
        elif line.upper().startswith("- NEXT:") or line.upper().startswith("NEXT:"):
            result["next_action"] = line.split(":", 1)[1].strip()

    result.setdefault("status", "completed")
    result.setdefault("files_changed", [])
    return result


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Hermes Coding Agent")
    parser.add_argument("--goal", required=True, help="Task description")
    parser.add_argument("--context", nargs="*", default=[], help="Context files to read first")
    parser.add_argument("--model", default="groq/llama-3.3-70b-versatile", help="LLM model name")
    parser.add_argument("--max-steps", type=int, default=15, help="Max agent steps")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()

    result = run_agent(
        goal=args.goal,
        context_files=args.context,
        model=args.model,
        max_steps=args.max_steps,
    )

    if args.json:
        # Remove raw_output for clean JSON
        out = {k: v for k, v in result.items() if k != "raw_output"}
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(f"Status: {result.get('status', 'unknown')}")
        if result.get("files_changed"):
            print(f"Files changed: {result['files_changed']}")
        if result.get("error"):
            print(f"Error: {result['error']}")
        print(f"\n--- Agent output ---\n{result.get('raw_output', '(none)')}")

    return 0 if result.get("status") in ("completed",) else 1


if __name__ == "__main__":
    sys.exit(main())
