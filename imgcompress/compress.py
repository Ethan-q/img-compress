from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
from typing import Iterable

from PIL import Image, ImageSequence

from .models import CompressOptions, CompressResult


def compress_files(files: Iterable[Path], options: CompressOptions) -> list[CompressResult]:
    results = []
    for source in files:
        results.append(compress_file(source, options))
    return results


def compress_file(source: Path, options: CompressOptions) -> CompressResult:
    output = build_output_path(source, options)
    output.parent.mkdir(parents=True, exist_ok=True)
    original_size = source.stat().st_size
    suffix = source.suffix.lower()
    if suffix == ".jpg" or suffix == ".jpeg":
        compress_jpeg(source, output, options)
        optimize_jpeg(output)
    elif suffix == ".png":
        compress_png(source, output, options)
        optimize_png(output, options.lossless)
    elif suffix == ".gif":
        compress_gif(source, output, options)
        optimize_gif(output)
    elif suffix == ".webp":
        compress_webp(source, output, options)
    else:
        return CompressResult(source, output, original_size, original_size, False, "不支持的格式")
    compressed_size = output.stat().st_size if output.exists() else original_size
    if output.exists() and compressed_size > original_size:
        shutil.copy2(source, output)
        compressed_size = original_size
    return CompressResult(source, output, original_size, compressed_size, True, "成功")


def build_output_path(source: Path, options: CompressOptions) -> Path:
    output_mode = getattr(options, "output_mode", "mirror")
    if output_mode == "same_dir":
        candidate = source.parent / f"{source.stem}{source.suffix}"
        return ensure_unique_path(candidate, source.stem, source.suffix)
    if source.is_relative_to(options.input_dir):
        relative = source.relative_to(options.input_dir)
        candidate = options.output_dir / relative
    else:
        candidate = options.output_dir / source.name
    return ensure_unique_path(candidate, source.stem, source.suffix)


def ensure_unique_path(path: Path, source_stem: str, source_suffix: str) -> Path:
    if not path.exists():
        return path
    parent = path.parent
    index = 1
    while True:
        candidate = parent / f"{source_stem}({index}){source_suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def compress_jpeg(source: Path, output: Path, options: CompressOptions) -> None:
    if options.lossless:
        jpegtran = get_tool_executable(["jpegtran"])
        if jpegtran and run_jpegtran(jpegtran, source, output):
            return
    else:
        cjpeg = get_tool_executable(["cjpeg", "mozjpeg"])
        quality = adjust_quality(options.quality, options.quality_profile)
        if cjpeg and run_cjpeg(cjpeg, source, output, quality):
            return
    with Image.open(source) as image:
        save_kwargs = {
            "optimize": True,
            "progressive": True,
        }
        if options.lossless:
            save_kwargs["quality"] = 100
            save_kwargs["subsampling"] = 0
        else:
            save_kwargs["quality"] = max(1, min(100, adjust_quality(options.quality, options.quality_profile)))
        image.save(output, format="JPEG", **save_kwargs)


def compress_png(source: Path, output: Path, options: CompressOptions) -> None:
    if options.lossless:
        optimized = optimize_png_source(source, output)
        if optimized:
            return
    pngquant = get_tool_executable(["pngquant"])
    if not options.lossless and pngquant:
        quality = max(10, min(100, adjust_quality(options.quality, options.quality_profile)))
        min_q, speed = get_pngquant_settings(options.quality_profile, quality)
        result = run_pngquant(pngquant, source, output, min_q, quality, speed)
        if result:
            return
    with Image.open(source) as image:
        if options.lossless:
            image.save(output, format="PNG", optimize=True, compress_level=9)
        else:
            quality = max(1, min(100, adjust_quality(options.quality, options.quality_profile)))
            colors = max(16, int(256 * quality / 100))
            colors = adjust_colors(options.quality_profile, colors)
            quantized = quantize_image(image, colors)
            quantized.save(output, format="PNG", optimize=True, compress_level=9)


def run_pngquant(
    pngquant: str,
    source: Path,
    output: Path,
    min_quality: int,
    max_quality: int,
    speed: int,
) -> bool:
    command = [
        pngquant,
        "--quality",
        f"{min_quality}-{max_quality}",
        "--speed",
        str(speed),
        "--strip",
        "--skip-if-larger",
        "--output",
        str(output),
        "--force",
        str(source),
    ]
    result = subprocess.run(command, capture_output=True)
    return result.returncode == 0 and output.exists()


