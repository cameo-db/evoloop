# Shrink a model

Skill `model-efficiency`. Design a smaller or faster student and train it to match the model you already have. The original model is the teacher. The student's architecture and its training against the teacher are both searched.

File: [`evoloop/skills/model-efficiency/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/model-efficiency/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/model-efficiency/skill.yaml)). A search copies this file to `mysearch/skills/model-efficiency/skill.yaml` when you choose the skill, and reads that copy. [Edit it during setup](../skills.md).

## Use it

```yaml
run:
  skill: model-efficiency
  type: explore_then_exploit
budget:
  evaluations: 100
limits:
  parameters:
    max: 5000000
```

Put these lines in `brief.yaml`. The budget and any limits or ranges are placeholders. <a href="../../which-search/?goal=model-efficiency&run=explore_then_exploit#preview-a-search">Preview the resulting search</a>.

You have a model that scores well enough and costs too much to run. The aim is one cheaper model at about the same score. For a family across sizes use model-size-frontier; when the teacher is an ensemble or a different model, use model-distillation.

## What it sets

A skill's settings override the run type's and the autonomy level's. Settings in your brief override the skill's.

| Setting | Value |
|---|---|
| [`report.columns`](../fields.md#report-columns) | `[speed]` |
| [`schedule.local_mix`](../fields.md#schedule-local_mix) | `{ablation: 0.2, edit: 0.5, settings: 0.3}` |
| [`space.preset`](../fields.md#space-preset) | `architecture_and_recipe` |
| [`strategy.mechanism`](../fields.md#strategy-mechanism) | `pareto` |
| [`strategy.second_direction`](../fields.md#strategy-second_direction) | `minimize` |
| [`strategy.second_metric`](../fields.md#strategy-second_metric) | `parameters` |

## What it tells the agents

This text is added to every call to the role named. It is the skill's file verbatim.

=== "Every role"

    The model being shrunk is the teacher. Every design in this search is a student: a cheaper architecture trained
    to reproduce the teacher's outputs. A student is judged on the trade-off between its score and its cost
    (parameter count, or measured speed if that is the second metric). Deleting parts of the original and
    retraining from scratch is the weakest version of this and rarely the best.

=== "Writer"

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

=== "Analyst"

    For each change say what it did to the score and to the size or speed, and whether the gain came from the
    architecture or from how the student was trained. Report the gap to the teacher and to the same student
    trained without the teacher.

=== "Strategist"

    If students of the current shape have stopped closing the gap to the teacher, order new architectures. If the
    gap is closing, keep the share of recipe changes up.

The writer and the analyst are also given these rules:

| If the results show | Then |
|---|---|
| the student cannot fit the teacher's outputs even on training inputs | it is too small or trained too briefly: lengthen training first, then add capacity where it is cheapest |
| the student fits the teacher on training inputs and not on held-out ones | add teacher-labelled augmented or synthetic inputs; do not enlarge the student |
| the student scores the same with and without the teacher | the distillation is not doing anything: check the teacher's outputs are used, and raise their weight |
| parameter count fell but measured speed did not | the time is not where the parameters are: reduce resolution, sequence length or depth, and measure speed directly |
| a much smaller student matches the teacher | the teacher was over-sized for the data: keep going down until the score moves |

And the writer is told, in the first half of the budget: "Try several efficient architectures at the target size, each trained against the teacher with one simple recipe." In the second half: "Take the two or three best students and work on how they are trained: targets, augmentation, schedule."

## What your scoring script must report

- produce the teacher's outputs (run the original model, or read stored predictions) and train each student against them; mark the student's architecture and the distillation loss as open blocks
- report `parameters` in result.json, and `inference_speed.examples_per_s` to rank on speed (then set strategy.second_metric to examples_per_s and strategy.second_direction to maximize)
- set `limits` for the largest size or lowest speed you accept, and put those figures in the first progress line so that a design outside them costs seconds
- `parameters` in every result. The report warns if no result has it.
- A leaderboard row for teacher, added with `evoloop reference`. The report warns if it is missing.
- A leaderboard row for from scratch, added with `evoloop reference`. The report warns if it is missing.

[Write the evaluator](../evaluator.md) · [Evaluator interface](../project-contract.md)

## Reading the results

Read the students on the trade-off front against two reference rows: the teacher, and the best student trained from scratch without the teacher. Pick the smallest student whose score is within your tolerance of the teacher. A student that only matches its from-scratch twin gained nothing from distillation, and the recipe needs work before the architecture does.

## Why these settings

A small model trained on the original targets is usually worse than the same small model trained to imitate a large one. So shrinking is set up as distillation: the model you have is the teacher, and the search looks for the student architecture and the training recipe that keep the most of it. Students are selected on the trade-off between score and size, which keeps cheaper students alive even when a larger one scores higher.

## Related skills

| If | Use |
|---|---|
| you want the best model at each of several sizes | [`model-size-frontier`](model-size-frontier.md) |
| the teacher is an ensemble or a model of a different kind | [`model-distillation`](model-distillation.md) |

Can be combined with [`model-distillation`](model-distillation.md): `run.skill: [model-efficiency, model-distillation]`.

## The file

[`evoloop/skills/model-efficiency/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/model-efficiency/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/model-efficiency/skill.yaml))

