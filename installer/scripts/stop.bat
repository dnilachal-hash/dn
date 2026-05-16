@echo off
echo Stopping HMC Payroll System ...
taskkill /F /IM python.exe /T 2>NUL
echo Stopped.
pause
