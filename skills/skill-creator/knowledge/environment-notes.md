# Environment Notes

Use this note when the surrounding environment changes what parts of the workflow are practical.

## Claude.ai

Claude.ai does not have subagents, so adapt the workflow:

- run test cases one at a time
- skip baseline comparisons
- follow the skill yourself for sanity checks
- focus on qualitative review instead of quantitative benchmarking

If a browser viewer is not practical:

- show outputs directly in the conversation
- save inspectable files to disk when needed
- gather feedback inline

Description optimization that relies on `claude -p` should be skipped in Claude.ai.

Blind comparison should also be skipped because it depends on subagents.

Packaging still works anywhere with Python and a writable filesystem.

When updating an existing installed skill:

- preserve the original skill name
- copy the skill to a writable location before editing if the installed copy is read-only
- stage packaging work in `/tmp/` if direct writes are unreliable

## Cowork or other headless environments

Cowork still supports subagents, so the main evaluation workflow works.

Adaptations:

- use static viewer output via `--static <output_path>`
- expect feedback to arrive as a downloaded `feedback.json`
- read the downloaded feedback back into the workspace

Important reminder:

- generate the eval viewer before doing your own qualitative judgment so the human can review outputs quickly

Description optimization should work if `claude -p` is available.

## Claude Code

Claude Code supports the full workflow:

- subagents
- benchmark aggregation
- live or static viewer generation
- packaging
- description optimization
