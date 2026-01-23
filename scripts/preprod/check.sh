#!/bin/bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

ORIGIN="${ORIGIN:-latest}"

if [ -n "${XSCANNER_RELEASE_TAG:-}" ]; then
  echo -e "${RED}Error: XSCANNER_RELEASE_TAG must not be set manually${NC}" >&2
  echo -e "${BLUE}Why:${NC} pre-prod scripts derive it from ORIGIN to avoid mismatched labels." >&2
  echo -e "${BLUE}Fix:${NC} unset XSCANNER_RELEASE_TAG and use ORIGIN=main|local|release-x.y.z." >&2
  exit 2
fi

if ! command -v docker >/dev/null 2>&1; then
  echo -e "${RED}Error: docker not found in PATH${NC}" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo -e "${RED}Error: docker compose not available${NC}" >&2
  exit 1
fi

if ! command -v supabase >/dev/null 2>&1; then
  echo -e "${RED}Error: supabase CLI not found in PATH${NC}" >&2
  exit 1
fi

if [ ! -f ".env.preprod" ]; then
  echo -e "${RED}Error: missing .env.preprod${NC}" >&2
  echo "Create it from .env.preprod.example (do not commit secrets)." >&2
  exit 1
fi

# For release-based deploys and for ORIGIN=main (CI verification), we rely on GitHub.
if [ "$ORIGIN" != "local" ]; then
  if ! command -v gh >/dev/null 2>&1; then
    echo -e "${RED}Error: gh CLI not found in PATH (required for ORIGIN != local)${NC}" >&2
    exit 1
  fi

  if ! gh auth status -h github.com >/dev/null 2>&1; then
    echo -e "${RED}Error: gh is not authenticated (required for ORIGIN != main)${NC}" >&2
    echo "Run: gh auth login" >&2
    exit 1
  fi
fi

# Guard against local modifications only when we depend on git operations (release checkouts).
if [ "$ORIGIN" != "local" ] && [ "$ORIGIN" != "main" ]; then
  if ! git diff --quiet || ! git diff --cached --quiet; then
    echo -e "${RED}Error: git working tree has uncommitted changes${NC}" >&2
    echo "This is intentional for release-based pre-prod deploys." >&2
    echo "Fix: commit, stash, or deploy from a clean clone." >&2
    git status -sb || true
    exit 1
  fi
fi

echo -e "${GREEN}✓ Pre-prod prerequisites OK${NC}"

echo -e "${BLUE}Repo:${NC} $REPO_ROOT"
echo -e "${BLUE}Branch:${NC} $(git branch --show-current)"
echo -e "${BLUE}HEAD:${NC} $(git rev-parse --short HEAD)"
