"""Erzeugt Drehbuch_Bilderstellung_Wuerfel-Zaehler.docx im Stil des Lastenhefts.

Nutzt das Lastenheft als Vorlage (Formatvorlagen, Deckblatt, Seitenränder),
ersetzt den Inhalt und legt ein frisches Inhaltsverzeichnis-Feld an.
Aufruf: python scripts/drehbuch_erzeugen.py
"""
import copy
from pathlib import Path

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

ROOT = Path(__file__).resolve().parent.parent
VORLAGE = ROOT / "Lastenheft_Wuerfel-Zaehler.docx"
ZIEL = ROOT / "Drehbuch_Bilderstellung_Wuerfel-Zaehler.docx"

d = docx.Document(VORLAGE)
body = d.element.body
elems = list(body)

# Deckblatt (Absätze 0-8) anpassen
cover = {
    0: "Drehbuch Bilderstellung",
    3: "KI-Anwendung mit Bilderkennung",
    4: "Planung des Bilddatensatzes für die Würfel- und Münzerkennung",
    6: "Christian Maschke, Niklas Bäricke",
    8: "16. November 2026",
}
for i, text in cover.items():
    p = d.paragraphs[i]
    p.runs[0].text = text
    for r in p.runs[1:]:
        r.text = ""

# Alles nach dem Seitenumbruch hinter dem Inhaltsverzeichnis entfernen
sectPr = body.find(qn("w:sectPr"))
for el in elems[13:]:
    if el is not sectPr:
        body.remove(el)

# Inhaltsverzeichnis durch frisches Feld ersetzen
toc_sdt = elems[11]
toc_p = OxmlElement("w:p")
r = OxmlElement("w:r")
fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), "begin"); r.append(fc)
toc_p.append(r)
r = OxmlElement("w:r")
it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = ' TOC \\o "1-2" \\h \\z \\u '
r.append(it); toc_p.append(r)
r = OxmlElement("w:r")
fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), "separate"); r.append(fc)
toc_p.append(r)
body.replace(toc_sdt, toc_p)
TOC_START = toc_p

settings = d.settings.element
uf = OxmlElement("w:updateFields"); uf.set(qn("w:val"), "true")
settings.append(uf)

# Vorlage für Aufzählungsabsätze aus dem Lastenheft
BULLET_PPR = None
src = docx.Document(VORLAGE)
for p in src.paragraphs:
    if p.style.name == "List Paragraph" and p._p.pPr is not None and p._p.pPr.numPr is not None:
        BULLET_PPR = copy.deepcopy(p._p.pPr)
        break


def _append(el):
    sectPr.addprevious(el)


def heading(text, level):
    p = d.add_paragraph(text, style=f"Heading {level}")
    _append(p._p)


def para(text, bold_prefix=None):
    p = d.add_paragraph()
    if bold_prefix:
        p.add_run(bold_prefix).bold = True
    p.add_run(text)
    _append(p._p)


def bullet(text, bold_prefix=None):
    p = d.add_paragraph()
    p._p.insert(0, copy.deepcopy(BULLET_PPR))
    if bold_prefix:
        p.add_run(bold_prefix).bold = True
    p.add_run(text)
    _append(p._p)


def page_break():
    p = d.add_paragraph()
    br = OxmlElement("w:br"); br.set(qn("w:type"), "page")
    r = OxmlElement("w:r"); r.append(br); p._p.append(r)
    _append(p._p)


def _cell_fmt(cell, header=False, bold=False):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        b = OxmlElement(f"w:{side}")
        b.set(qn("w:val"), "single"); b.set(qn("w:sz"), "4"); b.set(qn("w:space"), "0"); b.set(qn("w:color"), "BFBFBF")
        borders.append(b)
    tcPr.append(borders)
    if header:
        shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), "E7EEF7")
        tcPr.append(shd)
    mar = OxmlElement("w:tcMar")
    for side, w in (("top", 30), ("left", 100), ("bottom", 30), ("right", 100)):
        m = OxmlElement(f"w:{side}"); m.set(qn("w:w"), str(w)); m.set(qn("w:type"), "dxa"); mar.append(m)
    tcPr.append(mar)
    for p in cell.paragraphs:
        p.paragraph_format.space_after = Pt(0)
        for r in p.runs:
            r.font.size = Pt(10)
            if header or bold:
                r.bold = True


