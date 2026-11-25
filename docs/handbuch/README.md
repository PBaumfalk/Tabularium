# Tabularium — Handbuch

Willkommen im Handbuch von **Tabularium**, dem Archiv für Tabellen. Tabularium
bewahrt jede Fassung Ihrer Excel- und LibreOffice-Tabellen unverändert auf. Es
zeigt Zelle für Zelle, was sich geändert hat, und belegt mit einem
Prüfbericht, dass seit dem Sichern nichts mehr verändert wurde. Tabularium läuft
auf Ihrem eigenen Rechner. Es braucht keinen Cloud-Dienst und kein Abo und
sendet keine Telemetrie.

Dieses Handbuch richtet sich an alle, die mit wichtigen Tabellen arbeiten:
Mitarbeitende in Kanzlei, Buchhaltung und Verwaltung, Projektverantwortliche
und alle, die später nachweisen müssen, welcher Stand wann galt. Technische
Vorkenntnisse sind nicht nötig. Kapitel für Administratoren und IT sind mit
**(für IT)** gekennzeichnet.

## Inhalt

| Kapitel | Inhalt |
| --- | --- |
| [1 — Was ist Tabularium?](01-was-ist-tabularium.md) | Grundbegriffe einfach erklärt: Fassung, Fingerabdruck, Kette, Zeitstempel, revisionssicher. |
| [2 — Installation](02-installation.md) | Tabularium auf dem Mac einrichten und starten, unter Linux für IT, aktualisieren. |
| [3 — Die erste Fassung sichern](03-erste-fassung.md) | Eine Tabelle in 30 Sekunden ins Archiv bringen, mit Notiz und Namen. |
| [4 — Verlauf und Zellvergleich](04-verlauf-und-vergleich.md) | Alle Fassungen ansehen, zwei Fassungen vergleichen, die aktuelle Datei prüfen. |
| [5 — Ordner überwachen](05-ordner-ueberwachen.md) | Jede gespeicherte Änderung automatisch sichern lassen. |
| [6 — Prüfen und Prüfbericht](06-pruefen-und-pruefbericht.md) | Das Archiv auf Manipulation prüfen und einen Bericht für die Akte erstellen. |
| [7 — Zeitstempel](07-zeitstempel.md) | Was ein externer Zeitstempel bringt, wie Sie ihn einschalten und welchen Anbieter Sie wählen. |
| [8 — Frühere Fassungen zurückholen](08-wiederherstellen.md) | Eine alte Fassung herunterladen, ohne etwas zu überschreiben. |
| [9 — Kommandozeile](09-kommandozeile.md) | Alle Befehle für Terminal, Skripte und Automatisierung. |
| [10 — Archiv und Datensicherung (für IT)](10-archiv-und-sicherung.md) | Wo das Archiv liegt, Archiv auf dem NAS, Sicherung, WORM-Speicher, Archiv löschen. |
| [11 — Unabhängig prüfen (für IT und Gutachter)](11-unabhaengig-pruefen.md) | Das Archiv ohne Tabularium prüfen, nur mit `shasum`, `openssl` und Python. |
| [12 — Technik (für IT)](12-technik.md) | Archivformat, Journal, Zellabbild, Weboberfläche, Sicherheit, Tests. |
| [13 — Grenzen und rechtliche Einordnung](13-grenzen-und-recht.md) | Was Tabularium leistet und was nicht. GoBD, Beweiswert, Verfahrensdokumentation. |
| [14 — Häufige Fragen](14-haeufige-fragen.md) | Antworten auf typische Fragen, zum Beispiel „Warum erscheinen so viele Änderungen?“ |

## Für wen welches Kapitel

| Sie sind … | Lesen Sie zuerst |
| --- | --- |
| Neu bei Tabularium | Kapitel [1](01-was-ist-tabularium.md), [3](03-erste-fassung.md) und [4](04-verlauf-und-vergleich.md) |
| Mitarbeitende, die Tabellen pflegen | Kapitel [3](03-erste-fassung.md), [4](04-verlauf-und-vergleich.md), [5](05-ordner-ueberwachen.md) und [14](14-haeufige-fragen.md) |
| Verantwortlich für Nachweise, Akte oder Prüfung | Kapitel [6](06-pruefen-und-pruefbericht.md), [7](07-zeitstempel.md) und [13](13-grenzen-und-recht.md) |
| Für Tabularium auf dem eigenen Rechner zuständig | Kapitel [2](02-installation.md) und [10](10-archiv-und-sicherung.md) |
| IT, Gutachter, Betriebsprüfer | Kapitel [9](09-kommandozeile.md) bis [13](13-grenzen-und-recht.md) |

## Schnelleinstieg in fünf Schritten

1. Doppelklick auf **`Tabularium.command`**. Tabularium öffnet sich im Browser
   ([Installation](02-installation.md)).
2. Eine Tabelle in das Feld **Fassung sichern** ziehen oder **Datei auswählen …**
   klicken ([Kapitel 3](03-erste-fassung.md)).
3. Eine kurze **Notiz** eintragen, zum Beispiel „Zahlen nach Besprechung“, und auf
   **Sichern** klicken.
4. Nach der nächsten Änderung erneut sichern. Ein Klick auf das Dokument zeigt,
   welche Zellen sich geändert haben ([Kapitel 4](04-verlauf-und-vergleich.md)).
5. Für die Akte: **Archiv prüfen** und **Prüfbericht** öffnen und als PDF
   drucken ([Kapitel 6](06-pruefen-und-pruefbericht.md)).

Empfehlung: Schalten Sie in den **Einstellungen** die **Zeitstempel** ein
([Kapitel 7](07-zeitstempel.md)). Erst dann ist ein Archiv auch gegen jemanden
abgesichert, der vollen Zugriff auf den Rechner hat.

---

[1 — Was ist Tabularium?](01-was-ist-tabularium.md) →
