import subprocess
import sys


def main() -> None:
    subprocess.run([sys.executable, "-m", "PyInstaller", "imgcompress.spec"], check=True)


if __name__ == "__main__":
    main()
