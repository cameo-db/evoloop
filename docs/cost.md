# Budget and cost

A search spends two things: training runs on your hardware, and dollars on the agents. Each has its own
cap, and both can be raised while the search runs.

| Budget | Setting | When it runs out |
|---|---|---|
| training runs | `budget.evaluations` | the search ends |
| agent cost | `budget.model_dollars` | no further agent call is started; the search pauses, and continues when you raise the cap |

The dollar cap is checked before each agent call and the cost is added after it returns. A call already under
way when the cap is reached still completes, so the total can end slightly above the cap, by at most the cost of
the calls then in progress.

GPU time is not counted in dollars. Bound it with the number of evaluations and, if you like, with
`budget.wall_clock_hours`.

## What the agents will cost

`evoloop plan` estimates it before you confirm. For the built-in formula example at 100 designs, with
the default model (Claude Opus 5.5, at the prices of 2026-11-03):

```
What the agents will cost (an estimate, for 100 designs):
  writer       about 110 (100 to 130) calls, about $5.45 ($3.39 to $8.48)   [claude-opus-5-5, effort high]
  analyst      about 12 (12 to 15) calls, about $0.30 ($0.28 to $0.41)      [claude-opus-5-5, effort medium]
  strategist   about 10 (7 to 13) calls, about $0.19 ($0.12 to $0.29)       [claude-opus-5-5, effort medium]
  assessor     about 6 (6 to 6) calls, about $0.24 ($0.23 to $0.27)         [claude-opus-5-5, effort medium]
  in all       about 138 (125 to 164) calls, about $6.18 ($4.02 to $9.45)
```

That example's code is a few lines long. A real model's code is far larger, and the writers' cost grows
with it: a writer is sent the parents' code and returns the blocks it changes. Expect a real search to
cost several times this.

Treat the estimate as right to within about a factor of two. The number of calls follows from the
settings and is fairly sure. The size of a call is a guess: models differ in how much they write, and
the tokens they spend reasoning are not counted. It has not yet been checked against a real bill.

## What makes it cheaper or dearer

**How much the agents decide.** For the same example: about $3.50 with `harnessed`, $6.20 with `guided`,
$7.60 with `agentic` ([The agents](agents.md#how-much-to-let-them-decide)).

**The model.** The plan shows the same search on each current model. A cheaper model for most designs
and a strong one for some is `agents.writer_mix` ([Models and prices](models.md)).

**How many designs.** A promotion ladder makes the same training budget cover more designs, and each
design is written by an agent, so the agent cost rises with it.

**Whether agents are needed at all.** A search over settings alone can use the built-in estimator and
make no agent call ([`settings-tuning`](guides/settings-tuning.md)).

**The size of your blocks.** Returning local moves as edits (`variation.edit_format: diff`) cuts the
output of those calls on large blocks.

## While it runs

```
evoloop estimate mysearch --name r1
```

Once a role has made a few calls, its real cost per call replaces the guess and the rest of the search
is projected from that. `evoloop status` and the report show the spend so far, the cost per design over
the last twenty, and the total the search is heading for.

## Keeping inside the cap

With a dollar cap set, evoloop checks every ten scored designs whether the search is heading past it.
If so, it takes one step to make the search cheaper and records what it did:

1. one proposal fewer per slot, down to one;
2. the kind of move chosen by code, if an agent was choosing it;
3. the analyst half as often;
4. the strategist half as often;
5. reviews at the end only;
6. settings moves drawn by code.

It only ever makes the search cheaper. If you raise the cap and want proposals back, set them yourself.
`budget.spend_policy: none` switches this off; the cap still stops the calls.

The last 15% of the cap is kept for writing designs (`budget.reserve_share`). When it is reached, the
analyst, the strategist, scheduled reviews and the coordinator stop, so that what is left buys designs.

## What the cap cannot see

**A backend that reports no cost.** With the Anthropic API, give `agents.prices` for any model not on
the built-in list. The plan warns when one is missing, and a capped search pauses after three calls with
no cost.

**Subscription limits.** A call refused for your account's limit pauses all agent calls until the limit
resets. It is not retried in a loop and not charged.

## Settings on this page

[`budget.evaluations`](fields.md#budget-evaluations), [`budget.model_dollars`](fields.md#budget-model_dollars), [`budget.model_calls`](fields.md#budget-model_calls), [`budget.wall_clock_hours`](fields.md#budget-wall_clock_hours),
[`budget.spend_policy`](fields.md#budget-spend_policy), [`budget.reserve_share`](fields.md#budget-reserve_share), [`agents.prices`](fields.md#agents-prices).

