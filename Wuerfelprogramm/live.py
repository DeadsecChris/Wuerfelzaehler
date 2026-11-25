"""Live-Erkennung: Würfel und Münze im Kamerabild finden und auswerten.

Ablauf je Bild:
    1. Stufe 1 (modelle/stufe1.pt) findet alle Würfel und Münzen.
    2. Jedes Objekt wird als Graustufen-Ausschnitt an Stufe 2 (modelle/stufe2.pt)
       gegeben, die Augenzahl bzw. Kopf/Zahl liest.
    3. Plausibilität: Ein Würfel kann nur augen_1..6 sein, eine Münze nur kopf/zahl.
    4. Münze: Zahl ab 80 %, Kopf bis 20 %, dazwischen "unsicher".
    5. Ergebnis: Kopf = Summe der Augen, Zahl = Produkt.

Tasten: q = Beenden, + / - = Schwelle für Stufe 1 ändern.

Aufruf:  python live.py [--kamera 0|URL] [--schwelle 0.5]
"""
from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

import cv2
import numpy as np

from datensaetze import ausschnitt

ORDNER = Path(__file__).resolve().parent
MODELLE = ORDNER / "modelle"
GRUEN, GELB, ROT, WEISS = (0, 200, 0), (0, 220, 255), (0, 0, 255), (255, 255, 255)


def lade_modelle():
    from ultralytics import YOLO
    fehlt = [p.name for p in (MODELLE / "stufe1.pt", MODELLE / "stufe2.pt") if not p.exists()]
    if fehlt:
        print(f"Modell fehlt: {', '.join(fehlt)}. Zuerst trainieren (starten.py -> Trainieren).")
        return None, None
    return YOLO(str(MODELLE / "stufe1.pt")), YOLO(str(MODELLE / "stufe2.pt"))


def lies_objekt(m2, bild: np.ndarray, box_norm, ist_wuerfel: bool):
    """Gibt (Wert, Text, Farbe) zurück. Wert: 1..6 bei Würfeln, 'kopf'/'zahl' oder None."""
    teil = ausschnitt(bild, box_norm, 0.1)
    if teil is None:
        return None, "?", ROT
    erg = m2(cv2.cvtColor(teil, cv2.COLOR_GRAY2BGR), verbose=False)[0]
    p = {erg.names[i]: float(w) for i, w in enumerate(erg.probs.data.tolist())}
    if ist_wuerfel:
        augen = {k: v for k, v in p.items() if k.startswith("augen_")}
        if not augen:
            return None, "?", ROT
        beste = max(augen, key=augen.get)
        sicher = augen[beste] / max(sum(augen.values()), 1e-9)
        wert = int(beste[-1])
        return wert, f"{wert} ({sicher:.0%})", GRUEN if sicher >= 0.6 else GELB
    kopf, zahl = p.get("kopf", 0.0), p.get("zahl", 0.0)
    anteil_zahl = zahl / max(kopf + zahl, 1e-9)
    if anteil_zahl >= 0.8:
        return "zahl", f"Zahl ({anteil_zahl:.0%})", GRUEN
    if anteil_zahl <= 0.2:
        return "kopf", f"Kopf ({1 - anteil_zahl:.0%})", GRUEN
    return None, f"unsicher ({anteil_zahl:.0%} Zahl)", GELB


def ergebnis_text(augen: list[int], muenze: list) -> str:
    if not augen:
        return "Keine Wuerfel erkannt"
    if len(muenze) != 1:
        return f"Augen: {' '.join(map(str, augen))}  |  Muenze: {'keine' if not muenze else 'mehrere'}"
    seite = muenze[0]
    if seite == "kopf":
        return f"KOPF: {' + '.join(map(str, augen))} = {sum(augen)}"
    if seite == "zahl":
        return f"ZAHL: {' x '.join(map(str, augen))} = {math.prod(augen)}"
    return f"Augen: {' '.join(map(str, augen))}  |  Muenze unsicher"


def text(bild, t, pos, farbe=WEISS, skala=0.6):
    cv2.putText(bild, t, pos, cv2.FONT_HERSHEY_SIMPLEX, skala, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(bild, t, pos, cv2.FONT_HERSHEY_SIMPLEX, skala, farbe, 1 if skala < 0.8 else 2, cv2.LINE_AA)


def main() -> int:
    ap = argparse.ArgumentParser(description="Live-Erkennung mit Kamera")
    ap.add_argument("--kamera", default="0", help="Kamera-Nummer oder URL der Handy-Kamera")
    ap.add_argument("--schwelle", type=float, default=0.5, help="Mindest-Sicherheit Stufe 1 (Standard 0.5)")
    args = ap.parse_args()

    m1, m2 = lade_modelle()
    if m1 is None:
        return 1
    quelle = int(args.kamera) if args.kamera.isdigit() else args.kamera
    kamera = cv2.VideoCapture(quelle)
    if not kamera.isOpened():
        print(f"Kamera {args.kamera} lässt sich nicht öffnen. Andere Nummer probieren.")
        return 1

    fenster = "Wuerfel-Zaehler live (q = Ende, +/- = Schwelle)"
    cv2.namedWindow(fenster, cv2.WINDOW_NORMAL)
    schwelle = args.schwelle
    fps, letzte = 0.0, time.time()
    while True:
        ok, bild = kamera.read()
        if not ok:
            print("Kein Bild von der Kamera.")
            break
        h, w = bild.shape[:2]
        anzeige = bild.copy()
        augen, muenze = [], []
        for box in m1(bild, conf=schwelle, verbose=False)[0].boxes:
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
            ist_wuerfel = int(box.cls) == 0
            box_norm = ((x1 + x2) / 2 / w, (y1 + y2) / 2 / h, (x2 - x1) / w, (y2 - y1) / h)
            wert, beschriftung, farbe = lies_objekt(m2, bild, box_norm, ist_wuerfel)
            if ist_wuerfel and wert is not None:
                augen.append(wert)
            elif not ist_wuerfel:
                muenze.append(wert)
            name = "Wuerfel" if ist_wuerfel else "Muenze"
            cv2.rectangle(anzeige, (x1, y1), (x2, y2), farbe, 2)
            text(anzeige, f"{name} {float(box.conf):.0%}: {beschriftung}", (x1, max(18, y1 - 6)), farbe)

        jetzt = time.time()
        fps = 0.9 * fps + 0.1 / max(jetzt - letzte, 1e-6)
        letzte = jetzt
        cv2.rectangle(anzeige, (0, 0), (w, 64), (0, 0, 0), -1)
        text(anzeige, ergebnis_text(augen, muenze), (10, 28), WEISS, 0.9)
        text(anzeige, f"{fps:.0f} FPS  |  Schwelle Stufe 1: {schwelle:.0%}", (10, 54), (200, 200, 200), 0.5)
        cv2.imshow(fenster, anzeige)

        taste = cv2.waitKey(1) & 0xFF
        if taste in (ord("q"), 27):
            break
        if taste == 255 and cv2.getWindowProperty(fenster, cv2.WND_PROP_VISIBLE) < 1:
            break
        if taste in (ord("+"), ord("=")):
            schwelle = min(0.95, schwelle + 0.05)
        elif taste == ord("-"):
            schwelle = max(0.05, schwelle - 0.05)

    kamera.release()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
