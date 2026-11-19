"""Fotos für den Datensatz aufnehmen (Livebild, Speichern per Leertaste).

Speichert direkt in den Bilderordner (OneDrive) in den richtigen Unterordner und
mit dem Dateinamen aus dem Drehbuch (Abschnitt 6.1):
    Teachbilder/wurf/wurf_W1_0001.jpg
    Teachbilder/einzel/wuerfel_4/einzel_E2_wuerfel_4_WB_0007.jpg
    Teachbilder/einzel/muenze_kopf/einzel_E1_muenze_kopf_0003.jpg
    Testbilder/wurf/test_W1_0005.jpg

Tasten im Fenster (Einstellungen stehen oben im Bild, sie werden nicht mitgespeichert):
    Leertaste   Foto speichern
    w / e       Wurf / Einzel
    s           Situation weiterschalten (W1..W5 bzw. E1..E3, siehe Drehbuch 2.1)
    1..6 k z    Klasse bei Einzelaufnahmen (wuerfel_1..6, muenze_kopf, muenze_zahl)
    d           Würfel weiterschalten (WA, WB, WC, T1, T2)
    t           Teach / Test umschalten
    q           Beenden

Aufruf:  python fotos.py [--kamera 0|URL] [--bilder ORDNER]
         (am einfachsten über starten.py, Punkt "Fotos aufnehmen")
"""
import argparse
import re
import sys
import time
from pathlib import Path

import cv2
import numpy as np

STANDARD_BILDER = Path(r"C:\Users\chris\OneDrive\Bilder_wuerfelzaehler")
SITUATIONEN = {"wurf": ["W1", "W2", "W3", "W4", "W5"], "einzel": ["E1", "E2", "E3"]}
KLASSEN_TASTEN = {"1": "wuerfel_1", "2": "wuerfel_2", "3": "wuerfel_3", "4": "wuerfel_4",
                  "5": "wuerfel_5", "6": "wuerfel_6", "k": "muenze_kopf", "z": "muenze_zahl"}
WUERFEL = ["WA", "WB", "WC", "T1", "T2"]


class Zustand:
    def __init__(self) -> None:
        self.ziel = "teach"        # teach | test
        self.art = "wurf"          # wurf | einzel
        self.situation = {"wurf": 0, "einzel": 0}
        self.klasse = "wuerfel_1"
        self.wuerfel = 0

    @property
    def sit(self) -> str:
        return SITUATIONEN[self.art][self.situation[self.art]]

    def ordner(self, bilder: Path) -> Path:
        haupt = bilder / ("Teachbilder" if self.ziel == "teach" else "Testbilder")
        return haupt / "wurf" if self.art == "wurf" else haupt / "einzel" / self.klasse

    def praefix(self) -> str:
        if self.ziel == "test":
            return f"test_{self.sit}_"
        if self.art == "wurf":
            return f"wurf_{self.sit}_"
        if self.klasse.startswith("muenze"):
            return f"einzel_{self.sit}_{self.klasse}_"
        return f"einzel_{self.sit}_{self.klasse}_{WUERFEL[self.wuerfel]}_"


def naechste_nummer(ordner: Path, praefix: str) -> int:
    muster = re.compile(re.escape(praefix) + r"(\d+)\.(jpg|jpeg|png)$", re.IGNORECASE)
    nummern = [int(m.group(1)) for p in ordner.glob(praefix + "*") if (m := muster.match(p.name))]
    return max(nummern, default=0) + 1


