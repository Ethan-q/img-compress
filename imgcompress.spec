import os
import shutil
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None


qt_binaries = collect_dynamic_libs("PySide6")
qt_datas = collect_data_files("PySide6", include_py_files=False)
qt_hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
]


def _vendor_binaries():
    base_dir = os.path.dirname(__file__) if "__file__" in globals() else os.getcwd()
    local_dir = os.path.join(base_dir, "vendor")
    if not os.path.isdir(local_dir):
        return []
    binaries = []
    for root, _, files in os.walk(local_dir):
        for name in files:
            path = os.path.join(root, name)
            if name.startswith("."):
                continue
            if os.path.getsize(path) == 0:
                continue
            rel_path = os.path.relpath(path, base_dir)
            dest_dir = os.path.dirname(rel_path)
            binaries.append((path, dest_dir))
    return binaries

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=_vendor_binaries() + qt_binaries,
    datas=qt_datas,
    hiddenimports=["PIL", *qt_hiddenimports],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PySide6.scripts.deploy_lib",
        "PySide6.QtSql",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtQuickWidgets",
        "PySide6.QtQuickControls2",
        "PySide6.QtQuick3D",
        "PySide6.QtMultimedia",
        "PySide6.QtWebEngine",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
    ],
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
    name="Imgcompress",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    exclude_binaries=sys.platform == "darwin",
    disable_windowed_traceback=False,
    argv_emulation=sys.platform == "darwin",
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

if sys.platform == "darwin":
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        name="Imgcompress",
        strip=False,
        upx=False,
        upx_exclude=[],
    )
    app = BUNDLE(
        coll,
        name="Imgcompress.app",
        icon=None,
        bundle_identifier="com.imgcompress.app",
    )
else:
    app = exe
