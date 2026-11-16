# Umsetzungsplan: Würfel-Zähler

Stand: 16.11.2026. Grundlage: Lastenheft vom 12.11.2026 und `projekt_brain.md`.

## Was sich ändert: 3 Würfel in verschiedenen Farben

Statt drei gleicher weißer Würfel nehmen wir drei Würfel in unterschiedlichen Farben. Das Programm kann dadurch mehr als gefordert: Es sagt nicht nur das Ergebnis, sondern auch **welcher Würfel welche Augenzahl zeigt** (z. B. „Rot 4 + Blau 2 + Grün 5 = 11“).

**Empfehlung: Die KI bleibt bei 8 Klassen, die Farbe bestimmt das Programm selbst.**

| Weg | Klassen | Fotos nötig | Bewertung |
|---|---|---|---|
| A: YOLO erkennt Augenzahl, OpenCV misst die Farbe im Rahmen | 8 (wie Lastenheft) | ca. 300 (wie geplant) | **empfohlen**: Datensatz bleibt klein, jede Augenzahl-Klasse lernt von allen drei Farben, Farbmessung ist einfach und gut erklärbar |
| B: YOLO lernt Farbe und Augenzahl zusammen (`rot_1` … `gruen_6`) | 20 | ca. 750+ | zu viel Foto- und Labelaufwand für die Zeit, jede Klasse hätte nur ein Drittel der Beispiele |

Bei Weg A wird jeder erkannte Würfelrahmen ausgeschnitten und sein mittlerer Farbton (HSV-Farbraum) mit den drei kalibrierten Würfelfarben verglichen. Da genau drei Farben vorkommen, ordnet das Programm jedem Rahmen eindeutig eine Farbe zu. Zwei gleiche Farben im Bild sind ein zusätzliches Fehlersignal („Bitte neu würfeln“).

Folgen für die Dokumente:
- Lastenheft/`projekt_brain.md`: „3 gleiche weiße Würfel“ ersetzen durch „3 Würfel in verschiedenen Farben“, Farberkennung als Zusatzfunktion nennen.
- Drehbuch (fällig **18.11.2026, 22:00**): Strichliste je **Farbe × Augenzahl** führen, damit jede Farbe jede Augenzahl ungefähr gleich oft zeigt. Sonst lernt die KI zum Beispiel „rot heißt 6“.
- Data Augmentation: **keine starke Farbtonverschiebung** (höchstens ±5 %), sonst wird ein roter Würfel im Training orange oder lila. Helligkeit, Kontrast und Sättigung bleiben wie geplant.

## Schritte

### Schritt 0: Klären und Material (diese Woche)
- [ ] Lehrkraft fragen, ob ein vortrainiertes YOLO-Modell als Startpunkt erlaubt ist (offener Punkt aus dem Lastenheft).
- [ ] Würfelfarben und Augenfarbe notieren (z. B. Rot/weiße Augen, Blau/weiße Augen, Grün/weiße Augen). Farben, die sich im Farbton deutlich unterscheiden, funktionieren am besten. Schwarz/Weiß/Grau sind für die Farbmessung schwierig.
- [ ] Wurffläche mit Rand (Tablett oder Schuhkartondeckel) und dunkelgrünen Filz besorgen.
- [ ] Kamera festlegen und **fest montieren**, senkrecht von oben, ca. 40 cm (Stativ, Schwanenhals-Halterung oder Bücherstapel mit Brett). Dieselbe Kamera für Fotos und Programm verwenden.

### Schritt 1: Softwareumgebung (Christian, ca. 1 Stunde)
- Python 3.11 und VS Code installieren, Projektordner = dieses Repo.
- Virtuelle Umgebung anlegen und Pakete installieren:
  ```
  python -m venv .venv
  .venv\Scripts\activate
  pip install ultralytics opencv-python albumentations label-studio
  ```
  Mit NVIDIA-Grafikkarte vorher PyTorch mit CUDA von pytorch.org installieren, sonst läuft alles auf der CPU.
- Probelauf: `yolo predict model=yolo11n.pt source=0` öffnet die Webcam mit dem vortrainierten Modell. Wenn das läuft, funktionieren Kamera, OpenCV und PyTorch.

