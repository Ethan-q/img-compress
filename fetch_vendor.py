from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path
from typing import Iterable
from urllib.request import Request, urlopen


VENDOR_DIR = Path(__file__).resolve().parent / "vendor"
GITHUB_API = "https://api.github.com"
PLATFORMS = ["windows", "macos", "linux"]
ARCHS = ["x64", "arm64"]

TOOLS = {
    "pngquant": {
        "repo": "imagemin/pngquant-bin",
        "binary_names": ["pngquant"],
        "source": "contents",
    },
    "optipng": {
        "repo": "imagemin/optipng-bin",
        "binary_names": ["optipng"],
        "source": "contents",
    },
    "cjpeg": {
        "repo": "imagemin/mozjpeg-bin",
        "binary_names": ["cjpeg"],
        "source": "contents",
    },
    "jpegtran": {
        "repo": "imagemin/jpegtran-bin",
        "binary_names": ["jpegtran"],
        "source": "contents",
    },
    "gifsicle": {
        "repo": "imagemin/gifsicle-bin",
        "binary_names": ["gifsicle"],
        "source": "contents",
    },
    "cwebp": {
        "repo": "imagemin/cwebp-bin",
        "binary_names": ["cwebp"],
        "source": "contents",
    },
}


def main() -> None:
    args = parse_args(sys.argv[1:])
    VENDOR_DIR.mkdir(parents=True, exist_ok=True)
    for name in args.tools:
        tool = TOOLS[name]
        files = list_repo_files(tool["repo"], tool["source"])
        for platform_key in args.platforms:
            for arch_key in args.archs:
                selected = select_binary(files, tool["binary_names"], platform_key, arch_key)
                if not selected:
                    raise RuntimeError(f"未找到可用二进制：{name} ({platform_key}/{arch_key})")
                target_dir = VENDOR_DIR / platform_key / arch_key
                target_dir.mkdir(parents=True, exist_ok=True)
                target = target_dir / output_name(selected["name"], platform_key)
                download(selected["download_url"], target)
                ensure_executable(target, platform_key)
                print(f"{name} -> {target}")


def parse_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("tools", nargs="*", help="pngquant optipng cjpeg jpegtran gifsicle cwebp")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--platforms", default="")
    parser.add_argument("--archs", default="")
    parsed = parser.parse_args(args)
    tools = list(TOOLS.keys()) if parsed.all or not parsed.tools else parsed.tools
    unknown = [tool for tool in tools if tool not in TOOLS]
    if unknown:
        raise ValueError(f"未知工具：{', '.join(unknown)}")
    parsed.tools = tools
    parsed.platforms = normalize_targets(parsed.platforms, PLATFORMS, detect_platform())
    parsed.archs = normalize_targets(parsed.archs, ARCHS, detect_arch())
    return parsed


def normalize_targets(raw: str, allowed: list[str], default_value: str) -> list[str]:
    if not raw:
        return [default_value]
    if raw == "all":
        return allowed
    values = [item.strip() for item in raw.split(",") if item.strip()]
    unknown = [item for item in values if item not in allowed]
    if unknown:
        raise ValueError(f"未知平台或架构：{', '.join(unknown)}")
    return values


def list_repo_files(repo: str, source: str) -> list[dict[str, str]]:
    if source == "contents":
        return list_contents_recursive(repo, "vendor")
    raise ValueError(f"不支持的资源类型：{source}")


def list_contents_recursive(repo: str, path: str) -> list[dict[str, str]]:
    url = f"{GITHUB_API}/repos/{repo}/contents/{path}"
    payload = github_get(url)
    files: list[dict[str, str]] = []
    for item in payload:
        if item.get("type") == "dir":
            files.extend(list_contents_recursive(repo, item["path"]))
        elif item.get("type") == "file" and item.get("download_url"):
            files.append(
                {
                    "name": item["name"],
                    "path": item["path"],
                    "download_url": item["download_url"],
                }
            )
    return files


def select_binary(
    files: Iterable[dict[str, str]],
    names: list[str],
    platform_key: str,
    arch_key: str,
) -> dict[str, str] | None:
    candidates = [item for item in files if is_name_match(item["name"], names)]
    if not candidates:
        return None
    scored = [(score_candidate(item, platform_key, arch_key), item) for item in candidates]
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1]


def detect_platform() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def detect_arch() -> str:
    machine = os.uname().machine.lower()
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    if machine in {"x86_64", "amd64"}:
        return "x64"
    return machine


def score_candidate(item: dict[str, str], platform_key: str, arch_key: str) -> int:
    text = f"{item['name']} {item['path']}".lower()
    score = 0
    score += match_score(text, platform_tokens(platform_key)) * 3
    score += match_score(text, arch_tokens(arch_key)) * 2
    return score


def match_score(text: str, tokens: Iterable[str]) -> int:
    return sum(1 for token in tokens if token and token in text)


def platform_tokens(platform_key: str) -> list[str]:
    if platform_key == "windows":
        return ["win", "windows", "win32", "win64", "mingw", "msvc"]
    if platform_key == "macos":
        return ["mac", "macos", "darwin", "osx"]
    return ["linux", "gnu", "ubuntu", "debian", "centos"]


def arch_tokens(arch_key: str) -> list[str]:
    if arch_key == "arm64":
        return ["arm64", "aarch64", "arm"]
    if arch_key == "x64":
        return ["x64", "amd64", "x86_64"]
    return [arch_key]


def is_name_match(filename: str, names: Iterable[str]) -> bool:
    base = Path(filename).name
    stem = Path(filename).stem
    return any(base == name or stem == name for name in names)


def output_name(filename: str, platform_key: str) -> str:
    if platform_key == "windows" and not filename.endswith(".exe"):
        return f"{filename}.exe"
    if platform_key != "windows" and filename.endswith(".exe"):
        return Path(filename).stem
    return filename


def download(url: str, target: Path) -> None:
    request = Request(url, headers={"User-Agent": "imgcompress-fetcher"})
    with urlopen(request) as response:
        data = response.read()
    temp = target.with_suffix(target.suffix + ".partial")
    temp.write_bytes(data)
    temp.replace(target)


def ensure_executable(path: Path, platform_key: str) -> None:
    if platform_key == "windows":
        return
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def github_get(url: str) -> list[dict]:
    request = Request(url, headers={"User-Agent": "imgcompress-fetcher"})
    with urlopen(request) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


if __name__ == "__main__":
    main()
