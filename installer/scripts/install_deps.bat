@echo off
SET APPDIR=%~dp0
"%APPDIR%python\python.exe" -m pip install --no-index --find-links="%APPDIR%wheels" -r "%APPDIR%backend\requirements.txt"
