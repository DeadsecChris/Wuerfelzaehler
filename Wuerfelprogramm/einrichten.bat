@echo off
rem Wuerfel-Zaehler: Softwareumgebung einrichten (Doppelklick genuegt).
rem Die eigentliche Arbeit macht einrichten.ps1, das Protokoll steht in einrichten.log.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0einrichten.ps1"
if errorlevel 1 pause