def table(rows, widths=None, bold_last=False):
    t = d.add_table(rows=len(rows), cols=len(rows[0]))
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j)
            c.text = str(val)
            _cell_fmt(c, header=(i == 0), bold=(bold_last and i == len(rows) - 1))
    # Kopfzeile auf jeder Seite wiederholen
    trPr = t.rows[0]._tr.get_or_add_trPr()
    h = OxmlElement("w:tblHeader"); trPr.append(h)
    if widths:
        total = sum(widths)
        dxa = [int(w / total * 9026) for w in widths]
        t.autofit = False
        grid = t._tbl.tblGrid
        for j, gc in enumerate(grid.findall(qn("w:gridCol"))):
            gc.set(qn("w:w"), str(dxa[j]))
        for row in t.rows:
            for j, w in enumerate(dxa):
                row.cells[j].width = docx.shared.Twips(w)
    _append(t._tbl)
    spacer = d.add_paragraph(); _append(spacer._p)


# ---------------------------------------------------------------- Inhalt
heading("1 Zu erkennende Klassen und Bildmotive", 1)
heading("1.1 Änderung gegenüber dem Lastenheft", 2)
para("Statt drei gleicher Würfel soll das Programm mit möglichst unterschiedlichen Standardwürfeln funktionieren "
     "(beliebige Farbe und Größe, helle oder dunkle Augen). Die Münze bleibt immer dieselbe 1-Euro-Münze. "
     "Damit das gelingt, erkennt die KI in zwei Stufen:")
bullet("Ein Objekterkennungsmodell (YOLO nano) findet jedes Objekt im Bild und unterscheidet nur Würfel und Münze (Oberklasse).", "Stufe 1, Form: ")
bullet("Jedes gefundene Objekt wird ausgeschnitten. Ein Klassifizierer bestimmt im Graustufen-Ausschnitt die Augenzahl bzw. Kopf oder Zahl (Unterklasse). "
       "Für die Augenzahl zählt zusätzlich eine Kontrasterkennung die Augen als zweite Meinung.", "Stufe 2, Wert: ")
para("Für die Bilder heißt das: Es werden mehrere verschiedene Würfel fotografiert, und jeder Würfel muss jede Augenzahl ungefähr gleich oft zeigen. "
     "Sonst lernt die KI die Farbe eines Würfels statt seiner Augen.")

heading("1.2 Klassen", 2)
para("Beim Labeln werden weiterhin die 8 Klassen aus dem Lastenheft vergeben. Ein Skript leitet daraus automatisch die Klassen beider Stufen ab. "
     "Regel: Die Klasse eines Würfels ist die Augenzahl, die oben liegt. Der Rahmen umfasst das ganze Objekt.")
table([
    ["ID", "Label-Klasse", "Bildmotiv", "Stufe 1", "Stufe 2"],
    ["0", "wuerfel_1", "Würfel, oben liegt die 1", "wuerfel", "augen_1"],
    ["1", "wuerfel_2", "Würfel, oben liegt die 2", "wuerfel", "augen_2"],
    ["2", "wuerfel_3", "Würfel, oben liegt die 3", "wuerfel", "augen_3"],
    ["3", "wuerfel_4", "Würfel, oben liegt die 4", "wuerfel", "augen_4"],
    ["4", "wuerfel_5", "Würfel, oben liegt die 5", "wuerfel", "augen_5"],
    ["5", "wuerfel_6", "Würfel, oben liegt die 6", "wuerfel", "augen_6"],
    ["6", "muenze_kopf", "1-Euro-Münze, Bildseite oben", "muenze", "kopf"],
    ["7", "muenze_zahl", "1-Euro-Münze, Wertseite oben (Ziffer 1)", "muenze", "zahl"],
], widths=[25, 80, 200, 60, 60])

heading("1.3 Bildmotive und Material", 2)
bullet("Bisher 3 verschiedene Standardwürfel, bezeichnet als WA, WB und WC (Liste mit Foto im Aufnahmeprotokoll). "
       "Ziel sind mindestens 8 verschiedene Würfel (Farbe, Größe, helle und dunkle Augen, runde und scharfe Kanten).", "Würfel: ")
bullet("Mindestens 2 weitere Würfel (T1, T2) werden nur für die Testbilder verwendet und kommen im Training nie vor. "
       "Damit wird geprüft, ob das Programm auch unbekannte Würfel erkennt.", "Testwürfel: ")
