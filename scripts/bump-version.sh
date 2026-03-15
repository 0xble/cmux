#!/usr/bin/env bash
set -euo pipefail

# Bump MARKETING_VERSION and CURRENT_PROJECT_VERSION in the Xcode project.
# Usage:
#   ./scripts/bump-version.sh                 # Bump fork minor (0.62.2-0xble.0.1.0 -> 0.62.2-0xble.0.2.0)
#   ./scripts/bump-version.sh patch           # Bump fork patch (0.62.2-0xble.0.1.0 -> 0.62.2-0xble.0.1.1)
#   ./scripts/bump-version.sh major           # Bump fork major (0.62.2-0xble.0.1.0 -> 0.62.2-0xble.1.0.0)
#   ./scripts/bump-version.sh 0.63.0          # Set new upstream base and reset fork suffix to 0.1.0
#   ./scripts/bump-version.sh 0.63.0-0xble.1.2.3

PROJECT_FILE="GhosttyTabs.xcodeproj/project.pbxproj"
RELEASE_REPO="${RELEASE_REPO:-0xble/cmux}"

if [[ ! -f "$PROJECT_FILE" ]]; then
  echo "Error: $PROJECT_FILE not found. Run from repo root." >&2
  exit 1
fi

# Get current versions
CURRENT_MARKETING=$(/usr/bin/grep -m1 'MARKETING_VERSION = ' "$PROJECT_FILE" | sed 's/.*= \(.*\);/\1/')
CURRENT_BUILD=$(/usr/bin/grep -m1 'CURRENT_PROJECT_VERSION = ' "$PROJECT_FILE" | sed 's/.*= \(.*\);/\1/')
MIN_BUILD="$CURRENT_BUILD"

echo "Current: MARKETING_VERSION=$CURRENT_MARKETING, CURRENT_PROJECT_VERSION=$CURRENT_BUILD"

# Keep Sparkle build numbers monotonic with the latest published stable appcast.
# If local build numbers have fallen behind due merges/rebases, auto-correct upward.
LATEST_RELEASE_BUILD="$(
  { curl -fsSL --max-time 8 "https://github.com/${RELEASE_REPO}/releases/latest/download/appcast.xml" 2>/dev/null || true; } \
    | sed -n 's#.*<sparkle:version>\([0-9][0-9]*\)</sparkle:version>.*#\1#p' \
    | head -n1
)"
if [[ "$LATEST_RELEASE_BUILD" =~ ^[0-9]+$ ]]; then
  if (( LATEST_RELEASE_BUILD > MIN_BUILD )); then
    MIN_BUILD="$LATEST_RELEASE_BUILD"
  fi
  echo "Latest release appcast build: $LATEST_RELEASE_BUILD"
else
  echo "Latest release appcast build: unavailable (continuing with local build baseline)"
fi

BASE_VERSION=""
FORK_MAJOR=0
FORK_MINOR=1
FORK_PATCH=0
HAS_FORK_SUFFIX="false"

parse_marketing_version() {
  local marketing="$1"

  if [[ "$marketing" =~ ^([0-9]+\.[0-9]+\.[0-9]+)-0xble\.([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
    BASE_VERSION="${BASH_REMATCH[1]}"
    FORK_MAJOR="${BASH_REMATCH[2]}"
    FORK_MINOR="${BASH_REMATCH[3]}"
    FORK_PATCH="${BASH_REMATCH[4]}"
    HAS_FORK_SUFFIX="true"
    return
  fi

  if [[ "$marketing" =~ ^([0-9]+\.[0-9]+\.[0-9]+)$ ]]; then
    BASE_VERSION="${BASH_REMATCH[1]}"
    FORK_MAJOR=0
    FORK_MINOR=1
    FORK_PATCH=0
    HAS_FORK_SUFFIX="false"
    return
  fi

  echo "Error: unsupported MARKETING_VERSION format: $marketing" >&2
  exit 1
}

format_marketing_version() {
  printf '%s-0xble.%s.%s.%s\n' "$BASE_VERSION" "$FORK_MAJOR" "$FORK_MINOR" "$FORK_PATCH"
}

parse_marketing_version "$CURRENT_MARKETING"

# Determine new marketing version
if [[ $# -eq 0 ]] || [[ "$1" == "minor" ]]; then
  if [[ "$HAS_FORK_SUFFIX" == "true" ]]; then
    FORK_MINOR=$((FORK_MINOR + 1))
  fi
  FORK_PATCH=0
  NEW_MARKETING="$(format_marketing_version)"
elif [[ "$1" == "patch" ]]; then
  if [[ "$HAS_FORK_SUFFIX" == "true" ]]; then
    FORK_PATCH=$((FORK_PATCH + 1))
  fi
  NEW_MARKETING="$(format_marketing_version)"
elif [[ "$1" == "major" ]]; then
  if [[ "$HAS_FORK_SUFFIX" == "true" ]]; then
    FORK_MAJOR=$((FORK_MAJOR + 1))
  else
    FORK_MAJOR=1
  fi
  FORK_MINOR=0
  FORK_PATCH=0
  NEW_MARKETING="$(format_marketing_version)"
elif [[ "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+-0xble\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  parse_marketing_version "$1"
  NEW_MARKETING="$(format_marketing_version)"
elif [[ "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  BASE_VERSION="$1"
  FORK_MAJOR=0
  FORK_MINOR=1
  FORK_PATCH=0
  NEW_MARKETING="$(format_marketing_version)"
else
  echo "Usage: $0 [version|minor|patch|major]" >&2
  echo "  version: upstream base like 0.63.0, or full fork version like 0.63.0-0xble.1.2.3" >&2
  echo "  minor: bump fork minor version (default)" >&2
  echo "  patch: bump fork patch version" >&2
  echo "  major: bump fork major version" >&2
  exit 1
fi

# Always increment build number, and never go backwards relative to published releases.
NEW_BUILD=$((MIN_BUILD + 1))

echo "New:     MARKETING_VERSION=$NEW_MARKETING, CURRENT_PROJECT_VERSION=$NEW_BUILD"

# Update project file
sed -i '' "s/MARKETING_VERSION = $CURRENT_MARKETING;/MARKETING_VERSION = $NEW_MARKETING;/g" "$PROJECT_FILE"
sed -i '' "s/CURRENT_PROJECT_VERSION = $CURRENT_BUILD;/CURRENT_PROJECT_VERSION = $NEW_BUILD;/g" "$PROJECT_FILE"

# Verify
UPDATED_MARKETING=$(/usr/bin/grep -m1 'MARKETING_VERSION = ' "$PROJECT_FILE" | sed 's/.*= \(.*\);/\1/')
UPDATED_BUILD=$(/usr/bin/grep -m1 'CURRENT_PROJECT_VERSION = ' "$PROJECT_FILE" | sed 's/.*= \(.*\);/\1/')

if [[ "$UPDATED_MARKETING" != "$NEW_MARKETING" ]] || [[ "$UPDATED_BUILD" != "$NEW_BUILD" ]]; then
  echo "Error: Version update failed!" >&2
  exit 1
fi

echo "Updated $PROJECT_FILE successfully."
