# ISSUE TRIAGE HANDOFF — PROJECT KNOWLEDGE BASE

**Generated:** 2026-04-01 16:45 CST  
**Commit:** 408232f  
**Branch:** main

## OVERVIEW

LLM skill that compresses raw troubleshooting materials (logs, chat, comments) into structured handoff packages. Markdown workflows + Bash scripts + JSON schemas. Deterministic-first architecture.

## STRUCTURE

```
issue-triage-handoff/
├── SKILL.md                    # Entry point: intent dispatch, execution flow
├── workflows/                  # Workflow orchestrators (new, refine, evaluate)
│   ├── new-triage-handoff.md
│   ├── handoff-refinement.md
│   └── handoff-evaluation.md
├── knowledge/                  # Core principles, schemas, protocols
│   ├── triage-principles.md
│   ├── handoff-schema.md
│   └── evidence-protocol.md
├── scripts/                    # Deterministic tools (log collection, code search)
│   ├── collect-log-evidence.sh
│   └── search-code-symbols.sh
├── schemas/                    # JSON Schema validation
│   ├── handoff.schema.json
│   └── evaluation.schema.json
├── templates/                  # Output templates
│   └── handoff-template.json
├── __test__/                   # Integration test cases (conversation logs)
└── evals/                      # Test specifications (evals.json)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add new workflow | `workflows/*.md` | Follow intent dispatch pattern from SKILL.md |
| Modify evidence rules | `knowledge/evidence-protocol.md` | Impacts all workflows |
| Change output structure | `schemas/handoff.schema.json` + `templates/` | Must bump schema_version |
| Add core principle | `knowledge/triage-principles.md` | Update all workflow references |
| Fix log collection | `scripts/collect-log-evidence.sh` | Time-window filtering logic |
| Fix code search | `scripts/search-code-symbols.sh` | Multi-framework symbol resolution |
| Add test case | `__test__/case_NN.txt` + `evals/evals.json` | Follow naming convention |
| Validate output | `schemas/*.schema.json` | JSON Schema draft-07 |

## CONVENTIONS

### Operational Architecture

**Hybrid Execution Model** (SKILL.md § Execution Flow):
- `D: deterministic → L: LLM → D: deterministic` (batch deterministic ops to minimize context switches)
- Scripts run BEFORE LLM extraction (evidence collection → synthesis → validation)
- Script failures block LLM tasks (non-recoverable)

**Intent Dispatch** (SKILL.md § Intent Dispatch):
- User intent → workflow mapping enforced
- Ambiguous intent → must clarify (don't auto-guess)
- 3 mutually exclusive modes: create | refine | evaluate

**Time-Windowed Evidence Collection** (SKILL.md § Deterministic batching note):
- Anchor: `--event "YYYY-MM-DDTHH:MM:SS"` (required)
- Window: `--window-seconds 300` (default 5 minutes)
- Dual-stage filtering: filename timestamp → mtime filter
- Fail-fast if zero files after filtering

### Evidence & Findings

**Evidence ID Sequencing** (knowledge/evidence-protocol.md):
- Format: `E001`, `E002`, ... (3-digit zero-padded)
- Sequential within handoff version
- Never skip, never reuse (even after deletion)
- On merge: continue sequence (existing E001-E015 → new E016+)

**Three-Tier Finding Classification** (knowledge/triage-principles.md § Principle 3):

| Tier | Criteria | Promotion Rule |
|------|----------|----------------|
| **Confirmed Facts** | Direct evidence, no interpretation | Only from logs/stacktraces with source_ref |
| **Bounded Inferences** | Evidence supports but doesn't prove | Must state assumptions explicitly |
| **Open Questions** | Insufficient evidence | State what's missing, why unknown |

**Rule**: When uncertain, DEMOTE to lower tier (never promote narrative to fact without evidence).

**Source Reference Structure** (knowledge/evidence-protocol.md):
```json
{
  "evidence_id": "E001",
  "source_ref": {
    "source_type": "file|url|inline",
    "path": "string",
    "line_start": 1,
    "line_end": 3
  }
}
```

**Evidence Weight Hierarchy** (for conflict resolution):
1. Stacktraces/exceptions with timestamps
2. Structured logs with trace/request IDs
3. Unstructured logs with timestamps
4. Human comments/chat
5. Hearsay

### Schema & Output

**Required Fields** (schemas/handoff.schema.json):
- `schema_version: "1.0"` (constant)
- `case_meta.title`, `case_meta.created_at`, `case_meta.sources` (≥1)
- `context_summary.problem_statement`
- `evidence_inventory` (≥1 item)
- `findings.confirmed_facts`, `.bounded_inferences`, `.open_questions` (arrays, may be empty)
- `handoff_summary.scope`

**Version Bumping**:
- Core schema field changes → bump `schema_version`
- Downstream tools parse version for compatibility

**Output Envelope** (TODOS.md P0.2):
- Main: `handoff.summary.json` (≤120 lines)
- Attachment: `handoff.evidence.json` (full evidence, optional)

### Code Mapping

**Match Type Taxonomy** (workflows/new-triage-handoff.md § Step 6):
- `stacktrace` → confidence: **high**
- `symbol_search` → confidence: **medium**
- `route_mapping` → confidence: **medium**
- `keyword` → confidence: **low**

**Rule**: No code location without `evidence_refs` backing.

## ANTI-PATTERNS (THIS PROJECT)

### CRITICAL SCOPE VIOLATIONS

❌ **Writing patches, confirming root cause, proposing fixes**  
Location: SKILL.md:14  
Reason: Skill narrows scope, doesn't fix. Fix generation is downstream responsibility.

❌ **Promoting narrative to fact without evidence**  
Location: knowledge/triage-principles.md:20-31  
Reason: Human claims = `people_hypotheses`, not `confirmed_facts`. Unverified claims propagate downstream.

❌ **Silently picking one version of conflicting evidence**  
Location: workflows/handoff-refinement.md:62  
Reason: Conflicts are signal. Keep both, document explicitly. Downstream needs to see contradictions.

❌ **Hiding uncertainty or gaps**  
Location: knowledge/triage-principles.md:109-119  
Reason: Hidden uncertainty propagates. Downstream agents trust your confidence levels. Fake certainty kills reliability.

### EVIDENCE PROTOCOL VIOLATIONS

❌ **Vague references** ("from logs", "user mentioned", "somewhere in code")  
Location: knowledge/evidence-protocol.md:139-150  
Reason: References must be followable in <30 seconds. Broken refs make output unusable.

❌ **Missing evidence IDs** (referencing evidence not in inventory)  
Location: knowledge/evidence-protocol.md:139  
Reason: Every `evidence_ref` must exist in `evidence_inventory`. Orphan refs break traceability.

❌ **Reusing evidence IDs** (even after deletion)  
Location: knowledge/evidence-protocol.md:15  
Reason: IDs track provenance across refinements. Reusing creates ambiguity about version references.

### TOOL USAGE VIOLATIONS

❌ **Using deprecated script parameters** (`--start`, `--end`)  
Location: scripts/collect-log-evidence.sh:47,52  
Reason: Use `--event` + `--window-seconds` instead. Deprecated params silently ignored.

❌ **Code mapping without evidence backing**  
Location: workflows/new-triage-handoff.md:131  
Reason: Every `code_mapping` entry needs `evidence_refs`. Speculative locations are noise.

### COMPLETENESS VIOLATIONS

❌ **Silent skipping without inventory entry**  
Location: TODOS.md:159  
Reason: Record `status: skipped` with reason. Silent skips create invisible data loss.

❌ **Omitting open questions when gaps exist**  
Location: knowledge/handoff-schema.md:194  
Reason: `findings.open_questions` required. Empty array when gaps exist = dishonest.

## UNIQUE STYLES

### Deterministic Batching

**Time-Targeted Archive Expansion**:
- Select archives by filename timestamp within `EVENT_TIME±WINDOW_SECONDS`
- Expand only matching archives (not all)
- Apply second-stage mtime filter
- Fail-fast if zero files remain

### Cross-Framework Code Search

**Multi-Language Symbol Resolution** (scripts/search-code-symbols.sh):
- Supports: TS/JS (Express, NestJS), Python (Flask, FastAPI), Java, Go, Rust, C/C++, C#, PHP, Swift, Kotlin
- Detects: function definitions, class definitions, HTTP route handlers
- Route patterns: `@Get('/path')`, `app.post('/path')`, `@route('/path')`

### Conflict Preservation

**Never Silently Overwrite** (workflows/handoff-refinement.md):
- New confirms existing → promote `bounded_inferences` → `confirmed_facts`
- New contradicts → flag conflict, keep both, move to `open_questions`
- New extends → add to respective sections

## COMMANDS

```bash
# Log collection (time-windowed)
./scripts/collect-log-evidence.sh <log_dir> \
  --event "YYYY-MM-DDTHH:MM:SS" \
  --window-seconds 300 \
  --identifiers "trace-id,request-id"

# Cleanup extraction workspace
./scripts/collect-log-evidence.sh <log_dir> --cleanup

# Code symbol search
./scripts/search-code-symbols.sh <repo_dir> \
  --symbols "functionName,ClassName" \
  --stacktrace "file.py:123"

# Route handler resolution
./scripts/search-code-symbols.sh <repo_dir> \
  --routes "/api/users,/api/posts"

# Deploy skill to all agents
./init.sh --all

# Preview deployment (dry-run)
./init.sh --dry-run --all
```

## NOTES

### Dependencies

**Hard Requirements**:
- bash 3.2+
- python3 (for time-window calculations)

**Soft Requirements** (graceful fallback):
- ripgrep (rg) → fallback: grep
- unzip, tar, gzip → for archive extraction
- jq → optional (JSON extraction)

### Test Execution

**No Automated Test Runner**:
- Test cases: `__test__/case_NN.txt` (conversation logs)
- Expected outputs: `__test__/case_NN_output.txt`
- Validation: Manual comparison against `evals/evals.json` expectations
- Schema validation: `schemas/*.schema.json` (JSON Schema draft-07)

### Archive Support

**Supported Formats**: zip, tar, tgz, tar.gz, gz (auto-detected)  
**Unsupported** (TODOS.md P1.5): `.7z.001` (segmented), `.rar`

### Distribution Model

**Skills Deployment**:
- Not npm packages, not git submodules
- Symlink-based: `init.sh` creates links to `~/.agents/skills`, `~/.claude/skills`, `~/.codex/skills`
- Single-source deployment to heterogeneous agents

### Cost Awareness

**Cheap Operations** (do here):
- Summarization, pattern matching, keyword extraction, schema filling

**Expensive Operations** (leave downstream):
- Causal reasoning, code comprehension, fix generation, architectural analysis
