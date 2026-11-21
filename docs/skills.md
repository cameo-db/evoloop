# Skills: the kind of optimisation

Two choices set up a search, and they are independent.

- The **run type** says *how to search*: the strategy, the schedule, the harness.
- The **skill** says *what kind of problem it is*: what may change, how designs are selected, what the
  agents should know about this kind of task, and what the adapter and the leaderboard need for it.

Raising a score, distilling a student, tuning hyperparameters, shrinking a model and improving an
interpretable model are different jobs. A writer that is good at one needs different advice for
another, and the right selection rule differs too.

```yaml
run:
  type: explore_then_exploit
  skill: distillation
```

## The built-in skills

| Skill | For | What it sets | What the agents are told |
|---|---|---|---|
| `performance` | the best score, nothing else weighed | nothing: the plain search | find what limits the leader (capacity, optimisation, generalisation) before adding to it |
| `distillation` | a smaller or faster student trained to match a teacher | architecture and recipe both open; four approaches for the writers | the recipe matters as much as the architecture: the target, teacher-labelled augmentation, a longer schedule, the starting point |
| `tuning` | the settings of a fixed model | settings only; moves made by a Bayesian estimator in code; no agent calls | (nothing is asked of an agent) |
| `efficiency` | a smaller or faster model at the same score | selection on the trade-off between the score and size; half the local moves are ablations | take away before adding, and in what order; state the effect on score and on size |
| `mechanistic` | a model that is interpretable by design, or a biophysical one | the overall shape kept; every parameter must keep a stated meaning; more ablations, less novelty | change the form of a term, what is shared, the number of parts, the constraints; never add an unreadable component |

`evoloop skills` lists them, and `evoloop skills NAME` prints one in full: its settings, its guidance
for each role, and what it needs. The [menu](menu.md) shows exactly what each sets.

## How a skill takes effect

- **Settings.** A skill's settings are laid over the run type's and under yours: what you set in the
  brief always wins. `evoloop plan` lists them under "From the skill ...".
- **Guidance.** Every call to an agent carries the skill's guidance for that role. It is written for
  the kind of task, not for your project, so `task.md`, the results and your notes outrank it.
- **Needs.** A skill says what the adapter must do or report. The plan lists these, and the report
  warns when a figure the skill needs is in no result, or a reference row it expects is missing (for
  distillation: the teacher, and the same student trained from scratch).

A skill can be changed during a run (`evoloop set ... run.skill=efficiency`); the ledger lists every
setting that moved with it. A skill may only set what can change during a run: the objective, the data
and the length of a run stay in the brief.

## Combining with run types

Any skill goes with any run type. Where both set the same thing, the skill's value stands, because it
knows the problem.

| You want | Run type | Skill |
|---|---|---|
| a better model, architecture open | `explore_then_exploit` | `performance` |
| a known good model made smaller | `refine` | `efficiency` |
| a student for an ensemble, both architecture and recipe open | `explore_then_exploit` | `distillation` |
| the best learning rate, weight decay and widths for one model | any (the skill sets the schedule) | `tuning` |
| a readable model improved without losing what it means | `refine` | `mechanistic` |

## The tuning skill's estimator

With `variation.settings_by: tpe` (set by the `tuning` skill, and usable in any search), a settings
move is drawn in code by a tree-structured Parzen estimator, the method Optuna uses by default:

- The settings tried so far are split into the best quarter and the rest.
- For each setting, a density is laid over the values of the good ones and one over the others. New
  values are drawn from the good density, and the draw most typical of good designs and least typical
  of the others is taken.
- The first eight designs are drawn from a prior: evenly over the range if you gave one, otherwise
  around the value in the code.
- Positive numbers are modelled on a log scale, whole numbers stay whole, and true/false settings can
  take either value. A text setting only takes values already seen.

```yaml
space:
  ranges: {"fit.lr": [0.00001, 0.1], "fit.weight_decay": [0.000001, 0.01]}
```

`space.ranges` bounds a setting; without a range it may move a hundredfold either way from where it has
been. Each setting is modelled on its own, so an interaction between two settings is found only
through the designs that happened to combine them. Add `evaluation.ladder` to stop poor settings early.

## A skill of your own

A skill is a folder holding one file. Copy a built-in one and edit it:

```
evoloop skills efficiency --copy mysearch/skills/edge_device
```

```yaml
name: edge_device
summary: Fit the model into 2 MB at the same accuracy.
settings:
  strategy: {mechanism: pareto, second_metric: parameters, second_direction: minimize}
guidance:
  all: The model runs on a microcontroller with 2 MB of flash and no floating-point unit.
  writer: Prefer depthwise convolutions and powers of two for widths. No attention.
  analyst: Report the size in bytes beside every score.
needs:
  adapter: ["report `parameters` in result.json"]
  figures: [parameters]
  references: ["the current production model"]
```

Then `run.skill: skills/edge_device` (a name under the search's `skills/` folder, a relative path, or a
full path). `guidance` may address `all`, `writer`, `analyst`, `strategist`, `coordinator` and
`conductor`.

An edit to a skill's folder during a run takes effect at the controller's next turn and is not
recorded in the ledger. To keep a record of a change, copy the folder under a new name and
`evoloop set ... run.skill=NEW`.

## What is not known

The built-in guidance is written from experience of these tasks; none of it has been measured in this
package. Whether a search with a skill does better than the same search without one is a comparison
you can run: the same budget, with `run.skill` set and unset.
