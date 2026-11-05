@echo off
rem Starts MORIQ AI on this computer and opens it in the browser.
cd /d "%~dp0"
start "" "http://127.0.0.1:5180"
py -3.12 -m moriq.app
pause
