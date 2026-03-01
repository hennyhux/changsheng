# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Changsheng - Truck Lot Tracker
Builds a standalone Windows executable with all dependencies bundled
"""

import sys
from PyInstaller.utils.hooks import collect_submodules, collect_all

block_cipher = None


def _extend_package_bundle(package_name: str, hidden_imports: list[str], datas: list[tuple], binaries: list[tuple]) -> None:
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(package_name)
    except Exception:
        return
    datas.extend(pkg_datas)
    binaries.extend(pkg_binaries)
    hidden_imports.extend(pkg_hidden)

# Hidden imports required by the application
hidden_imports = [
    'tkinter',
    'sqlite3',
    'json',
    'csv',
    'logging',
    'logging.handlers',
    'datetime',
    'openpyxl',  # Optional but included if available
]

datas = [
    ('app/logo.png', 'app'),
    ('app/logo.png', '.'),
]
binaries = []

# Collect submodules from our application packages and tkinter
hidden_imports.extend(collect_submodules('tkinter'))
hidden_imports.extend(collect_submodules('app'))
hidden_imports.extend(collect_submodules('core'))
hidden_imports.extend(collect_submodules('utils'))
hidden_imports.extend(collect_submodules('data'))
hidden_imports.extend(collect_submodules('invoicing'))
hidden_imports.extend(collect_submodules('dialogs'))
hidden_imports.extend(collect_submodules('ui'))
hidden_imports.extend(collect_submodules('tabs'))
hidden_imports.extend(collect_submodules('reportlab'))
hidden_imports.extend(collect_submodules('tkcalendar'))
hidden_imports.extend(collect_submodules('openpyxl'))

# Bundle dependency package data/binaries used at runtime.
for dependency_pkg in ('reportlab', 'tkcalendar', 'babel', 'openpyxl', 'PIL'):
    _extend_package_bundle(dependency_pkg, hidden_imports, datas, binaries)

# Remove duplicates while preserving deterministic ordering.
hidden_imports = list(dict.fromkeys(hidden_imports))
datas = list(dict.fromkeys(datas))
binaries = list(dict.fromkeys(binaries))

a = Analysis(
    ['changsheng.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='changsheng',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add path to .ico file if available
)

# Optional: Create a distribution folder
# Uncomment to generate a folder with all dependencies
"""
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='changsheng',
)
"""
