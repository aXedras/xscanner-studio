@echo off
REM Stop Supabase (explicit; preprod-down does not stop it)

supabase stop

exit /b %errorlevel%
