# Distil a smaller student from a teacher

Train a smaller or faster student to match a teacher. The student's architecture and its training recipe (loss, optimizer, learning rate, regularization, augmentation) are both open.

## What a good result looks like

Compare the best student with two reference rows: the teacher (how much was lost) and the student trained from scratch (how much the teacher added). A student that only matches its from-scratch twin has not been distilled. Check the size or speed column against what you needed.

## Start here

```yaml
run:
  type: explore_then_exploit
  skill: model-distillation
budget:
  evaluations: 100
```

These lines go in `brief.yaml`. The budget, and any limits or ranges, are placeholders for your own. <a href="../../which-search/?goal=model-distillation&run=explore_then_exploit#preview-a-search">Preview this search</a> to see what it will do, or [set up this search](../setting-up.md) on your project. The goal is the skill `model-distillation`, shown in full in the [skill library](../skill-library.md#model-distillation).

## Why this set-up

A student's result depends as much on how it is trained against the teacher as on its shape, so both the architecture and the recipe are open, and the writers are told to work on the recipe first. The leaderboard is only meaningful beside the teacher and the same student trained without it.

The skill sets these for you (anything you set in the brief wins):

| Setting | Value |
|---|---|
| [`report.columns`](../fields.md#report-columns) | `[speed]` |
| [`space.preset`](../fields.md#space-preset) | `architecture_and_recipe` |
| [`variation.approach_seeds`](../fields.md#variation-approach_seeds) | `['Change how the student is trained before changing the student: the loss against the teacher, the weight between teacher and measured targets, the augmentations the teacher labels.', 'Give the student inputs the measured data does not contain (perturbed, shuffled, synthetic) and let the teacher label them.', 'Match the student''s capacity to the gap: if it underfits the teacher, widen or deepen; if it matches the teacher on training inputs and not on held-out ones, regularize or add teacher-labelled data.', Train longer at a lower learning rate before concluding a student is too small.]` |
| [`variation.approaches`](../fields.md#variation-approaches) | `fixed` |

## What your evaluator must report

- the training script must produce the teacher's outputs (or read stored ones) and train the student against them; the loss and augmentation blocks should be marked as open recipe blocks
- to rank on speed or size, report `parameters` and `inference_speed.examples_per_s` in result.json; then `strategy.mechanism: pareto` or `limits` can use them
- if the teacher is an ensemble, add a reference row for the ensemble and one for its best single member
- Add a row to the leaderboard for teacher, to compare against (`evoloop reference`).
- Add a row to the leaderboard for from scratch, to compare against (`evoloop reference`).

[Write the evaluator](../evaluator.md) shows how to report these; [Evaluator interface](../project-contract.md) is the reference.

## Choose something else when

| If | Use |
|---|---|
| there is no teacher, only a model to shrink | [`model-efficiency`](model-efficiency.md) |
| you want students at several sizes | add [`model-size-frontier`](model-size-frontier.md) to this one |

It combines well with [`model-size-frontier`](model-size-frontier.md), [`model-efficiency`](model-efficiency.md) (`run.skill: [model-distillation, ...]`).

## Where to look

`evoloop leaderboard` for the ranking, `evoloop show` for one design, and the report for everything ([Files of a run](../records.md)). To change course while it runs: [Watch and steer a run](../steering.md).

## What the agents are told

??? note "Every role"
    This search trains a student to reproduce a teacher (a larger model or an ensemble). The score measures the
    student on validation data. A student is judged against three references: the teacher, the same student
    trained from scratch on the measured targets alone, and the size or speed it was meant to reach.

??? note "The writer"
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

??? note "The analyst"
    Keep recipe findings and architecture findings apart, and say for each lesson which it is. Note the gap to the
    teacher and to the from-scratch student whenever the results show them: a student that only matches its
    from-scratch twin has gained nothing from the teacher.

??? note "The strategist"
    If recipe moves are still gaining, keep the share of settings moves and edits high. Move to new architectures
    when the recipe has stopped paying on the current ones.

| If the results show | Then |
|---|---|
| the student does not fit the teacher's outputs even on training inputs | the student is too small or trains too briefly: train longer first, then widen or deepen |
| the student fits the teacher on training inputs but not on held-out ones | add teacher-labelled augmented or synthetic inputs, or regularize; do not enlarge the student |
| the student matches the same student trained from scratch on measured targets | the teacher is adding nothing: raise the weight of the teacher's targets, or check that the teacher's outputs are used at all |
| the student beats the teacher on validation data | check for leakage between the teacher's training data and the validation set before believing it |
| stronger augmentation lowers the score | check that the augmented inputs are labelled by the teacher and not paired with the measured targets |

Early in the budget: Find a recipe that works on one or two student shapes before varying the shape.

Late in the budget: Keep the recipe, and vary the student's size and shape around the best one to find the smallest that holds the score.

You can change any of this: the search gets its own copy of the skill in `skills/model-distillation/skill.yaml` ([Skills](../skills.md)).
