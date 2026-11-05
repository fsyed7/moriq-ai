@echo off
rem Starts MORIQ AI on this computer and shows any startup errors. For normal use, run install-moriq.ps1 once and use the icon.
cd /d "%~dp0"
start "" /min cmd /c "timeout /t 2 /nobreak >nul & start msedge --app=http://127.0.0.1:5180/"
py -3.12 -m moriq.app
pause
