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
- To catch problems before CI, run `pre-commit install` once (needs
  [pre-commit](https://pre-commit.com) and Go for `yamlfmt`). It checks JSON, formats YAML,
  lints workflow files on commit, and applies the same commit-message
  rules (conventional type, 50-character subject) locally.

## Running tests

```bash
uv run --with pytest --with pyyaml pytest
```

This runs the deterministic repo checks: every skill, command, and agent
frontmatter parses as strict YAML, the plugin and marketplace versions agree
with the release manifest, the starter templates in
`skills/prune/archetypes.md` match `agents/*.md`, and every `castlist:<name>`
and `section N` reference resolves. CI runs the same command, including one
check that `npx skills` lists every skill; `pre-commit` runs everything except
that network check (`-m "not network"`).
