@echo off
setlocal EnableExtensions

for %%I in ("%~dp0..\..\..") do set "REPO_ROOT=%%~fI"
cd /d "%REPO_ROOT%" || exit /b 1

if not exist ".env.preprod" (
  echo Error: .env.preprod not found. Create it from .env.preprod.example
  exit /b 1
)

echo Stopping API + Studio (pre-prod compose)...
echo Note: Supabase will keep running
echo Note: also removing orphan containers (safe for this compose project)

docker compose --env-file .env.preprod -f docker-compose.preprod.yml down --remove-orphans
if errorlevel 1 exit /b 1

echo Compose is down
