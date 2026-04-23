# agno.context — main regression repros (2026-04-23)

Four standalone scripts that reproduce the bugs found while running
`cookbook/12_context/` end-to-end against main at SHA `b13788ac6`.

All scripts exit 0 if the bug reproduces, 1 if the bug is absent (fixed),
2 if the environment can't run the check.

## Matrix

| # | Script | Scope | External services | Bug |
|---|--------|-------|-------------------|-----|
| 1 | `01_slack_unconditional_post.py` | cookbook | none (static AST) | `05_slack.py` has no `SLACK_WRITE_CHANNEL` gate despite docstring + TEST_LOG claims |
| 2 | `02_custom_provider_typeerror.py` | framework | none | `ContextProvider._query_tool` wrapper unconditionally forwards `run_context`; legacy `aquery(self, question)` overrides raise `TypeError` |
| 3 | `03_mcp_astatus_lies.py` | framework | none (points at nonexistent binary) | `MCPContextProvider.astatus()` returns `ok=True` when `asetup()` silently failed |
| 4 | `04_mcp_aclose_scope_error.py` | framework | `uvx` + `mcp-server-time` | `MCPContextProvider.aclose()` raises `RuntimeError: Attempted to exit cancel scope in a different task than it was entered in` |

## Setup

```bash
cd /path/to/agno/.claude/worktrees/main-latest   # or any worktree at this branch

uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install -e ./libs/agno mcp slack-sdk
# repro #4 also needs: uv + uvx on PATH, Python 3.12 as the default
# `uv python install 3.12` (or set UV_PYTHON=3.12)
```

## Run everything

```bash
./cookbook/12_context/_regression_repros/run_all.sh
```

Or individually:

```bash
.venv/bin/python cookbook/12_context/_regression_repros/01_slack_unconditional_post.py
.venv/bin/python cookbook/12_context/_regression_repros/02_custom_provider_typeerror.py
.venv/bin/python cookbook/12_context/_regression_repros/03_mcp_astatus_lies.py
.venv/bin/python cookbook/12_context/_regression_repros/04_mcp_aclose_scope_error.py
```

## Provenance

- main SHA: `b13788ac6` (2026-04-23)
- Feature arrived in `main` via PR #7503 (`v2.6.0 → main`)
- Custom-provider backward-compat guard + 2 BC tests were dropped in
  PR #7639 (Ashpreet, rebased from closed PR #7637 by Mustafa)
- See `.context/e2e_context_results_2026_04_23.md` in this branch for
  the full E2E write-up.
