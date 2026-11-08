---
name: setup
description: Walk through a project's agent roles — existing or not yet created — quiz each one with the suggest-model heuristic, and fix model: mismatches after confirmation.
---

# Set up model routing for this project

## 1. Discover

Glob for `.claude/agents/*.md` in the current project.

- **One or more files found:** go to "2. Retrofit existing roles."
- **No files found, or the directory doesn't exist:** go to "3. Bootstrap mode" (see below).

## 2. Retrofit existing roles

For each `.claude/agents/<role>.md` found:

1. Read its `name` and current `model:` (if the field is absent, treat
   current as `inherit`).
2. Call the Skill tool with `right-model:suggest-model` for this role to
   get a recommended tier.
3. Record: role name, file path, current model, recommended model.

After every role has been quizzed, build a table:

| Role | Current | Recommended | Change? |
|---|---|---|---|

Only rows where current ≠ recommended count as a proposed change.

- **No rows differ:** say so plainly ("Every role already matches its
  recommended tier — nothing to change.") and stop. Do not ask for
  confirmation of an empty set.
- **One or more rows differ:** show the full table, then ask for
  confirmation before touching anything. Confirming once for every
  proposed row at once is sufficient — per-row confirmation is not
  required.
  - **Confirmed:** edit each confirmed file's `model:` frontmatter line to
    the recommended tier. Report which files changed.
  - **Declined:** change nothing, and say plainly that nothing was
    modified.

Never edit a file before this confirmation step.

## 3. Bootstrap mode (no existing roles)

See Task 6.
