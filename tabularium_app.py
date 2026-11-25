#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Startpunkt der installierbaren App (macOS: Tabularium.app, Windows: Tabularium.exe).

Ablauf bei Doppelklick:
  - Läuft Tabularium schon (für dieses Benutzerkonto), öffnet sich nur der Browser.
  - Sonst startet der Server. Auf dem Mac als eigenständiger Hintergrundprozess, damit
    ein erneuter Doppelklick wieder hier ankommt (Apps ohne Fenster bekämen ihn sonst
    nicht mit).

Schalter:
  --hintergrund   Server ohne Browser starten (Autostart bei der Anmeldung)
  --server        intern: Server im Vordergrund dieses Prozesses
  --selbsttest    Prüft die fertige App ohne Browser und beendet sich (für die CI)
"""

import os
import subprocess
import sys
import tempfile
import time
import traceback
import webbrowser


def logdatei():
    if sys.platform == "darwin":
        ordner = os.path.expanduser("~/Library/Logs/Tabularium")
    elif os.name == "nt":
        ordner = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                              "Tabularium")
    else:
        ordner = os.path.expanduser("~/.local/state/tabularium")
    os.makedirs(ordner, exist_ok=True)
    pfad = os.path.join(ordner, "tabularium.log")
    if os.path.exists(pfad) and os.path.getsize(pfad) > 2 * 1024 * 1024:
        os.replace(pfad, pfad + ".1")
    return pfad


def ausgabe_ins_log():
    """Fenster-Apps haben keine Konsole: Ausgaben in eine Logdatei schreiben."""
    f = open(logdatei(), "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = f
    print("\n--- %s ---" % time.strftime("%Y-%m-%d %H:%M:%S"))


def fehler_melden(text):
    """Letzter Ausweg, wenn der Start scheitert: sichtbare Meldung."""
    print(text)
    try:
        if sys.platform == "darwin":
            subprocess.run(["osascript", "-e",
                            'display alert "Tabularium konnte nicht starten" message "%s"'
                            % text.replace('"', "'")])
        elif os.name == "nt":
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, text, "Tabularium", 0x10)
    except Exception:
        pass


def server_starten(browser):
    import tabularium_web
    return tabularium_web.starten(browser=browser)


def doppelklick():
    import tabularium_web
    url = tabularium_web.laeuft_auf()
    if url:
        webbrowser.open(url)
        return 0
    if sys.platform != "darwin":
        return server_starten(browser=True)
    # macOS: Server abkoppeln, damit diese App sofort endet
    log = open(logdatei(), "a", encoding="utf-8")
    befehl = [sys.executable, "--server"] if getattr(sys, "frozen", False) else \
        [sys.executable, os.path.abspath(__file__), "--server"]
    subprocess.Popen(befehl, stdout=log, stderr=log,
                     stdin=subprocess.DEVNULL, start_new_session=True,
                     close_fds=True)
    for _ in range(100):                      # bis zu 20 Sekunden warten
        time.sleep(0.2)
        url = tabularium_web.laeuft_auf()
        if url:
            webbrowser.open(url)
            return 0
    fehler_melden("Der Server hat nicht geantwortet. Details stehen in %s" % logdatei())
    return 1


# --------------------------------------------------------------------------
# Selbsttest der fertigen App
# --------------------------------------------------------------------------

FODS = """<?xml version="1.0" encoding="UTF-8"?>
<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
 xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2" office:version="1.3"
 office:mimetype="application/vnd.oasis.opendocument.spreadsheet">
