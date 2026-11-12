# Contributing

Releases are automated with [release-please](https://github.com/googleapis/release-please).
Never edit the version in `.claude-plugin/plugin.json` or
`.claude-plugin/marketplace.json` by hand.

- **PR titles must be conventional commits** — `type: subject` or
  `type(scope): subject`, with `type` one of `feat`, `fix`, `perf`, `revert`,
  `docs`, `chore`, `ci`, `test`, `style`, `build`, `refactor` — and **at most
  50 characters**. A title that fails either rule blocks the PR.
- PRs are squash-merged, so the PR title becomes the commit on `main`.
- On every push to `main`, release-please keeps one release PR open. Merging it
  bumps both manifests (`feat` → minor, `fix` → patch, while below 1.0.0
  breaking changes also bump minor), tags `vX.Y.Z`, and publishes a GitHub
  Release. The release notes live there; there is no changelog file.
- `docs`, `chore`, `ci`, `test`, `style`, `build`, and `refactor` PRs stay out
  of the notes. To keep any other PR out, add the `skip-changelog` label
  **before merging**.
- To catch problems before CI, run `just setup` once (needs [just](https://just.systems),
  [uv](https://docs.astral.sh/uv/), [pre-commit](https://pre-commit.com) and Go for
  `yamlfmt`). The hooks check JSON, format YAML, lint workflow files, run the
  fast repo checks on commit, and apply the same commit-message rules
  (conventional type, 50-character subject) locally.

## Commands

Run `just` to list every command. The ones you'll use:

| Command | What it does |
|---|---|
| `just setup` | install the git hooks (once) |
| `just test` | all deterministic repo checks, including the network `npx skills` check (what CI runs) |
| `just test-fast` | the same without the network check (what the pre-commit hook runs) |
| `just check` | every pre-commit hook plus the full tests; run before opening a PR |
| `just validate` | `claude plugin validate .` |
| `just eval ...` | run the evals against the real skills (costs tokens) |
| `just eval-changed` | run only the eval cases affected by your changes |

## Running tests

`just test` runs the deterministic repo checks: every skill, command, and
agent frontmatter parses as strict YAML, the plugin and marketplace versions
agree with the release manifest, the starter templates in
`skills/prune/archetypes.md` match `agents/*.md`, and every `castlist:<name>`
and `section N` reference resolves. CI runs the same command, including one
check that `npx skills` lists every skill.

## Running evals

The fixtures under `tests/fixtures/` are scratch projects with seeded defects.
`just eval` drives the real skills against them through the Claude Agent SDK,
answers the skills' questions from scripted rules, and grades the files they
leave behind.

```bash
just eval --case clean-roles   # one case
just eval-changed              # only cases affected by your changes vs origin/main
```

- It **costs tokens** on your own Claude login (or `ANTHROPIC_API_KEY`).
  Defaults: model `haiku` (`EVAL_MODEL` overrides), 3 repeats per case with 2
  needed to pass, `$1` per run and `$10` in total (`--budget`, `--max-total-usd`).
- It uses the `claude` on your `PATH`; `EVAL_CLAUDE_CLI` or `--cli` points at a
  different one. Without any, the SDK's bundled copy is used.
- Each case declares the files it exercises (`covers` in its `expected.json`),
  which is how `just eval-changed` picks cases.
- Transcripts and per-run results land in `tests/evals/out/` (git-ignored).

**In CI**, the `evals` workflow runs automatically on pull requests that touch
the assets the evals exercise (`skills/`, `commands/`, `agents/`,
`tests/evals/`, `tests/fixtures/`) and runs only the affected cases, 2 repeats
each. It authenticates with the `CLAUDE_CODE_OAUTH_TOKEN` repo secret (create
one with `claude setup-token`, then `gh secret set CLAUDE_CODE_OAUTH_TOKEN`),
and skips with a notice when the secret isn't available, as on fork PRs. It is
not a required check. You can also start it by hand from the Actions tab
(`workflow_dispatch`) with specific cases. Transcripts are uploaded as the
`eval-transcripts` artifact for 7 days.
