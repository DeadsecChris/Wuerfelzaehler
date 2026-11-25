# Umsetzungsplan: Würfel-Zähler

Stand: 16.11.2026 (6. Fassung: Testmodus mit Bestätigung und Korrektur). Grundlage: Lastenheft vom 12.11.2026, `projekt_brain.md` und Chris' Vorgaben vom 16.11.2026.

## Vorgaben vom 16.11.2026

- **Farbunabhängig:** Das Spiel soll mit möglichst unterschiedlichen Standardwürfeln funktionieren (beliebige Farbe, helle oder dunkle Augen). Die Farbe spielt keine Rolle.
- **Idee von Chris:** Würfel anhand der **Form** finden, Augenzahl über **Kontrast innerhalb der Form** bestimmen.
- **Hardware:** Entwicklung auf dem Laptop, Training bei Bedarf auf dem Gaming-PC mit starker Grafikkarte (Code über GitHub synchron).
- **Kamera:** flexibel. Zum Entwickeln Laptop-Webcam oder USB-Webcam, später auch Handy.
- **Abgabe des Programms:** 16.12.2026.
- **Spielregeln bleiben:** Kopf = Summe, Zahl = Produkt. Keine Farbregel.
- **Münze:** vorerst immer dieselbe 1-Euro-Münze (Entscheidung 16.11.2026). Alle Euro-Münzen sind eine Erweiterung, falls Zeit bleibt (siehe Schritt 8).

## Ansatz: zweistufige Erkennung

```
Kamerabild ──► Stufe 1: YOLO findet Objekte (Form, Oberklasse)
                 ├─ "wuerfel" ──► Ausschnitt ──► Stufe 2: Unterklasse
                 │                                 ├─ A: Kontrast-Augenzählung (OpenCV)
                 │                                 └─ B: Klassifizierer → augen_1 … augen_6
                 │                                      A und B einig? ─ ja ──► Wert 1–6
                 │                                                     └ nein ─► "unsicher"
                 └─ "muenze"  ──► Ausschnitt ──► Stufe 2: Klassifizierer → kopf / zahl
                                                    (Würfel-Ausschnitt muss augen_x ergeben,
                                                     Münz-Ausschnitt kopf/zahl, sonst "unsicher")
```

**Stufe 1, Form = Oberklasse (selbst trainierte KI):** YOLO nano mit nur **2 Klassen**: `wuerfel` und `muenze`. Die KI lernt, wie ein Würfel aussieht (Würfelform mit Punkten), egal welche Farbe. Damit das klappt, kommen im Datensatz möglichst viele verschiedene Würfel vor, und die Bilder werden im Training zusätzlich zufällig in Graustufen umgewandelt und im Farbton verschoben.

**Stufe 2, Unterklasse im Ausschnitt.** Für Würfel wird Chris' Kontrast-Idee umgesetzt, abgesichert durch eine zweite Meinung. Für die Münze entscheidet der Klassifizierer allein:

- **A: Kontrast-Augenzählung (klassische Bildverarbeitung, kein Training):**
  1. Ausschnitt in Graustufen umwandeln, Kontrast ausgleichen (CLAHE).
  2. Adaptive Schwelle: Augen sind kleine runde Flecken, die sich stark vom Umfeld abheben. Beide Richtungen prüfen (dunkle Augen auf hellem Würfel und helle Augen auf dunklem Würfel); die Richtung mit den saubereren Flecken gewinnt.
  3. Flecken zählen, die rund genug sind, ähnlich groß sind und auf der oberen Fläche liegen (mittlerer Bereich des Ausschnitts). Ergebnis 1–6, alles andere ist „ungültig“.
  4. Sonderfälle: große oder farbige 1 bei manchen Würfeln, Glanzpunkte, sichtbare Seitenflächen bei schräger Kamera, verschmolzene Augen bei der 6.
