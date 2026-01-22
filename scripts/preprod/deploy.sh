#!/bin/bash

set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ORIGIN="${ORIGIN:-latest}"
MODE="${MODE:-}"

if [ -z "$MODE" ]; then
	if [ "$ORIGIN" = "main" ]; then
		MODE="cloud"
	else
		MODE="full"
	fi
fi

echo -e "${BLUE}🚀 Pre-prod deploy${NC}"

if [ "$MODE" != "cloud" ] && [ "$MODE" != "full" ]; then
	echo -e "${RED}Error: invalid MODE (expected cloud|full): ${MODE}${NC}" >&2
	exit 1
fi

if [ "$ORIGIN" = "main" ]; then
	echo -e "${BLUE}Origin:${NC} main (deploy from main HEAD, local build)"
	echo -e "${BLUE}Mode:${NC} ${MODE}"

	ORIGIN=main bash "$SCRIPT_DIR/check.sh"
	bash "$SCRIPT_DIR/update-main.sh"
	bash "$SCRIPT_DIR/verify-ci-main.sh" --strict
	bash "$SCRIPT_DIR/database-start.sh"
	ORIGIN=main MODE="$MODE" bash "$SCRIPT_DIR/up.sh"
	bash "$SCRIPT_DIR/health.sh"

	echo -e "${GREEN}✓ Deploy complete${NC}"
	exit 0
fi

TAG=""
if [ "$ORIGIN" = "latest" ]; then
	TAG="$(gh release view --repo aXedras/xScanner --json tagName --jq .tagName)"
elif [[ "$ORIGIN" == release-* ]]; then
	TAG="${ORIGIN#release-}"
	if [[ "$TAG" != v* ]]; then
		TAG="v$TAG"
	fi
else
	echo -e "${RED}Error: invalid ORIGIN (expected main|latest|release-x.y.z): ${ORIGIN}${NC}" >&2
	exit 1
fi

echo -e "${BLUE}Origin:${NC} ${ORIGIN}"
echo -e "${BLUE}Mode:${NC} ${MODE}"
echo -e "${BLUE}Release tag:${NC} ${TAG}"

ORIGIN="$ORIGIN" bash "$SCRIPT_DIR/check.sh"

ORIGINAL_REF="$(git symbolic-ref --quiet --short HEAD || true)"
git fetch --tags origin
git checkout "$TAG"

bash "$SCRIPT_DIR/verify-ci-sha.sh" --strict

export XSCANNER_API_IMAGE="ghcr.io/axedras/xscanner:${MODE}-${TAG}"
export XSCANNER_RELEASE_TAG="$TAG"
export ORIGIN
export MODE

bash "$SCRIPT_DIR/database-start.sh"
bash "$SCRIPT_DIR/up.sh"
bash "$SCRIPT_DIR/health.sh"

if [ -n "$ORIGINAL_REF" ]; then
	git checkout "$ORIGINAL_REF" >/dev/null 2>&1 || true
fi

echo -e "${GREEN}✓ Deploy complete${NC}"
