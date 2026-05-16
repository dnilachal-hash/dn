@echo off
title Build HMC Payroll Installer
cd /d "%~dp0"

echo.
echo  HMC Payroll System - Installer Builder
echo  ========================================
echo.

REM Step 1: Make sure the PyInstaller bundle exists (build it if not)
if exist "dist_exe\PayrollSystem\PayrollSystem.exe" goto :have_bundle

echo  Step 1: PyInstaller bundle not found. Running build_exe.bat first...
call build_exe.bat
if errorlevel 1 goto :err
if not exist "dist_exe\PayrollSystem\PayrollSystem.exe" goto :err_nobundle
goto :iscc

:have_bundle
echo  Step 1: PyInstaller bundle found.

:iscc
echo.
echo  Step 2: Locating Inno Setup compiler (ISCC.exe)...

set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
where ISCC.exe >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%I in ('where ISCC.exe') do set "ISCC=%%I"
)

if not defined ISCC goto :err_iscc
echo         Using: %ISCC%

echo.
echo  Step 3: Compiling installer...
cd installer
if not exist "output" mkdir output
"%ISCC%" setup_exe.iss
if errorlevel 1 goto :err_compile
cd ..

echo.
echo  ============================================================
echo   INSTALLER BUILT SUCCESSFULLY
echo  ============================================================
echo.
echo   Output:  installer\output\PayrollSystemSetup_v2.0.0.exe
echo.
echo   Copy this single .exe to any Windows 10/11 PC and
echo   double-click to install. No Python or Node required
echo   on the target machine.
echo  ============================================================
echo.
pause
goto :eof

:err
echo.
echo  BUILD FAILED during build_exe.bat.
pause
exit /b 1

:err_nobundle
echo.
echo  ERROR: dist_exe\PayrollSystem\PayrollSystem.exe was not produced.
pause
exit /b 1

:err_iscc
echo.
echo  ERROR: Inno Setup compiler (ISCC.exe) not found.
echo.
echo  Install Inno Setup 6 from:
echo     https://jrsoftware.org/isdl.php
echo.
echo  Default install path is:
echo     C:\Program Files (x86)\Inno Setup 6\ISCC.exe
echo.
pause
exit /b 1

:err_compile
echo.
echo  ERROR: Inno Setup compilation failed.
cd ..
pause
exit /b 1
