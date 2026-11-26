# For an agent helping someone use evoloop

evoloop searches over marked blocks of a project's code. `docs/index.md` is the overview and
`docs/setting-up.md` the procedure. This file is about how to work with the person.

## What the person decides, and what you do

evoloop is meant to be set up by you together with the person. They should not have to read the reference or
learn the commands, and you do not fill in the brief for them: **every entry of the brief that a set-up question
covers is put to the person**, with your suggested answer and its reason. `evoloop brief DIR --next` gives the
questions one at a time. Most take one word from the person ("fine"), because you came with a suggestion. These
are the ones that deserve a real conversation:

1. **What to optimize.** A better score, a smaller model, tuned settings, a faster algorithm: these are different
   searches. `evoloop skills` lists them and `evoloop skills --search WORDS` finds one; `docs/guides/` has a
   starting configuration for each.
2. **What may change.** Propose which parts of their code to mark as open blocks, and say what stays frozen.
3. **What is optimized and what is tracked.** The name of the metric that is optimized (`objective.metric`) and how
   it is computed; the other validation metrics to track (`evaluation.metrics`); and the test evaluations to run on
   every design (`evaluation.test_metrics`). Ask for the test evaluations by name: people usually want many of
   them, on the held-out split and on other datasets, and which evaluations count as validation and which as test
   is their decision. Read the evaluator's `result.json` and propose all three from it: what is under
   `diagnostics` is a validation metric, what is under `diagnostics.hidden` is a test evaluation. If the person
   names an evaluation the evaluator does not compute, add it to the evaluator before the dry run.
4. **The data.** What it is called, how it is split into training, validation and test (`data.name`,
   `data.splits`), and what share of the training data each run uses (`data.fraction`). Read the data loader and
   propose them.
5. **How much to spend**: evaluations (their compute) and agent dollars.
6. **Hard limits**, if any (`limits`): the largest size or slowest speed they would accept. When the goal says
   "without a larger model", propose the baseline's parameter count as the limit.
7. **The training run**: its length (`evaluation.allowance`, from the training script), whether weak runs are
   stopped early (`evaluation.screen_keep`), and what is done about the baseline.

