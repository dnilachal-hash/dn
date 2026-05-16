@echo off
REM ==========================================================================
REM Build the Inno Setup installer
REM Prerequisites: Inno Setup 6+ installed, ISCC.exe in PATH
REM ==========================================================================

echo Step 1: Building frontend...
cd ..\frontend
call npm install
call npm run build
cd ..\installer

echo.
echo Step 2: Downloading bundled assets (if not already present)...
if not exist payload\python\python.exe (
  echo Please download Python 3.11 embeddable zip from python.org/ftp/python/3.11.9/
  echo and extract to installer\payload\python\
  pause
)
if not exist payload\wheels\fastapi-*.whl (
  echo Downloading pip wheels for offline install...
  ..\backend\python -m pip download -r ..\backend\requirements.txt -d payload\wheels
)

echo.
echo Step 3: Compiling installer with Inno Setup...
ISCC.exe setup.iss

echo.
echo Done! Output: installer\output\PayrollSystemSetup_v2.0.0.exe
pause
