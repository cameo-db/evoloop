# Edit, merge or write a skill

A skill is one YAML file: settings for the search, text added to every agent call, and the measurements
your evaluator must report. [The file format](skill-format.md) lists every entry. Skills are optional.

The files that come with evoloop are a [library](skill-library.md) of starting points. A search never
reads the library's file. It reads its own copy, which you can change.

## During setup

When you choose a skill, evoloop copies it into the search folder straight away:

```
mysearch/
  skills/
    model-distillation/skill.yaml     <- the search reads this file
```

You can edit the copy before you read the plan and before you confirm. Each way of setting up has a
place to do it:

| Setting up with | How to edit the skill |
|---|---|
| `evoloop setup` | After the skill question it shows the file and what it sets. `e` opens the file in `$EDITOR`; `m` merges several skills into one file; Enter goes on. |
| `evoloop form` | Under the skill question, each chosen skill opens as an editable text box. Your edits are saved in the answers file, and `evoloop brief --import` writes them to the search folder. |
| an agent | `evoloop brief DIR --next` lists the files under `skill_files`. The agent shows you what the skill sets and tells the agents, and edits the copy as you ask. |
| the commands | `evoloop skills NAME --edit --dir mysearch`, or open the file in any editor. |

Then check the result:

```
evoloop plan mysearch                               # what the search will do with the file as it is now
evoloop skills model-distillation --diff --dir mysearch     # your changes against the library's version
```

The plan names each skill file and says whether it is unchanged, edited, or your own. A file that
cannot be read, or that sets something a skill may not set, is reported there and the search does not
start with it.

## Combining skills

Give several, as a list or separated by commas:

```yaml
run:
  skill: [model-distillation, model-size-frontier]
```

- Settings are laid over each other in the order given. Where two skills set the same thing, the later
  one's value stands, and the plan says which.
- The agents see the text of each, under the name of its skill.
- The measurements they need are added together.

Each skill stays a separate file in `mysearch/skills/`, and you can edit each one.

### Merge them into one file

To work on a combination as a single skill:

```
evoloop skills --merge model-distillation,model-size-frontier --name my-students --dir mysearch
evoloop brief mysearch --answer run.skill=my-students
```

This writes `mysearch/skills/my-students/skill.yaml`. It holds the same settings and the same agent
text as the combination did, so the search behaves the same until you edit it. Where the skills
disagreed, the file's first lines say which value was kept:

```
# small-family: merged from model-efficiency + model-size-frontier. This file is yours to edit.
# Where two of them set the same thing, the later one's value was kept:
#   strategy.mechanism: 'archive' (model-size-frontier), not 'pareto' (model-efficiency)
```

The merge is made from the search's copies, so edits you already made are carried over.

Combinations in the library that are meant to go together:

| Combine | For |
|---|---|
| `model-distillation` + `model-size-frontier` | a family of students across sizes |
| `model-distillation` + `model-efficiency` | the smallest student that holds the teacher's score |
| `model-finetuning` + `model-training-recipe` | adapting a pretrained model, with the recipe open |
| `bioinformatics-algorithm` + `algorithm-runtime` | a method that is both more accurate and faster |

A pair marked as conflicting (for example `settings-tuning` with any other skill) still runs; the plan
warns.

## During a run

- Edit the search's copy at any time. The controller notices at its next turn, uses the new text from
  then on, and records the change in the ledger with the file's digest before and after.
- Change skill: `evoloop set mysearch --name r1 run.skill=model-efficiency --by "Your Name"`. The new
  skill is copied in, and the ledger lists every setting that moved with it.

## Writing your own

Start from the nearest one:

```
evoloop skills model-efficiency --copy mysearch/skills/edge-device
```

Edit `mysearch/skills/edge-device/skill.yaml`, change its `name`, and set `run.skill: edge-device`. A
skill is looked up by name in the search's `skills/` folder first, then as a path, then in the library.

What to put in it, most useful first:

1. **Diagnoses.** "If the results show X, do Y." Write down the mistakes you have watched a search make.
2. **An order of attack.** What to try first, and what is rarely worth an evaluation.
3. **What must not change.** Conventions and constraints.
4. **What to measure.** Under `needs`, so that a search missing a figure is told.
5. **Settings.** Only where the task calls for them.

If you run without a skill and find yourself writing the same instructions into `task.md` and notes for
each search, those instructions are the skill.

## Adding a skill to the library

Add its folder under `evoloop/skills/` in the repository and open a pull request. The tests check that
every library skill loads and is complete. After adding one, regenerate the pages built from the
library (`evoloop skills --markdown > docs/skill-library.md`, `evoloop skills --guides docs/guides`,
`evoloop skills --table > docs/generated/skills-table.md`), add its guide to the navigation in
`mkdocs.yml`, and add its name to the list in `tests/test_skills.py`.

`evoloop skills --json` prints the library as a list of records (name, title, domain, objective, tags,
version, authors, what it sets, what it needs, a digest). There is no online registry yet; the library
is the folder in the repository.
