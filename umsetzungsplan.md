# Umsetzungsplan: Würfel-Zähler

Stand: 16.11.2026 (2. Fassung). Grundlage: Lastenheft vom 12.11.2026, `projekt_brain.md` und Chris' Vorgaben vom 16.11.2026.

## Vorgaben vom 16.11.2026

- **Farbunabhängig:** Das Spiel soll mit möglichst unterschiedlichen Standardwürfeln funktionieren (beliebige Farbe, helle oder dunkle Augen). Die Farbe spielt keine Rolle.
- **Idee von Chris:** Würfel anhand der **Form** finden, Augenzahl über **Kontrast innerhalb der Form** bestimmen.
- **Hardware:** Entwicklung auf dem Laptop, Training bei Bedarf auf dem Gaming-PC mit starker Grafikkarte (Code über GitHub synchron).
- **Kamera:** flexibel. Zum Entwickeln Laptop-Webcam oder USB-Webcam, später auch Handy.
- **Abgabe des Programms:** 16.12.2026.
- **Spielregeln bleiben:** Kopf = Summe, Zahl = Produkt. Keine Farbregel.
- **Münze:** bleibt immer dieselbe 1-Euro-Münze.

## Ansatz: zweistufige Erkennung

```
Kamerabild ──► Stufe 1: YOLO findet Objekte (Form)
                 ├─ "wuerfel"      ──► Ausschnitt ──► Stufe 2: Augenzahl
                 ├─ "muenze_kopf"                        ├─ A: Kontrast-Augenzählung (OpenCV)
                 └─ "muenze_zahl"                        └─ B: kleiner KI-Klassifizierer (Graustufen)
                                                              ▼
                                               A und B einig? ─ ja ──► Wert 1–6
                                                              └ nein ─► "unsicher, bitte neu würfeln"
```

**Stufe 1, Form (selbst trainierte KI):** YOLO nano mit nur **3 Klassen**: `wuerfel`, `muenze_kopf`, `muenze_zahl`. Die KI lernt, wie ein Würfel aussieht (Würfelform mit Punkten), egal welche Farbe. Damit das klappt, kommen im Datensatz möglichst viele verschiedene Würfel vor, und die Bilder werden im Training zusätzlich zufällig in Graustufen umgewandelt und im Farbton verschoben.

**Stufe 2, Augenzahl im Ausschnitt.** Hier wird Chris' Kontrast-Idee umgesetzt, abgesichert durch eine zweite Meinung:

- **A: Kontrast-Augenzählung (klassische Bildverarbeitung, kein Training):**
  1. Ausschnitt in Graustufen umwandeln, Kontrast ausgleichen (CLAHE).
  2. Adaptive Schwelle: Augen sind kleine runde Flecken, die sich stark vom Umfeld abheben. Beide Richtungen prüfen (dunkle Augen auf hellem Würfel und helle Augen auf dunklem Würfel); die Richtung mit den saubereren Flecken gewinnt.
  3. Flecken zählen, die rund genug sind, ähnlich groß sind und auf der oberen Fläche liegen (mittlerer Bereich des Ausschnitts). Ergebnis 1–6, alles andere ist „ungültig“.
  4. Sonderfälle: große oder farbige 1 bei manchen Würfeln, Glanzpunkte, sichtbare Seitenflächen bei schräger Kamera, verschmolzene Augen bei der 6.
- **B: KI-Klassifizierer (selbst trainiert):** YOLO-Klassifikation nano (`yolo11n-cls`) mit 6 Klassen `augen_1` … `augen_6`, trainiert auf **Graustufen-Ausschnitten** der Würfel. Er kommt mit Fällen zurecht, an denen die Augenzählung scheitert (Spiegelungen, schräge Lage).
- **Entscheidung:** Sind A und B einig, gilt der Wert. Sind sie uneinig, meldet das Programm „unsicher“. So ist ein falsches Ergebnis viel unwahrscheinlicher, was besonders beim Multiplizieren wichtig ist.

**Warum nicht nur die Kontrast-Zählung?** Das Lastenheft verlangt eine selbst trainierte KI, die die Klassen erkennt. Mit Stufe 1 und dem Klassifizierer B ist das klar erfüllt, und die Kontrast-Zählung ist ein Zusatz, der das System robuster macht. In der Präsentation lässt sich außerdem zeigen, wie gut klassische Bildverarbeitung und KI jeweils allein sind und was ihre Kombination bringt.

**Labeln bleibt fast gleich:** In Label Studio wird weiter mit den 8 Klassen aus dem Lastenheft gelabelt (`wuerfel_1` … `wuerfel_6`, `muenze_kopf`, `muenze_zahl`). Ein Skript macht daraus automatisch beide Datensätze: Für Stufe 1 werden `wuerfel_1–6` zu `wuerfel` zusammengefasst, für Stufe 2 werden die Würfel ausgeschnitten und nach Augenzahl sortiert. Einmal labeln, zwei Modelle trainieren.

## Folgen für die Dokumente

