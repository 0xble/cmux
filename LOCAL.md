# LOCAL

Track intentional fork drift on `main` relative to `upstream/main`.

Update this file whenever:

- syncing or rebasing against upstream
- carrying intentional fork-only behavior
- rebasing or resolving recurring conflicts
- leaving uncommitted local drift that should not be rediscovered later

## Baseline

- Comparison target: `upstream/main` from `git@github.com:manaflow-ai/cmux.git`
- Maintained branch: `main` at `63e0a85b`
- Upstream head on 2026-04-08: `ca39ddb0`
- Merge base with upstream: `ca39ddb07803e1eb2582b5ea6a3436871f4337c2`
- Divergence on 2026-04-08: `main` is 11 commits ahead and 0 commits behind `upstream/main`

## Committed Drift On `main`

These commits exist on `main` and not on `upstream/main`:

- `65bbbba6` feat(shortcuts): add workspace pin shortcut
- `428c10b8` chore(release): restore fork update metadata
- `e3592c0a` fix(release): harden fork updater tooling
- `125ea59f` fix(release): load sparkle key from shell env
- `6d7ba306` docs(local): refresh fork drift notes
- `4dded084` feat(fork): add bin/upgrade script for fork CLI
- `bfcbadc8` chore(bin): fix upgrade project path
- `84f75a4f` fix(release): use Brian's Developer ID signing identity
- `ac4d4e0f` feat(fork): automate bin/upgrade with Developer ID signing and MacBook deploy
- `30bd4770` fix(bin): use deterministic derived data path for upgrade installs
- `63e0a85b` feat(fork): add smoke verification

## Current Uncommitted Drift

- `Sources/cmuxApp.swift`: remove conflict leftovers so the rebased fork builds again.
- `bin/upgrade`: source managed signing env instead of hardcoding an empty keychain password.

## Rebase Notes

- `main` was rebased onto `upstream/main` at `ca39ddb0` on 2026-04-08.
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