```yaml
name: model-efficiency
title: Shrink a model by distilling it into an efficient student
summary: Design a smaller or faster student and train it to match the model you already have. The original model is the teacher. The student's architecture and its training against the teacher are both searched.
domain: model
objective: a smaller or faster model that keeps the original's score
tags: [efficiency, distillation, compression, student, teacher, size, speed, pareto]
version: 3
authors: [evoloop]
when: >
  You have a model that scores well enough and costs too much to run. The aim is one cheaper model at about the
  same score. For a family across sizes use model-size-frontier; when the teacher is an ensemble or a different
  model, use model-distillation.
settings:
  space:
    preset: architecture_and_recipe
  strategy:
    mechanism: pareto
    second_metric: parameters
    second_direction: minimize
  schedule:
    local_mix: {edit: 0.5, settings: 0.3, ablation: 0.2}
  report:
    columns: [speed]
guidance:
  all: |
    The model being shrunk is the teacher. Every design in this search is a student: a cheaper architecture trained
    to reproduce the teacher's outputs. A student is judged on the trade-off between its score and its cost
    (parameter count, or measured speed if that is the second metric). Deleting parts of the original and
    retraining from scratch is the weakest version of this and rarely the best.
  writer: |
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
  analyst: |
    For each change say what it did to the score and to the size or speed, and whether the gain came from the
    architecture or from how the student was trained. Report the gap to the teacher and to the same student
    trained without the teacher.
  strategist: |
    If students of the current shape have stopped closing the gap to the teacher, order new architectures. If the
    gap is closing, keep the share of recipe changes up.
diagnose:
  - see: "the student cannot fit the teacher's outputs even on training inputs"
    do: "it is too small or trained too briefly: lengthen training first, then add capacity where it is cheapest"
  - see: "the student fits the teacher on training inputs and not on held-out ones"
    do: "add teacher-labelled augmented or synthetic inputs; do not enlarge the student"
  - see: "the student scores the same with and without the teacher"
    do: "the distillation is not doing anything: check the teacher's outputs are used, and raise their weight"
  - see: "parameter count fell but measured speed did not"
    do: "the time is not where the parameters are: reduce resolution, sequence length or depth, and measure speed directly"
  - see: "a much smaller student matches the teacher"
    do: "the teacher was over-sized for the data: keep going down until the score moves"
stages:
  early: "Try several efficient architectures at the target size, each trained against the teacher with one simple recipe."
  late: "Take the two or three best students and work on how they are trained: targets, augmentation, schedule."
needs:
  adapter:
    - "produce the teacher's outputs (run the original model, or read stored predictions) and train each student against them; mark the student's architecture and the distillation loss as open blocks"
    - "report `parameters` in result.json, and `inference_speed.examples_per_s` to rank on speed (then set strategy.second_metric to examples_per_s and strategy.second_direction to maximize)"
    - "set `limits` for the largest size or lowest speed you accept, and put those figures in the first progress line so that a design outside them costs seconds"
  figures: [parameters]
  references: ["teacher", "from scratch"]
combines: [model-distillation]
conflicts: [settings-tuning, model-size-frontier]
goal: Shrink a model
start:
  run_type: explore_then_exploit
  evaluations: 100
  brief:
    limits: {parameters: {max: 5000000}}
why: >
  A small model trained on the original targets is usually worse than the same small model trained to imitate a
  large one. So shrinking is set up as distillation: the model you have is the teacher, and the search looks for
  the student architecture and the training recipe that keep the most of it. Students are selected on the
  trade-off between score and size, which keeps cheaper students alive even when a larger one scores higher.
reading: >
  Read the students on the trade-off front against two reference rows: the teacher, and the best student trained
  from scratch without the teacher. Pick the smallest student whose score is within your tolerance of the
  teacher. A student that only matches its from-scratch twin gained nothing from distillation, and the recipe
  needs work before the architecture does.
instead:
  - if: you want the best model at each of several sizes
    use: model-size-frontier
  - if: the teacher is an ensemble or a model of a different kind
    use: model-distillation
```
