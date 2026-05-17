@echo off
title Build HMC Fee Management EXE
cd /d "%~dp0"

echo.
echo  HMC Fee Management System - EXE Builder
echo  ==========================================
echo.

echo  Step 1: Installing Python packages...
python -m pip install -r backend\requirements.txt
if errorlevel 1 goto :err

if exist "frontend\dist\index.html" goto :skip_frontend
echo.
echo  Step 2: Building frontend...
cd frontend
call npm install
if errorlevel 1 goto :err
call npm run build
if errorlevel 1 goto :err
cd ..
:skip_frontend
echo  Step 2: Frontend ready.

echo.
echo  Step 3: Installing PyInstaller...
python -m pip install --upgrade pyinstaller
if errorlevel 1 goto :err

echo.
echo  Step 4: Cleaning old build...
if exist "build" rmdir /s /q build
if exist "dist_exe" rmdir /s /q dist_exe

echo.
echo  Step 5: Building EXE [takes 3-5 minutes]...
cd backend
python -m PyInstaller ^
    --name FeeManagement ^
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

echo.
echo  Step 6: Bundling frontend...
xcopy /e /i /y frontend\dist dist_exe\FeeManagement\frontend_dist >nul

echo HMC Fee Management System v1.0 > dist_exe\FeeManagement\README.txt
echo ======================================== >> dist_exe\FeeManagement\README.txt
echo. >> dist_exe\FeeManagement\README.txt
echo To run: double-click FeeManagement.exe >> dist_exe\FeeManagement\README.txt
echo Browser opens at http://localhost:8001 >> dist_exe\FeeManagement\README.txt
echo. >> dist_exe\FeeManagement\README.txt
echo Default login: admin / Admin@1234 >> dist_exe\FeeManagement\README.txt

echo.
echo  ============================================================
echo   BUILD COMPLETE
echo   Output: dist_exe\FeeManagement\FeeManagement.exe
echo   Zip the FeeManagement folder to distribute.
echo  ============================================================
echo.
pause
goto :eof

:err
echo.
echo  BUILD FAILED.
pause
exit /b 1
