from pathlib import Path
import os
import subprocess
import sys


def run_command(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    build_py = root_dir / "build.py"
    run_command([sys.executable, str(build_py)], root_dir, dict(os.environ))
    dist_bin = root_dir / "dist" / "Imgcompress"
    if not dist_bin.exists():
        raise SystemExit(f"未找到可执行文件：{dist_bin}")
    dmg_path = root_dir / "dist" / "Imgcompress.dmg"
    if dmg_path.exists():
        dmg_path.unlink()
    run_command(
        [
            "hdiutil",
            "create",
            "-volname",
            "Imgcompress",
            "-srcfolder",
            str(dist_bin),
            "-ov",
            "-format",
            "UDZO",
            str(dmg_path),
        ],
        root_dir,
        dict(os.environ),
    )
    print(f"已生成：{dmg_path}")


if __name__ == "__main__":
    main()
