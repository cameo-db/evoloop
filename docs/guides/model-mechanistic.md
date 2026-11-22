# Improve an interpretable or biophysical model

Skill `model-mechanistic`. Improve a model that is interpretable by design, where the parameters stand for something (motifs in filters, a graph of interactions, rates and affinities in a biophysical model). The structure that carries the meaning is kept.

File: [`evoloop/skills/model-mechanistic/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/model-mechanistic/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/model-mechanistic/skill.yaml)). A search copies this file to `mysearch/skills/model-mechanistic/skill.yaml` and reads that copy, which you can edit.

## Use it

```yaml
run:
  skill: model-mechanistic
  type: refine
budget:
  evaluations: 80
```

Put these lines in `brief.yaml`. The budget and any limits or ranges are placeholders. <a href="../../which-search/?goal=model-mechanistic&run=refine#preview-a-search">Preview the resulting search</a>.

The model is meant to be read, not only to predict: its parts stand for things. Not for making a black-box model explainable after the fact.

## What it sets

A skill's settings override the run type's and the autonomy level's. Settings in your brief override the skill's.

| Setting | Value |
|---|---|
| [`schedule.local_mix`](../fields.md#schedule-local_mix) | `{ablation: 0.3, edit: 0.45, settings: 0.25}` |
| [`schedule.novelty`](../fields.md#schedule-novelty) | `0.2` |
| [`space.must_keep`](../fields.md#space-must_keep) | `['Every learned parameter keeps a stated meaning (a motif, an interaction, a rate, an affinity, a concentration). Do not add a component whose parameters cannot be read this way, such as a dense network between the interpretable parts and the output.', 'Keep the constraints that make the parts readable: signs, non-negativity, normalisation, saturation, conservation, units.']` |
| [`space.preset`](../fields.md#space-preset) | `template` |

## What it tells the agents

This text is added to every call to the role named. It is the skill's file verbatim.

=== "Every role"

    This model is meant to be read, not only to predict. Its parts stand for things: filters for motifs, an
    explicit term or edge for each interaction, parameters for rates, affinities or energies. A design that scores
    higher by adding an unreadable component has failed the task, whatever its score.

=== "Writer"

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

=== "Analyst"

    Report what the fitted parts came to mean where the results show it, and whether a gain came with a readable
    change or only a numerical one. Flag any design that gained by weakening a constraint.

=== "Strategist"

    Favour ablations and local edits over new families. A new family is worth a slot when the errors of every
    current design fall in the same place.

The writer and the analyst are also given these rules:

| If the results show | Then |
|---|---|
| two parts have learned the same thing | remove one, or add a term that makes them compete or differ |
| a part has learned nothing (its parameters stay near their start, or removing it costs nothing) | remove it, or change its initialisation if the mechanism is known to matter |
| the score depends strongly on the seed | the fit has poor local optima: improve the initialisation or fit in stages before changing the model |
| errors of every design fall on the same examples | a mechanism is missing: add the term those examples call for, with a stated meaning |
| a design gains by loosening a constraint (sign, non-negativity, a fixed scale) | do not keep it: the parameters are no longer identifiable, so the gain is not a readable one |

And the writer is told, in the first half of the budget: "Find out which parts are doing work, with ablations, and get the optimization reliable across seeds." In the second half: "Change the form of the terms that matter, one at a time, and prefer the simpler design at equal score."

## What your scoring script must report

- optional, and worth doing: report a figure of how well the parts match what is known (the share of filters matching known motifs, recovered interactions, parameters within physical ranges) under diagnostics; it can then be a leaderboard column, a speciality metric, or the second figure of the pareto strategy
- report `signature` (where the errors fall) so that designs with the same failure are told apart from ones that fail differently
- mark as open only the blocks that define the interpretable parts and their combination; leave the data handling and the evaluation frozen

[Write the evaluator](../evaluator.md) · [Evaluator interface](../project-contract.md)

## Reading the results

A higher score is only half the result. For the best designs, read `evoloop show` to see what changed and what the writer said it stands for, and check the fitted parameters yourself. The rule that parameters keep a meaning is an instruction to the writers, not a check in code.

## Why these settings

The model is meant to be read, so the search keeps its overall shape, tells the writers that every parameter must keep a stated meaning, and uses more ablations than usual to find parts that do no work. Novelty is turned down: a different kind of model is not the goal.

## Related skills

| If | Use |
|---|---|
| only the score matters | [`model-performance`](model-performance.md) |

## The file

[`evoloop/skills/model-mechanistic/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/model-mechanistic/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/model-mechanistic/skill.yaml))

