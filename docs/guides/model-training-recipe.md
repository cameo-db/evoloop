# Train a fixed architecture better

Skill `model-training-recipe`. The architecture is fixed; the training recipe is open (the loss, the optimizer, the learning-rate schedule, regularization, augmentation). Between tuning numbers and changing the model.

File: [`evoloop/skills/model-training-recipe/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/model-training-recipe/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/model-training-recipe/skill.yaml)). A search copies this file to `mysearch/skills/model-training-recipe/skill.yaml` when you choose the skill, and reads that copy. [Edit it during setup](../skills.md).

## When to use it

The architecture is settled (it is published, deployed, or the point of comparison) and the question is how well it can be trained. If only numbers change, settings-tuning is cheaper; if the model may change too, use model-performance with the recipe opened.

## Use it

[Use this skill in setup](../setting-up.md#3-answer-the-questions) · [Combine it with another skill](../skills.md#combining-skills) · <a href="../../which-search/?goal=model-training-recipe&run=explore_then_exploit#preview-a-search">Preview the resulting search</a>

In setup, name it at the skill question. Or put these lines in `brief.yaml`; the budget and any limits or ranges are placeholders.

```yaml
run:
  skill: model-training-recipe
  type: explore_then_exploit
budget:
  evaluations: 80
```

## What it sets

A skill's settings override the run type's and the autonomy level's. Settings in your brief override the skill's.

| Setting | Value |
|---|---|
| [`schedule.local_mix`](../fields.md#schedule-local_mix) | `{ablation: 0.1, edit: 0.55, settings: 0.35}` |
| [`space.preset`](../fields.md#space-preset) | `custom` |
| [`space.roles`](../fields.md#space-roles) | `{augmentation: open, loss: open, optimizer: open, recipe: open, schedule: open, training: open}` |

## What it tells the agents

This text is added to every call to the role named. It is the skill's file verbatim.

=== "Every role"

    The model's architecture does not change in this search. Only how it is trained does: the loss, the optimizer,
    the learning-rate schedule, regularization, augmentation, and the training loop's own choices.

=== "Writer"

    The parts of a recipe interact, so a change to one usually needs another to be re-set:
    - the loss decides what the model is asked for. Consider what it weighs (classes, ranges of the target,
      noisy examples), whether it matches the metric that is scored, and auxiliary terms.
    - the optimizer and schedule decide whether the model gets there. Warm-up, the peak rate, the decay, the
      batch size and weight decay move together; changing one alone often looks like a failure of the other.
    - regularization and augmentation decide what it generalises to. Augmentations should be changes the answer
      is truly invariant to; ones it is not invariant to teach the wrong thing.
    - the loop: gradient clipping, mixed precision, averaging of weights, which checkpoint is kept.
    One change per design, with the settings it interacts with re-set in the same design and named.

=== "Analyst"

    Group lessons by part of the recipe (loss, optimizer, schedule, regularization, augmentation). Say whether a
    gain came from fitting better (training score rose) or generalising better (the gap closed).

=== "Strategist"

    When edits to one part of the recipe stop gaining, move the slots to another part before concluding the recipe
    is done.

The writer and the analyst are also given these rules:

| If the results show | Then |
|---|---|
| training is unstable or diverges after a recipe change | lower the peak learning rate or lengthen warm-up for that design before rejecting the change |
| the training score rose and the validation score did not | the change helped fitting, not generalisation: pair it with regularization or augmentation |
| a new augmentation lowers both training and validation scores | the answer is not invariant to it: weaken or drop it |
| the best epoch is the last one | the run is too short for this recipe: the comparison favours fast recipes, so say so and ask for a longer run |
| the best epoch is very early and later epochs are worse | the rate is too high late, or regularization too weak: change the decay or add regularization |

And the writer is told, in the first half of the budget: "Try one substantial change in each part of the recipe, to find which part has room." In the second half: "Work on the parts that paid, and re-tune the settings they interact with."

## What your scoring script must report

- mark the loss, optimizer, schedule and augmentation as blocks with those roles; the model blocks stay closed
- report the training score beside the validation score under diagnostics, so that fitting and generalising can be told apart
- report `best_epoch` and `epochs_run` in result.json

[Write the evaluator](../evaluator.md) · [Evaluator interface](../project-contract.md)

## Reading the results

Compare the best recipe with the baseline row: the difference is what training alone was worth. Look at whether the training score or the gap to validation moved, and at the best epoch: a best epoch at the end of the run means the comparison favoured fast recipes and a longer run is needed.

## Why these settings

The model is settled and the question is how well it can be trained, so only the blocks that define the loss, the optimizer, the schedule and the augmentation are open. Unlike tuning, the code of those blocks can change, not only their numbers.

## Related skills

| If | Use |
|---|---|
| only the numbers of the recipe should change | [`settings-tuning`](settings-tuning.md) |
| the model itself may change | [`model-performance`](model-performance.md) |

Can be combined with [`model-performance`](model-performance.md), [`model-finetuning`](model-finetuning.md): `run.skill: [model-training-recipe, model-performance]`.

## The file

[`evoloop/skills/model-training-recipe/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/model-training-recipe/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/model-training-recipe/skill.yaml))

