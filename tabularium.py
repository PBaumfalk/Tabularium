#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tabularium – revisionssichere Ablage von Tabellenkalkulationen.

Jede eingecheckte Fassung einer Tabelle (xlsx, xlsm, ods, fods, xls …) wird
unverändert abgelegt, ihr Zellinhalt (Werte und Formeln) ausgelesen und mit der
Vorversion verglichen. Alle Vorgänge stehen in einem Journal, dessen Einträge
über SHA-256 zu einer Kette verbunden sind. Optional sichert ein RFC-3161-
Zeitstempel jeden Eintrag gegenüber einer externen Zeitstempelstelle ab.

Nur Python-Standardbibliothek (ab 3.8). Für .xls/.xlsb wird LibreOffice
benötigt, für Zeitstempel OpenSSL.

Aufruf:  python3 tabularium.py --hilfe
"""

import argparse
import datetime
import getpass
import hashlib
import html
import json
import os
import pathlib
import posixpath
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from contextlib import contextmanager

try:                                    # macOS, Linux
    import fcntl
except ImportError:                     # Windows
    fcntl = None
    import msvcrt

# Unter Windows keine Konsolenfenster für Hilfsprogramme aufblitzen lassen
OHNE_FENSTER = {"creationflags": 0x08000000} if os.name == "nt" else {}

PROGRAMM = "Tabularium"
VERSION = "1.1.0"
ARCHIV_ORDNER = ".tabularium"
GENESIS = "0" * 64

FORMATE_XLSX = {".xlsx", ".xlsm", ".xltx", ".xltm"}
FORMATE_ODS = {".ods", ".ots"}
FORMATE_FODS = {".fods"}
FORMATE_KONVERTIEREN = {".xls", ".xlsb", ".xlt"}
ALLE_FORMATE = FORMATE_XLSX | FORMATE_ODS | FORMATE_FODS | FORMATE_KONVERTIEREN

STANDARD_EINSTELLUNGEN = {
    "zeitstempel": False,
    "tsa_url": "https://freetsa.org/tsr",
    "tsa_ca": "tsa/cacert.pem",
    "tsa_zertifikat": "tsa/tsa.crt",
}
FREETSA_DATEIEN = {
    "tsa/cacert.pem": "https://freetsa.org/files/cacert.pem",
    "tsa/tsa.crt": "https://freetsa.org/files/tsa.crt",
}


class ArchivFehler(Exception):
    pass


# --------------------------------------------------------------------------
# Hilfsfunktionen
# --------------------------------------------------------------------------

def sha256_datei(pfad):
    h = hashlib.sha256()
    with open(pfad, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def kanonisch(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def sha256_bytes(daten):
    return hashlib.sha256(daten).hexdigest()


def jetzt():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def zeit_lesbar(iso):
    try:
        d = datetime.datetime.fromisoformat(iso)
        return d.strftime("%d.%m.%Y %H:%M:%S")
    except (TypeError, ValueError):
        return iso or ""


def kurzpfad(pfad):
    """Ersetzt den Benutzerordner durch ~ (für Anzeigen)."""
    heim = os.path.expanduser("~")
    if pfad and pfad.startswith(heim + os.sep):
        return "~" + pfad[len(heim):]
    return pfad


def spalte(n):
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def spalten_nr(buchstaben):
    n = 0
    for ch in buchstaben:
        n = n * 26 + ord(ch) - 64
    return n


_REF_TEIL = re.compile(r"^([A-Z]+)([0-9]+)$")


def zerlege_ref(ref):
    m = _REF_TEIL.match(ref)
    if not m:
        return (0, 0)
    return (spalten_nr(m.group(1)), int(m.group(2)))


def zahl(text):
    if text is None:
        return None
    try:
        x = float(text)
    except ValueError:
        return text
    if x != x or x in (float("inf"), float("-inf")):
        return text
    if x.is_integer() and abs(x) < 1e15:
        return str(int(x))
    return format(x, ".15g")


def lokal(tag):
    return tag.rsplit("}", 1)[-1]


def kind(el, name):
    for c in el:
        if lokal(c.tag) == name:
            return c
    return None


def kinder(el, name):
    return [c for c in el if lokal(c.tag) == name]


def attr_lokal(el, name):
    for k, v in el.attrib.items():
        if lokal(k) == name:
            return v
    return None


def kurz(text, laenge=60):
    if text is None:
        return ""
    text = str(text).replace("\n", "⏎").replace("\t", "→")
    return text if len(text) <= laenge else text[: laenge - 1] + "…"


def setze_flag(pfad, flag):
    """Setzt ein macOS-Dateiflag (Schutz vor versehentlichem Ändern)."""
    try:
        aktuell = os.stat(pfad).st_flags
        os.chflags(pfad, aktuell | flag)
        return True
    except (AttributeError, OSError):
        return False


# --------------------------------------------------------------------------
# Auslesen: XLSX
# --------------------------------------------------------------------------

_REF_IN_FORMEL = re.compile(
    r"(?<![A-Za-z0-9_.$])(\$?)([A-Z]{1,3})(\$?)([0-9]{1,7})(?![A-Za-z0-9_(])")
_LITERALE = re.compile(r"(\"[^\"]*\"|'[^']*')")
DATUMS_IDS = set(range(14, 23)) | {45, 46, 47}


def verschiebe_formel(formel, d_spalte, d_zeile):
    """Verschiebt relative Bezüge einer geteilten Formel (wie Excel es tut)."""
    def ersetze(m):
        abs_s, buchst, abs_z, zeile = m.groups()
        s = spalten_nr(buchst)
        z = int(zeile)
        if not abs_s:
            s += d_spalte
        if not abs_z:
            z += d_zeile
        if s < 1 or z < 1 or s > 16384:
            return "#BEZUG!"
        return "%s%s%s%d" % (abs_s, spalte(s), abs_z, z)

    teile = _LITERALE.split(formel)
    for i in range(0, len(teile), 2):
        teile[i] = _REF_IN_FORMEL.sub(ersetze, teile[i])
    return "".join(teile)


def _ist_datumscode(code):
    if not code or code.lower() == "general":
        return False
    c = re.sub(r'"[^"]*"|\\.|\[[^\]]*\]', "", code)
    return bool(re.search(r"[dmyhs]", c, re.IGNORECASE))


def _seriell_zu_datum(wert, basis_1904):
    try:
        x = float(wert)
    except (TypeError, ValueError):
        return wert
    if basis_1904:
        basis = datetime.datetime(1904, 1, 1)
    else:
        basis = datetime.datetime(1899, 12, 30)
    try:
        d = basis + datetime.timedelta(days=x)
    except OverflowError:
        return wert
    if x < 1 and not basis_1904:
        return d.strftime("%H:%M:%S")
    if x == int(x):
        return d.strftime("%Y-%m-%d")
    return d.strftime("%Y-%m-%dT%H:%M:%S")


def lese_xlsx(pfad):
    with zipfile.ZipFile(pfad) as z:
        def xml(name):
            return ET.fromstring(z.read(name))

        namen = set(z.namelist())
        wb_pfad = "xl/workbook.xml"
        if "_rels/.rels" in namen:
            for r in xml("_rels/.rels"):
                if r.get("Type", "").endswith("/officeDocument"):
                    wb_pfad = r.get("Target", wb_pfad).lstrip("/")
        wb_dir = posixpath.dirname(wb_pfad)
        rels_pfad = posixpath.join(wb_dir, "_rels",
                                   posixpath.basename(wb_pfad) + ".rels")

        ziele, sst_pfad, styles_pfad = {}, None, None
        for r in xml(rels_pfad):
            if r.get("TargetMode") == "External":
                continue
            t = r.get("Target", "")
            voll = t.lstrip("/") if t.startswith("/") else \
                posixpath.normpath(posixpath.join(wb_dir, t))
            ziele[r.get("Id")] = voll
            typ = r.get("Type", "")
            if typ.endswith("/sharedStrings"):
                sst_pfad = voll
            elif typ.endswith("/styles"):
                styles_pfad = voll

        geteilt = []
        if sst_pfad and sst_pfad in namen:
            for si in kinder(xml(sst_pfad), "si"):
                teile = [t.text or "" for t in kinder(si, "t")]
                for r in kinder(si, "r"):
                    teile += [t.text or "" for t in kinder(r, "t")]
                geteilt.append("".join(teile))

        ist_datum = []
        if styles_pfad and styles_pfad in namen:
            st = xml(styles_pfad)
            codes = {}
            nf = kind(st, "numFmts")
            if nf is not None:
                for f in kinder(nf, "numFmt"):
                    codes[int(f.get("numFmtId", "0"))] = f.get("formatCode", "")
            xfs = kind(st, "cellXfs")
            if xfs is not None:
                for xf in kinder(xfs, "xf"):
                    nid = int(xf.get("numFmtId", "0"))
                    ist_datum.append(nid in DATUMS_IDS or
                                     _ist_datumscode(codes.get(nid)))

        wb = xml(wb_pfad)
        basis_1904 = False
        pr = kind(wb, "workbookPr")
        if pr is not None and pr.get("date1904") in ("1", "true"):
            basis_1904 = True

        blaetter, zellen = [], {}
        sheets = kind(wb, "sheets")
        for sh in (kinder(sheets, "sheet") if sheets is not None else []):
            name = sh.get("name")
            ziel = ziele.get(attr_lokal(sh, "id"))
            if not ziel or ziel not in namen:
                continue
            ws = xml(ziel)
            daten = kind(ws, "sheetData")
            if daten is None:          # Diagrammblatt
                continue
            blaetter.append(name)
            master = {}
            zeile = 0
            for row in kinder(daten, "row"):
                zeile = int(row.get("r")) if row.get("r") else zeile + 1
                spalte_nr = 0
                for c in kinder(row, "c"):
                    ref = c.get("r")
                    if ref:
                        spalte_nr, _ = zerlege_ref(ref)
                    else:
                        spalte_nr += 1
                        ref = "%s%d" % (spalte(spalte_nr), zeile)
                    typ = c.get("t", "n")
                    f_el, v_el = kind(c, "f"), kind(c, "v")
                    v = v_el.text if v_el is not None else None

                    formel = None
                    if f_el is not None:
                        si = f_el.get("si")
                        if f_el.text:
                            formel = "=" + f_el.text
                            if f_el.get("t") == "shared" and si is not None:
                                master[si] = (ref, f_el.text)
                        elif f_el.get("t") == "shared" and si in master:
                            m_ref, m_text = master[si]
                            ms, mz = zerlege_ref(m_ref)
                            s, zz = zerlege_ref(ref)
                            formel = "=" + verschiebe_formel(m_text, s - ms, zz - mz)

                    if typ == "s":
                        try:
                            wert = geteilt[int(v)]
                        except (TypeError, ValueError, IndexError):
                            wert = v
                    elif typ == "inlineStr":
                        is_el = kind(c, "is")
                        wert = "".join(t.text or "" for t in is_el.iter()
                                       if lokal(t.tag) == "t") if is_el is not None else ""
                    elif typ == "b":
                        wert = "WAHR" if v == "1" else "FALSCH"
                    elif typ in ("e", "str", "d"):
                        wert = v
                    else:
                        wert = zahl(v)
                        s_idx = int(c.get("s", "0"))
                        if wert is not None and s_idx < len(ist_datum) and ist_datum[s_idx]:
                            wert = _seriell_zu_datum(v, basis_1904)

                    if (wert is None or wert == "") and formel is None:
                        continue
                    zellen["%s!%s" % (name, ref)] = [wert if wert is not None else "", formel]
        return {"blaetter": blaetter, "zellen": zellen}


# --------------------------------------------------------------------------
# Auslesen: ODS / FODS
# --------------------------------------------------------------------------

NS_T = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
NS_O = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
NS_TX = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"


def T(n):
    return "{%s}%s" % (NS_T, n)


def O(n):
    return "{%s}%s" % (NS_O, n)


def TX(n):
    return "{%s}%s" % (NS_TX, n)


def _absatz_text(el):
    s = el.text or ""
    for k in el:
        if k.tag == TX("s"):
            s += " " * int(k.get(TX("c"), "1"))
        elif k.tag == TX("tab"):
            s += "\t"
        elif k.tag == TX("line-break"):
            s += "\n"
        elif k.tag == O("annotation"):
            pass
        else:
            s += _absatz_text(k)
        s += k.tail or ""
    return s


def _ods_zeilen(el):
    for c in el:
        if c.tag == T("table-row"):
            yield c
        elif c.tag in (T("table-header-rows"), T("table-row-group"), T("table-rows")):
            for z in _ods_zeilen(c):
                yield z


def _ods_zellinhalt(cell):
    formel = cell.get(T("formula"))
    if formel:
        for praefix in ("of:", "oooc:", "msoxl:"):
            if formel.startswith(praefix):
                formel = formel[len(praefix):]
                break
    vt = cell.get(O("value-type"))
    if vt in ("float", "percentage", "currency"):
        wert = zahl(cell.get(O("value")))
    elif vt == "date":
        wert = cell.get(O("date-value"))
    elif vt == "time":
        wert = cell.get(O("time-value"))
    elif vt == "boolean":
        wert = "WAHR" if cell.get(O("boolean-value")) == "true" else "FALSCH"
    else:
        sv = cell.get(O("string-value"))
        wert = sv if sv is not None else \
            "\n".join(_absatz_text(p) for p in cell.findall(TX("p")))
    if (wert is None or wert == "") and not formel:
        return None
    return [wert if wert is not None else "", formel or None]


def lese_ods_wurzel(root):
    body = root.find(O("body"))
    sp = body.find(O("spreadsheet")) if body is not None else None
    if sp is None:
        raise ArchivFehler("Keine Tabellenkalkulation (office:spreadsheet fehlt).")
    blaetter, zellen = [], {}
    for tab in sp.findall(T("table")):
        name = tab.get(T("name"))
        blaetter.append(name)
        zeile = 0
        for row in _ods_zeilen(tab):
            rr = int(row.get(T("number-rows-repeated"), "1"))
            inhalte = []
            sp_nr = 0
            for cell in row:
                if cell.tag not in (T("table-cell"), T("covered-table-cell")):
                    continue
                cr = int(cell.get(T("number-columns-repeated"), "1"))
                inhalt = _ods_zellinhalt(cell)
                if inhalt is not None:
                    for k in range(min(cr, 16384)):
                        inhalte.append((sp_nr + 1 + k, inhalt))
                sp_nr += cr
            if inhalte:
                for j in range(min(rr, 1048576)):
                    for sp_i, inhalt in inhalte:
                        zellen["%s!%s%d" % (name, spalte(sp_i), zeile + 1 + j)] = list(inhalt)
            zeile += rr
    return {"blaetter": blaetter, "zellen": zellen}


# --------------------------------------------------------------------------
# Auslesen: Weiche und Konvertierung
# --------------------------------------------------------------------------

def finde_soffice():
    kandidaten = [shutil.which("soffice"), shutil.which("libreoffice"),
                  "/Applications/LibreOffice.app/Contents/MacOS/soffice"]
    for basis in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if basis:
            kandidaten.append(os.path.join(basis, "LibreOffice", "program", "soffice.exe"))
    for p in kandidaten:
        if p and os.path.exists(p):
            return p
    return None


def konvertiere_nach_xlsx(pfad, zielordner):
    soffice = finde_soffice()
    if not soffice:
        raise ArchivFehler("LibreOffice nicht gefunden – für .xls/.xlsb nötig.")
    profil = tempfile.mkdtemp(prefix="tabularium-lo-")
    try:
        subprocess.run([soffice, "-env:UserInstallation=" + pathlib.Path(profil).as_uri(),
                        "--headless", "--convert-to", "xlsx",
                        "--outdir", zielordner, pfad],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=300, check=False, **OHNE_FENSTER)
    finally:
        shutil.rmtree(profil, ignore_errors=True)
    ziel = os.path.join(zielordner,
                        os.path.splitext(os.path.basename(pfad))[0] + ".xlsx")
    if not os.path.exists(ziel):
        raise ArchivFehler("Konvertierung mit LibreOffice fehlgeschlagen.")
    return ziel


def lese_tabelle(pfad):
    """Liefert {'blaetter': [...], 'zellen': {'Blatt!A1': [wert, formel]}}."""
    ext = os.path.splitext(pfad)[1].lower()
    try:
        if ext in FORMATE_XLSX:
            return lese_xlsx(pfad)
        if ext in FORMATE_ODS:
            with zipfile.ZipFile(pfad) as z:
                return lese_ods_wurzel(ET.fromstring(z.read("content.xml")))
        if ext in FORMATE_FODS:
            return lese_ods_wurzel(ET.parse(pfad).getroot())
        if ext in FORMATE_KONVERTIEREN:
            with tempfile.TemporaryDirectory(prefix="tabularium-") as td:
                return lese_xlsx(konvertiere_nach_xlsx(pfad, td))
    except zipfile.BadZipFile:
        raise ArchivFehler("Datei ist verschlüsselt oder beschädigt – "
                           "Zellinhalt nicht lesbar.")
    except (ET.ParseError, KeyError) as e:
        raise ArchivFehler("Dateiinhalt nicht lesbar (%s)." % e)
    raise ArchivFehler("Format %s wird nicht unterstützt." % ext)


# --------------------------------------------------------------------------
# Vergleich
# --------------------------------------------------------------------------

def _sortierschluessel(schluessel, blattreihenfolge):
    blatt, ref = schluessel.rsplit("!", 1)
    s, z = zerlege_ref(ref)
    return (blattreihenfolge.get(blatt, 9999), blatt, z, s)


def vergleiche(alt, neu):
    """Liste von (art, zelle, alt, neu); art in neu/geaendert/geloescht."""
    a = alt["zellen"] if alt else {}
    n = neu["zellen"] if neu else {}
    reihenfolge = {}
    for b in (neu or {}).get("blaetter", []) + (alt or {}).get("blaetter", []):
        reihenfolge.setdefault(b, len(reihenfolge))
    ergebnis = []
    for k in set(a) | set(n):
        if k not in a:
            ergebnis.append(("neu", k, None, n[k]))
        elif k not in n:
            ergebnis.append(("geloescht", k, a[k], None))
        elif a[k] != n[k]:
            ergebnis.append(("geaendert", k, a[k], n[k]))
    ergebnis.sort(key=lambda e: _sortierschluessel(e[1], reihenfolge))
    return ergebnis


def blattaenderungen(alt, neu):
    a = (alt or {}).get("blaetter", [])
    n = (neu or {}).get("blaetter", [])
    return [b for b in n if b not in a], [b for b in a if b not in n]


def zaehle(aenderungen):
    z = {"neu": 0, "geaendert": 0, "geloescht": 0}
    for art, _, _, _ in aenderungen:
        z[art] += 1
    return z


def zellanzeige(inhalt):
    if inhalt is None:
        return "–"
    wert, formel = inhalt
    if formel:
        return "%s  [%s]" % (wert, formel)
    return wert


# --------------------------------------------------------------------------
# Archiv
# --------------------------------------------------------------------------

class Archiv:
    def __init__(self, wurzel):
        self.wurzel = os.path.abspath(wurzel)
        self.journal = os.path.join(self.wurzel, "journal.jsonl")
        self.objekte = os.path.join(self.wurzel, "objekte")
        self.zellen = os.path.join(self.wurzel, "zellen")
        self.zeitstempel = os.path.join(self.wurzel, "zeitstempel")
        self.einstellungsdatei = os.path.join(self.wurzel, "einstellungen.json")

    # -- Finden / Anlegen ---------------------------------------------------
    @staticmethod
    def finden(start):
        pfad = os.path.abspath(start)
        while True:
            kandidat = os.path.join(pfad, ARCHIV_ORDNER)
            if os.path.isdir(kandidat):
                return Archiv(kandidat)
            oben = os.path.dirname(pfad)
            if oben == pfad:
                return None
            pfad = oben

    @staticmethod
    def anlegen(ordner):
        a = Archiv(os.path.join(os.path.abspath(ordner), ARCHIV_ORDNER))
        for d in (a.wurzel, a.objekte, a.zellen, a.zeitstempel):
            os.makedirs(d, exist_ok=True)
        if not os.path.exists(a.journal):
            open(a.journal, "a").close()
            setze_flag(a.journal, stat.UF_APPEND)
        if not os.path.exists(a.einstellungsdatei):
            a.einstellungen_speichern(dict(STANDARD_EINSTELLUNGEN))
        with open(os.path.join(a.wurzel, "LIESMICH.txt"), "w", encoding="utf-8") as f:
            f.write("Dies ist das Archiv des Tabulariums.\n"
                    "Nichts hier von Hand ändern, verschieben oder löschen.\n"
                    "Prüfen: python3 tabularium.py pruefen\n")
        return a

    # -- Einstellungen ------------------------------------------------------
    def einstellungen(self):
        e = dict(STANDARD_EINSTELLUNGEN)
        if os.path.exists(self.einstellungsdatei):
            with open(self.einstellungsdatei, encoding="utf-8") as f:
                e.update(json.load(f))
        return e

    def einstellungen_speichern(self, e):
        with open(self.einstellungsdatei, "w", encoding="utf-8") as f:
            json.dump(e, f, ensure_ascii=False, indent=2)

    # -- Sperre ---------------------------------------------------------------
    @contextmanager
    def sperre(self):
        with open(os.path.join(self.wurzel, "sperre"), "a+") as f:
            if fcntl:
                fcntl.flock(f, fcntl.LOCK_EX)
            else:
                f.seek(0)
                while True:
                    try:
                        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                        break
                    except OSError:     # LK_LOCK gibt nach ~10 s auf
                        time.sleep(0.2)
            try:
                yield
            finally:
                if fcntl:
                    fcntl.flock(f, fcntl.LOCK_UN)
                else:
                    f.seek(0)
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)

    # -- Journal ------------------------------------------------------------
    def eintraege(self):
        if not os.path.exists(self.journal):
            return []
        liste = []
        with open(self.journal, encoding="utf-8") as f:
            for nr, zeile in enumerate(f, 1):
                if not zeile.strip():
                    continue
                try:
                    liste.append(json.loads(zeile))
                except ValueError:
                    raise ArchivFehler("Journal Zeile %d ist beschädigt – "
                                       "bitte 'pruefen' ausführen." % nr)
        return liste

    def anhaengen(self, eintrag):
        zeile = json.dumps(eintrag, ensure_ascii=False, sort_keys=True) + "\n"
        with open(self.journal, "a", encoding="utf-8", newline="\n") as f:
            f.write(zeile)
            f.flush()
            os.fsync(f.fileno())

    # -- Ablage -------------------------------------------------------------
    def objektpfad(self, sha):
        return os.path.join(self.objekte, sha[:2], sha)

    def schnappschusspfad(self, sha):
        return os.path.join(self.zellen, sha[:2], sha + ".json")

    def zeitstempelpfad(self, eintrag_hash):
        return os.path.join(self.zeitstempel, eintrag_hash + ".tsr")

    def objekt_speichern(self, quelle, sha):
        ziel = self.objektpfad(sha)
        if os.path.exists(ziel):
            return ziel
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        tmp = ziel + ".tmp"
        shutil.copyfile(quelle, tmp)
        if sha256_datei(tmp) != sha:
            os.remove(tmp)
            raise ArchivFehler("Datei hat sich während des Sicherns verändert – "
                               "bitte erneut versuchen.")
        os.replace(tmp, ziel)
        os.chmod(ziel, 0o444)
        setze_flag(ziel, stat.UF_IMMUTABLE)
        return ziel

    def schnappschuss_speichern(self, daten):
        roh = kanonisch(daten)
        sha = sha256_bytes(roh)
        ziel = self.schnappschusspfad(sha)
        if not os.path.exists(ziel):
            os.makedirs(os.path.dirname(ziel), exist_ok=True)
            with open(ziel + ".tmp", "wb") as f:
                f.write(roh)
            os.replace(ziel + ".tmp", ziel)
            os.chmod(ziel, 0o444)
            setze_flag(ziel, stat.UF_IMMUTABLE)
        return sha

    def schnappschuss_laden(self, sha):
        if not sha:
            return None
        pfad = self.schnappschusspfad(sha)
        if not os.path.exists(pfad):
            return None
        with open(pfad, "rb") as f:
            return json.loads(f.read().decode("utf-8"))

    # -- Abfragen -------------------------------------------------------------
    def dokumente(self):
        docs = {}
        for e in self.eintraege():
            docs.setdefault(e["dokument"], []).append(e)
        return docs

    def versionen(self, dokument):
        return [e for e in self.eintraege() if e["dokument"] == dokument]


# --------------------------------------------------------------------------
# Zeitstempel (RFC 3161)
# --------------------------------------------------------------------------

def finde_openssl():
    """Pfad zu OpenSSL/LibreSSL oder None (z. B. unter Windows)."""
    for p in ("/opt/homebrew/bin/openssl", "/usr/local/bin/openssl", "/usr/bin/openssl",
              shutil.which("openssl")):
        if p and os.path.exists(p):
            return p
    return None


def http_holen(url, ziel, daten_datei=None, inhaltstyp=None):
    """Lädt url nach ziel (POST, wenn daten_datei). Nutzt curl, sonst urllib."""
    agent = "%s/%s" % (PROGRAMM.replace(" ", "-"), VERSION)
    curl = shutil.which("curl")
    if curl:
        befehl = [curl, "-sS", "--fail", "--max-time", "60", "-A", agent, "-o", ziel]
        if daten_datei:
            befehl += ["--data-binary", "@" + daten_datei]
        if inhaltstyp:
            befehl += ["-H", "Content-Type: " + inhaltstyp]
        r = subprocess.run(befehl + [url], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           universal_newlines=True, **OHNE_FENSTER)
        if r.returncode != 0:
            raise ArchivFehler("Abruf fehlgeschlagen (%s): %s" % (url, r.stderr.strip()))
        return
    daten = open(daten_datei, "rb").read() if daten_datei else None
    kopf = {"User-Agent": agent}
    if inhaltstyp:
        kopf["Content-Type"] = inhaltstyp
    with urllib.request.urlopen(urllib.request.Request(url, data=daten, headers=kopf),
                                timeout=60) as r:
        with open(ziel, "wb") as f:
            f.write(r.read())


def tsa_dateien_sicherstellen(archiv, einst):
    for rel, url in FREETSA_DATEIEN.items():
        pfad = os.path.join(archiv.wurzel, rel)
        if einst.get("tsa_ca") == rel or einst.get("tsa_zertifikat") == rel:
            if not os.path.exists(pfad) and "freetsa.org" in einst["tsa_url"]:
                os.makedirs(os.path.dirname(pfad), exist_ok=True)
                http_holen(url, pfad)


# -- DER (ASN.1) in reinem Python: genug für RFC-3161-Anfrage und -Antwort ------

_OID_SHA256 = bytes.fromhex("608648016503040201")


def _der_laenge(n):
    if n < 0x80:
        return bytes([n])
    b = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(b)]) + b


def _der(tag, inhalt):
    return bytes([tag]) + _der_laenge(len(inhalt)) + inhalt


def _der_int(n):
    return _der(0x02, n.to_bytes(max(1, (n.bit_length() + 8) // 8), "big"))


def _der_lesen(daten, pos):
    """Liest ein TLV ab pos -> (tag, inhalt_start, inhalt_ende)."""
    tag = daten[pos]
    laenge = daten[pos + 1]
    pos += 2
    if laenge & 0x80:
        n = laenge & 0x7F
        if n == 0 or n > 4:
            raise ValueError("unbestimmte oder zu große Länge")
        laenge = int.from_bytes(daten[pos:pos + n], "big")
        pos += n
    if pos + laenge > len(daten):
        raise ValueError("Länge über Datenende")
    return tag, pos, pos + laenge


def _der_kinder(daten, start, ende):
    teile, pos = [], start
    while pos < ende:
        t, s, e = _der_lesen(daten, pos)
        teile.append((t, s, e))
        pos = e
    return teile


def tsa_anfrage(hexhash, nonce):
    """TimeStampReq (RFC 3161) für einen SHA-256-Wert, mit Nonce und certReq."""
    algorithmus = _der(0x30, _der(0x06, _OID_SHA256) + b"\x05\x00")
    imprint = _der(0x30, algorithmus + _der(0x04, bytes.fromhex(hexhash)))
    return _der(0x30, _der_int(1) + imprint + _der_int(nonce) + b"\x01\x01\xff")


def tsa_info(roh):
    """Liest eine TimeStampResp: Status, Hash, Zeit (UTC), Nonce. Prüft KEINE Signatur."""
    _, s, e = _der_lesen(roh, 0)
    teile = _der_kinder(roh, s, e)
    st = _der_kinder(roh, teile[0][1], teile[0][2])[0]
    status = int.from_bytes(roh[st[1]:st[2]], "big")
    if status not in (0, 1) or len(teile) < 2:
        return {"status": status}
    ci = _der_kinder(roh, teile[1][1], teile[1][2])            # ContentInfo
    sd = _der_kinder(roh, ci[1][1], ci[1][2])[0]               # [0] -> SignedData
    sdk = _der_kinder(roh, sd[1], sd[2])
    eci = _der_kinder(roh, sdk[2][1], sdk[2][2])               # EncapsulatedContentInfo
    okt = _der_kinder(roh, eci[1][1], eci[1][2])[0]            # [0] -> OCTET STRING
    tst = roh[okt[1]:okt[2]]
    _, s, e = _der_lesen(tst, 0)
    tk = _der_kinder(tst, s, e)                                 # TSTInfo
    mi = _der_kinder(tst, tk[2][1], tk[2][2])
    alg = _der_kinder(tst, mi[0][1], mi[0][2])[0]
    nonce = None
    for t, a, b in tk[5:]:
        if t == 0x02:
            nonce = int.from_bytes(tst[a:b], "big")
            break
    zeit = tst[tk[4][1]:tk[4][2]].decode("ascii")
    m = re.match(r"(\d{14})(?:\.\d+)?Z$", zeit)
    utc = datetime.datetime.strptime(m.group(1), "%Y%m%d%H%M%S").replace(
        tzinfo=datetime.timezone.utc) if m else None
    return {"status": status, "algorithmus": tst[alg[1]:alg[2]],
            "hash": tst[mi[1][1]:mi[1][2]].hex(), "zeit": utc, "nonce": nonce}


def _zeit_text(utc):
    return utc.astimezone().strftime("%d.%m.%Y %H:%M:%S") if utc else "?"


def zeitstempel_holen(archiv, hexhash):
    einst = archiv.einstellungen()
    nonce = int.from_bytes(os.urandom(8), "big") >> 1
    with tempfile.TemporaryDirectory(prefix="tabularium-ts-") as td:
        anfrage = os.path.join(td, "anfrage.tsq")
        with open(anfrage, "wb") as f:
            f.write(tsa_anfrage(hexhash, nonce))
        antwort = os.path.join(td, "antwort.tsr")
        http_holen(einst["tsa_url"], antwort, daten_datei=anfrage,
                   inhaltstyp="application/timestamp-query")
        with open(antwort, "rb") as f:
            roh = f.read()
    try:
        info = tsa_info(roh)
    except (ValueError, IndexError, UnicodeDecodeError):
        raise ArchivFehler("Antwort der Zeitstempelstelle nicht lesbar.")
    if info["status"] not in (0, 1):
        raise ArchivFehler("Zeitstempelstelle hat abgelehnt (Status %s)." % info["status"])
    if info["hash"] != hexhash or info["algorithmus"] != _OID_SHA256:
        raise ArchivFehler("Zeitstempel gehört nicht zur Anfrage.")
    if info["nonce"] != nonce:
        raise ArchivFehler("Zeitstempel: Nonce stimmt nicht überein.")
    ziel = archiv.zeitstempelpfad(hexhash)
    with open(ziel, "wb") as f:
        f.write(roh)
    os.chmod(ziel, 0o444)
    tsa_dateien_sicherstellen(archiv, einst)
    ok, text = zeitstempel_pruefen(archiv, hexhash)
    if not ok:
        os.chmod(ziel, 0o644)
        os.remove(ziel)
        raise ArchivFehler("Zeitstempel ungültig: " + text)
    setze_flag(ziel, stat.UF_IMMUTABLE)
    return text


def zeitstempel_zeit(tsr_pfad):
    """Zeit laut Zeitstempelstelle, als Ortszeit (ohne Signaturprüfung)."""
    try:
        with open(tsr_pfad, "rb") as f:
            return _zeit_text(tsa_info(f.read()).get("zeit"))
    except (OSError, ValueError, IndexError, UnicodeDecodeError):
        return "?"


SIGNATUR_UNGEPRUEFT = " (Signatur ungeprüft – OpenSSL fehlt)"


def zeitstempel_pruefen(archiv, hexhash):
    """(ok, Text): Stempel deckt genau diesen Hash; mit OpenSSL auch die Signatur.
    ok ist None, wenn kein Zeitstempel vorliegt."""
    pfad = archiv.zeitstempelpfad(hexhash)
    if not os.path.exists(pfad):
        return None, "kein Zeitstempel"
    with open(pfad, "rb") as f:
        roh = f.read()
    try:
        info = tsa_info(roh)
    except (ValueError, IndexError, UnicodeDecodeError):
        info = None
    if info is not None and (info.get("status") not in (0, 1) or info.get("hash") != hexhash):
        return False, "gehört nicht zu diesem Eintrag"
    openssl = finde_openssl()
    if not openssl:
        if info is None:
            return False, "nicht lesbar"
        return True, _zeit_text(info.get("zeit")) + SIGNATUR_UNGEPRUEFT
    einst = archiv.einstellungen()
    ca = os.path.join(archiv.wurzel, einst["tsa_ca"])
    zert = os.path.join(archiv.wurzel, einst["tsa_zertifikat"])
    if not os.path.exists(ca):
        return False, "CA-Zertifikat der Zeitstempelstelle fehlt (%s)" % ca
    befehl = [openssl, "ts", "-verify", "-digest", hexhash, "-in", pfad, "-CAfile", ca]
    if os.path.exists(zert):
        befehl += ["-untrusted", zert]
    r = subprocess.run(befehl, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True, **OHNE_FENSTER)
    if "Verification: OK" in r.stdout:
        return True, zeitstempel_zeit(pfad)
    return False, (r.stdout.strip().splitlines() or ["unbekannter Fehler"])[-1]


# --------------------------------------------------------------------------
# Prüfung
# --------------------------------------------------------------------------

def pruefe_archiv(archiv, mit_zeitstempeln=True):
    """Liefert (fehler, hinweise, kopf_hash, anzahl, zeitstempel_ok)."""
    fehler, hinweise = [], []
    vorher = GENESIS
    anzahl = zs_ok = letzte_nr = 0
    versionen = {}
    if not os.path.exists(archiv.journal):
        return ["Journal fehlt."], [], None, 0, 0
    with open(archiv.journal, encoding="utf-8") as f:
        zeilen = f.readlines()
    for i, zeile in enumerate(zeilen, 1):
        if not zeile.strip():
            fehler.append("Journal Zeile %d: leere Zeile eingefügt." % i)
            continue
        try:
            e = json.loads(zeile)
        except ValueError:
            fehler.append("Journal Zeile %d: kein gültiger Eintrag (manipuliert?)." % i)
            vorher = None
            continue
        anzahl += 1
        name = "%s v%s" % (e.get("dokument", "?"), e.get("version", "?"))
        rest = {k: v for k, v in e.items() if k != "hash"}
        if sha256_bytes(kanonisch(rest)) != e.get("hash"):
            fehler.append("Eintrag %d (%s): Inhalt nachträglich verändert." % (i, name))
        if vorher is not None and e.get("vorher") != vorher:
            fehler.append("Eintrag %d (%s): Kette unterbrochen – davor wurde ein "
                          "Eintrag entfernt, eingefügt oder geändert." % (i, name))
        if e.get("nr") != letzte_nr + 1:
            fehler.append("Eintrag %d (%s): laufende Nummer %s, erwartet %d – "
                          "Eintrag fehlt oder eingeschoben." %
                          (i, name, e.get("nr"), letzte_nr + 1))
        letzte_nr = e.get("nr") if isinstance(e.get("nr"), int) else letzte_nr + 1
        erwartet = versionen.get(e.get("dokument"), 0) + 1
        if e.get("version") != erwartet:
            fehler.append("Eintrag %d (%s): Versionsnummer erwartet %d." %
                          (i, name, erwartet))
        versionen[e.get("dokument")] = e.get("version") if isinstance(e.get("version"), int) else erwartet

        obj = archiv.objektpfad(e.get("datei_sha256", "x" * 64))
        if not os.path.exists(obj):
            fehler.append("Eintrag %d (%s): gesicherte Datei fehlt." % (i, name))
        elif sha256_datei(obj) != e.get("datei_sha256"):
            fehler.append("Eintrag %d (%s): gesicherte Datei wurde verändert." % (i, name))

        zsha = e.get("zellen_sha256")
        if zsha:
            sp = archiv.schnappschusspfad(zsha)
            if not os.path.exists(sp):
                fehler.append("Eintrag %d (%s): Zellabbild fehlt." % (i, name))
            else:
                with open(sp, "rb") as f:
                    if sha256_bytes(f.read()) != zsha:
                        fehler.append("Eintrag %d (%s): Zellabbild verändert." % (i, name))

        if mit_zeitstempeln:
            ok, info = zeitstempel_pruefen(archiv, e.get("hash", ""))
            if ok:
                zs_ok += 1
            elif ok is False:
                fehler.append("Eintrag %d (%s): Zeitstempel ungültig – %s" % (i, name, info))
        vorher = e.get("hash")
    if anzahl and zs_ok == 0 and mit_zeitstempeln:
        hinweise.append("Keine Zeitstempel vorhanden. Ohne externen Zeitstempel "
                        "kann jemand mit Vollzugriff das gesamte Archiv neu "
                        "berechnen. Einschalten: tabularium einstellungen --zeitstempel an")
    if zs_ok and mit_zeitstempeln and not finde_openssl():
        hinweise.append("OpenSSL ist nicht installiert: Die Zeitstempel wurden auf "
                        "Zugehörigkeit und Zeit geprüft, ihre Signatur aber nicht. "
                        "Die vollständige Prüfung gelingt auf jedem Mac oder mit "
                        "OpenSSL (Handbuch, Kapitel 11).")
    return fehler, hinweise, vorher, anzahl, zs_ok


# --------------------------------------------------------------------------
# Befehle
# --------------------------------------------------------------------------

def archiv_holen(args, anlegen=False, start=None):
    if getattr(args, "archiv", None):
        pfad = os.path.abspath(args.archiv)
        if os.path.basename(pfad) != ARCHIV_ORDNER:
            pfad = os.path.join(pfad, ARCHIV_ORDNER)
        if os.path.isdir(pfad):
            return Archiv(pfad)
        if anlegen:
            print("Neues Archiv angelegt: %s" % pfad)
            return Archiv.anlegen(os.path.dirname(pfad))
        raise ArchivFehler("Kein Archiv unter %s." % pfad)
    a = Archiv.finden(start or os.getcwd())
    if a:
        return a
    if anlegen:
        ordner = start or os.getcwd()
        print("Neues Archiv angelegt: %s" % os.path.join(ordner, ARCHIV_ORDNER))
        return Archiv.anlegen(ordner)
    raise ArchivFehler("Kein Archiv gefunden. Zuerst eine Datei einchecken "
                       "oder --archiv angeben.")


def dokument_aufloesen(archiv, angabe):
    docs = archiv.dokumente()
    name = os.path.basename(angabe.rstrip("/"))
    if name in docs:
        return name
    treffer = [d for d in docs if d.lower() == name.lower()]
    if len(treffer) == 1:
        return treffer[0]
    raise ArchivFehler("Dokument '%s' ist nicht im Archiv. Vorhanden: %s" %
                       (name, ", ".join(sorted(docs)) or "keine"))


def dokumentname_fuer(archiv, pfad):
    """Gleicher Pfad -> gleiches Dokument. Gleicher Dateiname aus einem anderen,
    noch vorhandenen Ordner -> eigenes Dokument 'Name (Ordner)'."""
    pfad = os.path.abspath(pfad)
    docs = archiv.dokumente()
    for name, versionen in docs.items():
        if versionen[-1].get("quelle") == pfad:
            return name
    name = os.path.basename(pfad)
    if name in docs:
        q = docs[name][-1].get("quelle")
        if q and os.path.isabs(q) and q != pfad and os.path.exists(q):
            name = "%s (%s)" % (name, os.path.basename(os.path.dirname(pfad)))
    return name


def version_waehlen(versionen, angabe):
    if angabe is None:
        return None
    nr = int(str(angabe).lstrip("vV"))
    for e in versionen:
        if e["version"] == nr:
            return e
    raise ArchivFehler("Version %s gibt es nicht (1–%d)." % (nr, len(versionen)))


def einchecken_datei(archiv, pfad, name=None, notiz=None, bearbeiter=None,
                     zeitstempel=None, erzwingen=False, leise=False,
                     quelle=None, melden=print):
    """Sichert eine Fassung. quelle: abweichende Herkunftsangabe (z. B. Upload).
    melden: Funktion für Statusmeldungen (Standard: print)."""
    pfad = os.path.abspath(pfad)
    if not os.path.isfile(pfad):
        raise ArchivFehler("Datei nicht gefunden: %s" % pfad)
    ext = os.path.splitext(pfad)[1].lower()
    if ext not in ALLE_FORMATE:
        raise ArchivFehler("Format %s nicht unterstützt (%s)." %
                           (ext, ", ".join(sorted(ALLE_FORMATE))))
    dokument = name or os.path.basename(pfad)

    with archiv.sperre():
        sha = sha256_datei(pfad)
        versionen = archiv.versionen(dokument)
        letzte = versionen[-1] if versionen else None
        if letzte and letzte["datei_sha256"] == sha and not erzwingen:
            if not leise:
                melden("= %s: unverändert seit Version %d – nichts zu tun." %
                      (dokument, letzte["version"]))
            return None
        if letzte and letzte.get("quelle") and letzte["quelle"] != (quelle or pfad) and not leise:
            melden("! Hinweis: '%s' wurde bisher aus %s eingecheckt." %
                  (dokument, letzte["quelle"]))

        warnung = None
        try:
            abbild = lese_tabelle(pfad)
        except ArchivFehler as e:
            abbild, warnung = None, str(e)

        archiv.objekt_speichern(pfad, sha)
        zsha = archiv.schnappschuss_speichern(abbild) if abbild else None
        vorher_abbild = archiv.schnappschuss_laden(letzte.get("zellen_sha256")) if letzte else None
        aenderungen = vergleiche(vorher_abbild, abbild) if abbild else []
        neu_bl, weg_bl = blattaenderungen(vorher_abbild, abbild)

        alle = archiv.eintraege()
        st = os.stat(pfad)
        eintrag = {
            "nr": len(alle) + 1,
            "dokument": dokument,
            "version": len(versionen) + 1,
            "zeit": jetzt(),
            "nutzer": getpass.getuser(),
            "rechner": socket.gethostname(),
            "bearbeiter": bearbeiter,
            "notiz": notiz,
            "quelle": quelle or pfad,
            "format": ext.lstrip("."),
            "datei_sha256": sha,
            "datei_bytes": st.st_size,
            "datei_geaendert": datetime.datetime.fromtimestamp(st.st_mtime)
                                .astimezone().isoformat(timespec="seconds"),
            "zellen_sha256": zsha,
            "anzahl_zellen": len(abbild["zellen"]) if abbild else None,
            "blaetter": abbild["blaetter"] if abbild else None,
            "aenderungen": zaehle(aenderungen) if abbild else None,
            "blaetter_neu": neu_bl,
            "blaetter_entfernt": weg_bl,
            "warnung": warnung,
            "vorher": alle[-1]["hash"] if alle else GENESIS,
            "programm": "%s %s" % (PROGRAMM, VERSION),
        }
        eintrag["hash"] = sha256_bytes(kanonisch(eintrag))
        archiv.anhaengen(eintrag)

    z = eintrag["aenderungen"]
    if z is None:
        zusammenfassung = "Datei gesichert, Zellinhalt nicht lesbar"
    elif eintrag["version"] == 1:
        zusammenfassung = "Erstfassung, %d Zellen" % eintrag["anzahl_zellen"]
    else:
        zusammenfassung = "%d geändert, %d neu, %d gelöscht" % (
            z["geaendert"], z["neu"], z["geloescht"])
    melden("✔ %s – Version %d gesichert (%s)" % (dokument, eintrag["version"],
                                               zusammenfassung))
    if warnung:
        melden("  ! %s" % warnung)
    for b in (neu_bl if eintrag["version"] > 1 else []):
        melden("  + Blatt neu: %s" % b)
    for b in weg_bl:
        melden("  - Blatt entfernt: %s" % b)
    if eintrag["version"] > 1 and not leise:
        zeige_aenderungen(aenderungen, grenze=15, einzug="  ")

    if zeitstempel is None:
        zeitstempel = archiv.einstellungen().get("zeitstempel", False)
    if zeitstempel:
        try:
            info = zeitstempel_holen(archiv, eintrag["hash"])
            eintrag = dict(eintrag, _zeitstempel=info)
            melden("  ⏱ Zeitstempel erhalten: %s" % info)
        except Exception as e:  # Netz, TSA …
            eintrag = dict(eintrag, _zeitstempel_fehler=str(e))
            melden("  ! Zeitstempel fehlgeschlagen: %s" % e)
            melden("    Nachholen mit: tabularium zeitstempel")
    return eintrag


def zeige_aenderungen(aenderungen, grenze=None, einzug=""):
    if not aenderungen:
        print(einzug + "(keine Zelländerungen)")
        return
    zeichen = {"neu": "+", "geaendert": "~", "geloescht": "-"}
    liste = aenderungen if grenze is None else aenderungen[:grenze]
    breite = max(len(k) for _, k, _, _ in liste)
    for art, k, alt, neu in liste:
        if art == "geaendert":
            text = "%s  →  %s" % (kurz(zellanzeige(alt), 45), kurz(zellanzeige(neu), 45))
        elif art == "neu":
            text = kurz(zellanzeige(neu), 90)
        else:
            text = "(war: %s)" % kurz(zellanzeige(alt), 80)
        print("%s%s %s  %s" % (einzug, zeichen[art], k.ljust(breite), text))
    if grenze is not None and len(aenderungen) > grenze:
        print("%s… und %d weitere (tabularium vergleich zeigt alle)" %
              (einzug, len(aenderungen) - grenze))


def befehl_einchecken(args):
    erstes = os.path.dirname(os.path.abspath(args.dateien[0]))
    archiv = archiv_holen(args, anlegen=True, start=None if args.archiv else erstes)
    fehler = 0
    zs = {"an": True, "aus": False}.get(args.zeitstempel)
    for d in args.dateien:
        try:
            einchecken_datei(archiv, d, name=args.name, notiz=args.notiz,
                             bearbeiter=args.bearbeiter, zeitstempel=zs,
                             erzwingen=args.erzwingen)
        except ArchivFehler as e:
            print("✘ %s: %s" % (d, e))
            fehler += 1
    return 1 if fehler else 0


def befehl_liste(args):
    archiv = archiv_holen(args)
    docs = archiv.dokumente()
    if not docs:
        print("Das Archiv ist leer.")
        return 0
    print("Archiv: %s\n" % archiv.wurzel)
    breite = max(len(d) for d in docs)
    print("%s  %8s  %-19s  %s" % ("Dokument".ljust(breite), "Versionen",
                                   "zuletzt", "Status der Datei"))
    for d in sorted(docs):
        v = docs[d]
        letzte = v[-1]
        status = "–"
        q = letzte.get("quelle")
        if q and os.path.exists(q):
            status = "aktuell" if sha256_datei(q) == letzte["datei_sha256"] \
                else "GEÄNDERT, nicht eingecheckt"
        elif q:
            status = "Datei nicht mehr am Ort"
        print("%s  %8d  %-19s  %s" % (d.ljust(breite), len(v),
                                      zeit_lesbar(letzte["zeit"]), status))
    return 0


def befehl_verlauf(args):
    archiv = archiv_holen(args)
    dok = dokument_aufloesen(archiv, args.dokument)
    versionen = archiv.versionen(dok)
    print("Verlauf: %s  (%d Versionen)\n" % (dok, len(versionen)))
    vorher = None
    for e in versionen:
        z = e.get("aenderungen")
        if z is None:
            aend = "Zellen nicht lesbar"
        elif e["version"] == 1:
            aend = "Erstfassung, %d Zellen" % (e.get("anzahl_zellen") or 0)
        else:
            aend = "%d geändert, %d neu, %d gelöscht" % (z["geaendert"], z["neu"], z["geloescht"])
        wer = e.get("bearbeiter") or e.get("nutzer")
        zs = " ⏱" if os.path.exists(archiv.zeitstempelpfad(e["hash"])) else ""
        print("v%-3d %s  %-14s %s%s" % (e["version"], zeit_lesbar(e["zeit"]),
                                        kurz(wer, 14), aend, zs))
        if e.get("notiz"):
            print("     Notiz: %s" % e["notiz"])
        if args.details and e["version"] > 1:
            alt = archiv.schnappschuss_laden(vorher.get("zellen_sha256")) if vorher else None
            neu = archiv.schnappschuss_laden(e.get("zellen_sha256"))
            if neu:
                zeige_aenderungen(vergleiche(alt, neu), einzug="       ")
        vorher = e
    return 0


def befehl_vergleich(args):
    archiv = archiv_holen(args)
    dok = dokument_aufloesen(archiv, args.dokument)
    versionen = archiv.versionen(dok)
    if args.aktuell:
        von = version_waehlen(versionen, args.von) if args.von else versionen[-1]
        quelle = args.aktuell if isinstance(args.aktuell, str) else von.get("quelle")
        if not quelle or not os.path.exists(quelle):
            raise ArchivFehler("Aktuelle Datei nicht gefunden: %s" % quelle)
        alt = archiv.schnappschuss_laden(von.get("zellen_sha256"))
        neu = lese_tabelle(quelle)
        print("Vergleich %s: Version %d → aktuelle Datei (nicht eingecheckt)\n" %
              (dok, von["version"]))
    else:
        if len(versionen) < 2 and not args.von:
            raise ArchivFehler("Nur eine Version vorhanden – nichts zu vergleichen.")
        bis = version_waehlen(versionen, args.bis) if args.bis else versionen[-1]
        von = version_waehlen(versionen, args.von) if args.von else \
            versionen[bis["version"] - 2]
        alt = archiv.schnappschuss_laden(von.get("zellen_sha256"))
        neu = archiv.schnappschuss_laden(bis.get("zellen_sha256"))
        print("Vergleich %s: Version %d → Version %d\n" %
              (dok, von["version"], bis["version"]))
    if alt is None or neu is None:
        raise ArchivFehler("Für mindestens eine Version ist kein Zellabbild vorhanden.")
    nb, wb = blattaenderungen(alt, neu)
    for b in nb:
        print("+ Blatt neu: %s" % b)
    for b in wb:
        print("- Blatt entfernt: %s" % b)
    aend = vergleiche(alt, neu)
    zeige_aenderungen(aend)
    z = zaehle(aend)
    print("\n%d geändert, %d neu, %d gelöscht" % (z["geaendert"], z["neu"], z["geloescht"]))
    return 0


def befehl_pruefen(args):
    archiv = archiv_holen(args)
    print("Prüfe Archiv %s …" % archiv.wurzel)
    fehler, hinweise, kopf, anzahl, zs_ok = pruefe_archiv(archiv)
    print("  %d Einträge geprüft, %d mit gültigem Zeitstempel." % (anzahl, zs_ok))
    for h in hinweise:
        print("  Hinweis: %s" % h)
    if fehler:
        print("\n✘ PRÜFUNG FEHLGESCHLAGEN – %d Problem(e):" % len(fehler))
        for f in fehler:
            print("  - %s" % f)
        return 2
    print("\n✔ Archiv unversehrt. Kopf-Hash: %s" % kopf)
    return 0


def befehl_wiederherstellen(args):
    archiv = archiv_holen(args)
    dok = dokument_aufloesen(archiv, args.dokument)
    e = version_waehlen(archiv.versionen(dok), args.version)
    ziel = args.ziel
    if not ziel:
        stamm, ext = os.path.splitext(dok)
        ziel = "%s (Version %d)%s" % (stamm, e["version"], ext)
    if os.path.isdir(ziel):
        stamm, ext = os.path.splitext(dok)
        ziel = os.path.join(ziel, "%s (Version %d)%s" % (stamm, e["version"], ext))
    if os.path.exists(ziel):
        raise ArchivFehler("Ziel existiert bereits – nichts überschrieben: %s" % ziel)
    quelle = archiv.objektpfad(e["datei_sha256"])
    if sha256_datei(quelle) != e["datei_sha256"]:
        raise ArchivFehler("Gesicherte Datei ist beschädigt – 'pruefen' ausführen.")
    shutil.copyfile(quelle, ziel)
    os.chmod(ziel, 0o644)
    print("✔ Version %d von %s wiederhergestellt: %s" % (e["version"], dok,
                                                        os.path.abspath(ziel)))
    return 0


def befehl_web(args):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import tabularium_web
    return tabularium_web.starten(args.archiv, args.port, not args.kein_browser)


def befehl_zeitstempel(args):
    archiv = archiv_holen(args)
    nachgeholt = 0
    for e in archiv.eintraege():
        if not os.path.exists(archiv.zeitstempelpfad(e["hash"])):
            try:
                info = zeitstempel_holen(archiv, e["hash"])
                print("⏱ %s v%d: %s" % (e["dokument"], e["version"], info))
                nachgeholt += 1
            except Exception as ex:
                print("✘ %s v%d: %s" % (e["dokument"], e["version"], ex))
                return 1
    if not nachgeholt:
        print("Alle Einträge haben bereits einen Zeitstempel.")
    else:
        print("Hinweis: Nachgeholte Stempel belegen nur den Stand ab heute.")
    return 0


def befehl_einstellungen(args):
    archiv = archiv_holen(args, anlegen=True)
    e = archiv.einstellungen()
    geaendert = False
    if args.zeitstempel:
        e["zeitstempel"] = args.zeitstempel == "an"
        geaendert = True
    if args.tsa_url:
        e["tsa_url"] = args.tsa_url
        geaendert = True
    if args.tsa_ca:
        e["tsa_ca"] = os.path.abspath(args.tsa_ca)
        geaendert = True
    if args.tsa_zertifikat:
        e["tsa_zertifikat"] = os.path.abspath(args.tsa_zertifikat)
        geaendert = True
    if geaendert:
        archiv.einstellungen_speichern(e)
        print("Einstellungen gespeichert.")
    for k, v in e.items():
        print("  %-15s %s" % (k, v))
    if e["zeitstempel"] and "freetsa.org" in e["tsa_url"]:
        print("\nHinweis: FreeTSA ist kostenlos, aber kein qualifizierter "
              "Vertrauensdienst nach eIDAS. An die Zeitstempelstelle geht nur der "
              "SHA-256-Hash, nie der Dateiinhalt.")
    return 0


def befehl_ueberwachen(args):
    ordner = os.path.abspath(args.ordner)
    if not os.path.isdir(ordner):
        raise ArchivFehler("Ordner nicht gefunden: %s" % ordner)
    archiv = archiv_holen(args, anlegen=True, start=None if args.archiv else ordner)
    print("Überwache %s (alle %ds, %s). Beenden mit Ctrl+C." %
          (ordner, args.intervall, "mit Unterordnern" if args.rekursiv else "ohne Unterordner"))

    def kandidaten():
        for wurzel, dirs, dateien in os.walk(ordner):
            dirs[:] = [d for d in dirs if not d.startswith(".")] if args.rekursiv else []
            for d in dateien:
                if d.startswith((".", "~$")):
                    continue
                if os.path.splitext(d)[1].lower() in ALLE_FORMATE:
                    yield os.path.join(wurzel, d)

    stand, wartend = {}, {}
    try:
        while True:
            for p in kandidaten():
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                sig = (st.st_mtime, st.st_size)
                if stand.get(p) != sig:
                    stand[p] = sig
                    wartend[p] = sig
                elif wartend.get(p) == sig:
                    del wartend[p]
                    try:
                        e = einchecken_datei(archiv, p, name=dokumentname_fuer(archiv, p),
                                         notiz="automatisch (Ordnerüberwachung)", leise=True)
                        if e:
                            print("  [%s]" % time.strftime("%H:%M:%S"))
                    except ArchivFehler as ex:
                        print("✘ %s: %s" % (p, ex))
            time.sleep(args.intervall)
    except KeyboardInterrupt:
        print("\nÜberwachung beendet.")
    return 0


# --------------------------------------------------------------------------
# HTML-Prüfbericht
# --------------------------------------------------------------------------

BERICHT_CSS = """
body{font:14px/1.45 -apple-system,"Helvetica Neue",Arial,sans-serif;color:#1d2330;
max-width:1100px;margin:32px auto;padding:0 24px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:32px 0 8px;
border-bottom:1px solid #d5d9e0;padding-bottom:4px}h3{font-size:15px;margin:22px 0 6px}
.meta{color:#5b6475;margin-bottom:18px}
.ok,.fail{padding:12px 16px;border-radius:6px;margin:14px 0;font-weight:600}
.ok{background:#e7f5ec;color:#145a32;border:1px solid #a9dcbc}
.fail{background:#fdecec;color:#8a1c1c;border:1px solid #f2b5b5}
table{border-collapse:collapse;width:100%;margin:6px 0 10px;font-size:13px}
th,td{border:1px solid #d5d9e0;padding:5px 8px;text-align:left;vertical-align:top}
th{background:#f3f5f8;font-weight:600}table.aend{table-layout:fixed}
table.aend td{overflow-wrap:anywhere}
td.mono,.mono{font-family:"SF Mono",Menlo,monospace;font-size:11.5px;word-break:break-all}
tr.neu td:first-child{border-left:3px solid #2e9d57}
tr.geaendert td:first-child{border-left:3px solid #d49a13}
tr.geloescht td:first-child{border-left:3px solid #c0392b}
.formel{color:#5b6475;font-family:Menlo,monospace;font-size:11.5px}
.klein{font-size:12px;color:#5b6475}
@media print{body{margin:0;max-width:none}h2{break-after:avoid}tr{break-inside:avoid}}
"""


def _zelle_html(inhalt):
    if inhalt is None:
        return "<span class='klein'>–</span>"
    wert, formel = inhalt
    s = html.escape(str(wert)).replace("\n", "<br>")
    if formel:
        s += "<br><span class='formel'>%s</span>" % html.escape(formel)
    return s


def bericht_html(archiv, dok, erstfassung=False, grenze=1000):
    """Liefert (html_text, fehlerliste) des Prüfberichts für ein Dokument."""
    versionen = archiv.versionen(dok)
    fehler, hinweise, kopf, anzahl, zs_ok = pruefe_archiv(archiv)
    eigene = {e["hash"] for e in versionen}
    teile = []
    w = teile.append
    w("<!doctype html><html lang='de'><head><meta charset='utf-8'>")
    w("<meta name='viewport' content='width=device-width,initial-scale=1'>")
    w("<title>Prüfbericht – %s</title><style>%s</style></head><body>" %
      (html.escape(dok), BERICHT_CSS))
    w("<h1>Prüfbericht: %s</h1>" % html.escape(dok))
    w("<div class='meta'>Erstellt am %s mit %s %s · Archiv: <span class='mono'>%s</span></div>" %
      (zeit_lesbar(jetzt()), PROGRAMM, VERSION, html.escape(kurzpfad(archiv.wurzel))))
    if fehler:
        w("<div class='fail'>✘ Integritätsprüfung fehlgeschlagen (%d Problem(e))</div><ul>" % len(fehler))
        for f in fehler:
            w("<li>%s</li>" % html.escape(f))
        w("</ul>")
    else:
        w("<div class='ok'>✔ Integritätsprüfung bestanden: %d Journaleinträge, Hash-Kette "
          "lückenlos, alle gesicherten Dateien unverändert, %d gültige Zeitstempel.</div>" %
          (anzahl, zs_ok))
    for h in hinweise:
        w("<p class='klein'>Hinweis: %s</p>" % html.escape(h))

    w("<h2>Versionen</h2><table><tr><th>Version</th><th>Gesichert am</th>"
      "<th>Benutzer</th><th>Änderungen</th><th>Notiz</th><th>Zeitstempel (TSA)</th></tr>")
    for e in versionen:
        z = e.get("aenderungen")
        if z is None:
            aend = "Zellen nicht lesbar"
        elif e["version"] == 1:
            aend = "Erstfassung, %d Zellen" % (e.get("anzahl_zellen") or 0)
        else:
            aend = "%d geändert, %d neu, %d gelöscht" % (z["geaendert"], z["neu"], z["geloescht"])
        ok, info = zeitstempel_pruefen(archiv, e["hash"])
        zs = html.escape(info) if ok else ("ungültig: " + html.escape(info) if ok is False else "–")
        wer = e.get("nutzer", "")
        if e.get("bearbeiter"):
            wer = "%s (%s)" % (e["bearbeiter"], wer)
        w("<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" %
          (e["version"], zeit_lesbar(e["zeit"]), html.escape(wer), aend,
           html.escape(e.get("notiz") or ""), zs))
    w("</table>")

    w("<h2>Änderungen im Einzelnen</h2>")
    vorher_abbild = None
    for e in versionen:
        abbild = archiv.schnappschuss_laden(e.get("zellen_sha256"))
        w("<h3>Version %d – %s</h3>" % (e["version"], zeit_lesbar(e["zeit"])))
        w("<div class='klein'>Datei-SHA-256: <span class='mono'>%s</span> · %s Bytes · "
          "Eintrags-Hash: <span class='mono'>%s</span></div>" %
          (e["datei_sha256"], e.get("datei_bytes"), e["hash"]))
        if e.get("blaetter_neu") and e["version"] > 1:
            w("<p>Blatt neu: %s</p>" % html.escape(", ".join(e["blaetter_neu"])))
        if e.get("blaetter_entfernt"):
            w("<p>Blatt entfernt: %s</p>" % html.escape(", ".join(e["blaetter_entfernt"])))
        if abbild is None:
            w("<p class='klein'>Zellinhalt nicht lesbar%s.</p>" %
              (": " + html.escape(e["warnung"]) if e.get("warnung") else ""))
            continue
        if e["version"] == 1 and not erstfassung:
            w("<p class='klein'>Erstfassung mit %d Zellen (vollständiger Inhalt mit "
              "--erstfassung).</p>" % len(abbild["zellen"]))
        else:
            aend = vergleiche(vorher_abbild, abbild)
            if not aend:
                w("<p class='klein'>Keine Zelländerungen (nur Formatierung o. Ä.).</p>")
            else:
                w("<table class='aend'><colgroup><col style='width:16%'><col style='width:10%'>"
                  "<col style='width:37%'><col style='width:37%'></colgroup>"
                  "<tr><th>Zelle</th><th>Art</th><th>Vorher</th><th>Nachher</th></tr>")
                namen = {"neu": "neu", "geaendert": "geändert", "geloescht": "gelöscht"}
                for art, k, alt, neu in aend[:grenze]:
                    w("<tr class='%s'><td class='mono'>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" %
                      (art, html.escape(k), namen[art], _zelle_html(alt), _zelle_html(neu)))
                w("</table>")
                if len(aend) > grenze:
                    w("<p class='klein'>… %d weitere Änderungen nicht dargestellt "
                      "(--max erhöhen).</p>" % (len(aend) - grenze))
        vorher_abbild = abbild

    w("<h2>Hinweise zur Prüfung</h2><p class='klein'>Jede Fassung ist unverändert "
      "als Originaldatei abgelegt und über ihren SHA-256-Wert identifiziert. Die "
      "Journaleinträge sind über Hashwerte verkettet; jede nachträgliche Änderung, "
      "Löschung oder Einfügung bricht die Kette. Zeitstempel einer externen "
      "Zeitstempelstelle (RFC 3161) belegen, dass ein Eintrag samt aller vorherigen "
      "zum angegebenen Zeitpunkt existierte. Die Prüfung lässt sich jederzeit mit "
      "<span class='mono'>tabularium pruefen</span> wiederholen.</p>")
    w("<p class='klein'>Kopf-Hash des Journals zum Berichtszeitpunkt: "
      "<span class='mono'>%s</span></p>" % (kopf or "–"))
    if not eigene:
        w("<p>Keine Einträge.</p>")
    w("</body></html>")
    return "".join(teile), fehler


def befehl_bericht(args):
    archiv = archiv_holen(args)
    dok = dokument_aufloesen(archiv, args.dokument)
    text, fehler = bericht_html(archiv, dok, args.erstfassung, args.max)
    ziel = args.ausgabe or "Pruefbericht %s %s.html" % (
        os.path.splitext(dok)[0], datetime.date.today().isoformat())
    if os.path.exists(ziel) and not args.ueberschreiben:
        raise ArchivFehler("Datei existiert bereits: %s (--ueberschreiben)" % ziel)
    with open(ziel, "w", encoding="utf-8") as f:
        f.write(text)
    print("✔ Prüfbericht geschrieben: %s" % os.path.abspath(ziel))
    if args.oeffnen and sys.platform == "darwin":
        subprocess.run(["open", ziel])
    return 2 if fehler else 0


# --------------------------------------------------------------------------
# Kommandozeile
# --------------------------------------------------------------------------

def parser_bauen():
    p = argparse.ArgumentParser(
        prog="tabularium", add_help=False,
        description="%s %s – revisionssichere Ablage von Excel- und "
                    "LibreOffice-Tabellen mit Änderungsprotokoll." % (PROGRAMM, VERSION),
        epilog="Beispiele:\n"
               "  tabularium einchecken Kalkulation.xlsx --notiz \"Zahlen Q3\"\n"
               "  tabularium verlauf Kalkulation.xlsx --details\n"
               "  tabularium vergleich Kalkulation.xlsx --aktuell\n"
               "  tabularium pruefen\n"
               "  tabularium bericht Kalkulation.xlsx --oeffnen\n"
               "  tabularium ueberwachen ~/Tabellen\n",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-h", "--hilfe", "--help", action="help", help="Diese Hilfe anzeigen")
    p.add_argument("--archiv", help="Pfad zum Archiv (Standard: .tabularium im aktuellen "
                                    "oder einem übergeordneten Ordner)")
    p.add_argument("--version", action="version", version="%s %s" % (PROGRAMM, VERSION))
    sub = p.add_subparsers(dest="befehl", metavar="BEFEHL")

    def neu(name, hilfe, **kw):
        sp = sub.add_parser(name, help=hilfe, description=hilfe, add_help=False, **kw)
        sp.add_argument("-h", "--hilfe", "--help", action="help", help="Hilfe")
        return sp

    s = neu("einchecken", "Fassung einer oder mehrerer Tabellen sichern")
    s.add_argument("dateien", nargs="+", metavar="DATEI")
    s.add_argument("--notiz", "-n", help="Vermerk zur Fassung (Grund der Änderung)")
    s.add_argument("--bearbeiter", "-b", help="Name der bearbeitenden Person")
    s.add_argument("--name", help="Dokumentname im Archiv (Standard: Dateiname)")
    s.add_argument("--zeitstempel", choices=["an", "aus"],
                   help="Zeitstempel für diesen Vorgang erzwingen/abschalten")
    s.add_argument("--erzwingen", action="store_true",
                   help="auch einchecken, wenn unverändert")
    s.set_defaults(fn=befehl_einchecken)

    s = neu("liste", "Alle Dokumente im Archiv und ihren Stand zeigen")
    s.set_defaults(fn=befehl_liste)

    s = neu("verlauf", "Versionen eines Dokuments zeigen")
    s.add_argument("dokument")
    s.add_argument("--details", "-d", action="store_true", help="Zelländerungen je Version")
    s.set_defaults(fn=befehl_verlauf)

    s = neu("vergleich", "Zellen zweier Versionen vergleichen")
    s.add_argument("dokument")
    s.add_argument("von", nargs="?", help="Version, z. B. 2 oder v2 (Standard: vorletzte)")
    s.add_argument("bis", nargs="?", help="Version (Standard: letzte)")
    s.add_argument("--aktuell", nargs="?", const=True, metavar="DATEI",
                   help="mit der aktuellen, noch nicht eingecheckten Datei vergleichen")
    s.set_defaults(fn=befehl_vergleich)

    s = neu("pruefen", "Ganzes Archiv auf Manipulation prüfen")
    s.set_defaults(fn=befehl_pruefen)

    s = neu("wiederherstellen", "Eine frühere Fassung als Datei zurückholen")
    s.add_argument("dokument")
    s.add_argument("version")
    s.add_argument("ziel", nargs="?", help="Zieldatei oder -ordner")
    s.set_defaults(fn=befehl_wiederherstellen)

    s = neu("bericht", "HTML-Prüfbericht erstellen (druckbar, als PDF speicherbar)")
    s.add_argument("dokument")
    s.add_argument("--ausgabe", "-o", help="Zieldatei (.html)")
    s.add_argument("--oeffnen", action="store_true", help="danach im Browser öffnen")
    s.add_argument("--erstfassung", action="store_true",
                   help="vollständigen Inhalt der ersten Version aufführen")
    s.add_argument("--max", type=int, default=1000,
                   help="höchstens so viele Änderungen je Version (Standard 1000)")
    s.add_argument("--ueberschreiben", action="store_true")
    s.set_defaults(fn=befehl_bericht)

    s = neu("ueberwachen", "Ordner beobachten und jede gespeicherte Änderung einchecken")
    s.add_argument("ordner")
    s.add_argument("--intervall", type=int, default=5, help="Sekunden (Standard 5)")
    s.add_argument("--rekursiv", "-r", action="store_true", help="mit Unterordnern")
    s.set_defaults(fn=befehl_ueberwachen)

    s = neu("web", "Weboberfläche im Browser starten")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--kein-browser", action="store_true", help="Browser nicht öffnen")
    s.set_defaults(fn=befehl_web)

    s = neu("zeitstempel", "Fehlende Zeitstempel nachholen")
    s.set_defaults(fn=befehl_zeitstempel)

    s = neu("einstellungen", "Einstellungen anzeigen oder ändern")
    s.add_argument("--zeitstempel", choices=["an", "aus"])
    s.add_argument("--tsa-url", help="URL der Zeitstempelstelle (RFC 3161)")
    s.add_argument("--tsa-ca", help="CA-Zertifikat der Zeitstempelstelle (PEM)")
    s.add_argument("--tsa-zertifikat", help="Zertifikat der Zeitstempelstelle (PEM)")
    s.set_defaults(fn=befehl_einstellungen)
    return p


def main(argv=None):
    for strom in (sys.stdout, sys.stderr):      # Windows-Konsole: ✔ ⏱ → nicht abstürzen
        if strom is not None and hasattr(strom, "reconfigure"):
            try:
                strom.reconfigure(errors="replace")
            except (ValueError, OSError):
                pass
    p = parser_bauen()
    args = p.parse_args(argv)
    if not getattr(args, "fn", None):
        p.print_help()
        return 0
    try:
        return args.fn(args) or 0
    except ArchivFehler as e:
        print("✘ %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
