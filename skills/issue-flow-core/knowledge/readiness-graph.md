# readiness graph

Dependencies unlock artifact generation.

Readiness means:

- Downstream artifact generation is unlocked (not that it must execute immediately)
- Previous stages remain open for recollection if needed (not permanently closed)
- Optional artifacts remain optional (not every case produces every artifact)

Typical flow:

`sources.yaml` -> `curated/*` -> `investigation.xml` -> `findings.xml` -> `handoff.xml` -> `next-step.yaml`
