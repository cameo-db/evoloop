# Commands

`<dir>` is a search folder; `--name` is a run in it. Commands that change a run take `--by`, the name of
the person asking, which is recorded in the ledger, and an optional `--reason`.

## Setting up

| Command | Does |
|---|---|
| `evoloop init <dir> [--source PATH]` | makes a search folder; with `--source`, copies the code to `base/` |
| `evoloop example <dir>` | copies the built-in example to a new folder |
| `evoloop setup <dir>` | asks the questions one at a time in the terminal, with suggestions and a count of where you are |
| `evoloop form <dir> [--out FILE]` | writes the questions as a self-contained HTML form (`setup_form.html`) |
| `evoloop brief <dir> --import FILE` | reads the answers file the form gives, or any mapping of fields |
| `evoloop brief <dir> --next` | the next question as JSON, for an agent to ask one at a time |
| `evoloop brief <dir> --keep FIELD` | leaves a question as shown: accepts its suggestion, or its default |
| `evoloop brief <dir> --infer` | suggests answers from the machine, the folder and the answers so far |
| `evoloop brief <dir> --suggest FIELD=VALUE --because WHY` | proposes an answer for the person to accept or change |
| `evoloop brief <dir>` | lists what the brief still lacks |
| `evoloop brief <dir> --questions [--all]` | the same as JSON, for an agent to ask the person; `--all` for every field |
| `evoloop brief <dir> --answer FIELD=VALUE` | records an answer (repeatable; the value is read as YAML) |
| `evoloop brief <dir> --confirm NAME` | records the person's agreement; refused while a required field is empty |
| `evoloop plan <dir>` | every setting, grouped by where it came from, and the warnings |
| `evoloop menu [topic]` | every choice a run can make, the presets, and every field; topics: `run-types`, `autonomy`, `models`, `effort`, `strategies`, `modes`, `crossover`, `moves`, `spaces`, `harness`, `coordinator`, `strategist`, `strategist-actions`, `spend`, `reviews`, `guidance`, `defaults`, `fields` |
| `evoloop guide [N]` | the guidance for a budget of N evaluations |
| `evoloop skills [NAME] [--copy DIR]` | the kinds of optimisation a search can be set up for; one in full; or one written out as a folder to edit |
| `evoloop estimate <dir> [--name N]` | what the agents are likely to cost, at each level of autonomy; with `--name`, projected from a run's own calls |

## Running

| Command | Does |
|---|---|
| `evoloop run <dir> --name N` | starts a run, or continues one that stopped |
| `evoloop status <dir> --name N [--json]` | where the run stands, in a few lines |
| `evoloop leaderboard <dir> --name N [--top 15] [--columns ...]` | the best designs, the baseline and the reference rows |
| `evoloop show <dir> --name N R37` | one run in full: where it came from, what it changed, how it ended |
| `evoloop controller <dir> --name N [--partition P] [--qos Q] [--time T] [--setup LINE]` | writes a Slurm job script that runs the search and requeues itself at its time limit |
| `evoloop report <dir> --name N` | the run's report, from its records as they are now |
| `evoloop study <dir> --name N` | writes `study.json` and says which star it is on course for |

## Steering

| Command | Does |
|---|---|
| `evoloop set <dir> --name N KEY=VALUE... --by NAME` | changes settings; applies to the next design |
| `evoloop note <dir> --name N "TEXT" [--roles R...] [--from-review V3] --by NAME` | a standing note the agents read |
| `evoloop withdraw <dir> --name N --id S4 --by NAME` | withdraws a note |
| `evoloop steer <dir> --name N "WORDS" --by NAME [--yes]` | your words turned into changes and notes; shown first, applied with `--yes` |
| `evoloop chat <dir> --name N ["WORDS"] --by NAME` | talk with the agent that runs the search (`harness.conductor: agent`); what it decides is checked and recorded |
| `evoloop stop <dir> --name N --by NAME` | starts nothing more; the run ends when its jobs do |
| `evoloop stop <dir> --name N --run R12 --by NAME` | stops one run |
| `evoloop review <dir> --name N [--roles R...] --by NAME` | has the assessor review the agents now |
| `evoloop approve <dir> --name N --id S14 --by NAME` | says yes to a decision of the strategist that waits for you |
| `evoloop decline <dir> --name N --id S14 --by NAME` | says no to it |
| `evoloop lineage <dir> --name N --retire L4 --by NAME` | sets a lineage aside; `--revive L4` brings one back (lineage strategy) |
| `evoloop rehash <dir> --name N --by NAME --reason WHY [--moves-scores]` | records that a change to `base/` or `adapter/` during a run is meant |
| `evoloop force <dir> --name N --mode M [--kind K] [--count 3] [--instruction "..."] --by NAME` | orders the next slots yourself |
| `evoloop import <dir> --name N --from-run PATH [--top 3 | --designs C12 ...] --by NAME` | brings designs from an earlier run in, to be fitted here |
| `evoloop reference <dir> --name N --label L --score S [--metric test.x=v] --by NAME` | adds a model to compare with to the leaderboard; `--from-run PATH` takes an earlier run's best |

`evoloop set` refuses at once a setting that cannot change in a run, or a value of the wrong kind. A
request that passes that check and cannot be carried out when the controller reads it is recorded in
the ledger as refused, with the reason.
