from __future__ import annotations

import hashlib
import math
import os
import re
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

from .config import derive_target_size, ratio_to_float

try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except Exception:
    pillow_heif = None


def collision_safe_dataset_dir(input_dir: Path, base_name: str) -> Path:
    candidate = input_dir / base_name
    if not candidate.exists():
        return candidate
    index = 2
    while True:
        next_candidate = input_dir / f"{base_name}-{index}"
        if not next_candidate.exists():
            return next_candidate
        index += 1


def discover_images(input_dir: Path, supported_extensions: set[str]) -> list[Path]:
    discovered: list[Path] = []
    for current_root, dirs, files in os.walk(input_dir):
        current_path = Path(current_root)
        dirs[:] = [
            name
            for name in dirs
            if not re.fullmatch(r"dataset(?:-\d+)?", name) and name != "_meta"
        ]
        for filename in files:
            file_path = current_path / filename
            if file_path.suffix.lower() in supported_extensions:
                discovered.append(file_path)
    return sorted(discovered, key=lambda item: str(item.relative_to(input_dir)).lower())


def exif_normalized_rgb(image_path: Path) -> Image.Image:
    image = Image.open(image_path)
    image = ImageOps.exif_transpose(image)
    if image.mode in ("RGBA", "LA"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        alpha = image.getchannel("A")
        background.paste(image.convert("RGB"), mask=alpha)
        image.close()
        return background
    if image.mode != "RGB":
        converted = image.convert("RGB")
        image.close()
        return converted
    return image


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def best_ratio_match(width: int, height: int, ratio_map: dict[str, int]) -> tuple[str, float]:
    source_ratio = width / height
    best_ratio = ""
    best_delta = float("inf")
    for ratio_text in ratio_map:
        delta = abs(source_ratio - ratio_to_float(ratio_text))
        if delta < best_delta:
            best_ratio = ratio_text
            best_delta = delta
    return best_ratio, best_delta


def build_scan_summary(
    input_dir: Path,
    image_paths: list[Path],
    ratio_map: dict[str, int],
    threshold: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    items: list[dict[str, Any]] = []
    matched_counts = {ratio: 0 for ratio in ratio_map.keys()}
    unmapped_images: list[dict[str, Any]] = []

    for image_path in image_paths:
        with exif_normalized_rgb(image_path) as image:
            width, height = image.size
        matched_ratio, ratio_delta = best_ratio_match(width, height, ratio_map)
        matched_counts[matched_ratio] += 1
        item = {
            "source_path": str(image_path),
            "source_rel_path": str(image_path.relative_to(input_dir)),
            "source_width": width,
            "source_height": height,
            "source_ratio": round(width / height, 6),
            "matched_ratio": matched_ratio,
            "ratio_delta": round(ratio_delta, 6),
            "ratio_within_threshold": ratio_delta <= threshold,
        }
        if ratio_delta > threshold:
            unmapped_images.append(item)
        items.append(item)

    summary = {
        "total_images": len(items),
        "configured_ratios": list(ratio_map.keys()),
        "matched_ratio_counts": matched_counts,
        "unmapped_images": unmapped_images,
    }
    return items, summary


def print_ratio_summary(summary: dict[str, Any]) -> None:
    print("ratio scan summary:")
    print(f"  total_images: {summary['total_images']}")
    for ratio_text, count in summary["matched_ratio_counts"].items():
        print(f"  matched_{ratio_text}: {count}")
    if summary["unmapped_images"]:
        print(f"  warnings: {len(summary['unmapped_images'])} images are far from configured ratios")
        for item in summary["unmapped_images"][:10]:
            print(
                f"    - {item['source_rel_path']} "
                f"(source={item['source_width']}x{item['source_height']}, matched={item['matched_ratio']})"
            )


def crop_to_target(
    image: Image.Image,
    target_width: int,
    target_height: int,
) -> tuple[Image.Image, dict[str, Any]]:
    source_width, source_height = image.size
    scale = max(target_width / source_width, target_height / source_height)
    resized_width = max(target_width, int(math.ceil(source_width * scale)))
    resized_height = max(target_height, int(math.ceil(source_height * scale)))
    resized = image.resize((resized_width, resized_height), Image.Resampling.LANCZOS)

    left = max(0, (resized_width - target_width) // 2)
    top = max(0, (resized_height - target_height) // 2)
    cropped = resized.crop((left, top, left + target_width, top + target_height))

    crop_info = {
        "source_width": source_width,
        "source_height": source_height,
        "resized_width": resized_width,
        "resized_height": resized_height,
        "crop_left": left,
        "crop_top": top,
        "target_width": target_width,
        "target_height": target_height,
        "crop_fraction": round(
            1.0 - ((target_width * target_height) / (resized_width * resized_height)),
            6,
        ),
    }
    return cropped, crop_info


def format_output_name(pattern: str, index: int) -> str:
    return pattern.format(index=index)


def normalize_one_image(
    image_path: Path,
    output_path: Path,
    matched_ratio: str,
    long_edge: int,
    alignment: int,
    jpeg_quality: int,
) -> dict[str, Any]:
    target_width, target_height = derive_target_size(matched_ratio, long_edge, alignment)
    with exif_normalized_rgb(image_path) as image:
        cropped, crop_info = crop_to_target(image, target_width, target_height)
        cropped.save(output_path, format="JPEG", quality=jpeg_quality)
    return {
        "final_width": target_width,
        "final_height": target_height,
        "crop_info": crop_info,
    }
