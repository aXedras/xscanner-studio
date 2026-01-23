@echo off
setlocal EnableExtensions EnableDelayedExpansion

for %%I in ("%~dp0..\..\..") do set "REPO_ROOT=%%~fI"
cd /d "%REPO_ROOT%" || exit /b 1

if "%ORIGIN%"=="" set "ORIGIN=latest"

REM Ensure gh is on PATH (Windows installers don't always update PATH for all shells)
set "GH_DIR="
if exist "%ProgramW6432%\GitHub CLI\gh.exe" set "GH_DIR=%ProgramW6432%\GitHub CLI"
if not defined GH_DIR if exist "%ProgramFiles%\GitHub CLI\gh.exe" set "GH_DIR=%ProgramFiles%\GitHub CLI"
if not defined GH_DIR if exist "C:\Program Files\GitHub CLI\gh.exe" set "GH_DIR=C:\Program Files\GitHub CLI"
if defined GH_DIR set "PATH=%GH_DIR%;%PATH%"

where docker >nul 2>&1
if errorlevel 1 goto :err_docker

docker compose version >nul 2>&1
if errorlevel 1 goto :err_compose

where supabase >nul 2>&1
if errorlevel 1 goto :err_supabase

if not exist ".env.preprod" goto :err_env

if /I "%ORIGIN%"=="main" goto :gh_ok

where gh >nul 2>&1
if errorlevel 1 goto :err_gh

gh auth status -h github.com >nul 2>&1
if errorlevel 1 goto :err_gh_auth

:gh_ok

git diff --quiet
if errorlevel 1 goto :dirty
git diff --cached --quiet
if errorlevel 1 goto :dirty

for /f %%B in ('git branch --show-current') do set "BRANCH=%%B"
for /f %%H in ('git rev-parse --short HEAD') do set "HEAD=%%H"
echo Pre-prod prerequisites OK
echo Repo: %REPO_ROOT%
echo Branch: %BRANCH%
echo HEAD: %HEAD%
exit /b 0

:dirty
echo Error: git working tree has uncommitted changes
echo Fix: commit, stash, or deploy from a clean clone
git status -sb
exit /b 1

:err_docker
echo Error: docker not found in PATH
exit /b 1

:err_compose
echo Error: docker compose not available
exit /b 1

:err_supabase
echo Error: supabase CLI not found in PATH
exit /b 1

:err_env
echo Error: missing .env.preprod
echo Create it from .env.preprod.example - do not commit secrets.
exit /b 1

:err_gh
echo Error: gh CLI not found in PATH - required for ORIGIN not main
exit /b 1

:err_gh_auth
echo Error: gh is not authenticated - required for ORIGIN not main
echo Run: gh auth login
exit /b 1
