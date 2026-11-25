#!/usr/bin/env python3
"""
Prüft ein Tabularium-Archiv OHNE Tabularium – nur mit der Python-Standardbibliothek.

Für Gutachter, Prüfer und alle, die dem Programm nicht vertrauen wollen: Das Skript
ist bewusst kurz, damit man es vollständig lesen kann.

Aufruf:  python3 pruefe_ohne_tabularium.py PFAD/ZUM/.tabularium
Ergebnis: eine Zeile je Journaleintrag, am Ende der Kopf-Hash.
Exit-Code 0 = alles in Ordnung, 1 = Befund.
"""
import hashlib
import json
import os
import sys


def sha256(daten):
    return hashlib.sha256(daten).hexdigest()


archiv = sys.argv[1]
vorher = "0" * 64                     # der erste Eintrag verweist auf 64 Nullen
alles_ok = True

with open(os.path.join(archiv, "journal.jsonl"), encoding="utf-8") as journal:
    for zeilennr, zeile in enumerate(journal, 1):
        eintrag = json.loads(zeile)

        # 1. Eintrags-Hash = SHA-256 über den Eintrag ohne das Feld "hash",
        #    als JSON mit sortierten Schlüsseln, ohne Leerzeichen, UTF-8.
        ohne_hash = {k: v for k, v in eintrag.items() if k != "hash"}
        kanonisch = json.dumps(ohne_hash, sort_keys=True, ensure_ascii=False,
                               separators=(",", ":")).encode("utf-8")
        befunde = []
        if sha256(kanonisch) != eintrag["hash"]:
            befunde.append("Eintrag verändert")

        # 2. Kette: jeder Eintrag nennt den Hash seines Vorgängers.
        if eintrag["vorher"] != vorher:
            befunde.append("Kette unterbrochen")

        # 3. Die gesicherte Originaldatei liegt unter objekte/<2 Zeichen>/<SHA-256>.
        d = eintrag["datei_sha256"]
        pfad = os.path.join(archiv, "objekte", d[:2], d)
        if not os.path.exists(pfad):
            befunde.append("Datei fehlt")
        else:
            with open(pfad, "rb") as f:
                if sha256(f.read()) != d:
                    befunde.append("Datei verändert")

        print("%3d  %-40s v%-3d %s  %s" % (
            zeilennr, eintrag["dokument"][:40], eintrag["version"], eintrag["zeit"],
            "OK" if not befunde else "BEFUND: " + ", ".join(befunde)))
        alles_ok = alles_ok and not befunde
        vorher = eintrag["hash"]

print("\nKopf-Hash:", vorher)
print("Ergebnis:", "alles in Ordnung" if alles_ok else "BEFUND – siehe oben")
sys.exit(0 if alles_ok else 1)
