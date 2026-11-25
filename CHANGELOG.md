# Änderungsprotokoll

Alle nennenswerten Änderungen an Tabularium. Format nach
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionen nach
[Semantic Versioning](https://semver.org/lang/de/).

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
