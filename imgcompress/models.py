from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class CompressOptions:
    input_dir: Path
    output_dir: Path
    lossless: bool
    quality: int
    quality_profile: str
    output_mode: str
    formats: set[str]


@dataclass(frozen=True)
class CompressResult:
    source: Path
    output: Path
    original_size: int
    compressed_size: int
    success: bool
    message: str
    engine: str


def iter_image_files(root: Path, formats: Iterable[str]) -> list[Path]:
    patterns = {f".{fmt.lower()}" for fmt in formats}
    files = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in patterns:
            files.append(path)
    return files