- **Drehbuch (fällig 18.11.2026, 22:00):**
  - „3 gleiche weiße Würfel“ ersetzen durch „verschiedene Standardwürfel“. Ziel: **mindestens 8 verschiedene Würfel** (verschiedene Farben, Größen, helle und dunkle Augen, runde und eckige Kanten). Pro Wurf werden 3 davon zufällig gewählt.
  - Strichliste führt **Würfel × Augenzahl**, damit jeder Würfel alle Augenzahlen zeigt.
  - Einzelaufnahmen: je Augenzahl mehrere verschiedene Würfel.
  - Data Augmentation ergänzen: zufällige Graustufen, Farbtonverschiebung. Weiterhin **kein Spiegeln** (Münze).
  - **Testbilder mit 2 Würfeln, die im Training nie vorkamen.** So lässt sich zeigen, dass das Programm auch mit fremden Würfeln funktioniert.
- **Lastenheft/`projekt_brain.md`:** Zweistufige Erkennung, verschiedene Würfel, flexible Kameraquelle, Termin 16.12.2026 nachtragen.

## Zeitplan bis 16.12.2026

| Woche | Zeitraum | Ziel |
|---|---|---|
| 1 | 16.–22.11. | Drehbuch anpassen und abgeben, Softwareumgebung auf Laptop und Gaming-PC, Würfel sammeln, Kamera-Aufbau, Probedurchlauf mit 50 Fotos, erster Prototyp der Kontrast-Zählung |
| 2 | 23.–29.11. | Alle Fotos und Testsitzung, Labeln, Datensätze erzeugen |
| 3 | 30.11.–6.12. | Beide Modelle trainieren, auswerten, Fotos nachlegen, Programm mit Kamera |
| 4 | 7.–13.12. | Programm fertig, Tests mit 50 Live-Würfen, Präsentation |
| | 14.–16.12. | Puffer, Abgabe am 16.12. |

## Schritte

### Schritt 0: Klären und Material (Woche 1)
- [ ] Lehrkraft fragen: Ist ein vortrainiertes YOLO-Modell als Startpunkt erlaubt, und ist die zweistufige Lösung mit zusätzlicher Kontrast-Zählung in Ordnung?
- [ ] Mindestens 8 verschiedene Standardwürfel sammeln (Spielesammlung, Freunde, 1-Euro-Laden), nummerieren (z. B. Aufkleber unten oder Liste mit Foto).
- [ ] Wurffläche mit Rand und mindestens zwei Untergründe (dunkler Filz, heller Untergrund).
- [ ] Kamera fest von oben montieren (ca. 40 cm). Zum Entwickeln Laptop- oder USB-Webcam.

### Schritt 1: Softwareumgebung (Christian, Woche 1)
- Auf Laptop und Gaming-PC: Python 3.11, VS Code, Repo klonen.
  ```
  python -m venv .venv
  .venv\Scripts\activate
  pip install ultralytics opencv-python albumentations
  ```
- Auf dem Gaming-PC zuerst PyTorch mit CUDA von pytorch.org installieren, dann prüfen: `python -c "import torch; print(torch.cuda.is_available())"` muss `True` ausgeben.
- Label Studio am besten in einer eigenen Umgebung installieren (`pip install label-studio`), weil es viele eigene Pakete mitbringt.
- Probelauf: `yolo predict model=yolo11n.pt source=0` öffnet die Webcam.
- Bilder und Datensätze **nicht** in GitHub (zu groß), sondern über OneDrive oder USB-Stick zwischen den Rechnern austauschen. Über GitHub läuft nur der Code und das fertige Modell.

### Schritt 2: Drehbuch anpassen und abgeben (bis 18.11.2026, 22:00)
Siehe „Folgen für die Dokumente“. Namen ergänzen.

### Schritt 3: Probedurchlauf (Woche 1)
1. 50 Wurffotos mit verschiedenen Würfeln aufnehmen.
2. In Label Studio mit den 8 Klassen labeln, als YOLO exportieren.
3. Skript `scripts/datensaetze.py` erzeugt daraus Stufe 1 (3 Klassen) und Stufe 2 (Ausschnitte).
4. Probemodell Stufe 1 mit 30 Epochen trainieren, Prototyp der Kontrast-Zählung auf den Ausschnitten testen.
Ziel: Die ganze Kette läuft einmal durch, Fehler im Aufbau fallen früh auf.

### Schritt 4: Alle Fotos (Niklas, Woche 2)
- Rund 300 Originalfotos nach Aufnahmeplan (E1–E3 Einzel, W1–W5 Würfe), dabei die Würfel wechseln. Benennung wie im Drehbuch, Ablage in `rohbilder/`.
- Im Aufnahmeprotokoll pro Foto notieren, welche Würfel verwendet wurden.
- Etwa 10 % ungültige Würfe (Kante, gestapelt, halb verdeckt) zum Testen der Fehlermeldungen.
- **Testsitzung an einem anderen Tag:** 45 Fotos, davon ein Teil mit den 2 „fremden“ Würfeln, die im Training nicht vorkommen.

