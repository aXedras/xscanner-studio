#!/bin/bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

VERSION=${VERSION:-}
if [ -z "$VERSION" ] && [ $# -ge 1 ]; then
  VERSION="$1"
  shift
fi

if [ $# -gt 0 ]; then
  echo "Error: unknown arguments: $*"
  echo "Usage: VERSION=X.Y.Z $0" 1>&2
  exit 2
fi

if [ -z "$VERSION" ]; then
  echo "Error: VERSION is required (e.g. VERSION=X.Y.Z)"
  exit 1
fi

if [[ "$VERSION" == v* ]]; then
  TAG="$VERSION"
else
  TAG="v$VERSION"
fi
if [[ "$TAG" != v* ]]; then
  TAG="v$TAG"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

if ! command -v gh >/dev/null 2>&1; then
  echo -e "${RED}Error:${NC} gh CLI not found in PATH" >&2
  exit 1
fi

if ! gh auth status -h github.com >/dev/null 2>&1; then
  echo -e "${RED}Error:${NC} gh is not authenticated (run: gh auth login)" >&2
  exit 1
fi

CHANGELOG_FILE="docs/CHANGELOG.md"
if [ ! -f "$CHANGELOG_FILE" ]; then
  echo -e "${RED}Error:${NC} missing ${CHANGELOG_FILE}" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo -e "${RED}Error:${NC} python3 is required to extract changelog section" >&2
  exit 1
fi

# Extract the changelog section for VERSION (without leading 'v').
VERSION_NO_V="${TAG#v}"
CHANGELOG_SECTION="$(python3 - <<PY
import re
from pathlib import Path

version = "${VERSION_NO_V}"
text = Path("${CHANGELOG_FILE}").read_text(encoding="utf-8").splitlines()

start = None
for i, line in enumerate(text):
  if re.match(rf"^## \\[{re.escape(version)}\\](?:\\s|$)", line):
        start = i
        break

if start is None:
    raise SystemExit(f"Error: changelog section not found for {version}")

end = len(text)
for j in range(start + 1, len(text)):
  if re.match(r"^## \\[[^\\]]+\\](?:\\s|$)", text[j]):
        end = j
        break

section = "\n".join(text[start:end]).strip() + "\n"
print(section)
PY
)"

MARKER="<!-- xscanner-changelog:${TAG} -->"

resolve_previous_tag() {
  local current_tag="$1"
  local prev=""
  # Use version sort; pick the tag immediately before current_tag.
  prev="$(git tag --list 'v*' --sort=v:refname | awk -v cur="$current_tag" '
    $0==cur { print last; found=1 }
    { last=$0 }
    END { if (!found) exit 1 }
  ')" || true
  echo "$prev"
}

collect_contributors_with_links() {
  local current_tag="$1"
  local prev_tag="$2"

  if [ -z "$prev_tag" ]; then
    return 0
  fi

  gh api "repos/aXedras/xScanner/compare/${prev_tag}...${current_tag}" \
    --jq '.commits[] | [(.author.login // .committer.login // empty), .html_url] | @tsv' 2>/dev/null \
    | awk -F $'\t' 'NF >= 2 && $1 != "" && !seen[$1]++ { print $1 "\t" $2 }' \
    | sort -t $'\t' -k1,1
}

generate_github_notes() {
  local current_tag="$1"
  local prev_tag="$2"
  if [ -n "$prev_tag" ]; then
    gh api -X POST "repos/aXedras/xScanner/releases/generate-notes" \
      -f tag_name="$current_tag" \
      -f previous_tag_name="$prev_tag" \
      --jq .body
  else
    gh api -X POST "repos/aXedras/xScanner/releases/generate-notes" \
      -f tag_name="$current_tag" \
      --jq .body
  fi
}

# Fetch existing body (typically the auto-generated GitHub notes).
EXISTING_BODY="$(gh release view "$TAG" --repo aXedras/xScanner --json body --jq .body 2>/dev/null || true)"

PREV_TAG="$(resolve_previous_tag "$TAG")"
CONTRIBUTORS_WITH_LINKS="$(collect_contributors_with_links "$TAG" "$PREV_TAG" || true)"

# Prefer GitHub's generated notes (stable + avoids losing auto-notes on repeated syncs).
GITHUB_NOTES_BODY="$(generate_github_notes "$TAG" "$PREV_TAG" 2>/dev/null || true)"
if [ -z "$GITHUB_NOTES_BODY" ]; then
  GITHUB_NOTES_BODY="$EXISTING_BODY"
fi

TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT

{
  echo "$MARKER"
  echo "## Changelog"
  echo
  printf "%s" "$CHANGELOG_SECTION"
  echo

  if [ -n "$CONTRIBUTORS_WITH_LINKS" ]; then
    echo "## Contributors"
    echo
    while IFS=$'\t' read -r login url; do
      [ -z "$login" ] && continue
      [ -z "$url" ] && continue
      echo "* @$login in $url"
    done <<<"$CONTRIBUTORS_WITH_LINKS"
    echo
  fi

  echo "---"
  echo
  echo "## GitHub Notes"
  echo
  # Preserve existing body as-is.
  printf "%s\n" "$GITHUB_NOTES_BODY"
} >"$TMP_FILE"

echo -e "${BLUE}Updating GitHub release notes:${NC} ${TAG}"

gh release edit "$TAG" --repo aXedras/xScanner --notes-file "$TMP_FILE"

echo -e "${GREEN}✓ Release notes updated:${NC} ${TAG}"
