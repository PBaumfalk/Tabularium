# 2 — Installation

Tabularium besteht aus wenigen Dateien und braucht nur **Python 3.8 oder
neuer**. Weitere Pakete, ein Konto oder eine Datenbank sind nicht nötig.

| Was | Wofür | Nötig? |
| --- | --- | --- |
| Python 3.8+ | Tabularium selbst | ja |
| Ein Browser (Safari, Chrome, Firefox, Edge) | die Oberfläche | ja |
| [LibreOffice](https://de.libreoffice.org) | nur für alte Formate `.xls`, `.xlsb`, `.xlt` | optional |
| OpenSSL und curl | nur für Zeitstempel. Beides ist auf dem Mac vorhanden | optional |

## a) Auf dem Mac

1. Auf der GitHub-Seite von Tabularium oben auf **Code → Download ZIP**
   klicken.
2. Die ZIP-Datei im Ordner *Downloads* doppelklicken. Den entstandenen Ordner
   an einen festen Platz verschieben, zum Beispiel nach *Dokumente*.
3. Im Ordner doppelt auf **`Tabularium.command`** klicken.

Beim ersten Start kann macOS nachfragen:

- **„… kann nicht geöffnet werden, da es von einem nicht verifizierten
  Entwickler stammt“:** Mit der rechten Maustaste (oder Ctrl + Klick) auf
  `Tabularium.command` klicken, **Öffnen** wählen und im Dialog nochmals
  **Öffnen** bestätigen. Danach genügt ein Doppelklick.
- **„Der Befehl python3 erfordert die Befehlszeilenentwicklerwerkzeuge“:**
  Auf **Installieren** klicken und warten (einige Minuten). Danach
  `Tabularium.command` erneut doppelklicken.

Es öffnet sich ein **Terminalfenster** mit dieser Meldung:

```
Tabularium läuft: http://127.0.0.1:8765/
Archiv: /Users/ihrname/Tabularium/.tabularium
Dieses Fenster offen lassen. Beenden mit Ctrl+C oder Fenster schließen.
```

Gleichzeitig öffnet sich Tabularium im Browser. **Lassen Sie das
Terminalfenster offen**, solange Sie mit Tabularium arbeiten. Sie können es
mit dem gelben Knopf ins Dock legen. Schließen Sie es, wird Tabularium beendet.
Ihre Daten bleiben erhalten.

Ist Tabularium schon gestartet und Sie doppelklicken erneut, öffnet sich nur
ein weiterer Browser-Tab mit der laufenden Sitzung.

> **Tipp:** Ziehen Sie `Tabularium.command` in den rechten Teil des Docks
> (neben den Papierkorb). Dann startet ein Klick im Dock Tabularium.

### Startet nichts?

| Beobachtung | Lösung |
| --- | --- |
| Doppelklick öffnet ein Textprogramm | Rechte Maustaste → **Öffnen mit → Terminal** |
| „Permission denied“ im Terminal | Im Terminal `chmod +x ` eingeben (mit Leerzeichen), die Datei `Tabularium.command` in das Fenster ziehen, Enter |
| Browser öffnet sich nicht | Adresse aus dem Terminalfenster von Hand im Browser öffnen |
| Seite zeigt „Sitzung abgelaufen“ | Tabularium wurde neu gestartet. Seite neu laden (⌘R) |

## b) Unter Linux (für IT)

```bash
git clone https://github.com/PBaumfalk/Tabularium.git
cd Tabularium
./tabularium web
```

Die Oberfläche läuft dann unter `http://127.0.0.1:8765`. Unter Linux gibt es
die Mac-Dateidialoge („Datei auswählen …“, „Im Finder zeigen“) und die
Dateisperren (`chflags`) nicht. Dateien ziehen Sie dort in das Ablagefeld.
Alles andere funktioniert gleich. Die Tests laufen regelmäßig unter macOS und
Linux.

**Windows** wird derzeit nicht unterstützt.

## c) Wo das Archiv liegt

Beim ersten Start legt Tabularium den Ordner **Tabularium** in Ihrem
Benutzerordner an. Darin liegt das eigentliche Archiv im versteckten Ordner
`.tabularium`. Einen anderen Ort, zum Beispiel ein NAS, wählen Sie unter
**Einstellungen → Archiv → Anderen Archiv-Ordner wählen …**
([Kapitel 10](10-archiv-und-sicherung.md)). Tabularium merkt sich die Wahl in
der Datei `~/.tabularium.json`.

## d) Aktualisieren

1. Tabularium beenden (Terminalfenster schließen).
2. Die neue Version wie oben herunterladen und den alten Programmordner
   ersetzen. **Das Archiv ist davon nicht betroffen.** Es liegt in einem
   eigenen Ordner.
3. Neu starten.

Mit Git genügt `git pull` im Programmordner.

## e) Deinstallieren

Den Programmordner in den Papierkorb legen. Das Archiv bleibt erhalten. Wie Sie
auch das Archiv löschen, steht in [Kapitel 10](10-archiv-und-sicherung.md#archiv-löschen).

---

← [1 — Was ist Tabularium?](01-was-ist-tabularium.md) | [Inhalt](README.md) | [3 — Die erste Fassung sichern](03-erste-fassung.md) →
