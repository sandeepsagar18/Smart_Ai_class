@echo off
title SmartClass Vision
cd /d "%~dp0"
call "%~dp0venv\Scripts\activate.bat"
start "" "%~dp0venv\Scripts\python.exe" "%~dp0gui.py"
exit
