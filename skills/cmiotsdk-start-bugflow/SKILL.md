---
name: cmiotsdk-start-bugflow
description: Start a cmiotsdk bugfix workflow. Create or reuse bugfix/<TICKET-ID> from origin/develop, then optionally hand off the same payload to /issue-collect.
disable-model-invocation: true
argument-hint: "[TICKET-ID] [optional context, logs, screenshots]"
allowed-tools: Bash Read Grep
---

# cmiotsdk Start Bugflow

Repo-aware wrapper that bootstraps a `bugfix/<TICKET-ID>` branch in `cmiotsdk`, then delegates evidence registration to `/issue-collect`.

**This skill does NOT replace `/issue-collect`.** It is a thin orchestration layer:
- Step A: deterministic git bootstrap (via script)
- Step B: transparent handoff to `/issue-collect` (with same payload)

## Input

Compatible with `/issue-collect`. The user provides everything once:

| Field | Required | Description |
|-------|----------|-------------|
| `ticket_id` | Yes | e.g. `OMMUSIC-3397323` |
| `summary` | No | One-line issue description |
| `user_context` | No | User's original issue description |
| `materials` | No | Logs, screenshots, archives, notes — same as `/issue-collect` accepts |
| `code_references` | No | Paths the user identifies as relevant |
| `auto_enter_collect` | No | Default `true`. Set `false` to only create the branch. |

Hold on to any user-provided materials — they will be forwarded to `/issue-collect` in the handoff step.

## Step 1: Validate Repository

Confirm the current working directory or user-specified path is the `cmiotsdk` repository.

The script (`start-bugfix.sh`) performs the authoritative repo identity check using **remote URL matching** (not just directory basename). This skill delegates validation entirely to the script.

If the script reports the repo is not `cmiotsdk` → **STOP**: "This skill is for cmiotsdk only. Use `/issue-collect` directly for other repos."

## Step 2: Validate Ticket ID

Pattern: `^[A-Z]+-[0-9]+$` (e.g. `OMMUSIC-3397323`)

- Missing → **ASK** user.
- Invalid format → **STOP** with expected pattern.

## Step 3: Git Bootstrap

Run the deterministic script:

```bash
# SKILL_DIR is the directory containing this SKILL.md
bash "$SKILL_DIR/scripts/start-bugfix.sh" "<TICKET-ID>"
```

The script lives at `skills/cmiotsdk-start-bugflow/scripts/start-bugfix.sh` — it is a skill supporting file, not a project file.

Script behavior (see script source for full details):

1. Repo identity check via `git remote get-url origin` (not just basename)
2. `git fetch origin`
3. Abort if working tree is dirty (uncommitted changes)
4. Abort if currently on a **different** `bugfix/*` branch (explicit conflict)
5. If `bugfix/<TICKET-ID>` exists locally → switch to it (non-destructive)
6. Otherwise → `git checkout -b bugfix/<TICKET-ID> origin/develop`
7. Abort if `origin/develop` does not exist
8. Abort if in detached HEAD state

**Safety guarantees:**
- Never `reset --hard`
- Never auto-stash
- Never modify existing branch history
- All destructive behaviors require explicit flags (none exist today)

Verify after script:

```bash
git -C "$REPO_ROOT" branch --show-current
# Expected: bugfix/<TICKET-ID>
```

## Step 4: Handoff to /issue-collect

### Payload mapping (wrapper → collector contract)

| Wrapper field | → | `/issue-collect` usage |
|---------------|---|------------------------|
| `ticket_id` | → | `case_id` (highest priority, overrides slug) |
| `summary` | → | `case.yaml` summary field |
| `user_context` | → | `case.yaml` user_context field |
| `materials` | → | File paths to register as `evidence_sources` |
| `code_references` | → | Record in `case.yaml` only (not copied) |

**`ticket_id` as `case_id` is authoritative.** `/issue-collect`'s own "bug tracker ID > slug > date suffix" priority rule naturally handles this — the ticket ID is a bug tracker ID and will be selected first. No special override needed.

**`/issue-collect` resolves `PROJECT_ROOT` on its own.** This wrapper does NOT skip collect's Step 1. Each skill remains independently runnable.

### If `auto_enter_collect` is `true` (default)

Report branch status briefly, then **immediately proceed** to `/issue-collect`:

```
✅ Branch bugfix/<TICKET-ID> ready (from origin/develop).
   Entering /issue-collect...
```

`/issue-collect` takes over from its own Step 1. This skill is done.

### If `auto_enter_collect` is `false`

Report and stop:

```
✅ Branch bugfix/<TICKET-ID> ready (from origin/develop).

   Repository: cmiotsdk
   Branch:     bugfix/<TICKET-ID>
   Base:       origin/develop

   When ready, run /issue-collect to register evidence references.
```

