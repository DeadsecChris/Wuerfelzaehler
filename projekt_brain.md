# Projekt-Brain: Würfel-Zähler

Zentrale Sammlung aller Anforderungen, Entscheidungen und Pläne zum Projekt. Stand: 12.11.2026.

## 1. Projekt in Kürze

- **Name:** Würfel-Zähler
- **Team:** Christian Maschke, Niklas Bäricke
- **Idee:** 3 Würfel und 1 Münze werden auf den Tisch geworfen. Die Münze bestimmt die Rechenart, und wer zuerst das richtige Ergebnis ruft, gewinnt die Runde.
- **Rolle der KI:** Eine selbst trainierte KI erkennt per Kamera die Augenzahlen und die Münzseite. Das Programm berechnet daraus das Ergebnis und zeigt es an (Schiedsrichter bzw. Cheat-Hilfe).
- **Umfang (Lastenheft vom 12.11.2026):** Kein Mitspieler-Modus, keine Antwortprüfung und kein Punktestand im Programm. Die Spielregeln unten gelten am Tisch, das Programm liefert nur das richtige Ergebnis.
- **Vorgabe:** Die KI muss selbst trainiert werden, lokal und ohne Teachable Machine.

## 2. Spielregeln

- **Kopf:** Augenzahlen addieren (Ergebnis 3 bis 18).
- **Zahl:** Augenzahlen multiplizieren (Ergebnis 1 bis 216).
- **Richtige Antwort:** 1 Punkt, und man darf einen Schluck verteilen.
- **Falsche Antwort:** Strafschluck, und man würfelt die nächste Runde.

## 3. Abgaben

| Abgabe | Fällig | Status |
|---|---|---|
| Vereinfachtes Lastenheft | 12.11.2026, 22:00 | Fertig, Namen eingetragen |
| Drehbuch Bilderstellung | 18.11.2026, 22:00 | Dokument erstellt, Namen fehlen noch |

Beide Dokumente werden gemeinsam erstellt, aber von jedem Teammitglied einzeln eingereicht.

### Geforderte Inhalte Lastenheft

1. Projektbeschreibung (Name, Idee, Anwendungsbereich)
2. Zielsetzung (Problem und Nutzen)
3. Bilderkennung (Klassen, benötigte Bilder)
4. Anwendungsprogramm (konkrete Aufgabe; die reine Anzeige der erkannten Klasse reicht nicht)
5. Technische Anforderungen (Funktionen, Bildeingabe, Verarbeitung, Ausgabe, Oberfläche)
6. KI-Modell und Entwicklungsumgebung (Bibliotheken, lokales Training)
7. Geplanter Programmablauf
8. Aufgabenverteilung

### Geforderte Inhalte Drehbuch

1. Zu erkennende Klassen und Bildmotive
2. Planung der Fotoaufnahmen (Perspektiven, Abstände, Hintergründe, Licht, Positionen), möglichst als Tabelle
3. Umfang des Datensatzes (Originalbilder pro Klasse, zusätzliche Varianten)
4. Technische Bildvariation (Data Augmentation)
5. Aufteilung in Trainings- und Testdaten (Testbilder unabhängig, keine Varianten von Trainingsbildern im Test)
6. Organisation der Bilddaten (Benennung, Ordnerstruktur, Klassenzuordnung)
7. Aufgabenverteilung im Team

## 4. Bilderkennung

- **Verfahren:** Objekterkennung. Die KI findet jedes Objekt im Bild (Rahmen) und ordnet ihm eine Klasse zu.
- **Objekte:** 3 gleiche weiße Würfel mit schwarzen Augen und immer dieselbe 1-Euro-Münze (Entscheidung 12.11.2026: keine wechselnden Münzen, weil die Kopfseiten je nach Land und Münzart verschieden aussehen).
- **Ungültige Würfe:** Eine zusätzliche Klasse für ungültige Lagen ist bewusst offen und wird im Laufe der Entwicklung entschieden.
- **Regel fürs Labeln:** Die Klasse eines Würfels ist die Augenzahl, die oben liegt. Der Rahmen umfasst den ganzen Würfel.

