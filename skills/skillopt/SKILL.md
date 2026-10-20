---
name: skillopt
description: Optimize a Claude skill (a SKILL.md and its files) against a metric by running it on a set of test tasks with subagents, scoring the outputs, and iteratively editing the skill's instructions to raise the mean score while checking a held-out set for overfitting. Use when the user wants to "optimize/improve/tune a skill", "make my skill produce better results", "benchmark skill versions", or "evaluate a skill on test cases against my metric".
---

# skillopt

A skill is an artifact whose quality shows only in what it produces. So
`skillopt` does not score the SKILL.md text. It scores the **outputs** the
skill produces on test tasks, and it changes the instructions to raise the
mean score.

Read `references/metric-format.md` and `references/scoring.md` if you have
not seen them in this session.

## Inputs

- **Skill** to optimize: the path to its folder (with `SKILL.md`).
- **Output metric**: a `*.metric.yaml` that scores what the skill produces (for example a slide-deck metric for a deck-building skill). If there is none, build one with `make-it-measurable` first.
- **Test tasks**: a `tasks.yaml` file, or create one with the user (see below).
- **Budget**: the number of iterations (default 3) and the number of runs per task (default 1, or 2–3 if outputs vary a lot).

### Test tasks

```yaml
tasks:
  - id: intro-evals
    prompt: "Build a 10-slide intro deck on evaluating LLM apps for engineers."
    files: [inputs/objectives.md]     # optional inputs the task needs
    split: train                      # train | holdout
```

If the user has no tasks, draft 6–10 realistic ones together with them. Cover
typical cases and 1–2 hard cases. Put about 30% in `holdout`. The holdout
tasks are never used to decide on edits. They only show whether the gains
generalize.

## Cost check (required)

One evaluation of a version = (number of tasks × runs) skill runs + the same
number of scoring runs. Tell the user the estimated number of subagent runs
for the whole budget, for example "3 iterations × 7 train tasks × 2 agents ≈ 42
agent runs, plus the holdout runs", and get confirmation before you start.

## Setup

Never edit the original skill. Work in `skillopt-runs/<skill-name>/`:

```
v0/                 # copy of the original skill folder
v1/ ...             # one folder per candidate
outputs/v<n>/<task-id>/   # what each run produced
results.md          # one row per version: train mean, holdout mean, decision
```

## Evaluate a version

1. **Run**: for each task, start a subagent (Agent tool) with this instruction: "Read `<version>/SKILL.md` (and the files it references) and follow it to complete this task: <prompt>. The input files are in <paths>. Write all outputs to `outputs/v<n>/<task-id>/`. Do not ask questions. Make reasonable assumptions and list them in `outputs/.../assumptions.md`." Run the tasks in parallel.
2. **Score**: for each output, start a separate judge subagent that follows the scoring procedure in `references/scoring.md`. Give it only the output, the metric and the references. It must not see the skill or the version number. Collect each `*.scorecard.json`.
3. **Aggregate**: compute the mean total over the tasks (and over runs), the per-term means, and the gate pass rate. Record them in `results.md`.

If the user explicitly asked for a workflow or multi-agent orchestration, you
can run steps 1–2 as a Workflow script instead of single Agent calls.

## Optimization loop

1. **Baseline**: evaluate `v0` on the train tasks and the holdout tasks.
2. **Diagnose**: read the lowest-scoring outputs and the terms with the most headroom across tasks. For each pattern, find the instruction (or the missing instruction) in the SKILL.md that causes it. Write down 1–3 hypotheses, such as "Outputs are too dense because the skill says 'be comprehensive' and gives no length limit."
3. **Edit**: create `v<n+1>` with small, targeted changes that test the hypotheses. Prefer clarifying or replacing an instruction over adding new ones. Keep the skill about as long as it was. Never put task-specific content (answers, test prompts) into the skill: that is overfitting by definition.
4. **Evaluate** the candidate on the train tasks.
5. **Accept** it if the train mean improves by more than the noise margin (default 0.02, or the standard deviation between runs if you made several runs) and the gate pass rate does not drop. Otherwise, reject it and try the next hypothesis.
6. **Log** the hypothesis, the change, the scores and the decision in `results.md`.

After the last iteration, evaluate the best version on the holdout tasks. If
the holdout mean did not improve while the train mean did, say clearly that
the gains are probably overfitting.

## Final report

- The train and holdout means for `v0` and the best version, plus per-term deltas.
- The accepted changes with their hypotheses, and a diff of the SKILL.md (`diff -u v0/SKILL.md v<best>/SKILL.md`).
- The rejected hypotheses, briefly. They are useful knowledge too.
- Any metric gaps you found (outputs that scored high but look wrong).
- The location of the best version. Copy it over the original skill only if the user asks for it.
