# Improve an interpretable or biophysical model

Improve a model that is interpretable by design, where the parameters stand for something (motifs in filters, a graph of interactions, rates and affinities in a biophysical model). The structure that carries the meaning is kept.

## What a good result looks like

A higher score is only half the result. For the best designs, read `evoloop show` to see what changed and what the writer said it stands for, and check the fitted parameters yourself. The rule that parameters keep a meaning is an instruction to the writers, not a check in code.

## Start here

```yaml
run:
  type: refine
  skill: model-mechanistic
budget:
  evaluations: 80
```

These lines go in `brief.yaml`. The budget, and any limits or ranges, are placeholders for your own. <a href="../../which-search/?goal=model-mechanistic&run=refine#preview-a-search">Preview this search</a> to see what it will do, or [set up this search](../setting-up.md) on your project. The goal is the skill `model-mechanistic`, shown in full in the [skill library](../skill-library.md#model-mechanistic).

## Why this set-up

The model is meant to be read, so the search keeps its overall shape, tells the writers that every parameter must keep a stated meaning, and uses more ablations than usual to find parts that do no work. Novelty is turned down: a different kind of model is not the goal.

The skill sets these for you (anything you set in the brief wins):

| Setting | Value |
|---|---|
| [`schedule.local_mix`](../fields.md#schedule-local_mix) | `{ablation: 0.3, edit: 0.45, settings: 0.25}` |
| [`schedule.novelty`](../fields.md#schedule-novelty) | `0.2` |
| [`space.must_keep`](../fields.md#space-must_keep) | `['Every learned parameter keeps a stated meaning (a motif, an interaction, a rate, an affinity, a concentration). Do not add a component whose parameters cannot be read this way, such as a dense network between the interpretable parts and the output.', 'Keep the constraints that make the parts readable: signs, non-negativity, normalisation, saturation, conservation, units.']` |
| [`space.preset`](../fields.md#space-preset) | `template` |

## What your evaluator must report

- optional, and worth doing: report a figure of how well the parts match what is known (the share of filters matching known motifs, recovered interactions, parameters within physical ranges) under diagnostics; it can then be a leaderboard column, a speciality metric, or the second figure of the pareto strategy
- report `signature` (where the errors fall) so that designs with the same failure are told apart from ones that fail differently
- mark as open only the blocks that define the interpretable parts and their combination; leave the data handling and the evaluation frozen

[Write the evaluator](../evaluator.md) shows how to report these; [Evaluator interface](../project-contract.md) is the reference.

## Choose something else when

| If | Use |
|---|---|
| only the score matters | [`model-performance`](model-performance.md) |

## Where to look

`evoloop leaderboard` for the ranking, `evoloop show` for one design, and the report for everything ([Files of a run](../records.md)). To change course while it runs: [Watch and steer a run](../steering.md).

## What the agents are told

??? note "Every role"
    This model is meant to be read, not only to predict. Its parts stand for things: filters for motifs, an
    explicit term or edge for each interaction, parameters for rates, affinities or energies. A design that scores
    higher by adding an unreadable component has failed the task, whatever its score.

??? note "The writer"
    Ways to improve such a model without losing what it means:
    - the form of a term: a saturating or cooperative response in place of a linear one, a competition term, a
      distance or orientation dependence for an interaction, a different pooling over positions;
    - what is shared and what is free: tie parameters that should be the same thing (both strands, repeated
      units), free ones that were wrongly tied;
    - the number of parts: fewer, when two have learned the same thing or one has learned nothing (an ablation
      shows it); more, only when the errors point to a missing mechanism;
    - constraints and priors that keep the parts identifiable: sparsity on interactions, non-negativity,
      regularisation toward known values, a fixed scale so that two parameters cannot trade off against each other;
    - initialisation and optimization, which matter more here than in a free network: constrained models have
      poor local optima, so a better start or a staged fit (parts first, interactions after) can be the whole gain.
    In `hypothesis`, name the mechanism the change stands for and what it should make true of the fitted
    parameters, not only of the score. Prefer the simpler of two designs that score within the noise floor.
    For a biophysical model, keep the equations dimensionally consistent and say what each new parameter is.

??? note "The analyst"
    Report what the fitted parts came to mean where the results show it, and whether a gain came with a readable
    change or only a numerical one. Flag any design that gained by weakening a constraint.

??? note "The strategist"
    Favour ablations and local edits over new families. A new family is worth a slot when the errors of every
    current design fall in the same place.

| If the results show | Then |
|---|---|
| two parts have learned the same thing | remove one, or add a term that makes them compete or differ |
| a part has learned nothing (its parameters stay near their start, or removing it costs nothing) | remove it, or change its initialisation if the mechanism is known to matter |
| the score depends strongly on the seed | the fit has poor local optima: improve the initialisation or fit in stages before changing the model |
| errors of every design fall on the same examples | a mechanism is missing: add the term those examples call for, with a stated meaning |
| a design gains by loosening a constraint (sign, non-negativity, a fixed scale) | do not keep it: the parameters are no longer identifiable, so the gain is not a readable one |

Early in the budget: Find out which parts are doing work, with ablations, and get the optimization reliable across seeds.

Late in the budget: Change the form of the terms that matter, one at a time, and prefer the simpler design at equal score.

You can change any of this: the search gets its own copy of the skill in `skills/model-mechanistic/skill.yaml` ([Skills](../skills.md)).
