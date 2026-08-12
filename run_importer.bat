@echo off
REM Copies FModel-exported palette files into the color-swap tool.
REM Run this AFTER exporting Characters + Platforms from FModel.
cd /d "%~dp0"
if exist ".\python-3.12.6.amd64\python.exe" (
    ".\python-3.12.6.amd64\python.exe" ".\files_importer.py"
) else (
    python ".\files_importer.py"
)
echo.
pause