| ID | Klassenname | Bildmotiv |
|---|---|---|
| 0 | `wuerfel_1` | Würfel, oben liegt die 1 |
| 1 | `wuerfel_2` | Würfel, oben liegt die 2 |
| 2 | `wuerfel_3` | Würfel, oben liegt die 3 |
| 3 | `wuerfel_4` | Würfel, oben liegt die 4 |
| 4 | `wuerfel_5` | Würfel, oben liegt die 5 |
| 5 | `wuerfel_6` | Würfel, oben liegt die 6 |
| 6 | `muenze_kopf` | 1-Euro-Münze, Bildseite oben |
| 7 | `muenze_zahl` | 1-Euro-Münze, Wertseite oben (Ziffer 1) |

## 5. Anwendungsprogramm

Das Programm erkennt den Wurf, prüft ihn und berechnet das Ergebnis. Die reine Anzeige der Klassen reicht laut Vorgabe nicht, deshalb rechnet es mit den erkannten Klassen.

### Funktionen

- **Kameraübertragung:** Nach Druck auf den Start-Button („Scharfschalten“) sendet das Programm laufend Kamerabilder an das KI-Modell.
- **Vollständigkeit prüfen:** gewertet wird nur bei genau 3 Würfeln und 1 Münze, sonst Hinweis „Bitte neu würfeln“.
- **Ergebnis berechnen:** Den Würfelklassen werden Zahlenwerte zugeordnet; Summe bei Kopf, Produkt bei Zahl.
- **Ergebnisausgabe:** Das Ergebnis erscheint als Text.

### Technische Anforderungen

- **Eingabe:** Livebild einer Webcam (oder Handy als Webcam) über der Wurffläche, Start-Button. Zum Testen auch einzelne Bilddateien.
- **Verarbeitung:** Nur Erkennungen mit Sicherheit ab 50 % zählen (einstellbar). Ein Wurf gilt als stabil nach ca. 5 gleichen Kamerabildern. Ergebnis spätestens 2 Sekunden nach Stillstand.
- **Leistung:** mindestens 10 Bilder pro Sekunde auf einem Laptop ohne Grafikkarte.
- **Ausgabe:** Livebild, Ergebnis in Textform, Hinweise bei Fehlern (zu wenige/zu viele Objekte, zu unsichere Erkennung).
- **Oberfläche:** Programmfenster mit Livebild, Statusbereich und Start-Button.
- **Ziel:** mindestens 90 % der Würfe werden im festgelegten Aufbau vollständig richtig erkannt.

### Programmablauf

1. **Start:** Modell laden, Kamera öffnen, auf den Start-Button warten.
2. **Bilderfassung:** Die Kamera liefert laufend Bilder an das Modell.
3. **Erkennung:** Das Modell liefert pro Objekt Rahmen, Klasse und Sicherheit.
4. **Filterung:** Unsichere Erkennungen verwerfen, auf ein stabiles Ergebnis warten.
5. **Prüfung:** Genau 3 Würfel und 1 Münze? Sonst Hinweis und zurück zu Schritt 2.
6. **Wertzuteilung und Berechnung:** Augenzahlen und Rechenart aus den Klassen, Summe oder Produkt.
7. **Ausgabe:** Ergebnis als Text anzeigen.

## 6. KI-Modell und Werkzeuge

| Werkzeug / Bibliothek | Verwendung |
|---|---|
| Python 3.11 oder neuer | Programmiersprache für Training und Programm |
| Visual Studio Code | Entwicklungsumgebung |
| Ultralytics (YOLO) | Modell für die Objekterkennung, Variante „nano“ |
| PyTorch | Grundlage für das Training |
| OpenCV | Kamerazugriff, Bildverarbeitung, Programmfenster |
| Albumentations | Bildvariation inklusive Anpassung der Rahmen |
| NumPy | Rechnen mit Bilddaten |
| Label Studio | Labeln der Fotos |

