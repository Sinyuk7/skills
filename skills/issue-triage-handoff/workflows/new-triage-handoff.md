# New Triage Handoff Workflow

Use this workflow when the user provides raw troubleshooting materials and wants to generate a new handoff package.

## Prerequisites

Before starting, load:
- `knowledge/triage-principles.md` - Core operating principles
- `knowledge/handoff-schema.md` - Output structure definition
- `knowledge/evidence-protocol.md` - Evidence referencing rules

## Step 1: Material Intake

Accept whatever the user provides without requiring pre-formatting:
- Issue title and body
- Issue comments
- Chat logs / discussion threads
- Log files, directories, or archives
- Repository access
- Trace IDs, request IDs, or other identifiers

**Do not** ask the user to reorganize materials into a template first. The skill's job is to handle messy input.

Record what was provided in the handoff's `sources` field.

## Step 2: Context Extraction

Extract structured information from human-written content (issue, comments, chat):

| Extract | Source Weight |
|---------|---------------|
| Problem phenomenon (what's broken) | narrative |
| Expected vs actual behavior | narrative |
| Environment (OS, version, branch, commit) | narrative |
| Key timestamps | narrative |
| Key identifiers (trace_id, request_id, user_id) | narrative |
| Actions already attempted | narrative |
| Human hypotheses / suspicions | narrative (mark as `people_hypotheses`) |

**Critical**: Human narratives are claims, not facts. Mark them accordingly:
- `claimed_by: [source_ref]`
- Never promote to `confirmed_facts` without evidence

## Step 3: Log Triage

For large log directories, do NOT attempt full-text summarization. Instead:

### 3.1 Quick Survey
List directory structure, identify log types, note file sizes and timestamps.

### 3.2 Targeted Search
Use `ripgrep` or equivalent for:
- Error patterns: `error`, `exception`, `failed`, `timeout`, `panic`
- Key identifiers extracted from context
- Timestamps within the incident window
- Service/process names mentioned in the issue

### 3.3 Evidence Selection
Select files based on:
1. Contains error/exception within time window
2. Contains key identifiers
3. Time-proximate to reported incident

Record for each selected file:
- Path
- Selection reason
- Key line numbers

Record for excluded files:
- Why excluded (no errors, wrong time window, unrelated service)

### 3.4 Evidence Extraction
From selected files, extract:
- Timestamps (with timezone if available)
- Log levels
- Service/process identifiers
- Exception types and messages
- Request/trace/span IDs
- Endpoints, routes, method names
- Error signature patterns (for deduplication)

## Step 4: Code Mapping

Based on evidence from logs and context, locate relevant code:

### 4.1 Stacktrace-Driven
If logs contain stacktraces:
- Map each frame to file:line in the repo
- Note which frames are in user code vs libraries

### 4.2 Symbol-Driven
If logs mention function/class names:
- Search repo for definitions
- Record file, line range, and match confidence

### 4.3 Route/Endpoint-Driven
If logs mention API routes or endpoints:
- Find handler definitions
- Trace middleware chain if relevant

For each code location, record:
- `file`: Path relative to repo root
- `lines`: Line range (start-end)
- `symbols`: Function/class names
- `match_type`: `stacktrace` | `symbol_search` | `route_mapping` | `keyword`
- `confidence`: `high` (stacktrace) | `medium` (symbol match) | `low` (keyword)
- `evidence_ref`: Which log entry led here

**Rule**: No code location without evidence. Do not speculate.

## Step 5: Timeline Construction

Build a timeline of events:

```
timestamp | source | event | evidence_ref
```

Include:
- First error occurrence
- Subsequent errors
- User-reported observation times
- Deployment/change events if mentioned
- Recovery attempts

Mark gaps where timeline is uncertain.

## Step 6: Findings Synthesis

Organize findings into three tiers:

### Confirmed Facts
Things with direct evidence:
- "Error X occurred at timestamp Y" (with log ref)
- "Service A returned 500 to Service B" (with log ref)

### Bounded Inferences
Reasonable conclusions with stated assumptions:
- "Error likely triggered by timeout (evidence: timeout log at T1, error log at T2)"
- "Suspect database connection issue (evidence: connection pool exhausted message)"

### Open Questions
Things that need more investigation:
- "Why did the retry not succeed?"
- "What changed between working state and broken state?"

## Step 7: Output Generation

Generate handoff package following `templates/handoff-template.json`.

Ensure:
- All `evidence_ref` fields are populated
- No findings without supporting evidence
- Clear distinction between facts/inferences/questions
- Code mappings include confidence levels
- Timeline gaps are explicitly noted

## Step 8: Self-Check

Before delivering, verify:
- [ ] All key identifiers from context appear in evidence search
- [ ] Selected log files are justified
- [ ] Excluded files are documented
- [ ] Code mappings have evidence backing
- [ ] No human narrative promoted to fact without verification
- [ ] Open questions include obvious gaps
- [ ] Output follows schema

## Next Move

If user wants to refine the handoff with new materials, load `workflows/handoff-refinement.md`.

If user wants to evaluate handoff quality, load `workflows/handoff-evaluation.md`.
