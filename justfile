# castlist dev commands. Run `just` to list them.

default:
    @just --list

# One-time: install the git hooks (pre-commit + commit-msg)
setup:
    pre-commit install

# Full deterministic checks, including the network `npx skills` check (what CI runs)
test *args:
    uv run --with pytest --with pyyaml pytest -q {{ args }}

# Same checks without the network test (what the pre-commit hook runs)
test-fast:
    uv run --with pytest --with pyyaml pytest -q -m "not network"

# Every pre-commit hook on every file (includes test-fast)
lint:
    pre-commit run --all-files

# Everything that should pass before opening a PR
check: lint test

# Ask Claude Code to validate the plugin manifest and components
validate:
    claude plugin validate .

# Run the evals against the real skills (costs tokens). e.g. `just eval --case clean-roles`
eval *args:
    uv run --with claude-agent-sdk python tests/evals/run.py {{ args }}

# Run only the eval cases affected by changes since a ref
eval-changed ref="origin/main":
    just eval --changed-from {{ ref }}

# Remove eval transcripts and caches
clean:
    rm -rf tests/evals/out .pytest_cache
    find . -name __pycache__ -not -path './.git/*' -prune -exec rm -rf {} +
