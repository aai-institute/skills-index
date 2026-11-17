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

- **The user is the authority on quality. You are the authority on measurability.** Propose concrete drafts the user can react to, then stop and let them react. A draft is a message, not a file.
- **Nothing is final until the user confirms it.** Do not write the metric file until the user has confirmed the terms, the gates and the weights (checkpoint before step 6). This also applies when the user is in a hurry: compress the interview, do not skip it.
- **Few, independent terms.** 3–8 terms are usually enough. Two terms that measure the same thing count it twice. Merge them.
- **Observable, not adjectival.** "Every new concept has an example" can be checked. "Very clear" cannot.
- **Cheapest reliable measurement wins.** Use `computed` before `checklist`, and `checklist` before `judge`. Use `computed` only if a script can measure it without judgement.
- **Gates only with consent.** A gate rejects an artifact no matter how good the rest is. Only the user can decide that. Never add a gate the user has not confirmed.
- **The metric will be optimized against.** Whatever it fails to penalize, an optimizer will exploit (Goodhart's law). Look for those gaps on purpose.
- **Stay inside the project.** Do not read files outside the project, fetch web pages, or change skill files unless the user agrees.

## Workflow

Keep the interview short: usually 3–5 rounds. Use `AskUserQuestion` for
choices with clear options. Use plain conversation for open questions. Tell
the user where you are ("Step 2 of 6: turning your criteria into terms").

**User in a hurry?** Only if the user says so (for example "quick please"),
keep the interview to two messages:

1. **Questions.** Send one short message with a draft term table (at most 2
   terms of your own, marked "proposed by me") and exactly three questions:
   (a) "What do you fix or send back most often?", (b) "Is there anything that
   makes you reject one, or limits its score, no matter how good the rest is?",
   (c) "Rank the terms you want to keep, most important first, in one line."
2. **Final confirmation** (step 5) with weights derived from the ranking.

If an answer is missing or unclear, ask only that question again, in one
line. Never fill a gap with your own choice: no criteria, ranking or weights
the user did not give. "Keep them all" does not confirm a term you proposed;
ask which one to keep. Without time pressure, use the normal workflow.

### 1. Scope

Find out, or infer from the conversation and the files present, and confirm
with the user:

- **Artifact type**: what is scored (e.g. "course slide decks", "Python modules", "Claude skills").
- **One artifact or a family?** If the metric must work for many artifacts (for example all course decks of a program), do not tie terms to one of them: no fixed slide numbers, no items for one course's objectives. Write rules that apply to each artifact ("each objective stated at the start is practiced"; see the "each item" pattern in `references/metric-format.md`).
- **Audience and purpose** of these artifacts. This goes into `context`.
- **Whose standards** these are (the `owner`). Ask for the name. Do not take it from the account or the environment: the person who runs the skill is often not the owner.
- **How the metric will be used**: to improve own work, to review the work of others (approval), or to standardize content from many sources.
- **Examples**: ask for 1–3 artifacts the user considers good and, if possible, 1 that is bad. Examples are the best source of criteria and are needed for calibration.
- **Reference material** that judges need, for example learning objectives, a style guide or a brand guide. Record these as `references`, with paths relative to the metric file.

### 2. Elicit criteria

Collect raw criteria in the user's own words **before** you draft terms.
Examples only show some criteria: a user can care about things that all the
examples happen to get right or wrong. So ask the user first, even if examples
exist. Always ask at least these two:

- "When you reject or send back a <artifact>, what is usually the reason? What do you fix first?"
- "Think of the best <artifact> you have seen. What made it good?"

If examples exist, read them and also ask "What makes A better than B?", and
propose criteria that you notice in the examples. Users often name criteria a
few at a time. When an answer is short, ask "What else do you check for?"
once more. If the user names a criterion in one or two words ("clear ask"),
ask once what it must contain and where ("What must a clear ask say, and where
should it be?").

Users sometimes change their mind ("forget what I said about SEO"). The latest
statement wins: remove or change the affected terms and weights, and say what
you removed.

Always ask this question, also in the fast path: **"Is there anything that
makes you reject a <artifact> no matter how good the rest is?"** If there is
a rejected example, also ask why it was rejected. The answers are the
candidate gates.

Also propose 2–4 criteria that are common for this artifact type and that the
user has not mentioned. Let the user accept or reject each of them. Do not
add criteria that the user has not accepted.

### 3. Make each criterion measurable

For each criterion, decide the kind and draft the definition (see
`references/metric-format.md`):

- **computed**: a number that a script can measure deterministically (word counts, slide count, readability index, test pass rate). Define `measure` exactly. Pick a `normalize` mapping and ask the user for the values: "What is ideal? When is it clearly too much (or too little)?" Values you read off the examples are suggestions to confirm, not defaults. Add a lower bound only if the user wants one.
- **checklist**: a list of things that must be present or true (learning objectives covered, required sections present). Each item is a yes/no question.
- **judge**: everything subtle. Write a rubric with anchored levels (at least 0, 0.5, 1; five levels for subtle terms). Each anchor describes what a judge can *see* in the artifact. Where possible, take the anchors from the user's examples. Keep the bar where the user puts it: if the user wants "at least one number", do not require a number for every claim.

Then check the whole set:

- **Overlap**: do two terms reward the same thing? Merge them or make the boundary explicit. After a merge, check the merged rubric: if an anchor now describes two independent qualities, split the term again.
- **Gates and caps**: for each candidate from step 2, ask "Should failing this reject the artifact, limit its total, or only cost points?" Only a confirmed "reject" becomes a gate. "Without a recommendation it can't score above 0.5" becomes a cap (see `references/metric-format.md`). A gate or cap must be checkable from the artifact and its references alone. If the user says there are no deal-breakers, write no gates.
- **Limits per unit**: if the user's limit applies to every unit ("no slide over 90 words"), do not measure a mean: one bad slide hides among good ones. Measure the share of units within the limit, or the worst unit (see `references/metric-format.md`).
- **Gaming**: ask yourself and the user: "If an artifact maxed out every term, would you be happy with it? How could someone score high and still produce bad work?" Typical exploits: delete content to improve brevity, add filler to improve coverage, keyword-stuff to pass checklists, add trivial activities ("Any questions?") to count as interaction, replace acronyms with other jargon, invent sources or numbers to satisfy evidence terms. For each exploit you name, either change a term so that the exploit no longer pays, or tell the user that it stays open and why. Never just list exploits.

Show the draft terms as a compact table: id, kind, one-line definition, and
the user's own words that the term comes from (or "proposed by me"). Next to
every threshold and every 1.0 anchor, show what the user said, so that a bar
higher than the user's is visible. Then show the candidate gates and ask:
"Is anything missing, and is any bar stricter than you want?"

### 4. Weights

Weights express trade-offs, so get them from the user. Do not invent them.
Offer one of these methods:

- **Allocate 100 points** across the terms. This is the fastest method.
- **Pairwise**: "If you could improve only one of A and B, which one?" Repeat for close calls, then derive weights.
- **Start from a proposal**: suggest weights with a one-line reason each, and let the user adjust them.

Prefer methods where the user states the numbers or the order. If the user
only approves your proposal ("fine", "looks good"), ask them to rank the two
or three heaviest terms before you continue.

**Equal weights or contradictions:** equal weights are almost never true.
If the user says "everything is equally important", allocates equal points,
or states priorities that conflict with each other or with earlier answers,
ask 2–3 pairwise questions before you set the weights. Do this every time,
also in a hurry. Name the conflict: "Earlier you said length matters most,
but you rejected the last summary for missing evidence. If you could improve
only one, which one?"

**Points that do not add up:** if an allocation does not sum to 100, do not
rescale silently. First ask: "You left N points unassigned. Is there
something you care about that none of these terms captures?"

Normalize the weights so they sum to exactly 1 (round to 2–3 decimals and put
the rounding residue on the largest term). Show the final weights and say in
one sentence what they imply, for example "Coverage counts more than clarity
and density together."

**Checkpoint.** Before step 5, the user must have agreed to the term table,
the gates and caps (or "none") and the weights. If something is still open,
ask. Do not write the metric file before the confirmation in step 5.

### 5. Calibrate and confirm (one message)

Send **one** message that the user can confirm in one reply. It contains:

- **The complete terms as they will be written**: each rubric anchor, checklist item, `measure` and threshold, with the user's words next to them. Not only the summary table: the user confirms what they saw.
- **Gates and caps**, and the **weights** with their one-sentence trade-off.
- **Calibration**, if examples exist: score them with the draft metric (follow the scoring procedure in `references/scoring.md`, with short evidence) and show the totals and the term scores.

Then ask: "Does the ranking of the examples match your judgement? Does any
term score look wrong? Shall I write it like this?" Do not declare that the
ranking matches. Let the user say it.

If something does not match, find the cause: a vague rubric anchor, a missing
criterion, or a wrong weight. Show the fix and the new scores in one message
and ask again. Anything you change after the user confirmed needs a new
confirmation. Before writing, check that every counter-measure you told the
user about is actually in the file. If you tuned thresholds on the same
examples, say so: the calibration then shows consistency, not generalization.

**Only good examples?** Still score them. A known-good artifact that scores
low on a term shows a rubric that is too strict or unclear.

**No examples?** Offer two options as a real question and let the user
choose: (a) mark the metric as uncalibrated and calibrate it on the first
real artifact, or (b) write 2–3 short synthetic artifacts and let the user
rank them. Write them so that every term, including each threshold, is met in
one artifact and clearly missed in another. Do not look for examples outside
the project without asking.

### 6. Write and validate

1. Write the file. The default location is `metrics/<name>.metric.yaml` in the current project, unless the user wants another location. Set `version: 1`, or increment the version if you update an existing metric.
2. Validate it. The helper script ships in this skill's `scripts/` folder. When this skill loads, its text starts with a line `Base directory for this skill: <dir>`. The script is at `<dir>/scripts/metrictool.py`. Build the absolute path from that line, not from the current directory:
   ```bash
   uv run "<dir>/scripts/metrictool.py" validate metrics/<name>.metric.yaml
   ```
   If `uv` is not available, use `python3` with PyYAML installed. Fix all errors and warnings. Never say the metric is valid unless you ran the validator and it printed `OK`.
3. End with this summary:
   - **File**: the path.
   - **Terms**: id, kind and weight for each, plus the one-sentence trade-off.
   - **Gates and caps**: each gate and cap, or "none".
   - **Calibration**: calibrated on which examples, or "uncalibrated".
   - **Next step**: for example "Run `/score-card` on a deck, or `/make-it-better` to optimize one."

## Updating an existing metric

If the user brings an existing metric (for example "the score-card said 0.9,
but this deck is bad"), treat it as a calibration failure:

1. **Diagnose with the user first.** Ask what is wrong with the artifact. Confirm which term should have caught it, and how the artifact should score instead. Ask whether the metric is used for one artifact or a family. Do not edit the metric before this.
2. **Make the smallest change that fixes it.** Usually this means tightening one rubric, checklist item or `measure`. Apply the fix to every term that rewards the same problem (for example both "objectives practiced" and "activation"). Keep the weights, unless the user agrees to change them. If you change a weight, say which trade-off changed.
3. **Keep the scope.** If the metric is used for many artifacts, do not make it more specific to the one in front of you. If it already has items tied to one artifact (fixed slide numbers, one course's objectives), point them out and propose a general rule (see the "each item" pattern in `references/metric-format.md`).
4. **Check the changed terms for gaming.** For each changed term, ask the gaming question from step 3: how could an artifact max out the new definition and still be bad? Close each exploit you find, or tell the user that it stays open and why.
5. **Show the changed terms in full** (every anchor, item and threshold) and get confirmation before you write them.
6. Increment `version` once per update session, re-validate, and re-score the problem artifact to show the new result.
7. End with the summary from step 6.3.
