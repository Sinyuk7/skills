from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from .defaults import RuntimeConfig

MANIFEST_VERSION = 2

REQUIRED_MANIFEST_KEYS = {
    "version",
    "mode",
    "input_path",
    "dataset_dir",
    "created_at",
    "config_snapshot",
    "items",
}

REQUIRED_ITEM_KEYS = {
    "id",
    "source_path",
    "source_rel_path",
    "source_fingerprint",
    "image_path",
    "text_path",
    "raw_response_path",
    "parsed_json_path",
    "final_caption",
    "status",
    "last_error",
}


def dataset_paths(dataset_dir: Path) -> dict[str, Path]:
    meta_dir = dataset_dir / "_meta"
    return {
        "dataset_dir": dataset_dir,
        "meta_dir": meta_dir,
        "manifest": meta_dir / "manifest.json",
        "reports_dir": meta_dir / "reports",
        "raw_dir": meta_dir / "raw_responses",
        "parsed_dir": meta_dir / "parsed",
    }


def ensure_dataset_layout(dataset_dir: Path) -> dict[str, Path]:
    paths = dataset_paths(dataset_dir)
    dataset_dir.mkdir(parents=True, exist_ok=True)
    paths["meta_dir"].mkdir(parents=True, exist_ok=True)
    paths["reports_dir"].mkdir(parents=True, exist_ok=True)
    paths["raw_dir"].mkdir(parents=True, exist_ok=True)
    paths["parsed_dir"].mkdir(parents=True, exist_ok=True)
    return paths


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    temp_path.replace(path)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def initialize_manifest(
    mode: str,
    input_path: Path,
    dataset_dir: Path,
    config: RuntimeConfig,
) -> dict[str, Any]:
    return {
        "version": MANIFEST_VERSION,
        "mode": mode,
        "input_path": str(input_path),
        "dataset_dir": str(dataset_dir),
        "created_at": int(time.time()),
        "config_snapshot": {
            "ratio_long_edge_map": config.ratio_long_edge_map,
            "user_prompt_path": str(config.user_prompt_path),
            "shuffle_values": config.shuffle_values,
        },
        "items": [],
    }


def save_manifest(manifest_path: Path, manifest: dict[str, Any]) -> None:
    save_json(manifest_path, manifest)


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    return load_json(manifest_path)


def validate_manifest(manifest: dict[str, Any], dataset_dir: Path) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be a JSON object.")

    missing_keys = sorted(REQUIRED_MANIFEST_KEYS - set(manifest.keys()))
    if missing_keys:
        raise ValueError(f"Manifest is missing required keys: {', '.join(missing_keys)}")

    version = manifest.get("version")
    if version != MANIFEST_VERSION:
        raise ValueError(
            f"Unsupported manifest version: {version}. Re-run `crop` to create a fresh dataset."
        )

    manifest_dataset_dir = Path(str(manifest["dataset_dir"])).resolve()
    if manifest_dataset_dir != dataset_dir.resolve():
        raise ValueError("Manifest dataset_dir does not match the provided dataset directory.")

    items = manifest.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("Manifest does not contain any dataset items.")

    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Manifest item #{index} must be an object.")
        missing_item_keys = sorted(REQUIRED_ITEM_KEYS - set(item.keys()))
        if missing_item_keys:
            raise ValueError(
                f"Manifest item #{index} is missing required keys: {', '.join(missing_item_keys)}"
            )
        image_path = Path(str(item["image_path"]))
        if not image_path.exists():
            raise ValueError(
                f"Manifest item #{index} points to a missing cropped image: {image_path}"
            )

    return manifest
