@echo off
REM Start all xScanner services on Windows (development)

setlocal

echo Starting all xScanner services (development)...
echo.

REM Start Supabase (dev) directly via Supabase CLI.
where supabase >NUL 2>&1
if %errorlevel% neq 0 (
	echo Error: supabase CLI not found in PATH
	echo Fix: install Supabase CLI and ensure it is available in this terminal
	exit /b 1
)

echo Starting Supabase...
supabase start
if %errorlevel% neq 0 exit /b %errorlevel%

echo Starting xScanner Server...
start "xScanner Server" cmd /c "scripts\windows\development\start-server.bat"
timeout /t 2 /nobreak >nul

echo Starting xScanner Studio...
cd studio
start "xScanner Studio" cmd /c "npm run dev"
cd ..

echo.
echo All services started!
echo.
echo Supabase Studio:  http://127.0.0.1:56323
echo xScanner Server:  http://localhost:8010/docs
echo xScanner Studio:  http://localhost:8084

endlocal
