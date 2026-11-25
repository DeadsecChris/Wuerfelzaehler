# Ergebnisbericht: erster Probelauf (25.11.2026)

Würfel-Zähler, Team Christian Maschke und Niklas Bäricke.
Stand: Probetraining auf dem Laptop (nur CPU) mit den ersten 128 Einzelfotos.

## Kurzfassung

| Was wird geprüft | Testbilder | Ergebnis |
|---|---|---|
| **Rahmen finden** (Stufe 1: Würfel oder Münze, wo?) | 16 Objekte | **100 %** gefunden, **100 %** richtige Oberklasse, **0** Fehlalarme |
| Genauigkeit der Rahmen (Überlappung mit dem echten Rahmen) | 16 Objekte | im Mittel **89 %**, schlechtester **74 %** |
| **Augenzahl / Kopf-Zahl** (Stufe 2, ganze Kette Kamera → Ergebnis) | 16 Objekte | **75 %** richtig (12 von 16) |
| davon Münze Kopf/Zahl | 4 Objekte | **100 %** richtig |
| davon Würfel-Augenzahl | 12 Objekte | **67 %** richtig (8 von 12) |
| **Lernaufwand** | | 128 Fotos, **0** Bilder von Hand gelabelt, ca. **54 Minuten** Rechenzeit |
| **Nachtrag: Stufe 2 nachtrainiert** (gedrehte Ausschnitte, siehe Abschnitt 7) | 16 Ausschnitte | **81 %** richtig (vorher 56 %), val **100 %** |

**Fazit:** Würfel und Münze **finden** kann die KI schon zuverlässig. Die **Augenzahl lesen** ist der Schwachpunkt. Stufe 2 hat im Probelauf nur 24 Sekunden trainiert und wird gerade verbessert (siehe Abschnitt 6).

## 1. Datengrundlage

| | Anzahl |
|---|---|
| Fotos gesamt (Handy, Einzelaufnahmen, weißer Untergrund) | 128 |
| davon Training (train) | 95 |
| davon Trainingskontrolle (val, automatisch 15 % aus Teach) | 17 |
| davon Test (gezielt in `Testbilder/`, 2 pro Klasse) | 16 |
| Würfel / Münzen | 3 Würfel (rot, creme, schwarz) / eine 1-Euro-Münze |

Die Fotos wurden **nicht von Hand gelabelt**. Die Klasse kommt aus dem Ordnernamen, und den Rahmen findet `datensaetze.py` automatisch über den Kontrast zum Untergrund. Das hat bei **128 von 128 Fotos (100 %)** einen Rahmen ergeben. Bei den ersten 101 Fotos wurde jeder Rahmen einzeln mit dem Auge kontrolliert: Alle saßen am Objekt.

## 2. Wie die Prozentwerte zu lesen sind

- **Gefunden (Recall):** Anteil der echten Objekte, um die die KI einen Rahmen gezeichnet hat.
- **Präzision:** Anteil der gezeichneten Rahmen, die wirklich ein Objekt der richtigen Klasse umschließen. Was fehlt, sind Fehlalarme.
- **Überlappung (IoU):** Wie gut der Rahmen der KI mit dem echten Rahmen übereinstimmt. 100 % heißt deckungsgleich. Ab 50 % zählt er als Treffer.
- **mAP50:** Gesamtnote der Rahmenerkennung über alle Sicherheitsschwellen, Treffer ab 50 % Überlappung. **mAP50-95:** dasselbe mit strengeren Anforderungen an die Rahmenlage (50 bis 95 %).
- **val** hat die KI während des Trainings zur Kontrolle gesehen. **test** hat sie nie gesehen. Das sind die ehrlichen Zahlen.

Achtung, kleine Stichprobe: Pro Klasse gibt es nur 2 Testbilder. Ein einziges falsches Bild ändert den Wert einer Klasse also um 50 Prozentpunkte.

## 3. Rahmenerkennung (Stufe 1: Würfel oder Münze)

Schwelle 50 % Sicherheit, wie im Livebild.

| | val (17 Objekte) | test (16 Objekte) |
|---|---|---|
| Objekte gefunden (Recall) | **100 %** (17/17) | **100 %** (16/16) |
| richtige Oberklasse (Würfel bzw. Münze) | **100 %** | **100 %** |
| Fehlalarme | 0 | 0 |
| Präzision (Ultralytics) | 98,5 % | 98,5 % |
| mAP50 | 99,5 % | 99,5 % |
| mAP50-95 | 92,5 % | 83,2 % |
| mittlere Überlappung der Rahmen | 95 % | 89 % |
| schlechteste Überlappung | 92 % | 74 % |
| Sicherheit der KI bei ihren Rahmen | 88–100 %, Mittel 92 % | 82–100 %, Mittel 91 % |

