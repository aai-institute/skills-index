# Scoring procedure

How to score one artifact against a metric. This is the procedure of the
`score-card` skill, copied here so that this skill works on its own. The
metric and scores formats are in `metric-format.md`, next to this file.
Never edit the artifact or the metric while you score.

## 1. Prepare

- Read the metric. Read all files listed in `references`.
- Get the artifact into a form you can read. Text formats (md, txt, html, tex, code) can be read directly. For `.pptx`, `.docx` or `.pdf`, use the matching document skill if one is available, or extract the text (for example with `markitdown` or `pandoc`). Note the slide or page numbers so that evidence can point to them.

## 2. Measure each term

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

**Independent mode (recommended for long artifacts or many judge terms):** run
each `judge` term in its own subagent (Agent tool). Give it only the artifact,
the term definition, the metric `context` and the references. Ask it to return
JSON `{"score": ..., "evidence": "...", "suggestion": "..."}`. Run these
subagents in parallel. This keeps judgements independent, and the judge never
sees why an edit was made.

## 3. Check gates

For each gate, decide pass or fail and give evidence.

## 4. Aggregate

Write the results to `<artifact-stem>.scores.json` (see `metric-format.md`).
Then run the helper script that ships in this skill's `scripts/` folder:

```bash
uv run <skill-dir>/scripts/metrictool.py aggregate <metric.yaml> <scores.json> --out <artifact-stem>.scorecard.json --markdown
```

`<skill-dir>` is the folder that contains this skill's `SKILL.md`. Do not
compute the total by hand. If the script is not available, compute
`Σ weight · score` and say that you calculated it manually.
