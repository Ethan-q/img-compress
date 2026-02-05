import os
import shutil

block_cipher = None


def _vendor_binaries():
    local_dir = os.path.join(os.path.dirname(__file__), "vendor")
    if not os.path.isdir(local_dir):
        return []
    binaries = []
    for root, _, files in os.walk(local_dir):
        for name in files:
            path = os.path.join(root, name)
            rel_path = os.path.relpath(path, os.path.dirname(__file__))
            dest_dir = os.path.dirname(rel_path)
            binaries.append((path, dest_dir))
    return binaries

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=_vendor_binaries(),
    datas=[],
    hiddenimports=["PIL"],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Imgcompress",
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
)
