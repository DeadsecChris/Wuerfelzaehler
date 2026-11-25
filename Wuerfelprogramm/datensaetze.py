"""Erzeugt aus den gelabelten Fotos die Datensätze für beide Stufen.

Quelle (OneDrive, Standard: C:\\Users\\chris\\OneDrive\\Bilder_wuerfelzaehler):
    Teachbilder/einzel/<klasse>/bild.jpg   Einzelaufnahmen, Klasse über den Ordner
    Teachbilder/wurf/bild.jpg              ganze Würfe
    Testbilder/...                         gleicher Aufbau, nur für den Test
Einzelaufnahmen brauchen KEIN Label: Die Klasse kommt aus dem Ordnernamen, den
Rahmen um das Objekt sucht das Skript selbst (Objekt hebt sich vom Untergrund ab).
Zur Kontrolle landet jedes Bild verkleinert mit eingezeichnetem Rahmen in
datensaetze/kontrolle/. Passt ein Rahmen nicht, das Bild löschen oder neu
fotografieren (oder in Label Studio labeln, ein vorhandenes Label hat Vorrang).

Wurfbilder (mehrere Objekte) brauchen eine YOLO-Label-Datei mit gleichem Namen
(bild.txt), entweder direkt neben dem Bild oder in einem Unterordner "labels"
daneben (so exportiert es Label Studio). Liegt dort eine classes.txt, werden die
Klassen über ihre Namen zugeordnet, sonst gilt die Reihenfolge aus dem
Lastenheft (KLASSEN unten). Wurfbilder ohne Label werden übersprungen.

Ergebnis (Standard: Wuerfelprogramm/datensaetze):
    stufe1/images/{train,val,test}, stufe1/labels/..., stufe1/data.yaml
        Objekterkennung mit 2 Klassen: wuerfel, muenze
        train enthält zusätzlich je Bild N Varianten (Data Augmentation)
    stufe2/{train,val,test}/{augen_1..augen_6,kopf,zahl}/*.jpg
        Graustufen-Ausschnitte jedes Objekts für den Klassifizierer
    kontrolle/<klasse>/*.jpg   automatisch gefundene Rahmen zum Nachsehen
    bericht.txt   Anzahl je Klasse und Datensatz, Warnungen

Teach wird in train und val aufgeteilt (val nur zur Kontrolle während des
Trainings, Anteil einstellbar). Testbilder gehen ausschließlich in test.

Aufruf (in der aktivierten .venv, im Ordner Wuerfelprogramm):
    python datensaetze.py
    python datensaetze.py --quelle D:\\Bilder --varianten 3 --val-anteil 0.15
"""
from __future__ import annotations

import argparse
import random
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

# Label-Klassen laut Lastenheft (ID = Position)
KLASSEN = ["wuerfel_1", "wuerfel_2", "wuerfel_3", "wuerfel_4", "wuerfel_5", "wuerfel_6",
           "muenze_kopf", "muenze_zahl"]
STUFE1 = ["wuerfel", "muenze"]
STUFE2 = {"wuerfel_1": "augen_1", "wuerfel_2": "augen_2", "wuerfel_3": "augen_3",
          "wuerfel_4": "augen_4", "wuerfel_5": "augen_5", "wuerfel_6": "augen_6",
          "muenze_kopf": "kopf", "muenze_zahl": "zahl"}
BILDENDUNGEN = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
STANDARD_QUELLE = Path(r"C:\Users\chris\OneDrive\Bilder_wuerfelzaehler")


@dataclass
class Objekt:
    klasse: str                     # Label-Klasse, z. B. "wuerfel_4"
    box: tuple[float, float, float, float]  # YOLO: x_mitte, y_mitte, breite, hoehe (0..1)


@dataclass
class Bild:
    pfad: Path
    art: str                        # "teach" oder "test"
    objekte: list[Objekt] = field(default_factory=list)
    auto_klasse: str | None = None  # Einzelaufnahme ohne Label: Rahmen wird automatisch gesucht


