from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    script = root_dir / "fetch_vendor.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--all",
            "--platforms=windows,macos",
            "--archs=x64,arm64",
            "--allow-missing",
        ],
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
