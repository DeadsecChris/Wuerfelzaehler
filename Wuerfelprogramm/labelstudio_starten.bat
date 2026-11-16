@echo off
rem Startet Label Studio aus der eigenen Umgebung (angelegt von einrichten.bat).
set "LS=%USERPROFILE%\labelstudio-venv"
if not exist "%LS%\Scripts\label-studio.exe" (
    echo Label Studio ist noch nicht installiert. Bitte zuerst einrichten.bat ausfuehren.
    pause
    exit /b 1
)
echo Label Studio startet, der Browser oeffnet http://localhost:8080
echo Zum Beenden dieses Fenster schliessen.
"%LS%\Scripts\label-studio.exe" start
