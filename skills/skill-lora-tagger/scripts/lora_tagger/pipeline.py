from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

import aiohttp

from .captioning import (
    extract_json_text,
    extract_response_text,
    load_user_prompt,
    parse_existing_raw,
    process_caption_item,
    require_api_key,
    write_caption_outputs,
)
from .config import build_runtime_config, skill_root_from_script
from .image_ops import (
    build_scan_summary,
    collision_safe_dataset_dir,
    discover_images,
    file_sha256,
    format_output_name,
    normalize_one_image,
    print_ratio_summary,
)
from .manifest import (
    dataset_paths,
    ensure_dataset_layout,
    initialize_manifest,
    load_manifest,
    save_json,
    save_manifest,
    validate_manifest,
)


def normalize_phase(
    input_dir: Path,
    dataset_dir: Path,
    config,
    limit: int | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    image_paths = discover_images(input_dir, config.supported_extensions)
    if not image_paths:
        raise RuntimeError(f"No supported images were found in: {input_dir}")

    scan_items, scan_summary = build_scan_summary(
        input_dir=input_dir,
        image_paths=image_paths,
        ratio_map=config.ratio_long_edge_map,
        threshold=config.ratio_warn_threshold,
    )
    selected_scan_items = scan_items[:limit] if limit else scan_items
    scan_summary["processed_count"] = len(selected_scan_items)
    scan_summary["skipped_count"] = len(scan_items) - len(selected_scan_items)
    print_ratio_summary(scan_summary)

    if dry_run:
        print("crop dry-run summary:")
        print(f"  output_dir: {dataset_dir}")
        print(f"  images_to_write: {scan_summary['processed_count']}")
        print(f"  images_skipped: {scan_summary['skipped_count']}")
        return {"items": selected_scan_items, "summary": scan_summary}

    paths = ensure_dataset_layout(dataset_dir)
    save_json(paths["reports_dir"] / "ratio-summary.json", scan_summary)

    manifest = initialize_manifest("crop", input_dir, dataset_dir, config)
    items: list[dict[str, Any]] = []

    for index, scan_item in enumerate(selected_scan_items, start=1):
        image_path = Path(scan_item["source_path"])
        output_stem = format_output_name(config.rename_pattern, index)
        final_image_path = dataset_dir / f"{output_stem}.jpg"
        text_path = dataset_dir / f"{output_stem}.txt"
        raw_response_path = paths["raw_dir"] / f"{output_stem}.json"
        parsed_json_path = paths["parsed_dir"] / f"{output_stem}.json"

        matched_ratio = scan_item["matched_ratio"]
        long_edge = config.ratio_long_edge_map[matched_ratio]
        normalized = normalize_one_image(
            image_path=image_path,
            output_path=final_image_path,
            matched_ratio=matched_ratio,
            long_edge=long_edge,
            alignment=config.alignment,
            jpeg_quality=config.output_jpeg_quality,
        )

        items.append(
            {
                "id": output_stem,
                "source_path": str(image_path),
                "source_rel_path": str(image_path.relative_to(input_dir)),
                "source_fingerprint": file_sha256(image_path),
                "original_width": scan_item["source_width"],
                "original_height": scan_item["source_height"],
                "source_ratio": scan_item["source_ratio"],
                "matched_ratio": matched_ratio,
                "ratio_delta": scan_item["ratio_delta"],
                "ratio_within_threshold": scan_item["ratio_within_threshold"],
                "configured_long_edge": long_edge,
                "final_width": normalized["final_width"],
                "final_height": normalized["final_height"],
                "image_path": str(final_image_path),
                "text_path": str(text_path),
                "raw_response_path": str(raw_response_path),
                "parsed_json_path": str(parsed_json_path),
                "final_caption": "",
                "status": "cropped",
                "last_error": "",
                "crop_info": normalized["crop_info"],
            }
        )

    manifest["items"] = items
    save_manifest(paths["manifest"], manifest)
    print(f"crop complete: wrote {len(items)} images to {dataset_dir}")
    return manifest


def load_dataset_manifest(dataset_dir: Path) -> tuple[dict[str, Path], dict[str, Any]]:
    if not dataset_dir.exists() or not dataset_dir.is_dir():
        raise FileNotFoundError(f"Dataset directory does not exist: {dataset_dir}")

    paths = dataset_paths(dataset_dir)
    if not paths["manifest"].exists():
        raise FileNotFoundError(
            f"Dataset manifest not found at {paths['manifest']}. Run `crop <raw_input_dir>` first."
        )

    manifest = validate_manifest(load_manifest(paths["manifest"]), dataset_dir)
    return paths, manifest


def summarize_crop_plan(input_dir: Path, config, limit: int | None = None) -> dict[str, Any]:
    image_paths = discover_images(input_dir, config.supported_extensions)
    if not image_paths:
        raise RuntimeError(f"No supported images were found in: {input_dir}")
    scan_items, scan_summary = build_scan_summary(
        input_dir=input_dir,
        image_paths=image_paths,
        ratio_map=config.ratio_long_edge_map,
        threshold=config.ratio_warn_threshold,
    )
    selected_scan_items = scan_items[:limit] if limit else scan_items
    scan_summary["processed_count"] = len(selected_scan_items)
    scan_summary["skipped_count"] = len(scan_items) - len(selected_scan_items)
    return {"items": selected_scan_items, "summary": scan_summary}


def summarize_tag_plan(dataset_dir: Path, limit: int | None = None) -> dict[str, Any]:
    _, manifest = load_dataset_manifest(dataset_dir)
    items = manifest["items"]
    selected_items = items[:limit] if limit else items
    pending_items = [
        item for item in selected_items if not Path(str(item["raw_response_path"])).exists()
    ]
    existing_raw_count = len(selected_items) - len(pending_items)
    existing_txt_count = sum(
        1 for item in selected_items if Path(str(item["text_path"])).exists()
    )
    return {
        "manifest": manifest,
        "summary": {
            "dataset_total_count": len(items),
            "selected_count": len(selected_items),
            "existing_raw_count": existing_raw_count,
            "pending_request_count": len(pending_items),
            "existing_txt_count": existing_txt_count,
            "txt_to_write_count": len(selected_items),
        },
    }


async def tag_phase(
    dataset_dir: Path,
    config,
    limit: int | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    paths, manifest = load_dataset_manifest(dataset_dir)
    user_prompt = load_user_prompt(config.user_prompt_path)

    items = manifest["items"]
    selected_items = items[:limit] if limit else items
    pending_items = [
        item for item in selected_items if not Path(str(item["raw_response_path"])).exists()
    ]

    if dry_run:
        print("tag dry-run summary:")
        print(f"  dataset_total: {len(items)}")
        print(f"  selected: {len(selected_items)}")
        print(f"  api_requests_needed: {len(pending_items)}")
        print(f"  txt_files_to_write: {len(selected_items)}")
        print(f"  analysis_long_edge: {config.analysis_long_edge}")
        print(f"  analysis_jpeg_quality: {config.analysis_jpeg_quality}")
        return manifest

    api_key = require_api_key(config)
    ensure_dataset_layout(dataset_dir)

    timeout = aiohttp.ClientTimeout(total=config.timeout_seconds)
    connector = aiohttp.TCPConnector(limit=max(1, config.concurrency))
    semaphore = asyncio.Semaphore(max(1, config.concurrency))

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        async def guarded_process(target_item: dict[str, Any]) -> None:
            async with semaphore:
                try:
                    await process_caption_item(target_item, session, user_prompt, api_key, config)
                except Exception as error:
                    target_item["status"] = "failed_request"
                    target_item["last_error"] = str(error)
                finally:
                    save_manifest(paths["manifest"], manifest)

        await asyncio.gather(*(guarded_process(item) for item in pending_items))

    rebuilt_count = 0
    parse_failed_count = 0
    for item in selected_items:
        raw_path = Path(str(item["raw_response_path"]))
        if not raw_path.exists():
            continue
        try:
            raw_response = parse_existing_raw(item)
            response_text = extract_response_text(raw_response)
            parsed_payload = json.loads(extract_json_text(response_text))
            final_caption = write_caption_outputs(item, parsed_payload, config)
            item["final_caption"] = final_caption
            item["status"] = "complete"
            item["last_error"] = ""
            rebuilt_count += 1
        except Exception as error:
            item["status"] = "failed_parse"
            item["last_error"] = str(error)
            parse_failed_count += 1

    report = {
        "dataset_total_count": len(items),
        "selected_count": len(selected_items),
        "complete_count": sum(1 for item in items if item.get("status") == "complete"),
        "failed_count": sum(
            1 for item in items if str(item.get("status", "")).startswith("failed")
        ),
        "processed_count": len(pending_items),
        "skipped_count": len(selected_items) - len(pending_items),
        "rebuilt_txt_count": rebuilt_count,
        "parse_failed_count": parse_failed_count,
    }
    save_json(paths["reports_dir"] / "caption-summary.json", report)
    save_manifest(paths["manifest"], manifest)
    print(
        "tag complete: "
        f"{report['complete_count']} complete, {report['failed_count']} failed in {dataset_dir}"
    )
    return manifest


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LoRA dataset preprocessing CLI")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    crop_parser = subparsers.add_parser(
        "crop",
        help="Create a cropped training dataset from a raw image directory.",
    )
    crop_parser.add_argument("path", help="Raw image directory.")
    crop_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N discovered images.",
    )
    crop_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the crop plan without creating any files.",
    )

    tag_parser = subparsers.add_parser(
        "tag",
        help="Caption a dataset directory produced by `crop`.",
    )
    tag_parser.add_argument("path", help="Dataset directory created by `crop`.")
    tag_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N dataset items.",
    )
    tag_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the tag plan without creating or updating any files.",
    )
    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()

    config = build_runtime_config(
        user_config_path=(skill_root_from_script() / "references" / "config-skeleton.yaml").resolve(),
        developer_defaults_path=(
            skill_root_from_script() / "references" / "developer-defaults.yaml"
        ).resolve(),
    )

    target_path = Path(args.path).resolve()
    if not target_path.exists() or not target_path.is_dir():
        raise FileNotFoundError(f"Input directory does not exist: {target_path}")

    if args.mode == "crop":
        dataset_dir = collision_safe_dataset_dir(target_path, config.output_dir_name)
        if args.dry_run:
            plan = summarize_crop_plan(target_path, config, limit=args.limit)
            print_ratio_summary(plan["summary"])
            print("crop dry-run summary:")
            print(f"  output_dir: {dataset_dir}")
            print(f"  images_to_write: {plan['summary']['processed_count']}")
            print(f"  images_skipped: {plan['summary']['skipped_count']}")
            return 0
        normalize_phase(target_path, dataset_dir, config, limit=args.limit, dry_run=False)
        print(f"output_dir: {dataset_dir}")
        return 0

    if args.mode == "tag":
        if args.dry_run:
            plan = summarize_tag_plan(target_path, limit=args.limit)
            summary = plan["summary"]
            print("tag dry-run summary:")
            print(f"  dataset_total: {summary['dataset_total_count']}")
            print(f"  selected: {summary['selected_count']}")
            print(f"  existing_raw: {summary['existing_raw_count']}")
            print(f"  api_requests_needed: {summary['pending_request_count']}")
            print(f"  existing_txt: {summary['existing_txt_count']}")
            print(f"  txt_files_to_write: {summary['txt_to_write_count']}")
            print(f"  output_dir: {target_path}")
            return 0
        asyncio.run(tag_phase(target_path, config, limit=args.limit, dry_run=False))
        print(f"output_dir: {target_path}")
        return 0

    raise RuntimeError(f"Unsupported mode: {args.mode}")
