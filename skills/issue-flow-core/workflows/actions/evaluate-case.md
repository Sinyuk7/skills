# evaluate-case

Case action, not a top-level stage.

Use this action when:

- checking whether a case is ready for external handoff
- assessing whether collection should resume
- deciding whether resolution can begin

Typical outputs:

- updates to `status.yaml`
- readiness notes in `analysis/handoff.xml` (`next_step`)
