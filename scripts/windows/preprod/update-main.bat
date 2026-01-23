@echo off
setlocal EnableExtensions EnableDelayedExpansion

for %%I in ("%~dp0..\..\..") do set "REPO_ROOT=%%~fI"
cd /d "%REPO_ROOT%" || exit /b 1

where git >nul 2>&1
if errorlevel 1 (
  echo Error: git not found in PATH
  exit /b 1
)

echo Updating main branch...
git fetch origin main
if errorlevel 1 exit /b 1
git checkout main
if errorlevel 1 exit /b 1
git pull --ff-only origin main
if errorlevel 1 exit /b 1

for /f %%H in ('git rev-parse --short HEAD') do set "HEAD=%%H"
echo Updated to: %HEAD%
