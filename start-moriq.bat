@echo off
rem Starts MORIQ AI on this computer and opens it in the browser.
cd /d "%~dp0"
rem Opens in its own window once the server is up, using Edge app mode.
start "" /min cmd /c "timeout /t 2 /nobreak >nul & start msedge --app=http://127.0.0.1:5180"
py -3.12 -m moriq.app
pause