```yaml
name: model-training-recipe
title: Improve how a fixed model is trained
summary: The architecture is fixed; the training recipe is open (the loss, the optimizer, the learning-rate schedule, regularization, augmentation). Between tuning numbers and changing the model.
domain: model
objective: a better score from the same architecture, by training it better
tags: [recipe, training, loss, optimizer, schedule, regularization, augmentation]
version: 1
authors: [evoloop]
when: >
  The architecture is settled (it is published, deployed, or the point of comparison) and the question is how
  well it can be trained. If only numbers change, settings-tuning is cheaper; if the model may change too, use
  model-performance with the recipe opened.
settings:
  space:
    preset: custom
    roles: {loss: open, optimizer: open, schedule: open, augmentation: open, training: open, recipe: open}
  schedule:
    local_mix: {edit: 0.55, settings: 0.35, ablation: 0.1}
guidance:
  all: |
    The model's architecture does not change in this search. Only how it is trained does: the loss, the optimizer,
    the learning-rate schedule, regularization, augmentation, and the training loop's own choices.
  writer: |
    The parts of a recipe interact, so a change to one usually needs another to be re-set:
    - the loss decides what the model is asked for. Consider what it weighs (classes, ranges of the target,
      noisy examples), whether it matches the metric that is scored, and auxiliary terms.
    - the optimizer and schedule decide whether the model gets there. Warm-up, the peak rate, the decay, the
      batch size and weight decay move together; changing one alone often looks like a failure of the other.
    - regularization and augmentation decide what it generalises to. Augmentations should be changes the answer
      is truly invariant to; ones it is not invariant to teach the wrong thing.
    - the loop: gradient clipping, mixed precision, averaging of weights, which checkpoint is kept.
    One change per design, with the settings it interacts with re-set in the same design and named.
  analyst: |
    Group lessons by part of the recipe (loss, optimizer, schedule, regularization, augmentation). Say whether a
    gain came from fitting better (training score rose) or generalising better (the gap closed).
  strategist: |
    When edits to one part of the recipe stop gaining, move the slots to another part before concluding the recipe
    is done.
diagnose:
  - see: "training is unstable or diverges after a recipe change"
    do: "lower the peak learning rate or lengthen warm-up for that design before rejecting the change"
  - see: "the training score rose and the validation score did not"
    do: "the change helped fitting, not generalisation: pair it with regularization or augmentation"
  - see: "a new augmentation lowers both training and validation scores"
    do: "the answer is not invariant to it: weaken or drop it"
  - see: "the best epoch is the last one"
    do: "the run is too short for this recipe: the comparison favours fast recipes, so say so and ask for a longer run"
  - see: "the best epoch is very early and later epochs are worse"
    do: "the rate is too high late, or regularization too weak: change the decay or add regularization"
stages:
  early: "Try one substantial change in each part of the recipe, to find which part has room."
  late: "Work on the parts that paid, and re-tune the settings they interact with."
needs:
  adapter:
    - "mark the loss, optimizer, schedule and augmentation as blocks with those roles; the model blocks stay closed"
    - "report the training score beside the validation score under diagnostics, so that fitting and generalising can be told apart"
    - "report `best_epoch` and `epochs_run` in result.json"
  figures: []
  references: []
combines: [model-performance, model-finetuning]
conflicts: [settings-tuning]
goal: Train a fixed architecture better
start:
  run_type: explore_then_exploit
  evaluations: 80
why: >
  The model is settled and the question is how well it can be trained, so only the blocks that define the loss,
  the optimizer, the schedule and the augmentation are open. Unlike tuning, the code of those blocks can change,
  not only their numbers.
reading: >
  Compare the best recipe with the baseline row: the difference is what training alone was worth. Look at
  whether the training score or the gap to validation moved, and at the best epoch: a best epoch at the end of
  the run means the comparison favoured fast recipes and a longer run is needed.
instead:
  - if: only the numbers of the recipe should change
    use: settings-tuning
  - if: the model itself may change
    use: model-performance
```
