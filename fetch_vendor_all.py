from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    script = root_dir / "fetch_vendor.py"
    subprocess.run([sys.executable, str(script), "--all"], cwd=str(root_dir), check=True)


if __name__ == "__main__":
    main()
