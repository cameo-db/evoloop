# Tune hyperparameters

Skill `settings-tuning` · domain: settings · [the skill in full](../skill-library.md#settings-tuning)

Tune the settings of fixed code (a model's learning rate, regularization, widths, schedule; or the parameters of any algorithm) with a Bayesian estimator in code. No structure changes and no agent calls.

## Start here

Put this in `brief.yaml` (or give the same answers to `evoloop setup`), then read `evoloop plan` before you confirm.

```yaml
run:
  type: settings_only
  skill: settings-tuning
budget:
  evaluations: 60
space:
  ranges:
    "fit.lr": [1e-05, 0.1]
```

The budget, and any limits or ranges, are placeholders: put in your own.

## Why this set-up

When only numbers change, no judgement is needed to propose the next candidate: an estimator that models which values scored well is cheaper and more systematic than an agent. This search makes no model call, so it costs compute only.

The skill sets these for you (anything you set in the brief wins):

| Setting | Value |
|---|---|
| [`audit.reviews`](../fields.md#audit-reviews) | `none` |
| [`harness.conductor`](../fields.md#harness-conductor) | `code` |
| [`harness.coordinator`](../fields.md#harness-coordinator) | `code` |
| [`harness.level`](../fields.md#harness-level) | `minimal` |
| [`schedule.local_mix`](../fields.md#schedule-local_mix) | `{ablation: 0.0, edit: 0.0, settings: 1.0}` |
| [`schedule.novel_share`](../fields.md#schedule-novel_share) | `0.0` |
| [`schedule.phases`](../fields.md#schedule-phases) | `[{cross: 0.0, local: 1.0, new: 0.0, until: 1.0}]` |
| [`space.preset`](../fields.md#space-preset) | `settings_only` |
| [`strategist.mode`](../fields.md#strategist-mode) | `'off'` |
| [`strategy.mechanism`](../fields.md#strategy-mechanism) | `greedy` |
| [`variation.proposals_per_slot`](../fields.md#variation-proposals_per_slot) | `1` |
| [`variation.settings_by`](../fields.md#variation-settings_by) | `tpe` |
| [`variation.step_adaptation`](../fields.md#variation-step_adaptation) | `false` |

## What your evaluator must report

- every setting to tune must sit in a marked params block (one dict of numbers, true/false or text)
- give bounds for settings that must stay in a range with `space.ranges`, e.g. {"fit.lr": [0.00001, 0.1]}; without one a setting may move a hundredfold either way
- to stop poor settings early, report progress and set `evaluation.ladder`

[Write the evaluator](../evaluator.md) shows how to report these; [Evaluator interface](../project-contract.md) is the reference.

## Choose something else when

| If | Use |
|---|---|
| the loss, optimizer or augmentation code should change, not only their numbers | [`model-training-recipe`](model-training-recipe.md) |
| the model's structure may change | [`model-performance`](model-performance.md) |

## Reading the result

The best row of the leaderboard holds the settings to use. Before trusting them, look at where they sit: a best value at the edge of its range means the range was wrong, and a score that barely moves across a setting means that setting does not matter. Re-fit the winner on new seeds.

Where to look: `evoloop leaderboard`, `evoloop show`, and the report ([Files of a run](../records.md)). To change course while it runs: [Watch and steer a run](../steering.md).

## What the agents are told

??? note "Every role"
    This is a search over settings alone. The structure of the code does not change.

??? note "The writer"
    You are only called if the person has switched settings moves to an agent. Change settings together when they
    interact (learning rate with batch size, with warm-up, with weight decay), and move a setting by a factor, not
    by a small step, until the results bracket the best value.

??? note "The analyst"
    Say which settings the score is sensitive to and which it is not, and whether the best values sit at the edge
    of the range tried. A best value at an edge means the range is wrong.

| If the results show | Then |
|---|---|
| the best designs have a setting at the edge of its range | widen that range in space.ranges; the optimum is probably outside it |
| the score barely changes across a setting's whole range | the setting does not matter here: fix it and spend the budget on the others |
| scores differ as much between repeats as between settings | the noise floor is too high to tune on: lengthen the run or average seeds before continuing |
| good values of one setting depend on another | the estimator models each setting alone: tune the pair in a second, narrower search around the best design |

Early in the budget: The first designs cover the ranges evenly; nothing is concluded from them one by one.

Late in the budget: The draws concentrate near the best settings; narrow the ranges if the best values are well inside them.

You can change any of this: the search gets its own copy of the skill in `skills/settings-tuning/skill.yaml` ([Skills](../skills.md)).
