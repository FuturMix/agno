"""
Repro #3 — MCPContextProvider.astatus() reports ok=True when init failed.

asetup() catches subprocess / connection errors silently. astatus() then
returns `Status(ok=True, detail='mcp: <name> (<n> tools)')` even when n=0
or the session is dead. Any caller gating on status.ok gets a false green.

The easiest way to get asetup to "half-fail" is to point at a command that
starts but exits, or a command that doesn't exist on the path.

Run:
    python repro/context_main_regressions/03_mcp_astatus_lies.py

Exit 0 if astatus reports ok=True despite a failed asetup, 1 otherwise.
"""

from __future__ import annotations

import asyncio
import sys

from agno.context.mcp import MCPContextProvider


async def run() -> int:
    # python is on the command allowlist, so asetup gets past validation.
    # `-c "pass"` exits 0 immediately without performing any MCP handshake,
    # so the provider has no tools. This is the silent-init-failure path:
    # subprocess started, did nothing, closed.
    provider = MCPContextProvider(
        server_name="silent",
        transport="stdio",
        command="python",
        args=["-c", "pass"],
        timeout_seconds=3.0,
    )

    try:
        await provider.asetup()
        print("asetup() returned without raising")
    except Exception as exc:
        print(f"asetup() raised: {type(exc).__name__}: {exc}")

    status = await provider.astatus()
    print(f"astatus() = {status}")

    try:
        await provider.aclose()
    except Exception:
        pass

    # The bug: status.ok is True, but the underlying tool count is 0.
    # Parse the detail to extract tool count.
    if status.ok and "(0 tools)" in (status.detail or ""):
        print()
        print("REPRODUCED: astatus() reported ok=True with detail claiming a")
        print("connected provider, but tool count is 0 — init actually failed.")
        print("Callers gating on status.ok get a false green light.")
        return 0
    if status.ok:
        print()
        print("REPRODUCED (partial): astatus() reported ok=True for a provider")
        print(f"that won't serve any tools. detail: {status.detail}")
        return 0

    print("NOT REPRODUCED: astatus correctly reports failure.")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
