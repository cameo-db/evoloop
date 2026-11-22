# Moves

Once a slot has a kind of move and its parents, something has to write the design. This page lists
every move, who makes it, and what it costs.

| Move | Kind | Made by | Agent call |
|---|---|---|---|
| a new design | new | an agent | yes |
| an edit | local | an agent | yes |
| an ablation | local | an agent | yes |
| a settings move | local | an agent, a sampler, or an estimator | only with an agent |
| a graft | crossover | an agent | yes |
| a hybrid | crossover | an agent | yes |
| a block swap | crossover | code | no |

## Local moves

An **edit** makes one change to the parent's structure. One change, so that if the score moves you know
why. When a family's recent edits have often gained, the writer is asked for bolder ones; when they
rarely have, for smaller ones (`variation.step_adaptation`).

An **ablation** removes one component and changes nothing else. It finds dead weight: if the score does
not move, the component was not earning its place.

A **settings move** changes only numbers: a learning rate, a width, a dropout rate. Settings live in
their own marked blocks, each a single dictionary, which is what lets code change them safely.

By default local moves are shared 50% edits, 35% settings moves, 15% ablations (`schedule.local_mix`).

## Who makes a settings move

Three options, set by `variation.settings_by`.

An **agent** reads the results and proposes values, with a reason. It costs a call.

The **sampler** (`sampler`) nudges one or two values up or down by a random factor. No call.

The **estimator** (`tpe`) is Bayesian optimization, the method Optuna uses by default. It splits the
settings tried so far into the best quarter and the rest, works out which values are typical of the
good ones and untypical of the others, and draws the next settings from there. The first eight designs
are spread over the range. It makes no agent call. The
[`settings-tuning-bayesian` skill](guides/settings-tuning-bayesian.md) uses it; [`settings-tuning`](guides/settings-tuning.md) has an agent choose each trial instead.

For the estimator, give ranges where a value must stay within bounds:

```yaml
space:
  ranges: {"fit.lr": [0.00001, 0.1], "fit.weight_decay": [0.000001, 0.01]}
```

Without a range, a setting may drift a hundredfold either way from where it has been. Positive numbers
are searched on a log scale, whole numbers stay whole, and a true/false setting can take either value.
A text setting only takes values already seen. Each setting is modelled on its own, so an interaction
between two (learning rate and batch size, say) is found only through designs that happened to combine
them.

## Crossover

A crossover takes two designs from different families.

A **block swap** takes whole marked blocks from each: the trunk of one with the head of the other, or
the model of one with the training recipe of the other. Code does it. In architectures the pieces
often do not fit (the shapes disagree); the quick check catches those before any training.

A **graft** takes the single change that gained most in one parent's history and has an agent apply it
to the other parent.

A **hybrid** has an agent write one design from both parents and say which part came from which.

Only the kinds in `crossover.kinds` are used. If none is possible for a pair, the slot becomes a local
move and the record says so.

**Which two designs?** The first is chosen by the [strategy](parents.md). The second is the design
whose errors fall least like the first one's, if your evaluator reports where each model's errors fall
(`signature`); otherwise a design from another family. Two designs that fail in different places are
the pair worth combining.

## Several proposals for one slot

With `variation.proposals_per_slot` above 1 (three at about 100 evaluations, four at about 30), a writer
returns several different
proposals, each with a forecast. Only one is trained: the one with the best forecast plus a bonus for
being unlike what has been tried ([the novelty dial](schedule.md#the-novelty-dial)). A bold idea gets
its chance on paper, before a training run is spent on it.

## Returning a change as edits

By default a writer returns the whole of each block it changes. With `variation.edit_format: diff`, a
local move may come back as find-and-replace edits instead. Code applies an edit only if its text
occurs exactly once in the block, so a change cannot land in the wrong place; otherwise the proposal is
refused. On large blocks this cuts the output of a local move to a fraction.

## More than one model writing

`agents.writer_mix` shares the writer calls between models, for instance a fast one for most designs
and a strong one for a fifth of them:

```yaml
agents:
  writer_mix: [{model: claude-haiku-5-5, share: 0.8}, {model: claude-opus-5-5, share: 0.2}]
```

The report compares what each model's designs came to, so you can judge the mix.

## Approaches

An approach is one line of advice on how to go about designing, such as "change the receptive field
before the width". With `variation.approaches: fixed` you supply them; with `evolve` the analyst may
add more. Each slot is handed one approach, or none, and the report shows how often designs written
under each beat their parent. Approaches that do not pay are retired; yours never are. "No approach"
is always one of the options, so the table also shows whether approaches help at all.

## Settings on this page

[`schedule.local_mix`](fields.md#schedule-local_mix), [`variation.settings_by`](fields.md#variation-settings_by), [`space.ranges`](fields.md#space-ranges), [`variation.step_adaptation`](fields.md#variation-step_adaptation),
[`crossover.kinds`](fields.md#crossover-kinds), [`variation.proposals_per_slot`](fields.md#variation-proposals_per_slot), [`variation.edit_format`](fields.md#variation-edit_format), [`agents.writer_mix`](fields.md#agents-writer_mix),
[`variation.approaches`](fields.md#variation-approaches).