class Bericht:
    def __init__(self) -> None:
        self.zeilen: list[str] = []
        self.warnungen: list[str] = []

    def info(self, text: str) -> None:
        print(text)
        self.zeilen.append(text)

    def warnung(self, text: str) -> None:
        print("WARNUNG:", text)
        self.warnungen.append(text)

    def speichern(self, pfad: Path) -> None:
        text = "\n".join(self.zeilen)
        if self.warnungen:
            text += "\n\nWarnungen:\n" + "\n".join("- " + w for w in self.warnungen)
        pfad.write_text(text + "\n", encoding="utf-8")


# ---------------------------------------------------------------- Einlesen
def finde_label(bildpfad: Path) -> Path | None:
    for kandidat in (bildpfad.with_suffix(".txt"), bildpfad.parent / "labels" / (bildpfad.stem + ".txt")):
        if kandidat.exists():
            return kandidat
    return None


def finde_klassenliste(labelpfad: Path, wurzel: Path) -> list[str]:
    """Sucht classes.txt neben dem Label oder weiter oben (bis zur Quelle)."""
    ordner = labelpfad.parent
    while True:
        datei = ordner / "classes.txt"
        if datei.exists():
            namen = [z.strip() for z in datei.read_text(encoding="utf-8").splitlines() if z.strip()]
            if namen:
                return namen
        if ordner == wurzel or ordner.parent == ordner:
            return KLASSEN
        ordner = ordner.parent


def lies_label(labelpfad: Path, namen: list[str], bericht: Bericht) -> list[Objekt]:
    objekte = []
    for nr, zeile in enumerate(labelpfad.read_text(encoding="utf-8").splitlines(), 1):
        teile = zeile.split()
        if not teile:
            continue
        if len(teile) != 5:
            bericht.warnung(f"{labelpfad.name} Zeile {nr}: erwartet 5 Werte, gefunden {len(teile)}")
            continue
        try:
            kid = int(float(teile[0]))
            box = tuple(float(t) for t in teile[1:])
        except ValueError:
            bericht.warnung(f"{labelpfad.name} Zeile {nr}: keine Zahlen")
            continue
        if not 0 <= kid < len(namen) or namen[kid] not in STUFE2:
            bericht.warnung(f"{labelpfad.name} Zeile {nr}: unbekannte Klasse {kid}")
            continue
        objekte.append(Objekt(namen[kid], box))
    return objekte


def sammle_bilder(quelle: Path, bericht: Bericht) -> list[Bild]:
    bilder = []
    for ordnername, art in (("Teachbilder", "teach"), ("Testbilder", "test")):
        wurzel = quelle / ordnername
        if not wurzel.exists():
            bericht.warnung(f"Ordner fehlt: {wurzel}")
            continue
        for pfad in sorted(wurzel.rglob("*")):
            if pfad.suffix.lower() not in BILDENDUNGEN or "labels" in pfad.parts:
                continue
            ordner_klasse = pfad.parent.name if pfad.parent.parent.name == "einzel" else None
            labelpfad = finde_label(pfad)
            if labelpfad is None and ordner_klasse:
                if ordner_klasse not in STUFE2:
                    bericht.warnung(f"Unbekannter Klassenordner: {pfad.parent.relative_to(quelle)}")
                    continue
                bilder.append(Bild(pfad, art, auto_klasse=ordner_klasse))
                continue
            if labelpfad is None:
                bericht.warnung(f"Kein Label: {pfad.relative_to(quelle)} (übersprungen)")
                continue
            namen = finde_klassenliste(labelpfad, quelle)
            objekte = lies_label(labelpfad, namen, bericht)
            if not objekte:
                bericht.warnung(f"Leeres Label: {pfad.relative_to(quelle)} (übersprungen)")
                continue
            if ordner_klasse:
                if ordner_klasse not in STUFE2:
                    bericht.warnung(f"Unbekannter Klassenordner: {pfad.parent.relative_to(quelle)}")
                elif len(objekte) != 1:
                    bericht.warnung(f"Einzelaufnahme mit {len(objekte)} Objekten: {pfad.relative_to(quelle)}")
                elif objekte[0].klasse != ordner_klasse:
                    bericht.warnung(f"Label '{objekte[0].klasse}' passt nicht zum Ordner '{ordner_klasse}': "
                                    f"{pfad.relative_to(quelle)} (Ordner gilt)")
                    objekte[0].klasse = ordner_klasse
            bilder.append(Bild(pfad, art, objekte))
    return bilder


