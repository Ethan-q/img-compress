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
    spec_path = root_dir / "imgcompress.spec"
    cache_dir = root_dir / ".pyinstaller_cache"
    env = dict(os.environ)
    env["PYINSTALLER_CACHE_DIR"] = str(cache_dir)
    run_command([sys.executable, "-m", "PyInstaller", str(spec_path)], root_dir, env)
    dist_exe = root_dir / "dist" / "Imgcompress.exe"
    if not dist_exe.exists():
        raise SystemExit(f"未找到可执行文件：{dist_exe}")
    print(f"已生成：{dist_exe}")


if __name__ == "__main__":
    main()