### Schritt 5: Labeln und Datensätze (gemeinsam, Woche 2)
- Labeln mit den 8 Klassen, gegenseitige Stichprobenkontrolle (je 20 Bilder).
- `scripts/datensaetze.py`:
  1. Aufteilung 70/15/15 der Originale **vor** der Augmentation (Test = Testsitzung).
  2. Stufe 1: Klassen zusammenfassen, 3 Varianten je Trainingsbild mit Albumentations (Drehung, Helligkeit, Kontrast, Zuschnitt, **Graustufen**, **Farbton**, Rauschen, Unschärfe; kein Spiegeln).
  3. Stufe 2: Würfel ausschneiden (mit etwas Rand), in Graustufen umwandeln, nach `augen_1` … `augen_6` sortieren. Hier darf gedreht und auch gespiegelt werden, weil Würfelaugen symmetrisch sind (anders als die Münze).

### Schritt 6: Training (Christian, Woche 3, auf dem Gaming-PC)
```
yolo detect train data=dataset_stufe1/data.yaml model=yolo11n.pt imgsz=640 epochs=100 fliplr=0 patience=20
yolo classify train data=dataset_stufe2 model=yolo11n-cls.pt imgsz=96 epochs=50
```
- Mit starker Grafikkarte dauert jedes Training nur Minuten. So können viele Varianten ausprobiert werden.
- Ergebnis: `modelle/stufe1.pt` und `modelle/stufe2.pt` (ins Repo, sind klein).

### Schritt 7: Auswertung (gemeinsam, Woche 3)
- Stufe 1: `yolo detect val ... split=test` → Präzision, Trefferquote, Verwechslungsmatrix (Kopf/Zahl).
- Stufe 2: Verwechslungsmatrix der Augenzahlen getrennt für A (Kontrast), B (KI) und A+B.
- Gesamtziel mit `scripts/eval_wuerfe.py`: **mindestens 90 % der Testwürfe vollständig richtig**, zusätzlich getrennt ausgewiesen für die fremden Würfel.
- Bei Schwächen gezielt Fotos nachlegen (z. B. dunkle Würfel mit hellen Augen, schräge Lagen) und neu trainieren.

### Schritt 8: Anwendungsprogramm (Christian, Woche 3–4)
Aufbau in `app/`:
- `kamera.py`: **flexible Bildquelle** über Einstellung: Webcam-Nummer (`0`, `1`), Handy als Netzwerkkamera (URL, z. B. per DroidCam oder „IP Webcam“-App) oder Bilddatei zum Testen.
- `stufe1.py`: Objekterkennung, Schwelle 50 % (einstellbar).
- `augen.py`: Kontrast-Augenzählung (A) und Klassifizierer (B), Vergleich.
- `spiel.py`: Vollständigkeit (genau 3 Würfel, 1 Münze), Summe oder Produkt, Rechenweg.
- `main.py`: Fenster mit Livebild, Rahmen und erkannter Augenzahl an jedem Würfel, Statusbereich, Button „Scharfschalten“, Bilder pro Sekunde.
- Stabilitätsfilter: Ergebnis nach 5 gleichen Bildern, spätestens 2 s nach Stillstand.
- Ziel ≥ 10 Bilder pro Sekunde auch auf dem Laptop ohne Grafikkarte prüfen (zwei kleine Modelle plus OpenCV sollten das schaffen; sonst Stufe 2 nur auf stabilen Bildern ausführen).

Über das Lastenheft hinaus (nach Zeit):
1. Funktioniert mit beliebigen Standardwürfeln (Hauptziel dieser Fassung).
2. Rechenweg anzeigen („4 × 2 × 5 = 40“) und an jedem Würfel die erkannte Zahl einblenden.
3. Debug-Ansicht: Ausschnitt mit den gefundenen Augen-Flecken, gut für die Präsentation.
4. Wurfprotokoll als CSV und kleine Statistik.
5. Später Handy: Modelle nach ONNX oder TFLite exportieren (`yolo export model=stufe1.pt format=tflite`). Bis zum 16.12. reicht das Handy als Kamera; eine eigene App ist ein Ausblick.

### Schritt 9: Testen und Präsentation (Woche 4)
- 50 Live-Würfe mit gemischten Würfeln, darunter fremde Würfel, Quote ausrechnen.
- Präsentation: Aufbau, zweistufiger Ansatz, Datensatz, Verwechslungsmatrizen, Vergleich Kontrast vs. KI vs. beides, Live-Demo mit einem Würfel aus dem Publikum.

## Ordnerstruktur im Repo (Vorschlag)
```
wuerfelzaehler/
├── app/                  Anwendungsprogramm
├── scripts/              datensaetze.py, eval_wuerfe.py
├── modelle/              stufe1.pt, stufe2.pt
├── projekt_brain.md
└── umsetzungsplan.md
```
Fotos und Datensätze liegen lokal bzw. im OneDrive, nicht in GitHub.

## Noch offen
1. Lehrkraft: vortrainiertes Modell erlaubt? Zweistufige Lösung in Ordnung?
2. Wie viele verschiedene Würfel habt ihr schon?