```yaml
name: model-mechanistic
title: Improve an interpretable or biophysical model
summary: Improve a model that is interpretable by design, where the parameters stand for something (motifs in filters, a graph of interactions, rates and affinities in a biophysical model). The structure that carries the meaning is kept.
domain: model
objective: a better fit without losing what the parameters mean
tags: [interpretable, mechanistic, biophysical, motifs, interactions, constraints]
version: 2
authors: [evoloop]
when: >
  The model is meant to be read, not only to predict: its parts stand for things. Not for making a black-box model
  explainable after the fact.
settings:
  space:
    preset: template
    must_keep:
      - "Every learned parameter keeps a stated meaning (a motif, an interaction, a rate, an affinity, a concentration). Do not add a component whose parameters cannot be read this way, such as a dense network between the interpretable parts and the output."
      - "Keep the constraints that make the parts readable: signs, non-negativity, normalisation, saturation, conservation, units."
  schedule:
    novelty: 0.2
    local_mix: {edit: 0.45, settings: 0.25, ablation: 0.3}
guidance:
  all: |
    This model is meant to be read, not only to predict. Its parts stand for things: filters for motifs, an
    explicit term or edge for each interaction, parameters for rates, affinities or energies. A design that scores
    higher by adding an unreadable component has failed the task, whatever its score.
  writer: |
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
  analyst: |
    Report what the fitted parts came to mean where the results show it, and whether a gain came with a readable
    change or only a numerical one. Flag any design that gained by weakening a constraint.
  strategist: |
    Favour ablations and local edits over new families. A new family is worth a slot when the errors of every
    current design fall in the same place.
diagnose:
  - see: "two parts have learned the same thing"
    do: "remove one, or add a term that makes them compete or differ"
  - see: "a part has learned nothing (its parameters stay near their start, or removing it costs nothing)"
    do: "remove it, or change its initialisation if the mechanism is known to matter"
  - see: "the score depends strongly on the seed"
    do: "the fit has poor local optima: improve the initialisation or fit in stages before changing the model"
  - see: "errors of every design fall on the same examples"
    do: "a mechanism is missing: add the term those examples call for, with a stated meaning"
  - see: "a design gains by loosening a constraint (sign, non-negativity, a fixed scale)"
    do: "do not keep it: the parameters are no longer identifiable, so the gain is not a readable one"
stages:
  early: "Find out which parts are doing work, with ablations, and get the optimization reliable across seeds."
  late: "Change the form of the terms that matter, one at a time, and prefer the simpler design at equal score."
needs:
  adapter:
    - "optional, and worth doing: report a figure of how well the parts match what is known (the share of filters matching known motifs, recovered interactions, parameters within physical ranges) under diagnostics; it can then be a leaderboard column, a speciality metric, or the second figure of the pareto strategy"
    - "report `signature` (where the errors fall) so that designs with the same failure are told apart from ones that fail differently"
    - "mark as open only the blocks that define the interpretable parts and their combination; leave the data handling and the evaluation frozen"
  figures: []
  references: []
combines: []
conflicts: [settings-tuning]
goal: Improve an interpretable or biophysical model
start:
  run_type: refine
  evaluations: 80
why: >
  The model is meant to be read, so the search keeps its overall shape, tells the writers that every parameter
  must keep a stated meaning, and uses more ablations than usual to find parts that do no work. Novelty is turned
  down: a different kind of model is not the goal.
reading: >
  A higher score is only half the result. For the best designs, read `evoloop show` to see what changed and what
  the writer said it stands for, and check the fitted parameters yourself. The rule that parameters keep a
  meaning is an instruction to the writers, not a check in code.
instead:
  - if: only the score matters
    use: model-performance
```
