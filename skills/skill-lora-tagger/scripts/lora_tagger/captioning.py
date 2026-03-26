from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import random
import re
from pathlib import Path
from typing import Any

import aiohttp
from PIL import Image

from .defaults import RuntimeConfig
from .image_ops import exif_normalized_rgb
from .manifest import load_json, save_json


class RetryableRequestError(RuntimeError):
    pass


def load_user_prompt(prompt_path: Path) -> str:
    if not prompt_path.exists():
        raise FileNotFoundError(f"User prompt file does not exist: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()


def analysis_copy_as_data_url(
    source_image_path: Path,
    config: RuntimeConfig,
) -> tuple[str, dict[str, int]]:
    with exif_normalized_rgb(source_image_path) as image:
        source_width, source_height = image.size
        long_edge = max(source_width, source_height)
        scale = min(1.0, config.analysis_long_edge / long_edge)
        analysis_width = max(1, int(round(source_width * scale)))
        analysis_height = max(1, int(round(source_height * scale)))
        resized = image.resize((analysis_width, analysis_height), Image.Resampling.LANCZOS)

        import io

        buffer = io.BytesIO()
        resized.save(buffer, format="JPEG", quality=config.analysis_jpeg_quality)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return (
            f"data:image/jpeg;base64,{encoded}",
            {
                "analysis_width": analysis_width,
                "analysis_height": analysis_height,
            },
        )


def request_payload_for_item(
    item: dict[str, Any],
    user_prompt: str,
    config: RuntimeConfig,
) -> tuple[dict[str, Any], dict[str, int]]:
    image_path = Path(item["image_path"])
    if not image_path.exists():
        raise FileNotFoundError(f"Cropped dataset image does not exist: {image_path}")
    data_url, analysis_dims = analysis_copy_as_data_url(image_path, config)
    payload = {
        "model": config.model,
        "temperature": config.temperature,
        "top_p": config.top_p,
        "max_tokens": config.max_tokens,
        "messages": [
            {"role": "system", "content": config.system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": user_prompt},
                ],
            },
        ],
    }
    return payload, analysis_dims


async def post_chat_completion(
    session: aiohttp.ClientSession,
    base_url: str,
    payload: dict[str, Any],
    api_key: str,
) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    async with session.post(url, json=payload, headers=headers) as response:
        text = await response.text()
        if response.status == 200:
            return json.loads(text)
        if response.status in {429, 500, 502, 503, 504}:
            raise RetryableRequestError(f"{response.status}: {text[:300]}")
        raise RuntimeError(f"Caption request failed with status {response.status}: {text[:300]}")


async def fetch_raw_response(
    session: aiohttp.ClientSession,
    payload: dict[str, Any],
    api_key: str,
    config: RuntimeConfig,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, config.max_retries + 1):
        for base_url in [config.primary_base_url, config.fallback_base_url]:
            try:
                return await post_chat_completion(session, base_url, payload, api_key)
            except RetryableRequestError as error:
                last_error = error
            except aiohttp.ClientError as error:
                last_error = error
            except asyncio.TimeoutError as error:
                last_error = error
        await asyncio.sleep(min(10, 2 ** (attempt - 1)))
    raise RuntimeError(f"Caption request failed after retries: {last_error}")


def extract_response_text(raw_response: dict[str, Any]) -> str:
    choices = raw_response.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            texts = []
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    texts.append(part["text"])
            return "\n".join(texts).strip()

    output_text = raw_response.get("output_text")
    if isinstance(output_text, str):
        return output_text.strip()

    raise ValueError("Could not extract text content from the provider response.")


def extract_json_text(response_text: str) -> str:
    stripped = response_text.strip()
    if stripped.startswith("```"):
        code_block_match = re.search(r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```", stripped, re.S)
        if code_block_match:
            return code_block_match.group(1).strip()

    if stripped.startswith("{") or stripped.startswith("["):
        return stripped

    first_brace = stripped.find("{")
    last_brace = stripped.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return stripped[first_brace : last_brace + 1]

    first_bracket = stripped.find("[")
    last_bracket = stripped.rfind("]")
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        return stripped[first_bracket : last_bracket + 1]

    raise ValueError("No JSON object or array was found in the model response.")


def flatten_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, dict):
        flattened: list[str] = []
        for nested_value in value.values():
            flattened.extend(flatten_values(nested_value))
        return flattened
    if isinstance(value, list):
        flattened: list[str] = []
        for nested_value in value:
            flattened.extend(flatten_values(nested_value))
        return flattened
    if isinstance(value, bool):
        return ["true" if value else "false"]
    if isinstance(value, (int, float)):
        return [str(value)]
    text = str(value).strip()
    return [text] if text else []


def assemble_caption(parsed_payload: Any, item: dict[str, Any], config: RuntimeConfig) -> str:
    values: list[str] = []
    subject_values: list[str] = []
    remaining_values: list[str] = []

    if isinstance(parsed_payload, dict):
        for key, value in parsed_payload.items():
            flattened = flatten_values(value)
            if key == "subject" and config.keep_subject_first:
                subject_values.extend(flattened)
            else:
                remaining_values.extend(flattened)
    else:
        remaining_values.extend(flatten_values(parsed_payload))

    if config.shuffle_values and remaining_values:
        seed = int(hashlib.sha256(item["source_fingerprint"].encode("utf-8")).hexdigest()[:16], 16)
        random.Random(seed).shuffle(remaining_values)

    values.extend(subject_values)
    values.extend(remaining_values)
    return config.separator.join(value for value in values if value)


def write_caption_outputs(item: dict[str, Any], parsed_payload: Any, config: RuntimeConfig) -> str:
    caption = assemble_caption(parsed_payload, item, config)
    text_path = Path(item["text_path"])
    text_path.write_text(caption, encoding="utf-8")
    save_json(Path(item["parsed_json_path"]), parsed_payload)
    return caption


def parse_existing_raw(item: dict[str, Any]) -> dict[str, Any]:
    raw_path = Path(item["raw_response_path"])
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw response file does not exist: {raw_path}")
    return load_json(raw_path)


async def process_caption_item(
    item: dict[str, Any],
    session: aiohttp.ClientSession,
    user_prompt: str,
    api_key: str,
    config: RuntimeConfig,
) -> None:
    raw_path = Path(item["raw_response_path"])
    raw_response: dict[str, Any]
    analysis_dims: dict[str, int] = {}

    if raw_path.exists():
        raw_response = parse_existing_raw(item)
    else:
        payload, analysis_dims = request_payload_for_item(item, user_prompt, config)
        raw_response = await fetch_raw_response(session, payload, api_key, config)
        save_json(raw_path, raw_response)
        item.update(analysis_dims)
        item["status"] = "raw_saved"
        item["last_error"] = ""

    response_text = extract_response_text(raw_response)
    parsed_payload = json.loads(extract_json_text(response_text))
    final_caption = write_caption_outputs(item, parsed_payload, config)
    item["final_caption"] = final_caption
    item["status"] = "complete"
    item["last_error"] = ""


def require_api_key(config: RuntimeConfig) -> str:
    api_key = os.environ.get(config.api_key_env, "").strip()
    if not api_key:
        raise RuntimeError(f"Missing required environment variable: {config.api_key_env}")
    return api_key