### Schritt 2: Drehbuch anpassen und abgeben (bis 18.11.2026, 22:00)
- Farbänderung und Strichliste Farbe × Augenzahl eintragen (siehe oben), Namen ergänzen.
- Aufnahmeplan E1–E3 und W1–W5 bleibt. Bei den Einzelaufnahmen je Klasse alle drei Farben fotografieren (15 Bilder pro Würfelklasse = 5 je Farbe).

### Schritt 3: Probedurchlauf mit 50 Fotos (Woche 1)
Ziel ist, die ganze Kette einmal durchzuspielen, bevor 300 Fotos gemacht werden. Fehler im Aufbau fallen so früh auf.
1. 50 Wurffotos im Spielaufbau (W1) aufnehmen.
2. In Label Studio labeln: Projekt „Object Detection with Bounding Boxes“, 8 Labels genau wie im Lastenheft benannt. Rahmen um den ganzen Würfel, Klasse = Augenzahl oben. Export als „YOLO“.
3. Probemodell trainieren (siehe Schritt 6) mit 30 Epochen.
4. Auf ein paar neuen Fotos testen. Wenn die KI überhaupt Würfel findet, ist die Kette in Ordnung.

### Schritt 4: Alle Fotos aufnehmen (Niklas, Woche 1–2)
- 300 Originalfotos nach Aufnahmeplan, Benennung `wurf_W1_0001.jpg` bzw. `einzel_E2_wuerfel_4_0007.jpg`, Ablage in `rohbilder/`.
- Strichliste im `aufnahmeprotokoll.xlsx` mitführen, seltene Kombinationen von Hand legen.
- Etwa 10 % „ungültige“ Würfe mitfotografieren (Würfel auf der Kante, Würfel auf Münze, Objekt halb verdeckt). Diese werden nur so weit gelabelt, wie Objekte eindeutig erkennbar sind. Damit prüfen wir später, ob das Programm „Bitte neu würfeln“ sagt.
- **Testsitzung an einem anderen Tag:** 45 Fotos in `rohbilder/test_sitzung/`, gleiche Verteilung über die Situationen.

### Schritt 5: Labeln (gemeinsam, Woche 2)
- Alle Fotos in Label Studio labeln und als YOLO exportieren (eine `.txt` pro Bild).
- Gegenseitige Kontrolle: Jeder prüft 20 zufällige Bilder des anderen. Falsche Labels sind der häufigste Grund für ein schlechtes Modell.
- Skript `scripts/split_augment.py` (schreibt Christian):
  1. Teilt die Originale 70/15/15 auf (Test = Testsitzung), **vor** der Augmentation.
  2. Erzeugt mit Albumentations 3 Varianten je Trainingsbild, Rahmen werden mitgedreht, **kein Spiegeln**, Farbton höchstens ±5 %.
  3. Legt `dataset/` mit `images/` und `labels/` und die `data.yaml` an.
- Beim YOLO-Training die eingebaute Spiegelung ausschalten (`fliplr=0`), sonst ist die Münze doch spiegelverkehrt.

### Schritt 6: Training (Christian, Woche 2)
```
yolo detect train data=dataset/data.yaml model=yolo11n.pt imgsz=640 epochs=80 fliplr=0 hsv_h=0.005 patience=20
```
- `yolo11n.pt` ist die aktuelle Nano-Variante (alternativ `yolov8n.pt`, beides „nano“ wie im Lastenheft).
- Dauer grob geschätzt bei ca. 840 Trainingsbildern: mit NVIDIA-Grafikkarte 10–20 Minuten, nur CPU mehrere Stunden (über Nacht laufen lassen, notfalls `imgsz=480` oder weniger Epochen).
- Ergebnis: `runs/detect/train/weights/best.pt`.

### Schritt 7: Auswertung (gemeinsam, Woche 2)
- `yolo detect val data=dataset/data.yaml model=best.pt split=test` liefert Verwechslungsmatrix, Präzision und Trefferquote je Klasse (fürs Lastenheft).
- Zusätzlich eigenes Skript `scripts/eval_wuerfe.py`: Wie viele Testwürfe sind **vollständig** richtig (alle 3 Augenzahlen, alle 3 Farben, Münzseite, Ergebnis)? Das ist unser Ziel von **mindestens 90 %**.
- Typische Schwächen und Gegenmittel: 6 und 4 verwechselt (Fotos schräger Würfe nachlegen), Münzseiten verwechselt (mehr Münzfotos bei Seitenlicht), Würfel am Rand übersehen (Fotos mit Objekten am Rand). Danach neu trainieren.

