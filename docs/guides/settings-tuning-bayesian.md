# Tune hyperparameters without agents

Skill `settings-tuning-bayesian`. A built-in Bayesian optimizer (TPE) draws each set of hyperparameters from the results of earlier trials. No agent is called, so the search costs compute only.

File: [`evoloop/skills/settings-tuning-bayesian/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/settings-tuning-bayesian/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/settings-tuning-bayesian/skill.yaml)). A search copies this file to `mysearch/skills/settings-tuning-bayesian/skill.yaml` when you choose the skill, and reads that copy. [Edit it during setup](../skills.md).

## When to use

You want hyperparameter tuning at no agent cost, or a baseline to compare an agent against. For tuning led by an agent that reads the trials, use settings-tuning.

## Usage

[Use this skill in setup](../setting-up.md#3-answer-the-setup-questions) · [Combine it with another skill](../skills.md#combining-skills) · <a href="../../which-search/?goal=settings-tuning-bayesian&run=settings_only#preview-a-search">Preview the resulting search</a>

In setup, name it at the skill question. Or put these lines in `brief.yaml`; the budget and any limits or ranges are placeholders.

```yaml
run:
  skill: settings-tuning-bayesian
  type: settings_only
budget:
  evaluations: 60
space:
  ranges:
    "fit.lr": [1e-05, 0.1]
```

## Settings

A skill's settings override the run type's and the autonomy level's. Settings in your brief override the skill's.

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

## Agent guidance

This text is added to every call to the role named. It is taken from the skill's file.

=== "Every role"

    This is a search over settings alone. The structure of the code does not change.

=== "Writer"

    You are only called if the person has switched settings moves to an agent. Change settings together when they
    interact (learning rate with batch size, with warm-up, with weight decay), and move a setting by a factor, not
    by a small step, until the results bracket the best value.

=== "Analyst"

    Say which settings the score is sensitive to and which it is not, and whether the best values sit at the edge
    of the range tried. A best value at an edge means the range is wrong.

The writer and the analyst are also given these rules:

| If the results show | Then |
|---|---|
| the best designs have a setting at the edge of its range | widen that range in space.ranges; the optimum is probably outside it |
| the score barely changes across a setting's whole range | the setting does not matter here: fix it and spend the budget on the others |
| scores differ as much between repeats as between settings | the noise floor is too high to tune on: lengthen the run or average seeds before continuing |
| good values of one setting depend on another | the estimator models each setting alone: tune the pair in a second, narrower search around the best design |

And the writer is told, in the first half of the budget: "The first designs cover the ranges evenly; nothing is concluded from them one by one." In the second half: "The draws concentrate near the best settings; narrow the ranges if the best values are well inside them."

## Evaluator requirements

- every setting to tune must sit in a marked params block (one dict of numbers, true/false or text)
- give bounds for settings that must stay in a range with `space.ranges`, e.g. {"fit.lr": [0.00001, 0.1]}; without one a setting may move a hundredfold either way
- to stop poor settings early, report progress and set `evaluation.ladder`

[Write the evaluator](../evaluator.md) · [Evaluator interface](../project-contract.md)

## Reading the results

The best row of the leaderboard holds the settings to use. Before trusting them, look at where they sit: a best value at the edge of its range means the range was wrong, and a score that barely moves across a setting means that setting does not matter. Re-fit the winner on new seeds.

## Rationale

When only numbers change, no judgement is needed to propose the next candidate: an estimator that models which values scored well is cheaper and more systematic than an agent. This search makes no model call, so it costs compute only.

## Related skills

| If | Use |
|---|---|
| you want an agent to read the trials and reason about what to try | [`settings-tuning`](settings-tuning.md) |
| the loss, optimizer or augmentation code should change, not only their numbers | [`model-training-recipe`](model-training-recipe.md) |
| the model's structure may change | [`model-performance`](model-performance.md) |

## Skill file

[`evoloop/skills/settings-tuning-bayesian/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/settings-tuning-bayesian/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/settings-tuning-bayesian/skill.yaml))

