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

Read every `.claude/agents/<role>.md` found — name and current `model:`
(if the field is absent, treat current as `inherit`) — before asking
anything.

Ask the three `right-model:suggest-model` questions once for the whole
set: present all three questions for every role together, as one combined
form (one row per role, three answer columns), instead of walking the
whole quiz role by role. Score each role's answers against
`right-model:suggest-model`'s table and record: role name, file path,
current model, recommended model.

After every role has a recommendation, build a table:

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

1. Say plainly that no agents were found, and offer this starting menu
   (this plugin's own shipped examples): a **planning** role, an
   **implementation** role, a **verification** role, and a
   **lookup/research** role.
2. Ask the person to confirm the set: keep all four, drop any, rename
   any, or add roles the defaults don't cover.
3. Ask the `right-model:suggest-model` questions once for the whole
   confirmed set — one combined form covering every role — instead of
   walking the quiz role by role, and score each against its table.
4. Create `.claude/agents/<role-name>.md` for each one: base the `tools:`
   list and body on the matching shipped template under this plugin's
   `agents/` directory (nearest match if the role was renamed or added),
   set `description` to fit the role as the person described it, and set
   `model:` to the quiz's recommendation.
5. Report which files were created.

Never create a file before step 2's confirmation of the role set.
