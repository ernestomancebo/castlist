---
name: setup
description: Walk through a project's agent roles — existing or not yet created — quiz each one with the suggest-model heuristic, capture this project's conventions for roles that act on code, and fix model: mismatches after confirmation.
---

# Set up model routing for this project

## 1. Discover

Glob for `.claude/agents/*.md` in the current project.

- **One or more files found:** go to "Capturing project conventions," then "2. Retrofit existing roles."
- **No files found, or the directory doesn't exist:** go to "Capturing project conventions," then "3. Bootstrap mode" (see below).

## Capturing project conventions

Applies only to a role whose `tools:` list includes `Write`, `Edit`, or
`Bash` — a role that can only `Read`, `Grep`, `Glob` (a pure lookup role,
like the shipped `researcher`) never needs this; its one behavior doesn't
change with project conventions.

Check for `CLAUDE.md`, `AGENTS.md`, or a similar project-instructions file
at the project root.

- **Found:** note its path. Every qualifying role gets one line appended
  to its body: "Read `<path>` for this project's conventions before
  starting." Point at the file; don't copy its contents in.
- **Not found:** ask once, covering every qualifying role together in one
  prompt: any architecture or structure rules a planning-type role should
  know, any style or pattern rules an implementing-type role should
  follow, any standards a reviewing-type role should check against. A
  role with a real answer gets it appended as one line to its body; a
  role answered "none" gets no line — don't add filler.

## 2. Retrofit existing roles

Read every `.claude/agents/<role>.md` found — name, current `model:` (if
the field is absent, treat current as `inherit`), `tools:`, and whether it
already carries a conventions line — before asking anything.

Ask the three `right-model:suggest-model` questions once for the whole
set: present all three questions for every role together, as one combined
form (one row per role, three answer columns), instead of walking the
whole quiz role by role. Score each role's answers against
`right-model:suggest-model`'s table and record: role name, file path,
current model, recommended model.

After every role has a recommendation, build a table:

| Role | Current | Recommended | Model change? | Conventions |
|---|---|---|---|---|

The Conventions column reads "add" when "Capturing project conventions"
produced a line for this role and the file doesn't already carry one,
"already present" when it does, and is blank for a role that doesn't
qualify. A row counts as a proposed change when the model would change,
a conventions line would be added, or both.

- **No rows propose a change:** say so plainly ("Every role already
  matches its recommended tier and conventions — nothing to change.") and
  stop. Do not ask for confirmation of an empty set.
- **One or more rows propose a change:** show the full table, then ask
  for confirmation before touching anything. Confirming once for every
  proposed row at once is sufficient — per-row confirmation is not
  required.
  - **Confirmed:** for each confirmed row, edit the `model:` frontmatter
    line to the recommended tier and/or append the captured conventions
    line to the body, whichever the row proposed. Report which files
    changed and how.
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
   set `description` to fit the role as the person described it, set
   `model:` to the quiz's recommendation, and append "Capturing project
   conventions"'s line to the body of every role whose `tools:` list
   qualifies.
5. Report which files were created.

Never create a file before step 2's confirmation of the role set.