```yaml
name: settings-tuning-bayesian
title: Tune hyperparameters with a Bayesian optimizer, no agents
summary: A built-in Bayesian optimizer (TPE) draws each set of hyperparameters from the results of earlier trials. No agent is called, so the search costs compute only.
domain: settings
objective: the best hyperparameters for a fixed model, at no agent cost
tags: [hyperparameters, tuning, bayesian, tpe, learning rate, no agents]
version: 3
authors: [evoloop]
when: >
  You want hyperparameter tuning at no agent cost, or a baseline to compare an agent against. For tuning led by
  an agent that reads the trials, use settings-tuning.
settings:
  space:
    preset: settings_only
  variation:
    settings_by: tpe
    proposals_per_slot: 1
    step_adaptation: false
  strategy:
    mechanism: greedy
  schedule:
    phases: [{until: 1.0, new: 0.0, cross: 0.0, local: 1.0}]
    local_mix: {edit: 0.0, settings: 1.0, ablation: 0.0}
    novel_share: 0.0
  harness:
    level: minimal
    coordinator: code
    conductor: code
  strategist:
    mode: "off"
  audit:
    reviews: none
guidance:
  all: |
    This is a search over settings alone. The structure of the code does not change.
  writer: |
    You are only called if the person has switched settings moves to an agent. Change settings together when they
    interact (learning rate with batch size, with warm-up, with weight decay), and move a setting by a factor, not
    by a small step, until the results bracket the best value.
  analyst: |
    Say which settings the score is sensitive to and which it is not, and whether the best values sit at the edge
    of the range tried. A best value at an edge means the range is wrong.
diagnose:
  - see: "the best designs have a setting at the edge of its range"
    do: "widen that range in space.ranges; the optimum is probably outside it"
  - see: "the score barely changes across a setting's whole range"
    do: "the setting does not matter here: fix it and spend the budget on the others"
  - see: "scores differ as much between repeats as between settings"
    do: "the noise floor is too high to tune on: lengthen the run or average seeds before continuing"
  - see: "good values of one setting depend on another"
    do: "the estimator models each setting alone: tune the pair in a second, narrower search around the best design"
stages:
  early: "The first designs cover the ranges evenly; nothing is concluded from them one by one."
  late: "The draws concentrate near the best settings; narrow the ranges if the best values are well inside them."
needs:
  adapter:
    - "every setting to tune must sit in a marked params block (one dict of numbers, true/false or text)"
    - "give bounds for settings that must stay in a range with `space.ranges`, e.g. {\"fit.lr\": [0.00001, 0.1]}; without one a setting may move a hundredfold either way"
    - "to stop poor settings early, report progress and set `evaluation.ladder`"
  figures: []
  references: []
combines: []
conflicts: [settings-tuning, model-performance, model-distillation, model-efficiency, model-size-frontier, model-mechanistic, model-training-recipe, model-ensemble-members, model-finetuning, algorithm-runtime, bioinformatics-algorithm, data-pipeline]
goal: Tune hyperparameters without agents
start:
  run_type: settings_only
  evaluations: 60
  brief:
    space: {ranges: {"fit.lr": [0.00001, 0.1]}}
why: >
  When only numbers change, no judgement is needed to propose the next candidate: an estimator that models which
  values scored well is cheaper and more systematic than an agent. This search makes no model call, so it costs
  compute only.
reading: >
  The best row of the leaderboard holds the settings to use. Before trusting them, look at where they sit: a
  best value at the edge of its range means the range was wrong, and a score that barely moves across a setting
  means that setting does not matter. Re-fit the winner on new seeds.
instead:
  - if: you want an agent to read the trials and reason about what to try
    use: settings-tuning
  - if: the loss, optimizer or augmentation code should change, not only their numbers
    use: model-training-recipe
  - if: the model's structure may change
    use: model-performance
```
