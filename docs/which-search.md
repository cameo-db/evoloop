# Choose a skill and a run type

Two choices shape a search.

- **The skill** says what you are optimizing: a higher score, a distilled student, a faster algorithm.
  It brings settings and agent guidance for that goal, so you do not have to write them yourself. It is
  optional. In the brief it is `run.skill`.
- **The run type** says how the training runs are spent: exploring widely, refining one design, or
  exploring first and refining later. Every search has one. In the brief it is `run.type`.

```yaml
run:
  skill: model-performance
  type: explore_then_exploit
budget:
  evaluations: 100
```

If you are unsure, start with those three lines.

## Skills

A skill is a file with instructions for the agents, settings suited to the task, and the list of things
your scoring script must report. Each skill's page shows what it sets, the exact text it sends to the agents,
and the file itself, with a link to it in the repository.

=== "Models"

    | Skill | Use it to | The agent works on |
    |---|---|---|
    | [`model-performance`](guides/model-performance.md) | get the best score | the architecture |
    | [`model-training-recipe`](guides/model-training-recipe.md) | train a fixed architecture better | loss, optimizer, schedule, augmentation |
    | [`settings-tuning`](guides/settings-tuning.md) | tune hyperparameters | architecture and training hyperparameters, trial by trial |
    | [`model-finetuning`](guides/model-finetuning.md) | adapt a pretrained model | what to freeze, the head, learning rates by layer |

=== "Smaller and faster"

    | Skill | Use it to | The agent works on |
    |---|---|---|
    | [`model-efficiency`](guides/model-efficiency.md) | shrink the model you have | a cheaper student, distilled from your model |
    | [`model-distillation`](guides/model-distillation.md) | distil an ensemble or a larger model | the student and its training against the teacher |
    | [`model-size-frontier`](guides/model-size-frontier.md) | get the best model at several sizes | one design per size band |

=== "Algorithms and pipelines"

    | Skill | Use it to | The agent works on |
    |---|---|---|
    | [`algorithm-runtime`](guides/algorithm-runtime.md) | make code faster with the same output | the algorithm, then repeated work, then inner loops |
    | [`data-pipeline`](guides/data-pipeline.md) | make a pipeline faster or cheaper | what is read, how often data moves, step order |
    | [`bioinformatics-algorithm`](guides/bioinformatics-algorithm.md) | improve accuracy against a truth set | the model of the data and the hard cases |

=== "Other"

    | Skill | Use it to | The agent works on |
    |---|---|---|
    | [`model-ensemble-members`](guides/model-ensemble-members.md) | find models that fail differently | designs with different inductive biases |
    | [`model-mechanistic`](guides/model-mechanistic.md) | improve an interpretable or biophysical model | the form of each term, with every parameter keeping its meaning |
    | [`settings-tuning-bayesian`](guides/settings-tuning-bayesian.md) | tune hyperparameters with no agent calls | nothing: a built-in Bayesian optimizer (TPE) picks the values |

Skills are plain files. When you choose one during setup, it is copied to `mysearch/skills/`, and the
search reads that copy. You can edit it before you confirm, and at any time after. Two skills can be
combined (`skill: [model-distillation, model-size-frontier]`) or merged into one file.
[Edit, merge or write a skill](skills.md).

### Effect on the loop

| Stage | What the skill supplies |
|---|---|
| Propose a change | instructions shown to the agent on every call: what to try first, what to avoid, what a given result means |
| Evaluate it | the measurements your evaluator must report (score, and for some skills size, speed or an error profile) |
| Choose what to try next | the parent rule and the mix of moves, for example a score-versus-size front for `model-efficiency` |

## Run types

| `run.type` | Evaluations go to | Use when |
|---|---|---|
| `explore_then_exploit` | new designs for the first 60%, then mostly edits of the best | default |
| `refine` | edits of existing designs (70%) | you already have a good model |
| `survey` | new designs (75%) | the problem is new to you |
| `discovery` | new and unusual designs, with writers only | evaluations are cheap |
| `settings_only` | hyperparameter changes only | nothing structural should change |

Where a skill and a run type set the same thing, the skill's value is used.

## Budget

`budget.evaluations` counts full training runs. Some defaults scale with it.

| Evaluations | Lineages kept | Proposals per slot |
|---|---|---|
| about 30 | 3 | 4 |
| about 100 | 6 | 3 |
| about 300 | 10 | 2 |

Below about 40 evaluations a population does not have time to form. Set `strategy.mechanism: greedy`
so that every edit builds on the current best. The run types do not do this for you, and `evoloop plan`
warns when it applies.

`budget.model_dollars` caps what the agents may cost. `evoloop plan` prints an estimate before you
confirm. [Budget and cost](cost.md).

## Preview a search

<div class="evo-widget" id="evo-plan-explorer" data-src="../assets/plans.json">Loading the preview…</div>

The preview is generated by the code that reads a real brief. The label next to a value says which
setting it came from. `evoloop plan` prints the same for your project.

## Autonomy

By default evoloop's code runs the search and agents write designs and summaries of the results.
`harness.autonomy` changes that: `harnessed` gives agents the least to decide, `agentic` the most, and
each step up costs more agent calls. [Agents](agents.md).
