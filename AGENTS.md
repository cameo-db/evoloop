# For an agent helping someone use evoloop

evoloop searches over marked blocks of a project's code. `docs/index.md` is the overview and
`docs/setting-up.md` the procedure. This file is about how to work with the person.

## Setting up a search: propose, then ask one question at a time

The questions come from the tool, not from you. **Before the first question, propose your best guess for
every question you have evidence for**, each with its reason:

    evoloop brief DIR --infer                      # the tool's own guesses: the machine, the folder, the budget
    evoloop brief DIR --suggest objective.direction=minimize --suggest evaluation.noise=0.004 \
                      --because "the task text calls the score a loss; 0.004 is the seed spread in their notes"

Read `task.md`, the marked code and anything the person has told you, and suggest what you think is right.
A suggestion is not an answer: it is shown to the person preselected, with your reason, and becomes an
answer only when they leave it or pick it. Do not suggest where you have no evidence; say so and ask.

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

If they would rather fill in a form, `evoloop form DIR` writes a self-contained HTML page; they send back
the answers file it gives them and you run `evoloop brief DIR --import FILE`. In a terminal of their own,
`evoloop setup DIR` asks the same questions.

Then show them `evoloop plan DIR` (the settings with where each came from, the warnings, and what the
agents are likely to cost) before anything is confirmed.

## Rules that matter

- **Suggest, never decide.** Propose your best guess with its reason; the person sees every choice and has the
  last word. Never record a guess as their answer without their having seen it.
- **Confirm only with the name the person gives you**, after they have seen the plan:
  `evoloop brief DIR --confirm "Their Name"`. Never on your own word.
- **The approved plan is the agreement to spend.** Do not start a run they have not confirmed.
- **Dry-run first** with `agents.backend: stub` before real agents are paid.
- **Steering goes through the commands** (`set`, `note`, `steer`, `stop`, `approve`, `decline`,
  `lineage`), always with `--by` the person's name. Do not edit a run's files.
- **Do not change `base/` or `adapter/` during a run.**
- **Test-set results are under `diagnostics.hidden`** and are never shown to the search's agents.
- **Commit or push only when the person asks.**

## The code

`pytest tests` runs the suite with stub agents (no model call). The pages `docs/menu.md` and
`docs/fields.md` are written by the code: after changing an option, a preset or a field, regenerate them
with `evoloop menu --markdown > docs/menu.md` and `evoloop menu fields --markdown > docs/fields.md`, or
the tests fail.
