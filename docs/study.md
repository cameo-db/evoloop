# Save and deposit the study

Every search ends with one JSON file, `study.json`, holding every model, training recipe and run. It is in
the format of [CAMEO](https://cameo-db.github.io), a public database of models, how they were trained,
and how they performed, so a finished search can be deposited as one entry.

The exchange goes both ways: a study file from CAMEO can seed a new search.
[Start from earlier designs](warm-start.md).


## 1. Write the file

```
evoloop study mysearch --name r1
```

writes `mysearch/runs/r1/study.json` and prints the star the file is on course for, with what stands in
the way of the next one. The same file is written automatically whenever a run stops or ends, so this
command is for refreshing it after you have filled in more of the brief.

## 2. Fill in what the search cannot know

These come from the brief, and they decide the star:

| In the brief | Why |
|---|---|
| `data.accession` | the dataset's DOI, accession or link. Without it the entry gets no star |
| `data.name`, `data.splits`, `data.preprocessing` | what the data is and how it was divided and prepared; needed for Gold |
| `depositor.name`, `depositor.orcid`, `depositor.lab`, `depositor.institution` | who is depositing |
| `license` | `MIT` unless you choose another |

And these come from your evaluator, in `result.json` (see [The evaluator contract](project-contract.md)):

| In the result | Why |
|---|---|
| `captured.environment` | package versions and devices; needed for Gold |
| `captured.training` | the loss, schedule and stopping rule as the script built them; needed for Gold |
| `inference_speed`, `parameters` | for every model with a finished run; needed for Gold |
| `diagnostics.hidden` | held-out results: stored in the file, never shown to the agents |

Run `evoloop study` again after any change; it rewrites the file from the run's records.

## 3. Check it with the CAMEO kit

The kit is two files, kept in one folder:
[`cameo.py`](https://cameo-db.github.io/kit/cameo.py) and
[`rules.json`](https://cameo-db.github.io/kit/rules.json).

```
python3 cameo.py check mysearch/runs/r1/study.json
python3 cameo.py check mysearch/runs/r1/study.json --json     # every gap, with how to fix it
```

A complete file gives:

```
Sufficient? experiment: yes · model: yes · training: yes · performance: yes
Star: Gold
RESULT: ready to stage.
```

A file with a "no" is still accepted, with a lower star. evoloop does not run this check itself.

## 4. Deposit it

On the CAMEO site, choose
[Deposit a study](https://cameo-db.github.io/#/deposit) and follow the steps there with your `study.json`. Datasets and trained weights
stay outside the file; it links to them.

What the stars mean:

| Star | The file has |
|---|---|
| Gold | all four parts complete |
| Silver | model code, a link to the dataset, and for every run its training settings and seed |
| Bronze | model code, results and a link to the dataset |
| none | no link to the dataset, or no model code |

## What is in the file


`study.json` is written when a run stops or ends, and by `evoloop study`. It is one JSON file in the CAMEO entry
format, version 0.4, with four parts:

| Part | Holds |
|---|---|
| `experiment` | the objective, the data, the evaluation, the environment, the search, the conclusions |
| `models` | each architecture, with its code as text |
| `training` | each recipe: its settings and the training code as text |
| `runs` | each run: model, recipe, seed, history, performance |

The run's own stores are already in that shape, so the file is an export. What the run does not know
is written as `"not_reported"`; nothing is filled in. `evoloop study` prints the star the file is on
course for and what stands in the way of the next:

- no dataset link (`data.accession`): no star;
- the environment, inference speed, or the recipe's loss and stopping rule not reported by the adapter
  (`captured`, `inference_speed` in `result.json`): Silver rather than Gold.

Steering, modes and agent spend have no field in the format. They stay in the ledger beside the file,
and `experiment.search.method` says how many steering entries the run had.

