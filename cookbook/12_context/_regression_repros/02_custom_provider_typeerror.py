"""
Repro #2 — Custom provider TypeError.

The ContextProvider ABC declares `aquery(self, question, *, run_context=None)`.
The auto-generated tool wrapper at libs/agno/agno/context/provider.py:200
unconditionally calls `provider.aquery(question, run_context=run_context)`.

Any subclass that overrides `aquery` with the simpler documented signature
(`async def aquery(self, question)`) — as cookbook/12_context/10_custom_provider.py
does — raises TypeError at first tool call. The JSON error is swallowed into
the agent's tool response; the agent usually surfaces a vague apology.

This repro reaches directly for the generated tool, no LLM involved, so
the failure is deterministic and visible.

Run:
    python repro/context_main_regressions/02_custom_provider_typeerror.py

Exit 0 if the bug reproduces, 1 if the framework has been fixed.
"""

from __future__ import annotations

import asyncio
import json
import sys

from agno.context import Answer, ContextProvider, Status


class MinimalLegacyProvider(ContextProvider):
    """Uses the simpler override signature documented in 10_custom_provider.py."""

    def status(self) -> Status:
        return Status(ok=True, detail="test")

    async def astatus(self) -> Status:
        return self.status()

    def query(self, question: str) -> Answer:
        return Answer(text=f"answer for: {question}")

    async def aquery(self, question: str) -> Answer:
        return self.query(question)


async def run() -> int:
    provider = MinimalLegacyProvider(id="repro")
    tool = provider.get_tools()[0]
    print(f"Tool generated: {tool.name}")

    result_json = await tool.entrypoint(question="hello")
    print(f"Tool entrypoint returned: {result_json}")

    try:
        parsed = json.loads(result_json)
    except json.JSONDecodeError:
        print("NOT REPRODUCED: tool did not return JSON")
        return 1

    err = parsed.get("error", "")
    if "TypeError" in err and "run_context" in err:
        print()
        print("REPRODUCED: wrapper passes run_context= to a subclass that")
        print("doesn't accept it. Same pattern is shipped in")
        print("cookbook/12_context/10_custom_provider.py:47.")
        return 0

    print("NOT REPRODUCED: error message shape changed or framework was fixed.")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
