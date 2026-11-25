"""Trainiert beide Modelle aus den erzeugten Datensätzen.

Voraussetzung: datensaetze.py ist gelaufen (Ordner datensaetze/ mit stufe1 und stufe2).

    Stufe 1  YOLO-Objekterkennung (yolo11n): findet Würfel und Münze im Bild
    Stufe 2  Klassifizierer (yolo11n-cls): liest Augenzahl bzw. Kopf/Zahl aus
             dem Graustufen-Ausschnitt

Die fertigen Modelle landen in modelle/stufe1.pt und modelle/stufe2.pt,
die Trainingsverläufe (Kurven, Beispielbilder) in runs/.

Aufruf:
    python trainieren.py              voll (Stufe 1: 100, Stufe 2: 50 Epochen)
    python trainieren.py --probe      schneller Probelauf (20 / 15 Epochen), für den Laptop
    python trainieren.py --stufe 2    nur eine Stufe
Mit NVIDIA-Grafikkarte wird sie automatisch benutzt, sonst läuft es auf der CPU
(dann dauert das volle Training mehrere Stunden: besser auf dem Gaming-PC).
"""
from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

ORDNER = Path(__file__).resolve().parent
DATEN = ORDNER / "datensaetze"
MODELLE = ORDNER / "modelle"
LAEUFE = ORDNER / "runs"
BILDENDUNGEN = {".jpg", ".jpeg", ".png"}


def bilder_in(ordner: Path) -> list[Path]:
    return [p for p in ordner.rglob("*") if p.suffix.lower() in BILDENDUNGEN] if ordner.exists() else []


def geraet() -> str:
    import torch
    if torch.cuda.is_available():
        print(f"Grafikkarte: {torch.cuda.get_device_name(0)}")
        return "0"
    print("Keine NVIDIA-Grafikkarte gefunden, Training auf der CPU (langsam).")
    return "cpu"


def sichere_modell(lauf: Path, ziel: Path) -> bool:
    best = lauf / "weights" / "best.pt"
    if not best.exists():
        print(f"FEHLER: {best} fehlt, das Training ist wohl abgebrochen.")
        return False
    MODELLE.mkdir(exist_ok=True)
    shutil.copy2(best, ziel)
    print(f"Modell gespeichert: {ziel}")
    return True


def stufe1(epochen: int, dev: str) -> bool:
    from ultralytics import YOLO

    yaml = DATEN / "stufe1" / "data.yaml"
    if not yaml.exists() or not bilder_in(DATEN / "stufe1" / "images" / "train"):
        print("Stufe 1: Datensatz fehlt. Zuerst 'Datensätze erzeugen' ausführen.")
        return False
    if not bilder_in(DATEN / "stufe1" / "images" / "val"):
        print("Stufe 1: val ist leer, mehr Teachbilder nötig.")
        return False
    print(f"\n=== Stufe 1: Würfel und Münze finden ({epochen} Epochen) ===")
    modell = YOLO("yolo11n.pt")
    modell.train(data=str(yaml), imgsz=640, epochs=epochen, patience=20, fliplr=0.0,
                 device=dev, workers=2, project=str(LAEUFE), name="stufe1", exist_ok=True, plots=True)
    if not sichere_modell(LAEUFE / "stufe1", MODELLE / "stufe1.pt"):
        return False
    if bilder_in(DATEN / "stufe1" / "images" / "test"):
        print("\nStufe 1 auf den Testbildern:")
        m = YOLO(str(MODELLE / "stufe1.pt")).val(data=str(yaml), split="test", device=dev,
                                                   project=str(LAEUFE), name="stufe1_test", exist_ok=True)
        print(f"Testbilder: mAP50 = {m.box.map50:.3f} (1.0 = perfekt)")
    return True


def ergaenze_val(stufe2: Path) -> None:
    """Der Klassifizierer braucht in val jede Klasse (sonst verrutschen die Nummern).
    Fehlt eine, wird ein Trainingsbild davon kopiert und gewarnt."""
    for klasse in sorted(p.name for p in (stufe2 / "train").iterdir() if p.is_dir()):
        val = stufe2 / "val" / klasse
        if not bilder_in(val):
            beispiele = bilder_in(stufe2 / "train" / klasse)
            if beispiele:
                val.mkdir(parents=True, exist_ok=True)
                shutil.copy2(beispiele[0], val / beispiele[0].name)
                print(f"WARNUNG: val hatte kein Bild für '{klasse}', ein Trainingsbild wurde kopiert.")


def stufe2(epochen: int, dev: str) -> bool:
    from ultralytics import YOLO

    ordner = DATEN / "stufe2"
    if not bilder_in(ordner / "train"):
        print("Stufe 2: Datensatz fehlt. Zuerst 'Datensätze erzeugen' ausführen.")
        return False
    ergaenze_val(ordner)
    # test wird hier nicht an Ultralytics gegeben (fehlende Klassen würden die Nummern
    # verschieben), sondern unten selbst ausgewertet.
    print(f"\n=== Stufe 2: Augenzahl und Kopf/Zahl lesen ({epochen} Epochen) ===")
    trainordner = LAEUFE / "_stufe2_daten"
    if trainordner.exists():
        shutil.rmtree(trainordner)
    shutil.copytree(ordner / "train", trainordner / "train")
    shutil.copytree(ordner / "val", trainordner / "val")
    modell = YOLO("yolo11n-cls.pt")
    modell.train(data=str(trainordner), imgsz=96, epochs=epochen, patience=20, fliplr=0.0,
                 device=dev, workers=2, project=str(LAEUFE), name="stufe2", exist_ok=True, plots=True)
    if not sichere_modell(LAEUFE / "stufe2", MODELLE / "stufe2.pt"):
        return False
    testbilder = bilder_in(ordner / "test")
    if testbilder:
        m = YOLO(str(MODELLE / "stufe2.pt"))
        richtig = 0
        fehler = []
        for p in testbilder:
            erg = m(str(p), verbose=False)[0]
            vorhersage = erg.names[int(erg.probs.top1)]
            if vorhersage == p.parent.name:
                richtig += 1
            else:
                fehler.append(f"  {p.parent.name}/{p.name}: erkannt als {vorhersage}")
        print(f"\nStufe 2 auf den Testbildern: {richtig} von {len(testbilder)} richtig "
              f"({100 * richtig / len(testbilder):.0f} %)")
        for z in fehler:
            print(z)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stufe", choices=["1", "2", "beide"], default="beide")
    ap.add_argument("--probe", action="store_true", help="schneller Probelauf mit wenigen Epochen")
    ap.add_argument("--epochen1", type=int, help="Epochen Stufe 1 (Standard 100, Probe 20)")
    ap.add_argument("--epochen2", type=int, help="Epochen Stufe 2 (Standard 50, Probe 15)")
    args = ap.parse_args()
    e1 = args.epochen1 or (20 if args.probe else 100)
    e2 = args.epochen2 or (15 if args.probe else 50)

    dev = geraet()
    start = time.time()
    ok = True
    if args.stufe in ("2", "beide"):        # Stufe 2 zuerst: geht schnell, Fehler fallen früh auf
        ok = stufe2(e2, dev) and ok
    if args.stufe in ("1", "beide"):
        ok = stufe1(e1, dev) and ok
    minuten = (time.time() - start) / 60
    print(f"\nFertig nach {minuten:.0f} Minuten." if ok else f"\nMit Fehlern beendet nach {minuten:.0f} Minuten.")
    if ok:
        print("Live testen: starten.py -> 'Live-Erkennung'. Kurven und Beispiele: Ordner runs/.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
