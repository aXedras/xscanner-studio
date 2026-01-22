# Releasing xScanner (API + Studio)

This document defines the release flow for xScanner, the container image tags produced by CI, and how pre-prod deployments consume them.

## Goals

- Keep development fast by reusing a small set of moving tags.
- Create stable, reproducible release artifacts only when we decide a version is releaseable.
- Ensure pre-prod deployments use only CI-green release artifacts.

## Images & tags

xScanner publishes two API image flavors:

- **Cloud**: `ghcr.io/axedras/xscanner:cloud` (moving)
- **Full**: `ghcr.io/axedras/xscanner:full` (moving)

On every non-PR CI run, the moving tags are updated (overwritten) and do not accumulate long-term storage.

On GitHub Release, CI also publishes immutable release tags:

- Cloud release: `ghcr.io/axedras/xscanner:cloud-vX.Y.Z`
- Full release: `ghcr.io/axedras/xscanner:full-vX.Y.Z`

And two moving "latest release channel" tags:

- Cloud latest release: `ghcr.io/axedras/xscanner:cloud-release`
- Full latest release: `ghcr.io/axedras/xscanner:full-release`

## Creating a release

Versioning note:
- xScanner has no historical GitHub Releases yet.
- The first planned release is `v0.1.0`.

Prerequisites:
- You are on `main` and it is up to date
- Working tree is clean
- You are authenticated with GitHub CLI (`gh auth login`)

Mandatory docs step (manual):
- Update `docs/CHANGELOG.md` and ensure the release section exists (e.g. `## [X.Y.Z] - YYYY-MM-DD`).
- Update `pyproject.toml` `[project].version` to `X.Y.Z`.
- Update `src/xscanner/__init__.py` and `src/xscanner/server/__init__.py` `__version__` to `X.Y.Z`.
- The release script enforces that the changelog contains the release entry.

Notes:
- Git tags/releases are prefixed with `v` (e.g. `vX.Y.Z`).
- Changelog sections do not include the `v` prefix (e.g. `## [X.Y.Z] - YYYY-MM-DD`).

Recommended:

```bash
VERSION=X.Y.Z bash scripts/release/create-release.sh
```

This creates the git tag `vX.Y.Z`, pushes it, and creates a GitHub Release. CI will then build and publish the release image tags.

## Deploying to pre-prod

Pre-prod deploy defaults to the latest GitHub Release tag:

```bash
make preprod-deploy
```

Common overrides:

```bash
# Deploy a specific release
make preprod-deploy ORIGIN=release-X.Y.Z

# Deploy a specific release (cloud image)
make preprod-deploy ORIGIN=release-X.Y.Z MODE=cloud

# Deploy from main (local build)
make preprod-deploy ORIGIN=main MODE=cloud
```

Notes:
- In release mode, the deploy script checks out the release tag locally (so Studio is built from the same release source).
- API is pulled from GHCR using the release tags.
- Studio is built locally because Vite configuration is baked at build time.

Compose note:
- Pre-prod uses one compose file with two API services (`xscanner-api-release` vs `xscanner-api-build`).
- Deploy scripts start only one API service to avoid port conflicts.

Where the release is shown:
- Studio footer shows the baked `VITE_XSCANNER_RELEASE_TAG`.
- Swagger/OpenAPI shows the API version based on `XSCANNER_RELEASE_TAG`.
