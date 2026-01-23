#!/bin/bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

# shellcheck source=./common.sh
source "$SCRIPT_DIR/common.sh"
preprod_guard_unknown_env_var_names
preprod_parse_args "$@"

ORIGIN="${ORIGIN:-latest}"

ORIGIN="$(preprod_normalize_origin "$ORIGIN")"

# Inform about platform behavior on Apple Silicon for pulled images.
if [ "$ORIGIN" != "local" ]; then
  arch="$(preprod_host_arch)"
  if { [ "$arch" = "arm64" ] || [ "$arch" = "aarch64" ]; } && [ -z "${DOCKER_DEFAULT_PLATFORM:-}" ]; then
    echo -e "${BLUE}Note:${NC} host arch is ${arch}; pulled GHCR images may be amd64-only." >&2
    echo -e "${BLUE}Tip:${NC} set DOCKER_DEFAULT_PLATFORM=linux/amd64 (or enable multi-arch images)." >&2
  fi
fi

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

# Warn for a very common pre-prod misconfiguration:
# If the Studio is opened from a remote browser, SUPABASE_PUBLIC_URL must not be localhost/127.0.0.1.
supabase_public_url="$(grep -E '^SUPABASE_PUBLIC_URL=' .env.preprod 2>/dev/null | tail -n 1 | cut -d= -f2- | tr -d '"' | tr -d "'")"
if [ -n "$supabase_public_url" ]; then
  case "$supabase_public_url" in
    http://localhost:*|https://localhost:*|http://127.0.0.1:*|https://127.0.0.1:*|http://0.0.0.0:*|https://0.0.0.0:*)
      echo -e "${BLUE}Warning:${NC} SUPABASE_PUBLIC_URL is set to ${supabase_public_url}." >&2
      echo -e "${BLUE}Why:${NC} Studio runs in your browser; remote browsers cannot reach localhost on the VM." >&2
      echo -e "${BLUE}Fix:${NC} set SUPABASE_PUBLIC_URL=http://<vm-ip-or-domain>:56321 in .env.preprod" >&2
      ;;
  esac
else
  echo -e "${BLUE}Warning:${NC} SUPABASE_PUBLIC_URL is not set in .env.preprod (Studio auth will fail)." >&2
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
