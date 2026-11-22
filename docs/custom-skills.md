# Write a skill

A custom skill is one you write yourself. It does not have to resemble a library skill, belong to one
of the library's groups, or follow its naming. Any goal you can describe to the agents can be a skill,
and a skill can be a few lines long.

## Start

```
evoloop skills --new my-skill --dir mysearch
```

writes `mysearch/skills/my-skill/skill.yaml`, an empty skill with every entry explained in comments.
Fill it in, then use it and check it:

```
evoloop brief mysearch --answer run.skill=my-skill
evoloop plan mysearch
```

The plan shows the settings the skill applies and the text it adds to each agent call.

To begin from a library skill instead, copy the nearest one:

```
evoloop skills model-efficiency --copy mysearch/skills/edge-device
```

## Contents

Every entry is optional. This is a complete skill:

```yaml
guidance:
  writer: |
    Keep every model under two million parameters.
    Prefer dilated convolutions to pooling: the output is at base resolution.
```

The entries, most useful first:

| Entry | Holds |
|---|---|
| `guidance` | text added to the agent calls: `all` for every role, or `writer`, `analyst`, `strategist`, `coordinator` for one |
| `diagnose` | rules of the form "if the results show X, do Y", given to the writer and the analyst |
| `stages` | advice to the writer for the first half of the budget (`early`) and the second (`late`) |
| `settings` | search settings the skill applies, such as the strategy or the schedule |
| `needs` | what the evaluator must report for the skill to work: metrics and reference rows |

[Skill file format](skill-format.md) has every entry.

If you run searches without a skill and find yourself writing the same instructions into `task.md` and
notes each time, those instructions are the skill.

## Settings a skill may hold

A skill can set anything that can change during a run: the strategy, the schedule, the search space,
the harness, limits, the columns of the report. It cannot set what defines the problem, such as the
objective, the data or the evaluator. Those belong to the brief.

Guidance is advice to the agents. To make something hold whatever an agent writes, use a setting that
code enforces, such as `limits` or `space.forbidden_terms`.

## Reuse

| To use the skill in | Do this |
|---|---|
| one search | keep it in that search's `skills/` folder |
| several searches | keep the folder anywhere and give its path: `run.skill: /path/to/my-skill` |
| a search that also uses a library skill | list both: `run.skill: [model-distillation, my-skill]` |

## Adding a skill to the library

Add its folder under `evoloop/skills/` in the repository and open a pull request. The tests check that
every library skill loads and is complete. After adding one, regenerate the pages built from the
library (`evoloop skills --markdown > docs/skill-library.md`, `evoloop skills --guides docs/guides`,
`evoloop skills --table > docs/generated/skills-table.md`), add its guide to the navigation in
`mkdocs.yml`, and add its name to the list in `tests/test_skills.py`.

`evoloop skills --json` prints the library as a list of records (name, title, domain, objective, tags,
version, authors, what it sets, what it needs, a digest).
