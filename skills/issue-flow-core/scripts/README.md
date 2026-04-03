# scripts

Planned script contracts:

- `bootstrap-runtime-core.sh`
- `init-case.sh`
- `build-source-manifest.sh`
- `build-inventory.sh`
- `collect-log-window.sh`
- `collect-media-evidence.sh`
- `build-code-map.sh`
- `package-evidence.sh`

This directory is intentionally skeletal in the first pass. Script behavior will
be added after the workflow and artifact contracts are finalized.

---

## bootstrap-runtime-core.sh

**Purpose**: Initialize `<repo-root>/.issue-flow-core/` from the design-time
source in the skills repo.

**Usage**:

```bash
bootstrap-runtime-core.sh [--force]
```

**Behavior**:

1. Resolve the current git repository root
2. Check if `<repo-root>/.issue-flow-core/` exists
   - If exists and `--force` not provided: exit 0 (idempotent no-op)
   - If exists and `--force` provided: remove and recreate
3. Create `<repo-root>/.issue-flow-core/`
4. Copy `templates/` from design-time source
5. Copy `scripts/` from design-time source (including this script)
6. Exit 0 on success, non-zero on failure

**What gets copied**:

- `templates/` → `<repo-root>/.issue-flow-core/templates/`
- `scripts/` → `<repo-root>/.issue-flow-core/scripts/`

**What does NOT get copied**:

- `workflows/` (design-time reference only)
- `knowledge/` (design-time reference only)
- `examples/` (design-time reference only)
- `PRD.md` (design-time reference only)
- `README.md` (design-time reference only)

**Exit codes**:

- `0`: success (including idempotent skip)
- `1`: not inside a git repository
- `2`: failed to create directory or copy files

**Environment**:

- Requires `git` to resolve repository root
- No other external dependencies
