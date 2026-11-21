# Which search should I run?

Three answers decide most of a search: what you want to optimize, how to search for it, and how much
you can spend. Pick them here; everything else has a default that follows.

## What to optimize: the goal

Each goal is a different search with its own guide. The guide gives a brief to start from, says what
your evaluator has to report, and explains how to read the result.

**You have a model and a task.**

| You want | Guide |
|---|---|
| the best score you can get, with the architecture open | [`model-performance`](guides/model-performance.md) |
| a better score from the same architecture, by changing the loss, optimizer or augmentation | [`model-training-recipe`](guides/model-training-recipe.md) |
| its learning rate, weight decay or widths set better, and nothing else changed | [`settings-tuning`](guides/settings-tuning.md) |
| to adapt a pretrained model | [`model-finetuning`](guides/model-finetuning.md) |

**You have a model that works and costs too much.**

| You want | Guide |
|---|---|
| one smaller or faster replacement at about the same score | [`model-efficiency`](guides/model-efficiency.md) |
| the best model at each of several sizes | [`model-size-frontier`](guides/model-size-frontier.md) |
| a small model that keeps the accuracy of a large one or an ensemble | [`model-distillation`](guides/model-distillation.md) |

**Something more particular.**

| You want | Guide |
|---|---|
| several good models that fail differently, to average | [`model-ensemble-members`](guides/model-ensemble-members.md) |
| to improve a model that is interpretable by design, or a biophysical one | [`model-mechanistic`](guides/model-mechanistic.md) |
| the same output from an algorithm, sooner | [`algorithm-runtime`](guides/algorithm-runtime.md) |
| a bioinformatics method that is more accurate against a truth set | [`bioinformatics-algorithm`](guides/bioinformatics-algorithm.md) |
| a data pipeline that is faster or cheaper | [`data-pipeline`](guides/data-pipeline.md) |

Each goal is a *skill*: an editable file of settings and advice for the agents. Goals can be combined
(a family of distilled students is `model-distillation` with `model-size-frontier`), and you can write
your own. [Edit or write a skill](skills.md).

## How to search: the run type

The run type sets how the budget is shared between trying new designs and improving the ones found.

| Run type | Choose it when | New / crossover / local |
|---|---|---|
| `explore_then_exploit` | you have no reason to choose another | 65 / 10 / 25 for the first 60% of the budget, then 15 / 25 / 60 |
| `refine` | you have a good model and want it better | 10 / 20 / 70 throughout |
| `survey` | the problem is new and you want to see what works | 75 / 10 / 15 throughout |
| `discovery` | evaluations are cheap and you want something unusual | novelty turned up, fewest agent roles |
| `settings_only` | only numbers should change | every move is a settings move |
| `custom` | you want to describe the search yourself | the defaults, plus what you write |

A guide suggests a run type for its goal. Where a skill and a run type set the same thing, the skill's
value is used.

## How much: the budget

The budget is a number of evaluations, where an evaluation is one full training run. Its size changes
what is sensible, and evoloop adjusts its defaults to it.

With about **30**, there is no room for a population. The search builds on the current best, asks for
four proposals per slot so that the one trained is well chosen, and reviews the agents once at the end.

With about **100**, the search keeps up to six families of designs, asks for three proposals per slot,
and reviews the agents half way.

With about **300**, it keeps up to ten families and two proposals per slot. Islands, an archive and a
promotion ladder start to pay at this size.

With **1,000 or more**, the default becomes an archive with writers only and one proposal per slot.

You also set a cap on what the agents may cost, in dollars. `evoloop plan` estimates the cost before
you confirm, and the search stops asking agents when the cap is reached.

## See what a combination comes to

<div class="evo-widget" id="evo-plan-explorer" data-src="../assets/plans.json">Loading the plan explorer…</div>

The panel is worked out by the same code that reads a real brief. Lines marked on the left differ from
the plain default.

## Two more choices worth a minute

**How much the agents decide.** `harnessed`, `guided` or `agentic`: more autonomy means more agent
calls. Left unset, the run type decides. [The agents, and how much they decide](agents.md).

**Who makes it run.** By default code runs the search deterministically. With `harness.conductor:
agent`, an agent runs it and you can talk to it. [Working with the strategist](strategist.md).

Everything else can wait until a result gives you a reason. Any of these can be changed while the
search runs ([Watch and steer a run](steering.md)).
