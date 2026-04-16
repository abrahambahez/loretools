# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all, collect_data_files

datas, binaries, hiddenimports = [], [], []
for _pkg in ["pydantic", "pydantic_core", "loretools"]:
    _d, _b, _h = collect_all(_pkg)
    datas += _d; binaries += _b; hiddenimports += _h

datas += collect_data_files("loretools")

a = Analysis(
    [os.path.join(SPECPATH, "..", "loretools", "cli", "__init__.py")],
    pathex=[os.path.join(SPECPATH, "..")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + [
        "pdfplumber",
        "pdfplumber.utils",
        "pdfminer",
        "pdfminer.high_level",
        "pdfminer.layout",
        "pdfminer.pdfpage",
        "pdfminer.converter",
        "annotated_types",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    exclude_binaries=False,
    name="lore",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
