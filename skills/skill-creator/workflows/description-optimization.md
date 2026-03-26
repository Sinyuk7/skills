# Description Optimization Workflow

Use this workflow after the skill itself is working well enough that trigger quality is the next bottleneck.

The `description` field in `SKILL.md` frontmatter is the primary trigger surface for skill invocation.

## Step 1: Create trigger eval queries

Create about 20 realistic queries split between should-trigger and should-not-trigger examples.

Save them as JSON:

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "another prompt", "should_trigger": false}
]
```

Query design rules:

- Make them look like real user requests, not abstract labels.
- Include concrete details such as file names, paths, job context, URLs, or messy phrasing.
- Mix formal and casual language.
- Include edge cases and near-misses.

For should-trigger cases:

- cover multiple phrasings of the same need
- include cases where the user clearly needs the skill without naming it
- include adjacent cases where another skill might plausibly compete

For should-not-trigger cases:

- prefer tricky near-misses over obviously irrelevant prompts
- test ambiguous wording that could fool a naive matcher

## Step 2: Review the eval set with the user

Use `assets/eval_review.html` to let the user edit the eval set.

Fill these placeholders:

- `__EVAL_DATA_PLACEHOLDER__`
- `__SKILL_NAME_PLACEHOLDER__`
- `__SKILL_DESCRIPTION_PLACEHOLDER__`

Write a temporary HTML file, open it for the user, and let them export the edited eval set.

Check the most recent downloaded `eval_set.json` if multiple versions exist.

This review step matters. Poor eval queries lead to poor descriptions.

## Step 3: Run the optimization loop

Tell the user this will take time and that you will monitor it.

Run:

```bash
python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model <model-id-powering-this-session> \
  --max-iterations 5 \
  --verbose
```

Use the model ID from the current session so the trigger test matches the user's actual experience.

While it runs:

- tail progress
- report iteration number
- summarize train and held-out scores

The script handles train/test splitting, repeated trigger measurements, candidate description generation, and final best-description selection.

## Step 4: Apply the result

Take `best_description` from the output, update the skill frontmatter, and show the user:

- before/after description
- resulting scores
- any caveats about overfitting or tradeoffs

## Step 5: Package if useful

If packaging is available and helpful, run:

```bash
python -m scripts.package_skill <path/to/skill-folder>
```

Then point the user to the resulting `.skill` file.

## Triggering Notes

Remember that skills are usually consulted for tasks Claude would benefit from delegating to specialized instructions. Very simple one-step prompts often will not trigger a skill even if the description looks like a match, so the eval set should contain sufficiently substantive requests.
