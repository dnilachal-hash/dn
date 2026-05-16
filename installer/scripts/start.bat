@echo off
REM HMC Payroll System launcher
SET APPDIR=%~dp0
SET PYTHON=%APPDIR%python\python.exe
SET BACKEND=%APPDIR%backend
cd /d "%BACKEND%"
echo Starting HMC Payroll System on http://localhost:8000 ...
"%PYTHON%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
