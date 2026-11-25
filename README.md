<img src="assets/logo.svg" width="72" alt="Tabularium">

# Tabularium

[![Tests](https://github.com/PBaumfalk/Tabularium/actions/workflows/tests.yml/badge.svg)](https://github.com/PBaumfalk/Tabularium/actions/workflows/tests.yml)
[![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org)
[![Neueste Version](https://img.shields.io/github/v/release/PBaumfalk/Tabularium?label=Version)](https://github.com/PBaumfalk/Tabularium/releases/latest)
[![Mac & Windows](https://img.shields.io/badge/macOS%20%C2%B7%20Windows-Installer-blue)](https://github.com/PBaumfalk/Tabularium/releases/latest)
[![Abhängigkeiten: keine](https://img.shields.io/badge/Abh%C3%A4ngigkeiten-keine-brightgreen.svg)](#für-entwickler)

**Excel- und LibreOffice-Tabellen revisionssicher ablegen: jede Fassung, jede
geänderte Zelle, nachweisbar unverändert.**
Tabularium ist ein kostenloses Archiv für Tabellenkalkulationen in Kanzleien,
Unternehmen und Verwaltungen. Sie legen eine Tabelle hinein, und Tabularium
bewahrt jede Fassung unverändert auf. Es zeigt Zelle für Zelle, was sich
zwischen zwei Fassungen geändert hat, mit Werten und Formeln. Ein Prüfbericht
belegt, dass seit dem Sichern nichts mehr verändert wurde.

Blattschutz und Kennwörter in Excel lassen sich in Sekunden entfernen.
Tabularium setzt deshalb außerhalb der Datei an. Jede Fassung erhält einen
kryptografischen Fingerabdruck (SHA-256). Alle Fassungen sind in einer
lückenlosen Kette verbunden, und auf Wunsch bestätigt eine externe
Zeitstempelstelle den Zeitpunkt jeder Fassung. Wer nachträglich auch nur ein
Byte ändert, eine Fassung löscht oder eine einschiebt, fällt bei der Prüfung
auf.

Tabularium läuft auf Ihrem eigenen Mac oder Windows-PC und braucht keine Cloud,
kein Abo und kein Zusatzpaket. An die Zeitstempelstelle geht nur der Fingerabdruck, nie der
Inhalt Ihrer Tabellen.

*Tabularium* hieß das Staatsarchiv des antiken Rom am Kapitol. Dort lagen die
amtlichen Tafeln (*tabulae*), unverändert und für jeden nachprüfbar. Genau das
leistet Tabularium für Ihre Tabellen.

> **English abstract:** Tamper-evident archive for spreadsheets (xlsx, xlsm, ods,
> fods, xls via LibreOffice). Every saved version is stored byte-for-byte under its
> SHA-256, its cell contents (values and formulas) are extracted and diffed
> against the previous version, and all events are recorded in an append-only,
> hash-chained journal. Optional RFC 3161 timestamps from an external TSA anchor
> each entry. It offers a local web UI (drag & drop, version history, cell-level
> diff, folder watching, printable audit report), a CLI, and ready-to-install
> packages for macOS (DMG) and Windows (installer). It is written in pure
> Python 3.8+ with the standard library only, and the archive can be verified
> independently with `shasum`, `openssl` and a few lines of Python. The UI and
> documentation are in German.

![Verlauf und Zellvergleich einer Honorarübersicht](docs/screenshots/dokument.png)

## 📖 Handbuch

Die vollständige Anleitung steht im **[Handbuch](docs/handbuch/README.md)**. Sie
ist verständlich für Mitarbeitende ohne IT-Kenntnisse und hat eigene Kapitel
für die IT. Sie reicht von den [Grundbegriffen](docs/handbuch/01-was-ist-tabularium.md)
über die [erste gesicherte Fassung](docs/handbuch/03-erste-fassung.md) und den
[Zellvergleich](docs/handbuch/04-verlauf-und-vergleich.md) bis zum
[Prüfbericht](docs/handbuch/06-pruefen-und-pruefbericht.md) und zur
[Prüfung ohne Tabularium](docs/handbuch/11-unabhaengig-pruefen.md), etwa durch
Gutachter oder Betriebsprüfer.

## Installation

**[⬇ Tabularium herunterladen](https://github.com/PBaumfalk/Tabularium/releases/latest)**:
fertige Pakete für Mac und Windows. Python oder andere Zusatzprogramme sind
nicht nötig.

| Ihr Rechner | Datei |
| --- | --- |
| 🍎 Mac mit Apple-Chip (M1 bis M4) | `Tabularium-…-macOS-AppleSilicon.dmg` |
| 🍎 Mac mit Intel-Prozessor | `Tabularium-…-macOS-Intel.dmg` |
| 🪟 Windows 10/11 (64 Bit) | `Tabularium-…-Windows-Setup.exe` |

<details>
<summary><strong>🍎 Auf dem Mac</strong></summary>

1. DMG öffnen und **Tabularium** auf **Programme** ziehen.
2. Tabularium starten. Es öffnet sich im Browser, ohne eigenes Fenster.
3. **Beim ersten Start** meldet macOS, dass Apple die App nicht prüfen konnte,
   denn sie ist (noch) nicht notarisiert. Unter ** → Systemeinstellungen →
   Datenschutz & Sicherheit** ganz unten **Dennoch öffnen** klicken. Das ist
   nur einmal nötig.

Ausführlich: [Handbuch, Kapitel 2](docs/handbuch/02-installation.md#a-auf-dem-mac).
</details>

<details>
<summary><strong>🪟 Unter Windows</strong></summary>

1. `Tabularium-…-Windows-Setup.exe` ausführen. Meldet Windows *„Der Computer
   wurde durch Windows geschützt“*: **Weitere Informationen → Trotzdem
   ausführen**.
2. Den Installationsschritten folgen. Administratorrechte sind nicht nötig.
3. Tabularium startet aus dem Startmenü und öffnet sich im Browser.

Ausführlich: [Handbuch, Kapitel 2](docs/handbuch/02-installation.md#b-unter-windows).
</details>

<details>
<summary><strong>🐧 Linux und Kommandozeile</strong> (für IT, aus dem Quelltext)</summary>

```bash
git clone https://github.com/PBaumfalk/Tabularium.git
cd Tabularium
./tabularium web                         # Weboberfläche auf http://127.0.0.1:8765
./tabularium einchecken Liste.xlsx -n "Stand nach Prüfung"
./tabularium pruefen
```

Braucht nur Python 3.8 oder neuer. Alle Befehle:
[Kapitel 9](docs/handbuch/09-kommandozeile.md).
</details>

Ihr Archiv liegt im Ordner **Tabularium** in Ihrem Benutzerordner und bleibt bei
Updates und beim Deinstallieren erhalten. Für alte `.xls`-Dateien nutzt
Tabularium zusätzlich das kostenlose [LibreOffice](https://de.libreoffice.org),
falls installiert.

## Funktionen im Überblick

| Übersicht mit Status jeder Datei | Einstellungen |
| --- | --- |
| ![Startseite mit Dokumentliste](docs/screenshots/start.png) | ![Einstellungen mit Zeitstempel und überwachten Ordnern](docs/screenshots/einstellungen.png) |

- **Fassungen sichern** per Ziehen und Ablegen oder über den Dateidialog,
  mit Notiz und Namen der bearbeitenden Person
  ([Kapitel 3](docs/handbuch/03-erste-fassung.md))
- **Zellvergleich:** Was ist neu, geändert, gelöscht? Mit Vorher und Nachher,
  Formeln, Filter nach Blatt und Suche. Zwei beliebige Fassungen lassen sich
  vergleichen, ebenso die aktuelle Datei mit der letzten Sicherung
  ([Kapitel 4](docs/handbuch/04-verlauf-und-vergleich.md))
- **„Geändert – nicht gesichert“:** Tabularium merkt sich den Speicherort und
  zeigt an, wenn eine Datei seit der letzten Sicherung verändert wurde
- **Ordner überwachen:** Jede gespeicherte Änderung wird automatisch gesichert,
  auf Wunsch ab der Anmeldung im Hintergrund
  ([Kapitel 5](docs/handbuch/05-ordner-ueberwachen.md))
- **Archiv prüfen und Prüfbericht:** grün oder rot auf einen Blick. Der
  druckfertige Bericht für die Akte enthält alle Fassungen, Änderungen,
  Prüfwerte und Zeitstempel
  ([Kapitel 6](docs/handbuch/06-pruefen-und-pruefbericht.md))
- **Externe Zeitstempel** nach RFC 3161, wahlweise von einem qualifizierten
  Vertrauensdiensteanbieter nach eIDAS ([Kapitel 7](docs/handbuch/07-zeitstempel.md))
- **Jede Fassung zurückholen**, byte-genau wie damals gespeichert
  ([Kapitel 8](docs/handbuch/08-wiederherstellen.md))
- **Formate:** xlsx, xlsm, xltx, xltm, ods, ots, fods und mit LibreOffice auch
  xls, xlsb, xlt. Verschlüsselte oder beschädigte Dateien werden trotzdem
  gesichert
- **Kommandozeile** für Skripte und Automatisierung
  ([Kapitel 9](docs/handbuch/09-kommandozeile.md))
- **Mac und Windows** als fertige Pakete, Linux aus dem Quelltext
- **Hell und dunkel**, folgt der Systemeinstellung

| Prüfbericht für die Akte | Dunkler Modus |
| --- | --- |
| ![Prüfbericht mit Versionen und Zelländerungen](docs/screenshots/bericht.png) | ![Zellvergleich im dunklen Modus](docs/screenshots/dokument-dunkel.png) |

## So funktioniert die Absicherung

```mermaid
flowchart LR
    A["Tabelle<br/>(xlsx, ods …)"] --> B["SHA-256<br/>Fingerabdruck"]
    B --> C["Original ablegen<br/>schreibgeschützt"]
    A --> D["Zellen auslesen<br/>Werte + Formeln"]
    D --> E["Vergleich mit<br/>Vorfassung"]
    C --> F["Journal-Eintrag<br/>mit Hash des Vorgängers"]
    E --> F
    F --> G["Zeitstempel<br/>(RFC 3161, extern)"]
```

1. **Das Original bleibt unverändert.** Jede Fassung wird byte-genau unter ihrem
   SHA-256-Wert abgelegt. Sie ist schreibgeschützt und auf dem Mac zusätzlich
   gegen Ändern und Löschen gesperrt.
2. **Die Zellen werden lesbar gemacht.** Tabularium liest Werte und Formeln
   aller Blätter aus und vergleicht sie mit der Vorfassung.
3. **Alle Einträge bilden eine Kette.** Jeder Eintrag im Journal enthält den
   Fingerabdruck seines Vorgängers. Wer einen Eintrag ändert, löscht oder
   einschiebt, bricht die Kette.
4. **Ein Zeitstempel sichert die Kette nach außen ab.** Eine externe
   Zeitstempelstelle bestätigt, dass ein Eintrag und damit die ganze Kette bis
   dorthin zu diesem Zeitpunkt existierte. Erst damit hilft es nichts mehr, das
   Archiv mit Vollzugriff einfach neu zu berechnen.

**Prüfbar ohne Tabularium:** Das Archiv besteht aus gewöhnlichen Dateien. Ein
Gutachter kann es mit `shasum`, `openssl` und einem kurzen Python-Skript
unabhängig prüfen ([Kapitel 11](docs/handbuch/11-unabhaengig-pruefen.md)).

## Datenschutz und Sicherheit

- Keine Telemetrie und keine Cloud. Ihre Tabellen verlassen den Rechner nicht.
- Für einen Zeitstempel wird nur ein Fingerabdruck (64 Zeichen) übertragen. Aus
  ihm lässt sich nichts über den Inhalt ablesen. Zeitstempel sind
  standardmäßig ausgeschaltet.
- Die Weboberfläche lauscht nur auf `127.0.0.1`. Sie verlangt ein
  Sitzungstoken, prüft den `Host`-Header gegen DNS-Rebinding und setzt eine
  strenge Content-Security-Policy. Zellinhalte werden nie als HTML
  eingesetzt.
- Tabularium ändert Ihre Tabellen nie. Es liest sie nur.

## Was Tabularium nicht leistet

Ehrliche Grenzen: Wer eine Änderung vorgenommen hat, weiß Tabularium nur über
das Benutzerkonto bzw. die Angabe „Bearbeitet von“. Gegen das Löschen des
ganzen Archivs schützt nur eine Kopie auf unveränderbarem Speicher (WORM).
Verglichen werden Werte und Formeln, nicht Formatierung, Kommentare oder
Makros. Eine eingefügte Zeile erscheint als Änderung der darunter liegenden
Zellen. Für Unterlagen nach GoBD gehört eine Verfahrensdokumentation dazu.
Einzelheiten: [Kapitel 13](docs/handbuch/13-grenzen-und-recht.md).

## Für Entwickler

Reines Python ab 3.8, nur die Standardbibliothek, kein Build-Schritt. Den
Aufbau und das Archivformat beschreibt [Kapitel 12](docs/handbuch/12-technik.md).

| Datei | Inhalt |
| --- | --- |
| [`tabularium.py`](tabularium.py) | Kern und Kommandozeile: Auslesen (xlsx/ods), Vergleich, Archiv, Journal, Zeitstempel, Prüfbericht |
| [`tabularium_web.py`](tabularium_web.py) | Lokaler Webserver mit JSON-API, Ordnerüberwachung, Systemdialogen und Autostart |
| [`tabularium_app.py`](tabularium_app.py) | Startpunkt der installierbaren App, mit Selbsttest |
| [`packaging/`](packaging) | PyInstaller, DMG und Windows-Installer (Inno Setup) |
| [`web/`](web) | Oberfläche: HTML, CSS, Vanilla-JavaScript, ohne Framework |
| [`tests/`](tests) | Unit- und Integrationstests, darunter Manipulationsversuche und die Sicherheit der API |

```
python3 -m unittest discover tests -v
```

Die Tests laufen in GitHub Actions auf macOS, Linux und Windows. Ist
LibreOffice installiert, prüfen sie zusätzlich, dass ods, xlsx und xls dasselbe
Zellabbild liefern. Die Pakete baut und prüft der Workflow
[`pakete.yml`](.github/workflows/pakete.yml) bei jedem Versions-Tag. Änderungen stehen im [Änderungsprotokoll](CHANGELOG.md).

## Lizenz

[MIT](LICENSE), © 2026 Patrick Baumfalk.

## Haftungsausschluss

Tabularium unterstützt bei der nachvollziehbaren Ablage von Tabellen. Es ist
keine Rechts- oder Steuerberatung, und es ist kein zertifiziertes
Archivsystem. Ob eine Ablage den Anforderungen etwa der GoBD, der
Abgabenordnung oder einer Aufbewahrungspflicht genügt, hängt auch von
organisatorischen Maßnahmen ab: Zugriffsrechte, Verfahrensdokumentation,
Datensicherung. Die Beweiskraft eines Zeitstempels hängt vom gewählten
Anbieter ab. Für Folgen fehlerhafter oder unvollständiger Ablage wird keine
Gewähr übernommen.
