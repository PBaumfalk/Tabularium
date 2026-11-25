# -*- coding: utf-8 -*-
"""Tests für den Tabularium.  Aufruf:  python3 -m unittest discover tests"""
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import tabularium  # noqa: E402

FODS = """<?xml version="1.0" encoding="UTF-8"?>
<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
 xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
 xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0"
 xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2"
 office:version="1.3" office:mimetype="application/vnd.oasis.opendocument.spreadsheet">
<office:automatic-styles>
<number:date-style style:name="N1"><number:day/><number:text>.</number:text><number:month/><number:text>.</number:text><number:year number:style="long"/></number:date-style>
<style:style style:name="ce1" style:family="table-cell" style:data-style-name="N1"/>
</office:automatic-styles>
<office:body><office:spreadsheet>
<table:table table:name="Honorar">
<table:table-row><table:table-cell office:value-type="string"><text:p>Gebühr</text:p></table:table-cell>
<table:table-cell office:value-type="float" office:value="{b}"><text:p>{b}</text:p></table:table-cell></table:table-row>
<table:table-row><table:table-cell office:value-type="string"><text:p>Auslagen</text:p></table:table-cell>
<table:table-cell office:value-type="float" office:value="20"><text:p>20</text:p></table:table-cell></table:table-row>
<table:table-row><table:table-cell office:value-type="string"><text:p>Summe</text:p></table:table-cell>
<table:table-cell table:formula="of:=SUM([.B1:.B2])" office:value-type="float" office:value="{s}"><text:p>{s}</text:p></table:table-cell></table:table-row>
<table:table-row table:number-rows-repeated="1000"><table:table-cell table:number-columns-repeated="1024"/></table:table-row>
<table:table-row><table:table-cell table:style-name="ce1" office:value-type="date" office:date-value="{d}"><text:p>x</text:p></table:table-cell></table:table-row>
</table:table></office:spreadsheet></office:body></office:document>
"""


def entsperren(pfad):
    """Hebt die macOS-Schutzflags auf (auf Linux gibt es sie nicht)."""
    if shutil.which("chflags"):
        subprocess.run(["chflags", "-R", "nouchg,nouappnd", pfad])


def leise(fn, *a, **kw):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **kw)


class Basis(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="tabularium-test-")
        self.archiv = tabularium.Archiv.anlegen(self.dir)
        self.archiv.einstellungen_speichern(dict(tabularium.STANDARD_EINSTELLUNGEN))

    def tearDown(self):
        entsperren(self.dir)
        shutil.rmtree(self.dir, ignore_errors=True)

    def fods(self, name, b, s, d):
        pfad = os.path.join(self.dir, name)
        with open(pfad, "w", encoding="utf-8") as f:
            f.write(FODS.format(b=b, s=s, d=d))
        return pfad

    def entsperren(self):
        entsperren(self.archiv.wurzel)
        subprocess.run(["chmod", "-R", "u+w", self.archiv.wurzel])


class TestAuslesen(Basis):
    def test_fods_inhalt(self):
        abbild = tabularium.lese_tabelle(self.fods("a.fods", 100, 120, "2026-11-01"))
        z = abbild["zellen"]
        self.assertEqual(z["Honorar!A1"], ["Gebühr", None])
        self.assertEqual(z["Honorar!B3"], ["120", "=SUM([.B1:.B2])"])
        self.assertEqual(z["Honorar!A1004"], ["2026-11-01", None])   # nach 1000 Leerzeilen
        self.assertEqual(len(z), 7)

    def test_formelverschiebung(self):
        v = tabularium.verschiebe_formel
        self.assertEqual(v("SUM(A1:B2)", 0, 3), "SUM(A4:B5)")
        self.assertEqual(v("$A$1+A1", 1, 1), "$A$1+B2")
        self.assertEqual(v("LOG10(A1)&\"B2\"", 0, 2), "LOG10(A3)&\"B2\"")
        self.assertEqual(v("'Q1 2025'!A1", 0, 1), "'Q1 2025'!A2")

    def test_datumsformat_erkennung(self):
        self.assertTrue(tabularium._ist_datumscode("dd/mm/yyyy"))
        self.assertTrue(tabularium._ist_datumscode("[$-407]DD.MM.YYYY"))
        self.assertFalse(tabularium._ist_datumscode("#,##0.00 \"€\""))
        self.assertFalse(tabularium._ist_datumscode("General"))
        self.assertEqual(tabularium._seriell_zu_datum("46351", False), "2026-11-25")


