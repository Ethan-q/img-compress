from pathlib import Path
import subprocess
import sys


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    spec_path = root_dir / "imgcompress.spec"
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(spec_path)],
        cwd=str(root_dir),
        check=True,
    )


if __name__ == "__main__":
    main()
