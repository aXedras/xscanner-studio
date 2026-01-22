@echo off
REM Pre-prod deploy on Windows VM
REM Flow:
REM - ORIGIN=main: update main (ff-only) -> ensure Supabase running -> docker compose up (build)
REM - ORIGIN=latest|release-x.y.z: checkout tag (best-effort) -> ensure Supabase running -> docker pull + compose up (release)

setlocal EnableExtensions EnableDelayedExpansion

REM Inputs (provided via environment; Makefile exports variables)
if not defined ORIGIN set "ORIGIN=latest"

if not defined MODE (
	if /I "%ORIGIN%"=="main" (
		set "MODE=cloud"
	) else (
		set "MODE=full"
	)
)

call :validate_mode
if %errorlevel% neq 0 exit /b %errorlevel%

cd /d "%~dp0\..\..\.."

REM Resolve gh CLI (PATH is not always updated on Windows)
set "GH_EXE=gh"
if exist "%ProgramFiles%\GitHub CLI\gh.exe" set "GH_EXE=%ProgramFiles%\GitHub CLI\gh.exe"

call :check_prereqs
if %errorlevel% neq 0 exit /b %errorlevel%

echo Updating main...

call :ensure_clean_worktree
if %errorlevel% neq 0 exit /b %errorlevel%

git checkout main
if %errorlevel% neq 0 exit /b %errorlevel%

git pull --ff-only origin main
if %errorlevel% neq 0 exit /b %errorlevel%

if /I "%ORIGIN%"=="main" (
	call :verify_ci_main_strict
	set "RC=!errorlevel!"
	if not "!RC!"=="0" exit /b !RC!
)

if not exist ".env.preprod" goto missing_env

call scripts\windows\preprod\database-start.bat
if %errorlevel% neq 0 exit /b %errorlevel%

echo Stopping existing API + Studio ^(if any^)...
docker compose --env-file .env.preprod -f docker-compose.preprod.yml down --remove-orphans
if %errorlevel% neq 0 exit /b %errorlevel%

REM Deploy
if /I "%ORIGIN%"=="main" goto deploy_main
if /I "%ORIGIN%"=="latest" goto deploy_latest

echo %ORIGIN% | findstr /I /R "^release-" >NUL
if %errorlevel% neq 0 goto invalid_origin
set "TAG=%ORIGIN:release-=%"
if /I not "!TAG:~0,1!"=="v" set "TAG=v!TAG!"
goto deploy_release_common

:deploy_latest
"%GH_EXE%" --version >NUL 2>&1
if %errorlevel% neq 0 (
	echo Error: gh CLI not found in PATH. Install GitHub CLI or set ORIGIN=release-x.y.z.
	exit /b 1
)
"%GH_EXE%" release view --repo aXedras/xScanner --json tagName --jq .tagName >NUL 2>&1
if %errorlevel% neq 0 (
	echo Error: no GitHub Releases found for aXedras/xScanner.
	echo Tip: use ORIGIN=main ^(local build^) or ORIGIN=release-x.y.z once releases exist.
	exit /b 1
)
for /f "usebackq delims=" %%T in (`"%GH_EXE%" release view --repo aXedras/xScanner --json tagName --jq .tagName 2^>NUL`) do set "TAG=%%T"
if not defined TAG (
	echo Error: could not resolve latest release tag via gh.
	exit /b 1
)
goto deploy_release_common

:deploy_main
if not defined XSCANNER_RELEASE_TAG set "XSCANNER_RELEASE_TAG=dev"
set "API_SERVICE=xscanner-api-build"
echo Building API + Studio images ^(build mode^)...
docker compose --env-file .env.preprod -f docker-compose.preprod.yml build xscanner-api-build xscanner-studio
if %errorlevel% neq 0 exit /b %errorlevel%

echo Starting API + Studio ^(build mode^)...
docker compose --env-file .env.preprod -f docker-compose.preprod.yml up -d xscanner-api-build xscanner-studio
if %errorlevel% neq 0 exit /b %errorlevel%
goto after_deploy

:deploy_release_common
REM Best-effort: checkout tag so repo reflects deployed version
set "ORIGINAL_REF="
for /f "usebackq delims=" %%B in (`git branch --show-current 2^>NUL`) do set "ORIGINAL_REF=%%B"
git fetch --tags origin >NUL 2>&1
git checkout "!TAG!" >NUL 2>&1

if not defined XSCANNER_API_IMAGE set "XSCANNER_API_IMAGE=ghcr.io/axedras/xscanner:%MODE%-!TAG!"
if not defined XSCANNER_RELEASE_TAG set "XSCANNER_RELEASE_TAG=!TAG!"

call :ensure_ghcr_login
if %errorlevel% neq 0 exit /b %errorlevel%

set "API_SERVICE=xscanner-api-release"

echo Pulling release image: !XSCANNER_API_IMAGE!
docker compose --env-file .env.preprod -f docker-compose.preprod.yml pull xscanner-api-release
if %errorlevel% neq 0 (
	echo Error: failed to pull release image. If you see 'unauthorized', run: docker login ghcr.io
	exit /b %errorlevel%
)

echo Starting API + Studio ^(release mode^)...
echo Building Studio image ^(release mode^)...
docker compose --env-file .env.preprod -f docker-compose.preprod.yml build xscanner-studio
if %errorlevel% neq 0 exit /b %errorlevel%

docker compose --env-file .env.preprod -f docker-compose.preprod.yml up -d xscanner-api-release xscanner-studio
if %errorlevel% neq 0 exit /b %errorlevel%

if defined ORIGINAL_REF (
	git checkout "!ORIGINAL_REF!" >NUL 2>&1
)
goto after_deploy

:after_deploy

