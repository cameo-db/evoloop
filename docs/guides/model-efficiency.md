# Shrink a model

Design a smaller or faster student and train it to match the model you already have. The original model is the teacher. The student's architecture and its training against the teacher are both searched.

## What a good result looks like

Read the students on the trade-off front against two reference rows: the teacher, and the best student trained from scratch without the teacher. Pick the smallest student whose score is within your tolerance of the teacher. A student that only matches its from-scratch twin gained nothing from distillation, and the recipe needs work before the architecture does.

## Start here

```yaml
run:
  type: explore_then_exploit
  skill: model-efficiency
budget:
  evaluations: 100
limits:
  parameters:
    max: 5000000
```

These lines go in `brief.yaml`. The budget, and any limits or ranges, are placeholders for your own. <a href="../../which-search/?goal=model-efficiency&run=explore_then_exploit#preview-a-search">Preview this search</a> to see what it will do, or [set up this search](../setting-up.md) on your project. The goal is the skill `model-efficiency`, shown in full in the [skill library](../skill-library.md#model-efficiency).

## Why this set-up

A small model trained on the original targets is usually worse than the same small model trained to imitate a large one. So shrinking is set up as distillation: the model you have is the teacher, and the search looks for the student architecture and the training recipe that keep the most of it. Students are selected on the trade-off between score and size, which keeps cheaper students alive even when a larger one scores higher.

The skill sets these for you (anything you set in the brief wins):

| Setting | Value |
|---|---|
| [`report.columns`](../fields.md#report-columns) | `[speed]` |
| [`schedule.local_mix`](../fields.md#schedule-local_mix) | `{ablation: 0.2, edit: 0.5, settings: 0.3}` |
| [`space.preset`](../fields.md#space-preset) | `architecture_and_recipe` |
| [`strategy.mechanism`](../fields.md#strategy-mechanism) | `pareto` |
| [`strategy.second_direction`](../fields.md#strategy-second_direction) | `minimize` |
| [`strategy.second_metric`](../fields.md#strategy-second_metric) | `parameters` |

## What your evaluator must report

- produce the teacher's outputs (run the original model, or read stored predictions) and train each student against them; mark the student's architecture and the distillation loss as open blocks
- report `parameters` in result.json, and `inference_speed.examples_per_s` to rank on speed (then set strategy.second_metric to examples_per_s and strategy.second_direction to maximize)
- set `limits` for the largest size or lowest speed you accept, and put those figures in the first progress line so that a design outside them costs seconds
- Every result must report `parameters`. If none does, the report says so.
- Add a row to the leaderboard for teacher, to compare against (`evoloop reference`).
- Add a row to the leaderboard for from scratch, to compare against (`evoloop reference`).

[Write the evaluator](../evaluator.md) shows how to report these; [Evaluator interface](../project-contract.md) is the reference.

## Choose something else when

| If | Use |
|---|---|
| you want the best model at each of several sizes | [`model-size-frontier`](model-size-frontier.md) |
| the teacher is an ensemble or a model of a different kind | [`model-distillation`](model-distillation.md) |

It combines well with [`model-distillation`](model-distillation.md) (`run.skill: [model-efficiency, ...]`).

## Where to look

`evoloop leaderboard` for the ranking, `evoloop show` for one design, and the report for everything ([Files of a run](../records.md)). To change course while it runs: [Watch and steer a run](../steering.md).

## What the agents are told

??? note "Every role"
    The model being shrunk is the teacher. Every design in this search is a student: a cheaper architecture trained
    to reproduce the teacher's outputs. A student is judged on the trade-off between its score and its cost
    (parameter count, or measured speed if that is the second metric). Deleting parts of the original and
    retraining from scratch is the weakest version of this and rarely the best.

??? note "The writer"
    Design the student for efficiency; do not start from the teacher with pieces removed.
    - Pick operators that are cheap for the hardware: depthwise-separable or grouped convolutions, bottlenecks,
      early downsampling, shared weights, local attention in place of global where the context is short.
    - Size the student to the target. Decide the parameter or latency budget first, then spend it where the
      teacher's own ablations or the results say it matters.
    - Train against the teacher. Use the teacher's outputs as targets, alone or mixed with the measured ones, and
      let the teacher label augmented or synthetic inputs: a small student needs more data than the measured set
      holds, and the teacher supplies it.
    - Give the student time. Students usually need a longer schedule and less regularization than the teacher had.
    State in `predicted_effect` the expected score and the expected size or speed. Do not propose a student
    larger than the teacher.

??? note "The analyst"
    For each change say what it did to the score and to the size or speed, and whether the gain came from the
    architecture or from how the student was trained. Report the gap to the teacher and to the same student
    trained without the teacher.

??? note "The strategist"
    If students of the current shape have stopped closing the gap to the teacher, order new architectures. If the
    gap is closing, keep the share of recipe changes up.

| If the results show | Then |
|---|---|
| the student cannot fit the teacher's outputs even on training inputs | it is too small or trained too briefly: lengthen training first, then add capacity where it is cheapest |
| the student fits the teacher on training inputs and not on held-out ones | add teacher-labelled augmented or synthetic inputs; do not enlarge the student |
| the student scores the same with and without the teacher | the distillation is not doing anything: check the teacher's outputs are used, and raise their weight |
| parameter count fell but measured speed did not | the time is not where the parameters are: reduce resolution, sequence length or depth, and measure speed directly |
| a much smaller student matches the teacher | the teacher was over-sized for the data: keep going down until the score moves |

Early in the budget: Try several efficient architectures at the target size, each trained against the teacher with one simple recipe.

Late in the budget: Take the two or three best students and work on how they are trained: targets, augmentation, schedule.

You can change any of this: the search gets its own copy of the skill in `skills/model-efficiency/skill.yaml` ([Skills](../skills.md)).
