@echo off
REM xScanner Server Starter for Windows
REM Equivalent to scripts/start-server.sh

setlocal enabledelayedexpansion

REM Colors for Windows (limited support)
set "BLUE=[94m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "NC=[0m"

if "%1"=="-h" goto :show_help
if "%1"=="--help" goto :show_help
goto :start

:show_help
echo %BLUE%xScanner Server Starter%NC%
echo.
echo Usage: %0 [PORT] [-h^|--help]
echo.
echo Arguments:
echo   PORT          Server port (overrides SERVER_PORT from .env)
echo.
echo Options:
echo   -h, --help    Show this help message
echo.
echo Configuration:
echo   Port is determined in the following order:
echo   1. Command-line argument (highest priority)
echo   2. SERVER_PORT in .env.local
echo   3. SERVER_PORT in .env
echo.
echo Examples:
echo   %0              # Use SERVER_PORT from .env or .env.local
echo   %0 8001         # Start on port 8001
exit /b 0

:start
REM Navigate to project root
cd /d "%~dp0\..\..\"

REM Load environment variables from .env.local or .env
set "PORT="
if exist ".env.local" (
    for /f "usebackq tokens=1,2 delims==" %%a in (".env.local") do (
        if "%%a"=="SERVER_PORT" set "SERVER_PORT=%%b"
        if "%%a"=="SUPABASE_URL" set "SUPABASE_URL=%%b"
        if "%%a"=="SUPABASE_KEY" set "SUPABASE_KEY=%%b"
    )
) else if exist ".env" (
    for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
        if "%%a"=="SERVER_PORT" set "SERVER_PORT=%%b"
        if "%%a"=="SUPABASE_URL" set "SUPABASE_URL=%%b"
        if "%%a"=="SUPABASE_KEY" set "SUPABASE_KEY=%%b"
    )
)

REM Use command-line argument or fallback to SERVER_PORT
if not "%1"=="" (
    set "PORT=%1"
) else (
    set "PORT=%SERVER_PORT%"
)

if "%PORT%"=="" (
    echo %YELLOW%Error: No port configured!%NC%
    echo.
    echo Please either:
    echo   1. Set SERVER_PORT in .env or .env.local
    echo   2. Provide port as argument: %0 ^<PORT^>
    echo.
    echo Run '%0 --help' for more information.
    exit /b 1
)

echo %BLUE%Starting xScanner Server...%NC%
echo %GREEN%Port: %PORT%%NC%
echo %GREEN%Docs: http://localhost:%PORT%/docs%NC%
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo %YELLOW%Error: Virtual environment not found!%NC%
    echo.
    echo Please run: python -m venv venv
    echo Then run:    make dev
    exit /b 1
)

REM Set PYTHONPATH to include src directory
set PYTHONPATH=%CD%\src;%PYTHONPATH%

REM Use venv's Python directly to run uvicorn without reload (Windows multiprocessing issue)
venv\Scripts\python.exe -m uvicorn xscanner.server.server:app --host 0.0.0.0 --port %PORT%
