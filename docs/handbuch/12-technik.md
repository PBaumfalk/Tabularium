# 12 — Technik (für IT)

## Aufbau

| Datei | Aufgabe |
| --- | --- |
| `tabularium.py` | Kern und Kommandozeile: Tabellen auslesen, vergleichen, Archiv, Journal, Zeitstempel, Prüfung, Prüfbericht |
| `tabularium_web.py` | Lokaler HTTP-Server (`http.server`), JSON-API, Ordnerüberwachung im Hintergrund |
| `web/` | Oberfläche: `index.html`, `style.css`, `app.js` (Vanilla-JavaScript, kein Framework, kein Build) |
| `werkzeuge/pruefe_ohne_tabularium.py` | Unabhängiges Prüfskript ([Kapitel 11](11-unabhaengig-pruefen.md)) |
| `tests/` | `unittest`-Tests für Kern und Web-API |

Nur Python-Standardbibliothek, lauffähig ab Python 3.8. Externe Programme
werden nur bei Bedarf aufgerufen: LibreOffice (`soffice --headless
--convert-to xlsx`) für `.xls`/`.xlsb`/`.xlt`, `openssl ts` und `curl` für
Zeitstempel, `osascript` und `open` für Mac-Dialoge.

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

Schreibzugriffe laufen unter einer exklusiven `flock`-Sperre auf
`.tabularium/sperre`. Dateien werden erst als `.tmp` geschrieben und dann
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
| POST | `/api/einchecken` | `{"pfade": [...], "notiz": "", "bearbeiter": ""}` |
| POST | `/api/hochladen` | Rohdaten, Header `X-Dateiname`, `X-Notiz`, `X-Bearbeiter` (URL-kodiert) |
| POST | `/api/pruefen`, `/api/zeitstempel` | Archiv prüfen, Zeitstempel nachholen |
| POST | `/api/einstellungen`, `/api/ueberwachung`, `/api/archiv` | Einstellungen ändern |
| POST | `/api/datei-waehlen`, `/api/ordner-waehlen`, `/api/finder` | Mac-Dialoge |

Die Umgebungsvariable `TABULARIUM_KONFIG` ersetzt den Pfad von
`~/.tabularium.json`, etwa für Tests.

## Tests

```bash
python3 -m unittest discover tests -v
```

| Bereich | Getestet |
| --- | --- |
| Auslesen | ods/fods mit Wiederholungen, Datumsformate, Formelverschiebung, ods = xlsx = xls (mit LibreOffice) |
| Archiv | Versionen, „unverändert“, Vergleich, unlesbare Dateien, Mac-Dateisperren |
| Manipulation | veränderter Journaleintrag, gelöschter Eintrag, veränderte Originaldatei |
| Web-API | Token- und Host-Prüfung, Ablauf Sichern → Vergleich → Download → Bericht → Prüfung, Upload, Schutz von „Im Finder zeigen“ |

Die Tests laufen in GitHub Actions auf macOS und Linux.

---

← [11 — Unabhängig prüfen](11-unabhaengig-pruefen.md) | [Inhalt](README.md) | [13 — Grenzen und rechtliche Einordnung](13-grenzen-und-recht.md) →
