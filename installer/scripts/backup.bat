@echo off
REM Backup SQLite DB and uploaded data
SET APPDIR=%~dp0
SET STAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%
SET STAMP=%STAMP: =0%
SET BACKUPDIR=%APPDIR%data\backups\backup_%STAMP%
mkdir "%BACKUPDIR%" 2>NUL
copy "%APPDIR%backend\payroll.db" "%BACKUPDIR%\payroll.db" 2>NUL
xcopy /E /Y /I "%APPDIR%data\uploads" "%BACKUPDIR%\uploads" 2>NUL
echo Backup saved to %BACKUPDIR%
pause
