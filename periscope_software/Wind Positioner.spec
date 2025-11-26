# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['axis_handler.py'],
    pathex=[],
    binaries=[('.env/Lib/site-packages/nanotec_nanolib/_nanolib_python_3_12.pyd', 'nanotec_nanolib'), ('.env/Lib/site-packages/nanotec_nanolib/*.dll', 'nanotec_nanolib')],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Wind Positioner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
