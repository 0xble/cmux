# Maintenance

## Background

Maintained fork: `0xble/cmux` of `manaflow-ai/cmux`; maintained and upstream
branch `main`. This temporary isolated checkout is remote-only, not a runtime
canonical checkout. Accepted baseline: `f42270ec5691abaa4acdf02729d4caef434102cb`.
Publish only to `origin`; never push upstream.

## Preserve

- Fork workspace-pin shortcut safety and fork release/update metadata.
- Fork update/smoke source wiring is recorded here; installation, signing,
deployment, and runtime activation require separate authorization and proof.

## Active patches

### CMUX-001: `feat(shortcuts): add workspace pin shortcut`

- **Status:** Active; includes `67840da1`, `a198e93f`.
- **Behavior:** workspace pin remains available but is disabled without a selection.
- **Surfaces:** `Sources/AppDelegate.swift`, `Sources/ContentView.swift`,
  `Sources/KeyboardShortcutSettings.swift`, `Sources/cmuxApp.swift`, tests.
- **Upstream issue:** None after checked 2026-09-09.
- **Upstream PR:** None after checked 2026-09-09.
- **Regression:** GitHub Actions unit proof for shortcut-routing/workspace tests passes.
- **Rollback:** revert the two listed commits together, retaining any independent upstream equivalent.
- **Retire when:** upstream release supplies the behavior and its unit proof passes.

### CMUX-002: `chore(release): restore fork update metadata`

- **Status:** Active; `c71c5240`, `cc2e740f`, `b08b6add`, `9f83d7eb`, `f75829f1`.
- **Behavior:** fork updater metadata, signing-key environment loading, and release preparation stay fork-specific.
- **Surfaces:** project file, `scripts/build-sign-upload.sh`, `scripts/bump-version.sh`,
  `scripts/sparkle_generate_appcast.sh`.
- **Upstream issue:** None after checked 2026-09-09.
- **Upstream PR:** None after checked 2026-09-09.
- **Regression:** release-pretag guard and CI build complete without publishing.
- **Rollback:** revert this provenance set; do not publish or sign as rollback.
- **Retire when:** fork distribution metadata is explicitly retired or upstream replacement is adopted and verified.

### CMUX-003: `feat(fork): add bin/upgrade script for fork CLI`

- **Status:** Active; `9144f254`, `2b1c0d66`, `5d55ec2c`, `f55f5e23`, `c029979d`, `caf4fd66`.
- **Behavior:** fork upgrade and smoke wiring remains source-only and portable.
- **Surfaces:** `bin/upgrade`, `bin/smoke`, `README.md`, release scripts.
- **Upstream issue:** None after checked 2026-09-09.
- **Upstream PR:** None after checked 2026-09-09.
- **Regression:** `bash -n bin/upgrade bin/smoke`; CI build passes; no installer run.
- **Rollback:** revert this set and remove only its source wiring.
- **Retire when:** an authorized disposition retires the fork update path.

## Update

Every maintenance run fetches `origin` and the latest `upstream/main`, reconciles
`main`, preserves only these active records, and completes the declared proof
before authorized publication. Immediately before `Updated` or `Already current`,
fetch upstream again and prove no upstream-only commits; otherwise report
`Blocked` with stage, refs, and evidence. Contract changes accompany every patch
change or retirement; missing coverage blocks publication.

## Verify

```text
bash -n bin/upgrade bin/smoke
git diff --check
# GitHub Actions: focused shortcut/workspace units and build, no runtime launch
git rev-list --left-right --count upstream/main...main
```

Require a fresh final fetch with zero upstream-only commits and local/`origin`
SHA parity after authorized publication. Installation, signing, deployment, and
runtime SHA proof are separate stages.