@echo off
REM Pre-prod deploy on Windows VM
REM Flow: update main (ff-only) -> ensure Supabase running -> docker compose up

setlocal

cd /d "%~dp0\..\..\.."

echo Updating main...
git fetch origin main
if %errorlevel% neq 0 exit /b %errorlevel%

git checkout main
if %errorlevel% neq 0 exit /b %errorlevel%

git pull --ff-only origin main
if %errorlevel% neq 0 exit /b %errorlevel%

if not exist ".env.preprod" (
  echo Missing .env.preprod - create it from .env.preprod.example
  exit /b 1
)

call scripts\windows\preprod\database-start.bat
if %errorlevel% neq 0 exit /b %errorlevel%

echo Starting API + Studio...
docker compose --env-file .env.preprod -f docker-compose.preprod.yml up -d --build
if %errorlevel% neq 0 exit /b %errorlevel%

echo Healthcheck...
curl -fsS http://127.0.0.1:8010/health >nul
if %errorlevel% neq 0 (
  echo Healthcheck failed
  exit /b 1
)

echo Deploy complete
exit /b 0
