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
- when `strategist.plateau` designs (12 by default) have passed with no rise in the best score above
  the noise. The best to beat includes the baseline. While a plateau lasts it meets again every half
  that many designs.

## What it is shown

Facts worked out by code: the designs since the best score last rose; what each mode, each move and
each kind of crossover has returned; the population; how varied the recent designs are (families,
distance from what was tried); the schedule in force; the budget left; what the agents have cost and
where the run is heading at that rate; its own earlier decisions with what followed them; and your
notes.

## What it may do

Up to two decisions a meeting, one of a kind, from this menu:

| Action | What it does | Applied at once? |
|---|---|---|
| `stay` | changes nothing | yes |
| `shares` | the shares of new designs, crossover and local moves, for the phase in force | yes, while no share stands more than `strategist.max_share_shift` (0.15) from where you last left it |
| `novelty` | the novelty dial, and the novel share of new designs | yes |
| `local_mix` | the shares of the local moves | yes |
| `crossover_kinds` | which kinds of crossover are used; at least one | yes |
| `force` | the next few slots go to one mode and, if named, one kind of crossover or local move | yes, while no more than `strategist.force_max` (5) slots are on order in all |
| `retire`, `revive` | sets a lineage aside, or gives a retired or benched one a second chance | yes (lineage strategy only) |
| `direction` | advice to the writers | yes; three stand at once at most |
| `strategy` | changes the evolution strategy | no: waits for you |
| `question` | asks you something | yes; the run does not wait |

## The bounds, as code enforces them

- **Exploration is protected.** `shares` cannot set new designs below `strategist.min_new_share`
  (0.10). Slots ordered with `force` for crossover or local moves wait whenever new designs are below
  that share of the last twenty designs.
- **A share cannot creep.** The move is measured from where you last left the shares (the brief, a
  change of yours, or a decision of the strategist that you approved), however many decisions it takes
  to get there. Past `strategist.max_share_shift` it waits for you.
- **Ordered slots are capped in all.** However many meetings, no more than `strategist.force_max`
  slots are on order at once. An order whose mode cannot be filled is given up, and the record says so.
- **Your word stands.** A decision waits for you when it would change a setting you changed during the
  run: the setting itself, a part of it, or one that followed from your change of the run type or the
  budget. An order for slots waits when you have changed the shares it would override.
- **Anything in `strategist.ask_first` waits for you.** By default that is `strategy`.
- **The lineage holding the best design is never retired.** A lineage brought back gets a second
  chance, not a permanent place: its moves without a gain are counted afresh, it is active beside the
  best lineages without taking a place from them, and it retires again when it has used that chance up.
- **A decision that breaks a bound, or cannot be read, is refused**, and the refusal is in the ledger.
  It never ends the run.

`retire` and `revive` have an effect only under the `lineage` strategy without islands; elsewhere they
are refused.

## The three modes

| `strategist.mode` | What happens |
|---|---|
| `off` | no strategist (the default outside the run types below) |
| `advise` | it meets and decides; every decision waits for your yes or no |
| `act` | decisions within the bounds are applied at once; the others wait for you |

The run types `explore_then_exploit`, `refine` and `survey` set `act`. `discovery` and `settings_only`
leave it off.

Switching it `off` during a run takes effect at once: slots it had ordered are given up, and a meeting
that was under way changes nothing.

## Who runs the search: code, or an agent you talk to

`harness.conductor` decides who is in charge of the course of the search.

| `harness.conductor` | What happens |
|---|---|
| `code` (the default) | The deterministic option. The schedule and the strategy run the search exactly as set. Nothing changes course unless you change it (or a strategist you switched on does, within its bounds). |
| `agent` | An agent runs the search and you talk to it. It is the strategist with a voice: it meets on the same occasions, decides from the same menu under the same bounds, and it answers you. |

```
evoloop chat mysearch --name r1 --by "Your Name"                               # talk back and forth; an empty line ends it
evoloop chat mysearch --name r1 "why so few new designs lately?" --by "Your Name"   # one message, one answer
```

In a talk the agent is given the state of the search worked out by code, what it decided since you last
spoke, what waits for your yes, and the conversation so far. It can:

- **explain**: what is happening and why, from the records;
- **change course when you ask**: its decisions go to the controller as requests and are checked like
  any other decision, so one within the bounds is applied at the next turn, one beyond them waits for
  your yes, and one off the menu is refused. The command prints each thing it asked for;
- **take your yes or no**: saying "yes" to a waiting decision in the talk approves it in your name.

