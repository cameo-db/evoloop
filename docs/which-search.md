# Which search should I run?

Pick what you want and how to spend the budget. The panel shows the search evoloop would run.

## Preview your search

<div class="evo-widget" id="evo-plan-explorer" data-src="../assets/plans.json">Loading the preview…</div>

The panel is worked out by the same code that reads a real brief, and `evoloop plan` prints the same
for yours. The small label beside a value says where it came from: the goal, the run type, the size of
the budget, or the default.

## What you want: the goal

Each goal is a different search with its own guide. The guide gives a brief to start from, says what
your scoring script has to report, and explains how to read the result.

You have a model and a task:

| You want | Guide |
|---|---|
| the best score you can get, with the architecture open | [`model-performance`](guides/model-performance.md) |
| a better score from the same architecture, by changing the loss, optimizer or augmentation | [`model-training-recipe`](guides/model-training-recipe.md) |
| the learning rate, weight decay or widths set better, with nothing else changed | [`settings-tuning`](guides/settings-tuning.md) |
| to adapt a pretrained model | [`model-finetuning`](guides/model-finetuning.md) |

You have a model that works and costs too much:

| You want | Guide |
|---|---|
| one smaller or faster replacement at about the same score | [`model-efficiency`](guides/model-efficiency.md) |
| the best model at each of several sizes | [`model-size-frontier`](guides/model-size-frontier.md) |
| a small model that keeps the accuracy of a large one or an ensemble | [`model-distillation`](guides/model-distillation.md) |

Something more particular:

| You want | Guide |
|---|---|
| several good models that fail differently, to average | [`model-ensemble-members`](guides/model-ensemble-members.md) |
| to improve a model that is interpretable by design, or a biophysical one | [`model-mechanistic`](guides/model-mechanistic.md) |
| the same output from an algorithm, sooner | [`algorithm-runtime`](guides/algorithm-runtime.md) |
| a bioinformatics method that is more accurate against a truth set | [`bioinformatics-algorithm`](guides/bioinformatics-algorithm.md) |
| a data pipeline that is faster or cheaper | [`data-pipeline`](guides/data-pipeline.md) |

Behind each goal is a *skill*: a file of settings and advice for the agents that you can edit. Goals
can be combined (a family of distilled students is `model-distillation` with `model-size-frontier`),
and you can write your own. [Edit or write a skill](skills.md).

## How to spend the budget: the run type

| Run type | In the brief | Choose it when | New / crossover / local |
|---|---|---|---|
| Explore, then refine | `explore_then_exploit` | you have no reason to choose another | 65 / 10 / 25 for the first 60% of the budget, then 15 / 25 / 60 |
| Refine what works | `refine` | you have a good model and want it better | 10 / 20 / 70 throughout |
| Explore broadly | `survey` | the problem is new and you want to see what works | 75 / 10 / 15 throughout |
| Look for something unusual | `discovery` | evaluations are cheap | novelty turned up, writers only |
| Settings only | `settings_only` | only numbers should change | every move is a settings move |
| Your own | `custom` | you want to describe the search yourself | the defaults, plus what you write |

Each guide suggests a run type for its goal. Where a goal and a run type set the same thing, the goal's
value is used.

## How much: the budget

The budget is a number of evaluations, where one evaluation is one full training run. evoloop adjusts
some defaults to its size:

| About | Families kept | Proposals per slot | Reviews of the agents |
|---|---|---|---|
| 30 | 3 | 4 | once, at the end |
| 100 | 6 | 3 | half way |
| 300 | 10 | 2 | every quarter |

At about 30 evaluations there is little room to keep several families going. The budget guidance
suggests building on the current best design (`strategy.mechanism: greedy`), but a run type sets the
parent rule too, and the run type wins. So with the default run type the preview above still shows
several families at 30, and `evoloop plan` warns about it. To follow the guidance, set
`strategy.mechanism: greedy` yourself.

Islands, an archive and a promotion ladder start to pay from about 300 evaluations.

You also set a cap on what the agents may cost, in dollars. `evoloop plan` estimates the cost before you
confirm ([Budget and cost](cost.md)).

## Who controls the search?

By default code runs the search and agents only write designs and lessons. You can hand more over.
A level of autonomy (`harnessed`, `guided`, `agentic`) decides how much the agents choose, and each
step up adds agent calls: change it in the preview and watch the call count under "Agent calls by
role". [The agents, and how much they decide](agents.md).

You can also have an agent run the search and talk to it (`harness.conductor: agent`).
[Working with the strategist](strategist.md).

## What can change later

The budget, the parent rule, the split between new designs and local moves, the goal and the limits can
all be changed while a search runs. The objective, the direction of the score, the agent backend and
the scheduler are fixed when it starts. [Brief fields](fields.md) marks each setting, and
[Watch and steer a run](steering.md) has the commands.
