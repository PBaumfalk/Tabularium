#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weboberfläche für den Tabularium.

Startet einen kleinen Server, der nur auf diesem Rechner erreichbar ist
(127.0.0.1), und öffnet die Oberfläche im Browser. Jede Anfrage braucht das
Sitzungstoken, das in die Seite eingebettet wird; fremde Webseiten können den
Server dadurch nicht fernsteuern.

Start:  python3 tabularium.py web     (oder Doppelklick auf Tabularium.command)
"""

import collections
import getpass
import hashlib
import json
import plistlib
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
import socketserver
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import tabularium

# In der fertigen App (PyInstaller) liegen die Dateien unter sys._MEIPASS
HIER = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(HIER, "web")
KONFIG = os.environ.get("TABULARIUM_KONFIG") or os.path.expanduser("~/.tabularium.json")
STANDARD_ORDNER = os.path.expanduser("~/Tabularium")
STANDARD_PORT = 8765
MAX_UPLOAD = 300 * 1024 * 1024
MAX_ZEILEN = 5000
STATISCH = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/favicon.svg": ("favicon.svg", "image/svg+xml"),
}
UPLOAD_QUELLE = "(hochgeladen über die Weboberfläche)"


def konfig_laden():
    try:
        with open(KONFIG, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def konfig_speichern(daten):
    k = konfig_laden()
    k.update(daten)
    with open(KONFIG, "w", encoding="utf-8") as f:
        json.dump(k, f, ensure_ascii=False, indent=2)


# --------------------------------------------------------------------------
# Betriebssystem: Dialoge, Dateimanager, Autostart
# --------------------------------------------------------------------------

SYSTEM = "mac" if sys.platform == "darwin" else "windows" if os.name == "nt" else "linux"
OHNE_FENSTER = tabularium.OHNE_FENSTER
DATEIMANAGER = {"mac": "Finder", "windows": "Explorer", "linux": "Dateimanager"}[SYSTEM]
_ENDUNGEN = ";".join("*" + e for e in sorted(tabularium.ALLE_FORMATE))


def app_modus():
    """True, wenn Tabularium als fertige App (PyInstaller) läuft."""
    return bool(getattr(sys, "frozen", False))


def osascript(skript):
    """Führt AppleScript aus; None bei Abbruch durch den Nutzer."""
    r = subprocess.run(["osascript", "-e", skript], stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, universal_newlines=True)
    if r.returncode != 0:
        if "-128" in r.stderr:          # Abbrechen gedrückt
            return None
        raise tabularium.ArchivFehler("Dialog fehlgeschlagen: %s" % r.stderr.strip())
    return r.stdout


def powershell(skript):
    """Führt ein PowerShell-Skript aus (Windows-Dialoge); liefert UTF-8-Text."""
    skript = "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8\n" + skript
    r = subprocess.run(["powershell", "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass",
                        "-Command", skript],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, **OHNE_FENSTER)
    if r.returncode != 0:
        raise tabularium.ArchivFehler("Dialog fehlgeschlagen: %s" %
                                      r.stderr.decode("utf-8", "replace").strip())
    return r.stdout.decode("utf-8", "replace")


def _ps(text):
    return "'" + text.replace("'", "''") + "'"


def zenity(argumente):
    if not shutil.which("zenity"):
        raise tabularium.ArchivFehler("Dateiauswahl ist hier nicht verfügbar – bitte die "
                                      "Datei in das Feld ziehen.")
    r = subprocess.run(["zenity"] + argumente, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, universal_newlines=True)
    return r.stdout if r.returncode == 0 else None


def datei_dialog(titel):
    """Systemdialog zur Dateiauswahl -> Liste von Pfaden (leer bei Abbruch)."""
    if SYSTEM == "mac":
        aus = osascript(
            'tell me to activate\n'
            'set fs to choose file with prompt "%s" with multiple selections allowed\n'
            'set out to ""\n'
            'repeat with f in fs\n'
            'set out to out & POSIX path of f & linefeed\n'
            'end repeat\n'
            'return out' % titel.replace('"', ""))
    elif SYSTEM == "windows":
        aus = powershell(
            "Add-Type -AssemblyName System.Windows.Forms\n"
            "$f = New-Object System.Windows.Forms.Form -Property @{TopMost = $true}\n"
            "$d = New-Object System.Windows.Forms.OpenFileDialog\n"
            "$d.Multiselect = $true\n"
            "$d.Title = %s\n"
            "$d.Filter = %s\n"
            "if ($d.ShowDialog($f) -eq [System.Windows.Forms.DialogResult]::OK) "
            "{ $d.FileNames -join \"`n\" }" %
            (_ps(titel), _ps("Tabellen|%s|Alle Dateien|*.*" % _ENDUNGEN)))
    else:
        aus = zenity(["--file-selection", "--multiple", "--separator=\n", "--title", titel])
    return [p.strip() for p in (aus or "").splitlines() if p.strip()]


def ordner_dialog(titel):
    """Systemdialog zur Ordnerauswahl -> Pfad oder None."""
    if SYSTEM == "mac":
        aus = osascript('tell me to activate\n'
                        'return POSIX path of (choose folder with prompt "%s")' %
                        titel.replace('"', ""))
    elif SYSTEM == "windows":
        aus = powershell(
            "Add-Type -AssemblyName System.Windows.Forms\n"
            "$f = New-Object System.Windows.Forms.Form -Property @{TopMost = $true}\n"
            "$d = New-Object System.Windows.Forms.FolderBrowserDialog\n"
            "$d.Description = %s\n"
            "if ($d.ShowDialog($f) -eq [System.Windows.Forms.DialogResult]::OK) "
            "{ $d.SelectedPath }" % _ps(titel))
    else:
        aus = zenity(["--file-selection", "--directory", "--title", titel])
    aus = (aus or "").strip()
    if not aus:
        return None
    return aus.rstrip("/") if len(aus) > 1 else aus


def im_dateimanager_zeigen(pfad):
    if SYSTEM == "mac":
        subprocess.run(["open", "-R", pfad])
    elif SYSTEM == "windows":
        subprocess.run(["explorer", "/select,", pfad])
    else:
        subprocess.run(["xdg-open", os.path.dirname(pfad)])


AUTOSTART_NAME = "de.tabularium.app"


def _autostart_plist():
    return os.path.expanduser("~/Library/LaunchAgents/%s.plist" % AUTOSTART_NAME)


def autostart_aktiv():
    if not app_modus():
        return None
    if SYSTEM == "mac":
        return os.path.exists(_autostart_plist())
    if SYSTEM == "windows":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Run") as k:
                winreg.QueryValueEx(k, "Tabularium")
                return True
        except OSError:
            return False
    return None


def autostart_setzen(an):
    """Startet Tabularium bei der Anmeldung im Hintergrund (ohne Browser)."""
    if not app_modus() or SYSTEM == "linux":
        raise tabularium.ArchivFehler("Autostart gibt es nur in der installierten App.")
    if SYSTEM == "mac":
        pfad = _autostart_plist()
        if an:
            os.makedirs(os.path.dirname(pfad), exist_ok=True)
            with open(pfad, "wb") as f:
                plistlib.dump({"Label": AUTOSTART_NAME,
                               "ProgramArguments": [sys.executable, "--hintergrund"],
                               "RunAtLoad": True}, f)
        elif os.path.exists(pfad):
            os.remove(pfad)
    else:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                            winreg.KEY_SET_VALUE) as k:
            if an:
                winreg.SetValueEx(k, "Tabularium", 0, winreg.REG_SZ,
                                  '"%s" --hintergrund' % sys.executable)
            else:
                try:
                    winreg.DeleteValue(k, "Tabularium")
                except OSError:
                    pass


def kandidaten(ordner, rekursiv):
    for wurzel, dirs, dateien in os.walk(ordner):
        dirs[:] = [d for d in dirs if not d.startswith(".")] if rekursiv else []
        for d in dateien:
            if d.startswith((".", "~$")):
                continue
            if os.path.splitext(d)[1].lower() in tabularium.ALLE_FORMATE:
                yield os.path.join(wurzel, d)


# --------------------------------------------------------------------------
# Zustand
# --------------------------------------------------------------------------

class Zustand:
    def __init__(self, archiv_ordner, port):
        self.token = secrets.token_urlsafe(24)
        self.port = port
        self.lock = threading.RLock()
        self.protokoll = collections.deque(maxlen=300)
        self.hash_cache = {}
        self.zs_cache = {}
        self.letzte_pruefung = None
        self.archiv = None
        self.archiv_setzen(archiv_ordner)

    def archiv_setzen(self, ordner):
        ordner = os.path.abspath(os.path.expanduser(ordner))
        if os.path.basename(ordner) == tabularium.ARCHIV_ORDNER:
            ordner = os.path.dirname(ordner)
        os.makedirs(ordner, exist_ok=True)
        pfad = os.path.join(ordner, tabularium.ARCHIV_ORDNER)
        archiv = tabularium.Archiv(pfad) if os.path.isdir(pfad) else tabularium.Archiv.anlegen(ordner)
        with self.lock:
            self.archiv = archiv
            self.letzte_pruefung = None
            self.zs_cache = {}
        konfig_speichern({"archiv": ordner})
        self.log("Archiv geöffnet: %s" % kurzpfad(pfad))

    def log(self, text, art="info"):
        with self.lock:
            self.protokoll.appendleft({"zeit": time.strftime("%d.%m. %H:%M:%S"),
                                       "text": text, "art": art})

    def datei_hash(self, pfad):
        st = os.stat(pfad)
        schluessel = (pfad, st.st_mtime, st.st_size)
        h = self.hash_cache.get(schluessel)
        if h is None:
            h = tabularium.sha256_datei(pfad)
            self.hash_cache[schluessel] = h
        return h

    def zs_zeit(self, eintrag_hash):
        if eintrag_hash not in self.zs_cache:
            pfad = self.archiv.zeitstempelpfad(eintrag_hash)
            self.zs_cache[eintrag_hash] = tabularium.zeitstempel_zeit(pfad) \
                if os.path.exists(pfad) else None
        return self.zs_cache[eintrag_hash]

    def dokumentname(self, pfad):
        return tabularium.dokumentname_fuer(self.archiv, pfad)

    def einchecken(self, pfad, **kw):
        zeilen = []
        eintrag = tabularium.einchecken_datei(self.archiv, pfad, melden=zeilen.append, **kw)
        for z in zeilen:
            t = z.strip()
            art = "ok" if t.startswith(("✔", "⏱")) else "fehler" if t.startswith("!") else "info"
            if t and not t.startswith("Nachholen"):
                self.log(t, art)
        return eintrag


class Waechter(threading.Thread):
    """Beobachtet die eingestellten Ordner und checkt gespeicherte Änderungen ein."""

    def __init__(self, zustand):
        super().__init__(daemon=True)
        self.z = zustand
        self.stand, self.wartend = {}, {}

    def run(self):
        while True:
            try:
                self.runde()
            except Exception as e:  # nie abbrechen
                self.z.log("Überwachung: %s" % e, "fehler")
            time.sleep(3)

    def runde(self):
        archiv = self.z.archiv
        for o in archiv.einstellungen().get("ueberwachte_ordner", []):
            if not os.path.isdir(o.get("pfad", "")):
                continue
            for datei in kandidaten(o["pfad"], o.get("rekursiv", False)):
                if tabularium.ARCHIV_ORDNER in datei.split(os.sep):
                    continue
                try:
                    st = os.stat(datei)
                except OSError:
                    continue
                sig = (st.st_mtime, st.st_size)
                if self.stand.get(datei) != sig:
                    self.stand[datei] = sig
                    self.wartend[datei] = sig
                elif self.wartend.get(datei) == sig:
                    del self.wartend[datei]
                    try:
                        self.z.einchecken(datei, name=self.z.dokumentname(datei),
                                          notiz="automatisch (Ordnerüberwachung)",
                                          leise=True)
                    except tabularium.ArchivFehler as e:
                        self.z.log("%s: %s" % (os.path.basename(datei), e), "fehler")


# --------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------

kurzpfad = tabularium.kurzpfad


def _eins(q, schluessel, standard=None):
    return q.get(schluessel, [standard])[0]


def api_status(z, q, daten):
    a = z.archiv
    liste = []
    for name, v in a.dokumente().items():
        letzte = v[-1]
        quelle = letzte.get("quelle")
        status = "hochgeladen"
        if quelle and os.path.isabs(quelle):
            if os.path.exists(quelle):
                try:
                    status = "aktuell" if z.datei_hash(quelle) == letzte["datei_sha256"] \
                        else "geaendert"
                except OSError:
                    status = "fehlt"
            else:
                status = "fehlt"
        liste.append({
            "name": name, "versionen": len(v), "zuletzt": letzte["zeit"],
            "status": status, "quelle": quelle, "quelle_kurz": kurzpfad(quelle),
            "format": letzte.get("format"),
            "notiz": letzte.get("notiz"),
            "zeitstempel": sum(1 for e in v if os.path.exists(a.zeitstempelpfad(e["hash"]))),
        })
    liste.sort(key=lambda d: d["zuletzt"], reverse=True)
    e = a.einstellungen()
    return {
        "archiv": a.wurzel, "archiv_kurz": kurzpfad(a.wurzel),
        "dokumente": liste,
        "einstellungen": {"zeitstempel": e.get("zeitstempel"), "tsa_url": e.get("tsa_url")},
        "ueberwachung": [dict(o, kurz=kurzpfad(o.get("pfad"))) for o in e.get("ueberwachte_ordner", [])],
        "protokoll": list(z.protokoll)[:60],
        "pruefung": z.letzte_pruefung,
        "system": SYSTEM, "dateimanager": DATEIMANAGER,
        "app": app_modus(), "autostart": autostart_aktiv(),
        "version": tabularium.VERSION,
    }


FELDER = ("version", "zeit", "nutzer", "bearbeiter", "notiz", "aenderungen",
          "anzahl_zellen", "datei_sha256", "datei_bytes", "format", "warnung",
          "blaetter", "quelle", "hash", "blaetter_neu", "blaetter_entfernt")


def api_dokument(z, q, daten):
    name = _eins(q, "name")
    v = z.archiv.versionen(name)
    if not v:
        raise tabularium.ArchivFehler("Dokument nicht gefunden: %s" % name)
    versionen = []
    for e in v:
        d = {k: e.get(k) for k in FELDER}
        d["zeitstempel"] = z.zs_zeit(e["hash"])
        versionen.append(d)
    quelle = v[-1].get("quelle")
    return {"name": name, "versionen": versionen, "quelle": quelle,
            "quelle_kurz": kurzpfad(quelle),
            "quelle_existiert": bool(quelle and os.path.isabs(quelle) and os.path.exists(quelle))}


def api_vergleich(z, q, daten):
    a = z.archiv
    name = _eins(q, "name")
    v = a.versionen(name)
    if not v:
        raise tabularium.ArchivFehler("Dokument nicht gefunden: %s" % name)
    if _eins(q, "aktuell"):
        von = tabularium.version_waehlen(v, _eins(q, "von")) if _eins(q, "von") else v[-1]
        quelle = v[-1].get("quelle")
        if not quelle or not os.path.isabs(quelle) or not os.path.exists(quelle):
            raise tabularium.ArchivFehler("Die Originaldatei ist nicht am bekannten Ort.")
        alt = a.schnappschuss_laden(von.get("zellen_sha256"))
        neu = tabularium.lese_tabelle(quelle)
        von_nr, bis_nr = von["version"], "aktuell"
    else:
        bis = tabularium.version_waehlen(v, _eins(q, "bis")) if _eins(q, "bis") else v[-1]
        if _eins(q, "von"):
            von = tabularium.version_waehlen(v, _eins(q, "von"))
        else:
            von = v[bis["version"] - 2] if bis["version"] > 1 else None
        alt = a.schnappschuss_laden(von.get("zellen_sha256")) if von else None
        neu = a.schnappschuss_laden(bis.get("zellen_sha256"))
        if von and alt is None:
            raise tabularium.ArchivFehler("Für Version %d ist kein Zellinhalt vorhanden "
                                      "(Datei war nicht lesbar)." % von["version"])
        von_nr, bis_nr = (von["version"] if von else None), bis["version"]
    if neu is None:
        raise tabularium.ArchivFehler("Für diese Version ist kein Zellinhalt vorhanden "
                                  "(Datei war nicht lesbar). Die Originaldatei ist "
                                  "trotzdem gesichert und kann heruntergeladen werden.")
    aend = tabularium.vergleiche(alt, neu)
    nb, wb = tabularium.blattaenderungen(alt, neu)
    return {
        "von": von_nr, "bis": bis_nr,
        "zaehlung": tabularium.zaehle(aend), "gesamt": len(aend),
        "gekuerzt": len(aend) > MAX_ZEILEN,
        "blaetter_neu": nb if von_nr else [], "blaetter_entfernt": wb,
        "aenderungen": [{"art": art, "zelle": k, "alt": alt_, "neu": neu_}
                        for art, k, alt_, neu_ in aend[:MAX_ZEILEN]],
    }


def api_einchecken(z, q, daten):
    ergebnisse = []
    for pfad in daten.get("pfade", []):
        try:
            e = z.einchecken(pfad, name=z.dokumentname(pfad),
                             notiz=daten.get("notiz") or None,
                             bearbeiter=daten.get("bearbeiter") or None,
                             leise=True)
            ergebnisse.append(_ergebnis(pfad, e))
        except tabularium.ArchivFehler as ex:
            z.log("%s: %s" % (os.path.basename(pfad), ex), "fehler")
            ergebnisse.append({"datei": os.path.basename(pfad), "ok": False, "meldung": str(ex)})
    return {"ergebnisse": ergebnisse}


def _ergebnis(pfad, e):
    if e is None:
        return {"datei": os.path.basename(pfad), "ok": True, "unveraendert": True,
                "meldung": "unverändert – bereits gesichert"}
    return {"datei": e["dokument"], "ok": True, "version": e["version"],
            "aenderungen": e.get("aenderungen"), "warnung": e.get("warnung"),
            "zeitstempel": e.get("_zeitstempel"),
            "zeitstempel_fehler": e.get("_zeitstempel_fehler")}


def api_hochladen(z, q, daten, kopf):
    name = os.path.basename(urllib.parse.unquote(kopf.get("X-Dateiname", "")))
    if not name or name.startswith("."):
        raise tabularium.ArchivFehler("Dateiname fehlt.")
    if os.path.splitext(name)[1].lower() not in tabularium.ALLE_FORMATE:
        raise tabularium.ArchivFehler("Format nicht unterstützt: %s" % name)
    td = tempfile.mkdtemp(prefix="tabularium-upload-")
    try:
        pfad = os.path.join(td, name)
        with open(pfad, "wb") as f:
            f.write(daten)
        e = z.einchecken(pfad, name=name, quelle=UPLOAD_QUELLE,
                         notiz=urllib.parse.unquote(kopf.get("X-Notiz", "")) or None,
                         bearbeiter=urllib.parse.unquote(kopf.get("X-Bearbeiter", "")) or None,
                         leise=True)
        return {"ergebnisse": [_ergebnis(pfad, e)]}
    finally:
        shutil.rmtree(td, ignore_errors=True)


def api_datei_waehlen(z, q, daten):
    pfade = datei_dialog("Tabelle(n) zum Sichern wählen")
    ok = [p for p in pfade if os.path.splitext(p)[1].lower() in tabularium.ALLE_FORMATE]
    return {"pfade": ok, "abgelehnt": [os.path.basename(p) for p in pfade if p not in ok]}


def api_ordner_waehlen(z, q, daten):
    return {"pfad": ordner_dialog(daten.get("titel", "Ordner wählen"))}


def api_autostart(z, q, daten):
    autostart_setzen(bool(daten.get("aktiv")))
    z.log("Autostart %s" % ("eingeschaltet" if daten.get("aktiv") else "ausgeschaltet"))
    return {"ok": True, "aktiv": autostart_aktiv()}


def api_pruefen(z, q, daten):
    fehler, hinweise, kopf, anzahl, zs_ok = tabularium.pruefe_archiv(z.archiv)
    hinweise = [h.replace("Einschalten: tabularium einstellungen --zeitstempel an",
                          "Einschalten unter Einstellungen → Zeitstempel.") for h in hinweise]
    z.letzte_pruefung = {"zeit": tabularium.jetzt(), "ok": not fehler, "fehler": fehler,
                         "hinweise": hinweise, "kopf": kopf, "anzahl": anzahl,
                         "zeitstempel": zs_ok}
    z.log("Archivprüfung: %s" % ("bestanden" if not fehler else
                                 "%d Problem(e)" % len(fehler)),
          "ok" if not fehler else "fehler")
    return z.letzte_pruefung


def api_einstellungen(z, q, daten):
    e = z.archiv.einstellungen()
    if "zeitstempel" in daten:
        e["zeitstempel"] = bool(daten["zeitstempel"])
    if daten.get("tsa_url"):
        url = daten["tsa_url"].strip()
        if not url.startswith(("https://", "http://")):
            raise tabularium.ArchivFehler("Die Adresse muss mit https:// beginnen.")
        e["tsa_url"] = url
    z.archiv.einstellungen_speichern(e)
    return {"ok": True}


def api_ueberwachung(z, q, daten):
    e = z.archiv.einstellungen()
    liste = e.get("ueberwachte_ordner", [])
    pfad = os.path.abspath(daten.get("pfad", ""))
    if daten.get("aktion") == "hinzufuegen":
        if not os.path.isdir(pfad):
            raise tabularium.ArchivFehler("Ordner nicht gefunden.")
        liste = [o for o in liste if o["pfad"] != pfad]
        liste.append({"pfad": pfad, "rekursiv": bool(daten.get("rekursiv"))})
        z.log("Überwachung gestartet: %s" % kurzpfad(pfad), "ok")
    else:
        liste = [o for o in liste if o["pfad"] != pfad]
        z.log("Überwachung beendet: %s" % kurzpfad(pfad))
    e["ueberwachte_ordner"] = liste
    z.archiv.einstellungen_speichern(e)
    return {"ok": True}


def api_archiv(z, q, daten):
    z.archiv_setzen(daten["pfad"])
    return {"ok": True, "archiv": z.archiv.wurzel}


def api_finder(z, q, daten):
    pfad = daten.get("pfad")
    bekannt = {v[-1].get("quelle") for v in z.archiv.dokumente().values()}
    if pfad not in bekannt or not os.path.exists(pfad):
        raise tabularium.ArchivFehler("Datei nicht gefunden.")
    im_dateimanager_zeigen(pfad)
    return {"ok": True}


def api_zeitstempel(z, q, daten):
    a = z.archiv
    n = 0
    for e in a.eintraege():
        if not os.path.exists(a.zeitstempelpfad(e["hash"])):
            tabularium.zeitstempel_holen(a, e["hash"])
            n += 1
    z.zs_cache = {}
    if n:
        z.log("%d Zeitstempel nachgeholt" % n, "ok")
    return {"nachgeholt": n}


GET_ROUTEN = {"/api/status": api_status, "/api/dokument": api_dokument,
              "/api/vergleich": api_vergleich}
POST_ROUTEN = {"/api/einchecken": api_einchecken, "/api/datei-waehlen": api_datei_waehlen,
               "/api/ordner-waehlen": api_ordner_waehlen, "/api/pruefen": api_pruefen,
               "/api/einstellungen": api_einstellungen,
               "/api/ueberwachung": api_ueberwachung, "/api/archiv": api_archiv,
               "/api/finder": api_finder, "/api/zeitstempel": api_zeitstempel,
               "/api/autostart": api_autostart}


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    server_version = "Tabularium"
    sys_version = ""
    z = None

    def log_message(self, *args):
        pass

    def _host_ok(self):
        return self.headers.get("Host", "") in (
            "127.0.0.1:%d" % self.z.port, "localhost:%d" % self.z.port)

    def _token_ok(self, q):
        t = self.headers.get("X-Tabularium-Token") or _eins(q, "token") or ""
        return secrets.compare_digest(t.encode(), self.z.token.encode())

    def senden(self, code, daten, typ="application/json; charset=utf-8", kopf=None):
        if isinstance(daten, (dict, list)):
            daten = json.dumps(daten, ensure_ascii=False).encode("utf-8")
        elif isinstance(daten, str):
            daten = daten.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(daten)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Tabularium-Benutzer", BENUTZER)
        for k, v in (kopf or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(daten)

    def _fehler(self, ex):
        if isinstance(ex, tabularium.ArchivFehler):
            return self.senden(400, {"fehler": str(ex)})
        self.z.log("Interner Fehler: %s" % ex, "fehler")
        return self.senden(500, {"fehler": "Interner Fehler: %s" % ex})

    def do_GET(self):
        u = urllib.parse.urlsplit(self.path)
        q = urllib.parse.parse_qs(u.query)
        if not self._host_ok():
            return self.senden(403, {"fehler": "Host nicht erlaubt"})
        if u.path in STATISCH:
            datei, typ = STATISCH[u.path]
            with open(os.path.join(WEB, datei), encoding="utf-8") as f:
                inhalt = f.read()
            kopf = {}
            if datei == "index.html":
                inhalt = inhalt.replace("__TOKEN__", self.z.token)
                kopf["Content-Security-Policy"] = (
                    "default-src 'self'; script-src 'self'; style-src 'self'; "
                    "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
            return self.senden(200, inhalt, typ, kopf)
        if u.path == "/favicon.ico":
            return self.senden(204, b"", "image/x-icon")
        if not self._token_ok(q):
            return self.senden(403, {"fehler": "Sitzung abgelaufen – bitte Seite neu laden."})
        try:
            if u.path == "/api/datei":
                return self._datei(q)
            if u.path == "/api/bericht":
                text, _ = tabularium.bericht_html(self.z.archiv, _eins(q, "name"))
                return self.senden(200, text, "text/html; charset=utf-8", {
                    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'"})
            fn = GET_ROUTEN.get(u.path)
            if not fn:
                return self.senden(404, {"fehler": "Unbekannt"})
            return self.senden(200, fn(self.z, q, None))
        except Exception as ex:
            return self._fehler(ex)

    def do_POST(self):
        u = urllib.parse.urlsplit(self.path)
        if not self._host_ok() or not self._token_ok({}):
            return self.senden(403, {"fehler": "Sitzung abgelaufen – bitte Seite neu laden."})
        laenge = int(self.headers.get("Content-Length", "0"))
        if laenge > MAX_UPLOAD:
            return self.senden(413, {"fehler": "Datei zu groß (max. 300 MB)."})
        roh = self.rfile.read(laenge) if laenge else b""
        try:
            if u.path == "/api/beenden":
                self.z.log("Tabularium wird beendet")
                self.senden(200, {"ok": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return None
            if u.path == "/api/hochladen":
                return self.senden(200, api_hochladen(self.z, {}, roh, self.headers))
            fn = POST_ROUTEN.get(u.path)
            if not fn:
                return self.senden(404, {"fehler": "Unbekannt"})
            daten = json.loads(roh.decode("utf-8")) if roh else {}
            return self.senden(200, fn(self.z, {}, daten))
        except Exception as ex:
            return self._fehler(ex)

    def _datei(self, q):
        a = self.z.archiv
        name = _eins(q, "name")
        e = tabularium.version_waehlen(a.versionen(name), _eins(q, "version"))
        pfad = a.objektpfad(e["datei_sha256"])
        with open(pfad, "rb") as f:
            daten = f.read()
        if tabularium.sha256_bytes(daten) != e["datei_sha256"]:
            raise tabularium.ArchivFehler("Gesicherte Datei ist beschädigt – Archiv prüfen.")
        stamm, ext = os.path.splitext(name)
        dateiname = "%s (Version %d)%s" % (stamm, e["version"], ext)
        ascii_name = dateiname.encode("ascii", "replace").decode().replace("?", "_").replace('"', "")
        return self.senden(200, daten, "application/octet-stream", {
            "Content-Disposition": "attachment; filename=\"%s\"; filename*=UTF-8''%s" % (
                ascii_name, urllib.parse.quote(dateiname))})


# --------------------------------------------------------------------------
# Start
# --------------------------------------------------------------------------

class LokalerServer(ThreadingHTTPServer):
    """HTTP-Server nur für 127.0.0.1, ohne Namensauflösung beim Start.

    http.server ruft sonst socket.getfqdn() auf; diese DNS/mDNS-Abfrage kann je
    nach Netz und Startweg (z. B. über den Finder) viele Sekunden hängen."""
    daemon_threads = True

    def server_bind(self):
        socketserver.TCPServer.server_bind(self)
        self.server_name = "127.0.0.1"
        self.server_port = self.server_address[1]


# Direkte Verbindungen ohne System-Proxy (127.0.0.1 nie über einen Proxy)
_DIREKT = urllib.request.build_opener(urllib.request.ProxyHandler({}))


# Kennung des Benutzerkontos: Ein Doppelklick soll nie die Sitzung eines anderen
# Benutzers auf demselben Rechner öffnen.
BENUTZER = hashlib.sha256((getpass.getuser() + "|" + os.path.expanduser("~"))
                          .encode("utf-8")).hexdigest()[:16]
PORTBEREICH = 20


def laeuft_auf(port=STANDARD_PORT):
    """URL eines laufenden Tabularium-Servers dieses Benutzers oder None."""
    for p in range(port, port + PORTBEREICH):
        try:
            with _DIREKT.open("http://127.0.0.1:%d/favicon.ico" % p, timeout=0.5) as r:
                if r.headers.get("X-Tabularium-Benutzer") == BENUTZER:
                    return "http://127.0.0.1:%d/" % p
        except Exception:
            continue
    return None


def starten(archiv=None, port=STANDARD_PORT, browser=True):
    url = laeuft_auf(port)
    if url:
        print("Tabularium läuft bereits: %s" % url)
        if browser:
            webbrowser.open(url)
        return 0
    server = None
    for p in range(port, port + PORTBEREICH):
        try:
            server = LokalerServer(("127.0.0.1", p), Handler)
            port = p
            break
        except OSError:
            continue
    if server is None:
        raise tabularium.ArchivFehler("Kein freier Port gefunden.")
    server.daemon_threads = True
    ordner = archiv or konfig_laden().get("archiv") or STANDARD_ORDNER
    z = Zustand(ordner, port)
    Handler.z = z
    Waechter(z).start()
    url = "http://127.0.0.1:%d/" % port
    print("Tabularium läuft: %s" % url)
    print("Archiv: %s" % z.archiv.wurzel)
    if not app_modus():
        print("Dieses Fenster offen lassen. Beenden mit Ctrl+C oder Fenster schließen.")
    if browser:
        threading.Timer(0.6, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBeendet.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(starten())
