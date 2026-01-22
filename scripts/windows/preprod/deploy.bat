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

echo Updating main...
git checkout main
if %errorlevel% neq 0 exit /b %errorlevel%

git pull --ff-only origin main
if %errorlevel% neq 0 exit /b %errorlevel%

if not exist ".env.preprod" goto missing_env

call scripts\windows\preprod\database-start.bat
if %errorlevel% neq 0 exit /b %errorlevel%

echo Stopping existing API + Studio ^(if any^)...
docker compose --env-file .env.preprod -f docker-compose.preprod.yml down --remove-orphans >NUL 2>&1

REM Deploy
if /I "%ORIGIN%"=="main" goto deploy_main
if /I "%ORIGIN%"=="latest" goto deploy_latest

echo %ORIGIN% | findstr /I /R "^release-" >NUL
if %errorlevel% neq 0 goto invalid_origin
set "TAG=%ORIGIN:release-=%"
if /I not "!TAG:~0,1!"=="v" set "TAG=v!TAG!"
goto deploy_release_common

:deploy_latest
where gh >NUL 2>&1
if %errorlevel% neq 0 (
	echo Error: gh CLI not found in PATH. Install GitHub CLI or set ORIGIN=release-x.y.z.
	exit /b 1
)
gh release view --repo aXedras/xScanner --json tagName --jq .tagName >NUL 2>&1
if %errorlevel% neq 0 (
	echo Error: no GitHub Releases found for aXedras/xScanner.
	echo Tip: use ORIGIN=main ^(local build^) or ORIGIN=release-x.y.z once releases exist.
	exit /b 1
)
for /f "usebackq delims=" %%T in (`gh release view --repo aXedras/xScanner --json tagName --jq .tagName 2^>NUL`) do set "TAG=%%T"
if not defined TAG (
	echo Error: could not resolve latest release tag via gh.
	exit /b 1
)
goto deploy_release_common

:deploy_main
if not defined XSCANNER_RELEASE_TAG set "XSCANNER_RELEASE_TAG=dev"
set "API_SERVICE=xscanner-api-build"
echo Starting API + Studio ^(build mode^)...
docker compose --env-file .env.preprod -f docker-compose.preprod.yml up -d --build xscanner-api-build xscanner-studio
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
docker compose --env-file .env.preprod -f docker-compose.preprod.yml up -d --build xscanner-api-release xscanner-studio
if %errorlevel% neq 0 exit /b %errorlevel%

if defined ORIGINAL_REF (
	git checkout "!ORIGINAL_REF!" >NUL 2>&1
)
goto after_deploy

:after_deploy

echo Healthcheck...
set "HEALTH_URL=http://127.0.0.1:8010/health"
set /a HEALTH_RETRIES=30
:health_loop
curl -fsS "%HEALTH_URL%" >nul 2>&1
if %errorlevel% equ 0 goto health_ok
set /a HEALTH_RETRIES-=1
if %HEALTH_RETRIES% leq 0 goto health_fail
timeout /t 2 /nobreak >nul
goto health_loop

:health_fail
echo Healthcheck failed: %HEALTH_URL%
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

:ensure_ghcr_login
REM Best-effort GHCR auth to avoid 401 when pulling private images.
where docker >NUL 2>&1
if %errorlevel% neq 0 (
  echo Error: docker not found in PATH.
  exit /b 1
)

where gh >NUL 2>&1
if %errorlevel% neq 0 (
  REM No gh: user must login manually.
  exit /b 0
)

REM Ensure gh is authenticated
gh auth status -h github.com >NUL 2>&1
if %errorlevel% neq 0 (
  echo Note: gh not authenticated. If GHCR pull fails, run: gh auth login
  exit /b 0
)

set "GH_USER="
for /f "usebackq delims=" %%U in (`gh api user --jq .login 2^>NUL`) do set "GH_USER=%%U"
if not defined GH_USER set "GH_USER=%GITHUB_ACTOR%"
if not defined GH_USER set "GH_USER=github"

set "GH_TOKEN="
for /f "usebackq delims=" %%T in (`gh auth token 2^>NUL`) do set "GH_TOKEN=%%T"
if not defined GH_TOKEN exit /b 0

echo Logging into ghcr.io (best-effort)...
echo !GH_TOKEN! | docker login ghcr.io -u !GH_USER! --password-stdin >NUL 2>&1
exit /b 0
