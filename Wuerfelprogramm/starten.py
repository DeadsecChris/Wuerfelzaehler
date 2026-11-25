"""Startdatei für den Würfel-Zähler.

Startet die Programmteile immer mit der richtigen Umgebung (.venv) und aus dem
richtigen Ordner. Sie richtet nichts ein: Fehlt etwas, sagt sie, was zu tun ist
(meist: einrichten.bat ausführen).

Aufruf:
    Doppelklick auf starten.py             Menü
    python starten.py                      Menü
    python starten.py datensaetze          direkt einen Punkt starten
                     pruefen | kamera | fotos | labelstudio | datensaetze | trainieren | live
"""
import os
import subprocess
import sys
from pathlib import Path

ORDNER = Path(__file__).resolve().parent
WINDOWS = os.name == "nt"
VENV_PY = ORDNER / ".venv" / ("Scripts/python.exe" if WINDOWS else "bin/python")
LABELSTUDIO = Path.home() / "labelstudio-venv" / ("Scripts/label-studio.exe" if WINDOWS else "bin/label-studio")


def in_venv() -> bool:
    try:
        return Path(sys.prefix).resolve() == (ORDNER / ".venv").resolve()
    except OSError:
        return False


def warte() -> None:
    try:
        input("\nEnter drücken ...")
    except EOFError:
        pass


def starte(*befehl) -> int:
    print("\n> " + " ".join(str(t) for t in befehl) + "\n")
    try:
        return subprocess.call([str(t) for t in befehl], cwd=ORDNER)
    except KeyboardInterrupt:
        return 130


def pruefen() -> int:
    return starte(sys.executable, "pruefe_umgebung.py")


def kamera() -> int:
    quelle = input("Kamera-Nummer oder URL [0]: ").strip() or "0"
    return starte(sys.executable, "pruefe_umgebung.py", "--yolo", quelle)


def fotos() -> int:
    quelle = input("Kamera-Nummer oder URL [0]: ").strip() or "0"
    return starte(sys.executable, "fotos.py", "--kamera", quelle)


def datensaetze() -> int:
    code = starte(sys.executable, "datensaetze.py")
    bericht = ORDNER / "datensaetze" / "bericht.txt"
    if bericht.exists():
        print(f"\nBericht: {bericht}")
    return code


def trainieren() -> int:
    print("p = Probelauf beide Stufen (auf dem Laptop ca. 45 Min.)")
    print("2 = nur Stufe 2 (Augenzahl, Kopf/Zahl), volle Epochen, auf dem Laptop wenige Minuten")
    print("v = volles Training beide Stufen (auf dem Laptop mehrere Stunden, besser Gaming-PC)")
    art = input("Auswahl [p]: ").strip().lower() or "p"
    if art == "2":
        return starte(sys.executable, "trainieren.py", "--stufe", "2")
    return starte(sys.executable, "trainieren.py", *(["--probe"] if art != "v" else []))


def live() -> int:
    quelle = input("Kamera-Nummer oder URL [0]: ").strip() or "0"
    return starte(sys.executable, "live.py", "--kamera", quelle)


def labelstudio() -> int:
    if not LABELSTUDIO.exists():
        print("Label Studio ist nicht installiert. Bitte einrichten.bat ausführen und Label Studio mit 'j' wählen.")
        return 1
    print("Label Studio läuft unter http://localhost:8080 (Beenden mit Strg+C).")
    return starte(LABELSTUDIO, "start")


PUNKTE = {
    "1": ("pruefen", "Umgebung prüfen", pruefen),
    "2": ("kamera", "Kameratest mit YOLO", kamera),
    "3": ("fotos", "Fotos aufnehmen (in den OneDrive-Bilderordner)", fotos),
    "4": ("labelstudio", "Label Studio starten", labelstudio),
    "5": ("datensaetze", "Datensätze aus den Fotos erzeugen", datensaetze),
    "6": ("trainieren", "Modelle trainieren", trainieren),
    "7": ("live", "Live-Erkennung mit Kamera", live),
}


def menue() -> None:
    while True:
        print("\n=== Würfel-Zähler ===")
        for nr, (_, text, _) in PUNKTE.items():
            print(f"  {nr}  {text}")
        print("  q  Beenden")
        wahl = input("Auswahl: ").strip().lower()
        if wahl in ("q", "0", ""):
            return
        if wahl not in PUNKTE:
            print("Unbekannte Auswahl.")
            continue
        code = PUNKTE[wahl][2]()
        if code not in (0, 130):
            print(f"\nBeendet mit Fehlercode {code}. Die Meldungen oben zeigen den Grund.")
        warte()


def main() -> int:
    # 1. Immer mit der Python-Umgebung des Projekts laufen
    if not in_venv():
        if not VENV_PY.exists():
            print("Die Umgebung .venv fehlt. Bitte zuerst einrichten.bat ausführen (richtet alles ein).")
            warte()
            return 1
        return subprocess.call([str(VENV_PY), str(Path(__file__).resolve()), *sys.argv[1:]], cwd=ORDNER)

    os.chdir(ORDNER)
    # 2. Direktaufruf: python starten.py datensaetze
    if len(sys.argv) > 1:
        namen = {name: f for name, _, f in PUNKTE.values()}
        f = namen.get(sys.argv[1].lower())
        if f is None:
            print(f"Unbekannt: {sys.argv[1]}. Möglich: {', '.join(namen)}")
            return 1
        return f()
    # 3. Sonst Menü
    menue()
    return 0


if __name__ == "__main__":
    sys.exit(main())