### Schritt 8: Farberkennung (Christian, Woche 2–3)
- Kalibrier-Modus im Programm: Würfel einzeln unter die Kamera legen, Taste drücken, mittlerer Farbton (H) und Sättigung (S) der Würfelfläche werden in `farben.json` gespeichert. So passt es auch bei anderem Licht im Klassenraum.
- Zuordnung im Betrieb: Für jeden Würfelrahmen den Median-Farbton der farbigen Pixel nehmen (helle Augen und Schatten ausblenden), Abstand zu den drei gespeicherten Farben berechnen, jeder Farbe genau einen Rahmen zuordnen.
- Test: Farbe auf den Testbildern mit auswerten (siehe Schritt 7).

### Schritt 9: Anwendungsprogramm (Christian, Woche 3)
Aufbau in `app/`:
- `erkennung.py`: Modell laden, Bild auswerten, Erkennungen ab Schwelle (50 %, einstellbar) filtern.
- `farbe.py`: Kalibrierung und Farbzuordnung.
- `spiel.py`: Vollständigkeit prüfen (genau 3 Würfel, 1 Münze, 3 verschiedene Farben), Summe oder Produkt berechnen, Rechenweg als Text.
- `main.py`: Fenster mit Livebild, Rahmen + Klasse + Sicherheit an jedem Objekt, Statusbereich, Button „Scharfschalten“, Bilddatei laden zum Testen.
- Stabilitätsfilter: Ergebnis erst anzeigen, wenn 5 Bilder hintereinander dasselbe liefern.
- Messen: Bilder pro Sekunde im Fenster anzeigen (Ziel ≥ 10 ohne Grafikkarte).

Zusätzliche Funktionen über das Lastenheft hinaus (nach Zeit, in dieser Reihenfolge):
1. Farbe pro Würfel und Rechenweg („Rot 4 × Blau 2 × Grün 5 = 40“).
2. Wurfprotokoll als CSV (Uhrzeit, Würfel, Münze, Ergebnis, Sicherheit) für die Auswertung in der Präsentation.
3. Statistik am Ende: Verteilung der Augenzahlen je Farbe (zeigt, ob die Würfel fair sind).
4. Optionale Farbregel fürs Spiel, z. B. „der rote Würfel zählt doppelt“ (per Taste ein/aus).

### Schritt 10: Testen und Präsentation (gemeinsam, Woche 3)
- 50 echte Würfe live mit dem Programm, Ergebnis jeweils mit Strichliste prüfen, Quote ausrechnen.
- Präsentation: Aufbau, Datensatz, Verwechslungsmatrix, Quote, Live-Demo.

## Ordnerstruktur im Repo (Vorschlag)
```
wuerfelzaehler/
├── app/                 Anwendungsprogramm
├── scripts/             split_augment.py, eval_wuerfe.py
├── dataset/data.yaml    (Bilder selbst nicht ins Repo, zu groß)
├── modelle/best.pt      fertiges Modell
├── projekt_brain.md
└── umsetzungsplan.md
```
Die Fotos liegen lokal oder im OneDrive, nicht in GitHub.

## Noch offen (Antworten von Chris nötig)
1. Welche drei Farben haben die Würfel, und welche Farbe haben die Augen?
2. Laptop für das Training: Prozessor, Arbeitsspeicher, Grafikkarte (NVIDIA ja/nein), Windows-Version?
3. Kamera: eingebaute Webcam, externe USB-Webcam oder Handy? Gibt es eine Halterung von oben?
4. Wann ist die Abgabe bzw. Präsentation des fertigen Programms?
5. Bleiben die Spielregeln so (Kopf = Summe, Zahl = Produkt), oder sollen die Farben eine Spielregel bekommen?
6. Hat die Lehrkraft das vortrainierte Modell als Startpunkt erlaubt?