def compress_gif(source: Path, output: Path, options: CompressOptions) -> None:
    gifsicle = get_tool_executable(["gifsicle"])
    if gifsicle:
        quality = adjust_quality(options.quality, options.quality_profile)
        if run_gifsicle(gifsicle, source, output, options.lossless, quality, options.quality_profile):
            return
    with Image.open(source) as image:
        frames = [frame.copy() for frame in ImageSequence.Iterator(image)]
        if not frames:
            image.save(output, format="GIF", optimize=True)
            return
        if options.lossless:
            save_gif(frames, image, output, optimize=True)
        else:
            quality = max(1, min(100, adjust_quality(options.quality, options.quality_profile)))
            colors = max(16, int(256 * quality / 100))
            colors = adjust_colors(options.quality_profile, colors)
            reduced = [quantize_image(frame, colors) for frame in frames]
            save_gif(reduced, image, output, optimize=True)


def save_gif(frames: list[Image.Image], original: Image.Image, output: Path, optimize: bool) -> None:
    duration = original.info.get("duration", 0)
    loop = original.info.get("loop", 0)
    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=loop,
        optimize=optimize,
    )


def compress_webp(source: Path, output: Path, options: CompressOptions) -> None:
    cwebp = get_tool_executable(["cwebp"])
    if cwebp:
        quality = adjust_quality(options.quality, options.quality_profile)
        if run_cwebp(cwebp, source, output, options.lossless, quality):
            return
    with Image.open(source) as image:
        if options.lossless:
            image.save(output, format="WEBP", lossless=True, quality=100, method=6)
        else:
            quality = max(1, min(100, adjust_quality(options.quality, options.quality_profile)))
            image.save(
                output,
                format="WEBP",
                lossless=False,
                quality=quality,
                method=6,
            )


def quantize_image(image: Image.Image, colors: int) -> Image.Image:
    if image.mode in {"RGBA", "LA"}:
        return image.convert("RGBA").quantize(colors=colors, method=Image.FASTOCTREE)
    return image.convert("RGB").quantize(colors=colors, method=Image.MEDIANCUT)


def run_jpegtran(jpegtran: str, source: Path, output: Path) -> bool:
    command = [
        jpegtran,
        "-copy",
        "none",
        "-optimize",
        "-progressive",
        "-outfile",
        str(output),
        str(source),
    ]
    result = subprocess.run(command, capture_output=True)
    return result.returncode == 0 and output.exists()


def run_cjpeg(cjpeg: str, source: Path, output: Path, quality: int) -> bool:
    command = [
        cjpeg,
        "-quality",
        str(max(1, min(100, quality))),
        "-progressive",
        "-optimize",
        "-outfile",
        str(output),
        str(source),
    ]
    result = subprocess.run(command, capture_output=True)
    return result.returncode == 0 and output.exists()


def run_gifsicle(
    gifsicle: str,
    source: Path,
    output: Path,
    lossless: bool,
    quality: int,
    profile: str,
) -> bool:
    command = [gifsicle, "-O3", "--no-comments", "--no-names", "--no-extensions"]
    if not lossless:
        lossy = max(0, int((100 - max(1, min(100, quality))) * 2))
        lossy = adjust_lossy(profile, lossy)
        colors = max(32, int(256 * max(1, min(100, quality)) / 100))
        colors = adjust_colors(profile, colors)
        command += ["--lossy", str(lossy), "--colors", str(colors)]
    command += [str(source), "-o", str(output)]
    result = subprocess.run(command, capture_output=True)
    return result.returncode == 0 and output.exists()


def run_cwebp(cwebp: str, source: Path, output: Path, lossless: bool, quality: int) -> bool:
    if lossless:
        command = [
            cwebp,
            "-lossless",
            "-z",
            "9",
            "-m",
            "6",
            "-metadata",
            "none",
            str(source),
            "-o",
            str(output),
        ]
    else:
        command = [
            cwebp,
            "-q",
            str(max(1, min(100, quality))),
            "-m",
            "6",
            "-metadata",
            "none",
            str(source),
            "-o",
            str(output),
        ]
    result = subprocess.run(command, capture_output=True)
    return result.returncode == 0 and output.exists()


def get_tool_executable(names: list[str]) -> str | None:
    base_dirs = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        base_dirs.append(Path(meipass))
    base_dirs.append(Path(__file__).resolve().parent.parent / "vendor")
    base_dirs.append(Path(sys.executable).resolve().parent)
    for base in base_dirs:
        for name in names:
            candidates = [base / name, base / f"{name}.exe"]
            for path in candidates:
                if path.exists():
                    return str(path)
    for name in names:
        system_path = shutil.which(name)
        if system_path:
            return system_path
    return None


