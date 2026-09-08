@echo off
title SmartClass Vision Console
cd /d "%~dp0"
echo ========================================================
echo           Starting SmartClass Vision...
echo ========================================================
call "%~dp0venv\Scripts\activate.bat"
"%~dp0venv\Scripts\python.exe" "%~dp0gui.py"
pause
