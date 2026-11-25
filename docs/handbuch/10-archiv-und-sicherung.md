# 10 — Archiv und Datensicherung (für IT)

## Aufbau des Archivs

Das Archiv ist ein gewöhnlicher Ordner namens `.tabularium`. Die Oberfläche legt
ihn unter `~/Tabularium/.tabularium` an.

```
.tabularium/
├── journal.jsonl          Journal: ein JSON-Eintrag pro Zeile, verkettet
├── objekte/ab/abcd…       Originaldateien, Name = SHA-256 des Inhalts
├── zellen/ab/abcd….json   Zellabbilder (Werte und Formeln), Name = SHA-256
├── zeitstempel/<hash>.tsr Zeitstempel-Antworten (RFC 3161), je Journaleintrag
├── tsa/                   Zertifikate der Zeitstempelstelle
├── einstellungen.json     Zeitstempel, Zeitstempelstelle, überwachte Ordner
├── sperre                 Sperrdatei für gleichzeitige Zugriffe
└── LIESMICH.txt
```

Gleiche Inhalte werden nur einmal gespeichert. Sichern Sie dieselbe Datei
unter zwei Namen, liegt sie trotzdem nur einmal in `objekte/`.

**Ändern Sie im Archiv nichts von Hand.** Jede Änderung führt zu einer roten
Prüfmeldung, und das ist gewollt.

## Schutz auf dem Mac

Auf macOS setzt Tabularium zusätzlich Dateisperren:

| Datei | Sperre | Wirkung |
| --- | --- | --- |
| `objekte/…`, `zellen/…`, `zeitstempel/…` | `uchg` (unveränderlich) + schreibgeschützt | kann weder geändert noch gelöscht werden, auch nicht über den Finder |
| `journal.jsonl` | `uappnd` (nur anhängen) | kann ergänzt, aber nicht geändert oder gekürzt werden |

Mit `ls -lO .tabularium/journal.jsonl` sehen Sie die Sperre. Die Sperren
schützen vor **Versehen und Schadsoftware ohne Absicht**, nicht vor dem
Eigentümer. Wer den Rechner besitzt, kann sie mit `chflags` aufheben. Gegen
gezielte Manipulation schützen die Kette und die Zeitstempel
([Kapitel 7](07-zeitstempel.md)).

Die Sperren funktionieren auf APFS- und HFS+-Laufwerken. Auf Netzlaufwerken
(SMB) und exFAT-Sticks gibt es sie nicht. Tabularium arbeitet dort trotzdem,
nur ohne diese zusätzliche Schicht.

**Unter Windows** gibt es diese Sperren nicht. Tabularium setzt dort für die
Archivdateien das Attribut *Schreibgeschützt*. Das verhindert versehentliches
Überschreiben, aber kein Löschen. Umso wichtiger sind Zeitstempel und eine
Kopie auf WORM-Speicher.

## Das Archiv woanders ablegen

**Oberfläche:** Einstellungen → Archiv → **Anderen Archiv-Ordner wählen …**.
Wählen Sie einen Ordner mit vorhandenem Archiv, öffnet Tabularium es. Sonst legt
es dort ein neues an. Das bisherige Archiv bleibt unverändert, wo es ist.

**Kommandozeile:** `--archiv PFAD` vor jedem Befehl.

### Auf dem NAS

Ein Archiv auf einem NAS ist möglich und für mehrere Arbeitsplätze sinnvoll.
Beachten Sie:

- Die Mac-Dateisperren gibt es auf Netzlaufwerken nicht (siehe oben).
- Tabularium sperrt das Archiv beim Schreiben (`flock`). Über SMB ist das je
  nach NAS nicht zuverlässig. Lassen Sie deshalb möglichst **nur einen Rechner**
  schreiben, etwa einen, der die Ordnerüberwachung betreibt. Lesen, prüfen und
  Berichte erstellen können alle.
- Ist das NAS nicht erreichbar, kann Tabularium nicht sichern. Die Oberfläche
  meldet dann einen Fehler.

## Datensicherung

Das Archiv ist ein Ordner wie jeder andere. Time Machine, NAS-Sicherung oder
`rsync` sichern es vollständig. Achten Sie darauf, dass der versteckte Ordner
`.tabularium` mitgesichert wird.

Für eine **revisionssichere** Ablage reicht eine normale Datensicherung nicht,
denn wer das Archiv löscht, löscht beim nächsten Sicherungslauf oft auch die
Kopie. Empfohlen wird zusätzlich eine Kopie auf **WORM-Speicher** (*write once,
read many*). Dort kann nichts überschrieben oder gelöscht werden:

| Lösung | Beispiel |
| --- | --- |
| NAS mit unveränderbaren Snapshots | Synology *Immutable Snapshots*, QNAP *WORM-Freigabe* |
| Objektspeicher mit Sperre | S3 Object Lock im Modus *Compliance* (z. B. AWS S3, Wasabi, MinIO) |
| Optische Medien | M-DISC oder BD-R für Jahresabschlüsse |

Weil Tabularium nur Dateien anhängt und nie ändert, eignet sich das Archiv gut
für solche Speicher: Jede Sicherung fügt nur neue Dateien hinzu.

### Wiederherstellen aus der Sicherung

Archivordner zurückkopieren, Tabularium starten, **Archiv prüfen**. Ist die
Prüfung grün, ist das Archiv vollständig und unverändert.

## Archiv löschen

**Mac:** Wegen der Sperren lässt sich der Ordner nicht einfach in den
Papierkorb legen. Im Terminal:

```bash
chflags -R nouchg,nouappnd ~/Tabularium/.tabularium
rm -rf ~/Tabularium/.tabularium
```

**Windows:** Tabularium beenden, den Ordner `Tabularium` in Ihrem
Benutzerordner im Explorer löschen und die Rückfrage zu schreibgeschützten
Dateien bestätigen.

Prüfen Sie vorher Aufbewahrungsfristen. Für Geschäftsunterlagen gelten oft
sechs bis zehn Jahre (§ 147 AO, § 257 HGB), für Handakten von Rechtsanwälten
sechs Jahre (§ 50 Abs. 1 BRAO).

---

← [9 — Kommandozeile](09-kommandozeile.md) | [Inhalt](README.md) | [11 — Unabhängig prüfen](11-unabhaengig-pruefen.md) →
