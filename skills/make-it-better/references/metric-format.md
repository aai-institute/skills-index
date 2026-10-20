# Metric file format (`*.metric.yaml`)

A metric is a **reward function** for one kind of artifact. It is a convex
combination of terms:

```
total = Σ_i  weight_i · score_i        with  weight_i > 0,  Σ_i weight_i = 1,  score_i ∈ [0, 1]
```

So `total ∈ [0, 1]`. Every term must be normalized to `[0, 1]` (1 = best).
Hard requirements that must never be traded off live in `gates`. Gates do not
change `total`. They decide whether the artifact is *acceptable*.

`make-it-measurable`, `score-card`, `make-it-better` and `skillopt` read this format. `make-it-measurable` writes it.
`scripts/metrictool.py validate` checks it.

## Schema

```yaml
name: course-slides-quality          # kebab-case identifier
version: 1                           # bump when you change terms or weights
artifact: >                          # what this metric scores
  Slide decks for half-day courses at the institute.
owner: Jane Doe                      # whose preferences these are
context:                             # free-form background every judge reads
  audience: Mid-level engineers, no ML background.
  purpose: Teach the basics of evaluating LLM applications.
references:                          # optional files every judge may need
  learning_objectives: ./objectives.md

terms:
  - id: clarity                      # unique, kebab-case
    name: Clarity of explanations
    weight: 0.35
    kind: judge                      # judge | computed | checklist
    description: Each concept is explained once, in plain words, with an example.
    rubric:                          # judge only: anchored levels, score -> observable description
      0.0: Concepts are used before they are defined, or are not defined at all.
      0.5: Most concepts are defined, but definitions are long or abstract and have no example.
      1.0: Every new concept is defined in at most 2 sentences and has a concrete example.
    examples:                        # optional, strongly recommended
      good: "Slide 4 of last year's deck: 'A metric is ...'"
      bad: "Three slides of jargon before the first definition."

  - id: words-per-slide
    name: Text density
    weight: 0.15
    kind: computed
    measure: Mean number of words per content slide (skip title and section slides).
    normalize:                       # computed only: maps the raw value to [0, 1]
      type: band                     # linear | band | threshold
      zero_below: 0
      ideal_min: 15
      ideal_max: 40
      zero_above: 90

  - id: objectives-covered
    name: Covers the learning objectives
    weight: 0.5
    kind: checklist
    items:                           # checklist only: score = passed / total
      - id: lo-1
        check: Learners can name three failure modes of LLM apps.
      - id: lo-2
        check: Learners can write a simple eval for a classification prompt.

gates:                               # optional hard requirements (pass/fail)
  - id: no-confidential
    check: No customer names or internal financial numbers appear.
```

## Term kinds

| kind | Who measures | How it maps to [0, 1] | Use for |
|---|---|---|---|
| `judge` | An LLM judge reads the artifact and the rubric | The judge picks the closest anchor level. Values between anchors are allowed. | Subtle qualities: clarity, tone, structure, argument quality |
| `computed` | A deterministic measurement (count, script, tool) | `normalize` (see below) | Length, word counts, readability scores, test pass rate, slide count |
| `checklist` | A judge answers yes/no per item | Fraction of passed items | Coverage of required content, conventions, required sections |

Prefer `computed` and `checklist` where possible. They are cheaper and less
noisy than `judge`.

### Rubric rules (`judge`)

- Give at least the anchors `0.0`, `0.5` and `1.0`. Five anchors (`0.25` steps) are better for subtle terms.
- Each anchor describes **observable** features ("every concept has an example"), not adjectives ("very clear").
- One term measures one thing. If an anchor mentions two independent qualities, split the term.

### `normalize` (`computed`)

| type | Fields | Result |
|---|---|---|
| `linear` | `worst`, `best` | `(raw - worst) / (best - worst)`, clamped to [0, 1]. `best < worst` means lower is better. |
| `band` | `zero_below`, `ideal_min`, `ideal_max`, `zero_above` | 1 inside `[ideal_min, ideal_max]`, falls linearly to 0 at `zero_below` / `zero_above`. |
| `threshold` | `op` (`<`, `<=`, `>`, `>=`, `==`), `value` | 1 if `raw op value`, else 0. |

## Scores file (`*.scores.json`)

The output of a scoring run. `metrictool.py aggregate` turns it into a total.

```json
{
  "artifact": "decks/llm-evals.md",
  "metric": "metrics/course-slides-quality.metric.yaml",
  "terms": {
    "clarity": {"score": 0.5, "evidence": "Slide 7 uses 'logprobs' with no definition.", "suggestion": "Define logprobs on slide 6."},
    "words-per-slide": {"raw": 52.3, "evidence": "Measured on 18 content slides."},
    "objectives-covered": {"items": {"lo-1": true, "lo-2": false}, "evidence": "No hands-on eval exercise."}
  },
  "gates": {
    "no-confidential": {"pass": true, "evidence": "No customer names found."}
  }
}
```

For each term, give one of `score` (judge), `raw` (computed) or `items`
(checklist). The script computes the rest. Always add `evidence`: a quote or a
location in the artifact.
