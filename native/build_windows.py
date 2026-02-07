from pathlib import Path
import os
import shutil
import subprocess
import sys


def run_command(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    stdout = process.stdout
    if stdout is not None:
        for line in stdout:
            print(line, end="")
    process.wait()
    if process.returncode != 0:
        raise SystemExit(process.returncode)


def resolve_exe(build_dir: Path) -> Path:
    candidates = [
        build_dir / "ImgcompressNative.exe",
        build_dir / "Release" / "ImgcompressNative.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise SystemExit("未找到 ImgcompressNative.exe")


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"未找到 {name}，请安装并加入 PATH")


def resolve_cmake() -> str:
    found = shutil.which("cmake")
    if found:
        return found
    dir_candidates = [
        Path("C:/Qt/Tools/CMake_64/bin"),
        Path("C:/Program Files/CMake/bin"),
        Path("C:/Program Files (x86)/CMake/bin"),
    ]
    name_candidates = ["cmake.exe", "cmake", "cmake.bat", "cmake.cmd"]
    for d in dir_candidates:
        for name in name_candidates:
            exe = d / name
            if exe.exists():
                return str(exe)
    raise SystemExit("未找到 cmake，请安装或加入 PATH")


def resolve_windeployqt() -> str:
    found = shutil.which("windeployqt")
    if found:
        return found
    qt_root = Path("C:/Qt")
    if qt_root.exists():
        for version in sorted(qt_root.glob("6.*"), key=lambda p: str(p)):
            for msvc in sorted(version.glob("msvc*"), key=lambda p: str(p)):
                bin_dir = msvc / "bin"
                name_candidates = ["windeployqt.exe", "windeployqt", "windeployqt.bat", "windeployqt.cmd"]
                for name in name_candidates:
                    exe = bin_dir / name
                    if exe.exists():
                        return str(exe)
    raise SystemExit("未找到 windeployqt，请安装或加入 PATH")


def resolve_generator_args(cmake: str) -> list[str]:
    preferred = [
        "Visual Studio 18 2025",
        "Visual Studio 17 2022",
        "Visual Studio 16 2019",
    ]
    try:
        result = subprocess.run([cmake, "--help"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            generators: list[str] = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if "Visual Studio" in line:
                    name = line.split(" - ")[0]
                    generators.append(name)
            for name in preferred:
                if any(name in g for g in generators):
                    return ["-G", name, "-A", "x64"]
    except Exception:
        pass
    return ["-G", "Visual Studio 17 2022", "-A", "x64"]


def ensure_msvc_x64() -> None:
    candidates = [
        Path("C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC"),
        Path("C:/Program Files/Microsoft Visual Studio/17/Community/VC/Tools/MSVC"),
        Path("C:/Program Files (x86)/Microsoft Visual Studio/17/BuildTools/VC/Tools/MSVC"),
    ]
    for base in candidates:
        if not base.exists():
            continue
        for ver in sorted(base.glob("*/bin/Hostx64/x64/cl.exe")):
            if ver.exists():
                return
    raise SystemExit("未发现 x64 MSVC 编译器，请安装 x64 组件或使用 VS 开发者命令提示符")

def resolve_ninja() -> str | None:
    found = shutil.which("ninja")
    if found:
        return found
    dirs = [
        Path("C:/Qt/Tools/Ninja"),
        Path("C:/Program Files/Ninja"),
        Path("C:/Program Files (x86)/Ninja"),
        Path("C:/ProgramData/chocolatey/bin"),
    ]
    names = ["ninja.exe", "ninja"]
    for d in dirs:
        for n in names:
            exe = d / n
            if exe.exists():
                return str(exe)
    return None

def vs_version_exists(major: int) -> bool:
    roots = [
        Path(f"C:/Program Files/Microsoft Visual Studio/{major}"),
        Path(f"C:/Program Files (x86)/Microsoft Visual Studio/{major}"),
    ]
    return any(r.exists() for r in roots)

def has_nmake() -> bool:
    bases = [
        Path("C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC"),
        Path("C:/Program Files/Microsoft Visual Studio/17/Community/VC/Tools/MSVC"),
        Path("C:/Program Files (x86)/Microsoft Visual Studio/17/BuildTools/VC/Tools/MSVC"),
    ]
    for base in bases:
        for exe in base.glob("*/bin/Hostx64/x64/nmake.exe"):
            if exe.exists():
                return True
    return False

def find_msvc_bin_paths() -> list[str]:
    roots = [
        Path("C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC"),
        Path("C:/Program Files/Microsoft Visual Studio/17/Community/VC/Tools/MSVC"),
        Path("C:/Program Files (x86)/Microsoft Visual Studio/17/BuildTools/VC/Tools/MSVC"),
    ]
    found: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for p in root.glob("*/bin/Hostx64/x64"):
            if p.exists():
                found.append(str(p))
    return found

def find_msvc_lib_paths() -> list[str]:
    roots = [
        Path("C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC"),
        Path("C:/Program Files/Microsoft Visual Studio/17/Community/VC/Tools/MSVC"),
        Path("C:/Program Files (x86)/Microsoft Visual Studio/17/BuildTools/VC/Tools/MSVC"),
    ]
    found: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for p in root.glob("*/lib/x64"):
            if p.exists():
                found.append(str(p))
    return found

def find_msvc_include_paths() -> list[str]:
    roots = [
        Path("C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC"),
        Path("C:/Program Files/Microsoft Visual Studio/17/Community/VC/Tools/MSVC"),
        Path("C:/Program Files (x86)/Microsoft Visual Studio/17/BuildTools/VC/Tools/MSVC"),
    ]
    found: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for p in root.glob("*/include"):
            if p.exists():
                found.append(str(p))
    return found

def find_windows_sdk_bin_paths() -> list[str]:
    roots = [
        Path("C:/Program Files (x86)/Windows Kits/11/bin"),
        Path("C:/Program Files/Windows Kits/11/bin"),
        Path("C:/Program Files (x86)/Windows Kits/10/bin"),
        Path("C:/Program Files/Windows Kits/10/bin"),
        Path("D:/Windows Kits/11/bin"),
        Path("D:/Windows Kits/10/bin"),
    ]
    found: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for ver in sorted(root.glob("*/x64"), key=lambda p: str(p), reverse=True):
            rc = ver / "rc.exe"
            mt = ver / "mt.exe"
            if rc.exists() and mt.exists():
                found.append(str(ver))
                break
        x64 = root / "x64"
        if x64.exists():
            rc = x64 / "rc.exe"
            mt = x64 / "mt.exe"
            if rc.exists() and mt.exists():
                found.append(str(x64))
    return found

def find_windows_sdk_lib_paths() -> list[str]:
    roots = [
        Path("C:/Program Files (x86)/Windows Kits/11/Lib"),
        Path("C:/Program Files/Windows Kits/11/Lib"),
        Path("C:/Program Files (x86)/Windows Kits/10/Lib"),
        Path("C:/Program Files/Windows Kits/10/Lib"),
        Path("D:/Windows Kits/11/Lib"),
        Path("D:/Windows Kits/10/Lib"),
    ]
    found: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        versions = sorted(root.glob("*"), key=lambda p: str(p), reverse=True)
        for ver in versions:
            um = ver / "um" / "x64"
            ucrt = ver / "ucrt" / "x64"
            if um.exists() and ucrt.exists():
                found.extend([str(um), str(ucrt)])
                break
    return found

def find_windows_sdk_include_paths() -> list[str]:
    roots = [
        Path("C:/Program Files (x86)/Windows Kits/11/Include"),
        Path("C:/Program Files/Windows Kits/11/Include"),
        Path("C:/Program Files (x86)/Windows Kits/10/Include"),
        Path("C:/Program Files/Windows Kits/10/Include"),
        Path("D:/Windows Kits/11/Include"),
        Path("D:/Windows Kits/10/Include"),
    ]
    found: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        versions = sorted(root.glob("*"), key=lambda p: str(p), reverse=True)
        for ver in versions:
            parts = ["um", "ucrt", "shared", "winrt", "cppwinrt"]
            paths = [ver / part for part in parts]
            if all(p.exists() for p in paths):
                found.extend([str(p) for p in paths])
                break
    return found

def choose_generator(cmake: str) -> list[str]:
    args = resolve_generator_args(cmake)
    name = None
    for i, v in enumerate(args):
        if v == "-G" and i + 1 < len(args):
            name = args[i + 1]
            break
    ninja = resolve_ninja()
    if ninja:
        return ["-G", "Ninja", "-DCMAKE_MAKE_PROGRAM=" + ninja]
    if name == "Visual Studio 18 2025" and vs_version_exists(18):
        return ["-G", "Visual Studio 18 2025", "-A", "x64"]
    if name == "Visual Studio 17 2022" and vs_version_exists(17):
        return ["-G", "Visual Studio 17 2022", "-A", "x64"]
    if has_nmake():
        return ["-G", "NMake Makefiles"]
    return ["-G", "Visual Studio 17 2022", "-A", "x64"]
def expected_generator_from_args(args: list[str]) -> str | None:
    for i, v in enumerate(args):
        if v == "-G" and i + 1 < len(args):
            return args[i + 1]
    return None

def read_cache_generator(build_dir: Path) -> str | None:
    cache = build_dir / "CMakeCache.txt"
    if not cache.exists():
        return None
    try:
        with cache.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line.startswith("CMAKE_GENERATOR:") and "=" in line:
                    return line.split("=", 1)[1]
    except Exception:
        return None
    return None

def ensure_clean_build_dir(build_dir: Path, expected_generator: str | None) -> None:
    if expected_generator is None:
        return
    cached = read_cache_generator(build_dir)
    if cached and cached.strip() != expected_generator.strip():
        if build_dir.exists():
            shutil.rmtree(build_dir)

def resolve_qt_prefix() -> str | None:
    qt_root = Path("C:/Qt")
    if not qt_root.exists():
        return None
    versions = sorted(qt_root.glob("6.*"), key=lambda p: str(p), reverse=True)
    for version in versions:
        for msvc in sorted(version.glob("msvc*"), key=lambda p: str(p), reverse=True):
            cmake_dir = msvc / "lib" / "cmake"
            if cmake_dir.exists():
                return str(msvc).replace("\\", "/")
    return None


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    repo_dir = root_dir.parent
    build_dir = root_dir / "build"
    dist_dir = root_dir / "dist"
    env = dict(os.environ)
    cmake = resolve_cmake()
    generator_args = choose_generator(cmake)
    ensure_msvc_x64()
    msvc_bins = find_msvc_bin_paths()
    if msvc_bins:
        env["PATH"] = ";".join(msvc_bins) + ";" + env.get("PATH", "")
    sdk_bins = find_windows_sdk_bin_paths()
    if sdk_bins:
        env["PATH"] = ";".join(sdk_bins) + ";" + env.get("PATH", "")
    msvc_libs = find_msvc_lib_paths()
    sdk_libs = find_windows_sdk_lib_paths()
    libs: list[str] = []
    libs.extend(msvc_libs)
    libs.extend(sdk_libs)
    if libs:
        env["LIB"] = ";".join(libs) + ";" + env.get("LIB", "")
    msvc_includes = find_msvc_include_paths()
    sdk_includes = find_windows_sdk_include_paths()
    includes: list[str] = []
    includes.extend(msvc_includes)
    includes.extend(sdk_includes)
    if includes:
        env["INCLUDE"] = ";".join(includes) + ";" + env.get("INCLUDE", "")
    qt_prefix = resolve_qt_prefix()
    ensure_clean_build_dir(build_dir, expected_generator_from_args(generator_args))
    extra_args: list[str] = []
    try:
        for i, v in enumerate(generator_args):
            if v == "-G" and i + 1 < len(generator_args) and generator_args[i + 1] == "Ninja":
                extra_args.extend(["-DCMAKE_C_COMPILER=cl", "-DCMAKE_CXX_COMPILER=cl", "-DCMAKE_RC_COMPILER=rc", "-DCMAKE_MT=mt"])
                break
    except Exception:
        pass
    run_command(
        [
            cmake,
            "-S",
            str(root_dir),
            "-B",
            str(build_dir),
            "-DCMAKE_BUILD_TYPE=Release",
            *generator_args,
            *(["-DCMAKE_PREFIX_PATH=" + qt_prefix] if qt_prefix else []),
            *extra_args,
        ],
        root_dir,
        env,
    )
    run_command([cmake, "--build", str(build_dir), "--config", "Release"], root_dir, env)
    exe_path = resolve_exe(build_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)
    dist_exe = dist_dir / "ImgcompressNative.exe"
    shutil.copy2(exe_path, dist_exe)
    windeployqt = resolve_windeployqt()
    run_command([windeployqt, str(dist_exe)], root_dir, env)
    vendor_src = repo_dir / "vendor"
    vendor_dst = dist_dir / "vendor"
    if vendor_src.is_dir():
        if vendor_dst.exists():
            shutil.rmtree(vendor_dst)
        shutil.copytree(vendor_src, vendor_dst)
    print(f"已生成：{dist_exe}")


if __name__ == "__main__":
    main()
