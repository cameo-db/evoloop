# Commands

Every command is `evoloop COMMAND DIR ...`, where `DIR` is the search folder. Commands that act on a
running or finished search take `--name`, the name you gave it. Commands that change a search take
`--by`, your name, which is recorded with the change.

| To | Commands |
|---|---|
| [set up](#setup) | `init` · `example` · `setup` · `form` · `brief` · `plan` · `estimate` |
| [look things up](#lookup) | `skills` · `menu` · `guide` · `site` |
| [run, or resume](#run) | `run` · `controller` |
| [watch](#monitor) | `status` · `leaderboard` · `show` · `report` |
| [steer](#steer) | `set` · `note` · `withdraw` · `steer` · `chat` · `force` · `stop` |
| [answer the strategist](#strategist-and-agents) | `approve` · `decline` · `lineage` · `review` |
| [bring things in](#imports-and-references) | `import` · `reference` · `rehash` |
| [finish](#export) | `study` |

## Setup

### init

`evoloop init DIR [--source PATH]`

Makes a search folder. With `--source`, copies your project into `DIR/base/`.

```
evoloop init mysearch --source ~/projects/mymodel
```

### example

`evoloop example DIR [--kind classifier|formula]`

Copies a built-in example: a toy model search (the default) or a search for a formula.

```
evoloop example demo
```

### setup

`evoloop setup DIR`

Asks the set-up questions one at a time in the terminal, with a suggested answer where there is one.
Enter accepts what is shown, `b` goes back, `q` saves and stops.

### form

`evoloop form DIR [--out FILE]`

Writes the same questions as a self-contained web page, `setup_form.html`. It ends with an answers file
that `evoloop brief --import` reads.

### brief

`evoloop brief DIR [options]`

Reads and writes the brief. With no option it lists the questions still open.

| Option | Does |
|---|---|
| `--answer FIELD=VALUE` | records an answer; repeatable; the value is read as YAML |
| `--confirm NAME` | records your agreement to the plan; refused while a required answer is missing |
| `--import FILE` | reads an answers file from the form, or any mapping of fields; skills edited in the form are written to the search folder |
| `--next` | the next question as JSON, for an agent to ask |
| `--keep FIELD` | accepts the suggestion or default for one question |
| `--infer` | suggests answers from the machine, the folder and the answers so far |
| `--suggest FIELD=VALUE --because WHY` | proposes an answer for the person to accept or change |
| `--questions [--all]` | the open questions as JSON; `--all` for every field |

```
evoloop brief mysearch --answer budget.evaluations=100 --answer evaluation.noise=0.003
evoloop brief mysearch --confirm "Your Name"
```

### plan

`evoloop plan DIR`

Prints what the search will do at a glance, the warnings, the cost estimate, then every setting with
where its value came from. Read it before confirming.

### estimate

`evoloop estimate DIR [--name N]`

What the agents are likely to cost, at each level of autonomy. With `--name`, projected from a running
search's own calls.

## Lookup

### skills

`evoloop skills [NAME] [--dir DIR] [--search WORDS] [--edit] [--diff] [--merge A,B --name NEW] [--copy DIR] [--json]`

With nothing, lists the skill library by domain. With a name, prints that skill in full; with `--dir`,
the search's own copy of it.

| Option | Does |
|---|---|
| `--search WORDS` | finds skills by what they are for |
| `--edit --dir DIR` | opens the search's copy in `$EDITOR`, then checks it can be used |
| `--diff --dir DIR` | shows how the search's copy differs from the library's |
| `--merge A,B --name NEW --dir DIR` | writes several skills as one file, `DIR/skills/NEW/skill.yaml` |
| `--copy DIR` | writes one skill out as a folder, to start a skill of your own |

```
evoloop skills --search "smaller"
evoloop skills model-efficiency --edit --dir mysearch
evoloop skills --merge model-distillation,model-size-frontier --name my-students --dir mysearch
```

[Edit, merge or write a skill](skills.md).

`--json` prints the library as records. `--markdown` and `--guides DIR` write the documentation's skill
pages.

### menu

`evoloop menu [TOPIC]`

Every option with what it does, and what each preset sets. Topics: `run-types`, `skills`, `autonomy`,
`models`, `effort`, `strategies`, `modes`, `crossover`, `moves`, `spaces`, `harness`, `conductor`,
`coordinator`, `strategist`, `strategist-actions`, `spend`, `reviews`, `guidance`, `defaults`, `fields`,
`all`.

### guide

`evoloop guide [N]`

The defaults evoloop applies for a budget of N evaluations.

### site

`evoloop site [--dir DIR] [--detect] [--write PATH]`

Shows the site file in use: what is particular to this machine. With `--detect`, drafts one from what
the scheduler reports; nothing is submitted.

```
evoloop site --detect --write ~/.config/evoloop/site.yaml
```

## Run

### run

`evoloop run DIR --name N [--max-seconds S]`

Starts a search, or resumes one that stopped (after `evoloop stop`, a crash, or a preempted controller). It
returns when the budget is spent, the search is
stopped, or it pauses for a reason it prints.

```
evoloop run mysearch --name r1
```

### controller

`evoloop controller DIR --name N [--partition P] [--qos Q] [--time T] [--setup LINE] [--python PATH] [--out FILE]`

Writes a Slurm job script that runs the search itself as a job and puts itself back in the queue at its
time limit. For clusters where nothing may run on the login node.

```
evoloop controller mysearch --name r1 --partition cpu --time 1-00:00:00
sbatch mysearch/run_controller_r1.sbatch
```

## Monitor

### status

`evoloop status DIR --name N [--json]`

A few lines: budget used, the best so far, what is held up, what waits for you.

### leaderboard

`evoloop leaderboard DIR --name N [--top 15] [--columns ...]`

The best designs, the baseline and any reference rows. `state` is `full` or `stopped at N%`.

```
evoloop leaderboard mysearch --name r1 --columns test.accuracy speed
```

### show

`evoloop show DIR ID --name N`

One design in full: where it came from, what it changed, what its writer predicted, how it ended. `ID`
is a design (`C12`) or one of its evaluations (`R37`).

### report

`evoloop report DIR --name N`

Rewrites and prints the report from the search's files as they are now.

## Steer

All of these take effect within seconds on a running search, and are recorded with your name.
[Monitor and steer a search](steering.md) explains each.

### set

`evoloop set DIR --name N KEY=VALUE... --by NAME [--reason WHY]`

Changes settings from the next design on.

```
evoloop set mysearch --name r1 schedule.novelty=0.6 budget.evaluations=300 --by "Your Name"
evoloop set mysearch --name r1 'limits={"parameters": {"max": 20000000}}' --by "Your Name"
```

### note

`evoloop note DIR --name N "TEXT" [--roles ROLE...] --by NAME`

Advice the agents read on every call from then on.

```
evoloop note mysearch --name r1 "No attention layers." --roles writer --by "Your Name"
```

### withdraw

`evoloop withdraw DIR --name N --id S4 --by NAME`

Withdraws a note.

### steer

`evoloop steer DIR --name N "WORDS" --by NAME [--yes]`

Turns your own words into setting changes and notes. It shows them first; `--yes` applies them.

### chat

`evoloop chat DIR --name N ["MESSAGE"] --by NAME`

Talks with the agent that runs the search. Needs `harness.conductor: agent`.

### force

`evoloop force DIR --name N --mode MODE [--kind KIND] [--count 3] [--instruction "..."] --by NAME`

Orders the next few moves yourself, ahead of the schedule.

```
evoloop force mysearch --name r1 --mode cross --kind hybrid --count 2 --by "Your Name"
```

### stop

`evoloop stop DIR --name N [--run R12] --by NAME`

Starts nothing more; the search ends when its jobs do. With `--run`, stops one evaluation.

## Strategist and agents

### approve, decline

`evoloop approve DIR --name N --id S14 --by NAME` · `evoloop decline DIR --name N --id S14 --by NAME [--reason WHY]`

Answers a decision of the strategist that is waiting for you.

### lineage

`evoloop lineage DIR --name N --retire L4 --by NAME` (or `--revive L4`)

Retires a lineage, or brings one back. Lineage strategy only.

### review

`evoloop review DIR --name N [--roles ROLE...] --by NAME`

Has the assessor review the agents now.

## Imports and references

### import

`evoloop import DIR --name N (--from-run PATH | --from-study FILE) [--top 3 | --designs ID ...] [--as-ideas] --by NAME`

Brings designs in from an earlier run, or from a study file (this loop's `study.json`, or one from CAMEO; a
path or a link). A design that fits this project is trained here and built on. One from another project
is kept as an idea and shown to the writers. [Start from earlier designs](warm-start.md).
| --designs C12 ...] --by NAME`

Brings designs from an earlier search in, to be trained here and built on.

### reference

`evoloop reference DIR --name N --label LABEL --score S [--metric test.x=v] [--note TEXT] --by NAME`

Adds a row to the leaderboard for a model that is not part of the search: a published baseline, a
teacher. `--from-run PATH [--top N]` takes the best of an earlier search.

```
evoloop reference mysearch --name r1 --label "teacher ensemble" --score 0.912 --by "Your Name"
```

### rehash

`evoloop rehash DIR --name N --by NAME --reason WHY [--moves-scores]`

Records that a change you made to the frozen code or the evaluator during a search is intended. With
`--moves-scores`, a new comparison period begins.

## Export

### study

`evoloop study DIR --name N`

Writes `study.json` and says which star it is on course for.
[Save and deposit the study](study.md).