# ---------------------------------------------------------------- Ausgabe
def lies_bild(pfad: Path) -> np.ndarray | None:
    # imdecode statt imread, damit Umlaute im Pfad (Windows) funktionieren
    daten = np.fromfile(str(pfad), dtype=np.uint8)
    return cv2.imdecode(daten, cv2.IMREAD_COLOR) if daten.size else None


def verkleinere(bild: np.ndarray, max_seite: int) -> np.ndarray:
    """Handyfotos (z. B. 4000x3000) verkleinern, YOLO trainiert ohnehin mit 640."""
    h, w = bild.shape[:2]
    f = max_seite / max(h, w)
    if max_seite <= 0 or f >= 1:
        return bild
    return cv2.resize(bild, (round(w * f), round(h * f)), interpolation=cv2.INTER_AREA)


def finde_rahmen(bild: np.ndarray) -> tuple[float, float, float, float] | None:
    """Sucht das eine Objekt (Würfel oder Münze) auf einer Einzelaufnahme.

    Der Untergrund wird pro Bildstelle geschätzt (großer Medianfilter, so stören
    Lichtverläufe nicht). Als Objekt zählt, was sich deutlich in der Farbe
    unterscheidet, sehr viel dunkler ist (schwarzer Würfel, Augen) oder klare
    Kanten hat. Schatten sind nur etwas dunkler und gleich gefärbt und fallen
    deshalb heraus. Flächen am Bildrand (Tischkante, angeschnittene Gegenstände)
    werden ignoriert. Ergebnis: Rahmen im YOLO-Format (0..1) oder None.
    """
    h0, w0 = bild.shape[:2]
    f = 600 / max(h0, w0)
    klein = cv2.resize(bild, (max(1, round(w0 * f)), max(1, round(h0 * f))), interpolation=cv2.INTER_AREA)
    klein = cv2.GaussianBlur(klein, (3, 3), 0)
    h, w = klein.shape[:2]
    lab = cv2.cvtColor(klein, cv2.COLOR_BGR2LAB)

    # Untergrund je Bildstelle: Median über ein großes Fenster (Objekte sind klein)
    k = (min(h, w) // 3) | 1
    grund = cv2.merge([cv2.medianBlur(c, k) for c in cv2.split(lab)]).astype(np.float32)
    lab_f = lab.astype(np.float32)
    hell = lab_f[..., 0]
    hell_grund = np.maximum(grund[..., 0], 1)
    farbe = np.linalg.norm(lab_f[..., 1:] - grund[..., 1:], axis=2)

    maske = ((farbe > 12) | (hell < 0.5 * hell_grund) | (hell > hell_grund + 60)).astype(np.uint8) * 255
    kanten = cv2.Canny(cv2.cvtColor(klein, cv2.COLOR_BGR2GRAY), 80, 200)
    maske = cv2.bitwise_or(maske, cv2.dilate(kanten, np.ones((3, 3), np.uint8)))
    maske = cv2.morphologyEx(maske, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    maske = cv2.morphologyEx(maske, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    anzahl, _, werte, _ = cv2.connectedComponentsWithStats(maske)
    rand = 3
    kandidaten = []
    for i in range(1, anzahl):
        x, y, bw, bh, flaeche = werte[i]
        if flaeche < 0.0003 * h * w:
            continue                               # Staub, Rauschen
        if x <= rand or y <= rand or x + bw >= w - rand or y + bh >= h - rand:
            continue                               # berührt den Bildrand
        kandidaten.append((int(flaeche), int(x), int(y), int(bw), int(bh)))
    if not kandidaten:
        return None
    kandidaten.sort(reverse=True)
    _, x1, y1, bw, bh = kandidaten[0]
    x2, y2 = x1 + bw, y1 + bh
    # nahe Teile dazunehmen (z. B. einzelne Augen eines dunklen Würfels)
    geaendert = True
    while geaendert:
        geaendert = False
        abstand = 0.3 * max(x2 - x1, y2 - y1)
        for fl, x, y, bw, bh in kandidaten[1:]:
            if fl < 0.05 * kandidaten[0][0]:
                continue
            if x >= x1 and y >= y1 and x + bw <= x2 and y + bh <= y2:
                continue
            if x - abstand <= x2 and x + bw + abstand >= x1 and y - abstand <= y2 and y + bh + abstand >= y1:
                x1, y1, x2, y2 = min(x1, x), min(y1, y), max(x2, x + bw), max(y2, y + bh)
                geaendert = True
    anteil = (x2 - x1) * (y2 - y1) / (w * h)
    if anteil > 0.5:
        return None
    return ((x1 + x2) / 2 / w, (y1 + y2) / 2 / h, (x2 - x1) / w, (y2 - y1) / h)


def kontrollbild(bild: np.ndarray, box) -> np.ndarray:
    k = verkleinere(bild, 480).copy()
    h, w = k.shape[:2]
    xm, ym, bw, bh = box
    p1 = (round((xm - bw / 2) * w), round((ym - bh / 2) * h))
    p2 = (round((xm + bw / 2) * w), round((ym + bh / 2) * h))
    cv2.rectangle(k, p1, p2, (0, 255, 0), 2)
    return k


def schreib_bild(pfad: Path, bild: np.ndarray) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    ok, puffer = cv2.imencode(".jpg", bild, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not ok:
        raise RuntimeError(f"Bild konnte nicht gespeichert werden: {pfad}")
    puffer.tofile(str(pfad))


def stufe1_klasse(label_klasse: str) -> int:
    return 0 if label_klasse.startswith("wuerfel") else 1


def schreib_stufe1(ziel: Path, split: str, name: str, bild: np.ndarray, objekte: list[Objekt]) -> None:
    schreib_bild(ziel / "images" / split / f"{name}.jpg", bild)
    labeldatei = ziel / "labels" / split / f"{name}.txt"
    labeldatei.parent.mkdir(parents=True, exist_ok=True)
    labeldatei.write_text("".join(
        f"{stufe1_klasse(o.klasse)} {o.box[0]:.6f} {o.box[1]:.6f} {o.box[2]:.6f} {o.box[3]:.6f}\n"
        for o in objekte), encoding="utf-8")


def ausschnitt(bild: np.ndarray, box, rand: float) -> np.ndarray | None:
    h, w = bild.shape[:2]
    xm, ym, bw, bh = box
    seite = max(bw * w, bh * h) * (1 + 2 * rand)       # quadratisch, mit Rand
    x1, y1 = int(round(xm * w - seite / 2)), int(round(ym * h - seite / 2))
    x2, y2 = int(round(xm * w + seite / 2)), int(round(ym * h + seite / 2))
    x1c, y1c, x2c, y2c = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
    if x2c - x1c < 8 or y2c - y1c < 8:
        return None
    teil = bild[y1c:y2c, x1c:x2c]
    # am Bildrand mit Randpixeln auffüllen, damit der Ausschnitt quadratisch bleibt
    teil = cv2.copyMakeBorder(teil, y1c - y1, y2 - y2c, x1c - x1, x2 - x2c, cv2.BORDER_REPLICATE)
    return cv2.cvtColor(teil, cv2.COLOR_BGR2GRAY)


def baue_augmentierung(seed: int):
    import albumentations as A

    verfahren = [
        A.Affine(rotate=(-180, 180), scale=(0.8, 1.2), border_mode=cv2.BORDER_CONSTANT, p=1),
        A.RandomBrightnessContrast(brightness_limit=0.25, contrast_limit=0.2, p=1),
        A.HueSaturationValue(hue_shift_limit=90, sat_shift_limit=30, val_shift_limit=0, p=1),
        A.ToGray(p=1),
        A.GaussNoise(std_range=(0.02, 0.06), p=1),
        A.Blur(blur_limit=(3, 5), p=1),
    ]
    bbox = A.BboxParams(format="yolo", label_fields=["klassen"], min_visibility=0.9, clip=True)
    # Jede Variante kombiniert zufällig 2 bis 3 Verfahren. Kein Spiegeln (Münze!).
    pipelines = [A.Compose([A.SomeOf(verfahren, n=n, replace=False, p=1)], bbox_params=bbox, seed=seed + n)
                 for n in (2, 3)]
    return pipelines


def augmentiere(pipelines, rng: random.Random, bild: np.ndarray, objekte: list[Objekt]):
    boxen = [o.box for o in objekte]
    klassen = [o.klasse for o in objekte]
    for _ in range(10):                      # bis zu 10 Versuche, damit kein Objekt verloren geht
        ergebnis = rng.choice(pipelines)(image=bild, bboxes=boxen, klassen=klassen)
        if len(ergebnis["bboxes"]) == len(objekte):
            return ergebnis["image"], [Objekt(k, tuple(float(v) for v in b))
                                       for k, b in zip(ergebnis["klassen"], ergebnis["bboxes"])]
    return None, None


# ---------------------------------------------------------------- Hauptablauf
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quelle", type=Path, default=STANDARD_QUELLE, help="Ordner mit Teachbilder/ und Testbilder/")
    ap.add_argument("--ziel", type=Path, default=Path(__file__).resolve().parent / "datensaetze")
    ap.add_argument("--val-anteil", type=float, default=0.15, help="Anteil der Teachbilder für val (Standard 0.15)")
    ap.add_argument("--varianten", type=int, default=3, help="Varianten je Trainingsbild (0 = keine)")
    ap.add_argument("--rand", type=float, default=0.1, help="Rand um Ausschnitte für Stufe 2 (Standard 10 %%)")
    ap.add_argument("--max-seite", type=int, default=1280,
                    help="lange Bildseite für Stufe 1 begrenzen (Standard 1280, 0 = nicht verkleinern)")
    ap.add_argument("--seed", type=int, default=42, help="Zufallszahl für reproduzierbare Aufteilung")
    args = ap.parse_args()

    if not args.quelle.exists():
        print(f"Quelle nicht gefunden: {args.quelle}\nMit --quelle den Bilderordner angeben.")
        return 1

    bericht = Bericht()
    bericht.info(f"Quelle: {args.quelle}")
    bericht.info(f"Ziel:   {args.ziel}")
    bilder = sammle_bilder(args.quelle, bericht)
    if not bilder:
        bericht.warnung("Keine Bilder gefunden (Einzelaufnahmen in Teachbilder/einzel/<klasse>/ ablegen).")
        args.ziel.mkdir(parents=True, exist_ok=True)
        bericht.speichern(args.ziel / "bericht.txt")
        return 1

    # Aufteilung: Teach → train/val (zufällig, aber reproduzierbar), Test → test
    rng = random.Random(args.seed)
    teach = [b for b in bilder if b.art == "teach"]
    rng.shuffle(teach)
    n_val = round(len(teach) * args.val_anteil)
    split_von = {id(b): "val" for b in teach[:n_val]}
    split_von.update({id(b): "train" for b in teach[n_val:]})
    split_von.update({id(b): "test" for b in bilder if b.art == "test"})

    # Ziel neu anlegen, damit keine alten Bilder in falschen Datensätzen bleiben
    if args.ziel.exists():
        shutil.rmtree(args.ziel)
    stufe1, stufe2 = args.ziel / "stufe1", args.ziel / "stufe2"

    pipelines = baue_augmentierung(args.seed) if args.varianten > 0 else None
    zaehler1: dict[str, Counter] = defaultdict(Counter)
    zaehler2: dict[str, Counter] = defaultdict(Counter)
    namen_vergeben: set[str] = set()
    zaehler_auto: Counter = Counter()
    anzahl: Counter = Counter()             # tatsächlich geschriebene Originale je split

    for bild in bilder:
        split = split_von[id(bild)]
        daten = lies_bild(bild.pfad)
        if daten is None:
            bericht.warnung(f"Bild nicht lesbar: {bild.pfad}")
            continue
        name = bild.pfad.stem
        while name in namen_vergeben:            # gleiche Dateinamen in verschiedenen Ordnern
            name += "_x"
        namen_vergeben.add(name)

        if bild.auto_klasse:
            box = finde_rahmen(daten)
            if box is None:
                bericht.warnung(f"Kein Objekt gefunden: {bild.pfad.relative_to(args.quelle)} (übersprungen)")
                zaehler_auto["fehlgeschlagen"] += 1
                continue
            bild.objekte = [Objekt(bild.auto_klasse, box)]
            schreib_bild(args.ziel / "kontrolle" / bild.auto_klasse / f"{name}.jpg", kontrollbild(daten, box))
            zaehler_auto["gefunden"] += 1

        # Ausschnitte für Stufe 2 aus dem Original (volle Auflösung), Stufe 1 verkleinert
        original = daten
        daten = verkleinere(daten, args.max_seite)
        schreib_stufe1(stufe1, split, name, daten, bild.objekte)
        anzahl[split] += 1
        for o in bild.objekte:
            zaehler1[split][STUFE1[stufe1_klasse(o.klasse)]] += 1
        for i, o in enumerate(bild.objekte, 1):
            teil = ausschnitt(original, o.box, args.rand)
            if teil is None:
                bericht.warnung(f"Ausschnitt zu klein: {bild.pfad.name}, Objekt {i}")
                continue
            schreib_bild(stufe2 / split / STUFE2[o.klasse] / f"{name}_obj{i}.jpg", teil)
            zaehler2[split][STUFE2[o.klasse]] += 1

        if split == "train" and pipelines:
            for v in range(1, args.varianten + 1):
                aug_bild, aug_objekte = augmentiere(pipelines, rng, daten, bild.objekte)
                if aug_bild is None:
                    bericht.warnung(f"Variante {v} von {bild.pfad.name} verworfen (Objekt aus dem Bild gefallen)")
                    continue
                schreib_stufe1(stufe1, split, f"{name}_aug{v}", aug_bild, aug_objekte)
                zaehler1["train (Varianten)"]["bilder"] += 1

    yaml = (f"path: {stufe1.resolve().as_posix()}\n"
            "train: images/train\nval: images/val\ntest: images/test\n"
            "names:\n" + "".join(f"  {i}: {n}\n" for i, n in enumerate(STUFE1)))
    stufe1.mkdir(parents=True, exist_ok=True)
    (stufe1 / "data.yaml").write_text(yaml, encoding="utf-8")

    # Bericht
    bericht.info("")
    bericht.info(f"Originalbilder: train {anzahl['train']}, val {anzahl['val']}, test {anzahl['test']}")
    bericht.info(f"Varianten (nur train): {zaehler1['train (Varianten)']['bilder']}")
    if zaehler_auto:
        bericht.info(f"Einzelaufnahmen ohne Label: Rahmen automatisch gefunden {zaehler_auto['gefunden']}, "
                     f"nicht gefunden {zaehler_auto['fehlgeschlagen']}. Bitte datensaetze/kontrolle/ ansehen.")
    bericht.info("")
    bericht.info("Stufe 1, Objekte je Klasse (Originale):")
    for split in ("train", "val", "test"):
        bericht.info(f"  {split:5s} " + "  ".join(f"{k}: {zaehler1[split][k]}" for k in STUFE1))
    bericht.info("")
    bericht.info("Stufe 2, Ausschnitte je Unterklasse:")
    unterklassen = list(STUFE2.values())
    bericht.info("  " + " " * 6 + "".join(f"{k:>9s}" for k in unterklassen))
    for split in ("train", "val", "test"):
        bericht.info(f"  {split:5s} " + "".join(f"{zaehler2[split][k]:9d}" for k in unterklassen))
    for split in ("train", "val", "test"):
        fehlend = [k for k in unterklassen if zaehler2[split][k] == 0]
        if fehlend and anzahl[split]:
            bericht.warnung(f"In {split} fehlen Beispiele für: {', '.join(fehlend)}")
    if anzahl["val"] == 0:
        bericht.warnung("val ist leer: Für das Training mehr Teachbilder hinzufügen oder --val-anteil erhöhen.")
    if anzahl["test"] == 0:
        bericht.warnung("Keine Testbilder: Die Auswertung braucht Bilder in Testbilder/.")

    bericht.speichern(args.ziel / "bericht.txt")
    print(f"\nFertig. Bericht: {args.ziel / 'bericht.txt'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
