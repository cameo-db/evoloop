# Agents

An agent in evoloop is one LLM call with a fixed role. The controller decides when each role is
called and what it is sent. Roles never call each other.

## The roles

| Role | Called | Sent | Returns |
|---|---|---|---|
| writer | for each design that is not made in code | your `task.md`, the parents' code, the top of the leaderboard, the last 10 results, the analyst's lessons, your notes | one or more proposals: new code for the marked blocks, a hypothesis, a forecast of the gain |
| analyst | every 8 finished designs | results since its last call, the leaderboard, earlier lessons | lessons, each citing runs. A lesson counts as supported only if its evidence spans two lineages |
| strategist | every 15 scored designs, and on a plateau | figures worked out by code: gains by kind of move, diversity, budget left, its own earlier decisions | up to two decisions from a fixed list. Code checks each against your bounds before applying it |
| coordinator | every slot, if switched on | the kinds of move possible now, with the parents code would use for each | one of those options |
| assessor | at points you choose | each role's calls, with what happened afterwards | a written review of each role, for you |
| translator | when you run `evoloop steer` | your words and the current settings | setting changes and notes, shown to you before anything is applied |

Only the writer is required. A search can run with the writer alone, and the
[`settings-tuning-bayesian`](guides/settings-tuning-bayesian.md) skill runs with no agent at all.

The *controller* is not an agent. It is the Python process that runs the search. The *conductor* is
the strategist when you have chosen to talk to it with `evoloop chat`.

## How much the agents decide

`harness.autonomy` sets this in one step. More autonomy means more LLM calls, so it is also a choice
about cost. `evoloop plan` shows the estimate for each level before you commit.

| | `harnessed` | `guided` | `agentic` |
|---|---|---|---|
| Kind of move for each slot | the schedule | the schedule | a coordinator agent, from options code prepares |
| Parents | the strategy | the strategy | the strategy |
| Strategist | off | on, within bounds you set | on, more often, with wider bounds |
| Hyperparameter moves | a random sampler in code | the writer | the writer |
| Proposals per slot | 1 | set by budget size | 3 |
| LLM calls per 100 designs, estimated | about 110 | about 140 | about 270 |

Parents are always chosen by code. So are the checks on every design, the budget, the spend cap and
your limits. Left unset, the run type decides the level, and most run types behave like `guided`.

`harness.level` separately sets which roles run beside the writer. `minimal` is the writer alone.
`standard` adds the analyst. `full`, the default, also retrains the leading design on a new seed every
20 designs, to check that its score holds.

## Why there is a strategist

The schedule keeps to the shares you set, whatever the results say. If thirty new designs in a row go
nowhere, it still asks for new designs. A schedule that adapts to past gains has little to go on with
a few dozen results, and tends to settle on what already works.

A strategist can read why something is failing, which a count cannot. It is bounded because an agent
given a free hand over a search tends to do badly: code works out the facts, the agent chooses from a
fixed list of actions, and code checks each choice before applying it.
[Working with the strategist](strategist.md) has the list, the bounds, and how to approve or decline
what it proposes.

## Models

Every role runs on `claude-opus-5-5` at medium effort by default, and the writer at high effort. You
can change the model for all roles (`agents.default_model`) or for one (`agents.models`), or
[share the writing between several models](moves.md#more-than-one-model-writing).
[Models and prices](models.md)

The LLM is reached through the Anthropic API or the Claude Code command (`agents.backend`). For a dry
run it can be replaced by a script (`stub`).

## Checking the agents

Every call is recorded with what the agent was sent, what it forecast, and what happened. From that
record the report builds a scorecard for each role, and the assessor reviews each role at the points
you choose. [Audit the agents](auditing.md)

## Settings

[`harness.autonomy`](fields.md#harness-autonomy), [`harness.level`](fields.md#harness-level), [`harness.coordinator`](fields.md#harness-coordinator), [`harness.conductor`](fields.md#harness-conductor),
[`harness.analyst_every`](fields.md#harness-analyst_every), [`strategist.mode`](fields.md#strategist-mode), [`agents.default_model`](fields.md#agents-default_model), [`agents.models`](fields.md#agents-models), [`agents.effort`](fields.md#agents-effort), [`agents.backend`](fields.md#agents-backend).
