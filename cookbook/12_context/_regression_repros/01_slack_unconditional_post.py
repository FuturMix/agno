"""
Repro #1 — Slack cookbook posts unconditionally.

cookbook/12_context/05_slack.py claims in its docstring + in the repo
TEST_LOG.md that the write path is gated by SLACK_WRITE_CHANNEL. It is
not. The cookbook hardcodes `write_channel = "#agents"` and calls
agent.aprint_response(write_prompt) every run.

This repro performs static analysis on the cookbook file — no network,
no Slack token needed.

Run:
    python repro/context_main_regressions/01_slack_unconditional_post.py

Exit 0 if the bug reproduces, 1 if it has been fixed.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
COOKBOOK = REPO_ROOT / "cookbook" / "12_context" / "05_slack.py"


def main() -> int:
    src = COOKBOOK.read_text()
    tree = ast.parse(src)

    main_fn = next(
        (
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.AsyncFunctionDef) and n.name == "main"
        ),
        None,
    )
    if main_fn is None:
        print("FAIL: cookbook main() not found — file layout changed")
        return 2

    # The string "SLACK_WRITE_CHANNEL" has to appear somewhere in main()
    # for the write path to be env-gated. This captures both
    # `if os.getenv("SLACK_WRITE_CHANNEL")` and
    # `write_channel = os.getenv("SLACK_WRITE_CHANNEL"); if not write_channel: return`.
    main_src = ast.unparse(main_fn)
    references_env_var = "SLACK_WRITE_CHANNEL" in main_src

    aprint_calls = sum(
        1
        for n in ast.walk(main_fn)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "aprint_response"
    )

    print(f"Cookbook: {COOKBOOK.relative_to(REPO_ROOT)}")
    print(f"  references SLACK_WRITE_CHANNEL in main(): {references_env_var}")
    print(f"  aprint_response calls in main(): {aprint_calls}")
    print()

    if not references_env_var and aprint_calls >= 2:
        print("REPRODUCED: write prompt fires on every run; no env gate.")
        print("Cookbook will post 'Hello from agno.context' to '#agents' with")
        print("any valid SLACK_BOT_TOKEN (or SLACK_TOKEN) that has chat:write scope.")
        return 0

    print("NOT REPRODUCED: write path is env-gated.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
