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
Input: log directory path, key identifiers, time window
Output: list of relevant log files with line ranges
```

The script handles:
- Directory structure survey
- Error pattern search (`error`, `exception`, `failed`, `timeout`, `panic`)
- Identifier matching
- Time window filtering

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

Generate handoff JSON following template.

```
Template: ./templates/handoff-template.json
Schema: ./schemas/handoff.schema.json
```

Validate against schema.

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
Step 1 (D): sources[] ─────────────────────────────────────┐
Step 2 (D): log_files[] ──────────────────────────────────┐│
Step 3 (D): code_search_results[] ────────────────────────┐││
Step 4 (L): context_summary ───────────────────────────┐  │││
Step 5 (L): evidence_inventory[] ──────────────────────┤  │││
Step 6 (L): code_mapping[] ◄───────────────────────────┴──┘││
Step 7 (L): timeline[], findings.* ◄───────────────────────┘│
Step 8 (D): handoff.json ◄─────────────────────────────────┘
Step 9 (D): validation_result
```

---

## Next Move

If user wants to refine with new materials: load `workflows/handoff-refinement.md`
If user wants to evaluate quality: load `workflows/handoff-evaluation.md`