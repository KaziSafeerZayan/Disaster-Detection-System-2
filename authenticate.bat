@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Run start.bat once to install the project, then try again.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" authenticate_gee.py %*
pause
