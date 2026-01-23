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

echo -e "${BLUE}🚀 Pre-prod up${NC}"
echo -e "${BLUE}Note:${NC} this command may pull images, rebuild Studio, and recreate containers."
echo -e "${BLUE}Compose:${NC} docker-compose.preprod.yml"

resolve_release_tag() {
	local origin="$1"
	local tag=""

	if [ "$origin" = "latest" ]; then
		if ! command -v gh >/dev/null 2>&1; then
			return 2
		fi
		tag="$(gh release view --repo aXedras/xScanner --json tagName --jq .tagName 2>/dev/null || true)"
		echo "$tag"
		return 0
	fi

	if [[ "$origin" == release-* ]]; then
		tag="${origin#release-}"
		if [[ "$tag" != v* ]]; then
			tag="v$tag"
		fi
		echo "$tag"
		return 0
	fi

	return 1
}

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
	echo -e "${BLUE}Mode:${NC} release (API from GHCR image)"

	if [ -z "${XSCANNER_API_IMAGE:-}" ]; then
		need_tag=1
	else
		need_tag=0
	fi
	if [ -z "${XSCANNER_RELEASE_TAG:-}" ]; then
		need_tag=1
	fi

	TAG=""
	if [ "${need_tag:-0}" -eq 1 ]; then
		TAG="$(resolve_release_tag "$ORIGIN")" || rc=$?
		if [ "${rc:-0}" -eq 2 ]; then
			echo -e "${RED}Error:${NC} gh CLI not found in PATH, required for ORIGIN=latest." >&2
			echo -e "${BLUE}Fix:${NC} install GitHub CLI or use ORIGIN=release-x.y.z (or set XSCANNER_API_IMAGE + XSCANNER_RELEASE_TAG explicitly)." >&2
			exit 1
		fi
		if [ "${rc:-0}" -ne 0 ]; then
			echo -e "${RED}Error: invalid ORIGIN (expected main|latest|release-x.y.z): ${ORIGIN}${NC}" >&2
			exit 1
		fi
		if [ -z "$TAG" ]; then
			echo -e "${RED}Error:${NC} could not resolve release tag for ORIGIN=${ORIGIN}." >&2
			exit 1
		fi
	fi

	if [ -z "${XSCANNER_API_IMAGE:-}" ]; then
		export XSCANNER_API_IMAGE="ghcr.io/axedras/xscanner:${MODE}-${TAG}"
	fi
	if [ -z "${XSCANNER_RELEASE_TAG:-}" ]; then
		export XSCANNER_RELEASE_TAG="$TAG"
	fi

	echo -e "${BLUE}Origin:${NC} ${ORIGIN}"
	echo -e "${BLUE}Mode:${NC} ${MODE}"
	if [ -n "${TAG:-}" ]; then
		echo -e "${BLUE}Release tag:${NC} ${TAG}"
	fi
	echo -e "${BLUE}API image:${NC} ${XSCANNER_API_IMAGE}"
	echo -e "${BLUE}Actions:${NC} pull xscanner-api-release xscanner-studio-release; up -d xscanner-api-release xscanner-studio-release"

	docker compose --env-file .env.preprod -f docker-compose.preprod.yml pull xscanner-api-release xscanner-studio-release

	docker compose --env-file .env.preprod -f docker-compose.preprod.yml \
		up -d xscanner-api-release xscanner-studio-release
else
	echo -e "${BLUE}Mode:${NC} build (API built from source)"
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
	echo -e "${BLUE}Actions:${NC} up -d --build xscanner-api-build xscanner-studio"
	docker compose --env-file .env.preprod -f docker-compose.preprod.yml \
		up -d --build xscanner-api-build xscanner-studio
fi

echo -e "${GREEN}✓ Compose is up${NC}"
