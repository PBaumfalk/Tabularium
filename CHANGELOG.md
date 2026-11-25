# Änderungsprotokoll

Alle nennenswerten Änderungen an Tabularium. Format nach
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionen nach
[Semantic Versioning](https://semver.org/lang/de/).

## [1.1.0] – 2026-11-25

### Neu
- **Installierbare Pakete:** `Tabularium.app` als DMG für Apple Silicon und
  Intel, Windows-Installer (Inno Setup). Python ist eingebaut
- **Windows-Unterstützung:** Dateisperre, Dateidialoge, „Im Explorer zeigen“,
  LibreOffice-Pfade, Zeitstempel ohne OpenSSL
- Die App läuft ohne Fenster und Terminal. Ein erneuter Klick öffnet die
  laufende Sitzung. Knopf **Beenden** in der Oberfläche
- **Autostart** bei der Anmeldung im Hintergrund, damit überwachte Ordner immer
  gesichert werden
- Zeitstempel-Anfrage und -Antwort in reinem Python (RFC 3161). Die
  Signaturprüfung erfolgt mit OpenSSL, wo vorhanden, sonst mit ausdrücklichem
  Hinweis
- Selbsttest der fertigen App (`--selbsttest`), automatisch geprüft für jedes
  Paket
- Logdatei für die App
- Tests laufen zusätzlich unter Windows

### Geändert
- Ein Doppelklick öffnet nur Sitzungen des eigenen Benutzerkontos
- Das Journal wird auf allen Systemen mit `\n` als Zeilenende geschrieben

## [1.0.0] – 2026-11-25

Erste veröffentlichte Version.

### Neu
- Revisionssichere Ablage von Tabellen: Originaldatei byte-genau unter SHA-256,
  Zellabbild (Werte und Formeln), hash-verkettetes Journal
- Formate xlsx, xlsm, xltx, xltm, ods, ots, fods. Mit LibreOffice auch xls, xlsb,
  xlt. Verschlüsselte und beschädigte Dateien werden trotzdem gesichert
- Zellvergleich zwischen beliebigen Fassungen und gegen die aktuelle Datei,
  geteilte Formeln aus xlsx werden aufgelöst, Datumsformate erkannt
- Externe Zeitstempel nach RFC 3161 (FreeTSA voreingestellt, eigene
  Zeitstempelstelle einstellbar), Nachholen fehlender Zeitstempel
- Archivprüfung: Eintrags-Hashes, Kette, Nummern, Originaldateien,
  Zellabbilder, Zeitstempel
- Prüfbericht als druckfertiges HTML
- Weboberfläche (nur 127.0.0.1) mit Ziehen und Ablegen, Mac-Dateidialog,
  Status „geändert – nicht gesichert“, Verlauf, Zellvergleich mit Filter und
  Suche, Download jeder Fassung, Ordnerüberwachung, hell und dunkel
- Kommandozeile mit allen Funktionen
- macOS-Dateisperren (`uchg`, `uappnd`) für Archivdateien und Journal
- Unabhängiges Prüfskript `werkzeuge/pruefe_ohne_tabularium.py`
- Handbuch in 14 Kapiteln
