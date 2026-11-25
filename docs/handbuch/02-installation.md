# 2 — Installation

Tabularium gibt es als fertiges Programm für **Mac** und **Windows**. Python oder
andere Zusatzprogramme brauchen Sie dafür nicht. Alle Downloads stehen auf der
Seite **[Releases](https://github.com/PBaumfalk/Tabularium/releases/latest)**.

| Ihr Rechner | Datei |
| --- | --- |
| Mac mit Apple-Chip (M1, M2, M3, M4 …), etwa ab Ende 2020 | `Tabularium-…-macOS-AppleSilicon.dmg` |
| Mac mit Intel-Prozessor | `Tabularium-…-macOS-Intel.dmg` |
| Windows 10 oder 11 (64 Bit) | `Tabularium-…-Windows-Setup.exe` |

Welchen Chip Ihr Mac hat, steht unter  **→ Über diesen Mac** in der Zeile
*Chip* (Apple) oder *Prozessor* (Intel).

Optional: Für alte Excel-Dateien (`.xls`, `.xlsb`) braucht Tabularium das
kostenlose [LibreOffice](https://de.libreoffice.org). Für `.xlsx` und `.ods` ist
es nicht nötig.

## a) Auf dem Mac

1. Die passende `.dmg`-Datei herunterladen und doppelklicken.
2. Im Fenster **Tabularium** auf den Ordner **Programme** ziehen.
3. Das Fenster schließen und die DMG im Finder auswerfen.
4. **Tabularium** aus dem Ordner *Programme* oder über Spotlight (⌘ Leertaste,
   „Tabularium“) starten.

### Beim ersten Start: einmal bestätigen

Tabularium ist (noch) nicht bei Apple registriert. Beim ersten Start meldet
macOS deshalb: *„Tabularium“ kann nicht geöffnet werden, da Apple nicht prüfen
kann, ob es schädliche Software enthält.* So erlauben Sie den Start:

1. Die Meldung mit **Fertig** bzw. **OK** schließen.
2. ** → Systemeinstellungen → Datenschutz & Sicherheit** öffnen.
3. Ganz nach unten scrollen. Dort steht *„Tabularium“ wurde blockiert …*.
   Auf **Dennoch öffnen** klicken und mit Ihrem Passwort oder Touch ID
   bestätigen.
4. Tabularium erneut starten und im Dialog **Öffnen** wählen.

Das ist nur einmal nötig. Unter macOS 14 und älter genügt auch: rechte
Maustaste auf Tabularium → **Öffnen** → **Öffnen**.

### So sieht Tabularium auf dem Mac aus

Tabularium hat kein eigenes Fenster und kein Symbol im Dock. Es öffnet sich
**im Browser**. Klicken Sie Tabularium erneut an, öffnet sich wieder der
Browser mit der laufenden Sitzung. Beenden: oben rechts auf **Beenden**.

## b) Unter Windows

1. `Tabularium-…-Windows-Setup.exe` herunterladen und doppelklicken.
2. Meldet Windows *„Der Computer wurde durch Windows geschützt“*: auf
   **Weitere Informationen** und dann **Trotzdem ausführen** klicken. Die
   Warnung erscheint, weil das Programm (noch) nicht kostenpflichtig signiert
   ist.
3. Den Schritten des Installationsprogramms folgen. Administratorrechte sind
   nicht nötig. Tabularium wird nur für Ihr Benutzerkonto installiert, auf
   Wunsch auch für alle.
4. Am Ende **Tabularium jetzt starten** angehakt lassen.

Tabularium steht danach im **Startmenü** und auf Wunsch auf dem Desktop. Es läuft
ohne eigenes Fenster und öffnet sich im Browser. Beenden: oben rechts auf
**Beenden**.

## c) Wo das Archiv liegt

Beim ersten Start legt Tabularium den Ordner **Tabularium** in Ihrem
Benutzerordner an (Mac: `/Users/ihrname/Tabularium`, Windows:
`C:\Users\ihrname\Tabularium`). Darin liegt das eigentliche Archiv im
versteckten Ordner `.tabularium`. Einen anderen Ort, etwa ein NAS, wählen Sie
unter **Einstellungen → Archiv** ([Kapitel 10](10-archiv-und-sicherung.md)).

## d) Bei der Anmeldung starten

Damit überwachte Ordner ([Kapitel 5](05-ordner-ueberwachen.md)) immer gesichert
werden, auch wenn Sie Tabularium nicht von Hand öffnen: **Einstellungen →
Programm → Bei der Anmeldung im Hintergrund starten** ankreuzen. Tabularium
startet dann still mit dem Rechner. Den Browser öffnen Sie bei Bedarf mit einem
Klick auf Tabularium.

## e) Aktualisieren

Die neue Version herunterladen und wie oben installieren:

- **Mac:** Tabularium beenden und die neue App in *Programme* ziehen. Den Ordner
  ersetzen lassen.
- **Windows:** Das neue Setup ausführen. Es ersetzt die alte Version. Eine
  laufende Sitzung wird dabei beendet.

**Das Archiv ist davon nicht betroffen.** Es liegt in Ihrem Benutzerordner,
nicht im Programm.

## f) Deinstallieren

- **Mac:** Tabularium beenden und aus *Programme* in den Papierkorb legen. War
  der Autostart eingeschaltet, schalten Sie ihn vorher in den Einstellungen aus.
  Sonst die Datei `~/Library/LaunchAgents/de.tabularium.app.plist` löschen.
- **Windows:** **Einstellungen → Apps → Tabularium → Deinstallieren**. Der
  Autostart wird dabei mit entfernt.

Ihr Archiv bleibt in beiden Fällen erhalten. Wie Sie auch das Archiv löschen,
steht in [Kapitel 10](10-archiv-und-sicherung.md#archiv-löschen).

## g) Aus dem Quelltext (für IT, Linux)

Wer Tabularium unter Linux betreiben, die [Kommandozeile](09-kommandozeile.md)
nutzen oder den Quelltext prüfen will, braucht nur Python 3.8 oder neuer:

```bash
git clone https://github.com/PBaumfalk/Tabularium.git
cd Tabularium
./tabularium web                 # Weboberfläche
./tabularium --hilfe             # Kommandozeile
```

Unter macOS startet ein Doppelklick auf `Tabularium.command` im
Quelltextordner die Oberfläche mit Terminalfenster. Unter Linux erscheint die
Dateiauswahl über `zenity`, falls installiert. Die Mac-Dateisperren gibt es dort
nicht.

## Startet nichts?

| Beobachtung | Lösung |
| --- | --- |
| Nach dem Start passiert nichts | Einige Sekunden warten. Tabularium öffnet den Standardbrowser. Ist keiner eingestellt, `http://127.0.0.1:8765` von Hand öffnen. |
| Browser zeigt „Sitzung abgelaufen“ | Tabularium wurde neu gestartet. Seite neu laden (⌘R bzw. F5). |
| Browser zeigt „Keine Verbindung“ | Tabularium wurde beendet. Erneut starten. |
| Fehlermeldung beim Start | Details stehen in der Logdatei: Mac `~/Library/Logs/Tabularium/tabularium.log`, Windows `%LOCALAPPDATA%\Tabularium\tabularium.log` |

---

← [1 — Was ist Tabularium?](01-was-ist-tabularium.md) | [Inhalt](README.md) | [3 — Die erste Fassung sichern](03-erste-fassung.md) →
