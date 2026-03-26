# Pipeline Contract

This skill exposes one public workflow with two commands:

1. `crop <raw_input_dir>`
2. `tag <dataset_dir>`

The contract is intentionally small. Do not treat older design notes as a source of truth.

## Final Output Contract

The dataset produced by this workflow should be directly usable by ai-toolkit-style LoRA training:

- `image_0001.jpg`
- `image_0001.txt`
- `image_0002.jpg`
- `image_0002.txt`

Requirements:

- every final image has one matching caption file
- final images are JPEG
- final dimensions match the configured ratio-to-long-edge rules exactly
- final caption text is plain text, not JSON
- every successful captioned item has one raw response sidecar JSON file
- metadata lives under `_meta` instead of being mixed into the training root

## Public Command Contract

### `crop <raw_input_dir>`

Expected behavior:

- recursively discover supported raw image formats
- scan aspect ratios before rewriting files
- print a summary during dry-run
- create a collision-safe dataset directory such as `dataset` or `dataset-2`
- center crop to the exact derived target size
- write deterministic `.jpg` files
- write `_meta/manifest.json`
- write `_meta/reports/ratio-summary.json`

### `tag <dataset_dir>`

Expected behavior:

- only accept a dataset directory produced by `crop`
- fail fast if `_meta/manifest.json` is missing or invalid
- require the configured API key
- send one cropped image per request
- persist the full raw provider response before parsing it
- write parsed JSON under `_meta/parsed`
- write final `.txt` caption files beside the cropped `.jpg` files
- write `_meta/reports/caption-summary.json`

## Config Contract

User-facing config should stay minimal:

- ratio-to-long-edge mapping
- `user_prompt.txt` path
- caption assembly options such as shuffle

Everything else should remain a developer default loaded from `references/developer-defaults.yaml`:

- output directory naming
- supported extensions
- JPEG quality
- API base URLs
- model choice
- concurrency, timeout, retry, temperature, top_p, and max_tokens

The system prompt is a separate single source of truth:

- `references/system-prompt.txt`

Missing developer-default fields or a missing system prompt file are treated as configuration errors.

## Prompt Contract

- the user edits `user-prompt.txt`
- the developer-owned system prompt comes from `references/system-prompt.txt`
- the implementation builds the request payload internally
- the prompt defines the JSON shape
- the final training export still becomes plain text

## Manifest Contract

The manifest is a strict internal contract between `crop` and `tag`.

Required top-level fields:

- `version`
- `mode`
- `input_path`
- `dataset_dir`
- `created_at`
- `config_snapshot`
- `items`

Required item fields:

- `id`
- `source_path`
- `source_rel_path`
- `source_fingerprint`
- `image_path`
- `text_path`
- `raw_response_path`
- `parsed_json_path`
- `final_caption`
- `status`
- `last_error`

This skill does not preserve backwards compatibility for older manifest formats.

## Quality Bar

The workflow should feel boring and reliable:

- deterministic filenames
- explicit failures
- no silent format drift
- no hidden compatibility branches
- no unsupported public modes
