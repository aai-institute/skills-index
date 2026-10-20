---
name: make-it-measurable
description: Interview the user to turn their notion of quality for a kind of work (slide decks, documents, curricula, code, skills, emails, ...) into an explicit, weighted metric file (a reward function) that other skills can score and optimize against. Use when the user wants to "define quality criteria", "make my standards measurable", "build a rubric", "create a metric/scoring function", "formalize how I review X", or before running score-card or make-it-better without an existing metric.
---

# make-it-measurable

Turn the user's preferences into a metric file: a convex combination of
weighted terms, each scored in [0, 1], with weights that sum to 1. The output
is a `*.metric.yaml` file that `score-card`, `make-it-better` and `skillopt`
consume. This skill only builds the metric. It does not score or change any
artifact, except for the short calibration in step 5.

Read `references/metric-format.md` before you write the file. It defines the
schema, the three term kinds (`judge`, `computed`, `checklist`) and gates.

## Principles

- **The user is the authority on quality. You are the authority on measurability.** Propose concrete drafts the user can react to. Do not ask open questions and then wait.
- **Few, independent terms.** 3–8 terms are usually enough. Two terms that measure the same thing count it twice. Merge them.
- **Observable, not adjectival.** "Every new concept has an example" can be checked. "Very clear" cannot.
- **Cheapest reliable measurement wins.** Use `computed` before `checklist`, and `checklist` before `judge`.
- **Hard requirements are gates, not terms.** If the user says "no amount of quality makes up for X", make X a gate.
- **The metric will be optimized against.** Whatever it fails to penalize, an optimizer will exploit (Goodhart's law). Look for those gaps on purpose.

## Workflow

Keep the interview short: usually 3–5 rounds. Use `AskUserQuestion` for
choices with clear options. Use plain conversation for open questions. Tell
the user where you are ("Step 2 of 6: turning your criteria into terms").

### 1. Scope

Find out, or infer from the conversation and the files present:

- **Artifact type**: what is scored (e.g. "course slide decks", "Python modules", "Claude skills").
- **Audience and purpose** of these artifacts. This goes into `context`.
- **Whose standards** these are, and how the metric will be used: to improve own work, to review the work of others (approval), or to standardize content from many sources.
- **Examples**: ask for 1–3 artifacts the user considers good and, if possible, 1 that is bad. Examples are the best source of criteria and are needed for calibration.
- **Reference material** that judges need, for example learning objectives, a style guide or a brand guide. Record these as `references`.

### 2. Elicit criteria

Collect raw criteria in the user's own words. Useful prompts:

- "Think of the best <artifact> you have seen. What made it good?"
- "When you reject or send back a <artifact>, what is usually the reason?"
- "What do you fix first when you review someone else's <artifact>?"
- If examples exist: read them, then ask "What makes A better than B?" Also propose criteria that you notice in the examples.

Also propose 2–4 criteria that are common for this artifact type and that the
user has not mentioned. Let the user accept or reject them.

### 3. Make each criterion measurable

For each criterion, decide the kind and draft the definition (see
`references/metric-format.md`):

- **computed**: a number that can be measured deterministically (word counts, slide count, readability index, test pass rate). Define `measure` exactly. Pick a `normalize` mapping and ask the user for the ideal values ("How many words per slide is ideal? When is it clearly too much?").
- **checklist**: a list of things that must be present or true (learning objectives covered, required sections present). Each item is a yes/no question.
- **judge**: everything subtle. Write a rubric with anchored levels (at least 0, 0.5, 1; five levels for subtle terms). Each anchor describes what a judge can *see* in the artifact. Where possible, take the anchors from the user's examples.

Then check the whole set:

- **Overlap**: do two terms reward the same thing? Merge them or make the boundary explicit.
- **Gates**: which criteria are non-negotiable? Move them to `gates`.
- **Gaming**: ask yourself and the user: "If an artifact maxed out every term, would you be happy with it? How could someone score high and still produce bad work?" Typical exploits: delete content to improve brevity, add filler to improve coverage, keyword-stuff to pass checklists. Add a counter-term or a gate, or tighten a rubric, for each realistic exploit.

Show the draft terms as a compact table (id, kind, one-line definition) and
ask for corrections before you continue.

### 4. Weights

Weights express trade-offs, so get them from the user. Do not invent them.
Offer one of these methods:

- **Allocate 100 points** across the terms. This is the fastest method.
- **Pairwise**: "If you could improve only one of A and B, which one?" Repeat for close calls, then derive weights.
- **Start from a proposal**: suggest weights with a one-line reason each, and let the user adjust them.

Normalize the weights so they sum to exactly 1 (round to 2–3 decimals and put
the rounding residue on the largest term). Show the final weights and say in
one sentence what they imply, for example "Coverage counts more than clarity
and density together."

### 5. Calibrate (strongly recommended)

If example artifacts exist, score them quickly with the draft metric. Follow
the scoring procedure in `references/scoring.md`, but give only short evidence.
Then ask:

- Does the **ranking** of the examples match your judgement?
- Does any **single term score** look wrong?

If something does not match, find the cause: a vague rubric anchor, a missing
criterion, or a wrong weight. Fix it and re-score. One or two calibration
rounds are usually enough. If there are no examples, say that the metric is
uncalibrated and suggest calibrating it on the first real artifact.

### 6. Write and validate

1. Write the file. The default location is `metrics/<name>.metric.yaml` in the current project, unless the user wants another location. Set `version: 1`, or increment the version if you update an existing metric.
2. Validate it with the helper script that ships in this skill's `scripts/` folder:
   ```bash
   uv run <skill-dir>/scripts/metrictool.py validate metrics/<name>.metric.yaml
   ```
   If `uv` is not available, use `python3` with PyYAML installed. Fix all errors.
3. Give the user a short summary: the file path, the terms with their weights, the gates, the calibration status, and the next step, for example "Run `/score-card` on a deck, or `/make-it-better` to optimize one."

## Updating an existing metric

If the user brings an existing metric (for example "the score-card said 0.9,
but this deck is bad"), treat it as a calibration failure. Find out which
term should have caught the problem. Then tighten that term's rubric or add a
term, re-weight, increment `version`, and re-validate. Do not silently change
weights. Tell the user which trade-off changed.
