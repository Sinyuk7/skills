# source-curation

Purpose:

- account for all user-provided raw materials
- narrow the working set to issue-relevant evidence
- avoid repeated rescans of large raw directories by default

Expected outputs:

- `inventory.yaml`
- `curated/logs/`
- `curated/media/`
- `curated/notes/`
- `curated/ocr/`
- `curated/excerpts/`

Rules:

- every input should appear in `source-manifest.yaml`
- every curated or skipped item should be represented in `inventory.yaml`
- post-curation work should prefer case artifacts over raw directories