What you say is also shown to the agent at its later meetings, so a talk steers what it does when you
are not there. Every message, answer and decision is kept (`chat.jsonl`, and the ledger).

What does not change with an agent in charge: code enforces the budget, the limits, the frozen code and
the floor on new designs; code picks parents and records every action. The agent cannot edit files or
settings outside its menu. For those it tells you the command.

Choosing `agent` switches the strategist to `act` if it was `off`; `strategist.mode: advise` keeps
every decision waiting for your yes. You can switch either way during a run:

```
evoloop set mysearch --name r1 harness.conductor=agent --by "Your Name"
evoloop set mysearch --name r1 harness.conductor=code  --by "Your Name"
```

A talk costs one model call per message, charged to the run's model budget like any other call.

## Decisions that wait for you

```
evoloop report  mysearch --name r1                           # the strategist's section lists what is waiting
evoloop approve mysearch --name r1 --id S14 --by "Your Name"
evoloop decline mysearch --name r1 --id S14 --by "Your Name" --reason "keep exploring"
```

The report shows each waiting decision in full: its action and arguments, the strategist's reason, what
it expects, and why it waits. `status.json` lists them under `decisions_waiting`.

- A waiting decision changes nothing until you answer.
- **A yes is checked against the run as it is then**, not as it was when the decision was made. If the
  search has moved on and the decision can no longer be done within the bounds (the floor was raised,
  the lineage now holds the best design), it is refused with the reason. Its effects are worked out
  afresh, so it does not undo what changed in between.
- A decision left unanswered for twice `strategist.horizon` designs lapses.

## Setting a lineage aside yourself

```
evoloop lineage mysearch --name r1 --retire L4 --by "Your Name"
evoloop lineage mysearch --name r1 --revive L4 --by "Your Name"
```

The last word on a lineage stands, yours or the strategist's, and each is in the ledger.

## Talking to it

Write a note addressed to it; it reads your notes at every meeting.

```
evoloop note mysearch --name r1 "Exploration is underdelivering: be bolder, and try crossover between the top two families." --roles strategist --by "Your Name"
```

To change how it behaves, change its settings:

```
evoloop set mysearch --name r1 strategist.mode=advise strategist.every=10 --by "Your Name"
evoloop set mysearch --name r1 'strategist.ask_first=["strategy", "shares", "force"]' --by "Your Name"
```

Its own `direction` to the writers is shown to them apart from your notes, as advice; where the two
conflict, the writers are told that your note stands.

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
| `strategist.plateau` | 12 | designs with no gain that trigger a meeting |
| `strategist.horizon` | 15 | designs after which a decision is scored; twice that, an unanswered one lapses |
| `strategist.min_new_share` | 0.10 | the floor on new designs |
| `strategist.max_share_shift` | 0.15 | how far a share may stand from where you left it without your yes |
| `strategist.force_max` | 5 | the most slots on order at once |
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
the cost per design, and the figure the run is heading for.

The cost per design is dollars per design *written*, whether it was scored, failed, refused or is still
training, taken over the last twenty designs once there are that many, so that it follows a change
that made the run cheaper. The projection adds that rate for the designs still to be written.

### The spend governor

With `budget.spend_policy: pace` (the default) and a dollar cap set, code checks every ten scored
designs whether the run is heading past the cap. If it is, it takes one step to make the run cheaper,
and records it in the ledger with the figures:

1. one proposal fewer per slot (`variation.proposals_per_slot`), down to one
2. slots chosen by code, not by a coordinator agent
3. the analyst half as often
4. the strategist half as often
5. reviews at the end only
6. settings moves drawn by code, not written by an agent

It only makes the run cheaper. If you raise the cap and want proposals back, set them yourself.
`budget.spend_policy: none` switches it off; the cap still stops the calls.

### The reserve

With the `pace` policy, the last `budget.reserve_share` of the cap (0.15) is kept for writing designs.
When it is reached, the analyst, the strategist, the scheduled reviews and the coordinator agent stop,
so that what is left buys designs. A review you ask for yourself with `evoloop review` is still made.
With `budget.spend_policy: none` there is no reserve.

### What the cap cannot see

- A backend that reports no cost. For `anthropic_api`, give `agents.prices` for each model in use; the
  plan warns when one is missing, and a capped run pauses after three calls with no cost.
- Subscription limits. A call refused for the account's limit pauses every agent call until the limit
  resets; it is not retried in a loop and not charged.
- GPU time. That is `budget.evaluations` and `budget.wall_clock_hours`.
