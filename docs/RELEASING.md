# Releasing xScanner (API + Studio)

This document defines the release flow for xScanner, the container image tags produced by CI, and how pre-prod deployments consume them.

## Goals

- Keep development fast by reusing a small set of moving tags.
- Create stable, reproducible release artifacts only when we decide a version is releaseable.
- Ensure pre-prod deployments use only CI-green release artifacts.

## Images & tags

xScanner publishes two API image flavors:

- **Latest**: `ghcr.io/axedras/xscanner:latest` (moving, updated on every push to main/develop)
- **Branch**: `ghcr.io/axedras/xscanner:<branch>` (moving, e.g. `:main`, `:develop`)

On every non-PR CI run, the moving tags are updated (overwritten) and do not accumulate long-term storage.

On GitHub Release, CI also publishes immutable release tags:

- Versioned: `ghcr.io/axedras/xscanner:vX.Y.Z`

And a moving "latest release channel" tag:

- Latest release: `ghcr.io/axedras/xscanner:release`

xScanner also publishes a Studio (nginx) image:

- **Studio (branch moving tags)**: `ghcr.io/axedras/xscanner-studio:main` and `ghcr.io/axedras/xscanner-studio:develop`
- **Studio (immutable release tag)**: `ghcr.io/axedras/xscanner-studio:vX.Y.Z`
- **Studio (latest release channel)**: `ghcr.io/axedras/xscanner-studio:release`

## Creating a release

Versioning note:
- The first release was `v0.1.0`.

Prerequisites:
- You are on `main` and it is up to date
- Working tree is clean
- You are authenticated with GitHub CLI (`gh auth login`)

Mandatory docs step (manual):
- Update `docs/CHANGELOG.md` and ensure the release section exists (e.g. `## [X.Y.Z] - YYYY-MM-DD`).
- Update `pyproject.toml` `[project].version` to `X.Y.Z`.
- Update `src/xscanner/__init__.py` and `src/xscanner/server/__init__.py` `__version__` to `X.Y.Z`.
- Update `studio/package.json` and `studio/package-lock.json` version to `X.Y.Z`.
- The release script enforces that the changelog contains the release entry.

Notes:
- Git tags/releases are prefixed with `v` (e.g. `vX.Y.Z`).
- Changelog sections do not include the `v` prefix (e.g. `## [X.Y.Z] - YYYY-MM-DD`).

Recommended:

```bash
VERSION=X.Y.Z bash scripts/release/create-release.sh
```

This creates the git tag `vX.Y.Z`, pushes it, and creates a GitHub Release. CI will then build and publish the release image tags.

Release notes:
- The GitHub Release is created with GitHub auto-generated notes.
- The release script then runs `scripts/release/sync-release-notes.sh` to prepend the curated `docs/CHANGELOG.md` section and a `## Contributors` section (formatted like GitHub auto-notes, using `* @login in <url>`).

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
# Deploy from main (pull moving GHCR images)
make preprod-deploy ORIGIN=main MODE=cloud

# Deploy from local worktree (build, allows uncommitted changes)
make preprod-deploy ORIGIN=local MODE=cloud
```

Notes:
- In release mode, the deploy script checks out the release tag locally and pulls the API + Studio images from GHCR.
- Studio runtime config is injected via container env vars at startup (no rebuild required).
- In main mode, the deploy script pulls moving images from GHCR (API: `:cloud`/`:full`, Studio: `:main`).
- In local mode (build), Studio is built locally because Vite configuration is baked at build time.

Compose note:
- Pre-prod uses one compose file with two API services (`xscanner-api-release` vs `xscanner-api-build`).
- Deploy scripts start only one API service to avoid port conflicts.

Where the release is shown:
- Studio footer shows the baked `VITE_XSCANNER_RELEASE_TAG`.
- Swagger/OpenAPI shows the API version based on `XSCANNER_RELEASE_TAG`.

Note:
- `XSCANNER_RELEASE_TAG` is derived by the deploy scripts from `ORIGIN` (release tag / `main` / local worktree) to avoid mismatched labels.