class TestArchiv(Basis):
    def test_versionen_und_vergleich(self):
        p = self.fods("Honorar.fods", 100, 120, "2026-11-01")
        e1 = leise(tabularium.einchecken_datei, self.archiv, p, notiz="eins")
        self.assertEqual(e1["version"], 1)
        self.assertIsNone(leise(tabularium.einchecken_datei, self.archiv, p))  # unverändert
        self.fods("Honorar.fods", 150, 170, "2026-11-25")
        e2 = leise(tabularium.einchecken_datei, self.archiv, p)
        self.assertEqual(e2["version"], 2)
        self.assertEqual(e2["aenderungen"], {"neu": 0, "geaendert": 3, "geloescht": 0})
        fehler, _, kopf, anzahl, _ = tabularium.pruefe_archiv(self.archiv)
        self.assertEqual(fehler, [])
        self.assertEqual(kopf, e2["hash"])
        self.assertEqual(anzahl, 2)

    @unittest.skipUnless(hasattr(os, "chflags") and sys.platform == "darwin", "nur macOS")
    def test_schutzflags(self):
        p = self.fods("Honorar.fods", 100, 120, "2026-11-01")
        e = leise(tabularium.einchecken_datei, self.archiv, p)
        with self.assertRaises(OSError):
            os.remove(self.archiv.objektpfad(e["datei_sha256"]))
        with self.assertRaises(OSError):
            open(self.archiv.journal, "r+").write("x")

    def _zwei_versionen(self):
        p = self.fods("Honorar.fods", 100, 120, "2026-11-01")
        leise(tabularium.einchecken_datei, self.archiv, p)
        self.fods("Honorar.fods", 150, 170, "2026-11-25")
        return leise(tabularium.einchecken_datei, self.archiv, p)

    def test_manipulation_journal_wert(self):
        self._zwei_versionen()
        self.entsperren()
        with open(self.archiv.journal, encoding="utf-8") as f:
            zeilen = f.readlines()
        zeilen[0] = zeilen[0].replace('"version": 1', '"version": 1 ', 1).replace(
            '"notiz": null', '"notiz": "nachträglich"')
        with open(self.archiv.journal, "w", encoding="utf-8") as f:
            f.writelines(zeilen)
        fehler = tabularium.pruefe_archiv(self.archiv)[0]
        self.assertTrue(any("nachträglich verändert" in f for f in fehler), fehler)

    def test_manipulation_eintrag_geloescht(self):
        self._zwei_versionen()
        self.entsperren()
        with open(self.archiv.journal, encoding="utf-8") as f:
            zeilen = f.readlines()
        with open(self.archiv.journal, "w", encoding="utf-8") as f:
            f.writelines(zeilen[1:])
        fehler = tabularium.pruefe_archiv(self.archiv)[0]
        self.assertTrue(any("Kette unterbrochen" in f for f in fehler), fehler)

    def test_manipulation_datei(self):
        e = self._zwei_versionen()
        self.entsperren()
        with open(self.archiv.objektpfad(e["datei_sha256"]), "ab") as f:
            f.write(b"x")
        fehler = tabularium.pruefe_archiv(self.archiv)[0]
        self.assertTrue(any("gesicherte Datei wurde verändert" in f for f in fehler), fehler)

    def test_unlesbare_datei_wird_trotzdem_gesichert(self):
        p = os.path.join(self.dir, "kaputt.xlsx")
        with open(p, "wb") as f:
            f.write(b"kein zip")
        e = leise(tabularium.einchecken_datei, self.archiv, p)
        self.assertIsNone(e["zellen_sha256"])
        self.assertIn("nicht lesbar", e["warnung"])
        self.assertEqual(tabularium.pruefe_archiv(self.archiv)[0], [])


@unittest.skipUnless(tabularium.finde_soffice(), "LibreOffice nicht installiert")
class TestFormate(Basis):
    def test_ods_xlsx_xls_gleiches_ergebnis(self):
        quelle = self.fods("q.fods", 100, 120, "2026-11-01")
        ergebnisse = {}
        for fmt in ("ods", "xlsx", "xls"):
            out = os.path.join(self.dir, fmt)
            os.makedirs(out)
            profil = tempfile.mkdtemp()
            subprocess.run([tabularium.finde_soffice(), "-env:UserInstallation=file://" + profil,
                            "--headless", "--convert-to", fmt, "--outdir", out, quelle],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            shutil.rmtree(profil, ignore_errors=True)
            z = tabularium.lese_tabelle(os.path.join(out, "q." + fmt))["zellen"]
            ergebnisse[fmt] = {k: v[0] for k, v in z.items()}
        self.assertEqual(ergebnisse["ods"], ergebnisse["xlsx"])
        self.assertEqual(ergebnisse["xlsx"], ergebnisse["xls"])
        self.assertEqual(ergebnisse["xlsx"]["Honorar!A1004"], "2026-11-01")


if __name__ == "__main__":
    unittest.main()