def optimize_jpeg(output: Path) -> None:
    jpegtran = get_tool_executable(["jpegtran"])
    if not jpegtran or not output.exists():
        return
    temp = output.with_name(f"{output.stem}.__opt{output.suffix}")
    if run_jpegtran(jpegtran, output, temp):
        temp.replace(output)
    elif temp.exists():
        temp.unlink()


def optimize_png(output: Path, lossless: bool) -> None:
    if not output.exists():
        return
    if lossless:
        tool = get_tool_executable(["oxipng", "optipng"])
        if tool:
            run_png_optimizer(tool, output)
        return
    tool = get_tool_executable(["oxipng", "optipng"])
    if tool:
        run_png_optimizer(tool, output)


def optimize_png_source(source: Path, output: Path) -> bool:
    tool = get_tool_executable(["oxipng", "optipng"])
    if not tool:
        return False
    temp = output.with_name(f"{output.stem}.__opt{output.suffix}")
    if run_png_optimizer(tool, source, temp):
        temp.replace(output)
        return True
    if temp.exists():
        temp.unlink()
    return False


def run_png_optimizer(tool: str, source: Path, output: Path | None = None) -> bool:
    name = Path(tool).name.lower()
    if "oxipng" in name:
        command = [tool, "-o", "4", "--strip", "all"]
        if output is not None:
            command += ["-out", str(output), str(source)]
        else:
            command += [str(source)]
    else:
        command = [tool, "-o7", "-strip", "all"]
        if output is not None:
            command += ["-out", str(output), str(source)]
        else:
            command += [str(source)]
    result = subprocess.run(command, capture_output=True)
    if output is None:
        return result.returncode == 0
    return result.returncode == 0 and output.exists()


def optimize_gif(output: Path) -> None:
    gifsicle = get_tool_executable(["gifsicle"])
    if not gifsicle or not output.exists():
        return
    temp = output.with_name(f"{output.stem}.__opt{output.suffix}")
    command = [gifsicle, "-O3", "--no-comments", "--no-names", "--no-extensions", str(output), "-o", str(temp)]
    result = subprocess.run(command, capture_output=True)
    if result.returncode == 0 and temp.exists():
        temp.replace(output)
    elif temp.exists():
        temp.unlink()


def adjust_quality(quality: int, profile: str) -> int:
    profile = normalize_profile(profile)
    if profile == "strong":
        return max(10, quality - 10)
    if profile == "balanced":
        return max(10, quality - 4)
    return quality


def normalize_profile(profile: str) -> str:
    if profile in {"high", "balanced", "strong"}:
        return profile
    return "high"


def get_pngquant_settings(profile: str, quality: int) -> tuple[int, int]:
    profile = normalize_profile(profile)
    if profile == "strong":
        range_size = 25
        speed = 3
    elif profile == "balanced":
        range_size = 15
        speed = 2
    else:
        range_size = 8
        speed = 1
    min_q = max(10, quality - range_size)
    return min_q, speed


def adjust_colors(profile: str, colors: int) -> int:
    profile = normalize_profile(profile)
    if profile == "strong":
        return max(16, int(colors * 0.7))
    if profile == "balanced":
        return max(16, int(colors * 0.85))
    return colors


def adjust_lossy(profile: str, lossy: int) -> int:
    profile = normalize_profile(profile)
    if profile == "strong":
        return min(200, int(lossy * 1.4))
    if profile == "balanced":
        return min(200, int(lossy * 1.1))
    return lossy


def get_engine_status(lossless: bool) -> dict[str, str]:
    jpg = "Pillow"
    if lossless and get_tool_executable(["jpegtran"]):
        jpg = "jpegtran"
    if not lossless and get_tool_executable(["cjpeg", "mozjpeg"]):
        jpg = "mozjpeg"
    png = "Pillow"
    if lossless and get_tool_executable(["oxipng", "optipng"]):
        png = "oxipng"
    if not lossless and get_tool_executable(["pngquant"]):
        png = "pngquant"
    gif = "Pillow"
    if get_tool_executable(["gifsicle"]):
        gif = "gifsicle"
    webp = "Pillow"
    if get_tool_executable(["cwebp"]):
        webp = "cwebp"
    return {"JPG": jpg, "PNG": png, "GIF": gif, "WebP": webp}
