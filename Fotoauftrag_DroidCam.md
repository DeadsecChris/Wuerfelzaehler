# Fotoauftrag: Nachteachen mit der Handykamera (DroidCam)

Stand 25.11.2026. Für die nächste Sitzung.

## Warum

Der Livetest am 25.11. mit der Handykamera über DroidCam hat gezeigt:

- **Stufe 1** (Würfel und Münze finden) klappt live.
- **Würfelaugen** werden live noch zu oft falsch gelesen. Auf den Testbildern lagen 5 und 6 Augen schon vorher am schwächsten.
- **Münze Kopf/Zahl** hängt stark vom **Licht** ab.

Die bisherigen Trainingsfotos stammen von der Handy-Fotoapp mit hoher Auflösung, auf weißem Tisch und bei immer ähnlichem Licht. Live kommt das Bild aber über DroidCam mit 640 × 480 und unter anderem Licht. Am meisten bringen deshalb **neue Fotos aus genau dem Live-Aufbau**.

## 1. Kamera verbinden

1. App **DroidCam** auf dem Handy öffnen. Handy und Laptop müssen im selben WLAN sein.
2. Die App zeigt die Adresse, z. B. `192.168.99.157:4747`. Die Adresse für unser Programm lautet dann:
   `http://192.168.99.157:4747/video` (nur **ein** Schrägstrich vor `video`)
3. Das Bild geht immer nur an **ein** Programm. Browser-Tab und DroidCam-Client am Laptop deshalb vorher schließen.
4. Handy fest **senkrecht über** dem Tisch befestigen (Halterung oder Bücherstapel), ca. 30 bis 40 cm Abstand, wie beim Livetest.

Alternativ per USB: DroidCam-Client für Windows plus USB-Debugging am Handy. Dann ist die Kameranummer meist `1` oder `2`.

## 2. Fotos aufnehmen

`starten.py` → **3 „Fotos aufnehmen“** → als Kamera die DroidCam-Adresse eingeben.

| Taste | Wirkung |
|---|---|
| `e` | Einzelaufnahmen |
| `1` … `6` | Klasse Würfel mit 1 … 6 Augen |
| `k` / `z` | Klasse Münze Kopf / Zahl |
| `d` | Würfel weiterschalten (WA, WB, WC, T1, T2), steht im Dateinamen |
| `s` | Situation weiterschalten (E1, E2, E3, siehe Drehbuch 2.1) |
| `t` | Teach ↔ Test umschalten |
| **Leertaste** | Foto speichern |
| `q` | Beenden |

Oben im Bild stehen Ziel, Klasse und der nächste Dateiname. Die Fotos landen direkt im richtigen Ordner unter `C:\Users\chris\OneDrive\Bilder_wuerfelzaehler`. Labeln ist nicht nötig.

Immer nur **ein** Objekt ins Bild legen, mit etwas Abstand zum Bildrand.

## 3. Was fotografiert wird

### Würfel (Teachbilder)

| Klasse | Anzahl neu | Hinweis |
|---|---|---|
| augen_1 bis augen_4 | je ca. 10 | alle 3 Würfel (WA, WB, WC) abwechselnd |
| **augen_5, augen_6** | **je ca. 15** | die schwächsten Klassen, auch leicht schräg liegend |

Pro Würfel abwechseln:
- Würfel zwischen den Fotos **verschieben und drehen**
- **Licht wechseln**: Deckenlicht, Tageslicht, Lampe von der Seite mit Schatten

### Münze (Teachbilder)

| Klasse | Anzahl neu | Lichtsituationen |
|---|---|---|
| muenze_kopf | ca. 15 | Deckenlicht, Tageslicht, seitliche Lampe mit Schatten, abgedunkelt, mit Spiegelung |
| muenze_zahl | ca. 15 | dieselben Lichtsituationen wie bei Kopf |

Die Münze dabei auch drehen und an verschiedene Stellen im Bild legen. Die KI muss jede Lichtsituation gesehen haben, die später beim Spielen vorkommt.

### Testbilder

Mit `t` auf **Test** umschalten und **2 Fotos pro Klasse** aufnehmen, ebenfalls mit wechselndem Licht. Danach mit `t` wieder auf Teach zurückschalten. Diese Fotos werden nie trainiert. Mit ihnen messen wir ehrlich, ob es besser geworden ist.

**Gesamt:** ca. 120 neue Teachfotos und 16 neue Testfotos.

## 4. Danach trainieren und testen

1. `starten.py` → **5 „Datensätze erzeugen“**. Danach den Bericht und kurz `datensaetze/kontrolle/` ansehen, ob alle Rahmen sitzen.
2. `starten.py` → **6 „Modelle trainieren“** → **`2`** (nur Stufe 2, ca. 5 Minuten).
3. `starten.py` → **7 „Live-Erkennung“** mit der DroidCam-Adresse, bei verschiedenem Licht testen.
4. Die Zeile „Stufe 2 auf den Testbildern: x von y richtig“ notieren. Sie kommt in den Ergebnisbericht.

Stufe 1 wird später einmal voll neu trainiert, am besten auf dem Gaming-PC (`6` → `v`). Dann lernt auch sie die neuen Lichtsituationen.
