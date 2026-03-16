# LOCAL

Track intentional `local` branch drift relative to `upstream/main`.

Update this file whenever:

- cherry-picking upstream work
- carrying intentional fork-only behavior
- rebasing or resolving recurring conflicts
- leaving uncommitted local drift that should not be rediscovered later

## Baseline

- Comparison target: `upstream/main` from `git@github.com:manaflow-ai/cmux.git`
- Local branch: `local` at `73abacc2`
- Upstream head on 2026-03-16: `3b507d36`
- Merge base with upstream: `3b507d361fc35eef394da18fc5a52648ccd41622`
- Divergence on 2026-03-16: `local` is 7 commits ahead and 0 commits behind `upstream/main`

## Committed Drift On `local`

These commits exist on `local` and not on `upstream/main`:

- `a4f2c1c9` feat(shortcuts): add workspace pin shortcut
- `fffd2b5f` chore(release): restore fork update metadata
- `a4e426d7` fix(release): harden fork updater tooling
- `544f90e9` fix(release): load sparkle key from shell env
- `7d174c80` docs(repo): fix cmux deriveddata examples
- `79b6e7bb` fix(sidebar): avoid premature workspace title truncation

## Current Uncommitted Drift

- None. The rebuilt `local` branch intentionally drops the old portal, pane-tab-bar, and sidebar fallback drift.

## Rebase Notes

- `local` was hard-reset to `upstream/main` at `5776cd5d` on 2026-03-15, then rebuilt from scratch with only the fork release metadata and the workspace pin shortcut.
- Fork release drift is limited to:
  - `GhosttyTabs.xcodeproj/project.pbxproj`
  - `Resources/Info.plist`
  - `Sources/Update/UpdateDelegate.swift`
  - `scripts/build-sign-upload.sh`
  - `scripts/bump-version.sh`
  - `scripts/sparkle_generate_appcast.sh`
- Checked-in source defaults stay aligned with upstream updater URLs and keys, while the signed fork release path injects the `0xble/cmux` Sparkle feed and shared Sparkle key into release artifacts before signing.
- 2026-03-16: rebased `local` onto `upstream/main` at `3b507d36` (9 new upstream commits). Clean rebase, no conflicts. Upstream added pinned workspace sidebar drag ordering (#1503, #1505) which complements the fork's pin shortcut without overlap.
