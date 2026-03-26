# Evaluation Loop Workflow

Use this workflow when the user already has a draft skill or wants to validate and improve one.

This is one continuous sequence. Do not stop after launching runs and forget the review loop.

Do not use `/skill-test` or another testing skill for this process.

## Step 1: Prepare the workspace

Put results in `<skill-name>-workspace/` as a sibling to the skill directory.

Organize by iteration:

- `iteration-1/`
- `iteration-2/`
- one directory per eval inside each iteration

Do not create everything up front. Create directories as you go.

If you are improving an existing skill and need a baseline, snapshot the old version before editing.

## Step 2: Launch all runs in the same turn

For each eval prompt, launch both the evaluated version and its baseline together so they finish around the same time.

With-skill run:

```text
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input files: <eval files or "none">
- Save outputs to: <workspace>/iteration-<N>/eval-<ID>/with_skill/outputs/
- Outputs to save: <user-visible artifacts that matter>
```

Baseline choice:

- Creating a new skill: run without any skill and save to `without_skill/outputs/`.
- Improving an existing skill: run the old version from a snapshot and save to `old_skill/outputs/`.

For each eval, create `eval_metadata.json` with a descriptive eval name, not just `eval-0`.

Before writing metadata or other evaluation JSON, load `references/schemas.md`.

## Step 3: While runs execute, draft assertions

Do useful work while the runs are in progress.

- Draft quantitative assertions if they do not exist yet.
- If assertions already exist, review whether they are still good.
- Explain to the user what the assertions check and what they will see in the viewer.

Good assertions are:

- objectively verifiable
- easy to understand at a glance
- discriminating enough to catch real differences

Do not force quantitative assertions onto purely subjective output quality.

Update `eval_metadata.json` and `evals/evals.json` once assertions are ready.

## Step 4: Capture timing data immediately

When each run finishes, capture the completion notification data right away.

Save `total_tokens` and `duration_ms` to `timing.json` in the corresponding run directory. This data is not recoverable later.

## Step 5: Grade the outputs

When all runs are done, load `agents/grader.md`.

Grade each run and save `grading.json`.

The `expectations` array must use these exact field names:

- `text`
- `passed`
- `evidence`

If an assertion can be checked programmatically, write and run a script instead of grading by hand.

## Step 6: Aggregate the benchmark

Run:

```bash
python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
```

This should produce `benchmark.json` and `benchmark.md`.

Put each with-skill result before its baseline counterpart in the output ordering.

## Step 7: Do an analyst pass

Load `agents/analyzer.md` and look for patterns that summary stats can hide:

- assertions that always pass
- high-variance evals
- time or token tradeoffs
- signs of flaky grading or weak eval design

## Step 8: Launch the eval viewer

Use the bundled viewer generator. Do not build custom HTML for this.

```bash
nohup python <skill-creator-path>/eval-viewer/generate_review.py \
  <workspace>/iteration-N \
  --skill-name "<skill-name>" \
  --benchmark <workspace>/iteration-N/benchmark.json \
  > /dev/null 2>&1 &
```

For iteration 2 and later, also pass `--previous-workspace <workspace>/iteration-<N-1>`.

Headless or Cowork environments:

- use `--static <output_path>` instead of a live server
- expect `feedback.json` to be downloaded by the user
- copy the downloaded feedback back into the workspace before the next iteration

Tell the user what they will see:

- an `Outputs` tab for qualitative review
- a `Benchmark` tab for quantitative comparison

## Step 9: Read feedback and iterate

When the user is done, read `feedback.json`.

Empty feedback means the user likely accepted that case.

Focus revisions on the runs with specific complaints, then load `knowledge/improvement-guide.md` and iterate:

1. improve the skill
2. rerun the evals into a new iteration
3. reopen the viewer with previous-workspace attached
4. collect feedback again

Stop when:

- the user is happy
- feedback is effectively empty
- additional changes are not materially improving results