Also ask whether the search should start from earlier designs: an earlier run of theirs, or a study from
[CAMEO](https://cameo-db.github.io) on the same or another dataset (`evoloop import`, `docs/warm-start.md`).

The brief has many more settings than questions. For those, keep the default unless you have evidence for another
value, and say so in one line.

Your part before the questions:

- **The machine.** Run `evoloop site`. If no site file is in use, run `evoloop site --detect`, go through the draft
  with the person, and ask only for what the machine cannot report: the account to charge, how their environment
  is activated, and which queues must not be used. Save it as `~/.config/evoloop/site.yaml`. Its `rules` are
  printed in every plan: follow them (for instance, no compute on a login node).
  If the machine has a scheduler other than Slurm, say so and offer two routes: run designs as local processes
  inside an allocation the person holds (`compute.scheduler: local`), or add the scheduler as a class in
  `evoloop/jobs.py` with `submit`, `state`, `cancel` and `shutdown`, modelled on the Slurm class, registered in
  `jobs.make` and in the choices for `compute.scheduler` in `evoloop/form.py`. Prove either with a dry run.
- **The code.** `evoloop init DIR --source PROJECT` copies the project. Mark the blocks in `DIR/base/` with
  `# EVOLVE-BLOCK-START name=... kind=structure|params role=...` and `# EVOLVE-BLOCK-END`, write `DIR/task.md`
  (what the agents are told) and `DIR/adapter/run.py` (runs one design, writes `result.json`): see
  `docs/project-contract.md`. Show the person what you marked and what the evaluator reports.
  In `task.md`, describe the problem, the data and what the score means, and say what is known to work or fail.
  Do not present one published model as the starting point or list only changes to it: the writers take that
  literally and every design becomes a variant of it. Where you name ideas, name different kinds of model.
  Write the evaluator so that it resumes: the template saves its state after every step with `adapter/evojob.py`
  and continues from it when the job is started again. Keep that, and save the best weights apart from the latest
  ones, so that a step that diverges cannot cost the run its score.
- **The jobs.** On a cluster the default is one job per design, submitted as GPUs come free
  (`compute.allocation: per_design`), with a short time limit. Small, short jobs start sooner, and a run that
  reaches the limit or is preempted continues in another job. Do not reserve a block of GPUs, hold an allocation or
  build a job array on your own initiative: put the choice to the person (`compute.allocation`), and use `block`
  only when they pick it. Propose a time limit of a few hours once the evaluator resumes; if it cannot resume, the
  limit has to cover a whole training run, and say so. Do not write designs ahead or queue a batch of them: the
  controller writes each design when a job is about to be free and replaces one that results overtake while it waits.
- **The evaluator check.** `evoloop check DIR` trains the unchanged code once where the jobs will run, kills and
  restarts it, and asks it to stop. Fix what it reports before going on, and tell the person what it found: an
  evaluator that begins again after a restart needs a time limit longer than a whole run, and one that ignores a
  stop loses the score of every design stopped early.
- **A dry run.** Before any paid agent: `agents.backend: stub` and a budget of a few evaluations, to prove the
  jobs and the search loop work on this machine.

## Setting up a search: propose, then ask one question at a time

The questions come from the tool, not from you. **Before the first question, propose your best guess for
every question you have evidence for**, each with its reason:

    evoloop brief DIR --infer                      # the tool's own guesses: the machine, the folder, the budget
    evoloop brief DIR --suggest objective.direction=minimize --suggest evaluation.noise=0.004 \
                      --because "the task text calls the score a loss; 0.004 is the seed spread in their notes"

Read `task.md`, the marked code and anything the person has told you, and suggest what you think is right.
A suggestion is not an answer: it is shown to the person preselected, with your reason, and becomes an
answer only when they leave it or pick it. Do not suggest where you have no evidence; say so and ask.

After `--infer`, every question but two has a suggested answer or a default: the goal and the length of a
training run have none, because nothing can stand in for them. Replace the tool's general suggestions with
yours wherever you know the project better: its 100 evaluations, its noise of 0.001 and its single test
evaluation are starting points for a person who says nothing, not recommendations for this project.

Two of the questions decide most of the rest: the kind of search (`run.type`, how to search) and the kind of
optimization (`run.skill`: a better score, a distilled student, tuned settings, a smaller or faster model, or an
interpretable model improved, a faster algorithm or pipeline). `evoloop skills` lists the library and
`evoloop skills --search WORDS` finds one; suggest what the person's goal describes. A skill is optional.

**When a skill is chosen, go through it with the person before going on.** Choosing one copies its file to
`DIR/skills/NAME/skill.yaml`, and that copy is what the search reads (`evoloop brief DIR --next` lists the files
under `skill_files`). Show them what it sets and what it tells the agents (`evoloop skills NAME --dir DIR`), and
ask what does not fit their problem. Edit the copy as they say; add what they know from earlier searches as
`diagnose` entries. With several skills, offer to merge them into one file
(`evoloop skills --merge A,B --name NEW --dir DIR`, then `--answer run.skill=NEW`). `evoloop skills NAME --diff
--dir DIR` shows the changes, and `evoloop plan DIR` shows their effect.

Then get the next question with

    evoloop brief DIR --next

It returns one question as JSON: its number and how many there are, its section, the question, why it is
asked, its choices (each with a line on what it means), the suggestion if there is one, and the default.

Ask it like this, every time:

1. **Say where they are**: "Question 6 of 17, Budget."
2. **Ask that one question only.** Never send a list of several questions in one message.
3. **Give the choices as choices**, each with its one-line meaning. Put the suggested one first and say why
   it is suggested; where there is none, say which is the default. If your interface has a way to offer
   options to pick from, use it; otherwise number them.
4. **Record exactly what they said**:
   - their own answer: `evoloop brief DIR --answer FIELD=VALUE`
   - "that's fine" (the suggestion, or the default): `evoloop brief DIR --keep FIELD`
5. **Get the next question** and go on until `question` is null.

If the person says "use the defaults for the rest", read them the remaining suggestions and defaults in one
message (`evoloop brief DIR --confirm NAME` lists them when questions are left), and only then confirm with
`--accept-defaults`. Without that flag a brief with unasked questions cannot be confirmed.

If they would rather fill in a form, `evoloop form DIR` writes a self-contained HTML page; they send back
the answers file it gives them and you run `evoloop brief DIR --import FILE`. In a terminal of their own,
`evoloop setup DIR` asks the same questions.

Then show them `evoloop plan DIR` (what the search will do at a glance, the warnings, what the agents are likely
to cost, then every setting with where it came from) before anything is confirmed.

## While a search runs

Stay with the run; the person should not have to learn the commands.

- Check `evoloop status DIR --name N` and the leaderboard at sensible intervals, and tell the person what changed: the
  best so far, what is held up, what waits for their decision. Report failures plainly.
- When they react ("too many big models", "try more augmentation", "stop the transformer family"), turn it into a
  change with `evoloop steer`, `set` or `note`, show them what will be applied, and apply it with `--by` their name.
- Decisions of the strategist that wait for the person: put each to them and record their answer (`approve`,
  `decline`).
- If the controller stops (budget spent, a pause, a crash), say why and what resumes it.

## Rules that matter

- **Suggest, never decide.** Propose your best guess with its reason; the person sees every choice and has the
  last word. Never record a guess as their answer without their having seen it.
- **Ask every set-up question.** Do not write values into `brief.yaml` to skip a question, and do not pass
  `--accept-defaults` unless the person has seen the values it takes and said to take them.
- **Confirm only with the name the person gives you**, after they have seen the plan:
  `evoloop brief DIR --confirm "Their Name"`. Never on your own word.
- **The approved plan is the agreement to spend.** Do not start a run they have not confirmed.
- **Dry-run first** with `agents.backend: stub` before real agents are paid.
- **Steering goes through the commands** (`set`, `note`, `withdraw`, `steer`, `chat`, `force`, `import`, `reference`,
  `rehash`, `review`, `stop`, `approve`, `decline`,
  `lineage`), always with `--by` the person's name. Do not edit a run's files.
- **Do not change `base/` or `adapter/` during a run.**
- **Test-set results are under `diagnostics.hidden`** and are never shown to the search's agents. Every evaluation
  named in `evaluation.test_metrics` belongs there.
- **Commit or push only when the person asks.**

## The code

`pytest tests` runs the suite with stub agents (no model call). Several pages are written by the code, and the
tests fail if they are stale: regenerate `docs/skill-library.md` with `evoloop skills --markdown`, the guides with
`evoloop skills --guides docs/guides`, the code map with `python tools/code_map.py > docs/code.md`, the plan explorer's data with `evoloop menu --plans > docs/assets/plans.json`,
and the pages `docs/menu.md` and
`docs/fields.md` are written by the code: after changing an option, a preset or a field, regenerate them
with `evoloop menu --markdown > docs/menu.md` and `evoloop menu fields --markdown > docs/fields.md`, or
the tests fail.
