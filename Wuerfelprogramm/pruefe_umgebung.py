"""Prüft, ob die Softwareumgebung für den Würfel-Zähler vollständig ist.

Aufruf (in der aktivierten .venv):
    python pruefe_umgebung.py              nur Pakete prüfen
    python pruefe_umgebung.py --kamera 0   zusätzlich Kamera 0 anzeigen (Taste q beendet)
    python pruefe_umgebung.py --yolo 0     Kamera 0 mit vortrainiertem YOLO-Modell testen
Statt der Kameranummer geht auch eine URL, z. B. vom Handy (DroidCam / IP Webcam).
"""
import argparse
import platform
import sys
import time

OK, FEHLT = "OK   ", "FEHLT"


def pruefe_pakete() -> bool:
    alles_ok = True
    print(f"Python      {platform.python_version()}  ({sys.executable})")
    if sys.version_info < (3, 10):
        print("             Hinweis: Python 3.11 empfohlen")

    try:
        import torch
        cuda = torch.cuda.is_available()
        gpu = torch.cuda.get_device_name(0) if cuda else "keine (Training läuft auf der CPU)"
        print(f"{OK} torch {torch.__version__}, Grafikkarte: {gpu}")
    except ImportError:
        print(f"{FEHLT} torch  -> siehe EINRICHTUNG.md, Schritt 4")
        alles_ok = False

    for name, modul in [("ultralytics", "ultralytics"), ("opencv-python", "cv2"),
                        ("albumentations", "albumentations"), ("numpy", "numpy")]:
        try:
            m = __import__(modul)
            print(f"{OK} {name} {getattr(m, '__version__', '')}")
        except ImportError:
            print(f"{FEHLT} {name}  -> pip install -r requirements.txt")
            alles_ok = False

    # opencv-python-headless (kommt manchmal mit albumentations) hat keine Fenster-Funktionen
    try:
        from importlib.metadata import version
        version("opencv-python-headless")
        print(f"{FEHLT} opencv-python-headless ist installiert: Kamerafenster funktionieren dann nicht.")
        print("             -> einrichten.bat erneut ausführen (behebt das automatisch)")
        alles_ok = False
    except Exception:
        pass
    return alles_ok


def quelle(wert: str):
    return int(wert) if wert.isdigit() else wert


def zeige_kamera(src, mit_yolo: bool) -> None:
    import cv2
    modell = None
    if mit_yolo:
        from ultralytics import YOLO
        modell = YOLO("yolo11n.pt")  # wird beim ersten Mal automatisch heruntergeladen

    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"Kamera {src!r} lässt sich nicht öffnen. Andere Nummer (0, 1, 2) oder URL versuchen.")
        return
    print("Kamerafenster offen, Taste q beendet.")
    t0, bilder, fps = time.time(), 0, 0.0
    while True:
        ok, frame = cap.read()
        if not ok:
            print("Kein Bild von der Kamera.")
            break
        if modell is not None:
            frame = modell(frame, verbose=False)[0].plot()
        bilder += 1
        if time.time() - t0 >= 1:
            fps, bilder, t0 = bilder / (time.time() - t0), 0, time.time()
        h, w = frame.shape[:2]
        cv2.putText(frame, f"{w}x{h}  {fps:.1f} FPS", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow("Wuerfel-Zaehler: Kameratest", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kamera", help="Kameranummer oder URL anzeigen")
    ap.add_argument("--yolo", help="Kameranummer oder URL mit YOLO-Erkennung testen")
    args = ap.parse_args()

    ok = pruefe_pakete()
    if not ok:
        sys.exit(1)
    if args.kamera is not None:
        zeige_kamera(quelle(args.kamera), mit_yolo=False)
    if args.yolo is not None:
        zeige_kamera(quelle(args.yolo), mit_yolo=True)
    print("Umgebung bereit.")
