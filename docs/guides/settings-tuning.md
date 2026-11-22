# Tune hyperparameters

An agent tunes the hyperparameters of a fixed model, the architecture's (depth, widths, kernel sizes) and the training's (learning rate, weight decay, schedule), reading the results of earlier trials before choosing the next.

## What a good result looks like

The top row of the leaderboard holds the hyperparameters to use. Check where they sit before trusting them: a best value at the edge of what was tried means the search stopped too early in that direction, and a score that barely moves across a hyperparameter means it does not matter. Train the winner again on new seeds.

## Start here

```yaml
run:
  type: settings_only
  skill: settings-tuning
budget:
  evaluations: 60
```

These lines go in `brief.yaml`. The budget, and any limits or ranges, are placeholders for your own. <a href="../../which-search/?goal=settings-tuning&run=settings_only#preview-a-search">Preview this search</a> to see what it will do, or [set up this search](../setting-up.md) on your project. The goal is the skill `settings-tuning`, shown in full in the [skill library](../skill-library.md#settings-tuning).

## Why this set-up

Tuning is a sequence of trials where each should be chosen from the ones before. An agent that reads the trials can move interacting hyperparameters together and can tell a hyperparameter that does not matter from one that has not been pushed far enough. The search changes numbers only, always builds on the best trial, and keeps an analyst to summarise what the trials show.

The skill sets these for you (anything you set in the brief wins):

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

## What your evaluator must report

- every hyperparameter to tune must sit in a marked params block (one dict of numbers, true/false or text)
- report the parameter count, so that a change of width or depth shows its cost
- for tuning with no agent calls, use the settings-tuning-bayesian skill

[Write the evaluator](../evaluator.md) shows how to report these; [Evaluator interface](../project-contract.md) is the reference.

## Choose something else when

| If | Use |
|---|---|
| you want no agent calls at all | [`settings-tuning-bayesian`](settings-tuning-bayesian.md) |
| the loss, optimizer or augmentation code should change, not only their numbers | [`model-training-recipe`](model-training-recipe.md) |
| the model's structure may change | [`model-performance`](model-performance.md) |

## Where to look

`evoloop leaderboard` for the ranking, `evoloop show` for one design, and the report for everything ([Files of a run](../records.md)). To change course while it runs: [Watch and steer a run](../steering.md).

## What the agents are told

??? note "Every role"
    This search changes hyperparameters only. The code of the model and the training loop stays as it is.

??? note "The writer"
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

??? note "The analyst"
    Say which hyperparameters the score is sensitive to and which it is not, with the trials that show it. Flag a
    best value at the edge of the range tried, and pairs of hyperparameters that seem to interact.

| If the results show | Then |
|---|---|
| the best trials have a hyperparameter at the edge of the values tried | go further in that direction; the optimum is probably outside what has been tried |
| the score barely changes across a hyperparameter's whole range | it does not matter here: fix it and spend the trials on the others |
| scores differ as much between repeats as between settings | the noise floor is too high to tune on: train longer or average seeds before continuing |
| the best learning rate changes when the batch size or the width changes | tune them together: scale the learning rate with the batch size, and re-tune it after a change of width |
| training loss is still falling at the end of the best trials | the training length limits the result, not the hyperparameters: lengthen it before tuning further |

Early in the budget: Bracket each hyperparameter with large moves, one group of interacting ones at a time.

Late in the budget: Refine around the best trial with small moves, and re-check the leader on a new seed.

You can change any of this: the search gets its own copy of the skill in `skills/settings-tuning/skill.yaml` ([Skills](../skills.md)).
