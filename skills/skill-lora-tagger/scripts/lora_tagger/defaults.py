from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

@dataclass
class RuntimeConfig:
    user_config_path: Path
    developer_defaults_path: Path
    ratio_long_edge_map: dict[str, int]
    user_prompt_path: Path
    system_prompt_path: Path
    shuffle_values: bool
    output_dir_name: str
    supported_extensions: set[str]
    output_jpeg_quality: int
    rename_pattern: str
    supported_long_edges: set[int]
    analysis_long_edge: int
    analysis_jpeg_quality: int
    transport: str
    primary_base_url: str
    fallback_base_url: str
    model: str
    api_key_env: str
    concurrency: int
    timeout_seconds: int
    max_retries: int
    system_prompt: str
    separator: str
    keep_subject_first: bool
    alignment: int
    ratio_warn_threshold: float
    temperature: float
    top_p: float
    max_tokens: int
