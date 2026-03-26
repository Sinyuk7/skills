from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    cli_path = repo_root / "scripts" / "lora_tagger_cli.py"
    sample_dir = repo_root / "exsample"
    sample_images = sorted(
        path
        for path in sample_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".heic"}
    )

    if not os.environ.get("N1N_API_KEY", "").strip():
        raise RuntimeError("N1N_API_KEY is required for the real API smoke test.")

    with tempfile.TemporaryDirectory() as temp_dir:
        raw_dir = Path(temp_dir) / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        for source_path in sample_images[:2]:
            shutil.copy2(source_path, raw_dir / source_path.name)

        crop_result = subprocess.run(
            [sys.executable, str(cli_path), "crop", str(raw_dir), "--limit", "2"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if crop_result.returncode != 0:
            raise RuntimeError(f"crop failed:\n{crop_result.stderr}")

        dataset_dir = raw_dir / "dataset"
        tag_result = subprocess.run(
            [sys.executable, str(cli_path), "tag", str(dataset_dir), "--limit", "2"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if tag_result.returncode != 0:
            raise RuntimeError(f"tag failed:\n{tag_result.stderr}")

        jpg_count = len(list(dataset_dir.glob("*.jpg")))
        txt_count = len(list(dataset_dir.glob("*.txt")))
        raw_count = len(list((dataset_dir / "_meta" / "raw_responses").glob("*.json")))
        parsed_count = len(list((dataset_dir / "_meta" / "parsed").glob("*.json")))
        report = json.loads(
            (dataset_dir / "_meta" / "reports" / "caption-summary.json").read_text(
                encoding="utf-8"
            )
        )

        assert jpg_count == txt_count == raw_count == parsed_count == 2
        assert report["complete_count"] == 2
        assert report["failed_count"] == 0

        print("real API smoke test passed")
        print(f"dataset_dir: {dataset_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