bullet("Immer dieselbe 1-Euro-Münze, Kopf und Zahl ungefähr gleich oft.", "Münze: ")
bullet("Wurffläche mit Rand (Tablett), Untergründe dunkelgrüner Filz, Holztisch und weißes Papier.", "Aufbau: ")
bullet("Webcam fest montiert, senkrecht über der Wurffläche. Dieselbe Kamera wird später im Programm genutzt.", "Kamera: ")
bullet("Etwa jedes zehnte Wurfbild zeigt einen ungültigen Wurf (Würfel auf der Kante, Objekte gestapelt oder halb verdeckt). "
       "Daran wird geprüft, ob das Programm „Bitte neu würfeln“ meldet.", "Ungültige Würfe: ")

heading("2 Planung der Fotoaufnahmen", 1)
heading("2.1 Aufnahmeplan", 2)
table([
    ["Nr.", "Art", "Perspektive", "Abstand", "Hintergrund", "Licht", "Bilder"],
    ["E1", "Einzel", "senkrecht von oben", "ca. 30 cm", "dunkelgrüner Filz", "Tageslicht am Fenster", "40"],
    ["E2", "Einzel", "schräg, ca. 60–70°", "ca. 40 cm", "Holztisch", "Deckenlicht am Abend", "40"],
    ["E3", "Einzel", "senkrecht von oben", "ca. 50 cm", "weißes Papier", "Lampe von der Seite, mit Schatten", "40"],
    ["W1", "Wurf", "senkrecht von oben", "ca. 40 cm", "dunkelgrüner Filz", "Tageslicht am Fenster", "50"],
    ["W2", "Wurf", "senkrecht von oben", "ca. 40 cm", "dunkelgrüner Filz", "Deckenlicht am Abend", "40"],
    ["W3", "Wurf", "senkrecht von oben", "ca. 40 cm", "Holztisch", "Tageslicht am Fenster", "30"],
    ["W4", "Wurf", "leicht schräg, ca. 70°", "ca. 50 cm", "dunkelgrüner Filz", "Lampe von der Seite, mit Schatten", "30"],
    ["W5", "Wurf", "senkrecht von oben", "je zur Hälfte ca. 30 und 60 cm", "weißes Papier", "gedimmtes Licht", "30"],
    ["", "Summe", "", "", "", "", "300"],
], widths=[26, 46, 85, 70, 80, 100, 38], bold_last=True)

heading("2.2 Regeln für die Aufnahmen", 2)
bullet("Genau ein Objekt im Bild. Je Situation 5 Bilder pro Klasse. Bei den Würfelklassen wird dabei reihum gewechselt (WA, WB, WC), "
       "sodass jeder Würfel jede Augenzahl zeigt.", "Einzelaufnahmen (E1–E3): ")
bullet("Echte Spielsituation mit 3 Würfeln und der Münze. W1 und W2 sind der geplante Spielaufbau. "
       "Kommen weitere Würfel dazu, werden pro Wurf 3 Würfel zufällig gewählt.", "Wurfaufnahmen (W1–W5): ")
bullet("Jedes Bild mit anderer Drehung und Position. Bei etwa jedem fünften Wurf liegen die Objekte eng aneinander, einige liegen am Rand.", "Lagen: ")
bullet("Eine Strichliste hält fest, wie oft jeder Würfel welche Augenzahl zeigt (siehe 3.2). Seltene Kombinationen werden gezielt von Hand gelegt.", "Ausgewogenheit: ")
bullet("Im Aufnahmeprotokoll wird zu jedem Wurfbild notiert, welche Würfel verwendet wurden.", "Protokoll: ")

heading("3 Umfang des Datensatzes", 1)
heading("3.1 Originalbilder und Varianten", 2)
table([
    ["Bildart", "Anzahl"],
    ["Einzelaufnahmen (15 pro Klasse)", "120"],
    ["Wurfaufnahmen", "180"],
    ["Originalbilder gesamt", "300"],
    ["Technisch erzeugte Varianten (3 je Trainingsbild)", "630"],
    ["Bilder gesamt", "930"],
], widths=[300, 80])
bullet("Jede Klasse ist rund 105-mal in den Originalbildern zu sehen (15 Einzelaufnahmen und rund 90 Vorkommen in den Würfen).", "Verteilung: ")
bullet("Aus den 300 Originalen entstehen rund 840 Objekt-Ausschnitte (120 aus den Einzelaufnahmen, 4 je Wurfbild) für den Klassifizierer der Stufe 2, also rund 105 pro Unterklasse. "
       "Dafür sind keine zusätzlichen Fotos nötig.", "Ausschnitte für Stufe 2: ")
