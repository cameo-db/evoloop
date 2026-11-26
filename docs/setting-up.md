# Set up a search by hand

An agent normally does this for you: see [Get started](get-started.md). This page is the same
procedure step by step, for checking an agent's work or setting a search up yourself. There are five
steps: mark what may change, write the evaluator, answer the questions, read and confirm the plan, then
dry-run and run.

## Search folder

```
evoloop init mysearch --source path/to/project
```

copies your project into a search folder. Your original is never touched.

| In `mysearch/` | What it is |
|---|---|
| `base/` | the copy of your code, where you mark what may change |
| `adapter/run.py` | the evaluator: trains one design and writes its score |
| `task.md` | what the agents are told about the problem |
| `brief.yaml` | the answers that set up the search |

## 1. Mark the editable code

In `base/`, put a pair of comment lines around each part that may change:

```python
# EVOLVE-BLOCK-START name=trunk kind=structure role=trunk
class Trunk(nn.Module):
    ...
# EVOLVE-BLOCK-END

# EVOLVE-BLOCK-START name=fit kind=params role=optimizer
PARAMS = {"lr": 3e-4, "batch_size": 128}
# EVOLVE-BLOCK-END
```

Each start line has three labels:

- `name` identifies the block. It must be unique.
- `kind` is `structure` or `params`. A `structure` block is code that an agent rewrites. A `params` block
  is one dictionary of hyperparameters; an agent can change its values, and so can a sampler with no
  agent involved.
- `role` is your own word for what the block is (`trunk`, `head`, `loss`, `optimizer`, `augmentation`).
  Several blocks can share a role. The brief opens or closes blocks by role.

Mark generously, once. The brief then says which roles are open in a given search, so the same
marked-up project serves a search over settings only, over one module, or over the whole architecture.
Marking the trunk and the head as separate blocks also lets a crossover combine the trunk of one design
with the head of another.

Everything outside the markers is frozen. evoloop checks it on every start and will not continue if it
changed.

## 2. Write the evaluator

`adapter/run.py` trains one design and writes `result.json` with its score. `evoloop init` writes a
template that saves its state as it trains and resumes when its job is started again; [Write the evaluator](evaluator.md) has a complete example and how to test it by hand.

Then write `task.md`: a page telling the agents what the problem is, what the data looks like, what the
score means, and anything you already know works or does not. They read it on every call and see
nothing else of your project except the marked blocks.

## 3. Answer the setup questions

```
evoloop setup mysearch
```

asks one question at a time, with choices and where you are in the list. Every question but two comes
with a suggested answer or a default, and Enter accepts it. The goal and the length of a training run
have none and must be answered.