- **B: KI-Klassifizierer (selbst trainiert):** YOLO-Klassifikation nano (`yolo11n-cls`) mit **8 Unterklassen** `augen_1` … `augen_6`, `kopf`, `zahl`, trainiert auf **Graustufen-Ausschnitten** von Würfeln und Münze. Ein Modell für alle Ausschnitte. Er kommt mit Fällen zurecht, an denen die Augenzählung scheitert (Spiegelungen, schräge Lage).
- **Münze, Kopf/Zahl:**
  - Trainiert mit immer derselben 1-Euro-Münze, beide Seiten ungefähr gleich oft.
  - **Dreifache Entscheidung:** Sicherheit für Zahl ≥ 80 % → Zahl; ≤ 20 % → Kopf; dazwischen → „unsicher, bitte neu würfeln“ (Schwellen einstellbar). So wird eine schlecht sichtbare Seite (Glanz, Unschärfe, Verdeckung) nicht still falsch gewertet.
- **Plausibilität:** Ein Würfel-Ausschnitt muss eine Augenzahl ergeben, ein Münz-Ausschnitt Kopf oder Zahl. Sonst „unsicher“.
- **Vorteile der Ober-/Unterklassen auch bei der Münze:** einheitliches, gut erklärbares Prinzip (erst finden, dann genau hinschauen); Kopf/Zahl wird im vergrößerten Ausschnitt besser erkannt als im Gesamtbild (glänzende Münze); andere Münzen oder Würfel brauchen später nur neue Ausschnitte für Stufe 2. Nachteil: Fehler in zwei Stufen möglich, deshalb werden beide Stufen getrennt ausgewertet.
- **Entscheidung Augenzahl:** Sind A und B einig, gilt der Wert. Sind sie uneinig, meldet das Programm „unsicher“. So ist ein falsches Ergebnis viel unwahrscheinlicher, was besonders beim Multiplizieren wichtig ist.

**Warum nicht nur die Kontrast-Zählung?** Das Lastenheft verlangt eine selbst trainierte KI, die die Klassen erkennt. Mit Stufe 1 und dem Klassifizierer B ist das klar erfüllt, und die Kontrast-Zählung ist ein Zusatz, der das System robuster macht. In der Präsentation lässt sich außerdem zeigen, wie gut klassische Bildverarbeitung und KI jeweils allein sind und was ihre Kombination bringt.

**Einzelaufnahmen ohne Labeln (Chris, 19.11.):** Fotos (auch vom Handy) einfach in den passenden Klassenordner `einzel/<klasse>/` legen. `datensaetze.py` nimmt die Klasse aus dem Ordnernamen und sucht den Rahmen um das Objekt selbst (Objekt hebt sich vom Untergrund ab). Zur Kontrolle zeigt `datensaetze/kontrolle/` jedes Bild mit Rahmen. Nur Wurfbilder mit mehreren Objekten müssen gelabelt werden.

**Labeln für Wurfbilder:** In Label Studio wird weiter mit den 8 Klassen aus dem Lastenheft gelabelt (`wuerfel_1` … `wuerfel_6`, `muenze_kopf`, `muenze_zahl`). Ein Skript macht daraus automatisch beide Datensätze: Für Stufe 1 werden `wuerfel_1–6` zu `wuerfel` und `muenze_kopf`/`muenze_zahl` zu `muenze` zusammengefasst, für Stufe 2 werden alle Objekte ausgeschnitten und nach Unterklasse sortiert. Einmal labeln, zwei Modelle trainieren.

## Folgen für die Dokumente

- **Drehbuch (fällig 18.11.2026, 22:00):**
  - „3 gleiche weiße Würfel“ ersetzen durch „verschiedene Standardwürfel“. Ziel: **mindestens 8 verschiedene Würfel** (verschiedene Farben, Größen, helle und dunkle Augen, runde und eckige Kanten). Pro Wurf werden 3 davon zufällig gewählt.
  - Strichliste führt **Würfel × Augenzahl**, damit jeder Würfel alle Augenzahlen zeigt.
  - Einzelaufnahmen: je Augenzahl mehrere verschiedene Würfel.
  - Münze: dieselbe 1-Euro-Münze wie geplant, Kopf und Zahl ungefähr gleich oft.
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
- [x] Lehrkraft lässt Freiraum (16.11.2026): erlaubt, solange die Mindestanforderungen erfüllt sind und wir alles erklären können. Damit sind vortrainiertes Modell und zweistufige Lösung in Ordnung.
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
- Bilder und Datensätze **nicht** in GitHub (zu groß). Bilderordner seit 16.11.2026: `C:\Users\chris\OneDrive\Bilder_wuerfelzaehler` (über Teams/SharePoint mit Niklas geteilt), mit `Teachbilder/` und `Testbilder/`, darin je `einzel/<8 Klassen>` und `wurf/`. Teach und Test werden gezielt gewählt. Über GitHub läuft nur der Code und die fertigen Modelldateien (das Programm braucht zum Laufen keine Bilder).

