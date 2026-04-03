# readiness graph

Dependencies unlock artifact generation.

Readiness means:

- Downstream artifact generation is unlocked (not that it must execute immediately)
- Previous stages remain open for recollection if needed (not permanently closed)
- Optional artifacts remain optional (not every case produces every artifact)

Typical flow:

`sources.yaml` -> `curated/*` -> `investigation.xml` -> `handoff.xml` -> `resolution.xml` -> `verification.md`

The `next_step` recommendation now lives inside `analysis/handoff.xml`, and verification
state lives inside `resolve/resolution.xml`.