echo Healthcheck...
set "HEALTH_URL=http://127.0.0.1:8010/health"
curl -fsS "%HEALTH_URL%" >nul 2>&1
if %errorlevel% equ 0 goto health_ok
goto health_fail

:health_fail
echo Healthcheck failed: %HEALTH_URL%
echo Tip: this script intentionally fails fast; just run it again once the build/pull is ready.
if defined API_SERVICE (
	echo Recent logs ^(%API_SERVICE%^):
	docker compose --env-file .env.preprod -f docker-compose.preprod.yml logs --tail 200 %API_SERVICE%
)
exit /b 1

:health_ok
echo Healthcheck OK

echo Deploy complete
exit /b 0

:missing_env
echo Missing .env.preprod - create it from .env.preprod.example
exit /b 1

:invalid_origin
echo Error: invalid ORIGIN (expected main^|latest^|release-x.y.z): %ORIGIN%
exit /b 1

:validate_mode
if /I "%MODE%"=="cloud" exit /b 0
if /I "%MODE%"=="full" exit /b 0
echo Error: invalid MODE (expected cloud^|full): %MODE%
exit /b 1

:check_prereqs
where docker >NUL 2>&1
if %errorlevel% neq 0 (
	echo Error: docker not found in PATH
	exit /b 1
)

docker compose version >NUL 2>&1
if %errorlevel% neq 0 (
	echo Error: docker compose not available
	exit /b 1
)

where supabase >NUL 2>&1
if %errorlevel% neq 0 (
	echo Error: supabase CLI not found in PATH
	exit /b 1
)

if not exist ".env.preprod" (
	echo Error: missing .env.preprod
	echo Create it from .env.preprod.example ^(do not commit secrets^).
	exit /b 1
)

REM For release-based deploys, require gh + auth
if /I not "%ORIGIN%"=="main" (
	"%GH_EXE%" --version >NUL 2>&1
	if %errorlevel% neq 0 (
		echo Error: gh CLI not found in PATH ^(required for ORIGIN != main^)
		exit /b 1
	)
	"%GH_EXE%" auth status -h github.com >NUL 2>&1
	if %errorlevel% neq 0 (
		echo Error: gh is not authenticated ^(required for ORIGIN != main^)
		echo Run: gh auth login
		exit /b 1
	)
)

exit /b 0

:ensure_clean_worktree
REM Guard against local modifications (match scripts/preprod/check.sh intent)
git diff --quiet
if %errorlevel% neq 0 goto worktree_dirty
git diff --cached --quiet
if %errorlevel% neq 0 goto worktree_dirty
exit /b 0

:worktree_dirty
echo Error: git working tree has uncommitted changes
echo This is intentional for pre-prod deploys.
echo Fix: commit, stash, or deploy from a clean clone.
git status -sb
exit /b 1

:verify_ci_main_strict
REM Mirror scripts/preprod/verify-ci-main.sh --strict
"%GH_EXE%" --version >NUL 2>&1
if %errorlevel% neq 0 (
	echo Error: gh CLI not installed; cannot verify CI status
	exit /b 1
)

"%GH_EXE%" auth status -h github.com >NUL 2>&1
if %errorlevel% neq 0 (
	echo Error: gh is not authenticated; cannot verify CI status
	exit /b 1
)

set "HEAD_SHA="
for /f "usebackq delims=" %%S in (`git rev-parse HEAD 2^>NUL`) do set "HEAD_SHA=%%S"
if not defined HEAD_SHA (
	echo Error: cannot read HEAD sha
	exit /b 1
)

set "MATCHED_CONCLUSION="
for /f "usebackq delims=" %%C in (`"%GH_EXE%" api "repos/aXedras/xScanner/actions/workflows/ci.yml/runs?branch=main^&per_page=50" --jq ".workflow_runs[] | select(.head_sha == \"!HEAD_SHA!\") | .conclusion" 2^>NUL`) do (
	set "MATCHED_CONCLUSION=%%C"
	goto got_ci
)
:got_ci

if not defined MATCHED_CONCLUSION (
	echo Error: cannot verify CI for sha !HEAD_SHA!
	echo Ensure gh is authenticated and the workflow run exists for this commit.
	exit /b 1
)

if /I not "!MATCHED_CONCLUSION!"=="success" (
	echo Error: CI for sha !HEAD_SHA! is not successful ^(conclusion=!MATCHED_CONCLUSION!^)
	exit /b 1
)

echo CI successful for sha: !HEAD_SHA!
exit /b 0

:ensure_ghcr_login
REM Best-effort GHCR auth to avoid 401 when pulling private images.
where docker >NUL 2>&1
if %errorlevel% neq 0 (
  echo Error: docker not found in PATH.
  exit /b 1
)

"%GH_EXE%" --version >NUL 2>&1
if %errorlevel% neq 0 (
  REM No gh: user must login manually.
  exit /b 0
)

REM Ensure gh is authenticated
"%GH_EXE%" auth status -h github.com >NUL 2>&1
if %errorlevel% neq 0 (
  echo Note: gh not authenticated. If GHCR pull fails, run: gh auth login
  exit /b 0
)

set "GH_USER="
for /f "usebackq delims=" %%U in (`"%GH_EXE%" api user --jq .login 2^>NUL`) do set "GH_USER=%%U"
if not defined GH_USER set "GH_USER=%GITHUB_ACTOR%"
if not defined GH_USER set "GH_USER=github"

set "GH_TOKEN="
for /f "usebackq delims=" %%T in (`"%GH_EXE%" auth token 2^>NUL`) do set "GH_TOKEN=%%T"
if not defined GH_TOKEN exit /b 0

echo Logging into ghcr.io (best-effort)...
echo !GH_TOKEN! | docker login ghcr.io -u !GH_USER! --password-stdin >NUL 2>&1
exit /b 0
