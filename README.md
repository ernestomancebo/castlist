# right-model

A Claude Code plugin for matching each subagent role to the model it
actually needs — opus for planning and judgment-heavy review, sonnet for
everyday implementation, haiku for cheap, parallelizable lookups. The
mapping is native: it lives entirely in each agent's own `model:`
frontmatter field, not in a separate config file.

## Install

```bash
claude plugin install right-model --marketplace ernestomancebo/right-model
```

## The convention

Every Claude Code subagent definition (`.claude/agents/<role>.md`) carries
a `model:` field — `haiku`, `sonnet`, `opus`, or `inherit`. Pin it based on
three questions about the role's task:

| Question | Answer | Points |
|---|---|---|
| How costly is a wrong answer? | low / medium / high | 0 / 1 / 2 |
| Judgment calls, or pattern-following? | pattern-following / judgment | 0 / 2 |
| How much context does it need at once? | single file(s) / module-feature / whole repo-history | 0 / 1 / 2 |

Sum the three scores:

- **0–1 → `haiku`** — cheap, parallelizable, low-stakes work.
- **2–3 → `sonnet`** — everyday implementation and integration work.
- **4–6 → `opus`** — architecture, judgment calls, high cost of being wrong.

`/right-model:suggest` and `/right-model:setup` both apply this same table
interactively, so you don't have to run it by hand.

## Example agents

Four generic roles ship as starting points — copy, rename, and adapt them:

| Agent | Model | Job |
|---|---|---|
| `planner` | opus | Turns a task description into a short written plan |
| `implementer` | sonnet | Implements a small, well-specified task |
| `verifier` | opus | Reviews a change for correctness, read-only |
| `researcher` | haiku | Answers one factual question about the repo, read-only |

If a project already has its own agent with one of these names, Claude
Code resolves the project-level one over this plugin's — that's expected
behavior, not a conflict to fix.

## Interactive commands

- **`/right-model:suggest`** — ask about one task, get one recommended tier
  and the exact `model:` line to paste.
- **`/right-model:setup`** — apply the same quiz across a whole project:
  retrofit mismatches in existing `.claude/agents/*.md` roles (showing the
  proposed changes before touching anything), or, if none exist yet,
  bootstrap a starting set from this plugin's own example agents.

## The `PROCESS` log line

Append `PROCESS <role>: rounds=<n> duration=<min> model=<m>` wherever you
already track a role's work — a PR description, a commit trailer, an issue
comment, your tracker's notes field. This plugin doesn't assume which; the
point is just to leave evidence of which model handled which round, so you
can revisit your own split later with data instead of guesswork.

## Relationship to dynamic per-dispatch routing

Some Claude Code skills already choose a model per subagent dispatch,
dynamically, from prose heuristics — notably
`superpowers:subagent-driven-development`'s own "Model Selection" section
(cheapest model that fits each task, escalate a tier on repeated failure,
most capable for architecture and final review). That's the same judgment
this plugin teaches, arrived at independently, but mechanically different:
it picks a model fresh on every dispatch, with no persistent named role
file.

This plugin is for the other case: a **fixed, recurring** set of named
roles — the same planner/implementer/verifier you invoke call after call
for an ongoing workflow — where it's worth writing the model choice down
once, in a file, instead of re-deriving it on every dispatch. Use both:
a one-off plan executed through `subagent-driven-development` doesn't need
this plugin's agent files; a project with its own standing cast of roles
benefits from having them written down.

## Always use the bare tier alias

Never pin a dated model ID (`claude-sonnet-4-5`, etc.) — always the bare
alias (`sonnet`). Claude Code resolves the alias to the latest model in
that tier automatically, so a new Anthropic release needs no change here
at all.

## License

MIT