bullet("Mindestens 20 zusätzliche Wurfbilder in der Testsitzung mit den Testwürfeln T1 und T2.", "Testwürfel: ")

heading("3.2 Strichliste Würfel × Augenzahl", 2)
para("Zielwerte für die Originalbilder mit den 3 vorhandenen Trainingswürfeln (je Würfel und Augenzahl rund 35 Vorkommen). "
     "Kommen weitere Würfel dazu, verteilen sich die Werte entsprechend.")
table([
    ["Würfel", "1", "2", "3", "4", "5", "6", "Summe"],
    ["WA", "35", "35", "35", "35", "35", "35", "210"],
    ["WB", "35", "35", "35", "35", "35", "35", "210"],
    ["WC", "35", "35", "35", "35", "35", "35", "210"],
    ["Münze", "Kopf: 105", "Zahl: 105", "", "", "", "", "210"],
], widths=[60, 50, 50, 40, 40, 40, 40, 50])

heading("4 Technische Bildvariation (Data Augmentation)", 1)
para("Aus jedem Trainingsbild entstehen 3 Varianten mit der Bibliothek Albumentations. Jede Variante kombiniert zufällig 2 bis 3 Verfahren. "
     "Die Rahmen der Objekte werden automatisch mitverschoben.")
table([
    ["Verfahren", "Einstellung", "Zweck"],
    ["Drehen", "beliebiger Winkel, 0–360°", "Würfel liegen in jeder Richtung"],
    ["Helligkeit", "± 25 %", "wechselndes Licht"],
    ["Kontrast", "± 20 %", "wechselndes Licht, verschiedene Kameras"],
    ["Zuschneiden und Skalieren", "Ausschnitt 80–100 %, Zoom 80–120 %", "verschiedene Abstände"],
    ["Farbsättigung", "± 30 %", "verschiedene Kameras"],
    ["Farbton", "stark verschoben", "Würfelfarbe soll keine Rolle spielen"],
    ["Graustufen", "bei rund 30 % der Varianten", "Erkennung über Form und Kontrast statt Farbe"],
    ["Bildrauschen", "leicht", "schlechtere Kameras, wenig Licht"],
    ["Unschärfe", "leicht", "Bewegung, Fokus"],
], widths=[110, 150, 170])
bullet("Ziffer und Motiv der Münze wären sonst spiegelverkehrt. Das gilt für ganze Bilder und für Münz-Ausschnitte. "
       "Nur Würfel-Ausschnitte der Stufe 2 dürfen gespiegelt werden, weil Würfelaugen symmetrisch sind.", "Kein Spiegeln: ")
bullet("Beim Zuschneiden bleiben alle Objekte vollständig im Bild.", "Objekte vollständig: ")
bullet("Die Ausschnitte für Stufe 2 werden in Graustufen umgewandelt und gedreht. So zählt nur der Kontrast zwischen Würfel und Augen.", "Stufe 2: ")

heading("5 Aufteilung in Trainings- und Testdaten", 1)
table([
    ["Datensatz", "Originalbilder", "Varianten", "Zweck"],
    ["Training", "210 (70 %)", "630", "Lernen"],
    ["Validierung", "45 (15 %)", "keine", "Kontrolle während des Trainings"],
    ["Test", "45 (15 %) + mind. 20 mit Testwürfeln", "keine", "unabhängige Endbewertung"],
], widths=[80, 150, 60, 150])
bullet("Erst aufteilen, dann Varianten erzeugen, und zwar nur aus Trainingsbildern.", "Reihenfolge: ")
bullet("Die Testbilder entstehen in einer eigenen Sitzung an einem anderen Tag, mit rund 15 % der Bilder jeder Aufnahmesituation.", "Testsitzung: ")
bullet("Die Testwürfel T1 und T2 kommen nur in Testbildern vor.", "Unbekannte Würfel: ")
bullet("Kein Bild, keine Variante und kein Ausschnitt liegt in mehr als einem Datensatz. Die Ausschnitte für Stufe 2 werden erst nach der Aufteilung erzeugt.", "Trennung: ")
bullet("Mindestens 90 % der Testwürfe werden vollständig richtig erkannt (alle 3 Würfel und die Münze), getrennt ausgewertet für bekannte und unbekannte Würfel.", "Ziel: ")

