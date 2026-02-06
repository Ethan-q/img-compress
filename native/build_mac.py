from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile


def run_command(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
        env=env,
    )
    stdout = process.stdout
    if stdout is not None:
        for line in stdout:
            print(line, end="")
    process.wait()
    if process.returncode != 0:
        raise SystemExit(process.returncode)


def resolve_app(build_dir: Path) -> Path:
    candidates = [
        build_dir / "ImgcompressNative.app",
        build_dir / "Release" / "ImgcompressNative.app",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise SystemExit("未找到 ImgcompressNative.app")


def resolve_qtpaths(env: dict[str, str]) -> str:
    qtpaths_env = env.get("QT_PATHS")
    if qtpaths_env:
        return qtpaths_env
    candidates = [
        shutil.which("qtpaths"),
        shutil.which("qtpaths6"),
        "/opt/homebrew/opt/qt/bin/qtpaths",
        "/opt/homebrew/opt/qt/bin/qtpaths6",
        "/usr/local/opt/qt/bin/qtpaths",
        "/usr/local/opt/qt/bin/qtpaths6",
    ]
    for item in candidates:
        if item and Path(item).exists():
            return str(item)
    raise SystemExit("未找到 qtpaths 或 qtpaths6")


def read_qt_plugin_dir(env: dict[str, str]) -> Path:
    qtpaths = resolve_qtpaths(env)
    output = subprocess.check_output([qtpaths, "--plugin-dir"], text=True, env=env).strip()
    if not output:
        raise SystemExit("无法获取 Qt 插件目录")
    return Path(output)


def copy_plugin_files(plugin_dir: Path, app_path: Path, group: str, names: list[str]) -> None:
    src_dir = plugin_dir / group
    if not src_dir.exists():
        return
    dest_dir = app_path / "Contents" / "PlugIns" / group
    dest_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        src = src_dir / name
        if src.exists():
            shutil.copy2(src, dest_dir / name)


def copy_app(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, symlinks=True, copy_function=shutil.copy2)


def resolve_codesign(env: dict[str, str]) -> str:
    codesign = shutil.which("codesign")
    if codesign is None:
        raise SystemExit("未找到 codesign")
    return codesign


def build_codesign_args(identity: str) -> list[str]:
    args = ["--force", "--sign", identity]
    if identity == "-":
        args.append("--timestamp=none")
        return args
    return [*args, "--timestamp", "--options", "runtime"]


def sign_item(path: Path, env: dict[str, str]) -> None:
    codesign = resolve_codesign(env)
    identity = env.get("SIGN_IDENTITY", "-")
    run_command(
        [
            codesign,
            *build_codesign_args(identity),
            str(path),
        ],
        path.parent,
        env,
    )


def is_macho_file(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            magic = handle.read(4)
    except OSError:
        return False
    return magic in {
        b"\xfe\xed\xfa\xce",
        b"\xfe\xed\xfa\xcf",
        b"\xcf\xfa\xed\xfe",
        b"\xca\xfe\xba\xbe",
        b"\xbe\xba\xfe\xca",
        b"\xca\xfe\xba\xbf",
        b"\xbf\xba\xfe\xca",
    }


def iter_macho_files(app_path: Path):
    seen: set[str] = set()
    for root, _, files in os.walk(app_path):
        for name in files:
            path = Path(root) / name
            if any(part.endswith(".framework") for part in path.parts):
                continue
            real_path = path
            if path.is_symlink():
                try:
                    real_path = path.resolve()
                except OSError:
                    continue
            if not real_path.exists() or not real_path.is_file():
                continue
            if is_macho_file(real_path):
                key = str(real_path)
                if key in seen:
                    continue
                seen.add(key)
                yield real_path


def deploy_qt_plugins(app_path: Path, env: dict[str, str]) -> None:
    plugin_dir = read_qt_plugin_dir(env)
    copy_plugin_files(plugin_dir, app_path, "platforms", ["libqcocoa.dylib"])
    copy_plugin_files(
        plugin_dir,
        app_path,
        "imageformats",
        ["libqjpeg.dylib", "libqpng.dylib", "libqgif.dylib", "libqwebp.dylib"],
    )
    copy_plugin_files(plugin_dir, app_path, "styles", ["libqmacstyle.dylib"])


def deploy_vendor(app_path: Path, repo_dir: Path) -> None:
    resources_dir = app_path / "Contents" / "Resources"
    resources_dir.mkdir(parents=True, exist_ok=True)
    vendor_src = repo_dir / "vendor"
    vendor_dst = resources_dir / "vendor"
    if vendor_src.is_dir():
        if vendor_dst.exists():
            shutil.rmtree(vendor_dst)
        shutil.copytree(vendor_src, vendor_dst)


def has_framework_info(framework_path: Path) -> bool:
    return (framework_path / "Resources" / "Info.plist").exists() or (
        framework_path / "Versions" / "Current" / "Resources" / "Info.plist"
    ).exists()


def sign_app(app_path: Path, env: dict[str, str]) -> None:
    frameworks_dir = app_path / "Contents" / "Frameworks"
    if frameworks_dir.exists():
        for item in frameworks_dir.iterdir():
            if item.suffix == ".framework":
                framework_binary = item / "Versions" / "Current" / item.stem
                if framework_binary.exists():
                    try:
                        framework_binary = framework_binary.resolve()
                    except OSError:
                        pass
                    sign_item(framework_binary, env)
                if has_framework_info(item):
                    sign_item(item, env)
    targets = sorted(iter_macho_files(app_path), key=lambda item: str(item))
    for path in targets:
        sign_item(path, env)
    sign_item(app_path, env)


def build_dmg(staging_dir: Path, dist_dir: Path, env: dict[str, str]) -> Path:
    if shutil.which("hdiutil") is None:
        raise SystemExit("未找到 hdiutil")
    dmg_path = dist_dir / "ImgcompressNative.dmg"
    if dmg_path.exists():
        dmg_path.unlink()
    run_command(
        [
            "hdiutil",
            "create",
            "-volname",
            "ImgcompressNative",
            "-srcfolder",
            str(staging_dir),
            "-ov",
            "-format",
            "UDZO",
            str(dmg_path),
        ],
        dist_dir,
        env,
    )
    if not dmg_path.exists():
        raise SystemExit("dmg 生成失败")
    return dmg_path


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    repo_dir = root_dir.parent
    build_dir = root_dir / "build"
    dist_dir = root_dir / "dist"
    env = dict(os.environ)
    run_command(
        [
            "cmake",
            "-S",
            str(root_dir),
            "-B",
            str(build_dir),
            "-DCMAKE_BUILD_TYPE=Release",
            "-DCMAKE_DISABLE_FIND_PACKAGE_Vulkan=ON",
        ],
        root_dir,
        env,
    )
    run_command(["cmake", "--build", str(build_dir), "--config", "Release"], root_dir, env)
    app_path = resolve_app(build_dir)
    run_command(["macdeployqt", str(app_path), "-no-plugins"], root_dir, env)
    deploy_qt_plugins(app_path, env)
    deploy_vendor(app_path, repo_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)
    dist_app = dist_dir / "ImgcompressNative.app"
    if dist_app.exists():
        shutil.rmtree(dist_app)
    copy_app(app_path, dist_app)
    sign_app(dist_app, env)
    staging_dir = Path(tempfile.mkdtemp(prefix="imgcompress_native_dmg_"))
    keep_staging = env.get("KEEP_STAGING", "").lower() in {"1", "true", "yes"}
    try:
        app_target = staging_dir / "ImgcompressNative.app"
        copy_app(dist_app, app_target)
        apps_link = staging_dir / "Applications"
        if apps_link.exists():
            apps_link.unlink()
        os.symlink("/Applications", apps_link)
        dmg_path = build_dmg(staging_dir, dist_dir, env)
        print(f"已生成：{dist_app}")
        print(f"已生成：{dmg_path}")
    finally:
        if not keep_staging and staging_dir.exists():
            shutil.rmtree(staging_dir)


if __name__ == "__main__":
    main()
