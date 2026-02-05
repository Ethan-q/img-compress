from pathlib import Path
import subprocess
import sys


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    spec_path = root_dir / "imgcompress.spec"
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(spec_path)],
        cwd=str(root_dir),
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
