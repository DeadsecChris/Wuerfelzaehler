# ==========================================================================
#  Wuerfel-Zaehler: Softwareumgebung einrichten
#  Start per Doppelklick auf einrichten.bat. Alles, was hier passiert, wird
#  zusaetzlich in einrichten.log mitgeschrieben (zum Nachsehen bei Fehlern).
#  Kann beliebig oft laufen: Vorhandenes bleibt, nur Fehlendes wird installiert.
# ==========================================================================
$ErrorActionPreference = "Continue"
Set-Location -LiteralPath $PSScriptRoot
$log = Join-Path $PSScriptRoot "einrichten.log"
try { Start-Transcript -Path $log -Force | Out-Null } catch {}

function Schritt($text) { Write-Host ""; Write-Host "=== $text ===" -ForegroundColor Cyan }
function Ok($text)      { Write-Host "[OK] $text" -ForegroundColor Green }
function Fehler($text) {
    Write-Host ""
    Write-Host "*** FEHLER: $text ***" -ForegroundColor Red
    Write-Host "Bitte einrichten.log (im Ordner Wuerfelprogramm) an Claude schicken."
    try { Stop-Transcript | Out-Null } catch {}
    Read-Host "Enter druecken zum Beenden"
    exit 1
}

# Liefert den Pfad einer passenden python.exe (3.10 bis 3.13, bevorzugt 3.11) oder $null
function Finde-Python {
    $pruef = "import sys; v=sys.version_info; print(sys.executable) if (3,10)<=v[:2]<=(3,13) else sys.exit(1)"
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($v in "3.11", "3.12", "3.10", "3.13") {
            $exe = & py "-$v" -c $pruef 2>$null
            if ($LASTEXITCODE -eq 0 -and $exe) { return ($exe | Select-Object -Last 1).Trim() }
        }
    }
    foreach ($kandidat in @(
        "python",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "C:\Program Files\Python311\python.exe",
        "C:\Program Files\Python312\python.exe")) {
        if ($kandidat -ne "python" -and -not (Test-Path $kandidat)) { continue }
        if ($kandidat -eq "python" -and -not (Get-Command python -ErrorAction SilentlyContinue)) { continue }
        $exe = & $kandidat -c $pruef 2>$null
        if ($LASTEXITCODE -eq 0 -and $exe) { return ($exe | Select-Object -Last 1).Trim() }
    }
    return $null
}

Write-Host "Wuerfel-Zaehler: Einrichtung" -ForegroundColor Cyan
Write-Host "Ordner: $PSScriptRoot"
Write-Host "Protokoll: $log"

# --- 1. Python --------------------------------------------------------------
Schritt "1. Python suchen"
$python = Finde-Python
if (-not $python) {
    Write-Host "Kein passendes Python (3.10 bis 3.13) gefunden."
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        $a = Read-Host "Python 3.11 jetzt mit winget installieren? (j/n)"
        if ($a -match "^[jJyY]") {
            winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
            $python = Finde-Python
        }
    }
    if (-not $python) {
        Fehler "Python fehlt. Bitte Python 3.11 von python.org installieren (Haken bei 'Add python.exe to PATH') und einrichten.bat erneut starten."
    }
}
$pyVersion = & $python --version 2>&1
Ok "$pyVersion  ($python)"

# --- 2. Virtuelle Umgebung --------------------------------------------------
Schritt "2. Virtuelle Umgebung .venv"
$venvPy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPy) {
    & $venvPy -c "import sys" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Vorhandene .venv ist defekt, lege sie neu an ..."
        Remove-Item -Recurse -Force (Join-Path $PSScriptRoot ".venv")
    }
}
if (-not (Test-Path $venvPy)) {
    Write-Host "Lege .venv an ..."
    & $python -m venv (Join-Path $PSScriptRoot ".venv")
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $venvPy)) { Fehler "Die virtuelle Umgebung konnte nicht angelegt werden." }
}
Ok ".venv ($venvPy)"
& $venvPy -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -ne 0) { Fehler "pip konnte nicht aktualisiert werden (Internetverbindung?)." }

# --- 3. PyTorch -------------------------------------------------------------
Schritt "3. PyTorch"
$gpu = $false
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) { $gpu = $true }
try {
    $karten = Get-CimInstance Win32_VideoController -ErrorAction Stop | Select-Object -ExpandProperty Name
    Write-Host "Grafikkarten: $($karten -join ', ')"
    if ($karten -match "NVIDIA") { $gpu = $true }
} catch {}

