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
references:                          # optional files every judge may need,
  learning_objectives: ../objectives.md  # paths relative to this metric file
accept_threshold: 0.7                # optional: minimum total to be acceptable

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

  - id: required-parts
    name: Required parts are present
    weight: 0.5
    kind: checklist
    items:                           # checklist only: score = passed / total
      - id: objectives
        check: The deck states its learning objectives near the start.
      - id: recap
        check: The last content slide recaps the session and refers back to the objectives.

gates:                               # optional hard requirements (pass/fail),
  - id: no-confidential              # only those the owner confirmed
    check: No customer names or internal financial numbers appear.

caps:                                # optional: a failed check limits the total
  - id: has-recommendation
    check: The document states a recommendation or the decision it needs.
    max_total: 0.5                   # if the check fails, total = min(total, 0.5)
```

Notes on the top-level fields:

- `references`: paths are relative to the directory of the metric file. A metric in `metrics/` that needs `objectives.md` in the project root writes `../objectives.md`. `metrictool.py validate` warns if a file does not exist.
- `accept_threshold`: optional. An artifact is acceptable only if all gates pass **and** `total >= accept_threshold`. Leave it out if the total alone should not reject anything.
- `caps`: optional. Use a cap when a missing element should limit the score without rejecting the artifact ("without a recommendation it can't score above 0.5"). If a cap's check fails, `total` becomes at most `max_total`. A gate rejects; a cap limits; a term costs points.
- Every gate, cap and checklist item needs an `id` and a `check`. A gate or cap must be checkable from the artifact and its references alone.

## Term kinds

| kind | Who measures | How it maps to [0, 1] | Use for |
|---|---|---|---|
| `judge` | An LLM judge reads the artifact and the rubric | The judge picks the closest anchor level. Values between anchors are allowed. | Subtle qualities: clarity, tone, structure, argument quality |
| `computed` | A deterministic measurement (count, script, tool) | `normalize` (see below) | Length, word counts, readability scores, test pass rate, slide count |
| `checklist` | A judge answers yes/no per item | Fraction of passed items | Coverage of required content, conventions, required sections |

Prefer `computed` and `checklist` where possible. They are cheaper and less
noisy than `judge`. Use `computed` only if a script can measure the value
without judgement. "Number of slides with a question mark" is `computed`;
"number of slides where learners apply the concept" needs judgement, so make
it a `checklist` or `judge` term.

### Rubric rules (`judge`)

- Give at least the anchors `0.0`, `0.5` and `1.0`. Five anchors (`0.25` steps) are better for subtle terms.
- Each anchor describes **observable** features ("every concept has an example"), not adjectives ("very clear").
- One term measures one thing. If an anchor mentions two independent qualities, split the term.

### Rules for each item (`judge`)

Checklist items are fixed, so a checklist cannot say "each objective stated in
the deck is practiced" when every deck has different objectives. Do not
hardcode one artifact's items (`lo-1`, `lo-2`, ...) into a metric that is used
for many artifacts. Use a `judge` term whose anchors are shares instead:

```yaml
  - id: objectives-practiced
    kind: judge
    description: Each learning objective stated at the start has an activity that applies it.
    rubric:
      0.0: No stated objective is practiced, or no objectives are stated.
      0.5: About half of the stated objectives are practiced.
      1.0: Every stated objective is practiced.
```

### Limits per unit (`computed`)

A mean hides outliers: one 150-word slide among twenty 25-word slides still
averages under 40. If the user's limit applies to every unit (each slide,
each function, each section), measure one of these instead of the mean:

- the **share of units within the limit** ("share of content slides with at most 40 words"), normalized with `linear` (`worst: 0.5, best: 1`, for example), or
- the **worst unit** ("words on the longest content slide"), normalized with `band` or `threshold`.

### `normalize` (`computed`)

| type | Fields | Result |
|---|---|---|
| `linear` | `worst`, `best` | `(raw - worst) / (best - worst)`, clamped to [0, 1]. `best < worst` means lower is better. |
| `band` | `ideal_min`, `ideal_max`; optional `zero_below`, `zero_above` | 1 inside `[ideal_min, ideal_max]`, falls linearly to 0 at `zero_below` / `zero_above`. `ideal_min` and `ideal_max` are always required. Leave out `zero_below` if there is no lower limit (everything below `ideal_min` also scores 1), or `zero_above` if there is no upper limit. For "at most 250, zero at 400" write `ideal_min: 0, ideal_max: 250, zero_above: 400`. |
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
    "required-parts": {"items": {"objectives": true, "recap": false}, "evidence": "Last slide is 'Thank you', no recap."}
  },
  "gates": {
    "no-confidential": {"pass": true, "evidence": "No customer names found."}
  },
  "caps": {
    "has-recommendation": {"pass": true, "evidence": "Slide 1: 'We recommend option B.'"}
  }
}
```

For each term, give one of `score` (judge), `raw` (computed) or `items`
(checklist). Give a `pass` result for every gate and every cap. The script computes the rest. Always add `evidence`: a quote or a
location in the artifact.