Nach Oberklasse auf den Testbildern:

| Oberklasse | Objekte | gefunden | mittlere Überlappung | mAP50-95 |
|---|---|---|---|---|
| Würfel | 12 | 100 % | 87 % | 74 % |
| Münze | 4 | 100 % | 95 % | 92 % |

**Bewertung:** Finden und Unterscheiden von Würfel und Münze klappt auf diesen Bildern fehlerfrei. Die Rahmen um Würfel sitzen etwas weniger genau als um die Münze. Ein Würfel hat bei Schrägansicht keine eindeutige Kante, die Münze ist immer rund.

## 4. Klassenerkennung (Stufe 2: Augenzahl, Kopf/Zahl)

Gemessen wurde auf zwei Wegen:
- **Ganze Kette:** Stufe 1 zeichnet den Rahmen, der Ausschnitt geht an Stufe 2. So läuft es im Programm.
- **Nur Stufe 2:** mit den vorbereiteten Ausschnitten aus dem Datensatz.

### Testbilder (16, nie gesehen)

| Klasse | Testbilder | ganze Kette | nur Stufe 2 |
|---|---|---|---|
| augen_1 | 2 | 100 % | 50 % |
| augen_2 | 2 | 100 % | 100 % |
| augen_3 | 2 | 100 % | 50 % |
| augen_4 | 2 | 50 % | 0 % |
| augen_5 | 2 | 0 % | 50 % |
| augen_6 | 2 | 50 % | 0 % |
| kopf | 2 | 100 % | 100 % |
| zahl | 2 | 100 % | 100 % |
| **Würfel gesamt** | 12 | **67 %** | 42 % |
| **Münze gesamt** | 4 | **100 %** | 100 % |
| **alle** | 16 | **75 %** | 56 % |

### Konfusionsmatrix (Testbilder, ganze Kette)

Zeile = echte Klasse, Spalte = Antwort der KI. Auf der Diagonalen stehen die richtigen Antworten.

| echt ↓ / erkannt → | 1 | 2 | 3 | 4 | 5 | 6 | Kopf | Zahl |
|---|---|---|---|---|---|---|---|---|
| **1** | **2** | | | | | | | |
| **2** | | **2** | | | | | | |
| **3** | | | **2** | | | | | |
| **4** | 1 | | | **1** | | | | |
| **5** | | | | | **0** | 2 | | |
| **6** | | | | | 1 | **1** | | |
| **Kopf** | | | | | | | **2** | |
| **Zahl** | | | | | | | | **2** |

### Trainingskontrolle (val, 17 Ausschnitte)

| Klasse | augen_1 | augen_2 | augen_3 | augen_4 | augen_5 | augen_6 | kopf | zahl | alle |
|---|---|---|---|---|---|---|---|---|---|
| richtig | 3/3 | 1/1 | 0/2 | 0/2 | 3/4 | 1/1 | 2/2 | 1/2 | **11/17 = 65 %** |

**Bewertung:**
- Kopf und Zahl werden fast immer richtig erkannt: 100 % auf test, 75 % auf val.
- Bei den Würfeln verwechselt die KI vor allem **viele Augen untereinander** (5 ↔ 6, 4 → 5). Augenzahlen mit wenigen Punkten (1, 2, 3) erkennt sie schon gut. Das passt dazu, dass 4, 5 und 6 Augen sich im kleinen Ausschnitt (96 × 96 Pixel) ähnlicher sehen.
- Dass die ganze Kette besser abschneidet als „nur Stufe 2“, ist bei 16 Bildern Zufall: Die Ausschnitte unterscheiden sich minimal. Es zeigt aber, dass Stufe 2 noch **unsicher** ist und schon auf kleine Verschiebungen reagiert.

## 5. Lernaufwand

| | Stufe 1 (Rahmen) | Stufe 2 (Klassen) |
|---|---|---|
| Modell | YOLO11n (Objekterkennung) | YOLO11n-cls (Klassifizierer) |
| Größe des Modells | 2,6 Mio. Parameter, 5,5 MB | 1,5 Mio. Parameter, 3,2 MB |
| Trainingsbilder | 95 Fotos + 285 künstliche Varianten = 380 | 95 Graustufen-Ausschnitte |
| Bildgröße | 640 Pixel | 96 Pixel |
| Epochen (Durchgänge durch alle Bilder) | 20 | 15 |
| Lernschritte (Stapel à 16 Bilder) | 480 | 90 |
| Bilder insgesamt angesehen | ca. 7.600 | ca. 1.400 |
| Rechenzeit (Laptop-CPU, keine Grafikkarte) | 52,7 Minuten | 24 Sekunden |
| Handarbeit Labeln | 0 Bilder | 0 Bilder |

