# New Triage Handoff Workflow

Generate a new handoff package from raw troubleshooting materials.

## Prerequisites

Read these files before starting:

- `knowledge/triage-principles.md` - Core operating principles
- `knowledge/handoff-schema.md` - Output structure
- `knowledge/evidence-protocol.md` - Evidence referencing rules

---

## Step 1: Material Intake (Deterministic)

Record what user provides in the handoff's `sources` field.

Accept any format:
- Issue title and body
- Comments and chat logs
- Log files, directories, or archives
- Repository access
- Trace IDs, request IDs

**Do not** ask user to reorganize materials.

Output: `case_meta.sources[]` populated

---

## Step 2: Log Collection (Deterministic)

Run log evidence collection script.

```
Script: ./scripts/collect-log-evidence.sh
Input: log directory path, key identifiers, event time + fixed window
Example:
  ./scripts/collect-log-evidence.sh <log_dir> --event "YYYY-MM-DDTHH:MM:SS" --window-seconds 300 --identifiers "id1,id2"
Output: JSON with selected target files (after match + mtime window filters)
Cleanup: ./scripts/collect-log-evidence.sh <log_dir> --cleanup
```

The script handles:
- Directory structure survey
- Targeted archive expansion (only archives whose *filename timestamp* falls within `EVENT_TIME±WINDOW_SECONDS`)
- Error pattern search (`error`, `exception`, `failed`, `timeout`, `panic`)
- Identifier matching
- Second-stage mtime window filter to reduce noise
- Fail-fast if no target files are selected

Record selection reasons and excluded files.

---

## Step 3: Code Location Search (Deterministic)

Run code symbol search script.

```
Script: ./scripts/search-code-symbols.sh
Input: repo path, symbols from logs (function names, class names, routes)
Output: file:line mappings with match type
```

Match types:
- `stacktrace`: from exception stack frames
- `symbol_search`: function/class name match
- `route_mapping`: API route handler lookup
- `keyword`: generic text search

---

## Step 4: Context Extraction (LLM)

From human-written content (issue, comments, chat), extract:

| Field | Source Weight |
|-------|---------------|
| Problem phenomenon | narrative |
| Expected vs actual behavior | narrative |
| Environment (OS, version, branch, commit) | narrative |
| Key timestamps | narrative |
| Key identifiers (trace_id, request_id) | narrative |
| Actions attempted | narrative |
| Human hypotheses | narrative (mark as `people_hypotheses`) |

**Critical**: Human narratives are claims, not facts.
- Add `claimed_by: [source_ref]`
- Do not promote to `confirmed_facts` without evidence

Output: `context_summary` populated

---

## Step 5: Evidence Extraction (LLM)

From collected log file contents, extract:

- Timestamps (with timezone)
- Log levels
- Service/process identifiers
- Exception types and messages
- Request/trace/span IDs
- Endpoints, routes, method names
- Error signature patterns

Create evidence inventory entries with:
- `evidence_id`: E001, E002, ...
- `source_ref`: file path + line numbers
- `content`: excerpt
- `tags`: error, warning, stacktrace, etc.

Output: `evidence_inventory[]` populated

---

## Step 6: Code Mapping Analysis (LLM)

Using search results from Step 3 and evidence from Step 5:

For each code location, determine:
- `file`: path relative to repo root
- `lines`: start-end range
- `symbols`: function/class names
- `match_type`: stacktrace|symbol_search|route_mapping|keyword
- `confidence`: high (stacktrace) | medium (symbol) | low (keyword)
- `evidence_refs`: which evidence led here

**Rule**: No code location without evidence backing.

Output: `code_mapping[]` populated

---

## Step 7: Timeline & Findings Synthesis (LLM)

### Timeline
Build chronological event sequence:
```
timestamp | source | event | evidence_ref
```

Include: first error, subsequent errors, user observations, recovery attempts.
Mark gaps explicitly.

### Findings (Three Tiers)

**Confirmed Facts**: Direct evidence exists
- "Error X at timestamp Y" (with log ref)

**Bounded Inferences**: Reasonable conclusions with stated assumptions
- "Likely timeout issue (evidence: timeout log at T1, error at T2)"

**Open Questions**: Need more investigation
- "Why did retry not succeed?"

Output: `timeline[]`, `findings.*` populated

---

## Step 8: Output Generation (Deterministic)

Generate dual-layer output (schema v2.0):

### 8.1 Summary Generation

```
Template: ./templates/handoff-summary.json
Schema: ./schemas/handoff.schema.json (v2.0)
Target: ≤120 lines
```

**Summary Mode Rules**:
- Include `triage_decision` object (from Step 0)
- `evidence_inventory[*].content`: OPTIONAL (omit or truncate to ≤50 chars)
- All other sections: references only (evidence_refs, not full content)
- Add `_meta.evidence_attachment_available: true` if evidence file generated

### 8.2 Evidence Attachment Generation (Optional)

```
Template: ./templates/handoff-evidence.json
Schema: ./schemas/evidence.schema.json (v2.0)
```

**Generate evidence attachment WHEN**:
- Total evidence content >5KB, OR
- Any single evidence item >500 bytes, OR
- User explicitly requests full evidence

**Evidence Mode Rules**:
- `evidence_inventory[*].content`: REQUIRED (full original content)
- Include `extraction_metadata` for each item
- Populate `statistics` section

### 8.3 Validation

Validate both files against respective schemas:
```bash
# If using JSON Schema validator
jsonschema -i handoff.summary.json schemas/handoff.schema.json
jsonschema -i handoff.evidence.json schemas/evidence.schema.json
```

---

## Step 9: Self-Check (Deterministic)

Verify checklist:

- [ ] All key identifiers appear in evidence search
- [ ] Selected log files are justified
- [ ] Excluded files are documented
- [ ] Code mappings have evidence backing
- [ ] No human narrative promoted to fact without verification
- [ ] Open questions include obvious gaps
- [ ] Output passes schema validation

---

## Data Flow Summary

```
Step 0 (D): triage_decision ──────────────────────────────────┐
Step 1 (D): sources[] ─────────────────────────────────────┐  │
Step 2 (D): log_files[] ──────────────────────────────────┐│  │
Step 3 (D): code_search_results[] ────────────────────────┐││  │
Step 4 (L): context_summary ───────────────────────────┐  │││  │
Step 5 (L): evidence_inventory[] ──────────────────────┤  │││  │
Step 6 (L): code_mapping[] ◄───────────────────────────┴──┘││  │
Step 7 (L): timeline[], findings.* ◄───────────────────────┘│  │
Step 8.1 (D): handoff.summary.json ◄────────────────────────┴──┘
Step 8.2 (D): handoff.evidence.json (optional) ◄───────────────┘
Step 9 (D): validation_result
```

**V2.0 Changes**:
- Step 0 injects `triage_decision` into summary
- Step 8 splits into summary (≤120 lines) + evidence (optional)
- Evidence content in summary: optional/truncated
- Evidence content in attachment: required/full

---

## Next Move

If user wants to refine with new materials: load `workflows/handoff-refinement.md`
If user wants to evaluate quality: load `workflows/handoff-evaluation.md`