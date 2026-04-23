#!/usr/bin/env bash
# Runs the four context-provider repros and prints a summary.
#
# Usage:
#   ./repro/context_main_regressions/run_all.sh
#
# Requires the main-latest venv (or any venv with agno installed editable
# from libs/agno on this branch).

set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
REPRO_DIR="${REPO_ROOT}/cookbook/12_context/_regression_repros"
PY="${REPO_ROOT}/.venv/bin/python"

if [ ! -x "${PY}" ]; then
    echo "error: expected venv at .venv/bin/python in worktree root (${REPO_ROOT})"
    echo "Create one with: cd ${REPO_ROOT} && uv venv .venv --python 3.12 \\"
    echo "  && source .venv/bin/activate && uv pip install -e ./libs/agno mcp exa-py slack-sdk"
    exit 2
fi

# repros 03 + 04 spawn child processes and look up `python` / `uvx` on PATH.
# Put the venv's bin on PATH up front so child lookups resolve.
export PATH="${REPO_ROOT}/.venv/bin:${PATH}"

# Run each in a subshell and collect exit codes.
results=()
for script in 01_slack_unconditional_post.py \
              02_custom_provider_typeerror.py \
              03_mcp_astatus_lies.py \
              04_mcp_aclose_scope_error.py; do
    echo "============================================================"
    echo "=== Running: ${script}"
    echo "============================================================"
    "${PY}" "${REPRO_DIR}/${script}"
    rc=$?
    results+=("${rc}:${script}")
    echo
done

echo "============================================================"
echo "=== Summary"
echo "============================================================"
reproduced=0
not_repro=0
skipped=0
for entry in "${results[@]}"; do
    rc="${entry%%:*}"
    name="${entry#*:}"
    case "${rc}" in
        0) echo "  REPRODUCED     ${name}" ; reproduced=$((reproduced+1)) ;;
        1) echo "  not reproduced ${name}" ; not_repro=$((not_repro+1)) ;;
        2) echo "  SKIPPED        ${name} (env)" ; skipped=$((skipped+1)) ;;
        *) echo "  ERROR (rc=${rc}) ${name}" ;;
    esac
done
echo
echo "Reproduced: ${reproduced} / 4   not reproduced: ${not_repro}   skipped: ${skipped}"
