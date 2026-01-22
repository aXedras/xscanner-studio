#!/bin/bash

set -euo pipefail

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

STRICT=0
if [[ "${1:-}" == "--strict" ]]; then
  STRICT=1
fi

if ! command -v gh >/dev/null 2>&1; then
  if [ "$STRICT" -eq 1 ]; then
    echo -e "${RED}Error: gh CLI not installed; cannot verify CI status${NC}" >&2
    exit 1
  fi
  echo -e "${YELLOW}Warning: gh CLI not installed; skipping CI verification${NC}" >&2
  exit 0
fi

HEAD_SHA="$(git rev-parse HEAD)"

set +e
MATCHED_CONCLUSION="$(gh api \
  "repos/aXedras/xScanner/actions/workflows/ci.yml/runs?branch=main&per_page=50" \
  --jq ".workflow_runs[] | select(.head_sha == \"$HEAD_SHA\") | .conclusion" \
  2>/dev/null | head -n 1)"
GH_EXIT=$?
set -e

if [ "$GH_EXIT" -ne 0 ] || [ -z "${MATCHED_CONCLUSION:-}" ]; then
  if [ "$STRICT" -eq 1 ]; then
    echo -e "${RED}Error: cannot verify CI for sha ${HEAD_SHA}${NC}" >&2
    echo "Ensure gh is authenticated and the workflow run exists for this commit." >&2
    exit 1
  fi
  echo -e "${YELLOW}Warning: cannot verify CI for sha ${HEAD_SHA}; continuing${NC}" >&2
  exit 0
fi

if [ "$MATCHED_CONCLUSION" != "success" ]; then
  echo -e "${RED}Error: CI for sha ${HEAD_SHA} is not successful (conclusion=${MATCHED_CONCLUSION})${NC}" >&2
  exit 1
fi

echo -e "${GREEN}✓ CI successful for sha:${NC} ${HEAD_SHA}"
