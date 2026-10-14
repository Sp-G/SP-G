@echo off
cd /d "%~dp0"

if exist .venv\installed.ok goto run

echo === First run: installing MotiveCut (3-10 minutes) ===
if not exist .venv\Scripts\python.exe (
    where py >nul 2>nul && py -3 -m venv .venv
    if not exist .venv\Scripts\python.exe python -m venv .venv
)
if not exist .venv\Scripts\python.exe (
    echo.
    echo ERROR: Python not found. Install it from https://www.python.org/downloads/
    echo and check "Add python.exe to PATH" in the installer.
    pause
    exit /b 1
)
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: installation failed. Check your internet connection and run run.bat again.
    pause
    exit /b 1
)
echo ok> .venv\installed.ok

:run
chcp 65001 >nul
echo === MotiveCut is starting. Do not close this window. ===
echo === If the browser did not open, go to http://127.0.0.1:7860 ===
.venv\Scripts\python -m motivecut
pause
