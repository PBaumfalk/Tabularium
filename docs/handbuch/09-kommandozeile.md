# 9 — Kommandozeile

Alles, was die Oberfläche kann, geht auch im Terminal, dazu einige Extras für
Skripte und Automatisierung. Die Kommandozeile gehört zur Quelltextfassung
([Kapitel 2, Abschnitt g](02-installation.md#g-aus-dem-quelltext-für-it-linux)),
nicht zur installierten App. Beide können dasselbe Archiv nutzen. Die Befehle
starten Sie im Programmordner mit `./tabularium` (Windows:
`py tabularium.py`) oder von überall mit `python3 /pfad/zu/tabularium.py`.

> **Tipp:** Damit `tabularium` überall funktioniert, legen Sie einmalig eine
> Verknüpfung an:
> `ln -s "$PWD/tabularium" /usr/local/bin/tabularium`

## Welches Archiv?

Ohne Angabe sucht Tabularium den Ordner `.tabularium` und geht dabei, ähnlich
wie Git, vom Ausgangsordner aus nach oben. Bei `einchecken` ist das der Ordner
der ersten Datei, bei allen anderen Befehlen der aktuelle Ordner. Findet
`einchecken` kein Archiv, legt es eines neben der Datei an. Ein bestimmtes Archiv wählen Sie mit
`--archiv` **vor** dem Befehl:

```bash
./tabularium --archiv ~/Tabularium verlauf Fristenliste.ods
```

Die Oberfläche nutzt standardmäßig `~/Tabularium`. Für dasselbe Archiv geben
Sie also `--archiv ~/Tabularium` an.

## Befehle

| Befehl | Zweck |
| --- | --- |
| `einchecken DATEI … [-n NOTIZ] [-b NAME] [--name DOKUMENT] [--zeitstempel an\|aus] [--erzwingen]` | Fassung(en) sichern. Unveränderte Dateien werden übersprungen, außer mit `--erzwingen`. |
| `liste` | Alle Dokumente mit Anzahl der Fassungen und Status der Datei |
| `verlauf DOKUMENT [-d]` | Fassungen mit Zeit, Person, Notiz. `-d` zeigt die Zelländerungen. |
| `vergleich DOKUMENT [VON] [BIS]` | Zellvergleich zweier Fassungen, ohne Angabe die beiden letzten |
| `vergleich DOKUMENT --aktuell [DATEI]` | Letzte Fassung gegen die Datei am Speicherort oder eine beliebige Datei |
| `pruefen` | Ganzes Archiv prüfen. Exit-Code 0 = in Ordnung, 2 = Befund. |
| `bericht DOKUMENT [-o DATEI] [--oeffnen] [--erstfassung] [--max N]` | Prüfbericht als HTML |
| `wiederherstellen DOKUMENT VERSION [ZIEL]` | Fassung als Datei zurückholen, überschreibt nie |
| `ueberwachen ORDNER [-r] [--intervall SEK]` | Ordner beobachten, bis Ctrl+C |
| `zeitstempel` | Fehlende Zeitstempel nachholen |
| `einstellungen [--zeitstempel an\|aus] [--tsa-url URL] [--tsa-ca PEM] [--tsa-zertifikat PEM]` | Einstellungen zeigen oder ändern |
| `web [--port 8765] [--kein-browser]` | Weboberfläche starten |

`DOKUMENT` ist der Name im Archiv, meist der Dateiname. Ein Pfad geht auch,
dann zählt nur der Dateiname. Versionen geben Sie als `2` oder `v2` an. Hilfe
zu jedem Befehl: `./tabularium BEFEHL --hilfe`.

## Beispiele

```bash
# Sichern mit Notiz und Name
./tabularium einchecken "Honorarübersicht 2026.xlsx" -n "Monatsabschluss Oktober" -b "Frau Weber"

# Mehrere Dateien auf einmal
./tabularium einchecken ~/Kanzlei/Buchhaltung/*.xlsx -n "Jahresabschluss"

# Was hat sich seit der letzten Sicherung geändert?
./tabularium vergleich "Honorarübersicht 2026.xlsx" --aktuell

# Version 1 gegen Version 3
./tabularium vergleich "Honorarübersicht 2026.xlsx" 1 3
```

Ausgabe von `verlauf -d`:

```
Verlauf: Honorarübersicht 2026.xlsx  (3 Versionen)

v1   25.11.2026 21:32:41  Frau Weber     Erstfassung, 32 Zellen ⏱
     Notiz: Quartal 1 erfasst
v2   25.11.2026 21:32:49  Frau Weber     14 geändert, 4 neu, 0 gelöscht ⏱
     Notiz: April ergänzt, März korrigiert (Gutschrift)
       ~ Übersicht!B4      19875  →  20125
       ~ Übersicht!D4      21285  [=B4+C4]  →  21535  [=B4+C4]
       …
```

`+` steht für neu, `~` für geändert, `-` für gelöscht.

## Automatisieren (für IT)

### Nächtliche Prüfung mit Benachrichtigung

```bash
#!/bin/bash
# /usr/local/bin/tabularium-pruefung
cd /pfad/zu/Tabularium
if ! ./tabularium --archiv ~/Tabularium pruefen > /tmp/tabularium-pruefung.txt; then
  osascript -e 'display notification "Archivprüfung mit Befund – bitte prüfen" with title "Tabularium"'
fi
```

### Ordnerüberwachung als Hintergrunddienst (launchd)

Damit Ordner auch ohne geöffnete Oberfläche überwacht werden, legen Sie
`~/Library/LaunchAgents/de.tabularium.ueberwachen.plist` an:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>de.tabularium.ueberwachen</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/Users/IHRNAME/Programme/Tabularium/tabularium.py</string>
    <string>--archiv</string><string>/Users/IHRNAME/Tabularium</string>
    <string>ueberwachen</string><string>/Users/IHRNAME/Kanzlei/Fristen</string>
    <string>--rekursiv</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/Users/IHRNAME/Library/Logs/tabularium.log</string>
  <key>StandardErrorPath</key><string>/Users/IHRNAME/Library/Logs/tabularium.log</string>
</dict>
</plist>
```

Aktivieren mit `launchctl load ~/Library/LaunchAgents/de.tabularium.ueberwachen.plist`.
Liegt der Ordner unter *Dokumente* oder *Schreibtisch*, verlangt macOS für
`python3` die Freigabe unter **Systemeinstellungen → Datenschutz & Sicherheit →
Festplattenvollzugriff**.

Laufen Oberfläche und Hintergrunddienst gleichzeitig auf demselben Archiv, ist
das unbedenklich. Tabularium sperrt das Archiv beim Schreiben, sodass keine
Einträge verloren gehen.

---

← [8 — Frühere Fassungen zurückholen](08-wiederherstellen.md) | [Inhalt](README.md) | [10 — Archiv und Datensicherung](10-archiv-und-sicherung.md) →