heading("6 Organisation der Bilddaten", 1)
heading("6.1 Benennung", 2)
bullet("wurf_<Situation>_<Nummer>.jpg, z. B. wurf_W3_0042.jpg", "Wurfaufnahme: ")
bullet("einzel_<Situation>_<Klasse>_<Würfel>_<Nummer>.jpg, z. B. einzel_E2_wuerfel_4_WB_0007.jpg (bei der Münze ohne Würfel-Kürzel)", "Einzelaufnahme: ")
bullet("test_<Situation>_<Nummer>.jpg, z. B. test_W1_0005.jpg", "Testbild: ")
bullet("Name des Originals mit Zusatz, z. B. wurf_W3_0042_aug2.jpg", "Variante: ")
bullet("Name des Bildes mit Objektnummer, z. B. wurf_W3_0042_obj2.jpg", "Ausschnitt (Stufe 2): ")

heading("6.2 Klassenzuordnung", 2)
bullet("Über eine Label-Datei pro Bild mit gleichem Namen (.txt im YOLO-Format, eine Zeile pro Objekt mit Klassen-ID und Rahmen), nicht über Klassenordner. "
       "Gelabelt wird in Label Studio mit den 8 Klassen aus 1.2.", "Originale und Stufe 1: ")
bullet("Über Klassenordner (augen_1 … augen_6, kopf, zahl). Die Ausschnitte und Ordner erzeugt ein Skript automatisch aus den Labels.", "Stufe 2: ")
bullet("Jeder prüft 20 zufällige gelabelte Bilder des anderen.", "Kontrolle: ")

heading("6.3 Ordnerstruktur", 2)
struktur = [
    "wuerfel-zaehler/",
    "├── rohbilder/              Originalfotos, unverändert (Sicherung)",
    "│   ├── einzel/",
    "│   ├── wurf/",
    "│   └── test_sitzung/",
    "├── labels_original/        Export aus Label Studio (8 Klassen)",
    "├── dataset_stufe1/         Objekterkennung: wuerfel, muenze",
    "│   ├── images/ train, val, test",
    "│   ├── labels/ train, val, test",
    "│   └── data.yaml           Klassenliste und Pfade",
    "├── dataset_stufe2/         Ausschnitte für den Klassifizierer",
    "│   ├── train/ augen_1 … augen_6, kopf, zahl",
    "│   ├── val/   (gleiche Ordner)",
    "│   └── test/  (gleiche Ordner)",
    "└── aufnahmeprotokoll.xlsx  Strichliste, verwendete Würfel, Stand",
]
for line in struktur:
    p = d.add_paragraph()
    run = p.add_run(line)
    run.font.name = "Consolas"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
    run.font.size = Pt(9)
    p.paragraph_format.space_after = Pt(0)
    _append(p._p)
sp = d.add_paragraph(); _append(sp._p)
para("Die Fotos werden nicht in GitHub abgelegt (zu groß), sondern lokal bzw. im OneDrive. In GitHub liegen nur der Code und die fertigen Modelle.")

heading("7 Aufgabenverteilung im Team", 1)
table([
    ["Teammitglied", "Aufgaben"],
    ["Niklas Bäricke", "Aufbau der Wurffläche und Kamera, Fotoaufnahmen, Aufnahmeprotokoll und Strichliste"],
    ["Christian Maschke", "Skripte für Aufteilung, Bildvariation und Ausschnitte, Training und Auswertung"],
    ["Gemeinsam", "Weitere Würfel sammeln, Labeln in Label Studio, gegenseitige Kontrolle der Labels, Testsitzung, Dokumentation"],
], widths=[110, 330])

# Inhaltsverzeichnis: Überschriften als Platzhalter ins Feld schreiben, Word aktualisiert die Seitenzahlen
toc_lines = [p.text for p in d.paragraphs if p.style.name in ("Heading 1", "Heading 2")]
last = TOC_START
for i, line in enumerate(toc_lines):
    if i == 0:
        p_el = TOC_START
    else:
        p_el = OxmlElement("w:p")
        last.addnext(p_el)
    lvl2 = not line[:2].strip().isdigit() or "." in line.split()[0]
    if lvl2:
        pPr = OxmlElement("w:pPr"); ind = OxmlElement("w:ind"); ind.set(qn("w:left"), "360"); pPr.append(ind); p_el.insert(0, pPr)
    r = OxmlElement("w:r"); t = OxmlElement("w:t"); t.text = line; r.append(t); p_el.append(r)
    last = p_el
r = OxmlElement("w:r")
fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), "end"); r.append(fc)
last.append(r)

d.save(ZIEL)
print("gespeichert:", ZIEL)
