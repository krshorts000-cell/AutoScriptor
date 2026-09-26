@echo off
cd /d "%~dp0"
title AutoScriptor Local Server

echo ===================================================
echo        AutoScriptor - AI Video Script Cloner
echo ===================================================
echo.
echo Starting local server at http://localhost:8000 ...
echo Press Ctrl+C in this window to stop the server.
echo.

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python server.py
    goto end
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py server.py
    goto end
)

echo [ERROR] Python not found in PATH!
echo Please install Python from https://python.org or Microsoft Store.
pause

:end
