# Einrichtung der Softwareumgebung

Für den Laptop (Entwicklung, Programm) und den Gaming-PC (Training). Auf beiden Rechnern gleich, nur Schritt 4 unterscheidet sich. Dauer: ca. 30–45 Minuten pro Rechner.

## Kurzfassung: automatisch einrichten

1. Git und VS Code installieren (Schritt 1), Repo holen (Schritt 2).
2. Im Ordner `Wuerfelprogramm` **`einrichten.bat` doppelklicken.** Das Skript
   - prüft Python 3.11 und bietet an, es per `winget` zu installieren,
   - legt die virtuelle Umgebung `.venv` an,
   - installiert PyTorch passend zum Rechner (mit NVIDIA-Grafikkarte automatisch die CUDA-Variante),
   - installiert alles aus `requirements.txt`,
   - fragt, ob Label Studio in einer eigenen Umgebung mitinstalliert werden soll (Start dann mit `labelstudio_starten.bat`),
   - prüft am Ende alles mit `pruefe_umgebung.py`.
3. Das Skript kann beliebig oft laufen. Vorhandenes bleibt, nur Fehlendes wird nachinstalliert (z. B. nach neuen Einträgen in `requirements.txt`).

Die folgenden Schritte beschreiben dasselbe von Hand, falls das Skript hängt.

## 1. Programme installieren

| Programm | Woher | Hinweis |
|---|---|---|
| Python 3.11 | python.org → Downloads → Windows | Beim Installieren **„Add python.exe to PATH“** ankreuzen |
| Git | git-scm.com | Standardeinstellungen reichen |
| Visual Studio Code | code.visualstudio.com | danach Erweiterung **„Python“** (Microsoft) installieren |
| Nur Gaming-PC: aktueller NVIDIA-Treiber | nvidia.com oder GeForce Experience | Prüfen in der Eingabeaufforderung: `nvidia-smi` zeigt die Grafikkarte |

Prüfen in einer neuen Eingabeaufforderung (PowerShell):
```
py -3.11 --version
git --version
```

## 2. Repo holen

- **Laptop:** Der Repo-Ordner ist schon da (`...\KI_Würfelzähler\Wuerfelzaehler`). Darin den neuesten Stand holen:
  ```
  git pull
  ```
- **Gaming-PC:** Repo klonen:
  ```
  git clone https://github.com/DeadsecChris/Wuerfelzaehler.git
  ```

Den Ordner `Wuerfelzaehler` dann in VS Code öffnen (Datei → Ordner öffnen).

## 3. Virtuelle Umgebung anlegen

Im VS-Code-Terminal (Terminal → Neues Terminal), im Ordner `Wuerfelprogramm`:
```
cd Wuerfelprogramm
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
```
Vorne in der Zeile steht jetzt `(.venv)`. Die Umgebung muss bei jedem neuen Terminal wieder aktiviert werden (`.venv\Scripts\activate`).

Falls PowerShell das Aktivieren blockiert („Ausführung von Skripts ist deaktiviert“), einmalig:
```
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

In VS Code unten rechts den Interpreter `.venv` auswählen (Strg+Umschalt+P → „Python: Select Interpreter“), dann nutzt auch der Play-Button die richtige Umgebung.

## 4. PyTorch installieren

- **Laptop ohne NVIDIA-Grafikkarte:**
  ```
  pip install torch torchvision
  ```
- **Gaming-PC mit NVIDIA-Grafikkarte:** Auf https://pytorch.org unter „Get Started“ wählen: Stable, Windows, Pip, Python, und die höchste angebotene CUDA-Version. Den angezeigten Befehl kopieren, er sieht etwa so aus:
  ```
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu12x
  ```
  Wichtig: PyTorch **vor** Schritt 5 installieren, sonst holt Ultralytics die Version ohne Grafikkarten-Unterstützung.

## 5. Restliche Pakete

```
pip install -r requirements.txt
```
Das installiert Ultralytics (YOLO), OpenCV, Albumentations und NumPy.

## 6. Umgebung prüfen

```
python pruefe_umgebung.py
```
Alle Zeilen sollten mit `OK` beginnen. Auf dem Gaming-PC muss bei `torch` der Name der Grafikkarte stehen, sonst Schritt 4 wiederholen (`pip uninstall torch torchvision`, dann CUDA-Variante neu installieren).

Kamera testen (Fenster schließt mit Taste `q`):
```
python pruefe_umgebung.py --kamera 0
```
Kein Bild? `--kamera 1` oder `--kamera 2` probieren (USB-Webcam hat oft eine andere Nummer).

Test mit vortrainiertem YOLO-Modell (lädt beim ersten Mal ca. 6 MB herunter):
```
python pruefe_umgebung.py --yolo 0
```
Das Modell erkennt Alltagsgegenstände (Person, Tasse, Handy …), noch keine Würfel. Oben links steht die Bildrate. Auf dem Laptop sollten es mindestens 10 FPS sein.

## 7. Label Studio (nur auf dem Rechner, auf dem gelabelt wird)

Label Studio bringt viele eigene Pakete mit und bekommt deshalb eine **eigene** Umgebung, außerhalb des Repos:
```
cd %USERPROFILE%
py -3.11 -m venv labelstudio-venv
labelstudio-venv\Scripts\activate
pip install label-studio
label-studio start
```
Im Browser öffnet sich http://localhost:8080. Konto anlegen (bleibt lokal auf dem Rechner). Das Projekt mit den 8 Klassen richten wir ein, wenn die ersten Fotos da sind.

## 8. Optional: Handy als Kamera

App **DroidCam** oder **IP Webcam** auf dem Android-Handy installieren, Handy und Rechner ins selbe WLAN. Die App zeigt eine Adresse an, z. B. `http://192.168.0.23:8080/video`. Test:
```
python pruefe_umgebung.py --kamera http://192.168.0.23:8080/video
```

## Ordner und Dateien

| Ort | Inhalt |
|---|---|
| `Wuerfelprogramm/` | Programmcode, `requirements.txt`, später `modelle/` mit den fertigen Modelldateien |
| `Wuerfelprogramm/.venv/` | virtuelle Umgebung, wird nicht hochgeladen |
| `C:\Users\chris\OneDrive\Bilder_wuerfelzaehler` | Fotos (`Teachbilder/`, `Testbilder/`), nicht im Repo |

Die `.gitignore` sorgt dafür, dass Bilder, Datensätze, Trainingsläufe und die `.venv` nicht versehentlich nach GitHub gehen.
