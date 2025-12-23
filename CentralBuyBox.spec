# -*- mode: python ; coding: utf-8 -*-
# CentralBuyBox.spec - Configuração do PyInstaller

a = Analysis(
    ['app_principal.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data', 'data'),           # Inclui a pasta data (logo, etc)
        ('config', 'config'),       # Inclui a pasta config
    ],
    hiddenimports=[
        'mysql.connector',
        'mysql.connector.plugins',
        'mysql.connector.plugins.caching_sha2_password',
        'flet',
        'pandas',
        'openpyxl',
    ],
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
    name='CentralBuyBox',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['data/logo.ico'],
)