### Training

- Lokal auf dem eigenen Laptop, ohne Cloud-Dienst und ohne Teachable Machine.
- Vortrainiertes YOLO-Modell als Startpunkt, nachtrainiert auf die 8 Klassen (Transfer Learning).
- Bildgröße 640 Pixel, ca. 50 bis 100 Epochen.
- Auswertung auf den Testbildern: Verwechslungsmatrix, Präzision und Trefferquote je Klasse.
- Bei Schwächen einzelner Klassen gezielt Fotos nachlegen und neu trainieren.
- Ergebnis: Modelldatei `best.pt`, die das Programm beim Start lädt.

## 7. Bilddatensatz

### Aufnahmeplan

| Nr. | Art | Perspektive | Abstand | Hintergrund | Licht | Bilder |
|---|---|---|---|---|---|---|
| E1 | Einzel | senkrecht von oben | ca. 30 cm | dunkelgrüner Filz | Tageslicht am Fenster | 40 |
| E2 | Einzel | schräg, ca. 60–70° | ca. 40 cm | Holztisch | Deckenlicht am Abend | 40 |
| E3 | Einzel | senkrecht von oben | ca. 50 cm | weißes Papier | Lampe von der Seite, mit Schatten | 40 |
| W1 | Wurf | senkrecht von oben | ca. 40 cm | dunkelgrüner Filz | Tageslicht am Fenster | 50 |
| W2 | Wurf | senkrecht von oben | ca. 40 cm | dunkelgrüner Filz | Deckenlicht am Abend | 40 |
| W3 | Wurf | senkrecht von oben | ca. 40 cm | Holztisch | Tageslicht am Fenster | 30 |
| W4 | Wurf | leicht schräg, ca. 70° | ca. 50 cm | dunkelgrüner Filz | Lampe von der Seite, mit Schatten | 30 |
| W5 | Wurf | senkrecht von oben | je zur Hälfte ca. 30 cm und ca. 60 cm | weißes Papier | gedimmtes Licht | 30 |
| | **Summe** | | | | | **300** |

- **Einzelaufnahmen (E1–E3):** genau ein Objekt, je Situation 5 Bilder pro Klasse.
- **Wurfaufnahmen (W1–W5):** echte Spielsituation mit 3 Würfeln und Münze. W1 und W2 sind der geplante Spielaufbau.
- **Lagen:** jedes Bild mit anderer Drehung und Position; bei etwa jedem fünften Wurf liegen die Objekte eng aneinander.
- **Ausgewogenheit:** Eine Strichliste hält fest, wie oft jede Klasse fotografiert wurde. Seltene Klassen werden gezielt von Hand gelegt.

### Umfang

| Bildart | Anzahl |
|---|---|
| Einzelaufnahmen | 120 (15 pro Klasse) |
| Wurfaufnahmen | 180 |
| Originalbilder gesamt | 300 |
| Technisch erzeugte Varianten | 630 (3 je Trainingsbild) |
| Bilder gesamt | 930 |

Jede Klasse ist rund 105-mal in den Originalbildern zu sehen.

### Data Augmentation

| Verfahren | Einstellung |
|---|---|
| Drehen | beliebiger Winkel, 0–360° |
| Helligkeit | ± 25 % |
| Kontrast | ± 20 % |
| Zuschneiden und Skalieren | Ausschnitt 80–100 %, Zoom 80–120 % |
| Farbsättigung | ± 30 % |
| Bildrauschen | leicht |
| Unschärfe | leicht |

- Jede Variante kombiniert zufällig 2 bis 3 Verfahren.
- **Kein Spiegeln:** Ziffer und Motiv der Münze wären sonst spiegelverkehrt.
- Beim Zuschneiden bleiben alle Objekte vollständig im Bild.

