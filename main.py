from pathlib import Path
import os
import sys

meipass = getattr(sys, "_MEIPASS", None)
candidate_dirs: list[Path] = []
if meipass:
    candidate_dirs.append(Path(meipass))
executable = Path(sys.executable).resolve()
if sys.platform == "darwin":
    contents_dir = executable.parent.parent
    candidate_dirs.extend(
        [
            contents_dir / "Resources",
            contents_dir / "MacOS",
            contents_dir / "Frameworks",
            contents_dir / "PlugIns",
        ]
    )
else:
    candidate_dirs.append(executable.parent)
plugin_roots: list[Path] = []
platform_roots: list[Path] = []
libs_roots: list[Path] = []
for candidate in candidate_dirs:
    plugins_candidates = [
        candidate / "PySide6" / "Qt" / "plugins",
        candidate / "Qt" / "plugins",
        candidate / "plugins",
        candidate / "PlugIns",
    ]
    libs_candidates = [
        candidate / "PySide6" / "Qt" / "lib",
        candidate / "Qt" / "lib",
        candidate / "Frameworks",
    ]
    if candidate.name in {"plugins", "PlugIns"}:
        plugins_candidates.insert(0, candidate)
    for plugins_root in plugins_candidates:
        platforms_root = plugins_root / "platforms"
        if plugins_root.is_dir():
            plugin_roots.append(plugins_root)
        if platforms_root.is_dir():
            platform_roots.append(platforms_root)
    for libs_root in libs_candidates:
        if libs_root.is_dir():
            libs_roots.append(libs_root)
if plugin_roots:
    plugin_value = ":".join(str(path) for path in dict.fromkeys(plugin_roots))
    os.environ["QT_PLUGIN_PATH"] = plugin_value
if platform_roots:
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platform_roots[0])
if libs_roots:
    libs_value = ":".join(str(path) for path in dict.fromkeys(libs_roots))
    existing_dyld = os.environ.get("DYLD_LIBRARY_PATH", "")
    dyld_paths = [libs_value] + ([existing_dyld] if existing_dyld else [])
    os.environ["DYLD_LIBRARY_PATH"] = ":".join([p for p in dyld_paths if p])
    existing_fallback = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
    fallback_paths = [libs_value] + ([existing_fallback] if existing_fallback else [])
    os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join([p for p in fallback_paths if p])

from imgcompress.app import main


if __name__ == "__main__":
    main()
