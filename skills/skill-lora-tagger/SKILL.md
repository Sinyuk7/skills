---
name: skill-lora-tagger
description: Build, fix, or operate a two-step LoRA dataset preprocessing workflow. Use this when users need to crop raw image folders into ai-toolkit-ready JPG datasets, then caption that cropped dataset through an OpenAI-compatible Vision API into `.txt` pairs with per-image raw JSON sidecars. Prefer this over treating the task as generic image tagging whenever the real job is preparing a repeatable training dataset.
---

# LoRA Dataset Preprocessing

Treat this skill as a clean two-step dataset workflow:

1. `crop <raw_input_dir>`
2. `tag <dataset_dir>`

The important contract is simple:

- `crop` starts from a raw image directory and creates a new `dataset` directory
- `tag` only accepts a dataset directory produced by `crop`
- final training artifacts are `.jpg` plus `.txt`
- raw JSON is an intermediate artifact, not the training format

## When To Use

- The user wants to prepare a raw image folder for LoRA training.
- The user mentions ai-toolkit, FLUX, SDXL, aspect ratios, long-edge buckets, or dataset cleanup.
- The user has mixed image formats and needs a repeatable crop-plus-caption workflow.
- The user says "tag these images," but the real task includes dataset structure, manifests, or training compatibility.

## Procedure

### Step 1: Frame The Request As Two Commands

Infer or state the workflow explicitly:

- use `crop` when starting from raw image folders
- use `tag` when the input is already a cropped dataset directory

Do not describe unsupported public modes such as `build`, `assemble-only`, `caption-only`, or `retry-failed`.

### Step 2: Inspect The Existing Layout

Before changing code, inspect:

- the CLI entry point
- `references/config-skeleton.yaml`
- `references/developer-defaults.yaml`
- the manifest format under `dataset/_meta/manifest.json`
- the output layout for `.jpg`, `.txt`, raw JSON, parsed JSON, and reports

Keep the workflow centered on the current implementation instead of reviving older design ideas.

### Step 3: Preserve The Output Contract

The skill should preserve these guarantees:

- cropped images are written as deterministic `.jpg` files
- captions are written as matching `.txt` files in the same dataset directory
- each successful caption request writes a raw JSON sidecar before parsing
- parsed JSON is stored under `_meta/parsed`
- manifests and reports stay under `_meta`
- the user edits `user-prompt.txt`, not low-level request payloads
- `system_prompt` comes from `references/system-prompt.txt`

Read `references/pipeline-contract.md` when you need the canonical contract.

### Step 4: Keep The Implementation Lean

When modifying the code:

- treat the `crop` output manifest as the only supported `tag` input
- fail fast if the dataset directory or manifest is missing
- require the configured API key for `tag`
- keep `dry-run` truly read-only
- prefer deleting stale branches and unused config keys over adding compatibility layers

### Step 5: Verify The Workflow

Verify the important invariants:

- `crop --dry-run` does not create files
- `crop` creates cropped `.jpg` files plus `_meta/manifest.json`
- `tag --dry-run` does not create files
- `tag` fails on raw input directories that do not contain a valid dataset manifest
- `tag` fails fast when the API key is missing
- successful tagging writes `.txt`, raw JSON, parsed JSON, and a caption summary into the same dataset directory

## Output Format

When responding after using this skill, structure the answer around:

1. which command path you used: `crop` or `tag`
2. the dataset contract being preserved
3. the files or code paths changed
4. verification performed
5. remaining risks, mainly around crop quality or provider failures

## Bundled Resources

- `references/pipeline-contract.md` - current two-step dataset contract
- `references/config-skeleton.yaml` - user-facing config surface
- `references/developer-defaults.yaml` - developer defaults and request parameters
- `references/user-prompt.txt` - user-edited prompt text for JSON shape
- `evals/evals.json` - skill evaluation prompts and expectations

## Notes

- `tag` is for dataset directories, not raw image directories.
- JSON shape should come from the prompt file, not hard-coded output fields in the skill.
- `subject` stays first during caption assembly when present.
- If shuffle is enabled, only shuffle values after `subject`.
- Keep the workflow boring and reliable. Do not add old modes or compatibility layers unless the user explicitly asks for them.
