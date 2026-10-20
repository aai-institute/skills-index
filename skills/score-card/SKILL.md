---
name: score-card
description: Evaluate one artifact (document, slide deck, curriculum, code, skill, ...) once against a metric file (*.metric.yaml) and produce a human-readable score card with per-term scores, evidence, gate results and the biggest levers for improvement. Use when the user asks to "score", "grade", "rate", "review against our standards", "check whether this meets the bar", or wants a score card or approval check for a piece of work. Does not modify the artifact.
---

# score-card

Score an artifact against a metric and report the result. This skill is
read-only: never edit the artifact or the metric.

**Inputs**
- The artifact: a file, a folder or a URL. Ask if it is not clear.
- The metric file: `*.metric.yaml`. If none is given, look in `metrics/`. If there is no metric, offer to create one with `make-it-measurable`.

The format of metrics and scores is described in
`references/metric-format.md`. Read it if you have not
seen it in this session.

## Procedure

### 1. Prepare

- Read the metric. Read all files listed in `references`.
- Get the artifact into a form you can read. Text formats (md, txt, html, tex, code) can be read directly. For `.pptx`, `.docx` or `.pdf`, use the matching document skill if one is available, or extract the text (for example with `markitdown` or `pandoc`). Note the slide or page numbers so that evidence can point to them.

### 2. Measure each term

Score every term independently. Do not let the result of one term influence
another term.

- **computed**: measure exactly as `measure` says. Use a script or command where possible (word counts, test runs, linters) and report the method. Record `raw`. The helper script normalizes the value.
- **checklist**: for each item, decide `true` or `false` and quote the location that justifies the decision. If you are not sure, the answer is `false`.
- **judge**: first collect evidence (quotes or locations) for and against each rubric anchor. Then choose the anchor that fits best. Use a value between two anchors only when the artifact clearly sits between them. Write the evidence before the score, not the other way round.

Rules for judging:

- Judge only what the rubric asks. Do not reward qualities that are not in the metric, and do not punish their absence.
- Use the `context` (audience, purpose) of the metric. "Clear" means clear for that audience.
- Be strict. A score of 1.0 means that nothing in this term could reasonably be improved.
- Write one concrete `suggestion` per term with a score below 1: what exactly to change, and where.

**Independence (recommended for long artifacts or many judge terms):** run
each `judge` term in its own subagent (Agent tool). Give it only the artifact,
the term definition, the metric `context` and the references. Ask it to return
JSON `{"score": ..., "evidence": "...", "suggestion": "..."}`. Run these
subagents in parallel. This keeps judgements independent. The `make-it-better`
skill uses this mode so that the judge never sees why an edit was made.

### 3. Check gates

For each gate, decide pass or fail and give evidence.

### 4. Aggregate

Write the results to `<artifact-stem>.scores.json`, next to the artifact or in
a `scorecards/` folder (see the format reference). Then run the helper script
that ships in this skill's `scripts/` folder:

```bash
uv run <skill-dir>/scripts/metrictool.py aggregate <metric.yaml> <scores.json> --out <artifact-stem>.scorecard.json --markdown
```

Do not compute the total by hand. If the script is not available, compute
`Σ weight · score` and say that you calculated it manually.

### 5. Report

Present the score card. Lead with the verdict:

1. **Total** (two decimals) and **gate status**. If a gate failed, say clearly that the artifact is not acceptable, whatever the total.
2. **Table**: term, weight, score, a one-line reason.
3. **Biggest levers**: the 2–3 terms with the largest `headroom` (`weight · (1 − score)`), each with its concrete suggestion. These are the changes that raise the total most.
4. **Evidence** for low scores, with quotes and locations.
5. A **confidence note** if some terms were hard to judge (for example ambiguous rubric anchors, or content that could not be extracted).

If an `Artifact` tool is available and the user wants something to share (for
example for an approval or a review with the author), publish the score card
as an HTML page as well: total as a large number, a bar per term, gates, and
the levers. Otherwise, write `<artifact-stem>.scorecard.md` next to the JSON.

When the user wants to act on the results, point them to `make-it-better`. If
a score looks wrong to the user, the metric probably needs calibration:
suggest `make-it-measurable` to update it.
