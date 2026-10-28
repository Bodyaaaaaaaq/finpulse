@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv || goto :error
)
if not exist ".env" copy ".env.example" ".env" >nul

echo Checking dependencies...
if /i "%1"=="test" (
    ".venv\Scripts\python.exe" -m pip install -q -r requirements-dev.txt || goto :error
    ".venv\Scripts\python.exe" -m pytest
    goto :eof
)
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt || goto :error

if /i "%1"=="desktop" (
    ".venv\Scripts\flet.exe" run
) else (
    ".venv\Scripts\flet.exe" run --web
)
goto :eof

:error
echo.
echo Something went wrong. Check that Python is installed and you are online.
pause
