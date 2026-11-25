# 8 — Frühere Fassungen zurückholen

Jede gesicherte Fassung lässt sich jederzeit zurückholen, **byte-genau** so, wie
sie damals gespeichert wurde, mit allen Formaten, Kommentaren und Makros.

## In der Oberfläche

1. Das Dokument in der Liste anklicken.
2. Links die gewünschte Fassung wählen.
3. Unten auf **Diese Fassung herunterladen** klicken.

Die Datei landet in Ihrem Download-Ordner, zum Beispiel als
*Honorarübersicht 2026 (Version 2).xlsx*. Der Name mit Versionsnummer
verhindert, dass Sie versehentlich die aktuelle Datei überschreiben.

Tabularium prüft vor dem Herunterladen den Fingerabdruck. Ist die gesicherte
Datei beschädigt, bricht es mit einer Meldung ab, statt eine fehlerhafte Datei
auszuliefern.

## Einen alten Stand wieder in Gebrauch nehmen

Tabularium ersetzt nie selbst Ihre Arbeitsdatei. So gehen Sie vor:

1. Die gewünschte Fassung herunterladen.
2. Die aktuelle Arbeitsdatei umbenennen oder sichern lassen.
3. Die heruntergeladene Datei an ihren Platz legen und auf den alten Namen
   umbenennen.
4. In Tabularium sichern, mit einer Notiz wie *„Stand von Version 2
   wiederhergestellt“*.

Die Rückkehr zum alten Stand ist so selbst als neue Fassung dokumentiert.
Nichts wird aus dem Verlauf entfernt.

## Kommandozeile

```bash
./tabularium wiederherstellen "Honorarübersicht 2026.xlsx" 2 ~/Desktop
```

legt *Honorarübersicht 2026 (Version 2).xlsx* auf dem Schreibtisch ab.
Tabularium überschreibt keine vorhandene Datei. Existiert das Ziel schon,
bricht es mit einer Meldung ab.

## Echtheit einer Datei feststellen

Taucht irgendwo eine Tabelle auf und Sie wollen wissen, ob sie einer
gesicherten Fassung entspricht, vergleichen Sie ihren Fingerabdruck:

```bash
shasum -a 256 "Honorarübersicht 2026.xlsx"
```

Stimmt die Zeichenfolge mit dem SHA-256 einer Fassung überein (in der
Oberfläche unten im Zellvergleich, im Prüfbericht bei jeder Version), ist es
genau diese Datei, bis aufs letzte Byte. Weicht sie ab, zeigt dieser Befehl,
welche Zellen anders sind als in der letzten gesicherten Fassung
([Kapitel 9](09-kommandozeile.md)):

```bash
./tabularium vergleich "Honorarübersicht 2026.xlsx" --aktuell ~/Downloads/Fundstueck.xlsx
```

---

← [7 — Zeitstempel](07-zeitstempel.md) | [Inhalt](README.md) | [9 — Kommandozeile](09-kommandozeile.md) →
