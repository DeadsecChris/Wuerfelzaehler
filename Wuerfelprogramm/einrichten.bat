@echo off
rem ==========================================================================
rem  Wuerfel-Zaehler: Softwareumgebung einrichten
rem  Doppelklick genuegt. Legt .venv in diesem Ordner an und installiert
rem  alles aus requirements.txt. Mit NVIDIA-Grafikkarte wird automatisch
rem  PyTorch mit CUDA installiert. Kann beliebig oft ausgefuehrt werden:
rem  Vorhandenes bleibt, nur Fehlendes wird nachinstalliert.
rem ==========================================================================
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo === Wuerfel-Zaehler: Einrichtung ===
echo Ordner: %CD%
echo.

rem --- 1. Python 3.11 ------------------------------------------------------
py -3.11 --version >nul 2>&1
if not errorlevel 1 goto python_ok
echo Python 3.11 wurde nicht gefunden.
where winget >nul 2>&1
if errorlevel 1 goto python_manuell
choice /c JN /m "Python 3.11 jetzt mit winget installieren"
if errorlevel 2 goto python_manuell
winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
echo.
echo Python wurde installiert. Bitte dieses Fenster schliessen und
echo einrichten.bat noch einmal starten.
goto ende_pause

:python_manuell
echo Bitte Python 3.11 von https://www.python.org installieren
echo (Haken bei "Add python.exe to PATH") und danach einrichten.bat neu starten.
goto ende_pause

:python_ok
for /f "delims=" %%v in ('py -3.11 --version') do echo [OK] %%v

rem --- 2. Virtuelle Umgebung ----------------------------------------------
if exist ".venv\Scripts\python.exe" goto venv_ok
echo Lege virtuelle Umgebung .venv an ...
py -3.11 -m venv .venv
if errorlevel 1 goto fehler
:venv_ok
echo [OK] Virtuelle Umgebung .venv
set "PY=%CD%\.venv\Scripts\python.exe"
"%PY%" -m pip install --upgrade pip --quiet
if errorlevel 1 goto fehler

rem --- 3. PyTorch (mit oder ohne Grafikkarte) -----------------------------
set "GPU=0"
where nvidia-smi >nul 2>&1
if not errorlevel 1 set "GPU=1"

if "%GPU%"=="1" goto torch_gpu

:torch_cpu
"%PY%" -c "import torch" >nul 2>&1
if not errorlevel 1 goto torch_ok
echo Keine NVIDIA-Grafikkarte gefunden: installiere PyTorch fuer die CPU ...
"%PY%" -m pip install torch torchvision
if errorlevel 1 goto fehler
goto torch_ok

:torch_gpu
echo NVIDIA-Grafikkarte gefunden.
"%PY%" -c "import torch, sys; sys.exit(0 if torch.cuda.is_available() else 1)" >nul 2>&1
if not errorlevel 1 goto torch_ok
echo Installiere PyTorch mit CUDA (das sind ca. 3 GB, dauert etwas) ...
"%PY%" -m pip uninstall -y torch torchvision >nul 2>&1
"%PY%" -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
if not errorlevel 1 goto torch_ok
echo CUDA 12.8 hat nicht geklappt, versuche CUDA 12.6 ...
"%PY%" -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
if not errorlevel 1 goto torch_ok
echo CUDA-Variante nicht verfuegbar, installiere CPU-Variante ...
goto torch_cpu

:torch_ok
echo [OK] PyTorch

rem --- 4. Restliche Pakete -------------------------------------------------
echo Installiere bzw. pruefe Pakete aus requirements.txt ...
"%PY%" -m pip install -r requirements.txt --quiet
if errorlevel 1 goto fehler
echo [OK] requirements.txt

rem --- 5. Optional: Label Studio in eigener Umgebung ----------------------
set "LS=%USERPROFILE%\labelstudio-venv"
if exist "%LS%\Scripts\label-studio.exe" goto ls_ok
echo.
choice /c JN /m "Label Studio (zum Labeln der Fotos) auf diesem Rechner installieren"
if errorlevel 2 goto pruefen
py -3.11 -m venv "%LS%"
if errorlevel 1 goto fehler
"%LS%\Scripts\python.exe" -m pip install --upgrade pip --quiet
"%LS%\Scripts\python.exe" -m pip install label-studio
if errorlevel 1 goto fehler
:ls_ok
echo [OK] Label Studio (starten mit labelstudio_starten.bat)

rem --- 6. Pruefen ----------------------------------------------------------
:pruefen
echo.
echo === Pruefung ===
"%PY%" pruefe_umgebung.py
if errorlevel 1 goto fehler
echo.
echo Fertig. Kameratest:  .venv\Scripts\python.exe pruefe_umgebung.py --yolo 0
echo In VS Code den Interpreter ".venv" auswaehlen, dann laeuft alles per Play-Button.
goto ende_pause

:fehler
echo.
echo *** Es ist ein Fehler aufgetreten. Bitte die Meldungen oben an Claude schicken. ***

:ende_pause
echo.
pause
endlocal
