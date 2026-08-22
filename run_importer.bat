@echo off
REM Copies FModel-exported palette files into the color-swap tool.
REM Run this AFTER exporting Characters + Platforms from FModel.
cd /d "%~dp0"

REM Always use the tool's own local Python installed by setup.bat, never the
REM user's system Python. Pass args through, e.g.: run_importer.bat --verbose
if exist ".\python-3.12.6.amd64\python.exe" (
    ".\python-3.12.6.amd64\python.exe" ".\files_importer.py" %*
) else (
    echo The tool's local Python was not found.
    echo Run setup.bat once to install it, then try again.
)

echo.
pause
