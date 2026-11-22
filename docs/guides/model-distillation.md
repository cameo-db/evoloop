# Distil a smaller student from a teacher

Skill `model-distillation`. Train a smaller or faster student to match a teacher. The student's architecture and its training recipe (loss, optimizer, learning rate, regularization, augmentation) are both open.

File: [`evoloop/skills/model-distillation/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/model-distillation/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/model-distillation/skill.yaml)). A search copies this file to `mysearch/skills/model-distillation/skill.yaml` when you choose the skill, and reads that copy. [Edit it during setup](../skills.md).

## When to use it

You have a strong model or ensemble that is too large or slow to use, and want a student that keeps its accuracy. If the teacher is simply the model you want to shrink, and one cheaper model is the aim, use model-efficiency: it treats that model as the teacher. If no trained model's outputs are available, there is nothing to distil: use model-performance with limits on size.

## Use it

[Use this skill in setup](../setting-up.md#3-answer-the-questions) · [Combine it with another skill](../skills.md#combining-skills) · <a href="../../which-search/?goal=model-distillation&run=explore_then_exploit#preview-a-search">Preview the resulting search</a>

In setup, name it at the skill question. Or put these lines in `brief.yaml`; the budget and any limits or ranges are placeholders.

```yaml
run:
  skill: model-distillation
  type: explore_then_exploit
budget:
  evaluations: 100
```

## What it sets

A skill's settings override the run type's and the autonomy level's. Settings in your brief override the skill's.

| Setting | Value |
|---|---|
| [`report.columns`](../fields.md#report-columns) | `[speed]` |
| [`space.preset`](../fields.md#space-preset) | `architecture_and_recipe` |
| [`variation.approach_seeds`](../fields.md#variation-approach_seeds) | 1. Change how the student is trained before changing the student: the loss against the teacher, the weight between teacher and measured targets, the augmentations the teacher labels.<br>2. Give the student inputs the measured data does not contain (perturbed, shuffled, synthetic) and let the teacher label them.<br>3. Match the student's capacity to the gap: if it underfits the teacher, widen or deepen; if it matches the teacher on training inputs and not on held-out ones, regularize or add teacher-labelled data.<br>4. Train longer at a lower learning rate before concluding a student is too small. |
| [`variation.approaches`](../fields.md#variation-approaches) | `fixed` |

## What it tells the agents

This text is added to every call to the role named. It is taken from the skill's file.

=== "Every role"

    This search trains a student to reproduce a teacher (a larger model or an ensemble). The score measures the
    student on validation data. A student is judged against three references: the teacher, the same student
    trained from scratch on the measured targets alone, and the size or speed it was meant to reach.

=== "Writer"

    The recipe matters as much as the architecture here. What usually moves a student:

    - the target: the teacher's output in place of, or mixed with, the measured target. For classification, soft
      targets with a temperature. For regression, the teacher's mean prediction, which is less noisy than the data.
    - teacher-labelled augmentation: the teacher can label any input, so the student can train on perturbed and
      synthetic inputs far beyond the measured set. Aggressive augmentations that would be wrong against measured
      targets are right against the teacher's labels. Treat this as the default, not an extra.
    - optimization: students often want a longer schedule and less regularization than the teacher had, because
      the teacher's targets are smoother than the data.
    - starting point: a student that starts from an already trained model of its own kind learns faster than one
      from random weights.

    Change the student's size only with a reason from the results. Do not copy the teacher's architecture at
    reduced width as the only idea; a different shape often distils better.

=== "Analyst"

    Keep recipe findings and architecture findings apart, and say for each lesson which it is. Note the gap to the
    teacher and to the from-scratch student whenever the results show them: a student that only matches its
    from-scratch twin has gained nothing from the teacher.

=== "Strategist"

    If recipe moves are still gaining, keep the share of settings moves and edits high. Move to new architectures
    when the recipe has stopped paying on the current ones.

The writer and the analyst are also given these rules:

| If the results show | Then |
|---|---|
| the student does not fit the teacher's outputs even on training inputs | the student is too small or trains too briefly: train longer first, then widen or deepen |
| the student fits the teacher on training inputs but not on held-out ones | add teacher-labelled augmented or synthetic inputs, or regularize; do not enlarge the student |
| the student matches the same student trained from scratch on measured targets | the teacher is adding nothing: raise the weight of the teacher's targets, or check that the teacher's outputs are used at all |
| the student beats the teacher on validation data | check for leakage between the teacher's training data and the validation set before believing it |
| stronger augmentation lowers the score | check that the augmented inputs are labelled by the teacher and not paired with the measured targets |

And the writer is told, in the first half of the budget: "Find a recipe that works on one or two student shapes before varying the shape." In the second half: "Keep the recipe, and vary the student's size and shape around the best one to find the smallest that holds the score."

## What your evaluator must report

- the training script must produce the teacher's outputs (or read stored ones) and train the student against them; the loss and augmentation blocks should be marked as open recipe blocks
- to rank on speed or size, report `parameters` and `inference_speed.examples_per_s` in result.json; then `strategy.mechanism: pareto` or `limits` can use them
- if the teacher is an ensemble, add a reference row for the ensemble and one for its best single member
- A leaderboard row for teacher, added with `evoloop reference`. The report warns if it is missing.
- A leaderboard row for from scratch, added with `evoloop reference`. The report warns if it is missing.

[Write the evaluator](../evaluator.md) · [Evaluator interface](../project-contract.md)

## Reading the results

Compare the best student with two reference rows: the teacher (how much was lost) and the student trained from scratch (how much the teacher added). A student that only matches its from-scratch twin has not been distilled. Check the size or speed column against what you needed.

## Why these settings

A student's result depends as much on how it is trained against the teacher as on its shape, so both the architecture and the recipe are open, and the writers are told to work on the recipe first. The leaderboard is only meaningful beside the teacher and the same student trained without it.

## Related skills

| If | Use |
|---|---|
| the teacher is the model you want to shrink, and one cheaper model is the aim | [`model-efficiency`](model-efficiency.md) |
| no trained model's outputs are available | [`model-performance`](model-performance.md) |
| you want students at several sizes | add [`model-size-frontier`](model-size-frontier.md) to this one |

Can be combined with [`model-size-frontier`](model-size-frontier.md), [`model-efficiency`](model-efficiency.md): `run.skill: [model-distillation, model-size-frontier]`.

## The file

[`evoloop/skills/model-distillation/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/model-distillation/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/model-distillation/skill.yaml))

