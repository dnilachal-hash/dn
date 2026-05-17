@echo off
title HMC Fee Management System
cd /d "%~dp0"

echo.
echo  HMC Fee Management System v1.0
echo  =================================
echo.

echo  Step 1: Installing Python packages...
python -m pip install -r backend\requirements.txt
if errorlevel 1 goto :err_pip

if exist "frontend\dist\index.html" goto :run

echo.
echo  Step 2: Building frontend [first time only, ~2 min]...
cd frontend
call npm install
if errorlevel 1 goto :err_npm
call npm run build
if errorlevel 1 goto :err_build
cd ..

:run
echo.
echo  ====================================
echo   Open browser: http://localhost:8001
echo   Login:        admin / Admin@1234
echo   Stop:         close this window
echo  ====================================
echo.
start "" /b cmd /c "timeout /t 5 /nobreak >nul & start http://localhost:8001"
cd backend
python run.py
goto :eof

:err_pip
echo.
echo  ERROR: pip install failed.
pause & exit /b 1

:err_npm
echo.
echo  ERROR: npm install failed.
pause & exit /b 1

:err_build
echo.
echo  ERROR: npm run build failed.
pause & exit /b 1
