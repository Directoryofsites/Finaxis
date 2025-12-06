# contapy_backend.spec (Versión con Sintaxis 100% Corregida)
import os
import sys

CWD = os.getcwd()

block_cipher = None

a = Analysis(
    ['app/main.py'],
    pathex=[CWD],
    binaries=[],

    datas=[
        (os.path.join(CWD, 'app', 'templates'), 'app/templates'),
        (os.path.join(CWD, '.env'), '.'),
    ],

    hiddenimports=['passlib.handlers.bcrypt'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='contapy_backend',
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
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='contapy_backend',
)