& $venvPy -c "import torch" 2>$null
$torchDa = ($LASTEXITCODE -eq 0)
$cudaDa = $false
if ($torchDa) {
    & $venvPy -c "import torch, sys; sys.exit(0 if torch.cuda.is_available() else 1)" 2>$null
    $cudaDa = ($LASTEXITCODE -eq 0)
}

if ($gpu) {
    Write-Host "NVIDIA-Grafikkarte erkannt."
    if (-not $cudaDa) {
        if ($torchDa) { & $venvPy -m pip uninstall -y torch torchvision }
        Write-Host "Installiere PyTorch mit CUDA (ca. 3 GB, dauert etwas) ..."
        $fertig = $false
        foreach ($cu in "cu128", "cu126", "cu124") {
            & $venvPy -m pip install torch torchvision --index-url "https://download.pytorch.org/whl/$cu"
            if ($LASTEXITCODE -eq 0) { $fertig = $true; Write-Host "PyTorch mit $cu installiert."; break }
            Write-Host "$cu nicht verfuegbar, versuche die naechste Variante ..."
        }
        if (-not $fertig) {
            Write-Host "Keine CUDA-Variante verfuegbar, installiere die CPU-Variante."
            & $venvPy -m pip install torch torchvision
            if ($LASTEXITCODE -ne 0) { Fehler "PyTorch konnte nicht installiert werden." }
        }
    }
} elseif (-not $torchDa) {
    Write-Host "Keine NVIDIA-Grafikkarte: installiere PyTorch fuer die CPU ..."
    & $venvPy -m pip install torch torchvision
    if ($LASTEXITCODE -ne 0) { Fehler "PyTorch konnte nicht installiert werden." }
}
Ok "PyTorch"

# --- 4. requirements.txt ----------------------------------------------------
Schritt "4. Pakete aus requirements.txt"
& $venvPy -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { Fehler "Pakete aus requirements.txt konnten nicht installiert werden." }
# albumentations bringt oft opencv-python-headless mit. Das ueberschreibt cv2 ohne
# Fenster-Funktionen (cv2.imshow geht dann nicht). Deshalb nur opencv-python behalten.
& $venvPy -m pip show opencv-python-headless *> $null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Ersetze opencv-python-headless durch opencv-python (fuer Kamerafenster) ..."
    & $venvPy -m pip uninstall -y opencv-python-headless opencv-python
    & $venvPy -m pip install opencv-python
    if ($LASTEXITCODE -ne 0) { Fehler "opencv-python konnte nicht installiert werden." }
}
Ok "requirements.txt"

# --- 5. Label Studio (optional, eigene Umgebung) ----------------------------
Schritt "5. Label Studio (optional)"
$lsDir = Join-Path $env:USERPROFILE "labelstudio-venv"
$lsExe = Join-Path $lsDir "Scripts\label-studio.exe"
if (Test-Path $lsExe) {
    Ok "Label Studio ist installiert (Start mit labelstudio_starten.bat)"
} else {
    $a = Read-Host "Label Studio (zum Labeln der Fotos) auf diesem Rechner installieren? (j/n)"
    if ($a -match "^[jJyY]") {
        & $python -m venv $lsDir
        & (Join-Path $lsDir "Scripts\python.exe") -m pip install --upgrade pip --quiet
        & (Join-Path $lsDir "Scripts\python.exe") -m pip install label-studio
        if ($LASTEXITCODE -ne 0) { Fehler "Label Studio konnte nicht installiert werden." }
        Ok "Label Studio (Start mit labelstudio_starten.bat)"
    } else {
        Write-Host "Uebersprungen."
    }
}

# --- 6. Pruefen -------------------------------------------------------------
Schritt "6. Pruefung"
$env:PYTHONIOENCODING = "utf-8"
$pruefung = & $venvPy (Join-Path $PSScriptRoot "pruefe_umgebung.py") 2>&1
$pruefCode = $LASTEXITCODE
$pruefung | ForEach-Object { Write-Host $_ }
if ($pruefCode -ne 0) { Fehler "Die Pruefung hat fehlende Pakete gemeldet." }

Write-Host ""
Write-Host "Fertig. Kameratest:" -ForegroundColor Green
Write-Host "  .venv\Scripts\python.exe pruefe_umgebung.py --yolo 0"
Write-Host "In VS Code den Interpreter '.venv' auswaehlen (Strg+Umschalt+P -> Python: Select Interpreter)."
try { Stop-Transcript | Out-Null } catch {}
Read-Host "Enter druecken zum Beenden"
