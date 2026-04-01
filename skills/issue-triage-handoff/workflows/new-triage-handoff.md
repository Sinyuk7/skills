# New Triage Handoff Workflow

Generate a new handoff package from raw troubleshooting materials.

## Prerequisites

Read these files before starting:

- `knowledge/triage-principles.md` - Core operating principles
- `knowledge/handoff-schema.md` - Output structure
- `knowledge/evidence-protocol.md` - Evidence referencing rules

---

## Step 0.5: Evidence Inventory (Deterministic)

**Purpose**: Scan ALL input files and record processing status. Prevents silent file skipping.

Run evidence inventory script:

```bash
./scripts/build-evidence-inventory.sh <input_directory> evidence-inventory.json
```

**Output**: JSON array with:
- `file_path`: Full path to each file
- `type`: text | image | video | document | unknown
- `size_bytes`: File size
- `mtime`: Modification timestamp
- `status`: parsed | skipped | failed
- `reason`: Why not parsed (empty string if parsed)
- `evidence_refs`: Links to extracted evidence (populated in later steps)

**Validation**:
- Total file count == inventory array length (no silent skips)
- All `status: "skipped"` entries MUST have non-empty `reason`

**Integration**:
- Feeds into Step 2 (text evidence) and Step 2.5 (multimodal evidence)
- Provides traceability: every input file accounted for

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

## Step 2.5: Multimodal Evidence Collection (Deterministic)

**Purpose**: Extract evidence from images and videos.

Run multimodal evidence collection script:

```bash
./scripts/collect-multimodal-evidence.sh <input_directory> multimodal-evidence.json
```

**Output**: JSON array with multimodal evidence:
- `evidence_id`: E001, E002, ...
- `type`: image | video
- `visual_signals`: Detected visual indicators (error_dialog, error_text, etc.)
- `ocr_text`: Text extracted from image via OCR
- `relevance`: direct | context | weak
- `metadata`:
  - Images: dimensions, format, file_size_bytes
  - Videos: dimensions, duration_seconds, format, file_size_bytes

**Dependencies** (optional but recommended):
- `exiftool`: Image/video metadata extraction
- `tesseract`: OCR for images
- `ffprobe`: Video metadata extraction

**Evidence Weight** (see evidence-protocol.md):
1. Stacktrace/exception with timestamp (highest)
2. **Image with OCR + timestamp + visual_signals** (high)
3. Structured logs with trace IDs
4. **Screenshot with visual_signals only** (medium)
5. Unstructured logs
6. Human comments
7. **Video without error signals** (low — requires interpretation)

**Top-K Filtering**: Include only Top-K multimodal evidence (default K=3) in summary.

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

## Step 6.5: Project Context Loading (LLM)

**Purpose**: Load project-specific context to prevent incorrect responsibility attribution.

**Check for context file**: `./triage/project-context.md` or `./knowledge/project-context.md`

If file exists:
1. Parse YAML sections:
   - `team_role`: provider | consumer | integration | platform
   - `ownership.our_code`: List of components we own
   - `forbidden_assumptions`: Phrases to avoid in synthesis

2. Apply context-aware filtering:

   **If `team_role: provider`**:
   - Remove recommendations suggesting to "investigate external server"
   - Focus on internal code paths, configuration, deployment
   - `suitable_for`: Include `rca_agent`, `patch_agent` (we can fix our code)

   **If `team_role: consumer`**:
   - Focus on integration points with external services
   - Emphasize API behavior, credentials, network issues
   - `suitable_for`: Typically `human_review` (can't patch external code)

   **If `team_role: integration`**:
   - Balance upstream and downstream investigation
   - Focus on connection points, data transformation
   - `suitable_for`: `rca_agent` for our integration logic

3. Validate context:
   - File timestamp <90 days (warn if stale)
   - `team_role` is valid enum value
   - `ownership.our_code` is non-empty

**If file does not exist**: Skip this step, proceed with generic synthesis.

**Output**: Context object passed to Step 7 synthesis.

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

Generate dual-layer output:

### 8.1 Summary Generation

```
Template: ./templates/handoff-summary.json
Schema: ./schemas/handoff.schema.json
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
Schema: ./schemas/evidence.schema.json
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

**Key Features**:
- Step 0 decision gate prevents unnecessary full pipeline
- Step 8 dual-layer output: summary (≤120 lines) + optional evidence attachment
- Evidence content in summary: optional/truncated for token efficiency
- Evidence content in attachment: required/full for forensic analysis

---

## Next Move

If user wants to refine with new materials: load `workflows/handoff-refinement.md`
If user wants to evaluate quality: load `workflows/handoff-evaluation.md`