### Schritt 2: Drehbuch anpassen und abgeben (bis 18.11.2026, 22:00)
Siehe „Folgen für die Dokumente“. Namen ergänzen.

### Schritt 3: Probedurchlauf (Woche 1)
1. 50 Wurffotos mit verschiedenen Würfeln aufnehmen (`starten.py` → „Fotos aufnehmen“, speichert mit Drehbuch-Namen direkt in den OneDrive-Ordner).
2. In Label Studio mit den 8 Klassen labeln, als YOLO exportieren.
3. Skript `Wuerfelprogramm/datensaetze.py` erzeugt daraus Stufe 1 (2 Klassen) und Stufe 2 (Ausschnitte, 8 Unterklassen).
4. Probetraining beider Stufen (`starten.py` → 6 „Modelle trainieren“, Probelauf), dann live testen (→ 7 „Live-Erkennung“). Prototyp der Kontrast-Zählung auf den Ausschnitten testen.
Ziel: Die ganze Kette läuft einmal durch, Fehler im Aufbau fallen früh auf.

### Schritt 4: Alle Fotos (Niklas, Woche 2)
- Rund 300 Originalfotos nach Aufnahmeplan (E1–E3 Einzel, W1–W5 Würfe), dabei die Würfel wechseln. Benennung wie im Drehbuch, Ablage im OneDrive-Bilderordner (`Teachbilder/` bzw. `Testbilder/`).
- Im Aufnahmeprotokoll pro Foto notieren, welche Würfel verwendet wurden.
- Etwa 10 % ungültige Würfe (Kante, gestapelt, halb verdeckt) zum Testen der Fehlermeldungen.
- **Testsitzung an einem anderen Tag:** 45 Fotos, davon ein Teil mit den 2 „fremden“ Würfeln, die im Training nicht vorkommen.

### Schritt 5: Labeln und Datensätze (gemeinsam, Woche 2)
- Einzelaufnahmen: nur `datensaetze/kontrolle/` durchsehen, falsche Rahmen löschen oder neu fotografieren. Wurfbilder mit den 8 Klassen labeln, gegenseitige Stichprobenkontrolle (je 20 Bilder).
- `Wuerfelprogramm/datensaetze.py`:
  0. Liest `Teachbilder/` und `Testbilder/` aus dem OneDrive-Bilderordner, Labels neben dem Bild oder im Unterordner `labels/` (Label-Studio-Export, Klassen über `classes.txt`). Schreibt einen `bericht.txt` mit Anzahlen je Klasse und Warnungen (fehlende Labels, falscher Klassenordner).
  1. Teachbilder werden **vor** der Augmentation in train und val (15 %, nur Trainingskontrolle) geteilt, Testbilder gehen nur nach test.
  2. Stufe 1: Klassen zu `wuerfel` und `muenze` zusammenfassen, 3 Varianten je Trainingsbild mit Albumentations (Drehung, Helligkeit, Kontrast, Zuschnitt, **Graustufen**, **Farbton**, Rauschen, Unschärfe; kein Spiegeln).
  3. Stufe 2: Würfel und Münze ausschneiden (mit etwas Rand), in Graustufen umwandeln, nach `augen_1` … `augen_6`, `kopf`, `zahl` sortieren. Keine Varianten offline; die Klassifikation bekommt Ultralytics' eigene Bildvariation, mit `fliplr=0` wegen der Münze.

### Schritt 6: Training (Christian, Woche 3, auf dem Gaming-PC)
```
yolo detect train data=datensaetze/stufe1/data.yaml model=yolo11n.pt imgsz=640 epochs=100 fliplr=0 patience=20
yolo classify train data=datensaetze/stufe2 model=yolo11n-cls.pt imgsz=96 epochs=50 fliplr=0
```
- Mit starker Grafikkarte dauert jedes Training nur Minuten. So können viele Varianten ausprobiert werden.
- Ergebnis: `modelle/stufe1.pt` und `modelle/stufe2.pt` (ins Repo, sind klein).