```yaml
name: model-distillation
title: Distil a student from a teacher
summary: Train a smaller or faster student to match a teacher. The student's architecture and its training recipe (loss, optimizer, learning rate, regularization, augmentation) are both open.
domain: model
objective: a smaller or faster model that matches a larger model or an ensemble
tags: [distillation, student, teacher, compression, ensemble, augmentation]
version: 3
authors: [evoloop]
when: >
  You have a strong model or ensemble that is too large or slow to use, and want a student that keeps its
  accuracy. If the teacher is simply the model you want to shrink, and one cheaper model is the aim, use
  model-efficiency: it treats that model as the teacher. If no trained model's outputs are available, there is
  nothing to distil: use model-performance with limits on size.
settings:
  space:
    preset: architecture_and_recipe
  variation:
    approaches: fixed
    approach_seeds:
      - "Change how the student is trained before changing the student: the loss against the teacher, the weight between teacher and measured targets, the augmentations the teacher labels."
      - "Give the student inputs the measured data does not contain (perturbed, shuffled, synthetic) and let the teacher label them."
      - "Match the student's capacity to the gap: if it underfits the teacher, widen or deepen; if it matches the teacher on training inputs and not on held-out ones, regularize or add teacher-labelled data."
      - "Train longer at a lower learning rate before concluding a student is too small."
  report:
    columns: [speed]
guidance:
  all: |
    This search trains a student to reproduce a teacher (a larger model or an ensemble). The score measures the
    student on validation data. A student is judged against three references: the teacher, the same student
    trained from scratch on the measured targets alone, and the size or speed it was meant to reach.
  writer: |
    The recipe matters as much as the architecture here. What usually moves a student:
    - the target: the teacher's output in place of, or mixed with, the measured target. For classification, soft
      targets with a temperature. For regression, the teacher's mean prediction, which is less noisy than the data.
    - teacher-labelled augmentation: the teacher can label any input, so the student can train on perturbed and
      synthetic inputs far beyond the measured set. Aggressive augmentations that would be wrong against measured
      targets are right against the teacher's labels. Treat this as the default, not an extra.
    - optimization: students often want a longer schedule and less regularization than the teacher had, because
      the teacher's targets are smoother than the data.
    - starting point: a student that starts from an already trained model of its own kind learns faster than one
      from random weights.
    Change the student's size only with a reason from the results. Do not copy the teacher's architecture at
    reduced width as the only idea; a different shape often distils better.
  analyst: |
    Keep recipe findings and architecture findings apart, and say for each lesson which it is. Note the gap to the
    teacher and to the from-scratch student whenever the results show them: a student that only matches its
    from-scratch twin has gained nothing from the teacher.
  strategist: |
    If recipe moves are still gaining, keep the share of settings moves and edits high. Move to new architectures
    when the recipe has stopped paying on the current ones.
diagnose:
  - see: "the student does not fit the teacher's outputs even on training inputs"
    do: "the student is too small or trains too briefly: train longer first, then widen or deepen"
  - see: "the student fits the teacher on training inputs but not on held-out ones"
    do: "add teacher-labelled augmented or synthetic inputs, or regularize; do not enlarge the student"
  - see: "the student matches the same student trained from scratch on measured targets"
    do: "the teacher is adding nothing: raise the weight of the teacher's targets, or check that the teacher's outputs are used at all"
  - see: "the student beats the teacher on validation data"
    do: "check for leakage between the teacher's training data and the validation set before believing it"
  - see: "stronger augmentation lowers the score"
    do: "check that the augmented inputs are labelled by the teacher and not paired with the measured targets"
stages:
  early: "Find a recipe that works on one or two student shapes before varying the shape."
  late: "Keep the recipe, and vary the student's size and shape around the best one to find the smallest that holds the score."
needs:
  adapter:
    - "the training script must produce the teacher's outputs (or read stored ones) and train the student against them; the loss and augmentation blocks should be marked as open recipe blocks"
    - "to rank on speed or size, report `parameters` and `inference_speed.examples_per_s` in result.json; then `strategy.mechanism: pareto` or `limits` can use them"
    - "if the teacher is an ensemble, add a reference row for the ensemble and one for its best single member"
  figures: []
  references: ["teacher", "from scratch"]
combines: [model-size-frontier, model-efficiency]
conflicts: [settings-tuning]
goal: Distil a smaller student from a teacher
start:
  run_type: explore_then_exploit
  evaluations: 100
why: >
  A student's result depends as much on how it is trained against the teacher as on its shape, so both the
  architecture and the recipe are open, and the writers are told to work on the recipe first. The leaderboard
  is only meaningful beside the teacher and the same student trained without it.
reading: >
  Compare the best student with two reference rows: the teacher (how much was lost) and the student trained from
  scratch (how much the teacher added). A student that only matches its from-scratch twin has not been
  distilled. Check the size or speed column against what you needed.
instead:
  - if: the teacher is the model you want to shrink, and one cheaper model is the aim
    use: model-efficiency
  - if: no trained model's outputs are available
    use: model-performance
  - if: you want students at several sizes
    use: "model-distillation, model-size-frontier"
```
