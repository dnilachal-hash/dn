@echo off
title HMC Payroll System
cd /d "%~dp0"

echo.
echo  HMC Payroll Management System v2.0
echo  ====================================
echo.

REM ---- Python pip install ----
echo  Step 1: Installing Python packages...
python -m pip install -r backend\requirements.txt
if errorlevel 1 ( echo ERROR: pip install failed & pause & exit /b 1 )

REM ---- Frontend build (skip if already done) ----
if not exist "frontend\dist\index.html" (
    echo.
    echo  Step 2: Building frontend (first time only, ~2 min)...
    cd frontend
    call npm install
    call npm run build
    cd ..
    if not exist "frontend\dist\index.html" ( echo ERROR: frontend build failed & pause & exit /b 1 )
) else (
    echo  Step 2: Frontend already built.
)

REM ---- Start server ----
echo.
echo  ====================================
echo   Open browser to: http://localhost:8000
echo   Login:  admin / Admin@1234
echo   Close this window to stop the server.
echo  ====================================
echo.
start "" /b cmd /c "timeout /t 5 /nobreak >nul & start http://localhost:8000"

cd backend
python run.py
