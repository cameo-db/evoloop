# The strategist and the budget

Two things watch a run as a whole. The **strategist** is an agent that decides whether the search
should change course. The **spend governor** is code that keeps the agents' cost inside your cap.

## Why a strategist

The schedule follows the shares you set, whatever the results say. If thirty new designs in a row go
nowhere it keeps asking for new designs; if crossover of one kind keeps failing it keeps trying that
kind. The adaptive schedule reacts to past returns, but with a few dozen runs that signal is weak, and
anything driven by past returns tends to settle on what already works.

The strategist divides the work: **code detects and reports, the agent decides, code checks the
decision.** It can see why something is failing, which a count cannot; and it is bounded, because an
agent given a free hand over a search has a poor record.

## When it meets

- every `strategist.every` scored designs (15 by default), and
- at once when `strategist.plateau` designs (12 by default) have passed with no rise in the best score
  above the noise.

## What it is shown

Facts worked out by code: the designs since the best score last rose; what each mode, each move and
each kind of crossover has returned; the population; how varied the recent designs are (families,
distance from what was tried); the schedule in force; the budget left; what the agents have cost and
where the run is heading at that rate; its own earlier decisions with what followed them; and your
notes.

## What it may do

Up to two decisions a meeting, from this menu:

| Action | What it does | Applied at once? |
|---|---|---|
| `stay` | changes nothing | yes |
| `shares` | the shares of new designs, crossover and local moves, for the rest of this phase | yes, up to `strategist.max_share_shift` (0.15) per share |
| `novelty` | the novelty dial, and the novel share of new designs | yes |
| `local_mix` | the shares of the local moves | yes |
| `crossover_kinds` | which kinds of crossover are used | yes |
| `force` | the next few slots go to one mode and, if named, one kind of crossover or local move | yes, up to `strategist.force_max` (5) slots |
| `retire`, `revive` | takes a lineage out of the active set, or brings one back | yes |
| `direction` | a standing note to the writers | yes; three stand at once at most |
| `strategy` | changes the evolution strategy | no: waits for you |
| `question` | asks you something | yes; the run does not wait |

The bounds are enforced by code:

- **Exploration is protected.** New designs cannot be set below `strategist.min_new_share` (0.10).
- **Your word stands.** A setting you changed during the run is not changed back without your yes.
- **Anything in `strategist.ask_first` waits for you.** By default that is `strategy`; add any action to it.
- The lineage holding the best design is never retired.
- A decision that breaks a bound is refused, and the refusal is on the record.

## The three modes

| `strategist.mode` | What happens |
|---|---|
| `off` | no strategist (the default outside the run types below) |
| `advise` | it meets and decides; every decision waits for your yes or no |
| `act` | small decisions are applied at once; large ones wait for you |

The run types `explore_then_exploit`, `refine` and `survey` set `act`. `discovery` and `settings_only`
leave it off.

## Decisions that wait for you

```
evoloop report  mysearch --name r1                           # the strategist's section lists what is waiting
evoloop approve mysearch --name r1 --id S14 --by "Your Name"
evoloop decline mysearch --name r1 --id S14 --by "Your Name" --reason "keep exploring"
```

`status.json` lists them under `decisions_waiting`. A waiting decision changes nothing until you answer.

## Talking to it

Write a note; the strategist reads your notes at every meeting, like every other role.

```
evoloop note mysearch --name r1 "Exploration is underdelivering: be bolder, and try crossover between the top two families." --roles strategist --by "Your Name"
```

To change how it behaves, change its settings:

```
evoloop set mysearch --name r1 strategist.mode=advise strategist.every=10 --by "Your Name"
evoloop set mysearch --name r1 'strategist.ask_first=["strategy", "shares", "force"]' --by "Your Name"
```

## How it is judged

Every decision is a ledger entry: the action, its reason, the gain it expects and over how many
designs. `strategist.horizon` designs later (15 by default) code records what followed: the rise in
the best score, in noise floors, beside what was expected. The report has a table of every decision,
its status and both figures.

That shows what followed a decision. It does not show what the decision caused: there is no copy of the
run without it. To learn whether the strategist earns its place, compare a run with it against one
with `strategist.mode: off` on the same budget.

## Options and defaults

| Setting | Default | What it is |
|---|---|---|
| `strategist.mode` | `off` (`act` under three run types) | off, advise or act |
| `strategist.every` | 15 | scored designs between meetings |
| `strategist.plateau` | 12 | designs with no gain that trigger a meeting at once |
| `strategist.horizon` | 15 | designs after which a decision is scored |
| `strategist.min_new_share` | 0.10 | the least share of new designs it may set |
| `strategist.max_share_shift` | 0.15 | the largest move of a share without your yes |
| `strategist.force_max` | 5 | the most slots one `force` may order |
| `strategist.ask_first` | `["strategy"]` | actions that always wait for you |

The model it uses is `agents.models.strategist`, or `agents.default_model`. All of these can be changed
during a run.

## The budget

A run has two budgets, and both can be changed while it goes.

| Budget | Setting | When it runs out |
|---|---|---|
| training runs | `budget.evaluations` | the search ends |
| agent cost | `budget.model_dollars`, and `budget.model_calls` as a second cap | no further agent call is made; the run ends as paused, and goes on when you raise the cap |

Cost is whatever the backend reports for each call. The report and `status.json` show the spend so far,
the cost per design, and the figure the run is heading for at that rate.

### The spend governor

With `budget.spend_policy: pace` (the default) and a dollar cap set, code checks every ten designs
whether the run is on course to pass the cap. If it is, it takes one step to make the run cheaper, and
records it in the ledger with the figures:

1. one proposal fewer per slot (`variation.proposals_per_slot`), down to one
2. slots chosen by code, not by a coordinator agent
3. the analyst half as often
4. the strategist half as often
5. reviews at the end only
6. settings moves drawn by code, not written by an agent

It only makes the run cheaper. If you raise the cap and want proposals back, set them yourself.
`budget.spend_policy: none` switches it off; the cap still stops the calls.

### The reserve

The last `budget.reserve_share` of the cap (0.15) is kept for writing designs. When it is reached, the
analyst, the strategist, the reviews and the coordinator agent stop, so that what is left buys designs.

### What the cap cannot see

- A backend that reports no cost. For `anthropic_api`, give `agents.prices` for each model in use; the
  plan warns when one is missing, and a capped run pauses after three calls with no cost.
- Subscription limits. A call refused for the account's limit pauses every agent call until the limit
  resets; it is not retried in a loop and not charged.
- GPU time. That is `budget.evaluations` and `budget.wall_clock_hours`.
