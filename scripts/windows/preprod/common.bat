@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Shared helpers for Windows pre-prod scripts.
REM Usage:
REM   call "%~dp0common.bat" :preprod_parse_args %*
REM   call "%~dp0common.bat" :preprod_normalize_origin
REM   call "%~dp0common.bat" :preprod_normalize_mode
REM   call "%~dp0common.bat" :preprod_apply_default_mode
REM
REM This file is intended to be called via label invocation.

goto :eof

:preprod_parse_args
REM Parse optional KEY=VALUE args.
REM - Supports ORIGIN=... and MODE=...
REM - Errors for unknown keys to avoid silent fallback to defaults.
REM - Explicitly errors for common typo: origin=... / mode=...

:preprod_parse_args_loop
if "%~1"=="" exit /b 0

set "ARG=%~1"

echo %ARG% | findstr /I /B "origin=" >NUL
if not errorlevel 1 (
	echo Error: unknown parameter "origin". Use ORIGIN=main^|local^|latest^|release-x.y.z.
	exit /b 2
)

echo %ARG% | findstr /I /B "mode=" >NUL
if not errorlevel 1 (
	echo Error: unknown parameter "mode". Use MODE=cloud^|full.
	exit /b 2
)

REM Allow ORIGIN=... / MODE=...
if /I "%ARG:~0,7%"=="ORIGIN=" (
	set "ORIGIN=%ARG:~7%"
	shift
	goto :preprod_parse_args_loop
)
if /I "%ARG:~0,5%"=="MODE=" (
	set "MODE=%ARG:~5%"
	shift
	goto :preprod_parse_args_loop
)

REM Any other KEY=VALUE is treated as unknown.
echo %ARG% | findstr "=" >NUL
if not errorlevel 1 (
	for /f "tokens=1 delims==" %%K in ("%ARG%") do set "KEY=%%K"
	echo Error: unknown parameter "%KEY%".
	echo Fix: use ORIGIN=... and MODE=... as environment variables or pass them as ORIGIN=... MODE=... args.
	exit /b 2
)

REM Non key-value args are not supported.
echo Error: unexpected argument "%ARG%".
exit /b 2

:preprod_normalize_origin
if "%ORIGIN%"=="" exit /b 0

REM Be tolerant to common make/shell typos like ORIGIN=latest,
if "%ORIGIN:~-1%"=="," set "ORIGIN=%ORIGIN:~0,-1%"

if /I "%ORIGIN%"=="main" set "ORIGIN=main" & exit /b 0
if /I "%ORIGIN%"=="local" set "ORIGIN=local" & exit /b 0
if /I "%ORIGIN%"=="latest" set "ORIGIN=latest" & exit /b 0

REM Normalize release- prefix, keep suffix as provided (git tags are case-sensitive).
if /I "%ORIGIN:~0,8%"=="release-" (
	set "ORIGIN=release-%ORIGIN:~8%"
	exit /b 0
)

exit /b 0

:preprod_normalize_mode
if "%MODE%"=="" exit /b 0

REM Be tolerant to common make/shell typos like MODE=full,
if "%MODE:~-1%"=="," set "MODE=%MODE:~0,-1%"

if /I "%MODE%"=="cloud" set "MODE=cloud" & exit /b 0
if /I "%MODE%"=="full" set "MODE=full" & exit /b 0

exit /b 0

:preprod_apply_default_mode
REM Default MODE based on ORIGIN:
REM - ORIGIN=main|local => cloud
REM - ORIGIN=latest|release-* => full
if not "%MODE%"=="" exit /b 0

if /I "%ORIGIN%"=="main" set "MODE=cloud" & exit /b 0
if /I "%ORIGIN%"=="local" set "MODE=cloud" & exit /b 0

set "MODE=full"
exit /b 0
