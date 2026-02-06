from pathlib import Path
import os
import sys

meipass = getattr(sys, "_MEIPASS", None)
base_dir: Path | None = None
if meipass:
    base_dir = Path(meipass)
elif sys.platform == "darwin":
    executable = Path(sys.executable).resolve()
    contents_dir = executable.parent.parent
    resources_dir = contents_dir / "Resources"
    macos_dir = contents_dir / "MacOS"
    candidates = [resources_dir, macos_dir]
    for candidate in candidates:
        platforms = candidate / "PySide6" / "Qt" / "plugins" / "platforms"
        if platforms.is_dir():
            base_dir = candidate
            break
if base_dir is not None:
    plugins_root = base_dir / "PySide6" / "Qt" / "plugins"
    platforms_root = plugins_root / "platforms"
    libs_root = base_dir / "PySide6" / "Qt" / "lib"
    os.environ.setdefault("QT_PLUGIN_PATH", str(plugins_root))
    os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(platforms_root))
    existing_dyld = os.environ.get("DYLD_LIBRARY_PATH", "")
    dyld_paths = [str(libs_root)] + ([existing_dyld] if existing_dyld else [])
    os.environ["DYLD_LIBRARY_PATH"] = ":".join([p for p in dyld_paths if p])
    existing_fallback = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
    fallback_paths = [str(libs_root)] + ([existing_fallback] if existing_fallback else [])
    os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join([p for p in fallback_paths if p])

from imgcompress.app import main


if __name__ == "__main__":
    main()
