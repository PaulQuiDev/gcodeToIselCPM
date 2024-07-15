# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['interfaceEtConect.py'],
    pathex=['C:\\Users\\Paul\\OneDrive - De Vinci\\Bureau\\Scolaire\\2023-2024\\Stage Afleloo\\Code\\gcodeToIselCPM'],
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
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='mon_executable',
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

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='mon_executable'
)
