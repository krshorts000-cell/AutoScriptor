@echo off
cd /d "%~dp0"
title AutoScriptor Local Server

echo ===================================================
echo        AutoScriptor - AI Video Script Cloner
echo ===================================================
echo.
echo Checking dependencies...
python -c "import edge_tts" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing edge-tts for voice generation...
    python -m pip install edge-tts
)

echo Starting local server at http://localhost:8000 ...
echo Press Ctrl+C in this window to stop the server.
echo.

python server.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error starting server. Please check if Python is installed.
    pause
)
