@echo off
REM Start or check Supabase (pre-prod)

setlocal enabledelayedexpansion

REM Check if Supabase is already running
supabase status >nul 2>&1
if %errorlevel% equ 0 (
    echo Supabase is already running
    exit /b 0
)

echo Starting Supabase...
supabase start

exit /b %errorlevel%
