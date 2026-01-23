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
