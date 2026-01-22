@echo off
REM Start or check Supabase for Windows

setlocal enabledelayedexpansion

REM Colors for Windows
set "GREEN=[92m"
set "BLUE=[94m"
set "NC=[0m"

REM Check if Supabase is already running
supabase status >nul 2>&1
if %errorlevel% equ 0 (
    echo %GREEN%Supabase is already running%NC%
    exit /b 0
)

REM Start Supabase
echo %BLUE%Starting Supabase...%NC%
supabase start

exit /b %errorlevel%
