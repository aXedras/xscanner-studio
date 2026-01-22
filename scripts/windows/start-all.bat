@echo off
REM Start all xScanner services on Windows

setlocal enabledelayedexpansion

REM Colors
set "BLUE=[94m"
set "GREEN=[92m"
set "NC=[0m"

echo %BLUE%Starting all xScanner services...%NC%
echo.

REM 1. Start Supabase
call scripts\windows\preprod\database-start.bat
if %errorlevel% neq 0 (
    echo Failed to start Supabase
    exit /b 1
)

REM 2. Start FastAPI server in background
echo %BLUE%Starting xScanner Server...%NC%
start "xScanner Server" cmd /c "scripts\windows\development\start-server.bat"
timeout /t 2 /nobreak >nul

REM 3. Start Studio in background
echo %BLUE%Starting xScanner Studio...%NC%
cd studio
start "xScanner Studio" cmd /c "npm run dev"
cd ..

echo.
echo %GREEN%All services started!%NC%
echo.
echo Supabase Studio:  http://127.0.0.1:56323
echo xScanner Server:  http://localhost:8010/docs
echo xScanner Studio:  http://localhost:8084
echo.
echo Press Ctrl+C in the respective terminal windows to stop services
