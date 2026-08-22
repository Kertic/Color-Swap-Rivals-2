# Color-Swap-Rivals-2 prerequisite installer
# Installs: a local, self-contained Python 3.12 (+ Pillow), .NET 8 Desktop Runtime, FModel.
# Run via setup.bat, or:  powershell -ExecutionPolicy Bypass -File setup.ps1

# Native tools (winget, python) write to stderr on harmless conditions, which
# would abort the whole script under "Stop". Failures are checked explicitly
# via $LASTEXITCODE instead.
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }

# The tool always runs on its OWN bundled Python, never the user's system
# install. Recent system Pythons break the UI (e.g. Python 3.14 ships Tcl/Tk 9,
# which the tkinter build here needs), and a system Python may be missing
# tkinter or a working Pillow entirely. Keeping our own copy sidesteps all of it.
$localPythonDir = Join-Path $root "python-3.12.6.amd64"
$localPythonExe = Join-Path $localPythonDir "python.exe"

function Test-LocalPython {
    # Utilisable = présent ET capable d'importer tkinter (le maillon qui casse | Usable = present AND able to import tkinter (the piece that breaks on recent
    # sur les Python système récents). | system Pythons).
    if (-not (Test-Path $localPythonExe)) { return $false }
    & $localPythonExe -c "import tkinter" 2>$null
    return ($LASTEXITCODE -eq 0)
}

function Install-LocalPython {
    # Installe un Python 3.12 autonome DANS le dossier de l'outil. On utilise les | Installs a self-contained Python 3.12 INTO the tool's folder. We use the
    # builds "python-build-standalone" : un CPython relogeable qui embarque | "python-build-standalone" builds: a relocatable CPython that bundles tkinter
    # tkinter ET pip, sans installateur, sans admin, sans toucher au PATH. | AND pip, with no installer, no admin rights, and no PATH changes.
    if (-not (Get-Command tar -ErrorAction SilentlyContinue)) {
        Write-Host "The 'tar' command is required to unpack Python and was not found." -ForegroundColor Yellow
        Write-Host "It ships with Windows 10 (1803+) and Windows 11 - update Windows and retry."
        return $false
    }
    try {
        $headers = @{ "User-Agent" = "Color-Swap-Rivals-2-setup" }
        $rel = Invoke-RestMethod "https://api.github.com/repos/astral-sh/python-build-standalone/releases/latest" -Headers $headers
        $asset = $rel.assets | Where-Object {
            $_.name -match '^cpython-3\.12\.\d+\+.*-x86_64-pc-windows-msvc-install_only\.tar\.gz$'
        } | Select-Object -First 1
        if (-not $asset) {
            Write-Host "No suitable Python 3.12 build was found in the latest release." -ForegroundColor Yellow
            return $false
        }
        $archive = Join-Path $env:TEMP "cpython-local.tar.gz"
        Write-Host "Downloading $($asset.name)..."
        Invoke-WebRequest $asset.browser_download_url -OutFile $archive -Headers $headers
        # L'archive contient un dossier racine "python" : on extrait dans un | The archive contains a top-level "python" folder: extract into a temp dir,
        # dossier temporaire puis on le renomme vers python-3.12.6.amd64. | then rename it to python-3.12.6.amd64.
        $staging = Join-Path $env:TEMP ("cpython-local-" + [guid]::NewGuid().ToString("N"))
        New-Item -ItemType Directory -Force -Path $staging | Out-Null
        tar -xf $archive -C $staging
        $inner = Join-Path $staging "python"
        if (-not (Test-Path (Join-Path $inner "python.exe"))) {
            Write-Host "The downloaded Python archive had an unexpected layout." -ForegroundColor Yellow
            return $false
        }
        if (Test-Path $localPythonDir) { Remove-Item -Recurse -Force $localPythonDir }
        Move-Item $inner $localPythonDir
        Remove-Item $archive -Force -ErrorAction SilentlyContinue
        Remove-Item $staging -Recurse -Force -ErrorAction SilentlyContinue
        return $true
    } catch {
        Write-Host "Download failed: $($_.Exception.Message)" -ForegroundColor Yellow
        return $false
    }
}

# ---------------------------------------------------------------- Python (local, self-contained)
Write-Step "Python (local, self-contained)"
if (Test-LocalPython) {
    Write-Host "Local Python already present - nothing to install."
} else {
    if (Test-Path $localPythonExe) {
        Write-Host "Local Python is present but not working; reinstalling..." -ForegroundColor Yellow
    } else {
        Write-Host "Installing a self-contained Python 3.12 (with tkinter) into the tool folder..."
    }
    if ((Install-LocalPython) -and (Test-LocalPython)) {
        Write-Host "Local Python installed to $localPythonDir" -ForegroundColor Green
    } else {
        Write-Host "Could not set up the local Python automatically." -ForegroundColor Red
        Write-Host "Check your internet connection and run setup.bat again."
    }
}
$python = if (Test-Path $localPythonExe) { $localPythonExe } else { $null }

# Record the local interpreter so run_importer.bat can find it directly.
$pythonPathFile = Join-Path $root "python_path.txt"
if ($python) {
    # No BOM: Set-Content -Encoding UTF8 prepends one under PowerShell 5.1,
    # which ends up inside the path when .bat/.vbs read the file back.
    [System.IO.File]::WriteAllText($pythonPathFile, $python,
        (New-Object System.Text.UTF8Encoding $false))
}

# ---------------------------------------------------------------- Pillow (into the local Python)
Write-Step "Pillow (image library)"
if (-not $python) {
    Write-Host "Skipped - the local Python is not set up yet." -ForegroundColor Yellow
} else {
    # Tester l'import réel utilisé par l'outil (Image + ImageTk), pas seulement | Test the real import the tool uses (Image + ImageTk), not just that PIL is
    # que PIL existe : ImageTk dépend de tkinter et peut échouer seul. | present: ImageTk depends on tkinter and can fail on its own.
    & $python -c "from PIL import Image, ImageTk" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Already installed."
    } else {
        Write-Host "Installing Pillow into the local Python..."
        & $python -m pip --version 2>$null
        if ($LASTEXITCODE -ne 0) { & $python -m ensurepip --upgrade | Out-Null }
        & $python -m pip install --quiet --upgrade pillow
        & $python -c "from PIL import Image, ImageTk" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Pillow installed."
        } else {
            Write-Host "pip failed. Try manually: `"$python`" -m pip install pillow" -ForegroundColor Yellow
        }
    }
}

# winget is used only by the .NET step below (Python no longer needs it).
$winget = Get-Command winget -ErrorAction SilentlyContinue

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
    if ($LASTEXITCODE -ne 0) {
        # Sans blocage : le runtime ne sert qu'à FModel, donc à la réparation | Not a blocker: the runtime is only needed by FModel, i.e. for repairs
        Write-Host "winget could not install it (exit $LASTEXITCODE)." -ForegroundColor Yellow
        Write-Host "This is only needed for the 'Update Game Data' repair flow -"
        Write-Host "everything else works without it. To install it later:"
        Write-Host "  https://dotnet.microsoft.com/download/dotnet/8.0"
    }
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
    Write-Host "The local Python did not install. Fix your connection and run setup.bat again before using Start.vbs." -ForegroundColor Yellow
}
Write-Host "The 'Update Game Data' button will find FModel in the FModel subfolder automatically."
