@echo off
REM Installs prerequisites for Color-Swap-Rivals-2 (Python, Pillow, .NET runtime, FModel)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
echo.
pause
