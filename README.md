# castlist

Per-role model routing for Claude Code subagents: a cast list for your
agents, with each role cast to the model it actually needs.

A Claude Code plugin for matching each subagent role to the model it
actually needs — opus for planning and judgment-heavy review, sonnet for
everyday implementation, haiku for cheap, parallelizable lookups. The
mapping is native: it lives entirely in each agent's own `model:`
frontmatter field, not in a separate config file.

## Install

```bash
claude plugin install castlist --marketplace ernestomancebo/castlist
```

### Renamed from right-model

This plugin was called `right-model` through 0.2.x. The old name doesn't
migrate automatically, because the plugin and marketplace names changed.
If you installed it before:

```bash
claude plugin marketplace remove right-model-marketplace
claude plugin marketplace add ernestomancebo/castlist
claude plugin install castlist@castlist-marketplace
```

Then restart Claude Code. Commands are now `/castlist:setup`,
`/castlist:catch-up`, `/castlist:prune` and `/castlist:suggest`, and the
per-project role classification file is `.claude/castlist.json`.

## The convention

Every Claude Code subagent definition (`.claude/agents/<role>.md`) carries
a `model:` field — `haiku`, `sonnet`, `opus`, or `inherit`. Pin it by
scoring the role's task on three factors — cost of being wrong, judgment
calls vs. pattern-following, and how much context it needs at once:

- **0–1 → `haiku`** — cheap, parallelizable, low-stakes work.
- **2–3 → `sonnet`** — everyday implementation and integration work.
- **4–6 → `opus`** — architecture, judgment calls, high cost of being wrong.

The exact questions and point values live in one place:
`skills/suggest-model/SKILL.md`. `/castlist:suggest` and
`/castlist:setup` both apply that table interactively, so you don't
have to run it by hand.

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

- **`/castlist:suggest`** — ask about one task, get one recommended tier
  and the exact `model:` line to paste.
- **`/castlist:setup`** — apply the same quiz across a whole project:
  retrofit mismatches in existing `.claude/agents/*.md` roles (showing the
  proposed changes before touching anything), or, if none exist yet,
  bootstrap a starting set from this plugin's own example agents. Either
  way, roles that act on code (not pure read-only lookups) get a line
  recording this project's conventions — pointed at an existing
  `CLAUDE.md`/`AGENTS.md`, or captured by asking if neither exists.
  `setup` also runs `catch-up`'s and `prune`'s checks as a preflight, so
  re-running it later catches the same drift without a separate step.
  Convention lines are scoped to the role's job (a planner is pointed only
  at architecture and structure conventions, not coding style).
- **`/castlist:catch-up`** — on demand, re-examine existing roles
  against the project's *current* state: a role body whose procedural
  claim now contradicts an installed skill's own documented convention, a
  conventions pointer that's gone stale, a `CLAUDE.md`/`AGENTS.md` that
  showed up after a role was bootstrapped without one, and — report-only,
  never auto-applied — an installed skill whose own prose already
  recommends a model tier for a job one of your roles owns.
- **`/castlist:prune`** — check each role for concerns that belong to a
  different job (a planner carrying coding constraints, a verifier told to
  debug), and propose pruning or re-homing them. If a pruned concern has no
  owner, it proposes a new agent with a standard kebab-case name
  (`debugger`, `code-reviewer`, …). What each role may carry is defined in
  [`skills/prune/archetypes.md`](skills/prune/archetypes.md); a role it can't
  classify is asked about once and remembered in
  `.claude/castlist.json` (edit that file to reclassify; commit or ignore
  it as you prefer).

## The `PROCESS` log line

Record which model handled which round of a role's work, in whatever
format you already track that work — a PR description, a commit trailer,
an issue comment, your tracker's notes field. Free text is fine; the point
is just to leave evidence, so you can revisit your own split later with
data instead of guesswork. One ready-made format, if you want one:

```
PROCESS <role>: rounds=<n> duration=<min> model=<m>
```

## Relationship to dynamic per-dispatch routing

Some Claude Code skills choose a model per subagent dispatch, dynamically,
from prose heuristics, with no persistent per-role file —
`superpowers:subagent-driven-development`'s own "Model Selection" section
is the clearest example aimed at model choice itself (cheapest model that
fits each task, escalate a tier on repeated failure, most capable for
architecture and final review). That's the same judgment this plugin
teaches, arrived at independently, but mechanically different: it picks a
model fresh on every dispatch. Other skills apply similar per-invocation
judgment to different ends — `systematic-debugging`'s iterative loop, for
instance — but they aren't about model selection, so they're not a
comparison point here.

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

## Pairs with

[clearance](https://github.com/ernestomancebo/clearance): clear every pull
request before it lands, with review sweeps, feedback routing, merge order and
preflight checks for stacked and multi-repo PRs. Its review subagents fit this
plugin's `verifier` role.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for commit conventions and how releases
work.

## License

MIT
