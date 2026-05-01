# LOCAL

Track intentional fork drift on `main` relative to `upstream/main`.

Update this file whenever:

- syncing or rebasing against upstream
- carrying intentional fork-only behavior
- rebasing or resolving recurring conflicts
- leaving uncommitted local drift that should not be rediscovered later

## Baseline

- Comparison target: `upstream/main` from `git@github.com:manaflow-ai/cmux.git`
- Maintained branch: `main` at `37dfd06d`
- Upstream head on 2026-05-01: `6e69f2c6`
- Merge base with upstream: `6e69f2c6b2c7fbf830b764ac936fb43e774111c1`
- Divergence on 2026-05-01: `main` is 16 commits ahead and 0 commits behind `upstream/main`

## Committed Drift On `main`

These commits exist on `main` and not on `upstream/main`:

- `95d9101a` chore(fork): sync upstream main
- `24793e24` fix(shortcuts): disable workspace pin without selection
- `500eccbd` fix(fork): restore upgrade flow after upstream sync
- `0136e0d0` feat(fork): add smoke verification
- `714777c9` fix(bin): use deterministic derived data path for upgrade installs
- `12229d5b` feat(fork): automate bin/upgrade with Developer ID signing and MacBook deploy
- `a2a5d1b9` fix(release): use Brian's Developer ID signing identity
- `ef834ca1` chore(bin): fix upgrade project path
- `b0f620c8` feat(fork): add bin/upgrade script for fork CLI
- `fd358d5d` docs(local): refresh fork drift notes
- `72dcffa8` fix(release): load sparkle key from shell env
- `d11c5c37` fix(release): harden fork updater tooling
- `e20ac693` chore(release): restore fork update metadata
- `c5f3d4c3` feat(shortcuts): add workspace pin shortcut
- `8f90df17` fix(cmux): prepare ghosttykit before release upgrade
- `37dfd06d` chore(fork): sync upstream main

## Current Uncommitted Drift

- None.

## Rebase Notes

- `main` was rebased onto `upstream/main` at `ca39ddb0` on 2026-04-08.
- `main` was merged with `upstream/main` at `6e69f2c6` on 2026-05-01.
- Fork release drift is limited to:
  - `GhosttyTabs.xcodeproj/project.pbxproj`
  - `Resources/Info.plist`
  - `Sources/Update/UpdateDelegate.swift`
  - `scripts/build-sign-upload.sh`
  - `scripts/bump-version.sh`
  - `scripts/sparkle_generate_appcast.sh`
- Checked-in source defaults now stay fork-branded for updater metadata, while runtime install/deploy still flows through `bin/upgrade` and `bin/smoke`.
- Dropped `docs(repo): fix cmux deriveddata examples` during the 2026-04-08 rebase because current `CLAUDE.md` already uses the better generic `App path:` pattern instead of a user-specific path.
- Dropped `fix(sidebar): avoid premature workspace title truncation` during the 2026-04-08 rebase because upstream already ships the behavior and changelog entry via `#1859`.
