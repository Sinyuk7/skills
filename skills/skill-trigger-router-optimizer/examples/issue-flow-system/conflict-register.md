# Conflict Register

## Active Conflicts

| Conflict ID | Intent Region | Skills | Symptom | Arbitration Rule | Status |
|-------------|---------------|--------|---------|------------------|--------|
| `iflow-001` | Fresh issue phrased as "analyze this bug" | `issue-collect`, `issue-handoff` | Analysis wording may skip intake | Missing curated case routes to `issue-collect` | `active` |
| `iflow-002` | "Continue this case" without stage | `issue-handoff`, `issue-resolve` | Continue is underspecified | Check for `handoff.xml`, then inspect user verb | `active` |
| `iflow-003` | "Finish and sync this bug" | `issue-resolve`, `issue-overmind-sync` | Router may treat sync as standalone | Force `chain`: resolve before sync | `active` |

## Unresolved Risks

| Risk | Impact | Proposed Fix | Owner | Next Check |
|------|--------|--------------|-------|------------|
| No explicit top-level stage router | Users may manually choose the wrong stage skill | Add lightweight routing policy or wrapper skill later | issue-flow maintainers | next metadata pass |
| Generic verbs like "continue" and "analyze" remain high-frequency | False positives across stages | Add stronger negative triggers and prerequisite wording | issue-flow maintainers | next eval run |

## Recently Resolved

| Conflict ID | Resolution | Evidence |
|-------------|------------|----------|
| None yet | N/A | Sample audit only |
