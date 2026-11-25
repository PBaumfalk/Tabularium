# 14 — Häufige Fragen

### Verändert Tabularium meine Tabellen?

Nein. Tabularium liest Ihre Dateien nur. Es speichert eine Kopie im Archiv.

### Kann ich weiter ganz normal in Excel oder LibreOffice arbeiten?

Ja. Sie arbeiten wie bisher und sichern einen Stand in Tabularium, wenn er
festgehalten werden soll, oder lassen den Ordner überwachen
([Kapitel 5](05-ordner-ueberwachen.md)).

### Warum erscheinen so viele Änderungen, obwohl ich nur eine Zeile eingefügt habe?

Tabularium vergleicht nach Zelladresse. Rutschen Zellen durch eine eingefügte
Zeile nach unten, gilt jede verschobene Zelle als geändert. Siehe
[Kapitel 4](04-verlauf-und-vergleich.md#warum-erscheinen-so-viele-änderungen).

### Ich habe nur die Farbe einer Zelle geändert. Warum „keine Zelländerung“?

Tabularium vergleicht Werte und Formeln, keine Formatierung. Die neue Fassung
ist trotzdem gesichert, denn der Fingerabdruck der Datei hat sich geändert, und
die Originaldatei enthält die Farbe.

### „Unverändert – bereits gesichert“, obwohl ich gespeichert habe?

Die Datei ist Byte für Byte identisch mit der letzten Fassung, Sie haben also
ohne Änderung gespeichert. Oder die Ordnerüberwachung hat die Fassung schon
gesichert.

### Kann ich eine Fassung löschen, die versehentlich gesichert wurde?

Nein, und das ist Absicht. Eine Fassung zu löschen würde die Kette brechen und
bei der Prüfung auffallen. Sichern Sie stattdessen eine korrigierte Fassung mit
einer Notiz wie „Version 4 versehentlich, gilt nicht“.

### Kann ich die Notiz nachträglich ändern?

Nein. Die Notiz ist Teil des Journaleintrags und durch den Fingerabdruck
geschützt.

### Ich habe die Datei umbenannt. Wo ist der Verlauf?

Unter dem alten Namen. Die umbenannte Datei beginnt ein neues Dokument.

### Die Prüfung ist rot. Was nun?

Nichts am Archiv ändern, sofort einen Prüfbericht als PDF speichern und die IT
hinzuziehen. Mehr in [Kapitel 6](06-pruefen-und-pruefbericht.md#was-eine-rote-meldung-bedeutet).

### Ich kann den Ordner Tabularium nicht in den Papierkorb legen.

Die Dateien im Archiv sind auf dem Mac gegen Löschen gesperrt. Wie Sie ein Archiv
bewusst löschen, steht in [Kapitel 10](10-archiv-und-sicherung.md#archiv-löschen).

### „Sitzung abgelaufen – bitte Seite neu laden“

Tabularium wurde neu gestartet. Laden Sie die Seite neu (⌘R).

### „Keine Verbindung zu Tabularium“

Das Terminalfenster wurde geschlossen. Starten Sie Tabularium neu
(Doppelklick auf `Tabularium.command`).

### Der Dateidialog erscheint nicht.

Er öffnet sich manchmal hinter dem Browserfenster. Schauen Sie im Dock oder mit
⌘Tab nach dem Eintrag *osascript*.

### Brauche ich Internet?

Nur für Zeitstempel. Alles andere funktioniert offline.

### Können mehrere Personen dasselbe Archiv nutzen?

Ja, wenn das Archiv auf einem gemeinsamen Laufwerk liegt
([Kapitel 10](10-archiv-und-sicherung.md#auf-dem-nas)). Am zuverlässigsten
schreibt dabei nur ein Rechner, und alle anderen lesen und prüfen. Jede Person
startet Tabularium auf ihrem eigenen Rechner.

### Was kostet Tabularium?

Nichts. Tabularium steht unter der MIT-Lizenz. Kosten entstehen höchstens für
einen qualifizierten Zeitstempelanbieter.

### Wie groß darf eine Tabelle sein?

Uploads in der Oberfläche bis 300 MB. Sehr große Tabellen mit Hunderttausenden
gefüllten Zellen brauchen beim Sichern einige Sekunden und entsprechend
Arbeitsspeicher. Der Zellvergleich zeigt in der Oberfläche bis zu 5000
Änderungen, der Prüfbericht bis 1000 je Fassung, mit `--max` auch mehr.

---

← [13 — Grenzen und rechtliche Einordnung](13-grenzen-und-recht.md) | [Inhalt](README.md)
