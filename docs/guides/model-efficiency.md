# Find a smaller or faster model

Skill `model-efficiency` · domain: model · [the skill in full](../skill-library.md#model-efficiency)

Make the model smaller or faster while holding its score. Designs are selected on the trade-off between the score and size (or speed), and removal is the commonest move.

## Start here

Put this in `brief.yaml` (or give the same answers to `evoloop setup`), then read `evoloop plan` before you confirm.

```yaml
run:
  type: refine
  skill: model-efficiency
budget:
  evaluations: 100
limits:
  parameters:
    max: 5000000
```

!!! note "A starting point"
    These settings are a reasoned starting point. They have not been measured against alternatives; see [Status and limits](../status.md). The numbers in the example (the budget, any limits or ranges) are placeholders for yours.

## Why this set-up

The aim is one cheaper model at about the same score, so designs are selected on the trade-off between score and size instead of on score alone, and half the local moves remove something. Starting from a model you know is good, a refining search keeps close to it.

The skill sets these for you (anything you set in the brief wins):

| Setting | Value |
|---|---|
| [`report.columns`](../fields.md) | `[speed]` |
| [`schedule.local_mix`](../fields.md) | `{ablation: 0.5, edit: 0.35, settings: 0.15}` |
| [`strategy.mechanism`](../fields.md) | `pareto` |
| [`strategy.second_direction`](../fields.md) | `minimize` |
| [`strategy.second_metric`](../fields.md) | `parameters` |

## What your evaluator must report

- report `parameters` in result.json (and `inference_speed.examples_per_s` to rank on speed: then set strategy.second_metric to examples_per_s and strategy.second_direction to maximize)
- set `limits` for the largest size or lowest speed you accept, and put those figures in the first progress line so that a design outside them costs seconds
- add a reference row for the model you are trying to shrink
- **Required in every result:** `parameters`. A search that never sees it is told so in the report.

How the adapter reports these: [The project's code](../project-contract.md).

## Choose something else when

| If | Use |
|---|---|
| you want the best model at each of several sizes | [`model-size-frontier`](model-size-frontier.md) |
| a larger model or ensemble is available to learn from | [`model-distillation`](model-distillation.md) |

It combines well with [`model-distillation`](model-distillation.md) (`run.skill: [model-efficiency, ...]`).

## Reading the result

Read the population table: it lists the designs on the trade-off front with their score and size. Pick the smallest whose score is within your tolerance of the reference row. A design is only an improvement if its loss in score is below the noise floor or acceptable to you.

Where to look: `evoloop leaderboard`, `evoloop show`, and the report ([Records and the study file](../records.md)). To change course while it runs: [Steering a run](../steering.md).

## What the agents are told

??? note "Every role"
    The aim is the best trade-off between the score and the model's cost (its parameter count, or its speed if the
    person has set that as the second figure). A design that loses less than the noise floor and is clearly
    smaller or faster is a gain. `limits_enforced_by_code` gives the hard bounds; a design outside them is
    rejected unrun or stopped early.

??? note "The writer"
    Take away before adding. In rough order of what is usually cheapest to remove:
    - layers or blocks whose removal earlier ablations showed costs nothing;
    - width, where the layer is far from the output or follows a wider one;
    - dense layers and large heads, which often hold most of the parameters;
    - full convolutions, replaced by separable, grouped or bottlenecked ones; attention replaced by something local
      where the range it covers is short;
    - resolution early (stride or pooling sooner), which cuts the cost of everything after it.
    Then spend a little of what was saved where it pays most. State in `predicted_effect` both what you expect for
    the score and for the size or speed, since both are measured.
    When the parent sits at the small end of the front, try to recover score at the same size; at the accurate end,
    try to cut size at the same score. Do not propose a design larger than the largest on the leaderboard.

??? note "The analyst"
    For each change say what it did to the score and to the size or speed. A lesson of the form "removing X costs
    nothing" is the most useful kind here; cite the runs.

??? note "The strategist"
    If the front has stopped moving at the small end, order ablations on its smallest designs. If it has stopped
    at the accurate end, order crossovers between the two ends.

| If the results show | Then |
|---|---|
| an ablation costs less than the noise floor | the component is dead weight: keep it out, and try removing its neighbours |
| parameter count fell but speed did not | the time is not where the parameters are: cut resolution, sequence length or depth instead of width |
| every reduction costs score, however small | the model is already tight: change the kind of layer (separable, bottleneck, shared weights) instead of shrinking the same ones |
| a much smaller design scores the same as the reference | the reference was over-sized for the data: keep going down until the score moves |

Early in the budget: Find what can be removed for nothing, with ablations across the whole model.

Late in the budget: Work at the two ends of the front, and cross designs from the ends.

You can change any of this: the search gets its own copy of the skill in `skills/model-efficiency/skill.yaml` ([Skills](../skills.md)).
