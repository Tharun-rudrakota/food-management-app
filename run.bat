@echo off
echo ========================================================
echo   FreshPantry - Smart Food Inventory & Daily Management
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/2] Checking Python environment...
py --version >nul 2>&1
if %errorlevel% neq 0 (
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python was not found in PATH!
        echo Please ensure Python is installed and added to PATH.
        pause
        exit /b 1
    ) else (
        set PYCMD=python
    )
) else (
    set PYCMD=py
)

echo [2/2] Launching application on http://127.0.0.1:5000 ...
echo.
echo Demo Account:
echo   Username: demo
echo   Password: demo123
echo.
echo Press Ctrl+C in this window to stop the server.
echo.

start http://127.0.0.1:5000
%PYCMD% app.py

pause
