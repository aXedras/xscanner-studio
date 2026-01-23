@echo off
setlocal EnableExtensions

set "API_URL=%PREPROD_API_URL%"
if "%API_URL%"=="" set "API_URL=http://127.0.0.1:8010/health"

echo Healthcheck: %API_URL%

where curl >NUL 2>&1
if errorlevel 1 (
  echo Error: curl not found on PATH
  exit /b 1
)

curl -fsS "%API_URL%" >NUL
if errorlevel 1 (
  echo API healthcheck failed
  exit /b 1
)

echo API healthy
