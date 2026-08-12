@echo off
REM Copies FModel-exported palette files into the color-swap tool.
REM Run this AFTER exporting Characters + Platforms from FModel.
cd /d "%~dp0"

REM 1. Embedded Python shipped alongside the tool
if exist ".\python-3.12.6.amd64\python.exe" (
    ".\python-3.12.6.amd64\python.exe" ".\files_importer.py"
    goto done
)

REM 2. Interpreter recorded by setup.bat (PATH often hits the Store stub)
if exist ".\python_path.txt" (
    set /p PYEXE=<".\python_path.txt"
    if exist "%PYEXE%" (
        "%PYEXE%" ".\files_importer.py"
        goto done
    )
)

REM 3. The py launcher resolves real installs
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 ".\files_importer.py"
    goto done
)

echo Python was not found. Run setup.bat first to install the prerequisites.

:done
echo.
pause
