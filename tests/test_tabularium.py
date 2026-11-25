# -*- coding: utf-8 -*-
"""Tests für den Tabularium.  Aufruf:  python3 -m unittest discover tests"""
import contextlib
import io
import os
import shutil
import stat
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
    """Hebt Schutzflags (macOS) und Schreibschutz (alle Systeme) auf."""
    if shutil.which("chflags"):
        subprocess.run(["chflags", "-R", "nouchg,nouappnd", pfad])
    for wurzel, dirs, dateien in os.walk(pfad):
        for n in dirs + dateien:
            try:
                os.chmod(os.path.join(wurzel, n), stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
            except OSError:
                pass


def wegraeumen(pfad):
    entsperren(pfad)
    shutil.rmtree(pfad, ignore_errors=True)


def leise(fn, *a, **kw):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **kw)


class Basis(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="tabularium-test-")
        self.archiv = tabularium.Archiv.anlegen(self.dir)
        self.archiv.einstellungen_speichern(dict(tabularium.STANDARD_EINSTELLUNGEN))

    def tearDown(self):
        wegraeumen(self.dir)

    def fods(self, name, b, s, d):
        pfad = os.path.join(self.dir, name)
        with open(pfad, "w", encoding="utf-8") as f:
            f.write(FODS.format(b=b, s=s, d=d))
        return pfad

    def entsperren(self):
        entsperren(self.archiv.wurzel)


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


class TestZeitstempel(unittest.TestCase):
    """Echte Antwort von FreeTSA (tests/daten/freetsa.tsr) – ohne Netz und ohne OpenSSL."""
    HASH = "6a4583b3e22470e4da2b641eceedaa102d876cce4acbd34b554c23872d75f918"

    def test_antwort_lesen(self):
        with open(os.path.join(HIER, "daten", "freetsa.tsr"), "rb") as f:
            info = tabularium.tsa_info(f.read())
        self.assertEqual(info["status"], 0)
        self.assertEqual(info["hash"], self.HASH)
        self.assertEqual(info["algorithmus"], tabularium._OID_SHA256)
        self.assertEqual(info["zeit"].strftime("%Y-%m-%d %H:%M:%S"), "2026-11-25 20:32:42")
        self.assertTrue(info["nonce"])

    def test_anfrage_aufbau(self):
        roh = tabularium.tsa_anfrage("ab" * 32, 0x1234567890ABCDEF)
        t, s, e = tabularium._der_lesen(roh, 0)
        self.assertEqual((t, e), (0x30, len(roh)))
        teile = tabularium._der_kinder(roh, s, e)
        self.assertEqual([x[0] for x in teile], [0x02, 0x30, 0x02, 0x01])
        self.assertEqual(roh[teile[2][1]:teile[2][2]], bytes.fromhex("1234567890abcdef"))
        self.assertIn(bytes.fromhex("ab" * 32), roh)

    def test_ganzzahl_mit_hohem_bit(self):
        self.assertEqual(tabularium._der_int(255), b"\x02\x02\x00\xff")
        self.assertEqual(tabularium._der_int(127), b"\x02\x01\x7f")


class TestDokumentname(Basis):
    def test_gleicher_name_anderer_ordner(self):
        a = os.path.join(self.dir, "a")
        b = os.path.join(self.dir, "b")
        os.makedirs(a)
        os.makedirs(b)
        pa = os.path.join(a, "Liste.fods")
        pb = os.path.join(b, "Liste.fods")
        for p in (pa, pb):
            with open(p, "w", encoding="utf-8") as f:
                f.write(FODS.format(b=1, s=2, d="2026-01-01"))
        leise(tabularium.einchecken_datei, self.archiv, pa,
              name=tabularium.dokumentname_fuer(self.archiv, pa))
        self.assertEqual(tabularium.dokumentname_fuer(self.archiv, pa), "Liste.fods")
        self.assertEqual(tabularium.dokumentname_fuer(self.archiv, pb), "Liste.fods (b)")


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
