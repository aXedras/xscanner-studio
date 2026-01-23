#!/bin/bash

set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

ORIGIN="${ORIGIN:-latest}"
MODE="${MODE:-}"

if [ -z "$MODE" ]; then
	if [ "$ORIGIN" = "main" ]; then
		MODE="cloud"
	else
		MODE="full"
	fi
fi

if [ "$MODE" != "cloud" ] && [ "$MODE" != "full" ]; then
	echo -e "${RED}Error: invalid MODE (expected cloud|full): ${MODE}${NC}" >&2
	exit 1
fi

compute_release_tag_from_pyproject() {
	local repo_root="$1"
	local py=""

	if [ -x "$repo_root/venv/bin/python" ]; then
		py="$repo_root/venv/bin/python"
	elif command -v python3 >/dev/null 2>&1; then
		py="python3"
	elif command -v python >/dev/null 2>&1; then
		py="python"
	else
		return 1
	fi

	"$py" - <<'PY'
import tomllib

data = tomllib.load(open('pyproject.toml', 'rb'))
version = (data.get('project', {}) or {}).get('version', '')
version = str(version).strip()
if not version:
    raise SystemExit(1)

print(version)
PY
}

compute_short_sha() {
	local repo_root="$1"
	git -C "$repo_root" rev-parse --short HEAD 2>/dev/null || true
}


if [ "$ORIGIN" != "main" ]; then
	echo -e "${BLUE}🚀 Starting API + Studio (pre-prod compose, release mode)...${NC}"

	if [ -z "${XSCANNER_API_IMAGE:-}" ]; then
		export XSCANNER_API_IMAGE="ghcr.io/axedras/xscanner:${MODE}-release"
	fi
	if [ -z "${XSCANNER_RELEASE_TAG:-}" ]; then
		export XSCANNER_RELEASE_TAG="dev"
	fi

	echo -e "${BLUE}Origin:${NC} ${ORIGIN}"
	echo -e "${BLUE}Mode:${NC} ${MODE}"
	echo -e "${BLUE}API image:${NC} ${XSCANNER_API_IMAGE}"

	docker compose --env-file .env.preprod -f docker-compose.preprod.yml pull xscanner-api-release

	docker compose --env-file .env.preprod -f docker-compose.preprod.yml \
		up -d --build xscanner-api-release xscanner-studio
else
	echo -e "${BLUE}🚀 Starting API + Studio (pre-prod compose, build mode)...${NC}"
	export MODE
	if [ -z "${XSCANNER_RELEASE_TAG:-}" ]; then
		version="$(compute_release_tag_from_pyproject "$REPO_ROOT" 2>/dev/null || true)"
		sha="$(compute_short_sha "$REPO_ROOT")"

		if [ -n "$version" ] && [ -n "$sha" ]; then
			export XSCANNER_RELEASE_TAG="v${version}+g${sha}"
		elif [ -n "$version" ]; then
			export XSCANNER_RELEASE_TAG="v${version}"
		else
			export XSCANNER_RELEASE_TAG="dev"
		fi
	fi

	echo -e "${BLUE}Origin:${NC} ${ORIGIN}"
	echo -e "${BLUE}Mode:${NC} ${MODE}"
	echo -e "${BLUE}Release tag:${NC} ${XSCANNER_RELEASE_TAG}"
	echo -e "${BLUE}API dockerfile:${NC} Dockerfile.${MODE}"
	docker compose --env-file .env.preprod -f docker-compose.preprod.yml \
		up -d --build xscanner-api-build xscanner-studio
fi

echo -e "${GREEN}✓ Compose is up${NC}"