### Schritt 7: Auswertung (gemeinsam, Woche 3)
- Stufe 1: `yolo detect val ... split=test` → Präzision und Trefferquote für `wuerfel` und `muenze`.
- Stufe 2: Verwechslungsmatrix der 8 Unterklassen; für die Augenzahl getrennt für A (Kontrast), B (KI) und A+B.
- Gesamtziel mit `scripts/eval_wuerfe.py`: **mindestens 90 % der Testwürfe vollständig richtig**, zusätzlich getrennt ausgewiesen für die fremden Würfel.
- Bei Schwächen gezielt Fotos nachlegen (z. B. dunkle Würfel mit hellen Augen, schräge Lagen) und neu trainieren.

### Schritt 8: Anwendungsprogramm (Christian, Woche 3–4)
Aufbau in `app/`:
- `kamera.py`: **flexible Bildquelle** über Einstellung: Webcam-Nummer (`0`, `1`), Handy als Netzwerkkamera (URL, z. B. per DroidCam oder „IP Webcam“-App) oder Bilddatei zum Testen.
- `stufe1.py`: Objekterkennung, Schwelle 50 % (einstellbar).
- `stufe2.py`: Klassifizierer für alle Ausschnitte, Plausibilitätsprüfung, dreifache Kopf/Zahl-Entscheidung.
- `augen.py`: Kontrast-Augenzählung (A) und Vergleich mit dem Klassifizierer (B).
- `spiel.py`: Vollständigkeit (genau 3 Würfel, 1 Münze), Summe oder Produkt, Rechenweg.
- `main.py`: Fenster mit Livebild, Rahmen und erkannter Augenzahl an jedem Würfel, Statusbereich, Button „Scharfschalten“, Bilder pro Sekunde.
- Stabilitätsfilter: Ergebnis nach 5 gleichen Bildern, spätestens 2 s nach Stillstand.
- Ziel ≥ 10 Bilder pro Sekunde auch auf dem Laptop ohne Grafikkarte prüfen (zwei kleine Modelle plus OpenCV sollten das schaffen; sonst Stufe 2 nur auf stabilen Bildern ausführen).
- `testmodus.py`: **Bestätigen und Korrigieren** (Wunsch von Chris, siehe unten).

#### Testmodus: Bestätigen und Korrigieren (Human in the Loop)
Nach dem Korrekturprinzip aus dem Schere-Stein-Papier-Projekt (`teachable-ki` im Unibrain): Die KI rät, der Mensch bestätigt oder korrigiert, alles landet in einem Gedächtnis, und damit wird nachtrainiert.

1. **Ergebnis anzeigen:** Ist ein Wurf stabil erkannt, friert das Programm das Bild ein und zeigt an jedem Objekt eine Nummer und die erkannte Klasse (z. B. ① 4, ② 2, ③ 5, ④ Kopf) sowie das Ergebnis.
2. **Bestätigen:** Taste `J` = alles richtig. `N` = etwas ist falsch. `F` = Fehler, Runde verwerfen (z. B. Hand im Bild, Würfel rollt noch); es wird nichts gespeichert.
3. **Korrigieren:** Nach `N` wählt man das falsche Objekt (Klick oder Nummer) und gibt den richtigen Wert ein (`1`–`6`, `K`, `Z`). Fehlt ein Rahmen oder ist einer zu viel, wählt man „Rahmen falsch“. Dann wird das Bild zum Nachlabeln in Label Studio abgelegt, weil sich ein fehlender Rahmen nicht per Taste ergänzen lässt.
4. **Gedächtnis:** Jede bestätigte oder korrigierte Runde speichert
   - das Kamerabild in `gedaechtnis/bilder/`,
   - eine Label-Datei im YOLO-Format mit den (korrigierten) 8 Klassen in `gedaechtnis/labels/` (gleiche Form wie die Originaldaten, kann also direkt ins Training),
   - eine Zeile in `gedaechtnis/protokoll.csv`: Zeit, Bildname, KI-Ergebnis, korrigiertes Ergebnis, richtig ja/nein, Sicherheit je Objekt, ob Kontrast-Zählung und Klassifizierer einig waren, verwendete Würfel.
