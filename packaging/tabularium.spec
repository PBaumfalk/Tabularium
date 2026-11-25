# -*- mode: python ; coding: utf-8 -*-
# PyInstaller-Spezifikation für Tabularium (macOS .app und Windows .exe).
# Bauen:  pyinstaller --noconfirm packaging/tabularium.spec
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
with open(os.path.join(ROOT, "tabularium.py"), encoding="utf-8") as f:
    VERSION = re.search(r'^VERSION = "([^"]+)"', f.read(), re.M).group(1)
WINDOWS = sys.platform == "win32"
ICON = os.path.join(SPECPATH, "Tabularium.ico" if WINDOWS else "Tabularium.icns")

a = Analysis(
    [os.path.join(ROOT, "tabularium_app.py")],
    pathex=[ROOT],
    datas=[(os.path.join(ROOT, "web"), "web")],
    hiddenimports=["tabularium", "tabularium_web"],
    excludes=["tkinter", "_tkinter"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Tabularium",
    console=False,          # keine Konsole; Ausgaben gehen in die Logdatei
    icon=ICON,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="Tabularium", upx=False)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Tabularium.app",
        icon=ICON,
        bundle_identifier="de.tabularium.app",
        version=VERSION,
        info_plist={
            "CFBundleName": "Tabularium",
            "CFBundleDisplayName": "Tabularium",
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "LSUIElement": True,              # kein Dock-Symbol: die Oberfläche ist der Browser
            "LSMinimumSystemVersion": "11.0",
            "NSHumanReadableCopyright": "© 2026 Patrick Baumfalk · MIT-Lizenz",
        },
    )