## Rules

- **DO NOT** create case.yaml, collect.md, or any raw-evidence directories — that is `/issue-collect`'s job
- **DO NOT** read, analyze, or modify source code
- **DO NOT** duplicate any `/issue-collect` file-writing logic
- **DO NOT** run on repositories other than `cmiotsdk`
- **DO NOT** skip `/issue-collect`'s own PROJECT_ROOT resolution
- **DO** preserve all user-provided materials for transparent forwarding
- **DO** let the script handle all git safety checks and repo identity validation

## Done When

- [ ] Repository confirmed as `cmiotsdk` (by script)
- [ ] Branch `bugfix/<TICKET-ID>` active
- [ ] If `auto_enter_collect=true`: `/issue-collect` invoked with full payload
- [ ] If `auto_enter_collect=false`: user informed of next step

---

## Example: Happy Path — OMMUSIC-3397323

### User invokes

```
/cmiotsdk-start-bugflow OMMUSIC-3397323

播放过程中切换音频焦点后无法恢复播放。
日志见 /tmp/audio-focus-bug/player.log
截图见 /tmp/audio-focus-bug/screenshot.png
可能相关代码: biz/player/src/.../CarAudioFocusManager.kt
```

### Step 1–2 — Validation

```
ticket_id: OMMUSIC-3397323 ✓ (matches ^[A-Z]+-[0-9]+$)
```

### Step 3 — Git bootstrap

```bash
$ bash script/start-bugfix.sh OMMUSIC-3397323

🔄 Fetching origin...
🌿 Creating branch 'bugfix/OMMUSIC-3397323' from origin/develop...

✅ Bugfix branch ready.

   Repository: cmiotsdk
   Branch:     bugfix/OMMUSIC-3397323
   Base:       origin/develop (a1b2c3d)
```

### Step 4 — Auto handoff (auto_enter_collect=true)

```
✅ Branch bugfix/OMMUSIC-3397323 ready (from origin/develop).
   Entering /issue-collect...
```

Payload forwarded to `/issue-collect`:

```yaml
case_id: OMMUSIC-3397323
summary: "播放过程中切换音频焦点后无法恢复播放"
user_context: |
  播放过程中切换音频焦点后无法恢复播放。
materials:
  - /tmp/audio-focus-bug/player.log
  - /tmp/audio-focus-bug/screenshot.png
code_references:
  - biz/player/src/.../CarAudioFocusManager.kt
```

`/issue-collect` takes over → creates `.issue-flow/cases/OMMUSIC-3397323/`, registers evidence references, writes `case.yaml` + `collect.md`.

### Final output to user

```
✅ Bugfix workflow started for OMMUSIC-3397323.

   Branch:  bugfix/OMMUSIC-3397323 (from origin/develop)
   Case:    .issue-flow/cases/OMMUSIC-3397323/
   Status:  collected

   Evidence refs:
   - /tmp/audio-focus-bug/player.log
   - /tmp/audio-focus-bug/screenshot.png
   - Code ref: biz/player/src/.../CarAudioFocusManager.kt

   Next: run /issue-investigate to analyze evidence and find root cause.
```

---

## Example: Failure Cases

### Dirty working tree

```
/cmiotsdk-start-bugflow OMMUSIC-3397323
```

```
❌ You have uncommitted changes. Please commit or stash them first.
   git stash        # to stash changes
   git stash pop    # to restore later

Bugfix branch was NOT created.
```

### Wrong repository

```
/cmiotsdk-start-bugflow OMMUSIC-3397323
```

```
❌ This skill is for cmiotsdk only.
   Current repo remote: git@github.com:user/other-project.git
   Use /issue-collect directly for other repos.
```

### Invalid ticket ID format

```
/cmiotsdk-start-bugflow fix-audio-bug
```

```
❌ Invalid ticket ID format: 'fix-audio-bug'.
   Expected pattern: PROJ-12345 (e.g. OMMUSIC-3397323)
```

### Already on a different bugfix branch

```
/cmiotsdk-start-bugflow OMMUSIC-3397323
```

```
❌ You are currently on branch 'bugfix/OMMUSIC-1111111'.
   Please finish or switch off that branch before starting a new bugfix.
   git checkout develop    # to leave current bugfix
```

### Branch already exists (non-destructive reuse)

```
/cmiotsdk-start-bugflow OMMUSIC-3397323
```

```
⚠️  Branch 'bugfix/OMMUSIC-3397323' already exists locally.
   Switching to it...

✅ Now on existing branch: bugfix/OMMUSIC-3397323
   Entering /issue-collect...
```