### Aufteilung

| Datensatz | Originalbilder | Varianten |
|---|---|---|
| Training | 210 (70 %) | 630 |
| Validierung | 45 (15 %) | keine |
| Test | 45 (15 %) | keine |

- Erst aufteilen, dann Varianten erzeugen, und zwar nur aus Trainingsbildern.
- Die Testbilder entstehen in einer eigenen Sitzung an einem anderen Tag, mit rund 15 % der Bilder jeder Aufnahmesituation.
- Kein Bild und keine Variante liegt in mehr als einem Datensatz.

### Benennung und Ordner

- **Wurfaufnahme:** `wurf_<Situation>_<Nummer>.jpg`, z. B. `wurf_W3_0042.jpg`
- **Einzelaufnahme:** `einzel_<Situation>_<Klasse>_<Nummer>.jpg`, z. B. `einzel_E2_wuerfel_4_0007.jpg`
- **Variante:** Name des Originals mit Zusatz, z. B. `wurf_W3_0042_aug2.jpg`
- **Klassenzuordnung:** über eine Label-Datei pro Bild mit gleichem Namen (`.txt`, eine Zeile pro Objekt mit Klassen-ID und Rahmen), nicht über Klassenordner.

```
wuerfel-zaehler/
├── rohbilder/              Originalfotos, unverändert (Sicherung)
│   ├── einzel/
│   ├── wurf/
│   └── test_sitzung/
├── dataset/
│   ├── images/
│   │   ├── train/          210 Originale + 630 Varianten
│   │   ├── val/            45 Originale
│   │   └── test/           45 Originale
│   ├── labels/
│   │   ├── train/          eine .txt-Datei pro Bild
│   │   ├── val/
│   │   └── test/
│   └── data.yaml           Klassenliste und Pfade
└── aufnahmeprotokoll.xlsx  Strichliste und Stand der Aufnahmen
```

## 8. Aufgabenverteilung

| Person | Aufgaben |
|---|---|
| Niklas Bäricke | Aufbau und Bilderstellung |
| Christian Maschke | Training, Codeentwicklung und Softwareumgebung |
| Gemeinsam | Testen, Auswerten, Trainings-/Entwicklungsplanung, Labeln der Bilder, Bildvariation und Organisation des Datensatzes, Dokumentation und Präsentation |

## 9. Zeitplan

| Woche | Aufgaben |
|---|---|
| 1 | Aufbau festlegen, Python einrichten, Fotos aufnehmen und labeln, erstes Probemodell mit ca. 50 Bildern |
| 2 | Modell trainieren, mit der Verwechslungsmatrix testen, bei Schwächen Fotos nachlegen |
| 3 | Programm mit Webcam, Vollständigkeitsprüfung und Ergebnisanzeige fertigstellen, Präsentation vorbereiten |

## 10. Risiken

- **Falsch erkannter Würfel:** Ein einzelner Fehler verfälscht das Ergebnis, besonders beim Multiplizieren. Dagegen helfen genug Trainingsfotos und die Kontrollanzeige an jedem Objekt.
- **Münze:** Sie glänzt, und beide Seiten können sich ähneln. Immer dieselbe Münze verwenden und beide Seiten gleich oft fotografieren.
- **Verdeckung:** Würfel und Münze können aufeinander landen. Eine Wurffläche mit Rand (z. B. ein Tablett) verwenden.
- **Licht und Hintergrund:** Wechselnde Bedingungen stören die Erkennung. Die Trainingsfotos decken deshalb mehrere Situationen ab.

## 11. Offene Punkte

- Mit der Lehrkraft klären, ob ein vortrainiertes Modell als Startpunkt erlaubt ist.
- Namen und Rollenverteilung im Drehbuch eintragen (im Lastenheft erledigt).
- Material bestätigen: Würfel, Münze, Hintergründe (Filz, Holztisch, weißes Papier), Kamera.
