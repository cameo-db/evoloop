# Tune hyperparameters

Skill `settings-tuning`. An agent tunes the hyperparameters of a fixed model, the architecture's (depth, widths, kernel sizes) and the training's (learning rate, weight decay, schedule), reading the results of earlier trials before choosing the next.

File: [`evoloop/skills/settings-tuning/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/settings-tuning/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/settings-tuning/skill.yaml)). A search copies this file to `mysearch/skills/settings-tuning/skill.yaml` when you choose the skill, and reads that copy. [Edit it during setup](../skills.md).

## When to use it

The code is right and its numbers are in question. Use it on its own, or after an architecture search, on the winner. To tune without any agent calls, use settings-tuning-bayesian (a built-in Bayesian optimizer).

## Use it

[Use this skill in setup](../setting-up.md#3-answer-the-questions) · [Combine it with another skill](../skills.md#combining-skills) · <a href="../../which-search/?goal=settings-tuning&run=settings_only#preview-a-search">Preview the resulting search</a>

In setup, name it at the skill question. Or put these lines in `brief.yaml`; the budget and any limits or ranges are placeholders.

```yaml
run:
  skill: settings-tuning
  type: settings_only
budget:
  evaluations: 60
```

## What it sets

A skill's settings override the run type's and the autonomy level's. Settings in your brief override the skill's.

| Setting | Value |
|---|---|
| [`audit.reviews`](../fields.md#audit-reviews) | `end` |
| [`harness.conductor`](../fields.md#harness-conductor) | `code` |
| [`harness.coordinator`](../fields.md#harness-coordinator) | `code` |
| [`harness.level`](../fields.md#harness-level) | `standard` |
| [`schedule.local_mix`](../fields.md#schedule-local_mix) | `{ablation: 0.0, edit: 0.0, settings: 1.0}` |
| [`schedule.novel_share`](../fields.md#schedule-novel_share) | `0.0` |
| [`schedule.phases`](../fields.md#schedule-phases) | `[{cross: 0.0, local: 1.0, new: 0.0, until: 1.0}]` |
| [`space.preset`](../fields.md#space-preset) | `settings_only` |
| [`strategist.mode`](../fields.md#strategist-mode) | `'off'` |
| [`strategy.mechanism`](../fields.md#strategy-mechanism) | `greedy` |
| [`variation.proposals_per_slot`](../fields.md#variation-proposals_per_slot) | `1` |
| [`variation.settings_by`](../fields.md#variation-settings_by) | `agent` |
| [`variation.step_adaptation`](../fields.md#variation-step_adaptation) | `false` |

## What it tells the agents

This text is added to every call to the role named. It is the skill's file verbatim.

=== "Every role"

    This search changes hyperparameters only. The code of the model and the training loop stays as it is.

=== "Writer"

    You are tuning hyperparameters. Read `recent` and the leaderboard as a table of trials before proposing.
    - Hyperparameters interact. Learning rate moves with batch size, warm-up and weight decay; width moves with
      depth and dropout. Change the ones that interact together and say which you treated as a group.
    - Move by factors until the best value is bracketed: 3x or 10x on a learning rate, 2x on a width. Small steps
      come after you have a trial on each side of the best.
    - Architecture hyperparameters (depth, widths, kernel sizes, number of heads) change capacity and cost. A
      larger model that scores the same has not improved anything; say what the change does to the parameter count.
    - If the best trial sits at the edge of the values tried so far, go further in that direction next.
    - Do not repeat a setting within the noise floor of one already tried.
    State in `hypothesis` which hyperparameter you think limits the model now, and why the results say so.

=== "Analyst"

    Say which hyperparameters the score is sensitive to and which it is not, with the trials that show it. Flag a
    best value at the edge of the range tried, and pairs of hyperparameters that seem to interact.

The writer and the analyst are also given these rules:

| If the results show | Then |
|---|---|
| the best trials have a hyperparameter at the edge of the values tried | go further in that direction; the optimum is probably outside what has been tried |
| the score barely changes across a hyperparameter's whole range | it does not matter here: fix it and spend the trials on the others |
| scores differ as much between repeats as between settings | the noise floor is too high to tune on: train longer or average seeds before continuing |
| the best learning rate changes when the batch size or the width changes | tune them together: scale the learning rate with the batch size, and re-tune it after a change of width |
| training loss is still falling at the end of the best trials | the training length limits the result, not the hyperparameters: lengthen it before tuning further |

And the writer is told, in the first half of the budget: "Bracket each hyperparameter with large moves, one group of interacting ones at a time." In the second half: "Refine around the best trial with small moves, and re-check the leader on a new seed."

## What your scoring script must report

- every hyperparameter to tune must sit in a marked params block (one dict of numbers, true/false or text)
- report the parameter count, so that a change of width or depth shows its cost
- for tuning with no agent calls, use the settings-tuning-bayesian skill

[Write the evaluator](../evaluator.md) · [Evaluator interface](../project-contract.md)

## Reading the results

The top row of the leaderboard holds the hyperparameters to use. Check where they sit before trusting them: a best value at the edge of what was tried means the search stopped too early in that direction, and a score that barely moves across a hyperparameter means it does not matter. Train the winner again on new seeds.

## Why these settings

Tuning is a sequence of trials where each should be chosen from the ones before. An agent that reads the trials can move interacting hyperparameters together and can tell a hyperparameter that does not matter from one that has not been pushed far enough. The search changes numbers only, always builds on the best trial, and keeps an analyst to summarise what the trials show.

## Related skills

| If | Use |
|---|---|
| you want no agent calls at all | [`settings-tuning-bayesian`](settings-tuning-bayesian.md) |
| the loss, optimizer or augmentation code should change, not only their numbers | [`model-training-recipe`](model-training-recipe.md) |
| the model's structure may change | [`model-performance`](model-performance.md) |

## The file

[`evoloop/skills/settings-tuning/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/settings-tuning/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/settings-tuning/skill.yaml))

