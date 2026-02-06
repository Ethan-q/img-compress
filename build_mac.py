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


def resolve_codesign(env: dict[str, str]) -> str:
    codesign = shutil.which("codesign")
    if codesign is None:
        raise SystemExit("未找到 codesign")
    return codesign


def sign_item(path: Path, env: dict[str, str]) -> None:
    codesign = resolve_codesign(env)
    identity = env.get("SIGN_IDENTITY", "-")
    run_command(
        [
            codesign,
            "--force",
            "--sign",
            identity,
            "--timestamp=none",
            str(path),
        ],
        path.parent,
        env,
    )


def copy_app(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, symlinks=True, copy_function=shutil.copy2)


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


def sign_app(app_path: Path, env: dict[str, str]) -> None:
    for path in iter_macho_files(app_path):
        sign_item(path, env)
    sign_item(app_path, env)


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    build_py = root_dir / "build.py"
    print("开始 PyInstaller 打包...")
    run_command([sys.executable, str(build_py)], root_dir, dict(os.environ))
    dist_app = root_dir / "dist" / "Imgcompress.app"
    if not dist_app.exists():
        raise SystemExit(f"未找到应用包：{dist_app}")
    print("开始 codesign...")
    sign_app(dist_app, dict(os.environ))
    staging_dir = Path(tempfile.mkdtemp(prefix="imgcompress_dmg_"))
    app_target = staging_dir / "Imgcompress.app"
    copy_app(dist_app, app_target)
    apps_link = staging_dir / "Applications"
    if apps_link.exists():
        apps_link.unlink()
    os.symlink("/Applications", apps_link)
    dmg_path = root_dir / "dist" / "Imgcompress.dmg"
    if dmg_path.exists():
        dmg_path.unlink()
    print("开始制作 dmg...")
    run_command(
        [
            "hdiutil",
            "create",
            "-volname",
            "Imgcompress",
            "-srcfolder",
            str(staging_dir),
            "-ov",
            "-format",
            "UDZO",
            str(dmg_path),
        ],
        root_dir,
        dict(os.environ),
    )
    shutil.rmtree(staging_dir)
    pkg_path = root_dir / "dist" / "Imgcompress.pkg"
    if pkg_path.exists():
        pkg_path.unlink()
    print("开始制作 pkg...")
    run_command(
        [
            "pkgbuild",
            "--install-location",
            "/Applications",
            "--component",
            str(dist_app),
            str(pkg_path),
        ],
        root_dir,
        dict(os.environ),
    )
    print(f"已生成：{dmg_path}")
    print(f"已生成：{pkg_path}")


if __name__ == "__main__":
    main()
