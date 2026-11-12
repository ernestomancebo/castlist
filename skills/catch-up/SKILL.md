---
name: catch-up
description: Re-examine this project's existing .claude/agents/*.md roles against the project's current state — installed skills and CLAUDE.md/AGENTS.md — reconcile anything that's drifted, and flag any installed skill whose own prose already recommends a model tier for a role's job.
---

# Catch up on drift in existing agent roles

## 1. Discover

Glob for `.claude/agents/*.md` in the current project.

- **None found:** say so plainly ("No agent roles exist yet — nothing to catch up on.") and stop.
- **One or more found:** read each one's `name`, `description`, `tools:`, and full body, then continue.

## 2. Qualifying-role checks

Apply only to a role whose `tools:` list includes `Write`, `Edit`, or
`Bash` — the same filter `right-model:setup`'s conventions-capture step
uses. A pure read-only role never carries a conventions line and makes no
procedural claims, so it has nothing in this section to drift.

For each qualifying role:

**a. Convention pointer or inline text, against the project's actual files:**

- If the body contains a line of the form "Read `<path>` for this
  project's conventions before starting," check whether `<path>` still
  exists.
  - **Missing, but a different `CLAUDE.md`/`AGENTS.md`-style file now
    exists at the project root:** propose repointing the line at the new
    path — the convention didn't disappear, it just moved or got renamed.
  - **Missing, and no such file exists at all:** propose falling back to
    `right-model:setup`'s own "ask once for this project's conventions"
    question for this role (its "Capturing project conventions," Not-found
    path). Replace the stale pointer line with whatever that question
    produces — a fresh inline convention line for a real answer, or
    remove the line entirely if the answer is "none." Don't just delete
    the stale line without asking.
- If the body instead carries inline convention text (no pointer line),
  check whether a `CLAUDE.md`, `AGENTS.md`, or similar project-instructions
  file now exists at the project root (it didn't when this role was
  created, or it would have gotten a pointer instead).
  - **Found:** propose replacing the inline text with the pointer line,
    "Read `<path>` for this project's conventions before starting,"
    consolidating on the new file as the one source of truth.

**b. Procedural claims, against installed skills' own conventions:**

- From the role's own `description` and body, note what domain it works
  in (planning, implementing, reviewing, etc.) and any concrete procedural
  claim it makes — a file path it writes to, a command it runs, a
  convention it asserts as fact.
- Narrow using the role's own `description` as the query: keep only
  installed skills whose own `description` shares a concrete noun or verb
  with it (e.g., both mention "plan," "review," "test," "implement") —
  not every installed skill, which can easily number in the hundreds and
  mostly share no domain with any given role. If none clear this test,
  there's nothing to compare for this role — move on.
- Within that narrowed set, check whether any skill's own documented
  convention contradicts the role's procedural claim: the same
  procedural axis (same file-path purpose, same named-command purpose)
  with a different, mutually exclusive value (e.g., a role says
  "write the plan to `PLAN.md`" while an installed planning skill's own
  documented save location is a different path). A skill that's merely
  more specific or touches a related but different concern isn't a
  contradiction, and neither is silence — a role that doesn't mention a
  convention at all isn't flagged; only a claim that's actually
  contradicted is.
  - **Contradiction found:** propose the corrected line, quoting the
    installed skill's own documented convention as the reason.
  - **More than one skill in the narrowed set documents a different
    answer on the same axis, and they disagree with each other** (not
    just with the role): don't silently pick one to quote. Name all of
    them and ask the project owner which is actually in effect, instead
    of proposing a single corrected line.

## 3. All-roles check — model tier overlap, report only

For every role, qualifying or not: narrow using the role's own
`description` as the query — the same noun/verb-overlap test as section
2b — to the skills currently available to this session whose own prose
recommends a model tier (`haiku`/`sonnet`/`opus`, or wording like "most
capable model," "cheapest model that fits") for a responsibility that
overlaps this role's own stated job. Within that narrowed set, a genuine
recommendation is prescriptive and dispatch-oriented — it tells the
reader which model to use for a job ("dispatch this as opus," "use the
cheapest model that fits") — not a descriptive or historical mention of
a real tier name ("this runs on opus" today), and not an incidental,
unrelated use of a model-tier word (e.g., "haiku" meaning the poetry
form is not a model-tier recommendation).

For each overlap found, report it — name the skill, quote or summarize
its model-tier guidance, name the role and its own `model:` value — and
say plainly that right-model doesn't override another skill's own
mechanism, so which one applies for this responsibility is the project
owner's call.

This category never produces a proposed edit. Agreement or disagreement
between the two sources doesn't matter — a finding here is always
reported, never auto-resolved, and never blocks or gates section 4.

## 4. Build the table and confirm

Collect every proposal from step 2 into one table:

| Role | Found | Proposed fix |
|---|---|---|

- **No rows:** say so plainly ("No stale conventions or contradicted
  procedural claims found.") and stop. Do not ask for confirmation of an
  empty set.
- **One or more rows:** show the full table, then ask for confirmation
  before touching anything. Confirming once for every proposed row at
  once is sufficient — per-row confirmation is not required.
  - **Confirmed:** apply each confirmed row's proposed fix to its file.
    Report which files changed and how.
  - **Declined:** change nothing, and say plainly that nothing was
    modified.

Never edit a file before this confirmation step.

Then, regardless of the table above, list every finding from section 3 as
its own separate report — these are never gated behind the confirmation,
since nothing about them is ever written.

## Invoked as `right-model:setup`'s preflight

When called from `setup` rather than standalone, skip this skill's own
"1. Discover" (reuse `setup`'s own role discovery) and its own "4. Build
the table and confirm" — hand section 2's findings back to `setup`
instead, which merges those into its own proposed-change table and asks
for one combined confirmation alongside its model-tier proposals.
Section 3's findings get reported on their own, exactly as in
standalone use, after that combined confirmation (or `setup`'s
no-roles/bootstrap path) is resolved.
