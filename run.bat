@echo off
chcp 65001 > nul
echo ===================================================
echo        AutoScriptor - AI Video Script Cloner
echo ===================================================
echo.
echo Запуск локального сервера...
python server.py
if errorlevel 1 (
    echo.
    echo Ошибка при запуске. Убедитесь, что Python установлен.
    pause
)
