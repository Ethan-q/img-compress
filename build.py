from pathlib import Path
import subprocess
import sys
import tempfile


def run_command(command: list[str], cwd: Path) -> None:
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
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
    spec_path = root_dir / "imgcompress.spec"
    work_dir = Path(tempfile.mkdtemp(prefix="imgcompress_work_"))
    print("开始 PyInstaller 打包...")
    run_command(
        [sys.executable, "-m", "PyInstaller", "--workpath", str(work_dir), str(spec_path)],
        root_dir,
    )


if __name__ == "__main__":
    main()
