@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "STRICT=0"
if "%~1"=="--strict" set "STRICT=1"

set "LATEST=0"
if "%~1"=="--latest" set "LATEST=1"
if "%~2"=="--latest" set "LATEST=1"

for %%I in ("%~dp0..\..\..") do set "REPO_ROOT=%%~fI"
cd /d "%REPO_ROOT%" || exit /b 1

REM Ensure gh is on PATH (Windows installers don't always update PATH for all shells)
set "GH_DIR="
if exist "%ProgramW6432%\GitHub CLI\gh.exe" set "GH_DIR=%ProgramW6432%\GitHub CLI"
if not defined GH_DIR if exist "%ProgramFiles%\GitHub CLI\gh.exe" set "GH_DIR=%ProgramFiles%\GitHub CLI"
if not defined GH_DIR if exist "C:\Program Files\GitHub CLI\gh.exe" set "GH_DIR=C:\Program Files\GitHub CLI"
if defined GH_DIR set "PATH=%GH_DIR%;%PATH%"

gh --version >NUL 2>&1
if errorlevel 1 (
  if "%STRICT%"=="1" (
    echo Error: gh CLI not installed; cannot verify CI status
    exit /b 1
  )
  echo Warning: gh CLI not installed; skipping CI verification
  exit /b 0
)

gh auth status -h github.com >NUL 2>&1
if errorlevel 1 (
  if "%STRICT%"=="1" (
    echo Error: gh is not authenticated; cannot verify CI status
    exit /b 1
  )
  echo Warning: gh is not authenticated; skipping CI verification
  exit /b 0
)

set "MATCHED_CONCLUSION="
if "%LATEST%"=="1" (
  for /f "delims=" %%C in ('gh api "repos/aXedras/xScanner/actions/workflows/ci.yml/runs?branch=main^&per_page=1" --jq ".workflow_runs[0].conclusion" 2^>NUL') do (
    set "MATCHED_CONCLUSION=%%C"
    goto :got_ci
  )
) else (
  set "HEAD_SHA="
  for /f "delims=" %%S in ('git rev-parse HEAD 2^>NUL') do set "HEAD_SHA=%%S"
  if not defined HEAD_SHA (
    echo Error: cannot read HEAD sha
    exit /b 1
  )

  for /f "delims=" %%C in ('gh api "repos/aXedras/xScanner/actions/workflows/ci.yml/runs?branch=main^&per_page=50" --jq ".workflow_runs[] | select(.head_sha == \"!HEAD_SHA!\") | .conclusion" 2^>NUL') do (
    set "MATCHED_CONCLUSION=%%C"
    goto :got_ci
  )
)
:got_ci

if not defined MATCHED_CONCLUSION (
  if "%STRICT%"=="1" (
    if "%LATEST%"=="1" (
      echo Error: cannot verify latest CI for branch main
    ) else (
      echo Error: cannot verify CI for sha !HEAD_SHA!
      echo Ensure gh is authenticated and the workflow run exists for this commit.
    )
    exit /b 1
  )
  if "%LATEST%"=="1" (
    echo Warning: cannot verify latest CI for branch main; continuing
  ) else (
    echo Warning: cannot verify CI for sha !HEAD_SHA!; continuing
  )
  exit /b 0
)

if /I not "!MATCHED_CONCLUSION!"=="success" (
  if "%LATEST%"=="1" (
    echo Error: latest CI run for main is not successful (conclusion=!MATCHED_CONCLUSION!)
  ) else (
    echo Error: CI for sha !HEAD_SHA! is not successful (conclusion=!MATCHED_CONCLUSION!)
  )
  exit /b 1
)

if "%LATEST%"=="1" (
  echo Latest CI successful for branch: main
) else (
  echo CI successful for sha: !HEAD_SHA!
)
exit /b 0