| Question | Suggested answer or default |
|---|---|
| What is being improved, and why? | none: one or two sentences, read by every agent |
| Is a higher score better, or a lower one? | from the metric your goal names |
| What is the score called? | from the goal, such as `pearson_r`; otherwise `score` |
| Which validation metrics should be tracked, and how is each computed? | the score; add the others as `name: how it is computed` |
| Which test evaluations should be run on every design? | a held-out copy of the score; add as many as you want to follow |
| What data is the search run on? | not recorded |
| How is the data split into training, validation and test sets? | not recorded |
| What share of the training data should each training run use? | all of it |
| How many models may be trained in all? | 100 |
| How should the search spend its evaluations? | `explore_then_exploit`: [Choose a skill and a run type](which-search.md) |
| Which goal should the agents be given guidance for? | the skill your goal describes, or none |
| Which parts of the code may the search change? | the model blocks, with the training recipe fixed |
| Are there hard limits every design must stay within? | none; given as `parameters <= 2000000` |
| How much of the search should the agents decide? | `guided`: [Agents](agents.md#autonomy-levels) |
| How long is one training run? | none: in your evaluator's own unit, such as epochs |
| How much does the score differ between two fits of the same model? | 0.001: [Noise floor](noise.md) |
| Should weak training runs be stopped early? | the weaker half of new designs stop halfway: [Early stopping](early-stopping.md) |
| What should be done about the baseline? | train it inside the search |
| How many models may train at the same time? | the GPUs on this machine, or 4 on a cluster |
| Where do the training jobs run? | Slurm if the machine has it, with the partition and QoS of your site file |
| Should each design be its own job, or should one job hold all the GPUs? | one job per design, submitted as GPUs come free: [Getting GPUs](servers.md#getting-gpus) |
| What time limit should each job ask for? | the limit of your site file, else two days; a short limit starts sooner once the evaluator resumes |
| How are the agents called? | Claude Code or the API, whichever is set up here |
| Which model should the agents run on, and how hard should it reason? | [Models and prices](models.md) |
| What is the most the agents may cost? | the upper end of the cost estimate |
| When should the agents be reviewed? | halfway and at the end: [Audit the agents](auditing.md) |

The suggestions are starting points for someone who says nothing. Replace them where you know the
project better.

There are other ways to answer the same questions. `evoloop form mysearch` writes a self-contained web
page to fill in; save the answers file it gives you and run `evoloop brief mysearch --import
PATH/TO/answers.json`. Or edit `brief.yaml` directly: [Brief fields](fields.md) lists every field.

### Skill files

Choosing a skill copies its file to `mysearch/skills/NAME/skill.yaml`. That copy is what the search
reads. `evoloop setup` shows what it sets and offers to open it in your editor (`e`) or, with several
skills, to merge them into one file (`m`). The form shows each chosen skill as an editable text box.
Change the settings or the text the agents are given, then read the plan: it shows the effect.
[Edit or merge a skill](skills.md) · [Write a skill](custom-skills.md).

## 4. Review and confirm the plan

```
evoloop plan mysearch
```

The plan opens with what the search will actually do. For example:

```
At a glance
  Optimizing:      explore_then_exploit, skill model-performance
  Score:           pearson_r, higher is better; also tracked: count_r2
  Test evals:      test_pearson_r, test_count_r2, other_cell_line_r (run on every design, kept from the agents)
  Designs:         written by an agent; settings moves by an agent
  Agents:          writer (about 109 calls), analyst (about 13 calls), strategist (about 10 calls)
  Model:           claude-opus-5-5, effort medium
  Selection:       lineage
  Data:            K562 ATAC-seq; split: chromosomes 8 and 9 held out for test, 10 for validation
  Runs on:         Slurm, one job per design, submitted as GPUs come free, partition gpu, 8 at once, 4:00:00 per job (site file: our-cluster)
  Early stopping:  new designs screened at 50%, the best 50% go on
  Budget:          100 evaluations of 30 epochs; agents capped at $40
```

Then come warnings about choices that work against each other, an estimate of what the agents will
cost, and every setting with where its value came from. Read the first block and the warnings; the long
list is for looking things up.

When it says what you want:

```
evoloop brief mysearch --confirm "Your Name"
```

Nothing runs before this. Your name and a digest of what you agreed to are recorded, and a brief that
is edited afterwards has to be confirmed again.

Confirmation is refused while a setup question has not been asked, and the refusal lists each one with
the value it would be left at. Answer them, or add `--accept-defaults` to take the listed values.

## 5. Dry run and launch

First check the evaluator on its own. `evoloop check mysearch` trains your unchanged code once, kills
and restarts it, and asks it to stop, and reports whether it resumed and whether it stopped with a
score: [Evaluator check](evaluator.md#evaluator-check).

Then prove the plumbing with scripted proposals and a tiny budget, which costs nothing:

```
evoloop brief mysearch --answer agents.backend=stub --answer budget.evaluations=4 --confirm "Your Name"
evoloop run mysearch --name dry
```

If four designs train and a report appears, set the real backend and budget, confirm again, and run:

```
evoloop run mysearch --name r1
```

On a cluster, each design is its own job, and the search itself can run as a small job too.
[Run on a cluster](servers.md) covers describing your machine once so that every search uses it.

## Setting precedence

You answer a few questions and evoloop fills in the rest, from the first of these that has a value:

1. a change you made while the search was running;
2. the brief;
3. the skill;
4. the level of autonomy;
5. the run type;
6. the guidance for the size of your budget;
7. the default.

`evoloop plan` shows which of these each value came from.

## Next steps

[Monitor and steer a search](steering.md) once it is going.
