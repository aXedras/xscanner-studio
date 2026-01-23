#!/bin/bash

# Shared helpers for pre-prod scripts.
# Intentionally does not set shell options; calling scripts own that.

preprod_guard_unknown_env_var_names() {
	# Common pitfall: passing make variables with wrong casing, e.g. `origin=main`.
	# In that case ORIGIN remains unset and defaults kick in, which is surprising.
	if [ -n "${origin-}" ] && [ -z "${ORIGIN-}" ]; then
		echo "Error: unknown parameter \"origin\". Did you mean ORIGIN=... ?" >&2
		exit 2
	fi
	if [ -n "${mode-}" ] && [ -z "${MODE-}" ]; then
		echo "Error: unknown parameter \"mode\". Did you mean MODE=cloud|full ?" >&2
		exit 2
	fi
	if [ -n "${Origin-}" ] && [ -z "${ORIGIN-}" ]; then
		echo "Error: unknown parameter \"Origin\". Did you mean ORIGIN=... ?" >&2
		exit 2
	fi
	if [ -n "${Mode-}" ] && [ -z "${MODE-}" ]; then
		echo "Error: unknown parameter \"Mode\". Did you mean MODE=cloud|full ?" >&2
		exit 2
	fi
}

preprod_guard_no_positional_args() {
	if [ "$#" -gt 0 ]; then
		echo "Error: unexpected arguments: $*" >&2
		echo "Fix: pass configuration via environment variables, e.g. ORIGIN=main MODE=cloud." >&2
		exit 2
	fi
}

preprod_host_arch() {
	uname -m 2>/dev/null || true
}

preprod_ensure_default_platform_for_pulls() {
	# Apple Silicon (arm64) hosts cannot run amd64-only images without emulation.
	# Default to amd64 for pulled images if not explicitly set.
	local origin="$1"
	local arch
	arch="$(preprod_host_arch)"

	if [ "$origin" = "local" ]; then
		return 0
	fi

	if [ -n "${DOCKER_DEFAULT_PLATFORM:-}" ]; then
		return 0
	fi

	if [ "$arch" = "arm64" ] || [ "$arch" = "aarch64" ]; then
		export DOCKER_DEFAULT_PLATFORM="linux/amd64"
		echo "Note: host arch is ${arch}; setting DOCKER_DEFAULT_PLATFORM=linux/amd64 for GHCR pulls." >&2
		echo "Tip: to disable this, export DOCKER_DEFAULT_PLATFORM=linux/arm64 (requires arm64 images)." >&2
	fi
}

preprod_latest_github_release_tag() {
	# Returns the latest GitHub release tag (e.g. v0.1.1) or empty string.
	# Best-effort: ORIGIN=main/preprod-up may be used without gh installed.
	local tag=""
	if ! command -v gh >/dev/null 2>&1; then
		echo ""
		return 0
	fi
	tag="$(gh release view --repo aXedras/xScanner --json tagName --jq .tagName 2>/dev/null || true)"
	echo "$tag"
}

preprod_image_revision() {
	# Returns the OCI revision label (full sha) or empty string.
	local image="$1"
	if ! command -v docker >/dev/null 2>&1; then
		echo ""
		return 0
	fi
	docker image inspect "$image" --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' 2>/dev/null || true
}

preprod_normalize_origin() {
	local raw="$1"

	if [[ "$raw" =~ ^[Mm][Aa][Ii][Nn]$ ]]; then
		echo "main"
		return 0
	fi
	if [[ "$raw" =~ ^[Ll][Oo][Cc][Aa][Ll]$ ]]; then
		echo "local"
		return 0
	fi
	if [[ "$raw" =~ ^[Ll][Aa][Tt][Ee][Ss][Tt]$ ]]; then
		echo "latest"
		return 0
	fi
	if [[ "$raw" =~ ^[Rr][Ee][Ll][Ee][Aa][Ss][Ee]- ]]; then
		# Keep suffix as provided (git tags are case-sensitive).
		echo "release-${raw:8}"
		return 0
	fi

	echo "$raw"
}

preprod_normalize_mode() {
	local raw="$1"

	if [ -z "$raw" ]; then
		echo ""
		return 0
	fi

	if [[ "$raw" =~ ^[Cc][Ll][Oo][Uu][Dd]$ ]]; then
		echo "cloud"
		return 0
	fi
	if [[ "$raw" =~ ^[Ff][Uu][Ll][Ll]$ ]]; then
		echo "full"
		return 0
	fi

	echo "$raw"
}
