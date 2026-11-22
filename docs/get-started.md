# Get started

The way to use evoloop is through a coding agent. You say what you want to improve. The agent sets the
search up with you, and nothing is spent until you approve a plan. You do not need to read the code or
learn the commands.

## Requirements

- A project with code you want to improve and a way to tell whether a version is better. For a model,
  that is a training script and a validation metric.
- [Claude Code](https://claude.com/claude-code), or another coding agent that can read files and run
  commands.
- An Anthropic API key or a Claude Code login, for the agents inside the search.
- Somewhere to run it: a workstation or a Slurm cluster.

## Start

Clone evoloop and open it in Claude Code:

```
git clone https://github.com/cameo-db/evoloop.git
cd evoloop
claude
```

Then say what you want, in your own words. For example:

> Set up an evoloop search for my project in ~/projects/mymodel. I want a higher validation accuracy
> without making the model larger.

The repository carries instructions for the agent, so it knows how to proceed from there.

## Your decisions

The agent works most of the setup out from your project. It asks you for the rest one question at a
time, with a suggested answer wherever it has evidence for one. Five decisions are yours:

1. What to optimize.
2. Which parts of the code may change.
3. How a version is scored.
4. How much to spend: the number of training runs, and a dollar cap for the agents.
5. Any hard limits, such as a largest model size.

On a cluster it also asks which account to charge, how your environment is activated, and whether
there are queues it must not use.

## The agent's part

- It installs evoloop and copies your project into a search folder. Your original is not touched.
- It marks the code that may change and writes the evaluator, the script that scores one version. It
  shows you both.
- It proves the setup with a dry run that costs nothing.
- It shows you the plan: what will run, where, and what the agents are likely to cost.
- It starts the search only after you approve the plan, and records your approval under your name.
- It watches the search and reports on it.

## During the search

Talk to the agent. Ask how the search is going, or tell it what you think of the results: "too many
large models", "try more augmentation", "give it another hundred runs". The agent turns that into a
change to the running search, shows you what it will apply, and applies it. Every change is recorded.

## Demo

The [worked example](quickstart.md) is a complete search on a toy problem. It runs in about half a
minute, with no API key and no GPU.

## Manual setup

Everything the agent does is a command or a plain file, and all of it can be done or changed by hand.
[Manual setup](setting-up.md) documents each step. Read it to check an agent's work, or to do without
one.
