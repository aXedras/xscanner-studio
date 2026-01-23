@echo off
setlocal EnableExtensions

for %%I in ("%~dp0..\..\..") do set "REPO_ROOT=%%~fI"
cd /d "%REPO_ROOT%" || exit /b 1

if not exist ".env.preprod" (
  echo Error: .env.preprod not found. Create it from .env.preprod.example
  exit /b 1
)

docker compose --env-file .env.preprod -f docker-compose.preprod.yml logs -f --tail=200
