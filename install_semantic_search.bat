@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    echo ERROR: run run.bat first, then this file.
    pause
    exit /b 1
)
echo === Installing semantic search (about 1 GB, 5-15 minutes) ===
.venv\Scripts\python -m pip install sentence-transformers
if errorlevel 1 (
    echo ERROR: installation failed. Check your internet connection and try again.
    pause
    exit /b 1
)
echo.
echo === Done. Restart run.bat and choose semantic search. ===
pause
