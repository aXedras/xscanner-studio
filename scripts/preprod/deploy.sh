#!/bin/bash

set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./common.sh
source "$SCRIPT_DIR/common.sh"
preprod_guard_unknown_env_var_names
preprod_guard_no_positional_args "$@"

ORIGIN="${ORIGIN:-latest}"
MODE="${MODE:-}"

ORIGIN="$(preprod_normalize_origin "$ORIGIN")"
MODE="$(preprod_normalize_mode "$MODE")"

preprod_ensure_default_platform_for_pulls "$ORIGIN"

if [ -n "${XSCANNER_RELEASE_TAG:-}" ]; then
	echo -e "${RED}Error:${NC} XSCANNER_RELEASE_TAG must not be set manually." >&2
	echo -e "${BLUE}Why:${NC} the pre-prod scripts derive it from ORIGIN to avoid mismatched labels." >&2
	echo -e "${BLUE}Fix:${NC} unset XSCANNER_RELEASE_TAG and use ORIGIN=main|local|release-x.y.z." >&2
	exit 2
fi

if [ -z "$MODE" ]; then
	if [ "$ORIGIN" = "main" ] || [ "$ORIGIN" = "local" ]; then
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

if [ "$ORIGIN" = "local" ]; then
	echo -e "${BLUE}Origin:${NC} local (deploy from current worktree, local build)"
	echo -e "${BLUE}Mode:${NC} ${MODE}"

	ORIGIN=local bash "$SCRIPT_DIR/check.sh"
	bash "$SCRIPT_DIR/database-start.sh"
	ORIGIN=local MODE="$MODE" bash "$SCRIPT_DIR/up.sh"
	bash "$SCRIPT_DIR/health.sh"

	echo -e "${GREEN}✓ Deploy complete${NC}"
	exit 0
fi

if [ "$ORIGIN" = "main" ]; then
	echo -e "${BLUE}Origin:${NC} main (deploy by pulling GHCR images)"
	echo -e "${BLUE}Mode:${NC} ${MODE}"

	ORIGIN=main bash "$SCRIPT_DIR/check.sh"
	bash "$SCRIPT_DIR/verify-ci-main.sh" --strict --latest
	bash "$SCRIPT_DIR/database-start.sh"
	ORIGIN=main MODE="$MODE" bash "$SCRIPT_DIR/up.sh"
	bash "$SCRIPT_DIR/health.sh"

	echo -e "${GREEN}✓ Deploy complete${NC}"
	exit 0
fi

TAG=""
if [ "$ORIGIN" = "latest" ]; then
	TAG="$(gh release view --repo aXedras/xScanner --json tagName --jq .tagName 2>/dev/null || true)"
	if [ -z "$TAG" ]; then
		echo -e "${RED}Error:${NC} no GitHub Releases found for aXedras/xScanner." >&2
		echo -e "${BLUE}Tip:${NC} use ORIGIN=main (pull moving images) or ORIGIN=local (local build) until releases exist." >&2
		exit 1
	fi
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

if ! grep -q '^  xscanner-studio-release:' docker-compose.preprod.yml; then
	echo -e "${RED}Error:${NC} release tag ${TAG} does not support pulling the Studio image (missing xscanner-studio-release in docker-compose.preprod.yml)." >&2
	echo -e "${BLUE}Fix:${NC} create a new release after the Studio GHCR publishing was added." >&2
	exit 1
fi

bash "$SCRIPT_DIR/verify-ci-sha.sh" --strict

export XSCANNER_API_IMAGE="ghcr.io/axedras/xscanner:${MODE}-${TAG}"

# Ensure the downstream scripts do not need gh for ORIGIN=latest.
ORIGIN="release-${TAG}"

export ORIGIN
export MODE

bash "$SCRIPT_DIR/database-start.sh"
bash "$SCRIPT_DIR/up.sh"
bash "$SCRIPT_DIR/health.sh"

if [ -n "$ORIGINAL_REF" ]; then
	git checkout "$ORIGINAL_REF" >/dev/null 2>&1 || true
fi

echo -e "${GREEN}✓ Deploy complete${NC}"
