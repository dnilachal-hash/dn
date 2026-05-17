@echo off
title Build HMC Fee Management Installer
cd /d "%~dp0"

echo.
echo  HMC Fee Management System - Installer Builder
echo  ================================================
echo.

if exist "dist_exe\FeeManagement\FeeManagement.exe" goto :iscc

echo  Step 1: PyInstaller bundle not found. Running build_exe.bat first...
call build_exe.bat
if errorlevel 1 goto :err
if not exist "dist_exe\FeeManagement\FeeManagement.exe" goto :err

:iscc
echo  Step 1: PyInstaller bundle found.
echo.
echo  Step 2: Locating Inno Setup compiler...

set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe"      set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
where ISCC.exe >nul 2>&1
if not errorlevel 1 (for /f "delims=" %%I in ('where ISCC.exe') do set "ISCC=%%I")

if not defined ISCC goto :err_iscc
echo         Using: %ISCC%

echo.
echo  Step 3: Compiling installer...
cd installer
if not exist output mkdir output
"%ISCC%" setup_fee.iss
if errorlevel 1 goto :err_compile
cd ..

echo.
echo  ============================================================
echo   INSTALLER BUILT SUCCESSFULLY
echo   Output: installer\output\FeeManagementSetup_v1.0.0.exe
echo  ============================================================
echo.
pause
goto :eof

:err
echo  BUILD FAILED.
pause & exit /b 1

:err_iscc
echo  ERROR: Inno Setup (ISCC.exe) not found.
echo  Install from: https://jrsoftware.org/isdl.php
pause & exit /b 1

:err_compile
echo  ERROR: Inno Setup compilation failed.
cd ..
pause & exit /b 1
