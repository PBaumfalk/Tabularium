#!/bin/bash
# Packt dist/Tabularium.app in ein DMG mit Verknüpfung zum Programme-Ordner.
# Aufruf: packaging/dmg.sh VERSION ARCHITEKTUR   (z. B. 1.1.0 AppleSilicon)
set -euo pipefail
VERSION="$1"
ARCH="$2"
ZIEL="dist/Tabularium-${VERSION}-macOS-${ARCH}.dmg"

STUFE="$(mktemp -d)"
cp -R dist/Tabularium.app "$STUFE/"
ln -s /Applications "$STUFE/Programme"
cp LICENSE "$STUFE/Lizenz.txt"

rm -f "$ZIEL"
# hdiutil scheitert auf CI-Rechnern gelegentlich mit "Resource busy" -> wiederholen
for versuch in 1 2 3 4 5; do
  if hdiutil create -volname "Tabularium ${VERSION}" -srcfolder "$STUFE" \
       -fs HFS+ -format UDZO -imagekey zlib-level=9 -ov "$ZIEL"; then
    break
  fi
  [ "$versuch" = 5 ] && exit 1
  echo "hdiutil fehlgeschlagen, neuer Versuch in 10 s ($versuch/5)"
  sleep 10
done
rm -rf "$STUFE"
echo "$ZIEL"
