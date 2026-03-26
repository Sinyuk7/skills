from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

from aiohttp import web
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "lora_tagger_cli.py"
RAW_SAMPLE_DIR = REPO_ROOT / "exsample"
RAW_SAMPLE_IMAGES = sorted(
    path
    for path in RAW_SAMPLE_DIR.iterdir()
    if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".heic"}
)

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lora_tagger.config import build_runtime_config, skill_root_from_script
from lora_tagger.captioning import request_payload_for_item
from lora_tagger.pipeline import normalize_phase, tag_phase


def copy_sample_images(destination: Path, count: int = 2) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    for source_path in RAW_SAMPLE_IMAGES[:count]:
        shutil.copy2(source_path, destination / source_path.name)
    return destination


def run_cli(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPT_PATH), *args]
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


class PipelineCliTests(unittest.TestCase):
    def test_crop_dry_run_does_not_create_dataset_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_dir = copy_sample_images(Path(temp_dir) / "raw")

            result = run_cli(["crop", str(raw_dir), "--limit", "2", "--dry-run"])

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("ratio scan summary:", result.stdout)
            self.assertIn("images_to_write: 2", result.stdout)
            self.assertFalse((raw_dir / "dataset").exists())

    def test_crop_creates_dataset_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_dir = copy_sample_images(Path(temp_dir) / "raw")

            result = run_cli(["crop", str(raw_dir), "--limit", "2"])

            self.assertEqual(result.returncode, 0, result.stderr)
            dataset_dir = raw_dir / "dataset"
            self.assertTrue(dataset_dir.exists())
            self.assertTrue((dataset_dir / "_meta" / "manifest.json").exists())
            self.assertTrue((dataset_dir / "_meta" / "reports" / "ratio-summary.json").exists())

            image_paths = sorted(dataset_dir.glob("*.jpg"))
            self.assertEqual(len(image_paths), 2)
            for image_path in image_paths:
                with Image.open(image_path) as image:
                    self.assertIn(image.size, {(1280, 1280), (1024, 1536)})

            manifest = json.loads((dataset_dir / "_meta" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["version"], 2)
            self.assertEqual(manifest["mode"], "crop")
            self.assertEqual(len(manifest["items"]), 2)

    def test_tag_dry_run_does_not_write_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_dir = copy_sample_images(Path(temp_dir) / "raw")
            crop_result = run_cli(["crop", str(raw_dir), "--limit", "2"])
            self.assertEqual(crop_result.returncode, 0, crop_result.stderr)

            dataset_dir = raw_dir / "dataset"
            before_files = sorted(
                str(path.relative_to(dataset_dir))
                for path in dataset_dir.rglob("*")
                if path.is_file()
            )

            result = run_cli(["tag", str(dataset_dir), "--limit", "2", "--dry-run"])

            after_files = sorted(
                str(path.relative_to(dataset_dir))
                for path in dataset_dir.rglob("*")
                if path.is_file()
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("tag dry-run summary:", result.stdout)
            self.assertEqual(before_files, after_files)

    def test_tag_rejects_raw_input_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_dir = copy_sample_images(Path(temp_dir) / "raw")

            result = run_cli(["tag", str(raw_dir)])

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Dataset manifest not found", result.stderr)

    def test_tag_requires_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_dir = copy_sample_images(Path(temp_dir) / "raw")
            crop_result = run_cli(["crop", str(raw_dir), "--limit", "2"])
            self.assertEqual(crop_result.returncode, 0, crop_result.stderr)

            dataset_dir = raw_dir / "dataset"
            env = os.environ.copy()
            env.pop("N1N_API_KEY", None)

            result = run_cli(["tag", str(dataset_dir), "--limit", "2"], env=env)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Missing required environment variable: N1N_API_KEY", result.stderr)

    def test_evals_have_expectations(self) -> None:
        evals_path = REPO_ROOT / "evals" / "evals.json"
        payload = json.loads(evals_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["skill_name"], "skill-lora-tagger")
        self.assertGreaterEqual(len(payload["evals"]), 4)
        for eval_case in payload["evals"]:
            self.assertTrue(eval_case["expectations"], f"Eval {eval_case['id']} has no expectations")

    def test_runtime_config_loads_strict_defaults_and_top_p(self) -> None:
        config = build_runtime_config(
            user_config_path=(skill_root_from_script() / "references" / "config-skeleton.yaml").resolve(),
            developer_defaults_path=(
                skill_root_from_script() / "references" / "developer-defaults.yaml"
            ).resolve(),
        )

        self.assertEqual(config.temperature, 0.1)
        self.assertEqual(config.top_p, 1.0)
        self.assertEqual(config.max_tokens, 512)

    def test_runtime_config_requires_temperature(self) -> None:
        self._assert_missing_defaults_field("  temperature: 0.1\n", "developer_defaults.captioning.temperature")

    def test_runtime_config_requires_max_tokens(self) -> None:
        self._assert_missing_defaults_field("  max_tokens: 512\n", "developer_defaults.captioning.max_tokens")

    def test_runtime_config_requires_top_p(self) -> None:
        self._assert_missing_defaults_field("  top_p: 1.0\n", "developer_defaults.captioning.top_p")

    def test_runtime_config_requires_separator(self) -> None:
        self._assert_missing_defaults_field(
            "  separator: \". \"\n",
            "developer_defaults.caption_assembly.separator",
        )

    def test_runtime_config_requires_alignment(self) -> None:
        self._assert_missing_defaults_field(
            "  alignment: 64\n",
            "developer_defaults.images.alignment",
        )

    def test_runtime_config_requires_system_prompt_file(self) -> None:
        with mock.patch("lora_tagger.config.skill_root_from_script", return_value=Path("Z:/missing-skill-root")):
            with self.assertRaisesRegex(FileNotFoundError, "Required system prompt file does not exist"):
                build_runtime_config(
                    user_config_path=(skill_root_from_script() / "references" / "config-skeleton.yaml").resolve(),
                    developer_defaults_path=(
                        skill_root_from_script() / "references" / "developer-defaults.yaml"
                    ).resolve(),
                )

    def _assert_missing_defaults_field(self, removed_line: str, expected_error_fragment: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            defaults_path = temp_root / "developer-defaults.yaml"
            defaults_text = (
                (skill_root_from_script() / "references" / "developer-defaults.yaml")
                .read_text(encoding="utf-8")
                .replace(removed_line, "")
            )
            defaults_path.write_text(defaults_text, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, expected_error_fragment):
                build_runtime_config(
                    user_config_path=(skill_root_from_script() / "references" / "config-skeleton.yaml").resolve(),
                    developer_defaults_path=defaults_path,
                )


class TagPhaseIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_tag_phase_writes_txt_raw_and_parsed_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            raw_dir = copy_sample_images(temp_root / "raw")
            dataset_dir = raw_dir / "dataset"

            crop_config = build_runtime_config(
                user_config_path=(skill_root_from_script() / "references" / "config-skeleton.yaml").resolve(),
                developer_defaults_path=(
                    skill_root_from_script() / "references" / "developer-defaults.yaml"
                ).resolve(),
            )
            normalize_phase(raw_dir, dataset_dir, crop_config, limit=2, dry_run=False)

            async def handler(request: web.Request) -> web.Response:
                request_payload = await request.json()
                self.assertEqual(request_payload["temperature"], 0.1)
                self.assertEqual(request_payload["top_p"], 1.0)
                self.assertEqual(request_payload["max_tokens"], 512)
                response_payload = {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "subject": "test subject",
                                        "action": "standing",
                                        "details": "blue dress",
                                        "scene": "studio backdrop",
                                        "composition": "centered portrait",
                                        "camera": "50mm photo",
                                        "lighting": "soft key light",
                                        "style": "clean fashion photo",
                                    }
                                )
                            }
                        }
                    ]
                }
                return web.json_response(response_payload)

            app = web.Application()
            app.router.add_post("/v1/chat/completions", handler)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "127.0.0.1", 0)
            await site.start()
            sockets = getattr(site._server, "sockets", [])
            port = sockets[0].getsockname()[1]

            prompt_path = temp_root / "user-prompt.txt"
            prompt_path.write_text("Return JSON only.", encoding="utf-8")
            user_config_path = temp_root / "config.yaml"
            user_config_path.write_text(
                textwrap.dedent(
                    f"""
                    resolutions:
                      ratio_long_edge_map:
                        "1:1": 1280
                        "2:3": 1536

                    captioning:
                      user_prompt_path: {prompt_path.as_posix()}

                    caption_assembly:
                      shuffle_values: false
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            defaults_path = temp_root / "developer-defaults.yaml"
            defaults_path.write_text(
                textwrap.dedent(
                    f"""
                    paths:
                      output_dir_name: dataset

                    images:
                      supported_extensions:
                        - .jpg
                        - .jpeg
                        - .png
                        - .webp
                        - .heic
                      output_jpeg_quality: 95
                      rename_pattern: "image_{{index:04d}}"
                      alignment: 64

                    resolutions:
                      supported_long_edges:
                        - 1024
                        - 1280
                        - 1536
                      ratio_warn_threshold: 0.03

                    vision_upload:
                      long_edge: 896
                      jpeg_quality: 80
                      transport: data_url

                    captioning:
                      primary_base_url: http://127.0.0.1:{port}/v1
                      fallback_base_url: http://127.0.0.1:{port}/v1
                      model: fake-model
                      api_key_env: N1N_API_KEY
                      concurrency: 2
                      timeout_seconds: 30
                      max_retries: 1
                      temperature: 0.1
                      top_p: 1.0
                      max_tokens: 512

                    caption_assembly:
                      separator: ". "
                      keep_subject_first: true
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            original_api_key = os.environ.get("N1N_API_KEY")
            os.environ["N1N_API_KEY"] = "test-key"
            try:
                tag_config = build_runtime_config(
                    user_config_path=user_config_path,
                    developer_defaults_path=defaults_path,
                )
                await tag_phase(dataset_dir, tag_config, limit=2, dry_run=False)
            finally:
                if original_api_key is None:
                    os.environ.pop("N1N_API_KEY", None)
                else:
                    os.environ["N1N_API_KEY"] = original_api_key
                await runner.cleanup()

            txt_paths = sorted(dataset_dir.glob("*.txt"))
            raw_paths = sorted((dataset_dir / "_meta" / "raw_responses").glob("*.json"))
            parsed_paths = sorted((dataset_dir / "_meta" / "parsed").glob("*.json"))
            self.assertEqual(len(txt_paths), 2)
            self.assertEqual(len(raw_paths), 2)
            self.assertEqual(len(parsed_paths), 2)

            caption_text = txt_paths[0].read_text(encoding="utf-8")
            self.assertTrue(caption_text.startswith("test subject."))

            report = json.loads(
                (dataset_dir / "_meta" / "reports" / "caption-summary.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(report["complete_count"], 2)
            self.assertEqual(report["failed_count"], 0)

    async def test_request_payload_uses_yaml_sampling_parameters(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            raw_dir = copy_sample_images(temp_root / "raw", count=1)
            dataset_dir = raw_dir / "dataset"

            config = build_runtime_config(
                user_config_path=(skill_root_from_script() / "references" / "config-skeleton.yaml").resolve(),
                developer_defaults_path=(
                    skill_root_from_script() / "references" / "developer-defaults.yaml"
                ).resolve(),
            )
            normalize_phase(raw_dir, dataset_dir, config, limit=1, dry_run=False)

            manifest = json.loads((dataset_dir / "_meta" / "manifest.json").read_text(encoding="utf-8"))
            item = manifest["items"][0]
            payload, _ = request_payload_for_item(item, "Return JSON only.", config)

            self.assertEqual(payload["temperature"], 0.1)
            self.assertEqual(payload["top_p"], 1.0)
            self.assertEqual(payload["max_tokens"], 512)


if __name__ == "__main__":
    unittest.main()
