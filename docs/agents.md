# The agents, and how much they decide

A search uses language-model agents in several roles. Each role is a separate call with its own
instructions, and no role talks to another: each is shown what it needs from the run's files.

## The roles

| Role | What it does | When |
|---|---|---|
| **writer** | writes a design: a new one, an edit, a crossover | most slots |
| **analyst** | reads recent results and writes lessons the writers are shown | every 8 designs |
| **strategist** | reviews the search as a whole and may change its course | every 15 designs, and on a plateau |
| **coordinator** | chooses the kind of move for each slot, in place of the schedule | every slot, if switched on |
| **assessor** | reviews how well each other role has done, for you | at points you choose |
| **translator** | turns your own words into setting changes, for `evoloop steer` | when you use it |

Only the writer is needed. A search can run with writers alone, and the
[`settings-tuning` skill](guides/settings-tuning.md) runs with no agent at all.

Two things that sound like roles are not agents. The *controller* is the Python process that runs the
search. The *conductor* is the strategist when you have chosen to talk to it with `evoloop chat`.

## How much to let them decide

One setting, `harness.autonomy`, bundles the choices. More autonomy means more calls, so it is also a
choice about cost; `evoloop plan` shows the estimate for each level before you commit.

With **`harnessed`**, code decides where the search goes. The schedule picks every move, settings moves
are drawn by code, and agents only write designs and lessons. Fewest calls.

With **`guided`**, the schedule still picks every move, and a strategist may shift its shares, the
novelty and the mix of moves within bounds you set. It must ask you before changing the strategy.

With **`agentic`**, a coordinator agent picks the kind of move for each slot, the strategist meets more
often with wider bounds, and writers return three proposals per slot. Most calls.

At every level code still enforces the budget and the spend cap, the limits, the frozen code, the
checks on every design and a minimum share of new designs. More autonomy widens what agents may decide.
It does not remove those.

Left unset, the run type decides: most run types behave like `guided`. A [skill](skills.md) can
override the level where it knows better, which is how `settings-tuning` stays agent-free under any of
them. Anything you set yourself wins over all of these.

## Why have a strategist

The schedule follows the shares you set whatever the results say. If thirty new designs in a row go
nowhere, it keeps asking for new designs. An adaptive schedule reacts to past gains, but with a few
dozen results that signal is weak, and anything driven by past gains settles on what already works.

A strategist can read why something is failing, which a count cannot. It is also bounded, because an
agent given a free hand over a search tends to do badly. So code works out the facts, the agent decides
from a fixed menu of actions, and code checks each decision before applying it.
[Working with the strategist](strategist.md) covers the menu, the bounds and how to approve or decline
what it proposes.

## Which model, and how hard it thinks

Every role runs on `claude-opus-5-5` at medium effort by default, with writers at high effort. Change
the model for all roles (`agents.default_model`), for one (`agents.models`), or share the writing
between several ([more than one model writing](moves.md#more-than-one-model-writing)).
[Models and prices](models.md) has the list and what each costs.

## Checking that the agents earn their cost

Every call is recorded with what the agent was shown, what it forecast, and what happened. From that
the report builds a scorecard for each role, and at points you choose an assessor reviews each role.
[Audit the agents](auditing.md).

## Settings on this page

`harness.autonomy`, `harness.level`, `harness.coordinator`, `harness.conductor`,
`harness.analyst_every`, `strategist.mode`, `agents.default_model`, `agents.models`, `agents.effort`.
Each is described in [Brief fields](fields.md#harness).
