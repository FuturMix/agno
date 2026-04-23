"""
Repro #4 — MCPContextProvider.aclose() leaves the mcp stdio_client cancel
scope unclosed on the caller's task.

When asetup()/aclose() run on the same asyncio task (the exact pattern
cookbook/12_context/06_mcp_server.py uses), Python still surfaces:

    RuntimeError: Attempted to exit cancel scope in a different task
    than it was entered in

from mcp/client/stdio/__init__.py:189 / anyio/_backends/_asyncio.py:455.

The scope error fires during async-generator GC *after* aclose() returns,
not synchronously inside aclose(). In-process stderr capture doesn't see
it because it happens after our context manager exits. So this repro
runs the asetup/aclose sequence in a subprocess and inspects the
subprocess's stderr, which reliably captures the generator-cleanup noise
that the MCP client ends up shouting about.

Repro uses `command="python", args=["-c", "pass"]` — a valid command per
the provider allowlist that exits before any MCP handshake. This is the
minimum shape that triggers the bug without needing uvx / an installed
MCP server.

Run:
    python repro/context_main_regressions/04_mcp_aclose_scope_error.py

Exit 0 if the anyio scope error shows up, 1 otherwise.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

CHILD_SRC = textwrap.dedent(
    """
    import asyncio
    from agno.context.mcp import MCPContextProvider

    async def main():
        provider = MCPContextProvider(
            server_name="scope_repro",
            transport="stdio",
            command="python",
            args=["-c", "pass"],
            timeout_seconds=3.0,
        )
        try:
            await provider.asetup()
        finally:
            await provider.aclose()

    asyncio.run(main())
    """
).strip()


def main() -> int:
    py = Path(sys.executable)
    proc = subprocess.run(
        [str(py), "-c", CHILD_SRC],
        capture_output=True,
        text=True,
        timeout=30,
    )

    print(f"Child exit code: {proc.returncode}")
    combined = (proc.stderr or "") + "\n" + (proc.stdout or "")

    if "cancel scope" in combined:
        print()
        print("REPRODUCED: subprocess stderr contains the anyio cancel-scope error:")
        for line in combined.splitlines():
            if "cancel scope" in line or "Attempted to exit" in line:
                print(f"  {line}")
        return 0

    print()
    print("NOT REPRODUCED: no anyio scope error emitted.")
    print("---- subprocess stderr (first 2000 chars) ----")
    print((proc.stderr or "")[:2000])
    return 1


if __name__ == "__main__":
    sys.exit(main())
