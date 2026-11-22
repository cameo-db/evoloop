# Skill file format

A skill is a folder holding one file, `skill.yaml`. This page is the reference for that file.
[Edit, merge or write a skill](skills.md) explains how skills are used.

## Annotated example

```yaml
name: model-efficiency            # specific: <what>-<goal>
title: Make one model smaller or faster
summary: One or two lines, shown in listings.
domain: model                     # for browsing: model, algorithm, pipeline, bioinformatics, ...
objective: the same score at a lower cost in parameters or time
tags: [efficiency, compression, pruning, size, speed]
version: 2
authors: [evoloop]
when: >
  When to choose it, and when to choose another.

settings:                         # laid over the run type's and the autonomy level's; what you set in the brief still wins
  strategy: {mechanism: pareto, second_metric: parameters, second_direction: minimize}
  schedule: {local_mix: {edit: 0.35, settings: 0.15, ablation: 0.5}}

guidance:                         # read by the agents on every call
  all: What holds for every role.
  writer: What a writer should try, in what order, and what to avoid.
  analyst: What the analyst should look for and report.
  strategist: When to change course.

diagnose:                         # shown to the writer and the analyst
  - see: "parameter count fell but speed did not"
    do: "the time is not where the parameters are: cut resolution or depth instead of width"

stages:                           # added to the writer's guidance by how much of the budget is spent
  early: "Find what can be removed for nothing, with ablations across the whole model."
  late: "Work at the two ends of the front, and cross designs from the ends."

needs:
  adapter: ["report `parameters` in result.json"]     # listed in the plan
  figures: [parameters]           # the report warns if no result carries it
  references: ["the original model"]                  # the report warns if the leaderboard lacks the row

combines: [model-distillation]    # skills it is meant to be used with
conflicts: [settings-tuning, model-size-frontier]      # skills it should not be combined with: the plan warns

goal: Find a smaller or faster model          # the title of its guide page
start: {run_type: refine, evaluations: 100}   # the starting brief its guide shows
why: Why this set-up fits the task.
reading: How to read the result.
instead: [{if: you want the best model at several sizes, use: model-size-frontier}]
```

| Part | What it does | Who sees it |
|---|---|---|
| `settings` | sets what suits the task: the search space, the strategy, the mix of moves | the plan, under "From the skill ..." |
| `guidance` | what matters in this kind of task, what to try, what to avoid, for each role | every agent on every call, except the assessor and the translator |
| `goal`, `start`, `why`, `reading`, `instead` | the skill's guide page: where to start, why, how to read the result, when to choose another | you: in the [optimization guides](which-search.md) |
| `diagnose` | "if the results show this, do that" | the writer and the analyst |
| `stages` | advice for the first half of the budget, and for the second | the writer |
| `needs` | what the evaluator must do or report, and rows the leaderboard should carry | you: in the plan and in the report's warnings |
| `name`, `title`, `domain`, `objective`, `tags`, `when` | what the skill is for | you: in listings and searches |

## Rules

- A skill may only set what can change during a search. The objective, the data and the training length
  define the problem and stay in the brief; a skill that tries to set them is refused, with the reason.
- `settings` are laid over the run type's and the autonomy level's. Anything set in the brief wins.
- `guidance` may address `all`, `writer`, `analyst`, `strategist`, `coordinator` and `conductor`. It is
  shown on every call to those roles, and ranks below `task.md`, the results and your notes.
- `name` should be specific and follow the pattern *what*-*goal*, in lower case with hyphens:
  `model-size-frontier`, `algorithm-runtime`.
- Every skill carries the same record (name, title, domain, objective, tags, version, authors, what it
  sets, what it needs, a digest of its contents). `evoloop skills --json` prints the library as a list of
  those records.
