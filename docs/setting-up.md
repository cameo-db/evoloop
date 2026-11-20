# Setting up a search

```
evoloop init mysearch --source path/to/project
```

makes a search folder:

| In the folder | What it is |
|---|---|
| `brief.yaml` | the form that sets up the search |
| `task.md` | what the agents are told about the problem |
| `base/` | a snapshot of your code, where you mark what may change |
| `adapter/run.py` | how one design is trained and scored |

Your original code is never touched: the search works on the snapshot.

## 1. Mark the code

In `base/`, put comment lines around what may change, and say what part of the system each block is:

```python
# EVOLVE-BLOCK-START name=trunk kind=structure role=trunk
class Trunk(nn.Module):
    ...
# EVOLVE-BLOCK-END

# EVOLVE-BLOCK-START name=fit kind=params role=optimizer
PARAMS = {"lr": 3e-4, "batch_size": 128}
# EVOLVE-BLOCK-END
```

- `kind=structure` is code an agent rewrites.
- `kind=params` is exactly one assignment of a dict of numbers, booleans or strings.
- `role` is your own word for the part: `stem`, `trunk`, `heads`, `loss`, `optimizer`,
  `augmentation`. It defaults to `model` for structure and `settings` for params.

Mark the code once. The brief then says which roles are open in a given run (`space.preset`,
`space.roles`), so one marked-up project serves a settings search, a search over one module, and an
open architecture search. Blocks whose role is in `space.recipe_roles` make up the training recipe;
the other structure blocks make up the model.

Several blocks by role are worth the trouble: the `block_swap` crossover can then move the trunk of one
design onto the heads of another without an agent.

Everything outside the markers is frozen and checked by hash. A run refuses to go on if `base/` or
`adapter/` changed after it started.

## 2. Write `task.md` and the adapter

`task.md` says what the problem is, what each block is for, and what a good solution looks like.
Agents see it, the open blocks and the visible results, and nothing else of your code.

`adapter/run.py` trains one design and writes its result. See [The project's code](project-contract.md).

## 3. Fill in the brief

By hand in `brief.yaml`, or by question and answer:

```
evoloop brief mysearch                  # what is still to ask
evoloop brief mysearch --questions      # the same as JSON, for an agent to ask the person
evoloop brief mysearch --answer budget.evaluations=100 --answer run.type=explore_then_exploit
```

Ten fields are always asked when empty:

| Field | Question |
|---|---|
| `objective.goal` | What is being improved, and why? |
| `objective.direction` | Is a higher score better, or a lower one? |
| `run.type` | What kind of search? |
| `budget.evaluations` | How many models may be trained in all? |
| `evaluation.allowance` | How long is one training run? |
| `evaluation.noise` | How much does the score differ between two fits of the same model? |
| `baseline.mode` | Train the baseline, import a finished fit, or skip it? |
| `compute.gpus` | How many models may train at once? |
| `agents.backend` | Which agent backend? |
| `budget.model_dollars` | What is the most the agents may cost? |

Every other field takes its value from the first of these that gives one:

1. the brief (what you set)
2. the run type
3. the guidance for the size of the budget
4. the default

[Fields of the brief](fields.md) lists them all. `evoloop menu` prints the choices and the presets.

With `run.type: custom`, describe the search in `run.description`; where you set nothing, the guidance
and the defaults apply, and your description is kept as the first note the agents read.

## 4. Read the plan and confirm

```
evoloop plan mysearch
```

prints every setting grouped by where it came from, and warnings about choices that work against each
other (an archive on 30 models, a wide search space on a small budget, a model with no price while a
dollar cap is set). A warning never stops a run.

```
evoloop brief mysearch --confirm "Your Name"
```

records your agreement and a digest of what you agreed to. A run does not start on a brief that was
changed after it was confirmed.

## Guidance by size of budget

`evoloop guide 100` prints it for one size; the [menu](menu.md#budget-guidance) has the whole table.

| | about 30 | about 100 | about 300 | 1,000 or more |
|---|---|---|---|---|
| Suggested strategy | greedy | lineage | lineage | archive |
| Lineages kept | 3 | 6 | 10 | (cells) |
| Runs per new lineage | 1 | 2 | 2 | 2 |
| Crossover kinds | graft | graft, hybrid | all three | all three |
| Novel share of new designs | 0 | 0.15 | 0.33 | 0.33 |
| Proposals per slot | 4 | 3 | 2 | 1 |
| Reviews | end | halfway | quarterly | on demand |

A named run type keeps its own strategy; when the guidance suggests another, the plan says so. These
are rules of thumb, not measurements.

## 5. Dry-run, then run

Set `agents.backend: stub` and run a few models first: it shows that the adapter, the markers and the
job settings work before any agent is paid. Then:

```
evoloop run mysearch --name r1
```

The same command continues a run that was stopped.
