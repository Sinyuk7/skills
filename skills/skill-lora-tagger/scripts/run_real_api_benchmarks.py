from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


def run_cli(repo_root: Path, cli_path: Path, args: list[str], env: dict[str, str]) -> dict[str, Any]:
    started_at = time.perf_counter()
    result = subprocess.run(
        [sys.executable, str(cli_path), *args],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    duration_seconds = round(time.perf_counter() - started_at, 3)
    return {
        "args": args,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "duration_seconds": duration_seconds,
    }


def copy_sample_images(sample_images: list[Path], destination: Path, count: int) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for source_path in sample_images[:count]:
        shutil.copy2(source_path, destination / source_path.name)


def summarize_dataset(dataset_dir: Path) -> dict[str, Any]:
    report_path = dataset_dir / "_meta" / "reports" / "caption-summary.json"
    manifest_path = dataset_dir / "_meta" / "manifest.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
    return {
        "dataset_dir": str(dataset_dir),
        "jpg_count": len(list(dataset_dir.glob("*.jpg"))),
        "txt_count": len(list(dataset_dir.glob("*.txt"))),
        "raw_count": len(list((dataset_dir / "_meta" / "raw_responses").glob("*.json"))),
        "parsed_count": len(list((dataset_dir / "_meta" / "parsed").glob("*.json"))),
        "report": report,
        "manifest_item_count": len(manifest.get("items", [])) if manifest else 0,
    }


def assert_success_case(case_name: str, crop_result: dict[str, Any], tag_result: dict[str, Any], summary: dict[str, Any], expected_count: int) -> None:
    if crop_result["returncode"] != 0:
        raise RuntimeError(f"{case_name}: crop failed\n{crop_result['stderr']}")
    if tag_result["returncode"] != 0:
        raise RuntimeError(f"{case_name}: tag failed\n{tag_result['stderr']}")
    if summary["jpg_count"] != expected_count:
        raise RuntimeError(f"{case_name}: expected {expected_count} jpg files, got {summary['jpg_count']}")
    if summary["txt_count"] != expected_count:
        raise RuntimeError(f"{case_name}: expected {expected_count} txt files, got {summary['txt_count']}")
    if summary["raw_count"] != expected_count:
        raise RuntimeError(f"{case_name}: expected {expected_count} raw json files, got {summary['raw_count']}")
    if summary["parsed_count"] != expected_count:
        raise RuntimeError(f"{case_name}: expected {expected_count} parsed json files, got {summary['parsed_count']}")
    if summary["manifest_item_count"] != expected_count:
        raise RuntimeError(
            f"{case_name}: expected manifest with {expected_count} items, got {summary['manifest_item_count']}"
        )
    report = summary["report"] or {}
    if report.get("complete_count") != expected_count:
        raise RuntimeError(
            f"{case_name}: expected complete_count {expected_count}, got {report.get('complete_count')}"
        )
    if report.get("failed_count") != 0:
        raise RuntimeError(f"{case_name}: expected failed_count 0, got {report.get('failed_count')}")


def run_success_case(
    *,
    case_name: str,
    repo_root: Path,
    cli_path: Path,
    env: dict[str, str],
    sample_images: list[Path],
    temp_root: Path,
    image_count: int,
    max_attempts: int = 3,
) -> dict[str, Any]:
    last_error: str | None = None
    last_payload: dict[str, Any] | None = None

    for attempt in range(1, max_attempts + 1):
        case_root = temp_root / f"{case_name}-attempt-{attempt}"
        raw_dir = case_root / "raw"
        copy_sample_images(sample_images, raw_dir, count=image_count)

        crop = run_cli(repo_root, cli_path, ["crop", str(raw_dir), "--limit", str(image_count)], env)
        dataset_dir = raw_dir / "dataset"
        tag_dry_run = run_cli(
            repo_root,
            cli_path,
            ["tag", str(dataset_dir), "--limit", str(image_count), "--dry-run"],
            env,
        )
        tag = run_cli(repo_root, cli_path, ["tag", str(dataset_dir), "--limit", str(image_count)], env)
        summary = summarize_dataset(dataset_dir)
        payload = {
            "case": case_name,
            "attempt": attempt,
            "crop": crop,
            "tag_dry_run": tag_dry_run,
            "tag": tag,
            "summary": summary,
            "images_per_second": round(
                image_count / max(tag["duration_seconds"], 0.001),
                3,
            ),
        }
        try:
            assert_success_case(case_name, crop, tag, summary, image_count)
            return payload
        except Exception as error:
            last_error = str(error)
            last_payload = payload

    raise RuntimeError(
        f"{case_name} failed after {max_attempts} attempts: {last_error}\n"
        f"last_payload={json.dumps(last_payload, ensure_ascii=False) if last_payload else '{}'}"
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    cli_path = repo_root / "scripts" / "lora_tagger_cli.py"
    sample_dir = repo_root / "exsample"
    sample_images = sorted(
        path for path in sample_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )

    api_key = os.environ.get("N1N_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("N1N_API_KEY is required for the real API benchmark run.")

    env = os.environ.copy()
    env["N1N_API_KEY"] = api_key

    results: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)

        results.append(
            run_success_case(
                case_name="single_image_end_to_end",
                repo_root=repo_root,
                cli_path=cli_path,
                env=env,
                sample_images=sample_images,
                temp_root=temp_root,
                image_count=1,
            )
        )

        results.append(
            run_success_case(
                case_name="multi_image_end_to_end",
                repo_root=repo_root,
                cli_path=cli_path,
                env=env,
                sample_images=sample_images,
                temp_root=temp_root,
                image_count=4,
            )
        )

        multi_dataset_dir = temp_root / "multi_image_end_to_end-attempt-1" / "raw"
        raw_input_case = run_cli(repo_root, cli_path, ["tag", str(multi_dataset_dir)], env)
        if raw_input_case["returncode"] == 0:
            raise RuntimeError("raw_input_rejected: expected non-zero exit code")
        results.append(
            {
                "case": "raw_input_rejected",
                "command": raw_input_case,
            }
        )

        tagged_dataset_dir = (
            temp_root / f"{results[1]['case']}-attempt-{results[1]['attempt']}" / "raw" / "dataset"
        )
        missing_key_env = env.copy()
        missing_key_env.pop("N1N_API_KEY", None)
        missing_key_case = run_cli(
            repo_root, cli_path, ["tag", str(tagged_dataset_dir), "--limit", "1"], missing_key_env
        )
        if missing_key_case["returncode"] == 0:
            raise RuntimeError("missing_api_key_rejected: expected non-zero exit code")
        results.append(
            {
                "case": "missing_api_key_rejected",
                "command": missing_key_case,
            }
        )

        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "sample_image_count_available": len(sample_images),
            "cases": results,
        }
        report_path = repo_root / "real_api_benchmark_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("real API benchmark completed")
    print(f"report_path: {repo_root / 'real_api_benchmark_report.json'}")
    for case in results:
        if case["case"] in {"single_image_end_to_end", "multi_image_end_to_end"}:
            print(
                f"{case['case']}: crop={case['crop']['duration_seconds']}s "
                f"tag={case['tag']['duration_seconds']}s "
                f"images_per_second={case['images_per_second']}"
            )
        else:
            print(f"{case['case']}: returncode={case['command']['returncode']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
