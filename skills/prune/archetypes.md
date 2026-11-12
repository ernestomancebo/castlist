# Role archetypes

The single source of truth for what each kind of role owns and must not
carry. `castlist:prune` reads this file; to support a new archetype, add
a row — no skill logic changes.

| Archetype | Owns | Must not carry | Names it matches | Tools shape |
|---|---|---|---|---|
| planning | the approach, files to touch, step order | code style or pattern rules, test commands, implementation detail, debugging | `planner` | Write at most; no Edit/Bash |
| implementing | code changes, running tests, style rules | re-planning or design decisions, judging readiness, review verdicts | `implementer` | Write, Edit, Bash |
| verifying | a correctness verdict against the stated goal | debugging or root-causing, editing or fixing, rewriting, planning | `verifier` | read-only plus Bash; never Write/Edit |
| lookup | cited factual answers | recommendations, plans, edits | `researcher` | Read, Grep, Glob only |

## Scoped convention pointers

A role that reads the project's conventions file reads only its own slice:

- planning: "Read `<path>` for this project's architecture and structure conventions only."
- implementing: "Read `<path>` for this project's style and pattern conventions only."
- verifying: "Read `<path>` for the standards to check this project's changes against only."
- lookup: no pointer.

## Standard names for a new role

Lowercase kebab-case role noun, matching the shipped files' `name:` and
filename: `debugger`, `code-reviewer`, `test-runner`, `security-auditor`.
