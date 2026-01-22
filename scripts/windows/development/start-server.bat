@echo off
REM xScanner Server Starter for Windows

setlocal enabledelayedexpansion

if "%1"=="-h" goto :show_help
if "%1"=="--help" goto :show_help
goto :start

:show_help
echo xScanner Server Starter
echo.
echo Usage: %0 [PORT] [-h^|--help]
echo.
echo Arguments:
echo   PORT          Server port (overrides SERVER_PORT from .env)
echo.
echo Options:
echo   -h, --help    Show this help message
exit /b 0

:start
cd /d "%~dp0\..\..\.."

REM Load SERVER_PORT from .env.local or .env
set "PORT="
if exist ".env.local" (
    for /f "usebackq tokens=1,2 delims==" %%a in (".env.local") do (
        if "%%a"=="SERVER_PORT" set "SERVER_PORT=%%b"
    )
) else if exist ".env" (
    for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
        if "%%a"=="SERVER_PORT" set "SERVER_PORT=%%b"
    )
)

if not "%1"=="" (
    set "PORT=%1"
) else (
    set "PORT=%SERVER_PORT%"
)

if "%PORT%"=="" (
    echo Error: No port configured!
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    echo Error: Virtual environment not found!
    exit /b 1
)

set PYTHONPATH=%CD%\src;%PYTHONPATH%
venv\Scripts\python.exe -m uvicorn xscanner.server.server:app --host 0.0.0.0 --port %PORT%
