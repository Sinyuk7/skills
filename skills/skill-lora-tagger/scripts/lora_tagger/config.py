from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

import yaml

from .defaults import RuntimeConfig


def load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML file must contain an object at the top level: {path}")
    return data


def skill_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_path(base_path: Path, raw_path: str | None) -> Path | None:
    if not raw_path:
        return None
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return (base_path.parent / candidate).resolve()


def load_text_file(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    return path.read_text(encoding="utf-8").strip()


def require_dict(parent: dict[str, Any], key: str, context: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Missing required object `{context}.{key}`.")
    return value


def require_value(parent: dict[str, Any], key: str, context: str) -> Any:
    if key not in parent:
        raise ValueError(f"Missing required field `{context}.{key}`.")
    return parent[key]


def require_non_empty_string(parent: dict[str, Any], key: str, context: str) -> str:
    value = require_value(parent, key, context)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Field `{context}.{key}` must be a non-empty string.")
    return value.strip()


def require_int(parent: dict[str, Any], key: str, context: str, *, min_value: int | None = None) -> int:
    value = require_value(parent, key, context)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Field `{context}.{key}` must be an integer.")
    if min_value is not None and value < min_value:
        raise ValueError(f"Field `{context}.{key}` must be >= {min_value}.")
    return value


def require_float(
    parent: dict[str, Any],
    key: str,
    context: str,
    *,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    value = require_value(parent, key, context)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Field `{context}.{key}` must be a number.")
    numeric = float(value)
    if min_value is not None and numeric < min_value:
        raise ValueError(f"Field `{context}.{key}` must be >= {min_value}.")
    if max_value is not None and numeric > max_value:
        raise ValueError(f"Field `{context}.{key}` must be <= {max_value}.")
    return numeric


def require_string_list(parent: dict[str, Any], key: str, context: str) -> list[str]:
    value = require_value(parent, key, context)
    if not isinstance(value, list) or not value:
        raise ValueError(f"Field `{context}.{key}` must be a non-empty list.")
    normalized: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"Field `{context}.{key}[{index}]` must be a non-empty string.")
        normalized.append(item.strip())
    return normalized


def require_int_list(parent: dict[str, Any], key: str, context: str, *, min_value: int | None = None) -> list[int]:
    value = require_value(parent, key, context)
    if not isinstance(value, list) or not value:
        raise ValueError(f"Field `{context}.{key}` must be a non-empty list.")
    normalized: list[int] = []
    for index, item in enumerate(value):
        if isinstance(item, bool) or not isinstance(item, int):
            raise ValueError(f"Field `{context}.{key}[{index}]` must be an integer.")
        if min_value is not None and item < min_value:
            raise ValueError(f"Field `{context}.{key}[{index}]` must be >= {min_value}.")
        normalized.append(item)
    return normalized


def require_bool(parent: dict[str, Any], key: str, context: str) -> bool:
    value = require_value(parent, key, context)
    if not isinstance(value, bool):
        raise ValueError(f"Field `{context}.{key}` must be a boolean.")
    return value


def normalize_ratio_text(ratio_text: str) -> str:
    match = re.fullmatch(r"\s*(\d+)\s*:\s*(\d+)\s*", ratio_text)
    if not match:
        raise ValueError(f"Invalid ratio: {ratio_text}")
    left = int(match.group(1))
    right = int(match.group(2))
    if left <= 0 or right <= 0:
        raise ValueError(f"Invalid ratio: {ratio_text}")
    divisor = math.gcd(left, right)
    return f"{left // divisor}:{right // divisor}"


def ratio_to_tuple(ratio_text: str) -> tuple[int, int]:
    left_text, right_text = normalize_ratio_text(ratio_text).split(":")
    return int(left_text), int(right_text)


def ratio_to_float(ratio_text: str) -> float:
    left, right = ratio_to_tuple(ratio_text)
    return left / right


def round_to_multiple(value: float, multiple: int) -> int:
    rounded = int(round(value / multiple) * multiple)
    return max(multiple, rounded)


def derive_target_size(ratio_text: str, long_edge: int, alignment: int) -> tuple[int, int]:
    width_units, height_units = ratio_to_tuple(ratio_text)
    if width_units >= height_units:
        target_width = long_edge
        raw_height = long_edge * (height_units / width_units)
        target_height = round_to_multiple(raw_height, alignment)
    else:
        target_height = long_edge
        raw_width = long_edge * (width_units / height_units)
        target_width = round_to_multiple(raw_width, alignment)
    return int(target_width), int(target_height)


def build_runtime_config(user_config_path: Path, developer_defaults_path: Path) -> RuntimeConfig:
    user_config = load_yaml_file(user_config_path)
    developer_defaults = load_yaml_file(developer_defaults_path)

    ratio_map = (
        user_config.get("resolutions", {}).get("ratio_long_edge_map", {})
        if isinstance(user_config.get("resolutions"), dict)
        else {}
    )
    if not ratio_map:
        raise ValueError("Config is missing `resolutions.ratio_long_edge_map`.")

    user_prompt_raw = (
        user_config.get("captioning", {}).get("user_prompt_path", "")
        if isinstance(user_config.get("captioning"), dict)
        else ""
    )
    user_prompt_path = resolve_path(user_config_path, user_prompt_raw)
    if user_prompt_path is None:
        raise ValueError("Config is missing `captioning.user_prompt_path`.")

    system_prompt_path = skill_root_from_script() / "references" / "system-prompt.txt"
    if not system_prompt_path.exists():
        raise FileNotFoundError(f"Required system prompt file does not exist: {system_prompt_path}")
    system_prompt_text = load_text_file(system_prompt_path)
    if not system_prompt_text:
        raise ValueError(f"System prompt file is empty: {system_prompt_path}")

    shuffle_values = bool(
        (user_config.get("caption_assembly", {}) or {}).get("shuffle_values", False)
    )

    path_defaults = require_dict(developer_defaults, "paths", "developer_defaults")
    image_defaults = require_dict(developer_defaults, "images", "developer_defaults")
    resolution_defaults = require_dict(developer_defaults, "resolutions", "developer_defaults")
    upload_defaults = require_dict(developer_defaults, "vision_upload", "developer_defaults")
    caption_defaults = require_dict(developer_defaults, "captioning", "developer_defaults")
    assembly_defaults = require_dict(developer_defaults, "caption_assembly", "developer_defaults")

    supported_long_edges = set(
        require_int_list(
            resolution_defaults,
            "supported_long_edges",
            "developer_defaults.resolutions",
            min_value=1,
        )
    )

    normalized_ratio_map: dict[str, int] = {}
    for ratio_text, long_edge in ratio_map.items():
        normalized_ratio_text = normalize_ratio_text(ratio_text)
        long_edge_value = int(long_edge)
        if long_edge_value not in supported_long_edges:
            raise ValueError(
                f"Unsupported long edge in ratio_long_edge_map: {ratio_text} -> {long_edge_value}"
            )
        normalized_ratio_map[normalized_ratio_text] = long_edge_value

    return RuntimeConfig(
        user_config_path=user_config_path,
        developer_defaults_path=developer_defaults_path,
        ratio_long_edge_map=normalized_ratio_map,
        user_prompt_path=user_prompt_path,
        system_prompt_path=system_prompt_path,
        shuffle_values=shuffle_values,
        output_dir_name=require_non_empty_string(path_defaults, "output_dir_name", "developer_defaults.paths"),
        supported_extensions=set(
            ext.lower()
            for ext in require_string_list(
                image_defaults,
                "supported_extensions",
                "developer_defaults.images",
            )
        ),
        output_jpeg_quality=require_int(
            image_defaults,
            "output_jpeg_quality",
            "developer_defaults.images",
            min_value=1,
        ),
        rename_pattern=require_non_empty_string(
            image_defaults,
            "rename_pattern",
            "developer_defaults.images",
        ),
        supported_long_edges=supported_long_edges,
        analysis_long_edge=require_int(
            upload_defaults,
            "long_edge",
            "developer_defaults.vision_upload",
            min_value=1,
        ),
        analysis_jpeg_quality=require_int(
            upload_defaults,
            "jpeg_quality",
            "developer_defaults.vision_upload",
            min_value=1,
        ),
        transport=require_non_empty_string(
            upload_defaults,
            "transport",
            "developer_defaults.vision_upload",
        ),
        primary_base_url=require_non_empty_string(
            caption_defaults,
            "primary_base_url",
            "developer_defaults.captioning",
        ),
        fallback_base_url=require_non_empty_string(
            caption_defaults,
            "fallback_base_url",
            "developer_defaults.captioning",
        ),
        model=require_non_empty_string(
            caption_defaults,
            "model",
            "developer_defaults.captioning",
        ),
        api_key_env=require_non_empty_string(
            caption_defaults,
            "api_key_env",
            "developer_defaults.captioning",
        ),
        concurrency=require_int(
            caption_defaults,
            "concurrency",
            "developer_defaults.captioning",
            min_value=1,
        ),
        timeout_seconds=require_int(
            caption_defaults,
            "timeout_seconds",
            "developer_defaults.captioning",
            min_value=1,
        ),
        max_retries=require_int(
            caption_defaults,
            "max_retries",
            "developer_defaults.captioning",
            min_value=1,
        ),
        system_prompt=system_prompt_text,
        separator=require_non_empty_string(
            assembly_defaults,
            "separator",
            "developer_defaults.caption_assembly",
        ),
        keep_subject_first=require_bool(
            assembly_defaults,
            "keep_subject_first",
            "developer_defaults.caption_assembly",
        ),
        alignment=require_int(
            image_defaults,
            "alignment",
            "developer_defaults.images",
            min_value=1,
        ),
        ratio_warn_threshold=require_float(
            resolution_defaults,
            "ratio_warn_threshold",
            "developer_defaults.resolutions",
            min_value=0.0,
        ),
        temperature=require_float(
            caption_defaults,
            "temperature",
            "developer_defaults.captioning",
            min_value=0.0,
        ),
        top_p=require_float(
            caption_defaults,
            "top_p",
            "developer_defaults.captioning",
            min_value=0.0,
            max_value=1.0,
        ),
        max_tokens=require_int(
            caption_defaults,
            "max_tokens",
            "developer_defaults.captioning",
            min_value=1,
        ),
    )
