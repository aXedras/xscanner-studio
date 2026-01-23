@echo off
setlocal EnableExtensions EnableDelayedExpansion

for %%I in ("%~dp0..\..\..") do set "REPO_ROOT=%%~fI"
cd /d "%REPO_ROOT%" || exit /b 1

if exist ".env.preprod" goto :env_ok
echo Error: .env.preprod not found. Create it from .env.preprod.example
exit /b 1
:env_ok

if "%ORIGIN%"=="" set "ORIGIN=latest"

if not "%MODE%"=="" goto :mode_set
if /I "%ORIGIN%"=="main" set "MODE=cloud"
if /I not "%ORIGIN%"=="main" set "MODE=full"
:mode_set

if /I "%MODE%"=="cloud" goto :mode_ok
if /I "%MODE%"=="full" goto :mode_ok
echo Error: invalid MODE ^(expected cloud^|full^): %MODE%
exit /b 1
:mode_ok

if /I "%ORIGIN%"=="main" goto :build_mode

:release_mode
echo Starting API + Studio (pre-prod compose, release mode)...

if "%XSCANNER_API_IMAGE%"=="" set "XSCANNER_API_IMAGE=ghcr.io/axedras/xscanner:%MODE%-release"
if "%XSCANNER_RELEASE_TAG%"=="" set "XSCANNER_RELEASE_TAG=dev"

echo Origin: %ORIGIN%
echo Mode: %MODE%
echo API image: %XSCANNER_API_IMAGE%

docker compose --env-file .env.preprod -f docker-compose.preprod.yml pull xscanner-api-release
if errorlevel 1 exit /b 1

docker compose --env-file .env.preprod -f docker-compose.preprod.yml up -d --build xscanner-api-release xscanner-studio
if errorlevel 1 exit /b 1
goto :done

:build_mode
echo Starting API + Studio (pre-prod compose, build mode)...

if "%XSCANNER_RELEASE_TAG%"=="" set "XSCANNER_RELEASE_TAG=dev"

echo Origin: %ORIGIN%
echo Mode: %MODE%
echo API dockerfile: Dockerfile.%MODE%

docker compose --env-file .env.preprod -f docker-compose.preprod.yml up -d --build xscanner-api-build xscanner-studio
if errorlevel 1 exit /b 1

:done

echo Compose is up
