#!/bin/bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

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

# Guard against local modifications on the server.
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo -e "${RED}Error: git working tree has uncommitted changes${NC}" >&2
  git status -sb || true
  exit 1
fi

echo -e "${GREEN}✓ Pre-prod prerequisites OK${NC}"

echo -e "${BLUE}Repo:${NC} $REPO_ROOT"
echo -e "${BLUE}Branch:${NC} $(git branch --show-current)"
echo -e "${BLUE}HEAD:${NC} $(git rev-parse --short HEAD)"
