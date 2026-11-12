---
name: prune
description: Check each agent role for concerns that belong to a different job — a planner carrying coding constraints, a verifier told to debug — propose pruning or re-homing them, and propose a new agent when a pruned concern has no owner.
---

# Prune out-of-scope concerns from agent roles

Every question this skill asks goes through the AskUserQuestion tool, never
a plain-text form.

What each kind of role owns and must not carry is defined in
`archetypes.md` next to this file. Read it first; don't restate it here.

## 1. Discover

Glob for `.claude/agents/*.md` in the current project.

- **None found:** say so plainly ("No agent roles exist yet — nothing to
  prune.") and stop.
- **One or more found:** read each one's `name`, `description`, `tools:`,
  and full body, then continue.

## 2. Classify each role

Every role, read-only ones included. First hit wins, so results are stable
from run to run:

1. **Project override:** `.claude/right-model.json`, shaped
   `{"roles": {"<name>": "<archetype>"}}`. If the role is listed, use it.
2. **Name match:** the role's `name` matches a "Names it matches" entry in
   `archetypes.md`.
3. **Tools:** a hard constraint only — it can rule archetypes out (a role
   with no `Write`/`Edit`/`Bash` can't be implementing) but never decides
   on its own.
4. **Description:** compare against each remaining archetype's "owns"
   column. Exactly one clear match classifies it.
5. **Ambiguous, no match, or a tie:** ask which archetype the role is
   (options: the archetype names from `archetypes.md`; "Other" for a new
   one). After the confirmation in section 4, record the answer in
   `.claude/right-model.json` so later runs don't ask again. Never guess,
   and never propose an edit to a role whose archetype was guessed.

To reclassify a role later, edit `.claude/right-model.json`.

## 3. Scan for out-of-scope concerns

For each classified role, check its `description` and every body line
against that archetype's "must not carry" column. Each finding is one of:

- **Prune:** remove or trim the offending line. Quote it.
- **Re-home:** if an existing role of the owning archetype lacks that
  concern, add a second row moving the line there.
- **New agent:** if no existing role owns the concern, propose a new role
  named per "Standard names for a new role" in `archetypes.md`. A name that
  collides with an existing file is skipped and reported instead. Created
  only after confirmation: base `tools:` and body on the nearest shipped
  template under this plugin's `agents/` directory (a read-only archetype
  gets no `Write`/`Edit`), write `description` from the concern, and set
  `model:` by running `right-model:suggest-model` as a guided quiz in the
  confirmed pass, not before it.

Also check convention pointers: a pointer line on a planning, implementing,
or verifying role should be the scoped form from `archetypes.md`. An
unscoped "Read `<path>` for this project's conventions before starting"
line on one of those is itself a finding — propose the scoped form.

A role that makes none of these findings produces no row.

## 4. Build the table and confirm

| Role | Found | Proposed fix |
|---|---|---|

- **No rows and nothing to record:** say so plainly ("Every role stays in
  its lane — nothing to prune.") and stop. Do not ask for confirmation of
  an empty set.
- **One or more rows:** show the table, then ask apply or decline through
  AskUserQuestion. One confirmation for every row is sufficient.
  - **Confirmed:** apply each row, create any new agent (running its model
    quiz now), and write any new classification to
    `.claude/right-model.json`. Report which files changed and how.
  - **Declined:** change nothing, and say plainly that nothing was
    modified.

Never edit or create a file before this confirmation.

## Invoked as `right-model:setup`'s preflight

Skip this skill's own "1. Discover" (reuse `setup`'s role list) and its own
"4. Build the table and confirm" — hand sections 2 and 3's rows back to
`setup`, which merges them into its proposed-change table under its one
combined confirmation. Classification answers still get written to
`.claude/right-model.json` in that confirmed pass.

## Invoked for bootstrap

When `setup` has no roles yet, it calls this skill with the role
descriptions the person confirmed. Skip sections 1 and 4. For each
description, if it spans two archetypes ("plans and implements features"),
ask, via AskUserQuestion, whether to split it into two roles with standard
names; the shipped templates are already scoped, so they need no check.
Return the final role list to `setup`.
