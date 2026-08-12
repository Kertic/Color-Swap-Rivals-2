# Color-Swap-Rivals-2 prerequisite installer
# Installs: Python 3.12 (+ Pillow), .NET 8 Desktop Runtime, FModel.
# Run via setup.bat, or:  powershell -ExecutionPolicy Bypass -File setup.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }

# ---------------------------------------------------------------- winget check
$winget = Get-Command winget -ErrorAction SilentlyContinue
if (-not $winget) {
    Write-Host "winget (Windows Package Manager) was not found." -ForegroundColor Red
    Write-Host "Install 'App Installer' from the Microsoft Store, then re-run this script."
    exit 1
}

# ---------------------------------------------------------------- Python
Write-Step "Python"
$embedded = Join-Path $root "python-3.12.6.amd64\python.exe"
$havePython = $false
if (Test-Path $embedded) {
    Write-Host "Embedded Python found - nothing to install."
    $havePython = $true
} else {
    $sysPy = Get-Command python -ErrorAction SilentlyContinue
    if ($sysPy -and ((& python --version 2>&1) -match "Python 3")) {
        Write-Host "System Python found: $(& python --version 2>&1)"
        $havePython = $true
    } else {
        Write-Host "Installing Python 3.12 via winget..."
        winget install --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
        # Refresh PATH for this session so pip works below
        $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                    [Environment]::GetEnvironmentVariable("Path", "User")
        $havePython = [bool](Get-Command python -ErrorAction SilentlyContinue)
    }
}

# ---------------------------------------------------------------- Pillow
Write-Step "Pillow (image library)"
if (Test-Path $embedded) {
    Write-Host "Embedded Python already bundles Pillow - skipping."
} elseif ($havePython) {
    python -m pip install --quiet --upgrade pillow
    Write-Host "Pillow installed."
} else {
    Write-Host "Python unavailable - skipped. Re-run setup after installing Python." -ForegroundColor Yellow
}

# ---------------------------------------------------------------- .NET runtime (FModel dependency)
Write-Step ".NET 8 Desktop Runtime (needed by FModel)"
$dotnetOk = $false
$dotnet = Get-Command dotnet -ErrorAction SilentlyContinue
if ($dotnet) {
    $runtimes = & dotnet --list-runtimes 2>$null
    if ($runtimes -match "Microsoft.WindowsDesktop.App 8\.") { $dotnetOk = $true }
}
if ($dotnetOk) {
    Write-Host "Already installed."
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
    $release = Invoke-RestMethod "https://api.github.com/repos/4sval/FModel/releases/latest"
    $asset = $release.assets | Where-Object { $_.name -eq "FModel.zip" } | Select-Object -First 1
    if (-not $asset) { $asset = $release.assets | Where-Object { $_.name -like "*.zip" } | Select-Object -First 1 }
    if (-not $asset) {
        Write-Host "Could not find a FModel zip in the latest release - download it manually from https://fmodel.app" -ForegroundColor Yellow
    } else {
        $zip = Join-Path $env:TEMP "FModel.zip"
        Invoke-WebRequest $asset.browser_download_url -OutFile $zip
        New-Item -ItemType Directory -Force -Path $fmodelDir | Out-Null
        Expand-Archive -Path $zip -DestinationPath $fmodelDir -Force
        Remove-Item $zip
        Write-Host "FModel $($release.tag_name) installed to $fmodelDir"
    }
}

# ---------------------------------------------------------------- Summary
Write-Step "Done"
Write-Host "Launch the tool with Start.vbs."
Write-Host "The 'Update Game Data' button will find FModel in the FModel subfolder automatically."
