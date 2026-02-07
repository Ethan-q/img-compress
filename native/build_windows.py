from pathlib import Path
import os
import shutil
import subprocess
import sys


def run_command(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    stdout = process.stdout
    if stdout is not None:
        for line in stdout:
            print(line, end="")
    process.wait()
    if process.returncode != 0:
        raise SystemExit(process.returncode)


def resolve_exe(build_dir: Path) -> Path:
    candidates = [
        build_dir / "ImgcompressNative.exe",
        build_dir / "Release" / "ImgcompressNative.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise SystemExit("未找到 ImgcompressNative.exe")


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    repo_dir = root_dir.parent
    build_dir = root_dir / "build"
    dist_dir = root_dir / "dist"
    env = dict(os.environ)
    run_command(
        ["cmake", "-S", str(root_dir), "-B", str(build_dir), "-DCMAKE_BUILD_TYPE=Release"],
        root_dir,
        env,
    )
    run_command(["cmake", "--build", str(build_dir), "--config", "Release"], root_dir, env)
    exe_path = resolve_exe(build_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)
    dist_exe = dist_dir / "ImgcompressNative.exe"
    shutil.copy2(exe_path, dist_exe)
    run_command(["windeployqt", str(dist_exe)], root_dir, env)
    vendor_src = repo_dir / "vendor"
    vendor_dst = dist_dir / "vendor"
    if vendor_src.is_dir():
        if vendor_dst.exists():
            shutil.rmtree(vendor_dst)
        shutil.copytree(vendor_src, vendor_dst)
    print(f"已生成：{dist_exe}")


if __name__ == "__main__":
    main()