def anzahl_bilder(ordner: Path) -> int:
    return sum(1 for p in ordner.glob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png"))


def speichere(pfad: Path, bild: np.ndarray) -> bool:
    # imencode + tofile, damit auch Pfade mit Umlauten funktionieren
    ok, daten = cv2.imencode(".jpg", bild, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if ok:
        daten.tofile(str(pfad))
    return ok


def oeffne_kamera(quelle: str, breite: int, hoehe: int) -> cv2.VideoCapture:
    q = int(quelle) if quelle.isdigit() else quelle
    kamera = cv2.VideoCapture(q, cv2.CAP_DSHOW) if isinstance(q, int) and sys.platform == "win32" else cv2.VideoCapture(q)
    if isinstance(q, int):
        kamera.set(cv2.CAP_PROP_FRAME_WIDTH, breite)
        kamera.set(cv2.CAP_PROP_FRAME_HEIGHT, hoehe)
    return kamera


def zeichne_text(bild: np.ndarray, zeilen: list[str]) -> None:
    skala = max(0.5, bild.shape[1] / 1600)
    dicke = max(1, round(skala * 2))
    zeilenhoehe = int(32 * skala) + 6
    cv2.rectangle(bild, (0, 0), (bild.shape[1], zeilenhoehe * len(zeilen) + 8), (0, 0, 0), -1)
    for i, z in enumerate(zeilen):
        cv2.putText(bild, z, (10, zeilenhoehe * (i + 1)), cv2.FONT_HERSHEY_SIMPLEX, skala,
                    (255, 255, 255), dicke, cv2.LINE_AA)


def main() -> int:
    ap = argparse.ArgumentParser(description="Fotos für den Würfel-Datensatz aufnehmen")
    ap.add_argument("--kamera", default="0", help="Kamera-Nummer (0, 1, ...) oder URL der Handy-Kamera")
    ap.add_argument("--bilder", type=Path, default=STANDARD_BILDER, help="Bilderordner mit Teachbilder/ und Testbilder/")
    ap.add_argument("--breite", type=int, default=1920, help="gewünschte Bildbreite (Standard 1920)")
    ap.add_argument("--hoehe", type=int, default=1080, help="gewünschte Bildhöhe (Standard 1080)")
    args = ap.parse_args()

    if not args.bilder.is_dir():
        print(f"Bilderordner nicht gefunden: {args.bilder}\nMit --bilder den richtigen Ordner angeben.")
        return 1

    kamera = oeffne_kamera(args.kamera, args.breite, args.hoehe)
    if not kamera.isOpened():
        print(f"Kamera {args.kamera} lässt sich nicht öffnen. Andere Nummer probieren (--kamera 1).")
        return 1

    z = Zustand()
    fenster = "Fotos aufnehmen (Leertaste = speichern, q = beenden)"
    cv2.namedWindow(fenster, cv2.WINDOW_NORMAL)
    blitz_bis = 0.0
    meldung = ""
    gespeichert = 0
    print(f"Bilderordner: {args.bilder}")

    while True:
        ok, bild = kamera.read()
        if not ok:
            print("Kein Bild von der Kamera.")
            break

        ordner = z.ordner(args.bilder)
        nr = naechste_nummer(ordner, z.praefix()) if ordner.is_dir() else 1
        name = f"{z.praefix()}{nr:04d}.jpg"
        zeilen = [
            f"{'TEACH' if z.ziel == 'teach' else 'TEST'} | {z.art.upper()} {z.sit}"
            + (f" | {z.klasse}" if z.art == "einzel" else "")
            + (f" | Wuerfel {WUERFEL[z.wuerfel]}" if z.art == "einzel" and not z.klasse.startswith("muenze") else ""),
            f"Naechstes: {name}  (im Ordner: {anzahl_bilder(ordner) if ordner.is_dir() else 0})",
            "Leer=Foto  w/e=Wurf/Einzel  s=Situation  1-6/k/z=Klasse  d=Wuerfel  t=Teach/Test  q=Ende",
        ]
        if meldung:
            zeilen.append(meldung)

        anzeige = bild.copy()
        zeichne_text(anzeige, zeilen)
        if time.time() < blitz_bis:
            cv2.rectangle(anzeige, (0, 0), (anzeige.shape[1] - 1, anzeige.shape[0] - 1), (0, 255, 0), 12)
        cv2.imshow(fenster, anzeige)

        taste = cv2.waitKey(1) & 0xFF
        if taste == 255:
            if cv2.getWindowProperty(fenster, cv2.WND_PROP_VISIBLE) < 1:
                break
            continue
        zeichen = chr(taste).lower()
        if zeichen == "q" or taste == 27:
            break
        elif taste == 32:
            ordner.mkdir(parents=True, exist_ok=True)
            pfad = ordner / name
            if speichere(pfad, bild):
                gespeichert += 1
                blitz_bis = time.time() + 0.3
                meldung = f"Gespeichert: {pfad.relative_to(args.bilder)} ({bild.shape[1]}x{bild.shape[0]})"
                print(meldung)
            else:
                meldung = "FEHLER beim Speichern!"
        elif zeichen == "w":
            z.art = "wurf"
        elif zeichen == "e":
            z.art = "einzel"
        elif zeichen == "s":
            z.situation[z.art] = (z.situation[z.art] + 1) % len(SITUATIONEN[z.art])
        elif zeichen == "t":
            z.ziel = "test" if z.ziel == "teach" else "teach"
        elif zeichen == "d":
            z.wuerfel = (z.wuerfel + 1) % len(WUERFEL)
        elif zeichen in KLASSEN_TASTEN:
            z.klasse = KLASSEN_TASTEN[zeichen]
            z.art = "einzel"

    kamera.release()
    cv2.destroyAllWindows()
    print(f"{gespeichert} Fotos gespeichert.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
