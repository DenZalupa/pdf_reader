@echo off
cd /d "%~dp0"
if "%~1"=="" (
    start "" pythonw reader.py
) else (
    start "" pythonw reader.py "%~1"
)
exit
