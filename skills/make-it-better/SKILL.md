---
name: make-it-better
description: Iteratively improve an artifact (document, slide deck, curriculum, code, ...) to maximize its score on a metric file (*.metric.yaml), using a measured score -> edit -> re-score loop that keeps only changes which raise the total. Also has a suggest-only mode for reviewers who must not edit someone else's work. Use when the user asks to "improve/optimize/polish this according to my metric/standards", "raise the score", "make this meet our quality bar", or "tell the author what to fix".
---

# make-it-better

Hill-climb an artifact on a metric. Each iteration: find the biggest lever,
make a focused change, re-score with an independent judge, and keep the change
only if the total goes up. The metric is fixed: this skill never changes it.

The format of metrics and scores is described in
`references/metric-format.md`. The scoring procedure is in
`references/scoring.md`. Read both if you have not seen them in this session.

## Inputs

Ask only for what you cannot infer:

- **Artifact** to improve, and the **metric** (default: look in `metrics/`; if there is none, offer `make-it-measurable` first).
- **Mode**:
  - `edit` (default): produce an improved version.
  - `suggest-only`: do not produce a new version. Produce a prioritized list of changes for the author. Use this when the user reviews someone else's work, for example before an approval.
- **Budget**: the maximum number of iterations (default 5). Optionally a target total (for example 0.85).
- **Constraints**: what must not change (for example "keep slide order", "do not touch the code examples", "keep it under 20 slides"). Treat these like gates.

## Setup

Never overwrite the original. Create a working folder next to the artifact:

```
<artifact-stem>.better/
  v0/            # copy of the original
  v1/ ...        # one folder per accepted version
  log.md         # one entry per iteration, accepted or rejected
  v0.scores.json, v0.scorecard.json, ...
```

For a single file, the version folders can be plain files (`v0.md`, `v1.md`).
For `.pptx` or `.docx`, use the matching document skill if one is available to
edit the file. If no skill is available, work on an extracted markdown version
and tell the user that the final changes must be applied in the original tool.

## Loop

**0. Baseline.** Score `v0` with the score-card procedure, using the
independent mode (one subagent per `judge` term). Record the total, the gates
and the headroom per term.

Then repeat until a stop condition holds:

**1. Choose a lever.** Take the term with the largest headroom
`weight · (1 − score)` that you have not just failed on. If a gate fails, fix
the gate first. If the lever needs information that only the user has (for
example missing learning objectives, or facts you cannot verify), do not
invent it. Add it to the "needs the author" list and choose the next lever.

**2. Plan one focused change.** Base it on the judge's evidence and
suggestion. Change only what this term needs. Before you edit, check which
other terms the change could hurt (for example, "add examples" can hurt "text
density"). Prefer changes that help the lever without hurting the other
terms.

**3. Apply the change** to a copy of the current best version, as the
candidate `v<n>`.

**4. Re-score the candidate**, with all terms and all gates. The judges must
be blind: give them only the candidate, the metric and the references. Never
give them the plan, the diff or the previous score. Deterministic terms
(`computed`) can be re-measured directly.

**5. Accept or reject.** Accept the candidate if all of these hold:
- The total is higher than the current best by more than the noise margin (default 0.02. Judge scores vary between runs).
- No gate fails and no constraint is broken.
- No single term dropped by more than 0.25. A larger drop means that the change traded quality for score. Reject it even if the total went up.

When the result is borderline (the gain is less than 2× the noise margin),
re-score the changed judge terms once more and use the mean.

**6. Log** the iteration in `log.md`: the lever, the change (2–3 lines), the
total before → after, the term deltas, and the decision.

**Stop** when the budget is used up, the target is reached, all gates pass and
headroom is small everywhere, or two different levers in a row were rejected
(a plateau).

## Guard against gaming the metric

The metric is a proxy for what the user wants. If an edit raises the score but
the user would clearly not want it (for example deleting a needed section to
reduce length, adding filler to tick checklist items, or keyword stuffing),
do not make it. When you notice that the metric rewards such a change, stop
optimizing that term. Report it as a **metric gap** and suggest fixing it with
`make-it-measurable`. Never change content in ways that make it factually
wrong, and never fabricate facts, sources or numbers to satisfy a term.

## suggest-only mode

Run the same loop, but stop after you verify each change. For each of the top
levers, draft the concrete change and score the hypothetical result, so that
the expected gain is measured and not guessed. Do not create a final version
for the author. Deliver:

1. The current score card (total, gates, table).
2. A prioritized list of requested changes: what to change, where, why (the term and the evidence) and the expected score gain. Put gate failures first, marked as blocking.
3. Items that need the author's knowledge.

Write the list so that it can go to the author directly (for example
`<artifact-stem>.review.md`).

## Final report (edit mode)

- Total and gates: **before → after**, plus a per-term table with deltas.
- The accepted changes, one line each, with their term gains. Mention the rejected attempts briefly.
- The location of the best version and a diff or summary against the original.
- "Needs the author": open items that you could not fix without information.
- Any metric gaps you found.

Do not replace the original file unless the user asks for it.
