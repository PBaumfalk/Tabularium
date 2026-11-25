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
hdiutil create -volname "Tabularium ${VERSION}" -srcfolder "$STUFE" \
  -fs HFS+ -format UDZO -imagekey zlib-level=9 -ov "$ZIEL"
rm -rf "$STUFE"
echo "$ZIEL"