```yaml
name: settings-tuning
title: Tune a model's hyperparameters
summary: An agent tunes the hyperparameters of a fixed model, the architecture's (depth, widths, kernel sizes) and the training's (learning rate, weight decay, schedule), reading the results of earlier trials before choosing the next.
domain: settings
objective: the best hyperparameters for a fixed model
tags: [hyperparameters, tuning, architecture, learning rate, agent, bayesian, tpe]
version: 3
authors: [evoloop]
when: >
  The code is right and its numbers are in question. Use it on its own, or after an architecture search, on the
  winner. To tune without any agent calls, use settings-tuning-bayesian (a built-in Bayesian optimizer).
settings:
  space:
    preset: settings_only
  variation:
    settings_by: agent
    proposals_per_slot: 1
    step_adaptation: false
  strategy:
    mechanism: greedy
  schedule:
    phases: [{until: 1.0, new: 0.0, cross: 0.0, local: 1.0}]
    local_mix: {edit: 0.0, settings: 1.0, ablation: 0.0}
    novel_share: 0.0
  harness:
    level: standard
    coordinator: code
    conductor: code
  strategist:
    mode: "off"
  audit:
    reviews: end
guidance:
  all: |
    This search changes hyperparameters only. The code of the model and the training loop stays as it is.
  writer: |
    You are tuning hyperparameters. Read `recent` and the leaderboard as a table of trials before proposing.
    - Hyperparameters interact. Learning rate moves with batch size, warm-up and weight decay; width moves with
      depth and dropout. Change the ones that interact together and say which you treated as a group.
    - Move by factors until the best value is bracketed: 3x or 10x on a learning rate, 2x on a width. Small steps
      come after you have a trial on each side of the best.
    - Architecture hyperparameters (depth, widths, kernel sizes, number of heads) change capacity and cost. A
      larger model that scores the same has not improved anything; say what the change does to the parameter count.
    - If the best trial sits at the edge of the values tried so far, go further in that direction next.
    - Do not repeat a setting within the noise floor of one already tried.
    State in `hypothesis` which hyperparameter you think limits the model now, and why the results say so.
  analyst: |
    Say which hyperparameters the score is sensitive to and which it is not, with the trials that show it. Flag a
    best value at the edge of the range tried, and pairs of hyperparameters that seem to interact.
diagnose:
  - see: "the best trials have a hyperparameter at the edge of the values tried"
    do: "go further in that direction; the optimum is probably outside what has been tried"
  - see: "the score barely changes across a hyperparameter's whole range"
    do: "it does not matter here: fix it and spend the trials on the others"
  - see: "scores differ as much between repeats as between settings"
    do: "the noise floor is too high to tune on: train longer or average seeds before continuing"
  - see: "the best learning rate changes when the batch size or the width changes"
    do: "tune them together: scale the learning rate with the batch size, and re-tune it after a change of width"
  - see: "training loss is still falling at the end of the best trials"
    do: "the training length limits the result, not the hyperparameters: lengthen it before tuning further"
stages:
  early: "Bracket each hyperparameter with large moves, one group of interacting ones at a time."
  late: "Refine around the best trial with small moves, and re-check the leader on a new seed."
needs:
  adapter:
    - "every hyperparameter to tune must sit in a marked params block (one dict of numbers, true/false or text)"
    - "report the parameter count, so that a change of width or depth shows its cost"
    - "for tuning with no agent calls, use the settings-tuning-bayesian skill"
  figures: []
  references: []
combines: []
conflicts: [settings-tuning-bayesian, model-performance, model-distillation, model-efficiency, model-size-frontier, model-mechanistic, model-training-recipe, model-ensemble-members, model-finetuning, algorithm-runtime, bioinformatics-algorithm, data-pipeline]
goal: Tune hyperparameters
start:
  run_type: settings_only
  evaluations: 60
why: >
  Tuning is a sequence of trials where each should be chosen from the ones before. An agent that reads the
  trials can move interacting hyperparameters together and can tell a hyperparameter that does not matter from
  one that has not been pushed far enough. The search changes numbers only, always builds on the best trial, and
  keeps an analyst to summarise what the trials show.
reading: >
  The top row of the leaderboard holds the hyperparameters to use. Check where they sit before trusting them: a
  best value at the edge of what was tried means the search stopped too early in that direction, and a score that
  barely moves across a hyperparameter means it does not matter. Train the winner again on new seeds.
instead:
  - if: you want no agent calls at all
    use: settings-tuning-bayesian
  - if: the loss, optimizer or augmentation code should change, not only their numbers
    use: model-training-recipe
  - if: the model's structure may change
    use: model-performance
```
