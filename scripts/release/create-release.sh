#!/bin/bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

VERSION="${VERSION:-}"
if [ -z "$VERSION" ]; then
  echo -e "${RED}Error: VERSION is required (e.g. VERSION=X.Y.Z)${NC}" >&2
  exit 1
fi

TAG="$VERSION"
if [[ "$TAG" != v* ]]; then
  TAG="v$TAG"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

if ! command -v gh >/dev/null 2>&1; then
  echo -e "${RED}Error: gh CLI not found in PATH${NC}" >&2
  exit 1
fi

if ! gh auth status -h github.com >/dev/null 2>&1; then
  echo -e "${RED}Error: gh is not authenticated (run: gh auth login)${NC}" >&2
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo -e "${RED}Error: git working tree has uncommitted changes${NC}" >&2
  git status -sb || true
  exit 1
fi

CHANGELOG_FILE="docs/CHANGELOG.md"
VERSION_NO_V="${TAG#v}"

if [ ! -f "$CHANGELOG_FILE" ]; then
  echo -e "${RED}Error: missing ${CHANGELOG_FILE}${NC}" >&2
  exit 1
fi

if ! grep -Eq "^## \\[${VERSION_NO_V}\\]" "$CHANGELOG_FILE"; then
  echo -e "${RED}Error: changelog is missing release entry for ${VERSION_NO_V}${NC}" >&2
  echo "Add a section like: ## [${VERSION_NO_V}] - YYYY-MM-DD" >&2
  exit 1
fi

PYPROJECT_FILE="pyproject.toml"
if [ ! -f "$PYPROJECT_FILE" ]; then
  echo -e "${RED}Error: missing ${PYPROJECT_FILE}${NC}" >&2
  exit 1
fi

if ! grep -Eq "^version = \"${VERSION_NO_V}\"$" "$PYPROJECT_FILE"; then
  echo -e "${RED}Error: ${PYPROJECT_FILE} version must match ${VERSION_NO_V}${NC}" >&2
  echo "Update: [project].version = \"${VERSION_NO_V}\"" >&2
  exit 1
fi

for version_file in "src/xscanner/__init__.py" "src/xscanner/server/__init__.py"; do
  if [ ! -f "$version_file" ]; then
    echo -e "${RED}Error: missing ${version_file}${NC}" >&2
    exit 1
  fi
  if ! grep -Eq "^__version__ = \"${VERSION_NO_V}\"$" "$version_file"; then
    echo -e "${RED}Error: ${version_file} __version__ must match ${VERSION_NO_V}${NC}" >&2
    exit 1
  fi
done

STUDIO_PACKAGE_JSON="studio/package.json"
STUDIO_PACKAGE_LOCK="studio/package-lock.json"

if [ ! -f "$STUDIO_PACKAGE_JSON" ]; then
  echo -e "${RED}Error: missing ${STUDIO_PACKAGE_JSON}${NC}" >&2
  exit 1
fi

if [ ! -f "$STUDIO_PACKAGE_LOCK" ]; then
  echo -e "${RED}Error: missing ${STUDIO_PACKAGE_LOCK}${NC}" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo -e "${RED}Error: python3 is required to validate Studio package versions${NC}" >&2
  exit 1
fi

python3 - <<PY
import json

expected = "${VERSION_NO_V}"

with open("${STUDIO_PACKAGE_JSON}", "r", encoding="utf-8") as f:
    pkg = json.load(f)

pkg_version = str(pkg.get("version", "")).strip()
if pkg_version != expected:
    raise SystemExit(
        f"Error: {STUDIO_PACKAGE_JSON} version must match {expected} (found: {pkg_version!r})"
    )

with open("${STUDIO_PACKAGE_LOCK}", "r", encoding="utf-8") as f:
    lock = json.load(f)

lock_version = str(lock.get("version", "")).strip()
if lock_version != expected:
    raise SystemExit(
        f"Error: {STUDIO_PACKAGE_LOCK} version must match {expected} (found: {lock_version!r})"
    )

root_pkg = ((lock.get("packages") or {}).get("") or {})
root_version = str(root_pkg.get("version", "")).strip()
if root_version != expected:
    raise SystemExit(
        f"Error: {STUDIO_PACKAGE_LOCK} packages[''] version must match {expected} (found: {root_version!r})"
    )
PY

BRANCH="$(git branch --show-current)"
if [ "$BRANCH" != "main" ]; then
  echo -e "${RED}Error: releases must be created from main (current: ${BRANCH})${NC}" >&2
  exit 1
fi

git fetch origin main --tags

git pull --ff-only origin main

if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo -e "${RED}Error: tag already exists: ${TAG}${NC}" >&2
  exit 1
fi

echo -e "${BLUE}Creating tag:${NC} ${TAG}"
git tag "$TAG"
git push origin "$TAG"

echo -e "${BLUE}Creating GitHub release:${NC} ${TAG}"
# CI will build/push the release images for this tag.
gh release create "$TAG" --generate-notes --repo aXedras/xScanner

# Keep GitHub auto-generated notes, but prepend our curated changelog section.
VERSION="$VERSION" bash "$SCRIPT_DIR/sync-release-notes.sh"

echo -e "${GREEN}✓ Release created:${NC} ${TAG}"
