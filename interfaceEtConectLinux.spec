# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['interfaceEtConect.py'],
    pathex=['/home/paul/Documents/Scolaire/2023-2024/Stage_Afleloo/Code/gcodeToIselCPM'],
    binaries=[],
    datas=[
        ('img/home.png', 'img'),
        ('img/laser.png', 'img'),
        ('img/mouv.png', 'img'),
        ('img/mouvZ.png', 'img'),
        ('img/open.png', 'img'),
        ('img/outilO.png', 'img'),
        ('img/outilS.png', 'img'),
        ('img/PowerLaser.png', 'img'),
        ('img/spot0.png', 'img'),
        ('img/start.png', 'img'),
        ('img/start2.png', 'img'),
        ('img/Visu.png', 'img')
    ],
    hiddenimports=['tkinter', 'PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='gcodeToIselCPM',
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
    icon='img/apli.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='IselAPP'
)
