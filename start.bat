@echo off
REM ============================================================
REM  HMC Payroll Management System v2.0 - One-Click Launcher
REM  Method A: Native Python (Windows 10/11)
REM ============================================================
setlocal EnableDelayedExpansion
title HMC Payroll System - Launcher

cd /d "%~dp0"

echo.
echo ============================================================
echo   HMC Payroll Management System v2.0
echo   One-Click Launcher (Windows)
echo ============================================================
echo.

REM --- Step 1: Check Python ---
echo [1/6] Checking Python installation...
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] Python is not installed or not in PATH.
    echo.
    echo  Please install Python 3.11 from:
    echo      https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: During install, tick "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo       Found Python !PYVER!
echo.

REM --- Step 2: Create venv if missing ---
echo [2/6] Setting up virtual environment...
if not exist "backend\.venv\Scripts\python.exe" (
    echo       Creating new venv at backend\.venv ...
    pushd backend
    python -m venv .venv
    if errorlevel 1 (
        echo  [ERROR] Failed to create virtual environment.
        popd
        pause
        exit /b 1
    )
    popd
    echo       Virtual environment created.
) else (
    echo       Virtual environment already exists.
)
echo.

REM --- Step 3: Install Python dependencies ---
echo [3/6] Installing / verifying Python dependencies...
pushd backend
call .venv\Scripts\activate.bat
if not exist ".venv\.deps_installed" (
    echo       First-time install - this may take 3-5 minutes...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo  [ERROR] Failed to install dependencies.
        popd
        pause
        exit /b 1
    )
    echo. > .venv\.deps_installed
    echo       Dependencies installed.
) else (
    echo       Dependencies already installed (skip).
)
popd
echo.

REM --- Step 4: Build frontend if not already built ---
echo [4/6] Checking frontend build...
if not exist "frontend\dist\index.html" (
    echo       Frontend not built yet. Building now...
    echo.

    REM Check if Node.js / npm is available
    where npm >nul 2>&1
    if errorlevel 1 (
        echo  [ERROR] Node.js / npm is not installed or not in PATH.
        echo.
        echo  Please install Node.js (LTS) from:
        echo      https://nodejs.org/
        echo.
        echo  Then run start.bat again.
        echo.
        pause
        exit /b 1
    )

    pushd frontend
    echo       Running: npm install ...
    call npm install
    if errorlevel 1 (
        echo  [ERROR] npm install failed.
        popd
        pause
        exit /b 1
    )

    echo.
    echo       Running: npm run build ...
    call npm run build
    if errorlevel 1 (
        echo  [ERROR] Frontend build failed.
        popd
        pause
        exit /b 1
    )
    popd
    echo.
    echo       Frontend built successfully.
) else (
    echo       Frontend already built (skip).
)
echo.

REM --- Step 5: Launch the server ---
echo [5/6] Starting the payroll server...
echo.
echo ============================================================
echo   Server will be available at:  http://localhost:8000
echo ============================================================
echo.
echo   Default login:  admin  /  Admin@1234
echo.
echo   Keep this window open while using the system.
echo   Close it (or press Ctrl+C) to stop the server.
echo ============================================================
echo.

REM --- Step 6: Open browser after short delay (in background) ---
start "" /b cmd /c "timeout /t 6 /nobreak >nul & start http://localhost:8000"

pushd backend
call .venv\Scripts\activate.bat
python run.py
popd

echo.
echo Server stopped.
pause
endlocal
