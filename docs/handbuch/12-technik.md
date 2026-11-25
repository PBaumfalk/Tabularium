# 12 — Technik (für IT)

## Aufbau

| Datei | Aufgabe |
| --- | --- |
| `tabularium.py` | Kern und Kommandozeile: Tabellen auslesen, vergleichen, Archiv, Journal, Zeitstempel, Prüfung, Prüfbericht |
| `tabularium_web.py` | Lokaler HTTP-Server (`http.server`), JSON-API, Ordnerüberwachung im Hintergrund |
| `web/` | Oberfläche: `index.html`, `style.css`, `app.js` (Vanilla-JavaScript, kein Framework, kein Build) |
| `tabularium_app.py` | Startpunkt der installierbaren App: Doppelklick-Logik, Logdatei, Selbsttest |
| `packaging/` | PyInstaller-Spezifikation, Programmsymbole, DMG-Skript, Inno-Setup-Skript |
| `werkzeuge/pruefe_ohne_tabularium.py` | Unabhängiges Prüfskript ([Kapitel 11](11-unabhaengig-pruefen.md)) |
| `tests/` | `unittest`-Tests für Kern und Web-API |

Nur Python-Standardbibliothek, lauffähig ab Python 3.8. Externe Programme
werden nur bei Bedarf aufgerufen: LibreOffice (`soffice --headless
--convert-to xlsx`) für `.xls`/`.xlsb`/`.xlt`, `curl` für den Abruf der
Zeitstempel (sonst `urllib`), `openssl ts -verify` für die Signaturprüfung der
Zeitstempel, `osascript` (Mac), PowerShell (Windows) bzw. `zenity` (Linux) für
Dateidialoge.

Die Zeitstempel-Anfrage (`TimeStampReq`) erzeugt Tabularium selbst in DER und
liest die Antwort (`TimeStampResp`, `TSTInfo`) mit einem kleinen eigenen
ASN.1-Leser: Status, Hash-Algorithmus, Hash, Zeit und Nonce. Die Prüfung der
CMS-Signatur gegen das Zertifikat der Zeitstempelstelle übernimmt OpenSSL bzw.
LibreSSL, das auf macOS und Linux vorhanden ist. Fehlt es (meist unter Windows),
meldet Tabularium die Signatur ausdrücklich als ungeprüft.

## Journal

`journal.jsonl` enthält einen JSON-Eintrag pro Zeile:

