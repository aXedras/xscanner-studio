@echo off
setlocal EnableExtensions EnableDelayedExpansion

for %%I in ("%~dp0..\..\..") do set "REPO_ROOT=%%~fI"
cd /d "%REPO_ROOT%" || exit /b 1

if exist ".env.preprod" goto :env_ok
echo Error: .env.preprod not found. Create it from .env.preprod.example
exit /b 1
:env_ok

echo Fix: install GitHub CLI or use ORIGIN=release-x.y.z.

if not "%MODE%"=="" goto :mode_set
if /I "%ORIGIN%"=="main" set "MODE=cloud"

call :derive_local_release_tag
echo %ORIGIN% | findstr /I /R "^release-" >NUL
if %errorlevel%==0 set "MODE=full"
:mode_set

if /I "%MODE%"=="cloud" goto :mode_ok
if /I "%MODE%"=="full" goto :mode_ok
echo Error: invalid MODE ^(expected cloud^|full^): %MODE%
exit /b 1
:mode_ok

if defined XSCANNER_RELEASE_TAG (
	echo Error: XSCANNER_RELEASE_TAG must not be set manually.
	echo Why: pre-prod scripts derive it from ORIGIN to avoid mismatched labels.
	echo Fix: unset XSCANNER_RELEASE_TAG and use ORIGIN=main^|local^|release-x.y.z.
	exit /b 2
)

echo Pre-prod up
echo Note: this command may pull images, rebuild Studio, and recreate containers.
echo Compose: docker-compose.preprod.yml

if /I "%ORIGIN%"=="main" goto :main_pull_mode
if /I "%ORIGIN%"=="local" goto :build_mode

:release_mode
echo Mode: release (API from GHCR image)

set "TAG="
call :resolve_release_tag
if errorlevel 1 exit /b 1

if "%XSCANNER_API_IMAGE%"=="" set "XSCANNER_API_IMAGE=ghcr.io/axedras/xscanner:%MODE%-!TAG!"

REM Always derive release label from the resolved tag to avoid mismatches.
set "XSCANNER_RELEASE_TAG=!TAG!"

if "%XSCANNER_STUDIO_IMAGE%"=="" set "XSCANNER_STUDIO_IMAGE=ghcr.io/axedras/xscanner-studio:!TAG!"

echo Origin: %ORIGIN%
echo Mode: %MODE%
if not "!TAG!"=="" echo Release tag: !TAG!
echo API image: %XSCANNER_API_IMAGE%
echo Actions: pull xscanner-api-release xscanner-studio-release ^& up -d xscanner-api-release xscanner-studio-release

docker compose --env-file .env.preprod -f docker-compose.preprod.yml pull xscanner-api-release xscanner-studio-release
if errorlevel 1 exit /b 1

docker compose --env-file .env.preprod -f docker-compose.preprod.yml up -d xscanner-api-release xscanner-studio-release
if errorlevel 1 exit /b 1
goto :done

:build_mode
echo Mode: local (build from current worktree)

if "%XSCANNER_RELEASE_TAG%"=="" call :derive_local_release_tag

echo Origin: %ORIGIN%
echo Mode: %MODE%
echo Release tag: %XSCANNER_RELEASE_TAG%
echo API dockerfile: Dockerfile.%MODE%
echo Actions: up -d --build xscanner-api-build xscanner-studio

docker compose --env-file .env.preprod -f docker-compose.preprod.yml up -d --build xscanner-api-build xscanner-studio
if errorlevel 1 exit /b 1

goto :done

:main_pull_mode
echo Mode: main (pull moving GHCR images)

if "%XSCANNER_API_IMAGE%"=="" set "XSCANNER_API_IMAGE=ghcr.io/axedras/xscanner:%MODE%"
if "%XSCANNER_STUDIO_IMAGE%"=="" set "XSCANNER_STUDIO_IMAGE=ghcr.io/axedras/xscanner-studio:main"

REM Deterministic label for this origin.
set "XSCANNER_RELEASE_TAG=main"

echo Origin: %ORIGIN%
echo Mode: %MODE%
echo API image: %XSCANNER_API_IMAGE%
echo Studio image: %XSCANNER_STUDIO_IMAGE%
echo Actions: pull xscanner-api-release xscanner-studio-release ^& up -d xscanner-api-release xscanner-studio-release

docker compose --env-file .env.preprod -f docker-compose.preprod.yml pull xscanner-api-release xscanner-studio-release
if errorlevel 1 exit /b 1

docker compose --env-file .env.preprod -f docker-compose.preprod.yml up -d xscanner-api-release xscanner-studio-release
if errorlevel 1 exit /b 1

:done

echo Compose is up

exit /b 0

:resolve_release_tag
if /I "%ORIGIN%"=="latest" goto :resolve_latest

echo %ORIGIN% | findstr /I /R "^release-" >NUL
if %errorlevel% neq 0 goto :invalid_origin
set "TAG=%ORIGIN:release-=%"
if /I not "!TAG:~0,1!"=="v" set "TAG=v!TAG!"
exit /b 0

:resolve_latest
gh --version >NUL 2>&1
if %errorlevel% neq 0 goto :err_no_gh

for /f "usebackq delims=" %%T in (`gh release view --repo aXedras/xScanner --json tagName --jq .tagName 2^>NUL`) do set "TAG=%%T"
if not defined TAG goto :err_no_tag
exit /b 0

:err_no_gh
echo Error: gh CLI not found in PATH, required for ORIGIN=latest.
echo Fix: install GitHub CLI or use ORIGIN=release-x.y.z ^(or set XSCANNER_API_IMAGE + XSCANNER_RELEASE_TAG explicitly^).
exit /b 1

:err_no_tag
echo Error: could not resolve latest release tag via gh.
exit /b 1

:invalid_origin
echo Error: invalid ORIGIN ^(expected main^|latest^|release-x.y.z^): %ORIGIN%
exit /b 1

:derive_local_release_tag
REM Deterministic version label for ORIGIN=local deployments.
REM Prefer v<pyproject version>+g<shortsha>. Fall back to v<version> or dev.

set "PYPROJECT_VERSION="
for /f "usebackq delims=" %%V in (`powershell -NoProfile -Command "$m = (Select-String -Path 'pyproject.toml' -Pattern '^version\s*=\s*\"(.+)\"' -List).Matches; if ($m.Count -gt 0) { $m[0].Groups[1].Value }" 2^>NUL`) do set "PYPROJECT_VERSION=%%V"

set "SHORT_SHA="
for /f "usebackq delims=" %%S in (`git rev-parse --short HEAD 2^>NUL`) do set "SHORT_SHA=%%S"

if defined PYPROJECT_VERSION (
	if defined SHORT_SHA (
		set "XSCANNER_RELEASE_TAG=v%PYPROJECT_VERSION%+g%SHORT_SHA%"
	) else (
		set "XSCANNER_RELEASE_TAG=v%PYPROJECT_VERSION%"
	)
) else (
	set "XSCANNER_RELEASE_TAG=dev"
)

git diff --quiet
if errorlevel 1 set "XSCANNER_RELEASE_TAG=%XSCANNER_RELEASE_TAG%-dirty"
git diff --cached --quiet
if errorlevel 1 set "XSCANNER_RELEASE_TAG=%XSCANNER_RELEASE_TAG%-dirty"

exit /b 0
