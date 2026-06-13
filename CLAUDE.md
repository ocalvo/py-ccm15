# py-ccm15 — Project Directives

Python package (`py_ccm15`) to control Midea CCM15 data-converter modules.
The importable package lives in `ccm15/`; the version is declared **only** in
`pyproject.toml` (`[project] version`).

## Branch and PR Policy (release-please)

**Never commit directly to `main`.** All changes go through a feature branch and
a pull request. This repo uses
[release-please](https://github.com/googleapis/release-please)
(`.github/workflows/release-please.yml`, `release-please-config.json`,
`.release-please-manifest.json`) to bump `pyproject.toml`'s version and generate
`CHANGELOG.md` from merged PR titles.

1. `git checkout -b <short-slug>` — e.g. `feat/discovery-timeout`, `fix/xml-parse`.
2. Commit on that branch.
3. `gh pr create --base main --title "<type>: <description>" --body "..."`.
4. **Squash-merge** — GitHub uses the PR title as the commit subject, which
   release-please parses. (Plain merge commits with non-conforming messages are
   ignored.)
5. Release-please opens/updates a release PR bumping the version and
   `CHANGELOG.md`. Merging it tags `v<version>`, which triggers
   `main.yml` to publish to PyPI.

### PR titles must follow [Conventional Commits](https://www.conventionalcommits.org/)

```
<type>[optional scope][!]: <short description>
```

| Type | Version bump | Use for |
|------|--------------|---------|
| `feat` | minor (`0.1.2` → `0.2.0`) | New features, new public API |
| `fix` | patch (`0.1.2` → `0.1.3`) | Bug fixes |
| `feat!` / `fix!` / `BREAKING CHANGE:` footer | major (`0.1.2` → `1.0.0`) | Breaking API/behavior changes |
| `perf` | patch | Performance improvements |
| `refactor` | patch | Internal restructuring, no behavior change |
| `docs` | no release | Documentation only (README, CLAUDE.md) |
| `chore` | no release | Housekeeping, deps, formatting |
| `build` | no release | Build system, packaging |
| `ci` | no release | CI/CD config |
| `test` | no release | Test-only changes |

Examples:

```
feat: add async discovery of slave devices
fix(xml): handle empty response from CCM15 module
perf: reuse httpx client across polls
feat!: drop Python 3.7 support

BREAKING CHANGE: minimum supported runtime is now Python 3.9.
docs: document release-please PR title requirement
```

Rules:
- **Imperative mood** ("add", "fix", "remove" — not "added", "fixes").
- Under 72 characters.
- No generic titles ("update files", "misc changes").
- Split unrelated changes into separate PRs.
- **If a PR title doesn't match this grammar, release-please silently ignores
  it** and no release is cut.

## Versioning

Do **not** hand-edit the version in `pyproject.toml` — release-please owns it.
Bumps happen automatically from the Conventional Commit history when the release
PR is merged.
