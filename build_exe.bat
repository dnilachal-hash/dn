@echo off
title Build HMC Payroll EXE
cd /d "%~dp0"

echo.
echo  HMC Payroll System - EXE Builder
echo  ==================================
echo.

REM Step 1: Build frontend
if exist "frontend\dist\index.html" goto :skip_frontend
echo  Step 1: Building frontend...
cd frontend
call npm install
if errorlevel 1 goto :err
call npm run build
if errorlevel 1 goto :err
cd ..
:skip_frontend
echo  Step 1: Frontend ready.

REM Step 2: Install PyInstaller
echo.
echo  Step 2: Installing PyInstaller...
python -m pip install --upgrade pyinstaller
if errorlevel 1 goto :err

REM Step 3: Clean previous build
echo.
echo  Step 3: Cleaning old build...
if exist "build" rmdir /s /q build
if exist "dist_exe" rmdir /s /q dist_exe

REM Step 4: Run PyInstaller
echo.
echo  Step 4: Building EXE [takes 3-5 minutes]...
cd backend
python -m PyInstaller ^
    --name PayrollSystem ^
    --onedir ^
    --noconfirm ^
    --clean ^
    --distpath ..\dist_exe ^
    --workpath ..\build ^
    --add-data "app;app" ^
    --collect-all uvicorn ^
    --collect-all fastapi ^
    --collect-all sqlalchemy ^
    --collect-all pydantic ^
    --collect-all reportlab ^
    --collect-all openpyxl ^
    --collect-all pandas ^
    --collect-all cryptography ^
    --collect-all bcrypt ^
    --collect-all jose ^
    --collect-all email_validator ^
    --hidden-import app.main ^
    --hidden-import app.seed ^
    --hidden-import app.models ^
    --hidden-import app.routers ^
    --hidden-import app.services ^
    launcher.py
if errorlevel 1 goto :err
cd ..

REM Step 5: Copy frontend dist into the bundle
echo.
echo  Step 5: Bundling frontend...
xcopy /e /i /y frontend\dist dist_exe\PayrollSystem\frontend_dist >nul
if errorlevel 1 goto :err

REM Step 6: Create a friendly README inside the bundle
echo HMC Payroll Management System v2.0 > dist_exe\PayrollSystem\README.txt
echo ============================================ >> dist_exe\PayrollSystem\README.txt
echo. >> dist_exe\PayrollSystem\README.txt
echo To run: double-click PayrollSystem.exe >> dist_exe\PayrollSystem\README.txt
echo Browser opens automatically at http://localhost:8000 >> dist_exe\PayrollSystem\README.txt
echo. >> dist_exe\PayrollSystem\README.txt
echo Default login: admin / Admin@1234 >> dist_exe\PayrollSystem\README.txt
echo. >> dist_exe\PayrollSystem\README.txt
echo Database file (payroll.db) is saved next to the .exe. >> dist_exe\PayrollSystem\README.txt
echo Copy the entire PayrollSystem folder to back up. >> dist_exe\PayrollSystem\README.txt

echo.
echo  ============================================================
echo   BUILD COMPLETE
echo  ============================================================
echo.
echo   Output folder:  dist_exe\PayrollSystem\
echo   Main file:      dist_exe\PayrollSystem\PayrollSystem.exe
echo.
echo   To distribute:
echo     1. Zip the entire PayrollSystem folder
echo     2. Copy to any Windows 10/11 PC
echo     3. Unzip and double-click PayrollSystem.exe
echo.
echo   No Python install needed on the target PC.
echo  ============================================================
echo.
pause
goto :eof

:err
echo.
echo  BUILD FAILED.
pause
exit /b 1
