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

set "MAX_ATTEMPTS=%PREPROD_HEALTH_MAX_ATTEMPTS%"
if "%MAX_ATTEMPTS%"=="" set "MAX_ATTEMPTS=30"

for /L %%I in (1,1,%MAX_ATTEMPTS%) do (
  curl -fsS "%API_URL%" >NUL 2>&1
  if not errorlevel 1 (
    echo API healthy
    exit /b 0
  )

  echo Waiting: API not ready yet (attempt %%I/%MAX_ATTEMPTS%)
  timeout /t 1 /nobreak >NUL
)

echo API healthcheck failed
exit /b 1
