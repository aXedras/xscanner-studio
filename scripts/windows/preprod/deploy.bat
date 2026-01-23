@echo off
REM Pre-prod deploy on Windows VM
REM Flow:
REM - ORIGIN=main: check -> update main (ff-only) -> verify-ci-main --strict -> database-start -> up -> health
REM - ORIGIN=latest|release-x.y.z: resolve tag -> check -> checkout tag -> verify-ci-sha --strict -> database-start -> up -> health

setlocal EnableExtensions EnableDelayedExpansion

REM Inputs (provided via environment; Makefile exports variables)
if "%ORIGIN%"=="" set "ORIGIN=latest"

if "%MODE%"=="" (
	if /I "%ORIGIN%"=="main" (
		set "MODE=cloud"
	) else (
		set "MODE=full"
	)
)

call :validate_mode
if %errorlevel% neq 0 exit /b %errorlevel%

cd /d "%~dp0\..\..\.."

REM Ensure gh is on PATH (Windows installers don't always update PATH for all shells)
set "GH_DIR="
if exist "%ProgramW6432%\GitHub CLI\gh.exe" set "GH_DIR=%ProgramW6432%\GitHub CLI"
if not defined GH_DIR if exist "%ProgramFiles%\GitHub CLI\gh.exe" set "GH_DIR=%ProgramFiles%\GitHub CLI"
if not defined GH_DIR if exist "C:\Program Files\GitHub CLI\gh.exe" set "GH_DIR=C:\Program Files\GitHub CLI"
if defined GH_DIR set "PATH=%GH_DIR%;%PATH%"

REM Deploy
if /I "%ORIGIN%"=="main" goto deploy_main
if /I "%ORIGIN%"=="latest" goto deploy_latest

echo %ORIGIN% | findstr /I /R "^release-" >NUL
if %errorlevel% neq 0 goto invalid_origin
set "TAG=%ORIGIN:release-=%"
if /I not "!TAG:~0,1!"=="v" set "TAG=v!TAG!"
goto deploy_release

:deploy_latest
gh --version >NUL 2>&1
if %errorlevel% neq 0 goto err_no_gh
gh release view --repo aXedras/xScanner --json tagName --jq .tagName >NUL 2>&1
if %errorlevel% neq 0 goto err_no_releases
for /f "usebackq delims=" %%T in (`gh release view --repo aXedras/xScanner --json tagName --jq .tagName 2^>NUL`) do set "TAG=%%T"
if not defined TAG goto err_no_tag
goto deploy_release

:err_no_gh
echo Error: gh CLI not found in PATH. Install GitHub CLI or set ORIGIN=release-x.y.z.
exit /b 1

:err_no_releases
echo Error: no GitHub Releases found for aXedras/xScanner.
echo Tip: use ORIGIN=main (local build) or ORIGIN=release-x.y.z once releases exist.
exit /b 1

:err_no_tag
echo Error: could not resolve latest release tag via gh.
exit /b 1

:deploy_main
echo Origin: main (deploy from main HEAD, local build)
echo Mode: %MODE%

set "ORIGIN=main"
call scripts\windows\preprod\check.bat
if %errorlevel% neq 0 exit /b %errorlevel%

call scripts\windows\preprod\update-main.bat
if %errorlevel% neq 0 exit /b %errorlevel%

call scripts\windows\preprod\verify-ci-main.bat --strict
if %errorlevel% neq 0 exit /b %errorlevel%

call scripts\windows\preprod\database-start.bat
if %errorlevel% neq 0 exit /b %errorlevel%

call scripts\windows\preprod\up.bat
if %errorlevel% neq 0 exit /b %errorlevel%

call scripts\windows\preprod\health.bat
if %errorlevel% neq 0 exit /b %errorlevel%

echo Deploy complete
exit /b 0


:deploy_release
echo Origin: %ORIGIN%
echo Mode: %MODE%
echo Release tag: !TAG!

REM For releases, check requires gh + auth and a clean worktree.
call scripts\windows\preprod\check.bat
if %errorlevel% neq 0 exit /b %errorlevel%

set "ORIGINAL_REF="
for /f "usebackq delims=" %%B in (`git branch --show-current 2^>NUL`) do set "ORIGINAL_REF=%%B"

git fetch --tags origin
if %errorlevel% neq 0 exit /b %errorlevel%

git checkout "!TAG!"
if %errorlevel% neq 0 (
	echo Error: failed to checkout tag !TAG!
	if defined ORIGINAL_REF git checkout "!ORIGINAL_REF!" >NUL 2>&1
	exit /b 1
)

REM Guard: release tags must include the Windows preprod helper scripts.
if not exist "scripts\windows\preprod\up.bat" goto missing_windows_helpers
if not exist "scripts\windows\preprod\health.bat" goto missing_windows_helpers
if not exist "scripts\windows\preprod\database-start.bat" goto missing_windows_helpers
if not exist "scripts\windows\preprod\verify-ci-sha.bat" goto missing_windows_helpers

call scripts\windows\preprod\verify-ci-sha.bat --strict
if %errorlevel% neq 0 exit /b %errorlevel%

if not defined XSCANNER_API_IMAGE set "XSCANNER_API_IMAGE=ghcr.io/axedras/xscanner:%MODE%-!TAG!"
if not defined XSCANNER_RELEASE_TAG set "XSCANNER_RELEASE_TAG=!TAG!"

call scripts\windows\preprod\database-start.bat
if %errorlevel% neq 0 exit /b %errorlevel%

call scripts\windows\preprod\up.bat
if %errorlevel% neq 0 exit /b %errorlevel%

call scripts\windows\preprod\health.bat
if %errorlevel% neq 0 exit /b %errorlevel%

if defined ORIGINAL_REF (
	git checkout "!ORIGINAL_REF!" >NUL 2>&1
)

echo Deploy complete
exit /b 0

:missing_windows_helpers
echo Error: release tag !TAG! does not contain required Windows preprod helper scripts.
echo Fix: create a new release that includes scripts/windows/preprod/*.bat.
if defined ORIGINAL_REF git checkout "!ORIGINAL_REF!" >NUL 2>&1
exit /b 1

:invalid_origin
echo Error: invalid ORIGIN (expected main^|latest^|release-x.y.z): %ORIGIN%
exit /b 1

:validate_mode
if /I "%MODE%"=="cloud" exit /b 0
if /I "%MODE%"=="full" exit /b 0
echo Error: invalid MODE (expected cloud^|full): %MODE%
exit /b 1