Zum Vergleich: Ein „volles“ Training ist mit 100 Epochen für Stufe 1 geplant (Laptop ca. 3,5 Stunden, Gaming-PC mit Grafikkarte voraussichtlich unter 15 Minuten).

**Ungleich verteilter Aufwand:** Stufe 1 hat 99 % der Rechenzeit bekommen und ist fast perfekt. Stufe 2 hat nur 24 Sekunden bekommen und ist der Schwachpunkt.

## 6. Nächste Schritte

1. **Stufe 2 nachtrainieren** (PR #11): Jeder Ausschnitt bekommt 3 gedrehte Kopien, das ergibt viermal so viele Trainingsdaten. Dazu kommen 80 bis 150 Epochen statt 15. Das kostet auf dem Laptop nur wenige Minuten. In einem Vorabtest in der Cloud mit einem Teil dieser Fotos waren danach 8 von 8 Testausschnitten richtig.
2. **Livetest** mit der Kamera (`starten.py` → 7), auch auf anderem Untergrund und mit mehreren Würfeln gleichzeitig. Die Fotos stammen bisher nur von einem weißen Tisch.
3. **Mehr Fotos** nach Drehbuch (Situationen E2/E3: anderer Untergrund, anderes Licht, schräg) und die Testwürfel T1/T2.
4. **Kontrast-Zählung** der Augen als zweite Meinung für Stufe 2, vor allem für 4/5/6.
5. **Volles Training** auf dem Gaming-PC.

## 7. Nachtrag: Stufe 2 nachtrainiert (25.11.2026, nachmittags)

Umsetzung von Schritt 1 aus Abschnitt 6: Jeder Trainingsausschnitt hat 3 gedrehte Kopien bekommen (90°, 180°, 270°). Statt 15 Epochen waren bis zu 150 erlaubt, mit vorzeitigem Stopp, wenn 40 Epochen lang keine Verbesserung kommt. Stufe 1 blieb unverändert.

| | vorher (Probelauf) | nachher |
|---|---|---|
| Trainingsausschnitte | 95 | 380 (95 + 285 gedreht) |
| Epochen | 15 | 50 (vorzeitig gestoppt, bestes Modell aus Epoche 10) |
| Rechenzeit (Laptop-CPU) | 24 Sekunden | ca. 4 Minuten |
| **val** (17 Ausschnitte) | 71 % (bestes Modell) | **100 %** |
| **test** (16 Ausschnitte, nur Stufe 2) | 56 % (9/16) | **81 % (13/16)** |

Testbilder nach Klasse (nur Stufe 2):

| Klasse | augen_1 | augen_2 | augen_3 | augen_4 | augen_5 | augen_6 | kopf | zahl |
|---|---|---|---|---|---|---|---|---|
| vorher | 50 % | 100 % | 50 % | 0 % | 50 % | 0 % | 100 % | 100 % |
| **nachher** | **100 %** | **100 %** | **100 %** | **100 %** | **50 %** | **0 %** | **100 %** | **100 %** |

Die 3 verbliebenen Fehler:
- 5 Augen erkannt als 4
- 6 Augen erkannt als 4
- 6 Augen erkannt als 3

**Bewertung:** Die gedrehten Kopien haben Stufe 2 deutlich verbessert, mit 25 Prozentpunkten mehr auf den Testbildern bei 4 Minuten Rechenzeit. Würfel 1 bis 4, Kopf und Zahl werden jetzt durchgehend richtig erkannt. Schwach bleiben nur 5 und 6 Augen, also die Würfel mit den meisten, eng stehenden Punkten. Dort „übersieht“ die KI Punkte und nennt eine zu kleine Zahl. Abhilfe: mehr Fotos von 5 und 6 (auch schräg und mit anderem Licht) und die Kontrast-Zählung als zweite Meinung. Die Messung der ganzen Kette (Stufe 1 + Stufe 2) mit dem neuen Modell steht noch aus und folgt mit dem Livetest.

---
*Messung: Modelle `modelle/stufe1.pt` und `stufe2.pt` vom 25.11.2026 (Probelauf), nachgemessen auf den Datensätzen val/test aus `datensaetze.py`. Ultralytics 8.4, Schwelle Stufe 1: 50 %.*