5. **Auswertung:** Aus dem Protokoll berechnet das Programm laufend die Quote der vollständig richtigen Würfe (unser Ziel ≥ 90 %) und zeigt die häufigsten Verwechslungen. Das sind direkt die Live-Zahlen für die Präsentation.
6. **Nachtraining:** `scripts/nachtrainieren.py` nimmt die Originaldaten plus das Gedächtnis, erzeugt beide Datensätze neu und trainiert Stufe 1 und Stufe 2 (auf dem Gaming-PC in Minuten). Anders als bei Schere-Stein-Papier nicht automatisch beim Beenden, sondern bewusst per Skript, weil YOLO-Training länger dauert.

Lehren aus dem Schere-Stein-Papier-Projekt, die wir gleich einbauen:
- **Immer vom Ausgangsstand aus trainieren** (Originaldaten + Gedächtnis), nie das schon nachtrainierte Modell weiter verändern. So bleibt jedes Training nachvollziehbar, und ein schlechtes Nachtraining lässt sich zurücknehmen; das vorige Modell wird mit Datum gesichert.
- **Klassen ausgleichen:** Das Skript zeigt vor dem Training, wie oft jede Klasse im Gedächtnis vorkommt, und gewichtet seltene Klassen stärker.
- **Wirkung messen (Entscheidung Chris, 16.11.):** Kein automatisches Zurückhalten. Bilder werden gezielt in die Ordner `teach/` oder `test/` im lokalen Bilderordner gelegt. Im Testmodus wählt man beim Speichern per Taste, ob das Bild nach `teach` (Standard) oder `test` kommt. Testbilder werden nie trainiert, sodass sich Vorher/Nachher sauber vergleichen lässt.
- **Hintergrund beachten:** Fotos aus dem Testmodus stammen meist aus demselben Aufbau. Ab und zu Untergrund und Licht wechseln, damit die KI nicht den Tisch lernt.

Über das Lastenheft hinaus (nach Zeit):
1. Funktioniert mit beliebigen Standardwürfeln (Hauptziel dieser Fassung).
2. Rechenweg anzeigen („4 × 2 × 5 = 40“) und an jedem Würfel die erkannte Zahl einblenden.
3. Debug-Ansicht: Ausschnitt mit den gefundenen Augen-Flecken, gut für die Präsentation.
4. Wurfprotokoll als CSV und kleine Statistik.
5. **Alle Euro-Münzen (Idee von Chris, falls Zeit bleibt):** Die Wertseite ist in allen Euro-Ländern gleich, nur die Kopfseiten unterscheiden sich. `zahl` mit allen Wertseiten trainieren (1/2/5 Cent, 10/20/50 Cent, 1/2 Euro, alte und neue Europakarte), `kopf` mit möglichst vielen verschiedenen Ländern (die KI lernt „nicht die Wertseite“). Dreifache Entscheidung bleibt. Fremdwährungen würden als Kopf gewertet (akzeptiert). Stufe 1 (`muenze`) braucht dafür zusätzliche Fotos der anderen Münzgrößen.
6. Später Handy: Modelle nach ONNX oder TFLite exportieren (`yolo export model=stufe1.pt format=tflite`). Bis zum 16.12. reicht das Handy als Kamera; eine eigene App ist ein Ausblick.

### Schritt 9: Testen und Präsentation (Woche 4)
- 50 Live-Würfe mit gemischten Würfeln, darunter die Testwürfel T1 und T2, im **Testmodus** durchführen. Die Quote steht danach direkt im Protokoll.
- Einmal nachtrainieren und mit dem zurückgehaltenen Live-Test zeigen, ob es besser wurde (Vorher/Nachher für die Präsentation).
- Präsentation: Aufbau, zweistufiger Ansatz, Datensatz, Verwechslungsmatrizen, Vergleich Kontrast vs. KI vs. beides, Live-Demo mit einem Würfel aus dem Publikum.

## Ordnerstruktur im Repo (Vorschlag)
```
wuerfelzaehler/
├── app/                  Anwendungsprogramm
├── scripts/              datensaetze.py, eval_wuerfe.py, nachtrainieren.py
├── modelle/              stufe1.pt, stufe2.pt
├── projekt_brain.md
└── umsetzungsplan.md
```
Fotos liegen in `C:\Users\chris\OneDrive\Bilder_wuerfelzaehler` (Teams/SharePoint), erzeugte Datensätze lokal, nicht in GitHub.

## Noch offen
1. Würfel: 3 fürs Training (WA, WB, WC), 2 Testwürfel (T1, T2) organisiert das Team.
