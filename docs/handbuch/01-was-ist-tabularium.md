# 1 — Was ist Tabularium?

Tabularium ist ein Archiv für Tabellenkalkulationen. Es läuft auf Ihrem eigenen
Rechner, und Sie bedienen es im Browser. Sie legen eine Excel- oder
LibreOffice-Tabelle hinein, und Tabularium bewahrt diese Fassung unverändert auf.
Bei jeder weiteren Fassung zeigt es, welche Zellen sich geändert haben. Mit
einem Prüfbericht belegen Sie später, welcher Stand wann galt.

*Tabularium* hieß das Staatsarchiv des antiken Rom am Kapitol. Dort lagen die
amtlichen Tafeln (*tabulae*), unverändert und nachprüfbar.

## Wozu?

Tabellen werden ständig überschrieben. Später stellt sich dann oft eine dieser
Fragen:

- Welcher Betrag stand in der Honorarübersicht, als die Rechnung rausging?
- Wer hat die Frist in der Fristenliste verschoben, und wann?
- Ist die Tabelle, die der Mandant vorlegt, wirklich die Fassung vom März?
- Hat jemand nach der Abstimmung noch etwas geändert?

Excel und LibreOffice können das nicht zuverlässig beantworten. Blattschutz
und Kennwörter lassen sich in Sekunden entfernen. „Änderungen nachverfolgen“
lässt sich abschalten, und das Protokoll steckt in der Datei selbst. Tabularium
setzt deshalb **außerhalb** der Datei an.

## Was Sie mit Tabularium tun können

| Aufgabe | Beispiel | Kapitel |
| --- | --- | --- |
| Eine Fassung sichern | Honorarübersicht nach dem Monatsabschluss | [3](03-erste-fassung.md) |
| Sehen, was sich geändert hat | „März korrigiert: 19875 → 20125“ | [4](04-verlauf-und-vergleich.md) |
| Automatisch sichern | Jede gespeicherte Änderung der Fristenliste | [5](05-ordner-ueberwachen.md) |
| Nachweisen, dass nichts verändert wurde | Prüfbericht als PDF zur Akte | [6](06-pruefen-und-pruefbericht.md) |
| Den Zeitpunkt beweisen | Externer Zeitstempel für jede Fassung | [7](07-zeitstempel.md) |
| Einen alten Stand zurückholen | Die Fassung vom 3. März als Datei | [8](08-wiederherstellen.md) |

## Grundbegriffe

### Fassung

Eine **Fassung** ist der Stand einer Tabelle in dem Moment, in dem Sie ihn
sichern. Tabularium nummeriert die Fassungen eines Dokuments: Version 1,
Version 2 und so weiter. Jede Fassung bleibt für immer erhalten. Tabularium
überschreibt oder löscht nichts.

### Dokument

Ein **Dokument** fasst alle Fassungen einer Tabelle zusammen, zum Beispiel
*Honorarübersicht 2026.xlsx*. Tabularium erkennt das Dokument am Speicherort
der Datei, bei hochgeladenen Dateien am Dateinamen.

### Fingerabdruck (Hash)

Ein **Fingerabdruck** ist eine 64-stellige Zeichenfolge, die Tabularium aus dem
Inhalt einer Datei berechnet. Das Verfahren heißt SHA-256. Ändert sich auch nur
ein einziges Zeichen der Datei, entsteht ein völlig anderer Fingerabdruck. Aus
dem Fingerabdruck lässt sich der Inhalt nicht zurückrechnen.

So prüft Tabularium, ob eine gesicherte Datei noch genau die ist, die damals
gesichert wurde: Es berechnet den Fingerabdruck neu und vergleicht.

### Journal und Kette

Jedes Sichern wird als Eintrag im **Journal** festgehalten: wann, von wem, mit
welcher Notiz, welcher Fingerabdruck. Jeder Eintrag enthält dabei auch den
Fingerabdruck des **vorherigen** Eintrags. So entsteht eine **Kette**:

```
Eintrag 1  ←  Eintrag 2  ←  Eintrag 3  ←  Eintrag 4
```

Wer einen Eintrag in der Mitte ändert, entfernt oder einschiebt, zerstört die
Verbindung zum nächsten Eintrag. Die Prüfung meldet dann genau diese Stelle.

### Zeitstempel

Ein **Zeitstempel** ist eine Bestätigung einer unabhängigen
Zeitstempelstelle: „Dieser Fingerabdruck existierte am 25.11.2026 um 21:32:50.“
Die Stelle unterschreibt das digital. Weil der Fingerabdruck eines Eintrags die
ganze Kette davor einschließt, belegt ein einziger Zeitstempel auch alle
früheren Einträge ([Kapitel 7](07-zeitstempel.md)).

Ohne Zeitstempel kann jemand mit vollem Zugriff auf den Rechner das ganze
Archiv neu anlegen und alle Fingerabdrücke neu berechnen. Mit Zeitstempel geht
das nicht mehr, denn die Bestätigungen der Zeitstempelstelle lassen sich nicht
nachträglich erzeugen.

### Zellabbild

Neben der Originaldatei speichert Tabularium ein **Zellabbild**: eine Liste
aller gefüllten Zellen mit Wert und Formel, etwa
`Übersicht!D4 = 21535 [=B4+C4]`. Aus den Zellabbildern zweier Fassungen
entsteht der Zellvergleich. Formatierung, Farben, Kommentare und Makros sind
nicht Teil des Zellabbilds. Sie bleiben aber in der Originaldatei erhalten.

### Revisionssicher

„Revisionssicher“ heißt: Unterlagen sind **vollständig**, **unverändert**,
**nachvollziehbar** und **wiederauffindbar** abgelegt, und jede Änderung ist
erkennbar. Tabularium liefert dafür die Technik. Ob eine Ablage im rechtlichen
Sinn revisionssicher ist, hängt zusätzlich von organisatorischen Regeln ab
([Kapitel 13](13-grenzen-und-recht.md)).

## Wo liegen die Daten?

Alles liegt in einem Ordner auf Ihrem Rechner, standardmäßig unter
**Tabularium** in Ihrem Benutzerordner (genauer im versteckten Unterordner
`.tabularium`). Dort liegen die Originaldateien, die Zellabbilder, das Journal
und die Zeitstempel. Nichts davon wird in eine Cloud übertragen. Für einen
Zeitstempel geht nur der Fingerabdruck an die Zeitstempelstelle.

Ihre Tabellen selbst bleiben, wo sie sind. Tabularium liest sie nur und
verändert sie nie.

---

← [Inhalt](README.md) | [2 — Installation](02-installation.md) →
