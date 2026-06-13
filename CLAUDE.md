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

## Downstream consumer: Home Assistant core

**This library is a published dependency of Home Assistant core.** The `ccm15`
integration at `homeassistant/components/ccm15/` imports it directly:

- `coordinator.py` constructs `CCM15Device(host, port, timeout)` and calls
  `get_status_async()` and `async_set_state(ac_index, data)`.
- `climate.py` reads `CCM15SlaveDevice` fields (`temperature`,
  `temperature_setpoint`, `ac_mode`, `fan_mode`, `is_swing_on`, `error_code`).
- The version is pinned in `manifest.json` (`requirements: ["py_ccm15==X.Y.Z"]`)
  and mirrored into HA's generated `requirements_all.txt` /
  `requirements_test_all.txt`. `@ocalvo` is the codeowner.

Implications when changing this repo:

- **The public API is a contract.** Renaming/removing `CCM15Device`,
  `CCM15SlaveDevice`, `CCM15DeviceState`, their fields, or changing the
  `async_set_state` / `get_status_async` signatures **breaks HA core**. Treat
  such changes as `feat!`/`fix!` (major bump) and pair them with a
  homeassistant/core PR.
- **HA does not auto-upgrade.** Fixing a bug here only reaches HA users after a
  release **and** a follow-up homeassistant/core PR bumping the pin in
  `manifest.json` (target the `dev` branch). A fix sitting in a release nobody
  bumped to is invisible to HA users — e.g. issues reported against the
  integration may already be fixed in a newer release than HA pins.
- **Behavior decoded here, commanded in HA.** `CCM15SlaveDevice` decodes raw
  controller status; HA's `const.py` maps `HVACMode` <-> int command codes. A
  mode/fan-encoding mismatch between status and command surfaces as wrong
  behavior in HA (see issue #15), so keep the decode semantics stable and
  documented.

### homeassistant/core bump PRs must show the full version delta

A bump PR usually skips several releases (the pin lags the latest PyPI
version), so its description must cover **all** changes between the previously
pinned version and the new one — not just the headline fix that motivated the
bump. HA reviewers and changelog readers see only the PR description; an
undocumented fix in an intermediate release is effectively invisible.

Link the GitHub compare view rather than copying the changelog text — it is
self-updating and lets reviewers see every commit:

```
[`v0.1.2...v0.2.4`](https://github.com/ocalvo/py-ccm15/compare/v0.1.2...v0.2.4)
```

(both `v<old-pin>` and `v<new-version>` are real tags release-please pushes).
Then add a one- or two-sentence summary of only the **runtime-affecting**
changes (`feat`/`fix`/`perf`) with their upstream PR/issue links, and note
that the rest are `docs`/`chore`/`ci`/`test` with no runtime effect. Do not
paste the changelog entries verbatim.

## Versioning

Do **not** hand-edit the version in `pyproject.toml` — release-please owns it.
Bumps happen automatically from the Conventional Commit history when the release
PR is merged.
