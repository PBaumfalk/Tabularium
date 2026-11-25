# 11 — Unabhängig prüfen (für IT und Gutachter)

Ein Nachweis ist nur so gut wie seine Nachprüfbarkeit. Ein Tabularium-Archiv
lässt sich deshalb **ohne Tabularium** prüfen, mit Werkzeugen, die auf jedem Mac
und jedem Linux-System vorhanden sind. Dieses Kapitel richtet sich an
Sachverständige, Betriebsprüfer, die Gegenseite und alle, die dem Programm
selbst nicht vertrauen wollen.

Sie brauchen dafür eine **Kopie des Ordners `.tabularium`**, zum Beispiel auf
einem USB-Stick. Alles Folgende ändert nichts am Archiv.

## Was zu prüfen ist

| Behauptung | Prüfung |
| --- | --- |
| Diese Datei ist Fassung X | SHA-256 der Datei = `datei_sha256` im Journaleintrag |
| Die gesicherte Datei ist unverändert | SHA-256 von `objekte/ab/abcd…` = ihr Dateiname |
| Der Journaleintrag ist unverändert | SHA-256 des Eintrags (ohne Feld `hash`) = Feld `hash` |
| Kein Eintrag fehlt oder wurde eingeschoben | Feld `vorher` = `hash` des vorigen Eintrags; der erste verweist auf 64 Nullen |
| Der Eintrag existierte zum Zeitpunkt T | Zeitstempel unter `zeitstempel/<hash>.tsr` ist gültig und deckt genau diesen `hash` |

## 1. Eine einzelne Datei

```bash
shasum -a 256 "Honorarübersicht 2026.xlsx"          # Mac, Linux
certutil -hashfile "Honorarübersicht 2026.xlsx" SHA256   # Windows
```

Die ausgegebene Zeichenfolge suchen Sie im Journal:

```bash
grep <SHA-256> .tabularium/journal.jsonl
```

Ein Treffer zeigt Dokument, Version, Zeitpunkt, Person und Notiz dieser
Fassung.

## 2. Die Kette, mit einem kurzen Python-Skript

Das Skript [`werkzeuge/pruefe_ohne_tabularium.py`](../../werkzeuge/pruefe_ohne_tabularium.py)
nutzt nur die Python-Standardbibliothek und ist so kurz, dass man es
vollständig lesen kann, bevor man es ausführt:

```bash
python3 pruefe_ohne_tabularium.py /Volumes/STICK/.tabularium
```

```
  1  Honorarübersicht 2026.xlsx               v1   2026-11-25T21:32:41+01:00  OK
  2  Honorarübersicht 2026.xlsx               v2   2026-11-25T21:32:49+01:00  OK
  3  Honorarübersicht 2026.xlsx               v3   2026-11-25T21:32:54+01:00  OK
  …
Kopf-Hash: 6bb84231f36b0254dab07cfd117338cbce551842910afa87c9f90904b1990d2d
Ergebnis: alles in Ordnung
```

Ist ein Eintrag verändert, steht dort `BEFUND: Eintrag verändert`, bei
fehlenden oder eingeschobenen Einträgen `Kette unterbrochen`.

### Die Regel für den Eintrags-Hash

Wer ein eigenes Prüfprogramm schreiben will, braucht nur diese Regel:

> Der `hash` eines Journaleintrags ist der SHA-256 (hexadezimal, klein) über
> den Eintrag **ohne** das Feld `hash`, serialisiert als JSON mit
> **alphabetisch sortierten Schlüsseln**, **ohne Leerzeichen** (Trenner `,`
> und `:`), Nicht-ASCII-Zeichen **unmaskiert**, kodiert als **UTF-8**.

In Python: `json.dumps(eintrag, sort_keys=True, ensure_ascii=False, separators=(",", ":"))`.
Die Zeile im Journal selbst ist anders formatiert (mit Leerzeichen). Maßgeblich
ist allein die beschriebene Form.

## 3. Die Zeitstempel, mit OpenSSL

Für jeden Journaleintrag mit Zeitstempel liegt unter `zeitstempel/` eine Datei
`<hash>.tsr`. So prüfen Sie sie (macOS bringt OpenSSL bzw. LibreSSL mit):

```bash
cd .tabularium
H=6a4583b3e22470e4da2b641eceedaa102d876cce4acbd34b554c23872d75f918   # Feld "hash" des Eintrags

openssl ts -verify -digest $H -in zeitstempel/$H.tsr \
  -CAfile tsa/cacert.pem -untrusted tsa/tsa.crt
# → Verification: OK

openssl ts -reply -in zeitstempel/$H.tsr -text | grep "Time stamp"
# → Time stamp: Nov 25 20:32:42 2026 GMT
```

`Verification: OK` heißt: Die Zeitstempelstelle hat genau diesen Hash zu der
angegebenen Zeit unterschrieben. Weil der Hash den Verweis auf den Vorgänger
enthält, belegt der Stempel auch alle früheren Einträge.

**Zertifikate nicht nur aus dem Archiv nehmen.** Wer das Archiv manipuliert,
könnte auch `tsa/` austauschen. Laden Sie Wurzel- und TSA-Zertifikat für eine
belastbare Prüfung direkt beim Anbieter herunter, für FreeTSA unter
`https://freetsa.org/files/cacert.pem` und `https://freetsa.org/files/tsa.crt`,
und vergleichen Sie sie.

## 4. Den Inhalt einer Fassung ansehen

Die Originaldatei liegt unter `objekte/<erste zwei Zeichen>/<SHA-256>` ohne
Endung. Kopieren Sie sie an einen anderen Ort, hängen Sie die Endung aus dem
Journalfeld `format` an (z. B. `.xlsx`) und öffnen Sie die Kopie mit Excel oder
LibreOffice.

Das Zellabbild unter `zellen/<ab>/<zellen_sha256>.json` ist eine lesbare
JSON-Datei mit allen Zellen. Sein SHA-256 entspricht dem Dateinamen und dem
Journalfeld `zellen_sha256`.

## Was die Prüfung belegt und was nicht

Belegt ist: Die Fassung lag zum Zeitpunkt des Zeitstempels genau so vor, und
seitdem wurde weder sie noch ein Journaleintrag geändert, entfernt oder
eingeschoben.

Nicht belegt ist, **wer** die Tabelle bearbeitet hat (Benutzerkonto und
Angabe „Bearbeitet von“ sind Angaben des sichernden Rechners) und dass der
Inhalt **sachlich richtig** ist. Auch die Uhrzeit im Feld `zeit` stammt vom
sichernden Rechner. Verlässlich ist nur die Zeit im Zeitstempel. Mehr dazu in
[Kapitel 13](13-grenzen-und-recht.md).

---

← [10 — Archiv und Datensicherung](10-archiv-und-sicherung.md) | [Inhalt](README.md) | [12 — Technik](12-technik.md) →
