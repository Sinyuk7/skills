# readiness graph

Dependencies unlock artifact generation.

They do not mean:

- the next stage must run now
- the previous stage is permanently closed
- every case must produce every artifact

Typical flow:

`source-manifest.yaml` -> `inventory.yaml` -> `evidence-pack.xml` ->
`findings.xml` -> `handoff.xml` -> `next-step.yaml`
