# Comparison with FunSearch and AlphaEvolve

evoloop is put together from mechanisms that others introduced and tested. This page says which, how
each appears here, and where evoloop differs or falls short. Every mechanism below is an option; the
[menu](menu.md) lists the settings.

## The situation it is built for

FunSearch and AlphaEvolve search over programs that are scored in seconds, so they can afford
thousands to millions of evaluations, and a score is the same every time it is measured. A search over
model architectures is a different situation:

| | Program search (FunSearch, AlphaEvolve) | Architecture search |
|---|---|---|
| One evaluation | seconds, on a CPU | minutes to hours, on a GPU |
| Evaluations in a search | thousands to millions | tens to hundreds |
| The score | exact | noisy: two fits of one model differ |
| What a wrong turn costs | little | a real share of the budget |

So evoloop takes their mechanisms and changes the weight put on each. With a few hundred evaluations,
what matters most is which design is tried next, that a noisy score is not mistaken for a gain, and that
the person can change course when the results call for it.

## What is taken from where

### From FunSearch

| Mechanism | In evoloop | How it differs here |
|---|---|---|
| Evolve one function inside a fixed skeleton | `EVOLVE-BLOCK` markers in `base/`; the rest is frozen and hashed | several blocks, each with a kind and a role, so the space can be opened role by role |
| Islands, the weaker half reset at intervals | `strategy.islands`, `strategy.reset_every` | off by default: islands split a small budget thinly |
| Programs kept apart by what they do | `strategy.descriptors: [behaviour]` | grouped by where a trained model's errors fall, by correlation, not by an exact match |

### From AlphaEvolve

| Mechanism | In evoloop | How it differs here |
|---|---|---|
| A program database: an archive on islands | `strategy.mechanism: archive` with `strategy.islands` | cells are family, size, behaviour or any reported metric |
| A fast and a strong model writing together | `agents.writer_mix` | any models and shares; the report compares their designs |
| Edits as diffs | `variation.edit_format: diff` | an edit applies only if its text occurs exactly once in the block |
| An evaluation cascade | the quick check, then `evaluation.ladder` | successive halving inside one job, not a set of cheaper tests |
| Several objectives | `strategy.mechanism: pareto` | two figures, not many |
| Instructions that evolve | `variation.approaches` | one line per slot varies, with a record of what it led to |

### From other methods

| Method | Mechanism | In evoloop | How it differs here |
|---|---|---|---|
| Regularized evolution | tournament selection with aging | `strategy.mechanism: tournament` | as published, at smaller scale |
| MAP-Elites | the best of each kind, on a grid | `strategy.mechanism: archive` | the grid's axes are yours to choose |
| NEAT | new species protected while young | `strategy.mechanism: lineage` | lineages of designs, not genomes; the default |
| Successive halving, ASHA | weak runs stopped by rank | `evaluation.ladder` | within one job, charged by the share of the run used |
| TPE (Optuna, Hyperopt) | Bayesian choice of settings | `variation.settings_by: tpe` | a small implementation; each setting modelled alone |
| Network morphism, weight sharing | a child starts from its parent's weights | `evaluation.inherit_weights` | the evaluator decides what to load |

## What evoloop adds

Four things are not in the methods above.

You can change a search while it runs. Most settings can be changed without a restart, each change is
recorded with who made it, and because a strategy keeps no state, even the strategy can change
([Monitor and steer a search](steering.md)).

Scores are only compared when they mean the same thing. You state how noisy your score is, and a
difference below that counts as none. Lengthening training starts a new comparison period, so old and
new scores are never ranked together ([When two scores can be compared](comparable.md)).

What kind of problem a search is, is chosen apart from how to search. A skill carries the settings and
the advice for one kind of goal, and can be edited ([Choose a skill and a run type](which-search.md)).

The agents are audited. Every call is recorded with what the agent forecast and what happened, and a
scorecard says whether each role earns its cost ([Audit the agents](auditing.md)).

## Where it falls short of them

- Throughput. There is no tier of cheap stand-in evaluations (a smaller dataset or model) with
  promotion to the real task. The ladder stops weak designs early within the real task, which
  stretches a budget a few-fold, not a thousandfold.
- Scale of evidence. FunSearch and AlphaEvolve have published results. evoloop has passed its tests
  on a built-in example with stub agents; it has not yet been run with a real agent on a real training
  task. See [Status and limits](status.md).
- Novelty before training. How different a proposal is from what has been tried is measured on its
  code. What a model does is known only after it is trained.
- Prompt evolution. Only one line of the writer's instructions varies.
- Scope of an edit. A writer changes marked blocks. It cannot restructure the frozen code around
  them.

## Choosing settings that resemble a method

| To search like | Set |
|---|---|
| FunSearch | `strategy.mechanism: archive`, `strategy.descriptors: [behaviour]`, `strategy.islands: 4`, `strategy.reset_every: 40`, `harness.level: minimal` |
| AlphaEvolve | `strategy.mechanism: archive` on `strategy.islands: 3`, `agents.writer_mix`, `variation.edit_format: diff`, `variation.approaches: evolve`, `evaluation.ladder` |
| Regularized evolution | `strategy.mechanism: tournament`, a schedule of local moves only |
| Hyperband with a Bayesian sampler (BOHB) | `run.skill: settings-tuning-bayesian` with `evaluation.ladder` |
| A hill climb | `strategy.mechanism: greedy` |

These resemble the methods; they are not reimplementations of them, and they need budgets in the
hundreds to behave as described.

## Sources

- Romera-Paredes et al., "Mathematical discoveries from program search with large language models", *Nature*, 2024 (FunSearch).
- Novikov et al., "AlphaEvolve: A coding agent for scientific and algorithmic discovery", 2025.
- Real et al., "Regularized Evolution for Image Classifier Architecture Search", *AAAI*, 2019.
- Mouret and Clune, "Illuminating search spaces by mapping elites", 2015 (MAP-Elites).
- Stanley and Miikkulainen, "Evolving Neural Networks through Augmenting Topologies", *Evolutionary Computation*, 2002 (NEAT).
- Li et al., "Hyperband: A Novel Bandit-Based Approach to Hyperparameter Optimization", *JMLR*, 2018; Li et al., "A System for Massively Parallel Hyperparameter Tuning", *MLSys*, 2020 (ASHA).
- Bergstra et al., "Algorithms for Hyper-Parameter Optimization", *NeurIPS*, 2011 (TPE).
- Falkner et al., "BOHB: Robust and Efficient Hyperparameter Optimization at Scale", *ICML*, 2018.
