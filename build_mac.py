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


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    build_py = root_dir / "build.py"
    print("开始 PyInstaller 打包...")
    run_command([sys.executable, str(build_py)], root_dir, dict(os.environ))
    dist_app = root_dir / "dist" / "Imgcompress.app"
    if not dist_app.exists():
        raise SystemExit(f"未找到应用包：{dist_app}")
    print("开始 codesign...")
    run_command(
        ["codesign", "--force", "--deep", "--sign", "-", str(dist_app)],
        root_dir,
        dict(os.environ),
    )
    staging_dir = Path(tempfile.mkdtemp(prefix="imgcompress_dmg_"))
    app_target = staging_dir / "Imgcompress.app"
    shutil.copytree(dist_app, app_target)
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