| Feld | Inhalt |
| --- | --- |
| `nr` | laufende Nummer im Archiv, ab 1 |
| `dokument`, `version` | Dokumentname und Versionsnummer innerhalb des Dokuments |
| `zeit` | Zeitpunkt der Sicherung, ISO 8601 mit Zeitzone (Uhr des Rechners) |
| `nutzer`, `rechner` | Benutzerkonto und Rechnername |
| `bearbeiter`, `notiz` | Angaben „Bearbeitet von“ und Notiz |
| `quelle` | Pfad der Originaldatei bzw. `(hochgeladen über die Weboberfläche)` |
| `format`, `datei_bytes`, `datei_geaendert` | Endung, Größe, Änderungszeit der Datei |
| `datei_sha256` | SHA-256 der Originaldatei |
| `zellen_sha256`, `anzahl_zellen`, `blaetter` | Zellabbild (oder `null`, wenn nicht lesbar) |
| `aenderungen` | `{"neu": n, "geaendert": n, "geloescht": n}` gegenüber der Vorfassung |
| `blaetter_neu`, `blaetter_entfernt` | Blattänderungen |
| `warnung` | z. B. „Datei ist verschlüsselt …“ |
| `vorher` | `hash` des vorigen Eintrags, beim ersten 64 Nullen |
| `programm` | Programmname und Version |
| `hash` | SHA-256 über alle anderen Felder ([Regel](11-unabhaengig-pruefen.md#die-regel-für-den-eintrags-hash)) |

Zeitstempel werden über den `hash` des Eintrags angefordert und unter
`zeitstempel/<hash>.tsr` abgelegt (DER-kodierte `TimeStampResp`). Die Anfrage
enthält eine Nonce und fordert das Zertifikat der Zeitstempelstelle an
(`openssl ts -query -sha256 -cert`).

Schreibzugriffe laufen unter einer exklusiven Sperre auf `.tabularium/sperre`
(`flock` auf macOS und Linux, `msvcrt.locking` unter Windows). Das Journal wird
plattformunabhängig mit `\n` als Zeilenende geschrieben. Dateien werden erst als `.tmp` geschrieben und dann
atomar umbenannt. Nach dem Kopieren prüft Tabularium den SHA-256 erneut, damit
eine während des Sicherns veränderte Datei nicht unbemerkt archiviert wird.

## Zellabbild

```json
{"blaetter": ["Übersicht", "Offene Posten"],
 "zellen": {"Übersicht!B4": ["20125", null],
            "Übersicht!D4": ["21535", "=B4+C4"]}}
```

Je Zelle wird `[Wert, Formel]` gespeichert, nur für Zellen mit Inhalt. Die
Werte werden so vereinheitlicht:

| Typ | Darstellung |
| --- | --- |
| Zahl | ganzzahlig ohne `.0`, sonst bis 15 signifikante Stellen (`892.5`) |
| Datum/Uhrzeit | ISO 8601 (`2026-04-22`, `2026-04-22T10:15:00`). Bei xlsx wird das Zahlenformat der Zelle ausgewertet, auch das 1904-Datumssystem. Reine Uhrzeiten: xlsx `10:15:00`, ods als ISO-Dauer `PT10H15M00S` |
| Wahrheitswert | `WAHR` / `FALSCH` |
| Fehler | Text, z. B. `#DIV/0!` |
| Text | unverändert, Zeilenumbrüche bleiben erhalten |

Formeln aus xlsx werden mit `=` vorangestellt gespeichert. **Geteilte Formeln**
(`<f t="shared">`) werden für jede Zelle mit verschobenen relativen Bezügen
ausgeschrieben, wie Excel sie anzeigt. Bei ods entfällt das Präfix `of:`.
Wiederholte Zeilen und Spalten (`number-rows-repeated`,
`number-columns-repeated`) werden aufgelöst, leere Wiederholungen übersprungen.

Ausgelesen wird mit `zipfile` und `xml.etree` direkt aus dem Dateiformat.
Excel oder LibreOffice werden dafür nicht gestartet, Makros nie ausgeführt.
Einzige Ausnahme sind alte Binärformate (`.xls`, `.xlsb`, `.xlt`): Sie wandelt
LibreOffice im Hintergrund in eine temporäre xlsx-Kopie um. Gesichert wird
trotzdem das unveränderte Original.

## Vergleich

Verglichen wird nach Zelladresse. Eine Zelle ist *neu*, *geändert* (Wert
**oder** Formel unterschiedlich) oder *gelöscht*. Die Reihenfolge folgt den
Blättern, dann Zeile, dann Spalte.

## Weboberfläche und Sicherheit

Der Server bindet ausschließlich an `127.0.0.1` (Standardport 8765, bei Belegung
die nächsten 20 Ports). Läuft Tabularium schon, öffnet ein zweiter Start nur den
Browser.

| Maßnahme | Schützt vor |
| --- | --- |
| Zufälliges **Sitzungstoken** je Start, eingebettet in die Seite, verlangt als Header `X-Tabularium-Token` (bzw. Parameter `token` für Downloads) | fremden Webseiten, die per `fetch` oder Formular Befehle an den lokalen Server senden (CSRF) |
| **Host-Prüfung** (`127.0.0.1:PORT` oder `localhost:PORT`) | DNS-Rebinding |
| **Content-Security-Policy** ohne Inline-Skripte und -Styles, `frame-ancestors 'none'`, `X-Frame-Options: DENY` | Skripteinschleusung, Clickjacking |
| Zellinhalte nur über `textContent`, im Bericht über `html.escape` | HTML in Zellen |
| „Im Finder zeigen“ nur für bekannte Quelldateien, Uploads nur mit Tabellenendung und bis 300 MB | Missbrauch der API |

API (alle mit Token):

| Methode | Pfad | Zweck |
| --- | --- | --- |
| GET | `/api/status` | Archiv, Dokumente mit Status, Einstellungen, Aktivität, letzte Prüfung |
| GET | `/api/dokument?name=` | Fassungen eines Dokuments |
| GET | `/api/vergleich?name=&von=&bis=` bzw. `&aktuell=1` | Zellvergleich |
| GET | `/api/datei?name=&version=` | Originaldatei einer Fassung |
| GET | `/api/bericht?name=` | Prüfbericht (HTML) |
| POST | `/api/beenden` | Server beenden |
| POST | `/api/autostart` | `{"aktiv": true}` – Start bei der Anmeldung (nur App) |
| POST | `/api/einchecken` | `{"pfade": [...], "notiz": "", "bearbeiter": ""}` |
| POST | `/api/hochladen` | Rohdaten, Header `X-Dateiname`, `X-Notiz`, `X-Bearbeiter` (URL-kodiert) |
| POST | `/api/pruefen`, `/api/zeitstempel` | Archiv prüfen, Zeitstempel nachholen |
| POST | `/api/einstellungen`, `/api/ueberwachung`, `/api/archiv` | Einstellungen ändern |
| POST | `/api/datei-waehlen`, `/api/ordner-waehlen`, `/api/finder` | Systemdialoge, Finder/Explorer |

Die Umgebungsvariable `TABULARIUM_KONFIG` ersetzt den Pfad von
`~/.tabularium.json`, etwa für Tests.

## Installierbare App

Die Pakete baut [PyInstaller](https://pyinstaller.org) aus `tabularium_app.py`
und dem Ordner `web/`. Python ist darin enthalten, sonst nichts.

| | macOS | Windows |
| --- | --- | --- |
| Paket | `Tabularium.app` in einem DMG, je für Apple Silicon und Intel | Installer aus [Inno Setup](https://jrsoftware.org/isinfo.php), x64 |
| Fenster | keines, kein Dock-Symbol (`LSUIElement`). Die Oberfläche ist der Browser | keines (Fenster-App ohne Konsole) |
| Doppelklick bei laufendem Server | öffnet nur den Browser | öffnet nur den Browser |
| Server | als abgekoppelter Prozess (`--server`), damit ein erneuter Doppelklick wieder beim Starter ankommt | im Prozess der App |
| Autostart | LaunchAgent `~/Library/LaunchAgents/de.tabularium.app.plist` mit `--hintergrund` | `HKCU\…\Run\Tabularium` mit `--hintergrund` |
| Logdatei | `~/Library/Logs/Tabularium/tabularium.log` | `%LOCALAPPDATA%\Tabularium\tabularium.log` |
| Signatur | ad hoc (nicht notarisiert) | keine |

Ein laufender Server antwortet mit dem Header `X-Tabularium-Benutzer`, einem
Hash aus Benutzername und Benutzerordner. So öffnet ein Doppelklick nie die
Sitzung eines anderen Benutzerkontos. Ist Port 8765 belegt, weicht Tabularium
auf die nächsten 19 Ports aus.

`Tabularium --selbsttest` prüft die fertige App ohne Browser: Oberfläche,
ods/fods und xlsx einchecken, Vergleich, Zeitstempel-Anfrage, Archivprüfung,
Bericht, Beenden. Der Workflow [`pakete.yml`](../../.github/workflows/pakete.yml)
führt ihn auf jedem Paket aus. Bei einem Versions-Tag (`v1.2.3`) hängt er die
Pakete an ein GitHub-Release.

Selbst bauen:

```bash
python3 -m pip install "pyinstaller>=6.10,<7"
pyinstaller --noconfirm packaging/tabularium.spec
dist/Tabularium.app/Contents/MacOS/Tabularium --selbsttest     # macOS
packaging/dmg.sh 1.1.0 AppleSilicon                            # DMG
iscc /DVersion=1.1.0 packaging\windows.iss                     # Windows-Installer
```

Signieren lässt sich später nachrüsten: auf dem Mac mit `codesign` und einem
Developer-ID-Zertifikat plus `notarytool`, unter Windows mit `signtool` vor
dem Inno-Setup-Schritt.

## Tests

```bash
python3 -m unittest discover tests -v
```

| Bereich | Getestet |
| --- | --- |
| Auslesen | ods/fods mit Wiederholungen, Datumsformate, Formelverschiebung, ods = xlsx = xls (mit LibreOffice) |
| Archiv | Versionen, „unverändert“, Vergleich, unlesbare Dateien, Mac-Dateisperren, Dokumentnamen |
| Zeitstempel | Aufbau der Anfrage, Lesen einer echten FreeTSA-Antwort ohne Netz und ohne OpenSSL |
| Manipulation | veränderter Journaleintrag, gelöschter Eintrag, veränderte Originaldatei |
| Web-API | Token- und Host-Prüfung, Ablauf Sichern → Vergleich → Download → Bericht → Prüfung, Upload, Schutz von „Im Finder zeigen“ |

Die Tests laufen in GitHub Actions auf macOS, Linux und Windows, jeweils mit
Python 3.10 und 3.13. Dazu kommen ein Ende-zu-Ende-Lauf mit dem unabhängigen
Prüfskript und der Selbsttest.

---

← [11 — Unabhängig prüfen](11-unabhaengig-pruefen.md) | [Inhalt](README.md) | [13 — Grenzen und rechtliche Einordnung](13-grenzen-und-recht.md) →
