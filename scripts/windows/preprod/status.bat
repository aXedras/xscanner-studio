@echo off
setlocal EnableExtensions

for %%I in ("%~dp0..\..\..") do set "REPO_ROOT=%%~fI"
cd /d "%REPO_ROOT%" || exit /b 1

if not exist ".env.preprod" (
  echo Error: .env.preprod not found. Create it from .env.preprod.example
  exit /b 1
)

echo Supabase:
where supabase >NUL 2>&1
if errorlevel 1 (
  echo ^(supabase CLI not found^)
) else (
  supabase status
)

echo.
echo Compose:
docker compose --env-file .env.preprod -f docker-compose.preprod.yml ps
if errorlevel 1 exit /b 1
