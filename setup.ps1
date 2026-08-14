# Color-Swap-Rivals-2 prerequisite installer
# Installs: Python 3 (+ Pillow), .NET 8 Desktop Runtime, FModel.
# Run via setup.bat, or:  powershell -ExecutionPolicy Bypass -File setup.ps1

# Native tools (winget, python) write to stderr on harmless conditions, which
# would abort the whole script under "Stop". Failures are checked explicitly
# via $LASTEXITCODE instead.
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }

function Test-PythonExe($exe) {
    # A real Python 3 interpreter, not the Microsoft Store placeholder
    if (-not $exe) { return $false }
    if (-not (Test-Path $exe)) { return $false }
    if ($exe -like "*\WindowsApps\*") { return $false }
    $major = & $exe -c "import sys; print(sys.version_info.major)"
    return ($LASTEXITCODE -eq 0 -and $major -eq "3")
}

function Find-Python {
    # 1) The py launcher resolves real installs and never the Store stub
    $pyCmd = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($pyCmd) {
        $resolved = & $pyCmd.Source -3 -c "import sys; print(sys.executable)"
        if ($LASTEXITCODE -eq 0 -and $resolved) {
            $resolved = $resolved.Trim()
            if (Test-PythonExe $resolved) { return $resolved }
        }
    }
    # 2) python.exe entries on PATH, skipping the Store alias
    foreach ($cmd in @(Get-Command python.exe -All -ErrorAction SilentlyContinue)) {
        if (Test-PythonExe $cmd.Source) { return $cmd.Source }
    }
    # 3) Standard install locations
    $patterns = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python3*\python.exe"),
        (Join-Path $env:ProgramFiles "Python3*\python.exe"),
        "C:\Python3*\python.exe"
    )
    foreach ($pattern in $patterns) {
        foreach ($file in @(Get-ChildItem $pattern -ErrorAction SilentlyContinue | Sort-Object FullName -Descending)) {
            if (Test-PythonExe $file.FullName) { return $file.FullName }
        }
    }
    return $null
}

function Update-SessionPath {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
}

# ---------------------------------------------------------------- winget check
$winget = Get-Command winget -ErrorAction SilentlyContinue

# ---------------------------------------------------------------- Python
Write-Step "Python"
$python = $null
$embedded = Join-Path $root "python-3.12.6.amd64\python.exe"
if (Test-Path $embedded) {
    Write-Host "Embedded Python found - nothing to install."
    $python = $embedded
} else {
    $python = Find-Python
    if ($python) {
        Write-Host "Found Python: $python"
    } elseif (-not $winget) {
        Write-Host "Python is not installed and winget is unavailable." -ForegroundColor Red
        Write-Host "Install Python 3 from https://www.python.org/downloads/ then re-run setup.bat."
    } else {
        Write-Host "Installing Python 3.12 via winget..."
        winget install --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
        Update-SessionPath
        $python = Find-Python
        if ($python) {
            Write-Host "Installed: $python"
        } else {
            Write-Host "Python was installed but could not be located." -ForegroundColor Yellow
            Write-Host "Close this window, open a new one, and run setup.bat again."
        }
    }
}

# Record the interpreter so Start.vbs / run_importer.bat do not depend on PATH
# (where the Microsoft Store stub often shadows the real python.exe).
$pythonPathFile = Join-Path $root "python_path.txt"
if ($python -and (Test-Path $python)) {
    # No BOM: Set-Content -Encoding UTF8 prepends one under PowerShell 5.1,
    # which ends up inside the path when .bat/.vbs read the file back.
    [System.IO.File]::WriteAllText($pythonPathFile, $python,
        (New-Object System.Text.UTF8Encoding $false))
    Write-Host "Recorded interpreter in python_path.txt"
}

# ---------------------------------------------------------------- Pillow
Write-Step "Pillow (image library)"
if (-not $python) {
    Write-Host "Skipped - no Python available yet." -ForegroundColor Yellow
} else {
    # find_spec instead of a plain import: no traceback printed when missing
    $hasPillow = & $python -c "import importlib.util; print('ok' if importlib.util.find_spec('PIL') else 'no')"
    if ($LASTEXITCODE -eq 0 -and $hasPillow -eq "ok") {
        Write-Host "Already installed."
    } else {
        Write-Host "Installing Pillow..."
        & $python -m pip install --quiet --upgrade pillow
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Pillow installed."
        } else {
            Write-Host "pip failed. Try manually: `"$python`" -m pip install pillow" -ForegroundColor Yellow
        }
    }
}

# ---------------------------------------------------------------- .NET runtime (FModel dependency)
Write-Step ".NET 8 Desktop Runtime (needed by FModel)"
$dotnetOk = $false
$dotnet = Get-Command dotnet -ErrorAction SilentlyContinue
if ($dotnet) {
    $runtimes = & $dotnet.Source --list-runtimes
    if ($LASTEXITCODE -eq 0 -and ($runtimes -match "Microsoft.WindowsDesktop.App 8\.")) { $dotnetOk = $true }
}
if ($dotnetOk) {
    Write-Host "Already installed."
} elseif (-not $winget) {
    Write-Host "winget unavailable - install the .NET 8 Desktop Runtime manually from" -ForegroundColor Yellow
    Write-Host "https://dotnet.microsoft.com/download/dotnet/8.0 (needed only for Update Game Data)."
} else {
    Write-Host "Installing via winget (may show a UAC prompt)..."
    winget install --id Microsoft.DotNet.DesktopRuntime.8 --silent --accept-package-agreements --accept-source-agreements
}

# ---------------------------------------------------------------- FModel
Write-Step "FModel"
$fmodelDir = Join-Path $root "FModel"
$fmodelExe = Join-Path $fmodelDir "FModel.exe"
if (Test-Path $fmodelExe) {
    Write-Host "Already present at $fmodelExe"
} else {
    Write-Host "Downloading latest FModel release from GitHub..."
    try {
        $release = Invoke-RestMethod "https://api.github.com/repos/4sval/FModel/releases/latest"
        $asset = $release.assets | Where-Object { $_.name -eq "FModel.zip" } | Select-Object -First 1
        if (-not $asset) { $asset = $release.assets | Where-Object { $_.name -like "*.zip" } | Select-Object -First 1 }
        if (-not $asset) {
            Write-Host "No FModel zip in the latest release - download it from https://fmodel.app" -ForegroundColor Yellow
        } else {
            $zip = Join-Path $env:TEMP "FModel.zip"
            Invoke-WebRequest $asset.browser_download_url -OutFile $zip
            New-Item -ItemType Directory -Force -Path $fmodelDir | Out-Null
            Expand-Archive -Path $zip -DestinationPath $fmodelDir -Force
            Remove-Item $zip -ErrorAction SilentlyContinue
            Write-Host "FModel $($release.tag_name) installed to $fmodelDir"
        }
    } catch {
        Write-Host "Download failed: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "Get FModel manually from https://fmodel.app (only needed for Update Game Data)."
    }
}

# ---------------------------------------------------------------- Summary
Write-Step "Done"
if ($python) {
    Write-Host "Launch the tool with Start.vbs." -ForegroundColor Green
} else {
    Write-Host "Install Python 3, then run setup.bat again before using Start.vbs." -ForegroundColor Yellow
}
Write-Host "The 'Update Game Data' button will find FModel in the FModel subfolder automatically."