<office:body><office:spreadsheet><table:table table:name="Test">
<table:table-row><table:table-cell office:value-type="string"><text:p>Größe</text:p></table:table-cell>
<table:table-cell office:value-type="float" office:value="{b}"><text:p>{b}</text:p></table:table-cell>
<table:table-cell table:formula="of:=[.B1]*2" office:value-type="float" office:value="{s}"><text:p>{s}</text:p></table:table-cell>
</table:table-row></table:table></office:spreadsheet></office:body></office:document>
"""


def _xlsx(pfad):
    """Kleinste gültige xlsx-Datei mit Text, Zahl und Formel."""
    import zipfile
    teile = {
        "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
        "_rels/.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        "xl/workbook.xml": '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Blatt1" sheetId="1" r:id="rId1"/></sheets></workbook>',
        "xl/_rels/workbook.xml.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
        "xl/worksheets/sheet1.xml": '<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Größe</t></is></c><c r="B1"><v>7</v></c><c r="C1"><f>B1*2</f><v>14</v></c></row></sheetData></worksheet>',
    }
    with zipfile.ZipFile(pfad, "w") as z:
        for name, inhalt in teile.items():
            z.writestr(name, inhalt)


def selbsttest():
    import json
    import threading
    import urllib.request

    tmp = tempfile.mkdtemp(prefix="tabularium-selbsttest-")
    os.environ["TABULARIUM_KONFIG"] = os.path.join(tmp, "konfig.json")
    import tabularium
    import tabularium_web

    server = tabularium_web.LokalerServer(("127.0.0.1", 0), tabularium_web.Handler)
    port = server.server_address[1]
    z = tabularium_web.Zustand(os.path.join(tmp, "archiv"), port)
    tabularium_web.Handler.z = z
    threading.Thread(target=server.serve_forever, daemon=True).start()
    basis = "http://127.0.0.1:%d" % port

    def anfrage(pfad, daten=None):
        kopf = {"X-Tabularium-Token": z.token}
        body = None
        if daten is not None:
            body = json.dumps(daten).encode()
            kopf["Content-Type"] = "application/json"
        with tabularium_web._DIREKT.open(urllib.request.Request(basis + pfad, body, kopf)) as r:
            inhalt = r.read()
        return json.loads(inhalt) if r.headers.get_content_type() == "application/json" \
            else inhalt.decode("utf-8")

    def schritt(text, bedingung):
        print(("  ✔ " if bedingung else "  ✘ ") + text)
        if not bedingung:
            raise AssertionError(text)

    print("Tabularium %s – Selbsttest (%s, Python %s)" % (
        tabularium.VERSION, tabularium_web.SYSTEM, sys.version.split()[0]))
    seite = anfrage("/")
    schritt("Oberfläche ausgeliefert", "Tabularium" in seite and z.token in seite)
    for datei in ("/app.js", "/style.css", "/favicon.svg"):
        schritt("%s vorhanden" % datei, len(anfrage(datei)) > 100)

    fods = os.path.join(tmp, "Liste.fods")
    with open(fods, "w", encoding="utf-8") as f:
        f.write(FODS.format(b=7, s=14))
    r = anfrage("/api/einchecken", {"pfade": [fods], "notiz": "Selbsttest"})
    schritt("ods/fods eingecheckt", r["ergebnisse"][0].get("version") == 1)
    with open(fods, "w", encoding="utf-8") as f:
        f.write(FODS.format(b=8, s=16))
    r = anfrage("/api/einchecken", {"pfade": [fods]})
    schritt("zweite Fassung erkannt", r["ergebnisse"][0].get("version") == 2)
    v = anfrage("/api/vergleich?name=Liste.fods")
    schritt("Zellvergleich (2 geändert)", v["zaehlung"]["geaendert"] == 2)

    xlsx = os.path.join(tmp, "Tabelle.xlsx")
    _xlsx(xlsx)
    r = anfrage("/api/einchecken", {"pfade": [xlsx]})
    zellen = tabularium.lese_tabelle(xlsx)["zellen"]
    schritt("xlsx gelesen (Umlaut, Formel)", r["ergebnisse"][0].get("version") == 1 and
            zellen.get("Blatt1!A1") == ["Größe", None] and
            zellen.get("Blatt1!C1") == ["14", "=B1*2"])

    roh = tabularium.tsa_anfrage("ab" * 32, 12345)
    schritt("Zeitstempel-Anfrage erzeugt", roh[0] == 0x30 and len(roh) == 63)
    pr = anfrage("/api/pruefen", {})
    schritt("Archivprüfung bestanden", pr["ok"] and pr["anzahl"] == 3)
    schritt("Prüfbericht erzeugt",
            "Integritätsprüfung bestanden" in anfrage("/api/bericht?name=Liste.fods"))
    st = anfrage("/api/status")
    schritt("Status meldet App-Modus und Version",
            st["version"] == tabularium.VERSION and "app" in st)
    anfrage("/api/beenden", {})
    time.sleep(0.5)
    print("Selbsttest bestanden.")
    return 0


def main():
    for strom in (sys.stdout, sys.stderr):      # Windows-Konsole: ✔ ✘ nicht abstürzen lassen
        if strom is not None and hasattr(strom, "reconfigure"):
            try:
                strom.reconfigure(errors="replace")
            except (ValueError, OSError):
                pass
    args = [a for a in sys.argv[1:] if not a.startswith("-psn_")]
    if "--selbsttest" in args:
        if sys.stdout is None:                 # Windows-Fenster-App ohne Konsole
            ausgabe_ins_log()
        try:
            return selbsttest()
        except Exception:
            traceback.print_exc()
            return 1
    if getattr(sys, "frozen", False):
        ausgabe_ins_log()
    try:
        if "--server" in args:
            return server_starten(browser=False)
        if "--hintergrund" in args:
            return server_starten(browser=False)
        return doppelklick()
    except Exception:
        traceback.print_exc()
        fehler_melden("Unerwarteter Fehler. Details stehen in %s" % logdatei())
        return 1


if __name__ == "__main__":
    sys.exit(main())
